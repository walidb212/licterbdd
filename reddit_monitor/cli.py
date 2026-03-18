from __future__ import annotations

import argparse
from pathlib import Path

from .app import run_monitor_sync
from .render import (
    build_console,
    render_brand_table,
    render_comment_samples,
    render_run_header,
    render_seed_table,
    render_summary,
    render_top_posts,
    render_warnings,
)


def parse_bool(value: str) -> bool:
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes", "y", "on"}:
        return True
    if lowered in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Expected a boolean value, got: {value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reddit_monitor",
        description="Reddit monitor for Decathlon/Intersport using local crawl4ai.",
    )
    parser.add_argument(
        "--brand",
        choices=["both", "decathlon", "intersport"],
        default="both",
        help="Brand focus for seed selection.",
    )
    parser.add_argument(
        "--max-posts-per-seed",
        type=int,
        default=15,
        help="Maximum post URLs retained per seed page.",
    )
    parser.add_argument(
        "--max-comments-per-post",
        type=int,
        default=20,
        help="Maximum visible comments retained per post page.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path("data") / "reddit_runs"),
        help="Base output directory. A timestamped run subdirectory is created inside it.",
    )
    parser.add_argument(
        "--headless",
        type=parse_bool,
        default=True,
        help="Run the browser in headless mode. Default: true.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable crawl4ai verbosity and keep extra diagnostic output.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    console = build_console()
    result = run_monitor_sync(
        brand=args.brand,
        max_posts_per_seed=args.max_posts_per_seed,
        max_comments_per_post=args.max_comments_per_post,
        output_dir=args.output_dir,
        headless=args.headless,
        debug=args.debug,
    )

    render_run_header(
        console=console,
        selected_brand=result.selected_brand,
        run_id=result.run_id,
        run_dir=result.run_dir,
        headless=args.headless,
    )
    render_seed_table(console, result.seed_reports)
    render_brand_table(console, result.posts)
    render_top_posts(console, result.posts)
    render_comment_samples(console, result.comments)
    render_summary(console, result)
    render_warnings(console, result.warnings)
    return 0
