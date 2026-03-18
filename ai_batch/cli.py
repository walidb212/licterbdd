from __future__ import annotations

import argparse

from .app import run_batch_sync
from .config import DEFAULT_OPENAI_MODEL, DEFAULT_OUTPUT_DIR


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai_batch", description="Batch AI enrichment for the latest monitor runs.")
    parser.add_argument("--brand", choices=["both", "decathlon", "intersport"], default="both")
    parser.add_argument("--input-run", default="latest")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--provider", choices=["auto", "openai", "openrouter", "heuristic"], default="auto")
    parser.add_argument("--model", default=DEFAULT_OPENAI_MODEL)
    parser.add_argument("--chunk-size", type=int, default=8)
    parser.add_argument("--background-threshold", type=int, default=12)
    parser.add_argument("--strict-openai", action="store_true")
    parser.add_argument("--review-run", default=None)
    parser.add_argument("--store-run", default=None)
    parser.add_argument("--product-run", default=None)
    parser.add_argument("--news-run", default=None)
    parser.add_argument("--reddit-run", default=None)
    parser.add_argument("--youtube-run", default=None)
    parser.add_argument("--tiktok-run", default=None)
    parser.add_argument("--x-run", default=None)
    parser.add_argument("--global-run", default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = run_batch_sync(
        brand=args.brand,
        input_run=args.input_run,
        output_dir=args.output_dir,
        provider=args.provider,
        model=args.model,
        chunk_size=args.chunk_size,
        background_threshold=args.background_threshold,
        strict_openai=args.strict_openai,
        review_run=args.review_run,
        store_run=args.store_run,
        product_run=args.product_run,
        news_run=args.news_run,
        reddit_run=args.reddit_run,
        youtube_run=args.youtube_run,
        tiktok_run=args.tiktok_run,
        x_run=args.x_run,
        global_run=args.global_run,
    )
    print(f"[Execution] run_id={result.run_id} output={result.run_dir}")
    print(
        f"[Summary] social={len(result.social_records)} review={len(result.review_records)} news={len(result.news_records)} entities={len(result.entity_summaries)}"
    )
    if result.warnings:
        print("[Warnings]")
        for warning in result.warnings:
            print(f"- {warning}")
    return 0
