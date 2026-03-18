from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
import warnings
from collections import Counter
from pathlib import Path
from typing import Any

from monitor_core import StateStore, build_content_hash, normalize_hash_input, parse_published_at

from .exporter import build_run_artifacts, export_markdown, export_run
from .models import ReviewRecord, RunResult, SourceConfig, SourceSummary
from .parsers import (
    parse_custplace,
    parse_dealabs,
    parse_ebuyclub,
    parse_glassdoor,
    parse_indeed,
    parse_poulpeo,
    parse_trustpilot,
)
from .sources import select_sources


PARSER_BY_SITE = {
    "trustpilot": parse_trustpilot,
    "custplace": parse_custplace,
    "glassdoor": parse_glassdoor,
    "indeed": parse_indeed,
    "poulpeo": parse_poulpeo,
    "ebuyclub": parse_ebuyclub,
    "dealabs": parse_dealabs,
}
CLOUDFLARE_FIRST_SITES = {"trustpilot", "custplace", "ebuyclub", "dealabs"}
MONITOR_NAME = "review_monitor"


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


def _load_wrangler_account_id() -> str:
    command = [r"C:\Users\walid\AppData\Roaming\npm\wrangler.cmd", "whoami"]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    except Exception:
        return ""
    if completed.returncode != 0:
        return ""
    for line in completed.stdout.splitlines():
        if "Account ID" not in line:
            continue
        parts = [part.strip() for part in line.split("│") if part.strip()]
        if parts:
            candidate = parts[-1]
            if len(candidate) == 32:
                return candidate
    return ""


def _resolve_cloudflare_credentials() -> tuple[str, str]:
    token = (
        os.environ.get("CLOUDFLARE_API_TOKEN")
        or os.environ.get("CF_API_TOKEN")
        or os.environ.get("CLOUDFLARE_BROWSER_RENDERING_TOKEN")
        or ""
    ).strip()
    account_id = (
        os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        or os.environ.get("CF_ACCOUNT_ID")
        or _load_wrangler_account_id()
    ).strip()
    return token, account_id


def _fetch_cloudflare_content(url: str, token: str, account_id: str) -> str:
    endpoint = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/browser-rendering/content"
    payload = json.dumps({"url": url}).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        data = json.loads(response.read().decode("utf-8", "replace"))
    result = data.get("result")
    if isinstance(result, str):
        return result
    result = result or {}
    return result.get("content") or result.get("html") or ""


async def _crawl_html(crawler, CrawlerRunConfig, CacheMode, source: SourceConfig, debug: bool) -> str:
    js_code = []
    if source.site == "trustpilot":
        js_code.append(
            "Array.from(document.querySelectorAll('button, div[role=\"button\"], span')).filter(el => /Voir plus/i.test(el.innerText || '')).forEach(el => { try { el.click(); } catch(e) {} });"
        )
    config = CrawlerRunConfig(
        wait_for="css:body",
        delay_before_return_html=3,
        page_timeout=60000,
        cache_mode=CacheMode.BYPASS,
        verbose=debug,
        js_code=js_code or None,
    )
    result = await crawler.arun(source.url, config=config)
    if not getattr(result, "success", False):
        raise RuntimeError(getattr(result, "error_message", "Unknown crawl error") or "Unknown crawl error")
    return getattr(result, "html", "") or ""


async def _fetch_source_html(
    *,
    crawler,
    CrawlerRunConfig,
    CacheMode,
    source: SourceConfig,
    debug: bool,
    warnings_list: list[str],
) -> tuple[str, str]:
    token, account_id = _resolve_cloudflare_credentials()
    if source.site in CLOUDFLARE_FIRST_SITES and token and account_id:
        try:
            html = _fetch_cloudflare_content(source.url, token, account_id)
            if html and len(html) > 200:
                return html, "cloudflare"
            warnings_list.append(f"{source.name}: Cloudflare returned empty content, falling back to crawl4ai.")
        except urllib.error.HTTPError as exc:
            warnings_list.append(f"{source.name}: Cloudflare HTTP {exc.code}, falling back to crawl4ai.")
        except Exception as exc:
            warnings_list.append(f"{source.name}: Cloudflare failed ({exc}), falling back to crawl4ai.")
    html = await _crawl_html(crawler, CrawlerRunConfig, CacheMode, source, debug)
    return html, "crawl4ai"


