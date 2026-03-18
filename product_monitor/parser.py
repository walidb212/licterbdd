from __future__ import annotations

import json
import re
import urllib.parse
from collections import defaultdict

from bs4 import BeautifulSoup

from monitor_core import build_content_hash, normalize_hash_input, repair_mojibake
from review_monitor.parsers import extract_jsonld_nodes, parse_float, parse_int

from .models import ProductCandidate, ProductRecord, ProductReviewRecord


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", repair_mojibake(value or "").strip())


def _is_challenge_page(html: str) -> bool:
    lowered = (html or "").lower()
    return "just a moment" in lowered or "datadome" in lowered or "captcha-delivery.com" in lowered


def extract_product_candidates(html: str, *, brand_focus: str, category: str, source_url: str) -> list[ProductCandidate]:
    if _is_challenge_page(html):
        return []
    soup = BeautifulSoup(html or "", "html.parser")
    candidates: dict[str, ProductCandidate] = {}
    pattern = "/p/" if brand_focus == "decathlon" else "-p-"
    for anchor in soup.select("a[href]"):
        href = anchor.get("href") or ""
        if pattern not in href:
            continue
        product_url = urllib.parse.urljoin(source_url, href)
        text = _clean_text(anchor.get_text(" ", strip=True))
        if not text:
            continue
        card_text = _clean_text(anchor.find_parent().get_text(" ", strip=True) if anchor.find_parent() else text)
        review_count_hint = None
        rating_hint = None
        reviews_match = re.search(r"(\d+)\s+avis", card_text, re.I)
        if reviews_match:
            review_count_hint = int(reviews_match.group(1))
        rating_match = re.search(r"(\d+[.,]\d+)\s*[ée]toiles", card_text, re.I)
        if rating_match:
            rating_hint = float(rating_match.group(1).replace(",", "."))
        current = candidates.get(product_url)
        if current is None or (review_count_hint or 0) > (current.review_count_hint or 0):
            candidates[product_url] = ProductCandidate(
                brand_focus=brand_focus,
                category=category,
                product_url=product_url,
                product_name=text[:220],
                review_count_hint=review_count_hint,
                rating_hint=rating_hint,
                discovery_source=source_url,
            )
    return list(candidates.values())


