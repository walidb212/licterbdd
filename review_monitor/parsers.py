from __future__ import annotations

import json
import re
from statistics import fmean
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .models import ReviewRecord, SourceConfig, SourceSummary


def _repair_mojibake(value: str) -> str:
    if not value:
        return value
    if not any(token in value for token in ("Ã", "Â", "â", "ð")):
        return value
    try:
        repaired = value.encode("latin1").decode("utf-8")
    except Exception:
        return value
    suspicious_before = sum(value.count(token) for token in ("Ã", "Â", "â", "ð"))
    suspicious_after = sum(repaired.count(token) for token in ("Ã", "Â", "â", "ð"))
    return repaired if suspicious_after < suspicious_before else value


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", _repair_mojibake((value or "").strip()))


def parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    text = str(value).replace(",", ".")
    match = re.search(r"\d+(?:\.\d+)?", text)
    return float(match.group(0)) if match else None


def parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    digits = re.sub(r"[^0-9]", "", str(value))
    return int(digits) if digits else None


def extract_jsonld_nodes(soup: BeautifulSoup) -> list[dict]:
    nodes: list[dict] = []

    def collect(obj):
        if isinstance(obj, list):
            for item in obj:
                collect(item)
            return
        if not isinstance(obj, dict):
            return
        if "@graph" in obj:
            collect(obj["@graph"])
        if "mainEntity" in obj and isinstance(obj["mainEntity"], (list, dict)):
            collect(obj["mainEntity"])
        if "@type" in obj:
            nodes.append(obj)

    for script in soup.select("script[type='application/ld+json']"):
        text = script.get_text() or ""
        if not text.strip():
            continue
        try:
            collect(json.loads(text))
        except Exception:
            continue
    return nodes


def _make_summary(
    run_id: str,
    source: SourceConfig,
    aggregate_rating,
    aggregate_count,
    extracted_reviews,
    *,
    fetch_mode: str = "",
    error: str = "",
) -> SourceSummary:
    return SourceSummary(
        run_id=run_id,
        source_name=source.name,
        site=source.site,
        brand_focus=source.brand_focus,
        review_scope=source.review_scope,
        entity_level=source.entity_level,
        entity_name=source.entity_name,
        source_url=source.url,
        source_symmetry=source.source_symmetry,
        aggregate_rating=aggregate_rating,
        aggregate_count=aggregate_count,
        extracted_reviews=extracted_reviews,
        source_partition=source.review_scope,
        fetch_mode=fetch_mode,
        error=error,
    )


def _build_review(
    *,
    run_id: str,
    source: SourceConfig,
    review_url: str,
    author: str,
    published_at: str,
    experience_date: str,
    rating: float | None,
    aggregate_rating: float | None,
    aggregate_count: int | None,
    title: str,
    body: str,
    language_raw: str = "fr",
    location: str = "",
) -> ReviewRecord:
    return ReviewRecord(
        run_id=run_id,
        site=source.site,
        brand_focus=source.brand_focus,
        review_scope=source.review_scope,
        entity_level=source.entity_level,
        entity_name=source.entity_name,
        location=location,
        source_name=source.name,
        source_url=source.url,
        source_symmetry=source.source_symmetry,
        review_url=review_url,
        author=author,
        published_at=published_at,
        experience_date=experience_date,
        rating=rating,
        aggregate_rating=aggregate_rating,
        aggregate_count=aggregate_count,
        title=title,
        body=body,
        language_raw=language_raw,
        source_partition=source.review_scope,
    )


def _find_aggregate(nodes: list[dict], soup: BeautifulSoup) -> tuple[float | None, int | None]:
    aggregate_rating = None
    aggregate_count = None
    for node in nodes:
        if node.get("@type") == "EmployerAggregateRating":
            aggregate_rating = parse_float(node.get("ratingValue"))
            aggregate_count = parse_int(node.get("ratingCount"))
            return aggregate_rating, aggregate_count
        rating = node.get("aggregateRating") if isinstance(node.get("aggregateRating"), dict) else None
        if rating:
            aggregate_rating = parse_float(rating.get("ratingValue"))
            aggregate_count = parse_int(rating.get("reviewCount") or rating.get("ratingCount"))
            return aggregate_rating, aggregate_count
        if node.get("@type") == "AggregateRating":
            aggregate_rating = parse_float(node.get("ratingValue"))
            aggregate_count = parse_int(node.get("reviewCount") or node.get("ratingCount"))
            return aggregate_rating, aggregate_count
    title_text = clean_text(soup.title.get_text(" ", strip=True) if soup.title else "")
    if aggregate_rating is None:
        aggregate_rating = parse_float(title_text)
    if aggregate_count is None:
        aggregate_count = parse_int(title_text)
    return aggregate_rating, aggregate_count


