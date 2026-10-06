#!/usr/bin/env python3
"""
PortfolioX load-test runner.

Usage:
    python scripts/load_test.py --url http://localhost:8000 --account 1
    python scripts/load_test.py --url https://portfoliox.fly.dev --account 1

Outputs: latency percentiles, req/s, error rate per concurrency level.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import httpx


@dataclass
class Result:
    """Aggregated results for one concurrency level."""

    concurrency: int
    total_requests: int
    successful: int
    failed: int
    duration_seconds: float
    requests_per_second: float
    latencies_ms: list[float]

    def pct(self, p: int) -> float:
        if not self.latencies_ms:
            return 0.0
        return statistics.quantiles(self.latencies_ms, n=100)[p - 1]

    def p50(self) -> float:
        return self.pct(50)

    def p75(self) -> float:
        return self.pct(75)

    def p90(self) -> float:
        return self.pct(90)

    def p95(self) -> float:
        return self.pct(95)

    def p99(self) -> float:
        return self.pct(99)

    def mean(self) -> float:
        return statistics.mean(self.latencies_ms) if self.latencies_ms else 0.0


async def run_benchmark(
    base_url: str,
    account_id: int,
    concurrency: int,
    total_requests: int,
    timeout: float = 10.0,
) -> Result:
    """Run a single concurrency level benchmark."""
    semaphore = asyncio.Semaphore(concurrency)
    latencies: list[float] = []
    errors = 0
    completed = 0

    async def make_request(client: httpx.AsyncClient) -> None:
        nonlocal errors, completed
        url = f"{base_url}/api/accounts/{account_id}/portfolio"
        async with semaphore:
            start = time.perf_counter()
            try:
                resp = await client.get(url, timeout=timeout)
                elapsed = (time.perf_counter() - start) * 1000
                if resp.status_code == 200:
                    latencies.append(elapsed)
                    completed += 1
                else:
                    errors += 1
            except Exception:
                errors += 1

    async with httpx.AsyncClient() as client:
        start_time = time.perf_counter()
        tasks = [make_request(client) for _ in range(total_requests)]
        await asyncio.gather(*tasks)
        duration = time.perf_counter() - start_time

    return Result(
        concurrency=concurrency,
        total_requests=total_requests,
        successful=completed,
        failed=errors,
        duration_seconds=duration,
        requests_per_second=total_requests / duration if duration > 0 else 0,
        latencies_ms=latencies,
    )


def print_results(results: list[Result]) -> None:
    """Print a formatted table of results."""
    print("\n" + "=" * 90)
    print(
        f"{'Concurrency':>12} | {'Req/s':>10} | {'p50':>8} | {'p75':>8} | {'p90':>8} | {'p95':>8} | {'p99':>8} | {'Errors':>6}"
    )
    print("-" * 90)
    for r in results:
        print(
            f"{r.concurrency:>12} | {r.requests_per_second:>10.1f} | "
            f"{r.p50():>8.1f} | {r.p75():>8.1f} | {r.p90():>8.1f} | "
            f"{r.p95():>8.1f} | {r.p99():>8.1f} | {r.failed:>6}"
        )
    print("=" * 90)


def print_json(results: list[Result]) -> None:
    """Print JSON for CI/parsing."""
    out = [
        {
            "concurrency": r.concurrency,
            "requests_per_second": round(r.requests_per_second, 2),
            "p50_ms": round(r.p50(), 1),
            "p75_ms": round(r.p75(), 1),
            "p90_ms": round(r.p90(), 1),
            "p95_ms": round(r.p95(), 1),
            "p99_ms": round(r.p99(), 1),
            "mean_ms": round(r.mean(), 1),
            "successful": r.successful,
            "failed": r.failed,
            "duration_seconds": round(r.duration_seconds, 2),
        }
        for r in results
    ]
    print(json.dumps(out, indent=2))


async def main() -> int:
    parser = argparse.ArgumentParser(description="PortfolioX load test")
    parser.add_argument(
        "--url", required=True, help="Base URL (e.g., http://localhost:8000)"
    )
    parser.add_argument("--account", type=int, default=1, help="Account ID to query")
    parser.add_argument(
        "--concurrency",
        type=int,
        nargs="+",
        default=[1, 10, 50, 100],
        help="Concurrency levels to test",
    )
    parser.add_argument(
        "--requests", type=int, default=200, help="Total requests per concurrency level"
    )
    parser.add_argument(
        "--timeout", type=float, default=10.0, help="Request timeout (seconds)"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output JSON instead of table"
    )
    args = parser.parse_args()

    # Warm-up
    print(
        f"Warming up {args.url}/api/accounts/{args.account}/portfolio ...",
        end=" ",
        flush=True,
    )
    async with httpx.AsyncClient() as client:
        try:
            await client.get(
                f"{args.url}/api/accounts/{args.account}/portfolio", timeout=10.0
            )
            print("OK")
        except Exception as e:
            print(f"FAILED: {e}")
            print("Is the server running and the account seeded?")
            return 1

    results = []
    for c in args.concurrency:
        print(
            f"Running concurrency={c} ({args.requests} requests)...",
            end=" ",
            flush=True,
        )
        r = await run_benchmark(args.url, args.account, c, args.requests, args.timeout)
        results.append(r)
        print(f"done ({r.requests_per_second:.1f} req/s, {r.failed} errors)")

    if args.json:
        print_json(results)
    else:
        print_results(results)

    # Also write to file for the PDF
    out_file = Path("load_test_results.json")
    out_file.write_text(
        json.dumps(
            {
                str(r.concurrency): {
                    "requests_per_second": r.requests_per_second,
                    "p50_ms": r.p50(),
                    "p75_ms": r.p75(),
                    "p90_ms": r.p90(),
                    "p95_ms": r.p95(),
                    "p99_ms": r.p99(),
                    "mean_ms": r.mean(),
                    "successful": r.successful,
                    "failed": r.failed,
                }
                for r in results
            },
            indent=2,
        )
    )
    print(f"\nResults written to {out_file}")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
