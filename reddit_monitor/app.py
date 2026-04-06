"""Reddit monitor — fast JSON API version (no browser needed).

Uses old.reddit.com JSON endpoints instead of crawl4ai.
~400x faster: 10 seconds vs 12 minutes.
"""
from __future__ import annotations

import json
import logging
import time
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .exporter import build_run_artifacts, export_jsonl
from .models import CommentRecord, MonitorResult, PostRecord, SeedReport
from .relevance import is_relevant_post
from .seeds import select_seeds

log = logging.getLogger("reddit_monitor")

USER_AGENT = "LICTER/2.0 (brand monitoring bot; contact: licter@eugenia.school)"
REQUEST_DELAY = 2.0  # Reddit rate limit: ~1 req/2s for non-OAuth


def _fetch_json(url: str, retries: int = 3) -> dict:
    """Fetch JSON from old.reddit.com with retry on 429."""
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode("utf-8", "replace"))
        except urllib.request.HTTPError as exc:
            if exc.code == 429 and attempt < retries - 1:
                wait = (attempt + 1) * 5  # 5s, 10s, 15s
                log.info("  Rate limited, waiting %ds...", wait)
                time.sleep(wait)
            else:
                raise


def _iso_from_utc(ts: float | None) -> str:
    if not ts:
        return ""
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _convert_seed_url_to_json(seed_url: str) -> str:
    """Convert a reddit seed URL to the equivalent old.reddit.com JSON endpoint."""
    url = seed_url.replace("www.reddit.com", "old.reddit.com")
    # Remove trailing slash for clean append
    url = url.rstrip("/")
    # Handle search URLs
    if "/search/" in url or "/search?" in url:
        if ".json" not in url:
            if "?" in url:
                url = url.replace("?", ".json?", 1)
            else:
                url += ".json"
    # Handle subreddit URLs
    elif "/r/" in url and "/search" not in url:
        if ".json" not in url:
            url += "/new.json"
    else:
        if ".json" not in url:
            url += ".json"

    # Add limit
    sep = "&" if "?" in url else "?"
    if "limit=" not in url:
        url += f"{sep}limit=25"

    return url


def _fetch_posts_from_seed(seed, max_posts: int) -> tuple[SeedReport, list[dict]]:
    """Fetch posts from a single seed via JSON API with pagination."""
    report = SeedReport(
        seed_name=seed.name,
        seed_url=seed.url,
        brand_focus=seed.brand_focus,
        seed_type=seed.seed_type,
    )

    json_url = _convert_seed_url_to_json(seed.url)
    log.info("[%s] Fetching %s", seed.name, json_url)

    raw_posts = []
    after = None
    pages = 0
    max_pages = 3  # Max 3 pages × 25 = 75 posts per seed

    while len(raw_posts) < max_posts and pages < max_pages:
        url = json_url
        if after:
            sep = "&" if "?" in url else "?"
            url += f"{sep}after={after}"

        try:
            data = _fetch_json(url)
        except Exception as exc:
            if pages == 0:
                report.error = str(exc)
                log.warning("[%s] Failed: %s", seed.name, exc)
            break

        if not data or "data" not in data:
            break

        children = data.get("data", {}).get("children", [])
        if not children:
            break

        for child in children:
            if child.get("kind") != "t3":
                continue
            raw_posts.append(child["data"])
            if len(raw_posts) >= max_posts:
                break

        report.discovered_count += len(children)
        after = data.get("data", {}).get("after")
        pages += 1

        if not after:
            break
        time.sleep(REQUEST_DELAY)

    report.unique_count = len(raw_posts)
    log.info("[%s] %d posts found (%d pages)", seed.name, len(raw_posts), pages)
    return report, raw_posts


def _fetch_comments(permalink: str, max_comments: int) -> list[dict]:
    """Fetch comments for a post via JSON API."""
    url = f"https://old.reddit.com{permalink}.json?limit={max_comments}"
    try:
        data = _fetch_json(url)
        if not isinstance(data, list) or len(data) < 2:
            return []
        comments = []
        for child in data[1].get("data", {}).get("children", []):
            if child.get("kind") == "t1":
                comments.append(child["data"])
        return comments[:max_comments]
    except Exception as exc:
        log.debug("Comments fetch failed for %s: %s", permalink, exc)
        return []


def _detect_language(text: str) -> str:
    """Simple language detection based on common words."""
    fr_words = {"le", "la", "les", "de", "du", "des", "un", "une", "et", "en", "est", "que", "qui", "pour", "dans", "pas", "sur", "avec", "mais", "ou"}
    words = set(text.lower().split()[:30])
    fr_count = len(words & fr_words)
    return "fr" if fr_count >= 3 else "en"


