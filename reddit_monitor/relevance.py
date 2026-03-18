from __future__ import annotations

import re


BRAND_TOKENS = {
    "decathlon": {"decathlon"},
    "intersport": {"intersport"},
}

RETAIL_CONTEXT = {
    "store",
    "shop",
    "retail",
    "buy",
    "bought",
    "purchase",
    "purchased",
    "return",
    "refund",
    "service",
    "customer",
    "support",
    "seller",
    "gear",
    "product",
    "products",
    "quality",
    "price",
    "pricing",
    "budget",
    "brand",
    "brands",
    "shoe",
    "shoes",
    "bike",
    "bikes",
    "ski",
    "skiing",
    "apparel",
    "clothing",
    "delivery",
    "repair",
    "sportswear",
    "material",
    "equipment",
    "warranty",
    "size",
    "sizing",
}

ATHLETICS_NOISE = {
    "academic decathlon",
    "decathlon event",
    "track and field",
    "track",
    "pole vault",
    "long jump",
    "high jump",
    "javelin",
    "discus",
    "shot put",
    "hurdles",
    "110m",
    "100m",
    "400m",
    "800m",
    "1500m",
    "relay",
    "heptathlon",
    "pentathlon",
    "triathlon",
    "biathlon",
    "athlete",
    "athletics",
    "olympic",
    "scholastic",
}

HARD_EXCLUDE_SUBREDDITS = {
    "academicdecathlon",
    "usacademicdecathlon",
    "biathlon",
    "triathlon",
}


def slug_to_title(slug: str) -> str:
    text = slug.replace("_", " ").replace("-", " ").strip()
    return re.sub(r"\s+", " ", text).strip()


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def detect_brand_focus(text: str, fallback: str) -> str:
    haystack = _normalize_text(text)
    hits = [brand for brand, tokens in BRAND_TOKENS.items() if any(token in haystack for token in tokens)]
    if len(hits) >= 2:
        return "both"
    if len(hits) == 1:
        return hits[0]
    return fallback


def score_candidate_relevance(anchor_text: str, title_hint: str, subreddit_hint: str, url: str) -> float:
    text = _normalize_text(" ".join([anchor_text, title_hint, subreddit_hint, url]))
    raw = 0
    if "/r/decathlon/" in url.lower():
        raw += 3
    if subreddit_hint.lower() in HARD_EXCLUDE_SUBREDDITS:
        raw -= 4
    raw += sum(1 for token in RETAIL_CONTEXT if token in text)
    raw += 2 if "decathlon" in text else 0
    raw += 2 if "intersport" in text else 0
    raw -= sum(2 for token in ATHLETICS_NOISE if token in text)
    normalized = max(0.0, min(1.0, (raw + 2) / 8))
    return round(normalized, 3)


def should_filter_candidate(anchor_text: str, title_hint: str, subreddit_hint: str, url: str) -> bool:
    text = _normalize_text(" ".join([anchor_text, title_hint, subreddit_hint, url]))
    if subreddit_hint.lower() in HARD_EXCLUDE_SUBREDDITS:
        return True
    if "academicdecathlon" in text:
        return True
    if any(token in text for token in ATHLETICS_NOISE) and not any(token in text for token in RETAIL_CONTEXT):
        return True
    return False


def score_post_relevance(title: str, body: str, subreddit: str, brand_focus: str) -> float:
    haystack = _normalize_text(" ".join([title, body, subreddit, brand_focus]))
    title_scope = _normalize_text(" ".join([title, subreddit]))
    raw = 0
    brand_hits = sum(1 for tokens in BRAND_TOKENS.values() if any(token in haystack for token in tokens))
    raw += brand_hits * 2
    if subreddit.lower() == "decathlon":
        raw += 2
    if brand_hits == 0:
        raw -= 3
    elif not any(token in title_scope for tokens in BRAND_TOKENS.values() for token in tokens):
        raw -= 2
    raw += min(sum(1 for token in RETAIL_CONTEXT if token in haystack), 5)
    raw -= min(sum(1 for token in ATHLETICS_NOISE if token in haystack), 4) * 2
    if any(token in haystack for token in {"store", "shop", "service", "return", "quality", "price", "brand"}):
        raw += 1
    normalized = max(0.0, min(1.0, (raw + 2) / 10))
    return round(normalized, 3)


def is_relevant_post(title: str, body: str, subreddit: str, brand_focus: str) -> bool:
    return score_post_relevance(title, body, subreddit, brand_focus) >= 0.35
