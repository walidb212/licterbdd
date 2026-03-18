from __future__ import annotations

import argparse

from .app import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prod_pipeline", description="Production pipeline runner for the LICTER monitoring stack.")
    parser.add_argument("--brand", choices=["both", "decathlon", "intersport"], default="both")
    parser.add_argument("--steps", default="all")
    parser.add_argument("--output-dir", default="data/pipeline_runs")
    parser.add_argument("--state-db", default="data/state/monitor_state.sqlite3")
    parser.add_argument("--clix-bin", default="")
    parser.add_argument("--continue-on-error", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    exit_code, artifact_dir = run_pipeline(
        brand=args.brand,
        steps=args.steps,
        output_dir=args.output_dir,
        state_db=args.state_db,
        clix_bin=args.clix_bin,
        continue_on_error=args.continue_on_error,
    )
    print(f"[Execution] output={artifact_dir}")
    print(f"[Result] exit_code={exit_code}")
    return exit_code
