"""News Forums scraper — scrapes sport/consumer forums via search engines."""
from __future__ import annotations

import json
import logging
import re
import time
import urllib.parse
import urllib.request
from typing import Any

from .models import ReviewRecord, SourceSummary

log = logging.getLogger("review_monitor.forums")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
)

# Forums to search
FORUM_DOMAINS = [
    "forum.hardware.fr",
    "forum.doctissimo.fr",
    "forum.quechoisir.org",
    "www.dealabs.com",
    "www.reddit.com",
    "forum.frandroid.com",
    "forum-auto.caradisiac.com",
    "www.commentcamarche.net",
]

SEARCH_QUERIES = {
    "decathlon": [
        "decathlon avis forum",
        "decathlon qualité produit forum",
        "decathlon SAV retour forum",
        "decathlon vélo problème forum",
        "decathlon vs intersport forum",
    ],
    "intersport": [
        "intersport avis forum",
        "intersport qualité forum",
        "intersport SAV retour forum",
    ],
}


def _search_ddg(query: str, max_results: int = 20) -> list[dict]:
    """Search DuckDuckGo for forum posts."""
    try:
        from duckduckgo_search import DDGS
        ddgs = DDGS(timeout=15)
        results = ddgs.text(query, max_results=max_results, backend="auto")
        return [r for r in results if r.get("href")]
    except ImportError:
        log.warning("duckduckgo_search not installed, trying urllib fallback")
        return _search_ddg_html(query, max_results)
    except Exception as exc:
        log.warning("DDG search failed for '%s': %s", query, exc)
        return []


def _search_ddg_html(query: str, max_results: int = 20) -> list[dict]:
    """Fallback: scrape DDG HTML results."""
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", "replace")
        results = []
        for m in re.finditer(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL):
            href = m.group(1)
            title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
            if href and title:
                results.append({"href": href, "title": title, "body": ""})
        return results[:max_results]
    except Exception as exc:
        log.warning("DDG HTML fallback failed: %s", exc)
        return []


def _is_forum_url(url: str) -> bool:
    """Check if URL is from a known forum."""
    return any(domain in url for domain in FORUM_DOMAINS)


def _fetch_page_text(url: str) -> str:
    """Fetch and extract text from a forum page."""
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept-Language": "fr-FR,fr;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", "replace")
        # Strip HTML tags, keep text
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:3000]  # Cap at 3000 chars
    except Exception as exc:
        log.debug("Failed to fetch %s: %s", url, exc)
        return ""


def scrape_forums(
    brand_focus: str,
    run_id: str,
    max_results_per_query: int = 10,
) -> tuple[SourceSummary, list[ReviewRecord]]:
    """Search forums for brand mentions. Returns (summary, records)."""
    queries = SEARCH_QUERIES.get(brand_focus, [])
    source_name = f"forums_{brand_focus}"
    seen_urls: set[str] = set()
    records: list[ReviewRecord] = []

    for query in queries:
        log.info("[%s] Forum search: %s", brand_focus, query)
        results = _search_ddg(query, max_results=max_results_per_query)

        for r in results:
            url = r.get("href", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            title = r.get("title", "")
            snippet = r.get("body", "") or r.get("snippet", "")
            is_forum = _is_forum_url(url)

            # Use snippet as body (don't fetch full page to stay fast)
            body = snippet if snippet else title
            if not body or len(body) < 15:
                continue

            records.append(ReviewRecord(
                run_id=run_id,
                site="forum",
                brand_focus=brand_focus,
                review_scope="community",
                entity_level="brand",
                entity_name=f"{brand_focus.capitalize()} (forums)",
                location="",
                source_name=source_name,
                source_url=url,
                source_symmetry="forum",
                review_url=url,
                author="",
                published_at="",
                experience_date="",
                rating=None,
                aggregate_rating=None,
                aggregate_count=None,
                title=title[:200],
                body=body[:1000],
                language_raw="fr",
                source_partition="community",
            ))

        time.sleep(1)  # Rate limit between queries

    log.info("[%s] Forums: %d records from %d queries", brand_focus, len(records), len(queries))

    summary = SourceSummary(
        run_id=run_id,
        source_name=source_name,
        site="forum",
        brand_focus=brand_focus,
        review_scope="community",
        entity_level="brand",
        entity_name=f"{brand_focus.capitalize()} (forums)",
        source_url="",
        source_symmetry="forum",
        aggregate_rating=None,
        aggregate_count=None,
        extracted_reviews=len(records),
        source_partition="community",
        fetch_mode="ddg_search",
    )

    return summary, records