def _parse_reviews_from_jsonld(
    soup: BeautifulSoup,
    *,
    run_id: str,
    source: SourceConfig,
    aggregate_rating: float | None,
    aggregate_count: int | None,
) -> list[ReviewRecord]:
    nodes = extract_jsonld_nodes(soup)
    reviews: list[ReviewRecord] = []
    seen = set()
    for node in nodes:
        if node.get("@type") != "Review":
            continue
        author_value = node.get("author") or {}
        if isinstance(author_value, dict):
            author = clean_text(author_value.get("name") or "")
        else:
            author = clean_text(str(author_value))
        body = clean_text(node.get("reviewBody") or node.get("description") or "")
        title = clean_text(node.get("name") or node.get("headline") or "")
        published_at = clean_text(node.get("datePublished") or "")
        rating = parse_float(((node.get("reviewRating") or {}).get("ratingValue")) or node.get("ratingValue"))
        key = (author, published_at, title, body)
        if not body or key in seen:
            continue
        seen.add(key)
        reviews.append(
            _build_review(
                run_id=run_id,
                source=source,
                review_url=source.url,
                author=author,
                published_at=published_at,
                experience_date="",
                rating=rating,
                aggregate_rating=aggregate_rating,
                aggregate_count=aggregate_count,
                title=title,
                body=body,
            )
        )
    return reviews


def _text_or_empty(node) -> str:
    return clean_text(node.get_text(" ", strip=True) if node is not None else "")


def _select_first(node, selectors: list[str]) -> str:
    for selector in selectors:
        found = node.select_one(selector)
        text = _text_or_empty(found)
        if text:
            return text
    return ""


def _select_rating(node, selectors: list[str], *, scale: float = 1.0) -> float | None:
    for selector in selectors:
        found = node.select_one(selector)
        if found is None:
            continue
        rating = parse_float(found.get("aria-label") or found.get("title") or found.get_text(" ", strip=True))
        if rating is not None:
            return round(rating * scale, 2)
    return None


def _looks_like_access_challenge(soup: BeautifulSoup) -> bool:
    title_text = clean_text(soup.title.get_text(" ", strip=True) if soup.title else "").lower()
    page_text = clean_text(soup.get_text(" ", strip=True)[:4000]).lower()
    signals = (
        "security check - indeed",
        "just a moment",
        "verify you are human",
        "captcha",
        "datadome",
        "access denied",
        "checking if the site connection is secure",
        "press & hold",
    )
    return any(signal in title_text or signal in page_text for signal in signals)


def _looks_like_coupon_text(*values: str) -> bool:
    haystack = clean_text(" ".join(value or "" for value in values)).lower()
    if not haystack:
        return False
    patterns = (
        "expire le",
        "code promo",
        "réduction",
        "reduction",
        "bon plan",
        "économisez",
        "economisez",
        "% de réduc",
        "% de reduc",
    )
    return any(pattern in haystack for pattern in patterns)


def _parse_dom_cards(
    soup: BeautifulSoup,
    *,
    run_id: str,
    source: SourceConfig,
    aggregate_rating: float | None,
    aggregate_count: int | None,
    card_selectors: list[str],
    title_selectors: list[str],
    body_selectors: list[str],
    author_selectors: list[str],
    date_selectors: list[str],
    rating_selectors: list[str],
    rating_scale: float = 1.0,
) -> list[ReviewRecord]:
    reviews: list[ReviewRecord] = []
    seen = set()
    cards = []
    for selector in card_selectors:
        cards = soup.select(selector)
        if cards:
            break
    for card in cards:
        title = _select_first(card, title_selectors)
        body = _select_first(card, body_selectors)
        author = _select_first(card, author_selectors)
        published_at = _select_first(card, date_selectors)
        rating = _select_rating(card, rating_selectors, scale=rating_scale)
        review_link = source.url
        link_node = card.select_one("a[href]")
        if link_node is not None:
            review_link = urljoin(source.url, link_node.get("href") or source.url)
        key = (author, published_at, title, body)
        if not body or key in seen:
            continue
        seen.add(key)
        reviews.append(
            _build_review(
                run_id=run_id,
                source=source,
                review_url=review_link,
                author=author,
                published_at=published_at,
                experience_date="",
                rating=rating,
                aggregate_rating=aggregate_rating,
                aggregate_count=aggregate_count,
                title=title,
                body=body,
            )
        )
    return reviews


