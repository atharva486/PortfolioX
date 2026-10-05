"""Regression tests for import-time side effects.

Every test here asserts the SAME property: importing the application must
not depend on external credentials or a reachable network.

Why this file exists
--------------------
`app/api/routes/ai.py` used to do `ai_service = AIChatService()` at module
level, and `AIChatService.__init__` called `genai.Client(api_key=...)`,
which raises `ValueError` when the key is absent. Because the router was
imported by `app/main.py`, the whole process died on startup:

    ValueError: No API key was provided.   # killed the Docker healthcheck

That took down `/health`, `/docs`, and every unrelated endpoint because one
optional integration could not find a secret. These tests exist so that a
missing optional credential can never again be fatal to the process.
"""

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# A child process is used deliberately. Removing an environment variable and
# re-importing inside this interpreter would be unreliable, because a module
# already imported into `sys.modules` is not re-executed.
_CHILD = """
import os, sys, tempfile
sys.path.insert(0, {repo!r})

# Move out of the repo BEFORE importing anything. python-dotenv searches
# upward from the working directory, so a .env in the repo root would be
# found and repopulate the credentials cleared below.
os.chdir(tempfile.mkdtemp())

# Strip every credential an optional integration might look for.
for var in ("GEMINI_API_KEY", "FINNHUB_API_KEY", "FINNHUB_API_SECRET"):
    os.environ.pop(var, None)

import app.main
from fastapi.testclient import TestClient

client = TestClient(app.main.app)
assert client.get("/health").status_code == 200, "/health must work without secrets"
assert client.get("/version").status_code == 200, "/version must work without secrets"
assert client.get("/openapi.json").status_code == 200, "schema must build without secrets"
print("OK")
"""


def _run_child() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", _CHILD.format(repo=str(REPO_ROOT))],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env={
            # A deliberately bare environment: no .env is auto-loaded by
            # python-dotenv here because it is not invoked, and DATABASE_URL
            # falls back to SQLite via app/db/session.py.
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", "/tmp"),
        },
        timeout=120,
    )


def test_app_imports_and_serves_without_any_api_keys():
    """The regression itself: no credential may be required to boot."""
    result = _run_child()
    assert result.returncode == 0, (
        "Application failed to start without API keys.\n"
        f"--- stdout ---\n{result.stdout}\n"
        f"--- stderr ---\n{result.stderr}"
    )
    assert "OK" in result.stdout


def test_ai_service_defers_client_construction():
    """Constructing the service must not construct the Gemini client.

    Runs in a child process for the same reason as the test above: importing
    anything from `app` triggers `load_dotenv()` in `app/db/session.py`,
    which repopulates the environment from a local `.env`. Clearing the
    variable in this interpreter is therefore not enough to simulate an
    unconfigured host.
    """
    child = f"""
import os, sys, tempfile
sys.path.insert(0, {str(REPO_ROOT)!r})
os.chdir(tempfile.mkdtemp())
for var in ("GEMINI_API_KEY", "FINNHUB_API_KEY", "FINNHUB_API_SECRET"):
    os.environ.pop(var, None)

from app.api.routes.ai import get_ai_service
service = get_ai_service()          # must not raise
try:
    service.client
except RuntimeError as exc:
    assert "GEMINI_API_KEY" in str(exc), exc
    print("OK")
else:
    raise AssertionError("client was built without an API key")
"""

    result = subprocess.run(
        [sys.executable, "-c", child],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env={
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", "/tmp"),
        },
        timeout=120,
    )
    assert result.returncode == 0, (
        "AI service should construct lazily and fail loudly on use.\n"
        f"--- stdout ---\n{result.stdout}\n"
        f"--- stderr ---\n{result.stderr}"
    )
    assert "OK" in result.stdout


def test_ai_service_is_a_shared_singleton():
    """FastAPI's Depends caches the provider, so we get one client."""
    from app.api.routes.ai import get_ai_service

    assert get_ai_service() is get_ai_service()