async def _retry_with_browser_if_needed(
    *,
    crawler,
    CrawlerRunConfig,
    CacheMode,
    source: SourceConfig,
    debug: bool,
    warnings_list: list[str],
    parser,
    run_id: str,
    html: str,
    fetch_mode: str,
    summary: SourceSummary,
    reviews: list[ReviewRecord],
) -> tuple[SourceSummary, list[ReviewRecord]]:
    if fetch_mode != "cloudflare":
        return summary, reviews
    should_retry = summary.extracted_reviews == 0 or bool(summary.error)
    if not should_retry:
        return summary, reviews
    warnings_list.append(f"{source.name}: parsed no usable reviews from Cloudflare content, retrying with crawl4ai.")
    browser_html = await _crawl_html(crawler, CrawlerRunConfig, CacheMode, source, debug)
    retry_summary, retry_reviews = parser(browser_html, run_id, source, fetch_mode="crawl4ai")
    if retry_summary.error:
        warnings_list.append(f"{source.name}: {retry_summary.error}")
    return retry_summary, retry_reviews


def _build_markdown(
    run_id: str,
    selected_brand: str,
    selected_site: str,
    selected_scope: str,
    sources: list[SourceSummary],
    reviews: list[ReviewRecord],
    warnings_list: list[str],
) -> str:
    by_site = Counter(review.site for review in reviews)
    by_brand = Counter(review.brand_focus for review in reviews)
    by_scope = Counter(review.review_scope for review in reviews)
    top_reviews = sorted(reviews, key=lambda review: (review.rating or 0, len(review.body)), reverse=True)[:10]
    lines = [
        f"# Resultats review sites - Run {run_id}",
        "",
        "## Perimetre",
        "",
        f"- brand: `{selected_brand}`",
        f"- site: `{selected_site}`",
        f"- scope: `{selected_scope}`",
        f"- reviews retenues: `{len(reviews)}`",
        f"- sites presents: {', '.join(f'`{site}`={count}' for site, count in sorted(by_site.items())) or '`none`'}",
        f"- repartition marques: {', '.join(f'`{brand}`={count}' for brand, count in sorted(by_brand.items())) or '`none`'}",
        f"- repartition scopes: {', '.join(f'`{scope}`={count}' for scope, count in sorted(by_scope.items())) or '`none`'}",
        "",
        "## Source summary",
        "",
        "| Source | Site | Marque | Scope | Fetch | Note agg. | Volume agg. | Reviews extraites |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: |",
    ]
    for source in sources:
        agg = "-" if source.aggregate_rating is None else f"{source.aggregate_rating:.2f}"
        count = "-" if source.aggregate_count is None else str(source.aggregate_count)
        lines.append(
            f"| {source.source_name} | {source.site} | {source.brand_focus} | {source.review_scope} | {source.fetch_mode or '-'} | {agg} | {count} | {source.extracted_reviews} |"
        )
    lines.extend([
        "",
        "## Exemples de verbatims",
        "",
        "| Site | Marque | Scope | Rating | Auteur | Extrait |",
        "| --- | --- | --- | ---: | --- | --- |",
    ])
    for review in top_reviews:
        excerpt = review.body.replace("|", " ")[:180]
        rating = "-" if review.rating is None else f"{review.rating:.1f}"
        lines.append(f"| {review.site} | {review.brand_focus} | {review.review_scope} | {rating} | {review.author or '-'} | {excerpt} |")
    if warnings_list:
        lines.extend(["", "## Warnings", ""])
        for warning in warnings_list:
            lines.append(f"- {warning}")
    return "\n".join(lines) + "\n"


def _review_entity_key(source: SourceConfig) -> str:
    return normalize_hash_input(source.brand_focus, source.review_scope, source.entity_level, source.entity_name or source.url)


def _review_item_key(review: ReviewRecord) -> str:
    if review.review_url:
        return normalize_hash_input(review.review_url)
    return normalize_hash_input(
        review.source_url,
        review.author,
        review.published_at,
        review.title,
        review.body[:80],
    )


def _apply_incremental_review_filter(
    *,
    state_store: StateStore,
    source: SourceConfig,
    reviews: list[ReviewRecord],
) -> tuple[list[ReviewRecord], int]:
    entity_key = _review_entity_key(source)
    filtered: list[ReviewRecord] = []
    skipped = 0
    watermark = state_store.get_watermark(MONITOR_NAME, source.name, entity_key)
    for review in reviews:
        content_hash = build_content_hash(review.author, review.title, review.body)
        published_at = parse_published_at(review.published_at) or parse_published_at(review.experience_date)
        item_key = _review_item_key(review)
        is_new = state_store.record_item(
            monitor_name=MONITOR_NAME,
            source_name=source.name,
            source_partition=review.source_partition,
            entity_key=entity_key,
            item_key=item_key,
            content_hash=content_hash,
            published_at=published_at,
            metadata={
                "review_url": review.review_url,
                "watermark_at_run_start": watermark or "",
            },
        )
        if not is_new:
            skipped += 1
            continue
        filtered.append(review)
    return filtered, skipped


