"""App Store reviews via iTunes RSS API (no auth, no anti-bot)."""
from __future__ import annotations

import json
import logging
import urllib.request
from typing import Any

from .models import ReviewRecord, SourceSummary

log = logging.getLogger("review_monitor.appstore")

# Decathlon & Intersport App IDs on French App Store
APP_IDS = {
    "decathlon": {"id": "1168607403", "name": "Decathlon Shopping"},
    "intersport": {"id": "1579487998", "name": "Intersport App"},
}

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def fetch_appstore_reviews(app_id: str, country: str = "fr", page: int = 1) -> tuple[list[dict], dict | None]:
    """Fetch reviews from iTunes RSS API. Returns (reviews, feed_metadata)."""
    url = f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortBy=mostRecent/json"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8", "replace"))
    except Exception as exc:
        log.warning("App Store fetch failed for %s: %s", app_id, exc)
        return [], None

    feed = data.get("feed", {})
    entries = feed.get("entry", [])

    # First entry is often the app itself, not a review
    reviews = []
    for entry in entries:
        # Skip if no rating (it's the app summary, not a review)
        if "im:rating" not in entry:
            continue
        reviews.append(entry)

    return reviews, feed


def parse_appstore_reviews(
    raw_reviews: list[dict],
    *,
    run_id: str,
    brand_focus: str,
    source_name: str,
    entity_name: str,
    source_url: str,
    aggregate_rating: float | None = None,
    aggregate_count: int | None = None,
) -> list[ReviewRecord]:
    """Parse raw iTunes RSS entries into ReviewRecord objects."""
    records = []
    for entry in raw_reviews:
        try:
            rating = float(entry.get("im:rating", {}).get("label", 0))
            author = entry.get("author", {}).get("name", {}).get("label", "")
            title = entry.get("title", {}).get("label", "")
            body = entry.get("content", {}).get("label", "")
            # Version of the app
            version = entry.get("im:version", {}).get("label", "")
            if version:
                body = f"[v{version}] {body}"

            records.append(ReviewRecord(
                run_id=run_id,
                site="appstore",
                brand_focus=brand_focus,
                review_scope="customer",
                entity_level="brand",
                entity_name=entity_name,
                location="",
                source_name=source_name,
                source_url=source_url,
                source_symmetry="common",
                review_url=entry.get("id", {}).get("label", ""),
                author=author,
                published_at=entry.get("updated", {}).get("label", ""),
                experience_date="",
                rating=rating,
                aggregate_rating=aggregate_rating,
                aggregate_count=aggregate_count,
                title=title,
                body=body,
                language_raw="fr",
                source_partition="customer",
            ))
        except Exception as exc:
            log.debug("Skipping app store entry: %s", exc)
    return records


def scrape_appstore(
    brand_focus: str,
    run_id: str,
    max_pages: int = 3,
) -> tuple[SourceSummary, list[ReviewRecord]]:
    """Scrape App Store reviews for a brand. Returns (summary, reviews)."""
    app_info = APP_IDS.get(brand_focus)
    if not app_info:
        log.warning("No App Store ID for brand %s", brand_focus)
        return _empty_summary(brand_focus, run_id), []

    app_id = app_info["id"]
    entity_name = app_info["name"]
    source_name = f"appstore_{brand_focus}"
    source_url = f"https://apps.apple.com/fr/app/id{app_id}"

    all_reviews: list[dict] = []
    aggregate_rating = None
    aggregate_count = None

    for page in range(1, max_pages + 1):
        log.info("[%s] App Store page %d/%d", brand_focus, page, max_pages)
        reviews, feed = fetch_appstore_reviews(app_id, page=page)
        if not reviews:
            break
        all_reviews.extend(reviews)

        # Extract aggregate info from feed links
        if feed and not aggregate_count:
            for link in feed.get("link", []):
                if isinstance(link, dict) and "attributes" in link:
                    pass  # RSS doesn't expose aggregate easily

    log.info("[%s] App Store: %d reviews fetched", brand_focus, len(all_reviews))

    records = parse_appstore_reviews(
        all_reviews,
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
        site="appstore",
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
        fetch_mode="itunes_rss",
    )

    return summary, records


def _empty_summary(brand_focus: str, run_id: str) -> SourceSummary:
    return SourceSummary(
        run_id=run_id,
        source_name=f"appstore_{brand_focus}",
        site="appstore",
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
        fetch_mode="itunes_rss",
        error="no app id configured",
    )
