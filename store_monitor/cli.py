from __future__ import annotations

import argparse
from pathlib import Path

from .app import run_monitor_sync
from .render import build_console, render_header, render_reviews, render_stores, render_summary, render_warnings


def parse_bool(value: str) -> bool:
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes", "y", "on"}:
        return True
    if lowered in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Expected a boolean value, got: {value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="store_monitor",
        description="Store discovery and Google Maps review monitor for Decathlon/Intersport.",
    )
    parser.add_argument("--brand", choices=["both", "decathlon", "intersport"], default="both")
    parser.add_argument("--stage", choices=["all", "discovery", "reviews"], default="all")
    parser.add_argument("--output-dir", default=str(Path("data") / "store_runs"))
    parser.add_argument("--incremental", type=parse_bool, default=True)
    parser.add_argument("--state-db", default=str(Path("data") / "state" / "monitor_state.sqlite3"))
    parser.add_argument("--city-seeds", default="Paris,Lyon,Marseille,Lille,Toulouse,Bordeaux,Nantes,Nice,Strasbourg,Rennes,Montpellier")
    parser.add_argument("--stale-after-days", type=int, default=30)
    parser.add_argument("--headless", type=parse_bool, default=True)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--limit-stores", type=int, default=None)
    parser.add_argument("--max-reviews-per-store", type=int, default=40)
    parser.add_argument("--resume", type=parse_bool, default=True)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    console = build_console()
    result = run_monitor_sync(
        brand=args.brand,
        stage=args.stage,
        output_dir=args.output_dir,
        incremental=args.incremental,
        state_db=args.state_db,
        city_seeds=[value.strip() for value in args.city_seeds.split(",") if value.strip()],
        stale_after_days=args.stale_after_days,
        headless=args.headless,
        debug=args.debug,
        limit_stores=args.limit_stores,
        max_reviews_per_store=args.max_reviews_per_store,
        resume=args.resume,
    )
    render_header(console, result.run_id, result.run_dir, result.selected_brand, result.selected_stage)
    render_stores(console, result.stores)
    render_reviews(console, result.reviews)
    render_summary(console, result)
    render_warnings(console, result.warnings)
    return 0
