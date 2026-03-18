from __future__ import annotations

import argparse
from pathlib import Path

from .app import run_monitor_sync
from .render import build_console, render_documents, render_header, render_summary, render_warnings


def parse_bool(value: str) -> bool:
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes", "y", "on"}:
        return True
    if lowered in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Expected a boolean value, got: {value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="context_monitor", description="Official context document monitor for Decathlon/Intersport.")
    parser.add_argument("--brand", choices=["both", "decathlon", "intersport"], default="both")
    parser.add_argument("--document-types", default="all")
    parser.add_argument("--output-dir", default=str(Path("data") / "context_runs"))
    parser.add_argument("--incremental", type=parse_bool, default=True)
    parser.add_argument("--state-db", default=str(Path("data") / "state" / "monitor_state.sqlite3"))
    parser.add_argument("--debug", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    console = build_console()
    result = run_monitor_sync(
        brand=args.brand,
        document_types=args.document_types,
        output_dir=args.output_dir,
        incremental=args.incremental,
        state_db=args.state_db,
        debug=args.debug,
    )
    render_header(console, result.run_id, result.run_dir, result.selected_brand, result.selected_document_types)
    render_documents(console, result.documents)
    render_summary(console, result)
    render_warnings(console, result.warnings)
    return 0
