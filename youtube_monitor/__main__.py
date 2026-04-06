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

from .config import DEFAULT_DATE_FILTER, DEFAULT_MAX_CHANNEL_SHORTS, DEFAULT_MAX_COMMENTS, DEFAULT_MAX_REPLIES, DEFAULT_SEARCH_RESULTS, OFFICIAL_CHANNELS, SEARCH_QUERIES
from .extractor import CommentRecord, VideoRecord, YouTubeExtractor


def _brand_in_text(raw: dict, brand: str) -> bool:
    """Return True if brand name appears in the video title or description."""
    title = (raw.get("title") or "").lower()
    desc = (raw.get("description") or "").lower()
    return brand.lower() in title or brand.lower() in desc


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("youtube_monitor")


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
    duration_s: float,
    videos: list[VideoRecord],
    comments: list[CommentRecord],
    query_stats: list[dict[str, object]],
    channel_stats: list[dict[str, object]],
) -> str:
    by_brand = Counter(row.brand_focus for row in videos)
    by_pillar = Counter(row.pillar for row in videos)
    lines = [
        f"# youtube_monitor - run `{run_id}`",
        "",
        "## Scope",
        "",
        f"- brand: `{selected_brand}`",
        f"- duration_s: `{duration_s:.1f}`",
        f"- videos: `{len(videos)}`",
        f"- comments: `{len(comments)}`",
        f"- video brands: {', '.join(f'`{name}`={count}' for name, count in sorted(by_brand.items())) or '`none`'}",
        f"- pillars: {', '.join(f'`{name}`={count}' for name, count in sorted(by_pillar.items())) or '`none`'}",
        "",
        "## Search Queries",
        "",
        "| Brand | Query | Pillar | Videos | Comments |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for row in query_stats:
        lines.append(f"| {row['brand']} | {row['name']} | {row['pillar']} | {row['videos']} | {row['comments']} |")
    lines.extend(
        [
            "",
            "## Official Channels",
            "",
            "| Brand | Channel | Pillar | Videos | Comments |",
            "| --- | --- | --- | ---: | ---: |",
        ]
    )
    for row in channel_stats:
        lines.append(f"| {row['brand']} | {row['name']} | {row['pillar']} | {row['videos']} | {row['comments']} |")
    return "\n".join(lines) + "\n"


def run(
    *,
    brand: str = "both",
    max_search_results: int = DEFAULT_SEARCH_RESULTS,
    max_comments: int = DEFAULT_MAX_COMMENTS,
    max_replies: int = DEFAULT_MAX_REPLIES,
    max_channel_videos: int = 20,
    max_channel_shorts: int = DEFAULT_MAX_CHANNEL_SHORTS,
    date_filter: str = DEFAULT_DATE_FILTER,
    output_dir: str = "data/youtube_runs",
    quiet: bool = True,
) -> Path:
    import time

    t0 = time.time()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid.uuid4().hex[:6]
    run_dir = Path(output_dir) / run_id
    brands = ["decathlon", "intersport"] if brand == "both" else [brand]
    extractor = YouTubeExtractor(max_comments=max_comments, max_replies=max_replies, quiet=quiet)
    log.info("date_filter=%s", date_filter or "(none)")

    videos: list[VideoRecord] = []
    comments: list[CommentRecord] = []
    query_stats: list[dict[str, object]] = []
    channel_stats: list[dict[str, object]] = []
    seen_video_ids: set[tuple[str, str]] = set()
    seen_comment_ids: set[tuple[str, str, str]] = set()

    # ── Phase 1: Parallel search queries (no comments) ──
    import subprocess, os
    search_tasks: list[dict] = []
    for brand_focus in brands:
        for query in SEARCH_QUERIES.get(brand_focus, []):
            search_tasks.append({"brand": brand_focus, **query})

    log.info("Launching %d searches in parallel...", len(search_tasks))

    # Run searches sequentially but without comments (fast: ~5s each vs ~40s with comments)
    for task in search_tasks:
        brand_focus = task["brand"]
        log.info("[%s] search - %s (%s)", brand_focus, task["name"], task["query"])
        try:
            raw_videos = extractor.search_videos(task["query"], max_results=max_search_results, date_filter=date_filter)
        except Exception as exc:
            log.warning("Search failed for %s: %s", task["name"], exc)
            raw_videos = []

        added_videos = 0
        skipped_brand = 0
        for raw in raw_videos:
            video_id = str(raw.get("id") or raw.get("display_id") or "")
            if not video_id:
                continue
            if not _brand_in_text(raw, brand_focus):
                skipped_brand += 1
                continue
            video_key = (brand_focus, video_id)
            if video_key not in seen_video_ids:
                videos.append(
                    extractor.normalize_video(
                        raw,
                        run_id=run_id,
                        brand_focus=brand_focus,
                        source_type="search",
                        query_name=task["name"],
                        query_text=task["query"],
                        pillar=task["pillar"],
                    )
                )
                seen_video_ids.add(video_key)
                added_videos += 1
        if skipped_brand:
            log.info("[%s] %s - skipped %d (no brand match)", brand_focus, task["name"], skipped_brand)
        query_stats.append({"brand": brand_focus, "name": task["name"], "pillar": task["pillar"], "videos": added_videos, "comments": 0})

    # ── Phase 2: Fetch comments only for top 10 most relevant videos ──
    top_videos = sorted(videos, key=lambda v: v.view_count + v.like_count * 10, reverse=True)[:10]
    if top_videos:
        log.info("Fetching comments for top %d videos (by engagement)...", len(top_videos))
        for vid in top_videos:
            try:
                raw = extractor.fetch_video_with_comments(vid.video_url)
                if raw:
                    for comment in extractor.normalize_comments(raw, run_id=run_id, brand_focus=vid.brand_focus, pillar=vid.pillar):
                        comment_key = (vid.brand_focus, comment.video_id, comment.comment_id)
                        if not comment.comment_id or comment_key in seen_comment_ids:
                            continue
                        seen_comment_ids.add(comment_key)
                        comments.append(comment)
                    log.info("  [%s] %d comments for '%s'", vid.brand_focus, len([c for c in comments if c.video_id == vid.video_id]), vid.title[:50])
            except Exception as exc:
                log.debug("Comments failed for %s: %s", vid.video_id, exc)

        for channel in OFFICIAL_CHANNELS.get(brand_focus, []):
            # --- Channel videos ---
            log.info("[%s] channel videos - %s", brand_focus, channel["name"])
            try:
                raw_videos = extractor.channel_videos(
                    str(channel["url"]),
                    max_videos=min(max_channel_videos, int(channel["max_videos"])),
                )
            except Exception as exc:
                log.warning("Channel videos failed for %s: %s", channel["name"], exc)
                raw_videos = []

            # --- Channel shorts ---
            log.info("[%s] channel shorts - %s", brand_focus, channel["name"])
            try:
                raw_shorts = extractor.channel_shorts(
                    str(channel["url"]),
                    max_shorts=max_channel_shorts,
                )
            except Exception as exc:
                log.warning("Channel shorts failed for %s: %s", channel["name"], exc)
                raw_shorts = []

            added_videos = 0
            added_comments = 0
            for raw in raw_videos + raw_shorts:
                video_id = str(raw.get("id") or raw.get("display_id") or "")
                if not video_id:
                    continue
                video_key = (brand_focus, video_id)
                if video_key not in seen_video_ids:
                    videos.append(
                        extractor.normalize_video(
                            raw,
                            run_id=run_id,
                            brand_focus=brand_focus,
                            source_type="channel",
                            query_name=str(channel["name"]),
                            query_text=str(channel["url"]),
                            pillar=str(channel["pillar"]),
                        )
                    )
                    seen_video_ids.add(video_key)
                    added_videos += 1
                for comment in extractor.normalize_comments(raw, run_id=run_id, brand_focus=brand_focus, pillar=str(channel["pillar"])):
                    comment_key = (brand_focus, comment.video_id, comment.comment_id)
                    if not comment.comment_id or comment_key in seen_comment_ids:
                        continue
                    seen_comment_ids.add(comment_key)
                    comments.append(comment)
                    added_comments += 1
            channel_stats.append(
                {
                    "brand": brand_focus,
                    "name": channel["name"],
                    "pillar": channel["pillar"],
                    "videos": added_videos,
                    "comments": added_comments,
                }
            )

    _write_jsonl(run_dir / "videos.jsonl", videos)
    _write_jsonl(run_dir / "comments.jsonl", comments)
    (run_dir / "results.md").write_text(
        _build_results_markdown(
            run_id=run_id,
            selected_brand=brand,
            duration_s=time.time() - t0,
            videos=videos,
            comments=comments,
            query_stats=query_stats,
            channel_stats=channel_stats,
        ),
        encoding="utf-8",
    )
    log.info("youtube_monitor done - videos=%d comments=%d output=%s", len(videos), len(comments), run_dir)
    return run_dir


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="YouTube monitor based on yt-dlp for Decathlon/Intersport.")
    parser.add_argument("--brand", default="both", choices=["decathlon", "intersport", "both"])
    parser.add_argument("--max-search-results", type=int, default=DEFAULT_SEARCH_RESULTS)
    parser.add_argument("--max-comments", type=int, default=DEFAULT_MAX_COMMENTS)
    parser.add_argument("--max-replies", type=int, default=DEFAULT_MAX_REPLIES)
    parser.add_argument("--max-channel-videos", type=int, default=20)
    parser.add_argument("--max-channel-shorts", type=int, default=DEFAULT_MAX_CHANNEL_SHORTS)
    parser.add_argument("--date-filter", default=DEFAULT_DATE_FILTER, choices=["", "hour", "today", "week", "month", "year"], help="YouTube upload date filter for searches")
    parser.add_argument("--output-dir", default="data/youtube_runs")
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
        max_search_results=args.max_search_results,
        max_comments=args.max_comments,
        max_replies=args.max_replies,
        max_channel_videos=args.max_channel_videos,
        max_channel_shorts=args.max_channel_shorts,
        date_filter=args.date_filter,
        output_dir=args.output_dir,
        quiet=not args.verbose,
    )


if __name__ == "__main__":
    main()
