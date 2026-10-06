#!/usr/bin/env python3
"""
PortfolioX async vs sequential comparison runner.

Runs load tests in both modes and outputs comparison JSON.

Usage:
    python scripts/compare_pricing_modes.py --url http://localhost:8000 --account 1

This will:
1. Run benchmarks with PRICING_MODE=sequential
2. Run benchmarks with PRICING_MODE=async
3. Output side-by-side comparison
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_load_test(
    base_url: str,
    account_id: int,
    concurrency: int,
    requests: int,
    pricing_mode: str,
) -> dict[str, Any]:
    """Run load_test.py as subprocess with given pricing mode."""
    env = os.environ.copy()
    env["PRICING_MODE"] = pricing_mode

    cmd = [
        sys.executable,
        "scripts/load_test.py",
        "--url",
        base_url,
        "--account",
        str(account_id),
        "--concurrency",
        str(concurrency),
        "--requests",
        str(requests),
        "--json",
    ]

    result = subprocess.run(
        cmd, capture_output=True, text=True, env=env, cwd=Path(__file__).parent.parent
    )

    if result.returncode != 0:
        raise RuntimeError(f"Load test failed: {result.stderr}")

    return json.loads(result.stdout)


def compare_modes(
    base_url: str,
    account_id: int,
    concurrency_levels: list[int],
    requests_per_level: int,
) -> dict[str, Any]:
    """Run benchmarks in both modes and compare."""
    comparison = {
        "url": base_url,
        "account_id": account_id,
        "levels": [],
    }

    for c in concurrency_levels:
        print(f"\n=== Concurrency {c} ===")

        print("  Running sequential mode...", end=" ", flush=True)
        seq = run_load_test(base_url, account_id, c, requests_per_level, "sequential")
        print("done")

        print("  Running async mode...", end=" ", flush=True)
        async_res = run_load_test(base_url, account_id, c, requests_per_level, "async")
        print("done")

        # Aggregate across all results for this concurrency
        def aggregate(results: list[dict]) -> dict:
            if not results:
                return {}
            r = results[0]
            return {
                "requests_per_second": r["requests_per_second"],
                "p50_ms": r["p50_ms"],
                "p75_ms": r["p75_ms"],
                "p90_ms": r["p90_ms"],
                "p95_ms": r["p95_ms"],
                "p99_ms": r["p99_ms"],
                "mean_ms": r["mean_ms"],
                "successful": r["successful"],
                "failed": r["failed"],
            }

        seq_agg = aggregate(seq)
        async_agg = aggregate(async_res)

        speedup = {}
        if seq_agg and async_agg and seq_agg.get("mean_ms", 0) > 0:
            speedup = {
                "reqs_per_sec_ratio": round(
                    async_agg["requests_per_second"] / seq_agg["requests_per_second"], 2
                )
                if seq_agg["requests_per_second"] > 0
                else 0,
                "mean_latency_improvement_pct": round(
                    (1 - async_agg["mean_ms"] / seq_agg["mean_ms"]) * 100, 1
                )
                if seq_agg["mean_ms"] > 0
                else 0,
                "p95_latency_improvement_pct": round(
                    (1 - async_agg["p95_ms"] / seq_agg["p95_ms"]) * 100, 1
                )
                if seq_agg["p95_ms"] > 0
                else 0,
            }

        comparison["levels"].append(
            {
                "concurrency": c,
                "sequential": seq_agg,
                "async": async_agg,
                "speedup": speedup,
            }
        )

    return comparison


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare sequential vs async pricing")
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
    args = parser.parse_args()

    print(f"Comparing sequential vs async pricing at {args.url}")
    print(f"Account: {args.account}, Concurrency levels: {args.concurrency}")

    try:
        comparison = compare_modes(
            args.url, args.account, args.concurrency, args.requests
        )
    except RuntimeError as e:
        print(f"ERROR: {e}")
        return 1

    # Print summary
    print("\n" + "=" * 100)
    print(
        f"{'Concurrency':>12} | {'Mode':>10} | {'Req/s':>10} | {'p50':>8} | {'p75':>8} | {'p90':>8} | {'p95':>8} | {'p99':>8}"
    )
    print("-" * 100)
    for level in comparison["levels"]:
        c = level["concurrency"]
        for mode_name, data in [
            ("sequential", level["sequential"]),
            ("async", level["async"]),
        ]:
            if data:
                print(
                    f"{c:>12} | {mode_name:>10} | {data['requests_per_second']:>10.1f} | "
                    f"{data['p50_ms']:>8.1f} | {data['p75_ms']:>8.1f} | "
                    f"{data['p90_ms']:>8.1f} | {data['p95_ms']:>8.1f} | {data['p99_ms']:>8.1f}"
                )
            else:
                print(f"{c:>12} | {mode_name:>10} | {'FAILED':>10}")
    print("=" * 100)

    # Print speedups
    print("\nSPEEDUP (async over sequential):")
    print("-" * 60)
    for level in comparison["levels"]:
        s = level.get("speedup", {})
        if s:
            print(
                f"  Concurrency {level['concurrency']:>3}: "
                f"req/s {s.get('reqs_per_sec_ratio', 0):.2f}x, "
                f"mean latency -{s.get('mean_latency_improvement_pct', 0):.1f}%, "
                f"p95 latency -{s.get('p95_latency_improvement_pct', 0):.1f}%"
            )

    # Write to file
    out_file = Path(__file__).parent.parent / "pricing_mode_comparison.json"
    out_file.write_text(json.dumps(comparison, indent=2))
    print(f"\nComparison written to {out_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
