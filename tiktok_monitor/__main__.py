from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import random
import sys
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .config import DEFAULT_MAX_ITEMS_PER_SOURCE, is_source_enabled, list_sources
from .extractor import CommentRecord, TikTokExtractor, TikTokHashtagScraper, VideoRecord, extract_comments_ytdlp

# DrissionPage fetches ~150+ videos per hashtag (top by relevance).
# We scrape all of them but only keep videos from the last N days.
HASHTAG_SCRAPE_LIMIT = 200  # max raw videos to extract per hashtag
DEFAULT_MAX_AGE_DAYS = 30   # only keep videos published in last 30 days


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
    headless: bool = True,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
) -> Path:
    t0 = time.time()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid.uuid4().hex[:6]
    run_dir = Path(output_dir) / run_id
    extractor = TikTokExtractor(quiet=quiet)

    videos: list[VideoRecord] = []
    all_comments: list[CommentRecord] = []
    source_stats: list[dict[str, object]] = []
    warnings: list[str] = []
    seen_video_ids: set[tuple[str, str]] = set()

    # Separate sources by type
    all_sources = list_sources(brand)
    account_sources = [s for s in all_sources if s.source_type == "account"]
    hashtag_sources = [s for s in all_sources if s.source_type == "hashtag"]

    # --- Phase 1: yt-dlp extraction (official accounts) ---
    for source in account_sources:
        source_brand = source.brand_focus
        enabled_in_run = is_source_enabled(source, include_experimental=include_experimental)
        source_row: dict[str, object] = {
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

        log.info("[%s] account - %s", source_brand, source.name)
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

    # --- Phase 2: DrissionPage hashtag scraping ---
    enabled_hashtags = [s for s in hashtag_sources if is_source_enabled(s, include_experimental=include_experimental)]
    scraper = None

    if enabled_hashtags:
        try:
            scraper = TikTokHashtagScraper(headless=headless)
            scraper.start()

            for i, source in enumerate(enabled_hashtags):
                source_brand = source.brand_focus
                source_row = {
                    "brand": source.brand_focus,
                    "name": source.name,
                    "source_type": source.source_type,
                    "pillar": source.pillar,
                    "production_status": source.production_status,
                    "enabled_in_run": True,
                    "videos": 0,
                    "note": source.coverage_note,
                }

                log.info("[%s] hashtag - #%s", source_brand, source.query_text)
                try:
                    raw_results = scraper.scrape_hashtag(
                        source.query_text, max_items=HASHTAG_SCRAPE_LIMIT,
                    )
                except Exception as exc:
                    warnings.append(f"{source.name} hashtag failed: {exc}")
                    raw_results = []

                # Filter 1: Relevance — video text must mention the keyword
                keyword_lower = source.query_text.lower()
                relevant = []
                for raw in raw_results:
                    text = (raw.get("description") or raw.get("title") or "").lower()
                    hashtags = [h.lower() for h in raw.get("hashtags", [])]
                    if keyword_lower in text or keyword_lower in hashtags:
                        relevant.append(raw)

                # Filter 2: Date — only keep videos from the last max_age_days
                cutoff = datetime.now(timezone.utc).timestamp() - (max_age_days * 86400)
                filtered = []
                for raw in relevant:
                    pub = raw.get("published_at", "")
                    if pub:
                        try:
                            ts = datetime.fromisoformat(pub).timestamp()
                            if ts >= cutoff:
                                filtered.append(raw)
                        except (ValueError, TypeError):
                            filtered.append(raw)
                    else:
                        filtered.append(raw)

                # Sort by most recent first, cap to max_items_per_source
                filtered.sort(key=lambda r: r.get("published_at", ""), reverse=True)
                filtered = filtered[:max_items_per_source]

                log.info("  #%s: %d relevant / %d raw -> %d after %d-day filter",
                         source.query_text, len(relevant), len(raw_results), len(filtered), max_age_days)

                added = 0
                for raw in filtered:
                    video_id = raw.get("video_id", "")
                    if not video_id:
                        continue
                    normalized_brand = source_brand if source_brand != "both" else "both"
                    video_key = (normalized_brand, video_id)
                    if video_key in seen_video_ids:
                        continue
                    seen_video_ids.add(video_key)

                    vid_record = VideoRecord(
                        run_id=run_id,
                        brand_focus=normalized_brand,
                        source_type="hashtag",
                        query_name=source.name,
                        query_text=source.query_text,
                        pillar=source.pillar,
                        production_status=source.production_status,
                        video_id=video_id,
                        video_url=raw.get("video_url", ""),
                        title=(raw.get("title") or "")[:160],
                        description=(raw.get("description") or "")[:2000],
                        author_name=raw.get("author_name", ""),
                        author_id=raw.get("author_id", ""),
                        published_at=raw.get("published_at", ""),
                        duration_seconds=raw.get("duration_seconds", 0),
                        view_count=raw.get("view_count", 0),
                        like_count=raw.get("like_count", 0),
                        comment_count=raw.get("comment_count", 0),
                        repost_count=raw.get("repost_count", 0),
                        save_count=raw.get("save_count", 0),
                        thumbnail_url=raw.get("thumbnail_url", ""),
                    )
                    videos.append(vid_record)
                    added += 1

                # Extract comments from the top videos via yt-dlp
                comment_candidates = sorted(filtered[:added], key=lambda r: r.get("view_count", 0), reverse=True)
                for raw in comment_candidates[:3]:  # top 3 videos per hashtag
                    vid = raw.get("video_id", "")
                    vurl = raw.get("video_url", "")
                    if not vurl:
                        continue
                    try:
                        raw_comments = extract_comments_ytdlp(vurl, vid, max_comments=20, quiet=quiet)
                        for rc in raw_comments:
                            all_comments.append(CommentRecord(
                                run_id=run_id,
                                brand_focus=source_brand if source_brand != "both" else "both",
                                video_id=vid,
                                video_url=vurl,
                                video_title=(raw.get("title") or "")[:160],
                                pillar=source.pillar,
                                comment_id=rc.get("comment_id", ""),
                                parent_id=rc.get("parent_id", ""),
                                author=rc.get("author", ""),
                                text=rc.get("text", ""),
                                published_at=rc.get("published_at", ""),
                                like_count=rc.get("like_count", 0),
                                is_reply=rc.get("is_reply", False),
                            ))
                    except Exception as exc:
                        log.debug("Comment extraction failed for %s: %s", vid, exc)

                if not added:
                    warnings.append(f"{source.name}: no hashtag results found.")
                source_row["videos"] = added
                source_stats.append(source_row)

                # Random pause between hashtags (anti-detection)
                if i < len(enabled_hashtags) - 1:
                    pause = random.uniform(4, 8)
                    log.info("  Pause %.1fs...", pause)
                    time.sleep(pause)

        except Exception as exc:
            warnings.append(f"DrissionPage init failed: {exc}")
            log.warning("TikTok DrissionPage failed: %s", exc)
            for source in enabled_hashtags:
                if not any(s["name"] == source.name for s in source_stats):
                    source_stats.append({
                        "brand": source.brand_focus,
                        "name": source.name,
                        "source_type": source.source_type,
                        "pillar": source.pillar,
                        "production_status": source.production_status,
                        "enabled_in_run": True,
                        "videos": 0,
                        "note": f"Error: {exc}",
                    })
        finally:
            if scraper:
                try:
                    scraper.close()
                except Exception:
                    pass
    else:
        for source in hashtag_sources:
            source_stats.append({
                "brand": source.brand_focus,
                "name": source.name,
                "source_type": source.source_type,
                "pillar": source.pillar,
                "production_status": source.production_status,
                "enabled_in_run": False,
                "videos": 0,
                "note": source.coverage_note,
            })

    _write_jsonl(run_dir / "videos.jsonl", videos)
    _write_jsonl(run_dir / "comments.jsonl", all_comments)
    _write_jsonl(run_dir / "sources.jsonl", source_stats)
    log.info("Comments collected: %d", len(all_comments))
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
    parser = argparse.ArgumentParser(description="TikTok monitor (yt-dlp + DrissionPage) for Decathlon/Intersport.")
    parser.add_argument("--brand", default="both", choices=["decathlon", "intersport", "both"])
    parser.add_argument("--max-items-per-source", type=int, default=DEFAULT_MAX_ITEMS_PER_SOURCE)
    parser.add_argument("--output-dir", default="data/tiktok_runs")
    parser.add_argument("--include-experimental", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--no-headless", action="store_true", help="Show browser window for DrissionPage")
    parser.add_argument("--max-age-days", type=int, default=DEFAULT_MAX_AGE_DAYS, help="Only keep videos from last N days (default 30)")
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
        headless=not args.no_headless,
        max_age_days=args.max_age_days,
    )


if __name__ == "__main__":
    main()
