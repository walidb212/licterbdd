from __future__ import annotations

import argparse
from pathlib import Path

from .app import run_monitor_sync


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="news_monitor",
        description="Google News monitor for Decathlon/Intersport with optional Cloudflare enrichment.",
    )
    parser.add_argument("--brand", choices=["both", "decathlon", "intersport"], default="both")
    parser.add_argument("--language", default="fr")
    parser.add_argument("--region", default="FR")
    parser.add_argument("--days-back", type=int, default=7)
    parser.add_argument("--max-items-per-query", type=int, default=20)
    parser.add_argument("--output-dir", default=str(Path("data") / "news_runs"))
    parser.add_argument("--enrich-mode", choices=["auto", "none"], default="auto")
    parser.add_argument("--max-enriched-items", type=int, default=5)
    return parser


def _print_result(result) -> None:
    print(f"[Execution] run_id={result.run_id} brand={result.selected_brand} region={result.selected_region} output={result.run_dir}")
    print(f"[Summary] queries={len(result.query_runs)} articles={len(result.articles)} cloudflare={result.cloudflare_mode}")
    print("[Queries]")
    for row in result.query_runs:
        status = "ok"
        if row.error:
            status = f"error: {row.error}"
        elif row.warning:
            status = f"warning: {row.warning}"
        print(
            f"- {row.query_name}: fetched={row.fetched_count} retained={row.retained_count} added={row.added_count} status={status}"
        )
    if result.articles:
        print("[Articles]")
        for article in result.articles[:10]:
            print(
                f"- {article.published_at or '-'} | {article.brand_detected} | {article.signal_type} | {article.source_name or '-'} | {article.article_title}"
            )
    if result.warnings:
        print("[Warnings]")
        for warning in result.warnings:
            print(f"- {warning}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    result = run_monitor_sync(
        brand=args.brand,
        language=args.language,
        region=args.region,
        days_back=args.days_back,
        max_items_per_query=args.max_items_per_query,
        output_dir=args.output_dir,
        enrich_mode=args.enrich_mode,
        max_enriched_items=args.max_enriched_items,
    )
    _print_result(result)
    return 0
