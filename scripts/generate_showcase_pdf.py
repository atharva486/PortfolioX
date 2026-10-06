#!/usr/bin/env python3
"""
Generate PortfolioX showcase PDF from collected metrics and benchmarks.
Run after deploy_and_benchmark.sh to produce updated PDF.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

try:
    from fpdf import FPDF
except ImportError:
    print("Installing fpdf2...")
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "fpdf2"])
    from fpdf import FPDF


class PortfolioPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(25, 60, 120)
        self.cell(0, 10, "PortfolioX — Technical Showcase", ln=True, align="C")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(100)
        self.cell(
            0,
            6,
            f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            ln=True,
            align="C",
        )
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title: str):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(25, 60, 120)
        self.cell(0, 8, title, ln=True)
        self.set_draw_color(25, 60, 120)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def bullet(self, text: str, indent: int = 15):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30)
        self.cell(indent, 5, "\u2022")
        self.multi_cell(0, 5, text)

    def key_value(self, key: str, value: str, indent: int = 15):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(30)
        self.cell(indent, 5, "")
        self.cell(60, 5, f"{key}:")
        self.set_font("Helvetica", "", 10)
        self.cell(0, 5, value, ln=True)


def load_json(path: Path) -> dict | None:
    if path.exists():
        return json.loads(path.read_text())
    return None


def main() -> int:
    root = Path(__file__).resolve().parents[1]

    metrics = load_json(root / "project_metrics.json")
    comparison = load_json(root / "pricing_mode_comparison.json")

    pdf = PortfolioPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # --- Executive Summary ---
    pdf.section_title("Executive Summary")
    pdf.body_text(
        "PortfolioX is a production-grade portfolio-trading backend built with FastAPI, SQLAlchemy, "
        "and PostgreSQL. It demonstrates professional software engineering practices: strict typing, "
        "comprehensive testing, concurrency-safe database operations, containerized deployment, "
        "and CI/CD automation. This document presents measured performance data from a live deployment."
    )

    # --- Project Metrics ---
    if metrics:
        pdf.section_title("Project Metrics")
        loc = metrics.get("lines_of_code", {})
        pdf.key_value("Total Python LOC", f"{loc.get('total', 0):,}")
        pdf.key_value("App code", f"{loc.get('app', 0):,}")
        pdf.key_value("Test code", f"{loc.get('test', 0):,}")
        pdf.key_value("REST endpoints", str(metrics.get("endpoints", 0)))
        pdf.key_value("Test functions", str(metrics.get("test_functions", 0)))
        pdf.key_value("Git commits", str(metrics.get("commits", 0)))
        deps = metrics.get("dependencies", {})
        pdf.key_value("Runtime dependencies", str(deps.get("runtime", 0)))
        pdf.key_value("Dev-only dependencies", str(deps.get("dev_only", 0)))
        pdf.key_value("CI est. duration", f"{metrics.get('ci_estimated_seconds', 0)}s")

    # --- Architecture Highlights ---
    pdf.section_title("Architecture Highlights")
    highlights = [
        "Layered architecture: domain (pure Python) / application / infrastructure",
        "Domain models fully typed; mypy --strict on app.domain.*",
        "Async price fetching via asyncio.gather() with configurable PRICING_MODE",
        "Concurrency-safe order execution: SELECT FOR UPDATE SKIP LOCKED + PG advisory locks",
        "Multi-stage Docker build (python:3.10-slim, non-root, HEALTHCHECK on /health)",
        "CI pipeline: ruff + mypy + pytest + coverage + Docker build + GHCR publish",
        "GitHub Actions required status checks on main branch",
    ]
    for h in highlights:
        pdf.bullet(h)

    # --- Performance Benchmarks ---
    if comparison and comparison.get("levels"):
        pdf.section_title("Live Performance Benchmarks")
        pdf.body_text(
            "Measured against deployed instance. Each concurrency level: 100 requests. "
            "Sequential mode awaits each price fetch in order; async mode fires all concurrently via asyncio.gather()."
        )

        # Table header
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(25, 60, 120)
        pdf.set_text_color(255)
        cols = [22, 18, 18, 18, 18, 18, 18, 18, 18]
        headers = [
            "Concurrency",
            "Mode",
            "Req/s",
            "p50",
            "p75",
            "p90",
            "p95",
            "p99",
            "Mean",
        ]
        for i, h in enumerate(headers):
            pdf.cell(cols[i], 6, h, border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(30)
        for level in comparison["levels"]:
            c = level["concurrency"]
            for mode_name, data in [
                ("sequential", level["sequential"]),
                ("async", level["async"]),
            ]:
                if data:
                    row = [
                        str(c) if mode_name == "async" else "",
                        mode_name,
                        f"{data['requests_per_second']:.1f}",
                        f"{data['p50_ms']:.1f}",
                        f"{data['p75_ms']:.1f}",
                        f"{data['p90_ms']:.1f}",
                        f"{data['p95_ms']:.1f}",
                        f"{data['p99_ms']:.1f}",
                        f"{data['mean_ms']:.1f}",
                    ]
                else:
                    row = [
                        str(c) if mode_name == "async" else "",
                        mode_name,
                        "FAILED",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                    ]
                for i, val in enumerate(row):
                    pdf.cell(cols[i], 5, val, border=1, align="C")
                pdf.ln()
        pdf.ln(4)

        # Speedup summary
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(25, 60, 120)
        pdf.cell(0, 6, "Speedup (async over sequential):", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(30)
        for level in comparison["levels"]:
            s = level.get("speedup", {})
            if s:
                pdf.bullet(
                    f"Concurrency {level['concurrency']}: {s['reqs_per_sec_ratio']:.2f}x throughput, "
                    f"p95 latency -{s['p95_latency_improvement_pct']:.1f}%, "
                    f"mean latency -{s['mean_latency_improvement_pct']:.1f}%"
                )

    # --- Key Technical Decisions ---
    pdf.section_title("Key Technical Decisions (ADR Summary)")
    adrs = [
        ("ADR-001", "Layered architecture with pure-Python domain core"),
        ("ADR-007", "PostgreSQL advisory lock for single-active-scheduler"),
        ("ADR-008", "Numeric(18,4) money / Numeric(20,8) quantity precision"),
        ("ADR-009", "Position dataclass replacing dict — enables static typing"),
        ("ADR-011", "asyncio.gather for concurrent price fetching"),
        ("ADR-012", "LLM tool calling isolated behind interface; graceful degradation"),
        ("ADR-013", "Order lifecycle: PENDING -> FILLED/REJECTED/CANCELLED"),
        ("ADR-014", "Scheduler topology: APScheduler heartbeat + DB locking"),
    ]
    for id_, desc in adrs:
        pdf.bullet(f"{id_}: {desc}")

    # --- Resume Bullets ---
    pdf.section_title("Resume-Ready Bullets")
    if metrics and comparison:
        loc = metrics.get("lines_of_code", {}).get("total", 0)
        endpoints = metrics.get("endpoints", 0)
        tests = metrics.get("test_functions", 0)

        best = max(
            comparison["levels"],
            key=lambda x: x.get("speedup", {}).get("reqs_per_sec_ratio", 0),
        )
        s = best.get("speedup", {})
        p95_imp = s.get("p95_latency_improvement_pct", 0)
        reqs_ratio = s.get("reqs_per_sec_ratio", 0)

        bullets = [
            f"Built a layered portfolio-trading backend (FastAPI, SQLAlchemy, PostgreSQL) with {loc:,} lines of Python across {endpoints} REST endpoints",
            f"Designed async price-fetching pipeline using asyncio.gather(); cut p95 latency by {p95_imp:.0f}% and increased throughput {reqs_ratio:.1f}x under {best['concurrency']} concurrent requests vs sequential baseline",
            "Implemented concurrency-safe order execution with SELECT FOR UPDATE SKIP LOCKED + advisory locks; verified against real PostgreSQL in CI (not SQLite)",
            "Enforced strict typing (mypy --strict on domain layer), linting (ruff), and 100% typed domain models; CI pipeline: lint -> type-check -> test -> coverage -> Docker build -> GHCR publish",
            "Multi-stage Docker build (python:3.10-slim, non-root, HEALTHCHECK); image excludes dev tooling (pytest, ruff, mypy)",
            "Deployed to Cloud Run with managed PostgreSQL (Neon); CI/CD via GitHub Actions with required status checks",
            f"Wrote {tests} tests including regression tests for 3 critical bugs (double-order execution, portfolio valuation, row-locking); coverage ~57%",
        ]
        for b in bullets:
            pdf.bullet(b)

    # --- Tech Stack ---
    pdf.section_title("Tech Stack")
    stack = [
        "Language: Python 3.10",
        "Framework: FastAPI 0.141",
        "Database: PostgreSQL (Neon) + SQLAlchemy 2.0 (async)",
        "Migrations: Alembic",
        "Testing: pytest + pytest-asyncio + pytest-cov",
        "Linting/Typing: ruff + mypy (strict on domain)",
        "Container: Docker multi-stage, GHCR",
        "CI/CD: GitHub Actions (quality, concurrency, build, release)",
        "Deploy: Google Cloud Run (or Fly.io/Railway)",
        "Monitoring: /health, /ready, /health/db, /version endpoints",
    ]
    for item in stack:
        pdf.bullet(item)

    # Output
    out_path = root / "PortfolioX_Showcase.pdf"
    pdf.output(str(out_path))
    print(f"PDF generated: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
