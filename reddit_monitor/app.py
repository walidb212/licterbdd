from __future__ import annotations

import asyncio
import sys
import warnings
from pathlib import Path
from typing import Any

from .exporter import build_run_artifacts, export_jsonl
from .models import CandidateLink, MonitorResult
from .parser import parse_post_page, parse_seed_page
from .relevance import is_relevant_post
from .seeds import select_seeds


def _workspace_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_crawl4ai() -> dict[str, Any]:
    clone_root = _workspace_root() / "crawl4ai"
    if not clone_root.exists():
        raise RuntimeError(f"crawl4ai clone not found at {clone_root}")
    if str(clone_root) not in sys.path:
        sys.path.insert(0, str(clone_root))

    warnings.filterwarnings(
        "ignore",
        message=r"urllib3 .* doesn't match a supported version!",
    )

    try:
        from requests import RequestsDependencyWarning

        warnings.filterwarnings("ignore", category=RequestsDependencyWarning)
    except Exception:
        pass

    from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
    from crawl4ai.async_logger import AsyncLogger

    return {
        "AsyncWebCrawler": AsyncWebCrawler,
        "BrowserConfig": BrowserConfig,
        "CacheMode": CacheMode,
        "CrawlerRunConfig": CrawlerRunConfig,
        "AsyncLogger": AsyncLogger,
    }


async def _crawl_html(crawler, CrawlerRunConfig, CacheMode, url: str, debug: bool) -> str:
    config = CrawlerRunConfig(
        wait_for="css:body",
        delay_before_return_html=2,
        page_timeout=45000,
        cache_mode=CacheMode.BYPASS,
        verbose=debug,
    )
    result = await crawler.arun(url, config=config)
    if not getattr(result, "success", False):
        error_message = getattr(result, "error_message", "") or "Unknown crawl error"
        raise RuntimeError(error_message)
    return getattr(result, "html", "") or ""


async def run_monitor(
    *,
    brand: str,
    max_posts_per_seed: int,
    max_comments_per_post: int,
    output_dir: str,
    headless: bool,
    debug: bool,
) -> MonitorResult:
    c4a = _load_crawl4ai()
    artifacts = build_run_artifacts(output_dir)
    warnings: list[str] = []
    seed_reports = []
    posts = []
    comments = []

    AsyncWebCrawler = c4a["AsyncWebCrawler"]
    BrowserConfig = c4a["BrowserConfig"]
    CacheMode = c4a["CacheMode"]
    CrawlerRunConfig = c4a["CrawlerRunConfig"]
    AsyncLogger = c4a["AsyncLogger"]

    browser_config = BrowserConfig(headless=headless, verbose=debug)
    logger = AsyncLogger(verbose=debug)
    selected_seeds = select_seeds(brand)
    unique_links: dict[str, CandidateLink] = {}

    async with AsyncWebCrawler(config=browser_config, logger=logger) as crawler:
        for seed in selected_seeds:
            try:
                html = await _crawl_html(crawler, CrawlerRunConfig, CacheMode, seed.url, debug)
                candidates, report = parse_seed_page(html, seed, max_posts_per_seed)
                for candidate in candidates:
                    if candidate.post_url not in unique_links:
                        unique_links[candidate.post_url] = candidate
                    else:
                        report.duplicate_count += 1
                if report.unique_count == 0 and not report.error:
                    warnings.append(f"Seed {seed.name} produced no usable post URLs.")
            except Exception as exc:
                _, report = parse_seed_page("", seed, max_posts_per_seed)
                report.error = str(exc)
                warnings.append(f"Seed {seed.name} failed: {exc}")
            seed_reports.append(report)

        for candidate in unique_links.values():
            try:
                html = await _crawl_html(crawler, CrawlerRunConfig, CacheMode, candidate.post_url, debug)
                post, extracted_comments = parse_post_page(
                    html=html,
                    run_id=artifacts.run_id,
                    candidate=candidate,
                    max_comments_per_post=max_comments_per_post,
                )
                if post is None:
                    warnings.append(f"Post page had no shreddit-post node: {candidate.post_url}")
                    continue
                if not is_relevant_post(post.post_title, post.post_text, post.subreddit, post.brand_focus):
                    warnings.append(f"Filtered low-relevance thread: {post.post_url}")
                    continue
                posts.append(post)
                comments.extend(extracted_comments)
            except Exception as exc:
                warnings.append(f"Post crawl failed for {candidate.post_url}: {exc}")

    if not posts:
        warnings.append("No relevant Reddit posts were retained after filtering.")

    export_jsonl(artifacts, posts, comments)
    return MonitorResult(
        run_id=artifacts.run_id,
        run_dir=artifacts.run_dir,
        selected_brand=brand,
        seed_reports=seed_reports,
        posts=posts,
        comments=comments,
        warnings=warnings,
    )


def run_monitor_sync(**kwargs) -> MonitorResult:
    return asyncio.run(run_monitor(**kwargs))