def pick_balanced_candidates(candidates: list[ProductCandidate], *, max_products_per_brand: int) -> list[ProductCandidate]:
    by_brand_category: dict[tuple[str, str], list[ProductCandidate]] = defaultdict(list)
    for row in candidates:
        by_brand_category[(row.brand_focus, row.category)].append(row)
    for rows in by_brand_category.values():
        rows.sort(key=lambda row: (row.review_count_hint or 0, row.product_name), reverse=True)

    selected: list[ProductCandidate] = []
    selected_urls: set[str] = set()
    target_per_category = max(1, max_products_per_brand // 5)
    brands = sorted({row.brand_focus for row in candidates})
    for brand in brands:
        brand_rows = [row for row in candidates if row.brand_focus == brand]
        categories = sorted({row.category for row in brand_rows})
        for category in categories:
            taken = 0
            for row in by_brand_category[(brand, category)]:
                if row.product_url in selected_urls:
                    continue
                selected.append(row)
                selected_urls.add(row.product_url)
                taken += 1
                if taken >= target_per_category:
                    break
        if sum(1 for row in selected if row.brand_focus == brand) < max_products_per_brand:
            remainder = [
                row
                for row in sorted(brand_rows, key=lambda item: (item.review_count_hint or 0, item.product_name), reverse=True)
                if row.product_url not in selected_urls
            ]
            for row in remainder:
                if sum(1 for existing in selected if existing.brand_focus == brand) >= max_products_per_brand:
                    break
                selected.append(row)
                selected_urls.add(row.product_url)
    return selected


def parse_product_page(
    *,
    run_id: str,
    candidate: ProductCandidate,
    html: str,
    fetch_mode: str,
) -> tuple[ProductRecord, list[ProductReviewRecord], str]:
    if _is_challenge_page(html):
        return (
            ProductRecord(
                run_id=run_id,
                brand_focus=candidate.brand_focus,
                category=candidate.category,
                source_partition="product",
                entity_level="product",
                entity_name=candidate.product_name,
                product_url=candidate.product_url,
                discovery_source=candidate.discovery_source,
                aggregate_rating=None,
                aggregate_count=None,
                rating_hint=candidate.rating_hint,
                review_count_hint=candidate.review_count_hint,
                fetch_mode=fetch_mode,
                status="challenge",
            ),
            [],
            "Product page is protected by an anti-bot challenge.",
        )
    soup = BeautifulSoup(html or "", "html.parser")
    title = _clean_text((soup.select_one("h1") or soup.title).get_text(" ", strip=True) if (soup.select_one("h1") or soup.title) else candidate.product_name)
    aggregate_rating = None
    aggregate_count = None
    for node in extract_jsonld_nodes(soup):
        rating = node.get("aggregateRating") if isinstance(node.get("aggregateRating"), dict) else None
        if rating:
            aggregate_rating = parse_float(rating.get("ratingValue"))
            aggregate_count = parse_int(rating.get("reviewCount") or rating.get("ratingCount"))
            break
        if node.get("@type") == "AggregateRating":
            aggregate_rating = parse_float(node.get("ratingValue"))
            aggregate_count = parse_int(node.get("reviewCount") or node.get("ratingCount"))
            break
    page_text = _clean_text(soup.get_text(" ", strip=True))
    if aggregate_count is None:
        count_match = re.search(r"(\d+)\s+avis", page_text, re.I)
        if count_match:
            aggregate_count = int(count_match.group(1))
    reviews: list[ProductReviewRecord] = []
    seen: set[str] = set()
    for selector in ("article", "[data-bv-show='reviews']", "[class*='review']", "[data-testid*='review']"):
        cards = soup.select(selector)
        if not cards:
            continue
        for card in cards:
            body = _clean_text(" ".join(node.get_text(" ", strip=True) for node in card.select("p, div, span")))
            author = _clean_text((card.select_one("[class*='author'], strong, [itemprop='author']") or card.select_one("span")).get_text(" ", strip=True) if (card.select_one("[class*='author'], strong, [itemprop='author']") or card.select_one("span")) else "")
            if not body or len(body) < 25:
                continue
            body_hash = build_content_hash(author, body)
            if body_hash in seen:
                continue
            seen.add(body_hash)
            title_node = card.select_one("h2, h3, h4")
            title_value = _clean_text(title_node.get_text(" ", strip=True) if title_node else "")
            rating_value = None
            rating_node = card.select_one("[aria-label*='étoile'], [aria-label*='star'], [class*='rating']")
            if rating_node is not None:
                rating_value = parse_float(rating_node.get("aria-label") or rating_node.get_text(" ", strip=True))
            date_node = card.select_one("time, [class*='date']")
            published_at = _clean_text(date_node.get("datetime") if date_node and date_node.get("datetime") else (date_node.get_text(" ", strip=True) if date_node else ""))
            reviews.append(
                ProductReviewRecord(
                    run_id=run_id,
                    brand_focus=candidate.brand_focus,
                    category=candidate.category,
                    source_partition="product",
                    entity_level="product",
                    entity_name=title,
                    product_url=candidate.product_url,
                    author=author,
                    published_at=published_at,
                    rating=rating_value,
                    aggregate_rating=aggregate_rating,
                    aggregate_count=aggregate_count,
                    title=title_value,
                    body=body[:1500],
                )
            )
        if reviews:
            break
    product = ProductRecord(
        run_id=run_id,
        brand_focus=candidate.brand_focus,
        category=candidate.category,
        source_partition="product",
        entity_level="product",
        entity_name=title,
        product_url=candidate.product_url,
        discovery_source=candidate.discovery_source,
        aggregate_rating=aggregate_rating,
        aggregate_count=aggregate_count,
        rating_hint=candidate.rating_hint,
        review_count_hint=candidate.review_count_hint,
        fetch_mode=fetch_mode,
        status="ok" if reviews or aggregate_count or aggregate_rating else "no_reviews_visible",
    )
    return product, reviews, ""