async def run_monitor(
    *,
    brand: str = "both",
    max_posts_per_seed: int = 25,
    max_comments_per_post: int = 20,
    output_dir: str = "data/reddit_runs",
    headless: bool = True,
    debug: bool = False,
) -> MonitorResult:
    """Run the Reddit monitor using JSON API (no browser)."""
    artifacts = build_run_artifacts(output_dir)
    run_id = artifacts.run_id
    seeds = select_seeds(brand)
    warnings_list: list[str] = []

    all_posts: list[PostRecord] = []
    all_comments: list[CommentRecord] = []
    seed_reports: list[SeedReport] = []
    seen_post_ids: set[str] = set()

    for seed in seeds:
        report, raw_posts = _fetch_posts_from_seed(seed, max_posts_per_seed)
        seed_reports.append(report)

        for raw in raw_posts:
            post_id = raw.get("id", "")
            if post_id in seen_post_ids:
                report.duplicate_count = (report.duplicate_count or 0) + 1
                continue
            seen_post_ids.add(post_id)

            post_url = f"https://www.reddit.com{raw.get('permalink', '')}"
            subreddit = raw.get("subreddit", "")
            title = raw.get("title", "")
            selftext = raw.get("selftext", "")
            author = raw.get("author", "")
            full_text = f"{title} {selftext}".strip()
            lang = _detect_language(full_text)

            post = PostRecord(
                run_id=run_id,
                brand_focus=seed.brand_focus,
                seed_url=seed.url,
                seed_type=seed.seed_type,
                post_url=post_url,
                subreddit=subreddit,
                post_title=title,
                post_text=selftext[:2000],
                author=author,
                created_at=_iso_from_utc(raw.get("created_utc")),
                score=raw.get("score"),
                comment_count=raw.get("num_comments"),
                domain=raw.get("domain", ""),
                language_raw=lang,
                relevance_score=1.0,
            )

            # Check relevance
            if not is_relevant_post(title, selftext, subreddit, seed.brand_focus):
                report.filtered_count = (report.filtered_count or 0) + 1
                continue

            all_posts.append(post)

            # Fetch comments for posts with discussions
            num_comments = raw.get("num_comments", 0)
            if num_comments and num_comments > 0:
                permalink = raw.get("permalink", "")
                if permalink:
                    time.sleep(REQUEST_DELAY)
                    raw_comments = _fetch_comments(permalink, max_comments_per_post)
                    for idx, rc in enumerate(raw_comments):
                        comment_text = rc.get("body", "")
                        if not comment_text or comment_text == "[deleted]" or comment_text == "[removed]":
                            continue
                        all_comments.append(CommentRecord(
                            run_id=run_id,
                            brand_focus=seed.brand_focus,
                            post_url=post_url,
                            subreddit=subreddit,
                            comment_index=idx,
                            comment_author=rc.get("author", ""),
                            comment_text=comment_text[:1000],
                            comment_score_raw=str(rc.get("score", "")),
                            comment_meta_raw={
                                "created": _iso_from_utc(rc.get("created_utc")),
                                "is_submitter": rc.get("is_submitter", False),
                            },
                            language_raw=_detect_language(comment_text),
                        ))

        time.sleep(REQUEST_DELAY)

    # Export
    export_jsonl(artifacts, all_posts, all_comments)

    # Results markdown
    results_md = f"""# reddit_monitor - run `{run_id}`

## Scope
- brand: `{brand}`
- method: `json_api` (no browser)
- posts: `{len(all_posts)}`
- comments: `{len(all_comments)}`
- seeds: `{len(seeds)}`
- dedup_skipped: `{sum(r.duplicate_count or 0 for r in seed_reports)}`

## Seeds
| Seed | Brand | Found | Unique | Filtered | Error |
| --- | --- | ---: | ---: | ---: | --- |
"""
    for r in seed_reports:
        results_md += f"| {r.seed_name} | {r.brand_focus} | {r.discovered_count} | {r.unique_count} | {r.filtered_count or 0} | {r.error or '-'} |\n"

    Path(artifacts.run_dir).joinpath("results.md").write_text(results_md, encoding="utf-8")

    log.info("reddit_monitor done — posts=%d comments=%d (JSON API, no browser)", len(all_posts), len(all_comments))

    return MonitorResult(
        run_id=run_id,
        run_dir=artifacts.run_dir,
        selected_brand=brand,
        seed_reports=seed_reports,
        posts=all_posts,
        comments=all_comments,
        warnings=warnings_list,
    )


def run_monitor_sync(**kwargs) -> MonitorResult:
    """Synchronous wrapper."""
    import asyncio
    return asyncio.run(run_monitor(**kwargs))
