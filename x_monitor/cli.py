from __future__ import annotations

import argparse
from pathlib import Path

from .app import run_monitor_sync
from .render import (
    build_console,
    render_benchmark_samples,
    render_distribution,
    render_header,
    render_queries,
    render_reply_samples,
    render_summary,
    render_top_tweets,
    render_warnings,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="x_monitor",
        description="X monitor for Decathlon/Intersport using a local clix clone.",
    )
    parser.add_argument("--brand", choices=["both", "decathlon", "intersport"], default="both")
    parser.add_argument("--latest-count", type=int, default=50)
    parser.add_argument("--latest-pages", type=int, default=2)
    parser.add_argument("--top-count", type=int, default=25)
    parser.add_argument("--top-pages", type=int, default=1)
    parser.add_argument("--output-dir", default=str(Path("data") / "x_runs"))
    parser.add_argument("--clix-bin", default="clix")
    parser.add_argument("--debug", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    console = build_console()
    result = run_monitor_sync(
        brand=args.brand,
        latest_count=args.latest_count,
        latest_pages=args.latest_pages,
        top_count=args.top_count,
        top_pages=args.top_pages,
        output_dir=args.output_dir,
        clix_bin=args.clix_bin,
        debug=args.debug,
    )
    render_header(console, result)
    render_queries(console, result.query_runs)
    render_distribution(console, result.tweets)
    render_top_tweets(console, result.tweets)
    render_reply_samples(console, result.tweets)
    render_benchmark_samples(console, result.tweets)
    render_summary(console, result)
    render_warnings(console, result.warnings)
    return 0
