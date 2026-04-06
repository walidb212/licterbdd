"""Avis Verifies scraper — parses public review pages."""
from __future__ import annotations

import json
import logging
import re
import urllib.request
from typing import Any

from .models import ReviewRecord, SourceSummary

log = logging.getLogger("review_monitor.avis_verifies")

BRAND_SLUGS = {
    "decathlon": "decathlon.fr",
    "intersport": "intersport.fr",
}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
)


def _fetch_html(url: str) -> str:
    request = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept-Language": "fr-FR,fr;q=0.9",
        "Accept": "text/html,application/xhtml+xml",
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "replace")


def _parse_json_ld(html: str) -> list[dict]:
    """Extract reviews from JSON-LD structured data."""
    reviews = []
    for match in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL):
        try:
            data = json.loads(match.group(1))
            if isinstance(data, dict):
                # AggregateRating
                if "review" in data:
                    for rev in data["review"]:
                        if isinstance(rev, dict):
                            reviews.append(rev)
                # Direct review list
                if "@type" in data and data["@type"] == "Review":
                    reviews.append(data)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type") == "Review":
                        reviews.append(item)
        except (json.JSONDecodeError, TypeError):
            continue
    return reviews


def _parse_html_cards(html: str) -> list[dict]:
    """Fallback: extract reviews from HTML patterns."""
    reviews = []
    # Common patterns for review cards on avis-verifies
    # Look for rating + text patterns
    blocks = re.findall(
        r'(?:data-rating|class="[^"]*rating[^"]*")[^>]*>.*?(\d(?:\.\d)?)\s*/?5.*?'
        r'(?:class="[^"]*(?:review-text|comment|avis-text)[^"]*"[^>]*>)(.*?)</',
        html, re.DOTALL | re.IGNORECASE
    )
    for rating_str, text in blocks:
        text = re.sub(r'<[^>]+>', '', text).strip()
        if len(text) > 10:
            reviews.append({
                "reviewRating": {"ratingValue": float(rating_str)},
                "reviewBody": text,
            })

    # Also try simpler extraction: any div with star rating + text
    for m in re.finditer(r'(\d)\s*(?:étoile|star|/5).*?(?:<p[^>]*>|<div[^>]*>)(.*?)</(?:p|div)>', html, re.DOTALL | re.IGNORECASE):
        text = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        if len(text) > 10 and not any(r.get("reviewBody") == text for r in reviews):
            reviews.append({
                "reviewRating": {"ratingValue": float(m.group(1))},
                "reviewBody": text,
            })

    return reviews


def fetch_avis_verifies(slug: str, max_pages: int = 3) -> tuple[list[dict], float | None, int | None]:
    """Fetch reviews from avis-verifies.com. Returns (reviews, aggregate_rating, aggregate_count)."""
    base_url = f"https://www.avis-verifies.com/avis-clients/{slug}"
    all_reviews: list[dict] = []
    aggregate_rating = None
    aggregate_count = None

    for page in range(1, max_pages + 1):
        url = base_url if page == 1 else f"{base_url}?p={page}"
        log.info("Fetching %s", url)

        try:
            html = _fetch_html(url)
        except Exception as exc:
            log.warning("Avis Verifies fetch failed for %s page %d: %s", slug, page, exc)
            break

        # Try JSON-LD first
        json_reviews = _parse_json_ld(html)
        if json_reviews:
            all_reviews.extend(json_reviews)
        else:
            # Fallback to HTML parsing
            html_reviews = _parse_html_cards(html)
            all_reviews.extend(html_reviews)

        # Extract aggregate rating from page
        if not aggregate_rating:
            agg_match = re.search(r'(?:ratingValue|note\s*(?:moyenne|globale))["\s:]+(\d+(?:\.\d+)?)', html, re.IGNORECASE)
            if agg_match:
                aggregate_rating = float(agg_match.group(1))
            count_match = re.search(r'(?:ratingCount|reviewCount|nombre\s*(?:d\'?avis|avis))["\s:]+(\d+)', html, re.IGNORECASE)
            if count_match:
                aggregate_count = int(count_match.group(1))

        if not json_reviews and not _parse_html_cards(html):
            break  # No more pages

    return all_reviews, aggregate_rating, aggregate_count


