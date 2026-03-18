from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import sys
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .config import DEFAULT_MAX_ITEMS_PER_SOURCE, is_source_enabled, list_sources
from .extractor import TikTokExtractor, VideoRecord


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("tiktok_monitor")


def _write_jsonl(path: Path, records: list[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            payload = dataclasses.asdict(record) if dataclasses.is_dataclass(record) else record
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _build_results_markdown(
    *,
    run_id: str,
    selected_brand: str,
    include_experimental: bool,
    duration_s: float,
    videos: list[VideoRecord],
    source_stats: list[dict[str, object]],
    warnings: list[str],
) -> str:
    by_brand = Counter(row.brand_focus for row in videos)
    by_pillar = Counter(row.pillar for row in videos)
    by_status = Counter(str(row["production_status"]) for row in source_stats)
    enabled_count = sum(1 for row in source_stats if row["enabled_in_run"])
    lines = [
        f"# tiktok_monitor - run `{run_id}`",
        "",
        "## Scope",
        "",
        f"- brand: `{selected_brand}`",
        f"- include_experimental: `{str(include_experimental).lower()}`",
        f"- duration_s: `{duration_s:.1f}`",
        f"- videos: `{len(videos)}`",
        f"- video brands: {', '.join(f'`{name}`={count}' for name, count in sorted(by_brand.items())) or '`none`'}",
        f"- pillars: {', '.join(f'`{name}`={count}' for name, count in sorted(by_pillar.items())) or '`none`'}",
        f"- configured_sources: `{len(source_stats)}`",
        f"- enabled_sources: `{enabled_count}`",
        f"- source_statuses: {', '.join(f'`{name}`={count}' for name, count in sorted(by_status.items())) or '`none`'}",
        "",
        "## Sources",
        "",
        "| Brand | Source | Type | Pillar | Status | Enabled | Videos | Note |",
        "| --- | --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for row in source_stats:
        enabled_label = "yes" if row["enabled_in_run"] else "no"
        note = str(row.get("note") or "").replace("|", " ")
        lines.append(
            f"| {row['brand']} | {row['name']} | {row['source_type']} | {row['pillar']} | {row['production_status']} | {enabled_label} | {row['videos']} | {note} |"
        )
    if warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in warnings:
            lines.append(f"- {warning}")
    return "\n".join(lines) + "\n"


def run(
    *,
    brand: str = "both",
    max_items_per_source: int = DEFAULT_MAX_ITEMS_PER_SOURCE,
    output_dir: str = "data/tiktok_runs",
    include_experimental: bool = False,
    quiet: bool = True,
) -> Path:
    import time

    t0 = time.time()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid.uuid4().hex[:6]
    run_dir = Path(output_dir) / run_id
    extractor = TikTokExtractor(quiet=quiet)

    videos: list[VideoRecord] = []
    source_stats: list[dict[str, object]] = []
    warnings: list[str] = []
    seen_video_ids: set[tuple[str, str]] = set()

    for source in list_sources(brand):
        source_brand = source.brand_focus
        enabled_in_run = is_source_enabled(source, include_experimental=include_experimental)
        source_row = {
            "brand": source.brand_focus,
            "name": source.name,
            "source_type": source.source_type,
            "pillar": source.pillar,
            "production_status": source.production_status,
            "enabled_in_run": enabled_in_run,
            "videos": 0,
            "note": source.coverage_note,
        }
        if not enabled_in_run:
            source_stats.append(source_row)
            continue

        log.info("[%s] %s - %s", source_brand, source.source_type, source.name)
        try:
            raw_videos = extractor.extract_source(str(source.query_text), max_items=max_items_per_source)
        except Exception as exc:
            warnings.append(f"{source.name} failed: {exc}")
            raw_videos = []

        added = 0
        for raw in raw_videos:
            video_id = str(raw.get("id") or raw.get("display_id") or "")
            if not video_id:
                continue
            normalized_brand = source_brand if source_brand != "both" else "both"
            video_key = (normalized_brand, video_id)
            if video_key in seen_video_ids:
                continue
            seen_video_ids.add(video_key)
            videos.append(
                extractor.normalize_video(
                    raw,
                    run_id=run_id,
                    brand_focus=normalized_brand,
                    source_type=source.source_type,
                    query_name=source.name,
                    query_text=source.query_text,
                    pillar=source.pillar,
                    production_status=source.production_status,
                )
            )
            added += 1

        if not added:
            warnings.append(f"{source.name}: no usable TikTok videos extracted.")
        source_row["videos"] = added
        source_stats.append(source_row)

    _write_jsonl(run_dir / "videos.jsonl", videos)
    _write_jsonl(run_dir / "comments.jsonl", [])
    _write_jsonl(run_dir / "sources.jsonl", source_stats)
    (run_dir / "results.md").write_text(
        _build_results_markdown(
            run_id=run_id,
            selected_brand=brand,
            include_experimental=include_experimental,
            duration_s=time.time() - t0,
            videos=videos,
            source_stats=source_stats,
            warnings=warnings,
        ),
        encoding="utf-8",
    )
    log.info("tiktok_monitor done - videos=%d output=%s", len(videos), run_dir)
    return run_dir


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TikTok monitor based on yt-dlp for Decathlon/Intersport.")
    parser.add_argument("--brand", default="both", choices=["decathlon", "intersport", "both"])
    parser.add_argument("--max-items-per-source", type=int, default=DEFAULT_MAX_ITEMS_PER_SOURCE)
    parser.add_argument("--output-dir", default="data/tiktok_runs")
    parser.add_argument("--include-experimental", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    args = _parse_args()
    run(
        brand=args.brand,
        max_items_per_source=args.max_items_per_source,
        output_dir=args.output_dir,
        include_experimental=args.include_experimental,
        quiet=not args.verbose,
    )


if __name__ == "__main__":
    main()