def parse_trustpilot(html: str, run_id: str, source: SourceConfig, *, fetch_mode: str = "") -> tuple[SourceSummary, list[ReviewRecord]]:
    soup = BeautifulSoup(html or "", "html.parser")
    nodes = extract_jsonld_nodes(soup)
    aggregate_rating = None
    aggregate_count = None
    for node in nodes:
        rating = node.get("aggregateRating") if isinstance(node.get("aggregateRating"), dict) else None
        if rating:
            aggregate_rating = parse_float(rating.get("ratingValue"))
            aggregate_count = parse_int(rating.get("reviewCount"))
            break
    if aggregate_count is None:
        for node in nodes:
            if node.get("@type") == "Dataset":
                columns = (((node.get("mainEntity") or {}).get("csvw:tableSchema") or {}).get("csvw:columns") or [])
                total_col = next((col for col in columns if clean_text(col.get("csvw:name") or "").lower() == "total"), None)
                if total_col:
                    cells = total_col.get("csvw:cells") or []
                    if cells:
                        aggregate_count = parse_int(cells[0].get("csvw:value"))
                weighted = []
                for col in columns:
                    stars = parse_int(col.get("csvw:name"))
                    cells = col.get("csvw:cells") or []
                    count = parse_int(cells[0].get("csvw:value")) if cells else None
                    if stars and count:
                        weighted.extend([stars] * count)
                if weighted:
                    aggregate_rating = round(fmean(weighted), 2)
                break

    reviews = []
    seen = set()
    for paragraph in soup.select("p[data-relevant-review-text-typography='true']"):
        article = paragraph.find_parent("article")
        if article is None:
            continue
        body = clean_text(paragraph.get_text(" ", strip=True).replace("Voir plus", ""))
        author_node = article.select_one("[data-consumer-name-typography='true']")
        author = _text_or_empty(author_node)
        time_node = article.select_one("time[data-service-review-date-time-ago='true']")
        published_at = clean_text(time_node.get("datetime") if time_node else "")
        rating_node = article.select_one("img.CDS_StarRating_starRating__614d2e")
        rating = parse_float(rating_node.get("alt") if rating_node else None)
        key = (author, published_at, body)
        if not body or key in seen:
            continue
        seen.add(key)
        reviews.append(
            _build_review(
                run_id=run_id,
                source=source,
                review_url=source.url,
                author=author,
                published_at=published_at,
                experience_date="",
                rating=rating,
                aggregate_rating=aggregate_rating,
                aggregate_count=aggregate_count,
                title="",
                body=body,
            )
        )
    return _make_summary(run_id, source, aggregate_rating, aggregate_count, len(reviews), fetch_mode=fetch_mode), reviews


def parse_custplace(html: str, run_id: str, source: SourceConfig, *, fetch_mode: str = "") -> tuple[SourceSummary, list[ReviewRecord]]:
    soup = BeautifulSoup(html or "", "html.parser")
    nodes = extract_jsonld_nodes(soup)
    aggregate_rating, aggregate_count = _find_aggregate(nodes, soup)
    reviews = []
    seen = set()
    for article in soup.select("article.topic-sample"):
        title_node = article.select_one("h3 a")
        body_node = article.select_one("p.mb-3")
        title = _text_or_empty(title_node)
        body = _text_or_empty(body_node)
        info_spans = article.select("div.flex.items-center.text-xs.text-black span")
        author = ""
        published_at = ""
        for span in info_spans:
            text = clean_text(span.get_text(" ", strip=True))
            if text.startswith("Par "):
                author = text.replace("Par ", "", 1)
            elif not published_at and text.startswith("il y a"):
                published_at = text
        exp_node = article.select_one("div.text-xs.text-black.opacity-60 span")
        experience_date = _text_or_empty(exp_node)
        rating_wrapper = article.select_one("div.aggregateRating")
        rating = None
        if rating_wrapper is not None:
            rating = parse_float(" ".join(rating_wrapper.get("class") or []))
        review_url = urljoin(source.url, title_node.get("href") if title_node else source.url)
        key = (author, published_at, title, body)
        if not body or key in seen:
            continue
        seen.add(key)
        reviews.append(
            _build_review(
                run_id=run_id,
                source=source,
                review_url=review_url,
                author=author,
                published_at=published_at,
                experience_date=experience_date,
                rating=rating,
                aggregate_rating=aggregate_rating,
                aggregate_count=aggregate_count,
                title=title,
                body=body,
            )
        )
    return _make_summary(run_id, source, aggregate_rating, aggregate_count, len(reviews), fetch_mode=fetch_mode), reviews