def parse_avis_verifies_reviews(
    raw_reviews: list[dict],
    *,
    run_id: str,
    brand_focus: str,
    source_name: str,
    entity_name: str,
    source_url: str,
    aggregate_rating: float | None,
    aggregate_count: int | None,
) -> list[ReviewRecord]:
    """Parse JSON-LD or HTML-extracted reviews into ReviewRecord objects."""
    records = []
    seen_texts = set()

    for rev in raw_reviews:
        try:
            # JSON-LD format
            if "reviewRating" in rev:
                rating_obj = rev["reviewRating"]
                rating = float(rating_obj.get("ratingValue", 0)) if isinstance(rating_obj, dict) else float(rating_obj)
            elif "rating" in rev:
                rating = float(rev["rating"])
            else:
                rating = None

            body = rev.get("reviewBody") or rev.get("description") or rev.get("text") or ""
            body = re.sub(r'<[^>]+>', '', str(body)).strip()

            if not body or len(body) < 5:
                continue

            # Dedup
            body_key = body[:100].lower()
            if body_key in seen_texts:
                continue
            seen_texts.add(body_key)

            author_obj = rev.get("author", {})
            author = author_obj.get("name", "") if isinstance(author_obj, dict) else str(author_obj)

            published = rev.get("datePublished") or rev.get("dateCreated") or ""

            records.append(ReviewRecord(
                run_id=run_id,
                site="avis_verifies",
                brand_focus=brand_focus,
                review_scope="customer",
                entity_level="brand",
                entity_name=entity_name,
                location="",
                source_name=source_name,
                source_url=source_url,
                source_symmetry="common",
                review_url="",
                author=author,
                published_at=published,
                experience_date="",
                rating=rating,
                aggregate_rating=aggregate_rating,
                aggregate_count=aggregate_count,
                title="",
                body=body,
                language_raw="fr",
                source_partition="customer",
            ))
        except Exception as exc:
            log.debug("Skipping avis verifies entry: %s", exc)

    return records


def scrape_avis_verifies(
    brand_focus: str,
    run_id: str,
    max_pages: int = 3,
) -> tuple[SourceSummary, list[ReviewRecord]]:
    """Scrape Avis Verifies for a brand. Returns (summary, reviews)."""
    slug = BRAND_SLUGS.get(brand_focus)
    if not slug:
        log.warning("No Avis Verifies slug for brand %s", brand_focus)
        return _empty_summary(brand_focus, run_id, "no slug configured"), []

    source_name = f"avis_verifies_{brand_focus}"
    entity_name = f"{brand_focus.capitalize()} France"
    source_url = f"https://www.avis-verifies.com/avis-clients/{slug}"

    raw_reviews, aggregate_rating, aggregate_count = fetch_avis_verifies(slug, max_pages=max_pages)
    log.info("[%s] Avis Verifies: %d raw reviews, rating=%s, count=%s", brand_focus, len(raw_reviews), aggregate_rating, aggregate_count)

    records = parse_avis_verifies_reviews(
        raw_reviews,
        run_id=run_id,
        brand_focus=brand_focus,
        source_name=source_name,
        entity_name=entity_name,
        source_url=source_url,
        aggregate_rating=aggregate_rating,
        aggregate_count=aggregate_count,
    )

    summary = SourceSummary(
        run_id=run_id,
        source_name=source_name,
        site="avis_verifies",
        brand_focus=brand_focus,
        review_scope="customer",
        entity_level="brand",
        entity_name=entity_name,
        source_url=source_url,
        source_symmetry="common",
        aggregate_rating=aggregate_rating,
        aggregate_count=aggregate_count,
        extracted_reviews=len(records),
        source_partition="customer",
        fetch_mode="html_scrape",
    )

    return summary, records


def _empty_summary(brand_focus: str, run_id: str, error: str = "") -> SourceSummary:
    return SourceSummary(
        run_id=run_id,
        source_name=f"avis_verifies_{brand_focus}",
        site="avis_verifies",
        brand_focus=brand_focus,
        review_scope="customer",
        entity_level="brand",
        entity_name="",
        source_url="",
        source_symmetry="common",
        aggregate_rating=None,
        aggregate_count=None,
        extracted_reviews=0,
        source_partition="customer",
        fetch_mode="html_scrape",
        error=error,
    )