async def run_monitor(
    *,
    brand: str,
    site: str,
    scope: str,
    output_dir: str,
    incremental: bool,
    state_db: str,
    headless: bool,
    debug: bool,
) -> RunResult:
    c4a = _load_crawl4ai()
    artifacts = build_run_artifacts(output_dir)
    warnings_list: list[str] = []
    source_rows: list[SourceSummary] = []
    review_rows: list[ReviewRecord] = []
    state_store = StateStore(state_db) if incremental else None

    AsyncWebCrawler = c4a["AsyncWebCrawler"]
    BrowserConfig = c4a["BrowserConfig"]
    CacheMode = c4a["CacheMode"]
    CrawlerRunConfig = c4a["CrawlerRunConfig"]
    AsyncLogger = c4a["AsyncLogger"]

    browser_config = BrowserConfig(headless=headless, verbose=debug)
    logger = AsyncLogger(verbose=debug)
    selected_sources = select_sources(site, brand, scope)
    if state_store is not None:
        state_store.log_run_start(
            artifacts.run_id,
            MONITOR_NAME,
            artifacts.run_dir,
            config={"brand": brand, "site": site, "scope": scope, "incremental": incremental},
        )

    try:
        async with AsyncWebCrawler(config=browser_config, logger=logger) as crawler:
            for source in selected_sources:
                parser = PARSER_BY_SITE[source.site]
                try:
                    html, fetch_mode = await _fetch_source_html(
                        crawler=crawler,
                        CrawlerRunConfig=CrawlerRunConfig,
                        CacheMode=CacheMode,
                        source=source,
                        debug=debug,
                        warnings_list=warnings_list,
                    )
                    summary, reviews = parser(html, artifacts.run_id, source, fetch_mode=fetch_mode)
                    summary, reviews = await _retry_with_browser_if_needed(
                        crawler=crawler,
                        CrawlerRunConfig=CrawlerRunConfig,
                        CacheMode=CacheMode,
                        source=source,
                        debug=debug,
                        warnings_list=warnings_list,
                        parser=parser,
                        run_id=artifacts.run_id,
                        html=html,
                        fetch_mode=fetch_mode,
                        summary=summary,
                        reviews=reviews,
                    )
                    if state_store is not None:
                        reviews, skipped = _apply_incremental_review_filter(
                            state_store=state_store,
                            source=source,
                            reviews=reviews,
                        )
                        if skipped:
                            warnings_list.append(f"{source.name}: skipped {skipped} already-seen review rows.")
                    summary.extracted_reviews = len(reviews)
                    summary.source_partition = source.review_scope
                    if summary.error:
                        warnings_list.append(f"{source.name}: {summary.error}")
                    source_rows.append(summary)
                    review_rows.extend(reviews)
                except Exception as exc:
                    warnings_list.append(f"{source.name} failed: {exc}")
                    source_rows.append(
                        SourceSummary(
                            run_id=artifacts.run_id,
                            source_name=source.name,
                            site=source.site,
                            brand_focus=source.brand_focus,
                            review_scope=source.review_scope,
                            entity_level=source.entity_level,
                            entity_name=source.entity_name,
                            source_url=source.url,
                            source_symmetry=source.source_symmetry,
                            aggregate_rating=None,
                            aggregate_count=None,
                            extracted_reviews=0,
                            source_partition=source.review_scope,
                            fetch_mode="",
                            error=str(exc),
                        )
                    )
        export_run(artifacts, source_rows, review_rows)
        export_markdown(
            artifacts,
            _build_markdown(artifacts.run_id, brand, site, scope, source_rows, review_rows, warnings_list),
        )
        if state_store is not None:
            state_store.log_run_end(
                artifacts.run_id,
                status="ok",
                stats={"sources": len(source_rows), "reviews": len(review_rows)},
            )
    except Exception as exc:
        if state_store is not None:
            state_store.log_run_end(artifacts.run_id, status="error", error=str(exc))
            state_store.close()
        raise
    finally:
        if state_store is not None:
            state_store.close()
    return RunResult(
        run_id=artifacts.run_id,
        run_dir=artifacts.run_dir,
        selected_brand=brand,
        selected_site=site,
        selected_scope=scope,
        sources=source_rows,
        reviews=review_rows,
        warnings=warnings_list,
    )


def run_monitor_sync(**kwargs) -> RunResult:
    return asyncio.run(run_monitor(**kwargs))