def parse_glassdoor(html: str, run_id: str, source: SourceConfig, *, fetch_mode: str = "") -> tuple[SourceSummary, list[ReviewRecord]]:
    soup = BeautifulSoup(html or "", "html.parser")
    nodes = extract_jsonld_nodes(soup)
    aggregate_rating, aggregate_count = _find_aggregate(nodes, soup)
    reviews = _parse_reviews_from_jsonld(
        soup,
        run_id=run_id,
        source=source,
        aggregate_rating=aggregate_rating,
        aggregate_count=aggregate_count,
    )
    return _make_summary(run_id, source, aggregate_rating, aggregate_count, len(reviews), fetch_mode=fetch_mode), reviews


def parse_indeed(html: str, run_id: str, source: SourceConfig, *, fetch_mode: str = "") -> tuple[SourceSummary, list[ReviewRecord]]:
    soup = BeautifulSoup(html or "", "html.parser")
    if _looks_like_access_challenge(soup):
        return _make_summary(
            run_id,
            source,
            None,
            None,
            0,
            fetch_mode=fetch_mode,
            error="Access challenge detected on Indeed page.",
        ), []
    nodes = extract_jsonld_nodes(soup)
    aggregate_rating, aggregate_count = _find_aggregate(nodes, soup)
    reviews = _parse_reviews_from_jsonld(
        soup,
        run_id=run_id,
        source=source,
        aggregate_rating=aggregate_rating,
        aggregate_count=aggregate_count,
    )
    if not reviews:
        reviews = _parse_dom_cards(
            soup,
            run_id=run_id,
            source=source,
            aggregate_rating=aggregate_rating,
            aggregate_count=aggregate_count,
            card_selectors=["[data-testid='reviews[]']", "[data-testid='review']", "[data-tn-component='review']", "article", "div[class*='review']"],
            title_selectors=["[data-testid='title']", "h2", "h3", "[data-testid*='title']"],
            body_selectors=["[data-testid='reviewDescription']", "[data-testid='review-text']", "[data-testid*='reviewText']", "div[class*='reviewText']", "p", "span"],
            author_selectors=["[itemprop='author']", "[itemprop='name']", "[data-testid*='author']", "[data-testid*='reviewer']", "span"],
            date_selectors=["[itemprop='datePublished']", "time", "span[class*='date']", "[data-testid*='date']"],
            rating_selectors=["[role='img'][aria-label*='étoile']", "[role='img'][aria-label*='star']", "[aria-label*='star']", "[aria-label*='étoile']", "span[class*='rating']"],
        )
    return _make_summary(run_id, source, aggregate_rating, aggregate_count, len(reviews), fetch_mode=fetch_mode), reviews


def parse_poulpeo(html: str, run_id: str, source: SourceConfig, *, fetch_mode: str = "") -> tuple[SourceSummary, list[ReviewRecord]]:
    soup = BeautifulSoup(html or "", "html.parser")
    if _looks_like_access_challenge(soup):
        return _make_summary(
            run_id,
            source,
            None,
            None,
            0,
            fetch_mode=fetch_mode,
            error="Access challenge detected on Poulpeo page.",
        ), []
    nodes = extract_jsonld_nodes(soup)
    aggregate_rating, aggregate_count = _find_aggregate(nodes, soup)
    if aggregate_rating is not None and aggregate_rating > 5:
        aggregate_rating = None
    reviews = _parse_reviews_from_jsonld(
        soup,
        run_id=run_id,
        source=source,
        aggregate_rating=aggregate_rating,
        aggregate_count=aggregate_count,
    )
    if not reviews:
        reviews = _parse_dom_cards(
            soup,
            run_id=run_id,
            source=source,
            aggregate_rating=aggregate_rating,
            aggregate_count=aggregate_count,
            card_selectors=["article", "li[class*='review']", "div[class*='review']"],
            title_selectors=["h2", "h3", "h4"],
            body_selectors=["p", "div[class*='content']"],
            author_selectors=["[class*='author']", "strong", "span"],
            date_selectors=["time", "[class*='date']", "small"],
            rating_selectors=["[aria-label*='étoile']", "[aria-label*='star']", "[class*='note']"],
        )
    return _make_summary(run_id, source, aggregate_rating, aggregate_count, len(reviews), fetch_mode=fetch_mode), reviews


def parse_ebuyclub(html: str, run_id: str, source: SourceConfig, *, fetch_mode: str = "") -> tuple[SourceSummary, list[ReviewRecord]]:
    soup = BeautifulSoup(html or "", "html.parser")
    nodes = extract_jsonld_nodes(soup)
    aggregate_rating, aggregate_count = _find_aggregate(nodes, soup)
    page_text = clean_text(soup.get_text(" ", strip=True))
    if aggregate_rating is not None and aggregate_rating > 5:
        aggregate_rating = None
    if aggregate_count is None:
        aggregate_count = parse_int(page_text)
    if aggregate_rating is None:
        ten_scale_match = re.search(r"(\d+(?:[.,]\d+)?)\s*/\s*10", page_text)
        if ten_scale_match:
            aggregate_rating = round(float(ten_scale_match.group(1).replace(",", ".")) / 2.0, 2)
    reviews = _parse_reviews_from_jsonld(
        soup,
        run_id=run_id,
        source=source,
        aggregate_rating=aggregate_rating,
        aggregate_count=aggregate_count,
    )
    if not reviews:
        reviews = _parse_dom_cards(
            soup,
            run_id=run_id,
            source=source,
            aggregate_rating=aggregate_rating,
            aggregate_count=aggregate_count,
            card_selectors=["article", "li[class*='review']", "div[class*='review']"],
            title_selectors=["h2", "h3", "h4"],
            body_selectors=["p", "div[class*='content']"],
            author_selectors=["[class*='author']", "strong", "span"],
            date_selectors=["time", "[class*='date']", "small"],
            rating_selectors=["[aria-label*='étoile']", "[aria-label*='star']", "[class*='note']"],
            rating_scale=0.5,
        )
    filtered_reviews: list[ReviewRecord] = []
    for review in reviews:
        author = clean_text(review.author)
        if author in {"%", "€", "$"}:
            continue
        if _looks_like_coupon_text(review.title, review.body, review.published_at):
            continue
        filtered_reviews.append(review)
    return _make_summary(run_id, source, aggregate_rating, aggregate_count, len(filtered_reviews), fetch_mode=fetch_mode), filtered_reviews


def parse_dealabs(html: str, run_id: str, source: SourceConfig, *, fetch_mode: str = "") -> tuple[SourceSummary, list[ReviewRecord]]:
    soup = BeautifulSoup(html or "", "html.parser")
    reviews = _parse_dom_cards(
        soup,
        run_id=run_id,
        source=source,
        aggregate_rating=None,
        aggregate_count=None,
        card_selectors=["article", "div[class*='thread']", "div[data-testid*='thread']"],
        title_selectors=["a[href*='/bons-plans/']", "a[href*='/discussions/']", "h2", "h3"],
        body_selectors=["p", "[class*='description']", "[class*='thread-title']"],
        author_selectors=["[class*='user']", "[class*='author']", "span"],
        date_selectors=["time", "[class*='date']", "small"],
        rating_selectors=[],
    )
    unique = []
    seen = set()
    for review in reviews:
        key = (review.title, review.body)
        if key in seen:
            continue
        if review.author and (len(review.author) > 90 or review.author == review.body):
            review.author = ""
        seen.add(key)
        unique.append(review)
    return _make_summary(run_id, source, None, None, len(unique), fetch_mode=fetch_mode), unique
