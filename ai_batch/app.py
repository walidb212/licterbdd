from __future__ import annotations

import json
import logging
import math
import re
import uuid
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from monitor_core import load_workspace_env, normalize_hash_input, parse_published_at, repair_mojibake, resolve_openai_api_key

from .config import DEFAULT_OPENAI_MODEL, DEFAULT_OPENROUTER_MODEL, PRIMARY_FILES, SOURCE_DIRS
from .models import BatchRunResult, EnrichedRecord, EntitySummaryRecord, PreparedRecord
from .openai_client import OpenAIResponsesClient
from .mistral_client import MistralChatClient
from .openrouter_client import OpenRouterChatClient


log = logging.getLogger("ai_batch")

_NEGATIVE_HINTS = (
    "bad",
    "boycott",
    "broken",
    "complaint",
    "crash",
    "danger",
    "decu",
    "defaut",
    "defect",
    "deplorable",
    "failed",
    "failure",
    "fuite",
    "incident",
    "inefficace",
    "issue",
    "litige",
    "mauvais",
    "nul",
    "panne",
    "poor",
    "problem",
    "retard",
    "risk",
    "risque",
    "scandal",
    "scandale",
    "terrible",
)
_POSITIVE_HINTS = (
    "aimable",
    "bon",
    "excellent",
    "facile",
    "great",
    "heureux",
    "love",
    "parfait",
    "pratique",
    "quality",
    "rapide",
    "recommande",
    "satisf",
    "super",
    "top",
)
_THEME_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("service_client", ("service client", "support", "sav", "customer service", "support client")),
    ("retour_remboursement", ("retour", "remboursement", "refund", "return", "exchange")),
    ("qualite_produit", ("qualite", "quality", "defaut", "defect", "broken", "panne", "durable", "fragile")),
    ("livraison_stock", ("livraison", "delivery", "stock", "indisponible", "rupture", "expedition")),
    ("magasin_experience", ("magasin", "store", "parking", "rayon", "atelier", "boutique")),
    ("prix_promo", ("prix", "promo", "discount", "shopping", "cadeau", "cheap", "cher")),
    ("velo_mobilite", ("velo", "bike", "cycling", "vtt", "airbag", "chambre a air", "snowboard")),
    ("running_fitness", ("running", "marathon", "yoga", "pilate", "fitness", "course")),
    ("football_teamwear", ("football", "foot", "soccer", "maillot", "team")),
    ("brand_controversy", ("boycott", "scandale", "controverse", "russie", "exploit", "calais", "controversy")),
    ("community_engagement", ("community", "communaute", "association", "concours", "giveaway", "followers")),
    ("sponsoring_partnership", ("partenariat", "sponsor", "team", "equipe", "ag2r", "eurosport")),
)
_RISK_THEME_MAP = {
    "service_client": "customer_service_issue",
    "retour_remboursement": "refund_friction",
    "qualite_produit": "product_quality_risk",
    "livraison_stock": "availability_risk",
    "magasin_experience": "store_operations_issue",
    "brand_controversy": "brand_controversy",
    "velo_mobilite": "product_safety_risk",
}
_OPPORTUNITY_THEME_MAP = {
    "community_engagement": "community_momentum",
    "sponsoring_partnership": "brand_visibility_opportunity",
    "prix_promo": "promo_engagement",
    "running_fitness": "sport_category_interest",
    "football_teamwear": "sport_category_interest",
    "velo_mobilite": "product_interest",
}


def _latest_run_dir(base_dir: Path, *, primary_file: str | None = None) -> Path | None:
    if not base_dir.exists():
        return None
    candidates = [row for row in base_dir.iterdir() if row.is_dir()]
    if not candidates:
        return None
    if primary_file:
        non_empty: list[Path] = []
        for candidate in candidates:
            primary_path = candidate / primary_file
            if primary_path.exists() and primary_path.stat().st_size > 0:
                non_empty.append(candidate)
        if non_empty:
            return max(non_empty, key=lambda row: row.stat().st_mtime)
    return max(candidates, key=lambda row: row.stat().st_mtime)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, records: Iterable[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            payload = record
            if hasattr(record, "to_dict"):
                payload = record.to_dict()
            elif hasattr(record, "__dataclass_fields__"):
                payload = asdict(record)
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _clean_text(value: Any) -> str:
    return " ".join(repair_mojibake(str(value or "")).split())


def _normalize_language(raw_language: str, text: str) -> str:
    cleaned = _clean_text(raw_language).lower()
    if cleaned.startswith("fr"):
        return "fr"
    if cleaned.startswith("en"):
        return "en"
    lowered = text.lower()
    if any(token in lowered for token in (" le ", " la ", " les ", " une ", " des ", " pour ", " avec ")):
        return "fr"
    return "en"


def _safe_float(value: Any) -> float | None:
    try:
        if value in ("", None):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _brand_matches(value: str, selected_brand: str) -> bool:
    if selected_brand == "both":
        return True
    return value in {selected_brand, "both"}


def _resolve_run(path_or_none: str | None, key: str, *, input_run: str) -> Path | None:
    if path_or_none:
        return Path(path_or_none)
    if input_run != "latest":
        return None
    return _latest_run_dir(SOURCE_DIRS[key], primary_file=PRIMARY_FILES[key])


def _resolve_input_runs(
    *,
    input_run: str,
    review_run: str | None,
    store_run: str | None,
    product_run: str | None,
    news_run: str | None,
    reddit_run: str | None,
    youtube_run: str | None,
    tiktok_run: str | None,
    x_run: str | None,
    global_run: str | None,
) -> dict[str, Path | None]:
    return {
        "review": _resolve_run(review_run, "review", input_run=input_run),
        "store": _resolve_run(store_run, "store", input_run=input_run),
        "product": _resolve_run(product_run, "product", input_run=input_run),
        "news": _resolve_run(news_run, "news", input_run=input_run),
        "reddit": _resolve_run(reddit_run, "reddit", input_run=input_run),
        "youtube": _resolve_run(youtube_run, "youtube", input_run=input_run),
        "tiktok": _resolve_run(tiktok_run, "tiktok", input_run=input_run),
        "x": _resolve_run(x_run, "x", input_run=input_run),
        "global": _resolve_run(global_run, "global", input_run=input_run),
    }


def _engagement_from_row(row: dict[str, Any]) -> int:
    return sum(
        _safe_int(row.get(name))
        for name in (
            "like_count",
            "comment_count",
            "repost_count",
            "save_count",
            "view_count",
            "likes",
            "share_count",
            "reply_count",
            "quote_count",
        )
    )


def _truncate_text(text: str, *, limit: int = 2000) -> str:
    text = _clean_text(text)
    return text[:limit]


def _prepare_reddit_items(run_dir: Path, selected_brand: str) -> list[PreparedRecord]:
    posts = _read_jsonl(run_dir / "posts.jsonl")
    comments = _read_jsonl(run_dir / "comments.jsonl")
    items: list[PreparedRecord] = []
    for row in posts:
        if not _brand_matches(str(row.get("brand_focus") or ""), selected_brand):
            continue
        item_key = f"reddit_post:{normalize_hash_input(row.get('post_url'), row.get('post_title'))}"
        title = _clean_text(row.get("post_title"))
        body = _truncate_text(" ".join(part for part in [title, _clean_text(row.get("post_text"))] if part))
        items.append(
            PreparedRecord(
                source_run_id=run_dir.name,
                source_name="reddit_post",
                source_partition="social",
                brand_focus=str(row.get("brand_focus") or ""),
                entity_name=_clean_text(row.get("subreddit") or "reddit"),
                item_key=item_key,
                pillar="community",
                published_at=str(row.get("created_at") or ""),
                title=title,
                content_text=body,
                author=_clean_text(row.get("author")),
                source_url=str(row.get("post_url") or row.get("seed_url") or ""),
                raw_language=str(row.get("language_raw") or ""),
                engagement_score=_safe_int(row.get("score")) + _safe_int(row.get("comment_count")),
                metadata={"kind": "post", "domain": row.get("domain", "")},
            )
        )
    for row in comments:
        if not _brand_matches(str(row.get("brand_focus") or ""), selected_brand):
            continue
        item_key = f"reddit_comment:{normalize_hash_input(row.get('post_url'), row.get('comment_index'), row.get('comment_author'))}"
        text = _truncate_text(row.get("comment_text"))
        items.append(
            PreparedRecord(
                source_run_id=run_dir.name,
                source_name="reddit_comment",
                source_partition="social",
                brand_focus=str(row.get("brand_focus") or ""),
                entity_name=_clean_text(row.get("subreddit") or "reddit"),
                item_key=item_key,
                pillar="community",
                published_at=str((row.get("comment_meta_raw") or {}).get("created") or ""),
                title="",
                content_text=text,
                author=_clean_text(row.get("comment_author")),
                source_url=str(row.get("post_url") or ""),
                raw_language=str(row.get("language_raw") or ""),
                engagement_score=_safe_int(row.get("comment_score_raw")),
                metadata={"kind": "comment"},
            )
        )
    return items


def _prepare_youtube_items(run_dir: Path, selected_brand: str) -> list[PreparedRecord]:
    videos = _read_jsonl(run_dir / "videos.jsonl")
    comments = _read_jsonl(run_dir / "comments.jsonl")
    video_lookup = {str(row.get("video_id") or ""): row for row in videos}
    items: list[PreparedRecord] = []
    for row in videos:
        if not _brand_matches(str(row.get("brand_focus") or ""), selected_brand):
            continue
        video_id = str(row.get("video_id") or "")
        items.append(
            PreparedRecord(
                source_run_id=run_dir.name,
                source_name="youtube_video",
                source_partition="social",
                brand_focus=str(row.get("brand_focus") or ""),
                entity_name=_clean_text(row.get("channel_name") or row.get("query_name") or "youtube"),
                item_key=f"youtube_video:{video_id}",
                pillar=str(row.get("pillar") or ""),
                published_at=str(row.get("published_at") or ""),
                title=_clean_text(row.get("title")),
                content_text=_truncate_text(" ".join(part for part in [_clean_text(row.get("title")), _clean_text(row.get("description"))] if part)),
                author=_clean_text(row.get("channel_name")),
                source_url=str(row.get("video_url") or row.get("channel_url") or ""),
                raw_language=str(row.get("language") or ""),
                engagement_score=_engagement_from_row(row),
                metadata={"kind": "video", "query_name": row.get("query_name", "")},
            )
        )
    for row in comments:
        if not _brand_matches(str(row.get("brand_focus") or ""), selected_brand):
            continue
        video_row = video_lookup.get(str(row.get("video_id") or ""), {})
        channel_name = _clean_text(video_row.get("channel_name") or row.get("video_title") or "youtube")
        items.append(
            PreparedRecord(
                source_run_id=run_dir.name,
                source_name="youtube_comment",
                source_partition="social",
                brand_focus=str(row.get("brand_focus") or ""),
                entity_name=channel_name,
                item_key=f"youtube_comment:{normalize_hash_input(row.get('video_id'), row.get('comment_id'))}",
                pillar=str(row.get("pillar") or ""),
                published_at=str(row.get("published_at") or ""),
                title=_clean_text(row.get("video_title")),
                content_text=_truncate_text(row.get("text")),
                author=_clean_text(row.get("author")),
                source_url=str(row.get("video_url") or ""),
                raw_language="",
                engagement_score=_safe_int(row.get("like_count")),
                metadata={"kind": "comment", "is_reply": bool(row.get("is_reply"))},
            )
        )
    return items


def _prepare_tiktok_items(run_dir: Path, selected_brand: str) -> list[PreparedRecord]:
    videos = _read_jsonl(run_dir / "videos.jsonl")
    items: list[PreparedRecord] = []
    for row in videos:
        if not _brand_matches(str(row.get("brand_focus") or ""), selected_brand):
            continue
        items.append(
            PreparedRecord(
                source_run_id=run_dir.name,
                source_name="tiktok_video",
                source_partition="social",
                brand_focus=str(row.get("brand_focus") or ""),
                entity_name=_clean_text(row.get("author_name") or row.get("query_name") or "tiktok"),
                item_key=f"tiktok_video:{normalize_hash_input(row.get('video_id'))}",
                pillar=str(row.get("pillar") or ""),
                published_at=str(row.get("published_at") or ""),
                title=_clean_text(row.get("title")),
                content_text=_truncate_text(" ".join(part for part in [_clean_text(row.get("title")), _clean_text(row.get("description"))] if part)),
                author=_clean_text(row.get("author_name")),
                source_url=str(row.get("video_url") or ""),
                raw_language="",
                engagement_score=_engagement_from_row(row),
                metadata={
                    "kind": "video",
                    "production_status": row.get("production_status", ""),
                    "query_name": row.get("query_name", ""),
                },
            )
        )
    return items


def _prepare_x_items(run_dir: Path, selected_brand: str) -> list[PreparedRecord]:
    tweets = _read_jsonl(run_dir / "tweets_normalized.jsonl")
    items: list[PreparedRecord] = []
    for row in tweets:
        if not _brand_matches(str(row.get("brand_focus") or ""), selected_brand):
            continue
        items.append(
            PreparedRecord(
                source_run_id=run_dir.name,
                source_name="x_post",
                source_partition="social",
                brand_focus=str(row.get("brand_focus") or ""),
                entity_name=_clean_text(row.get("author_handle") or row.get("author_name") or "x"),
                item_key=f"x_post:{normalize_hash_input(row.get('review_id') or row.get('tweet_url'))}",
                pillar="community",
                published_at=str(row.get("date") or ""),
                title="",
                content_text=_truncate_text(row.get("text")),
                author=_clean_text(row.get("author_handle") or row.get("author_name")),
                source_url=str(row.get("tweet_url") or ""),
                raw_language=str(row.get("language") or ""),
                engagement_score=_engagement_from_row(row),
                metadata={"kind": row.get("post_type", "tweet"), "search_type": row.get("search_type", "")},
            )
        )
    return items


def _prepare_review_items_from_rows(run_dir: Path, rows: list[dict[str, Any]], source_name: str, selected_brand: str) -> list[PreparedRecord]:
    items: list[PreparedRecord] = []
    for row in rows:
        if not _brand_matches(str(row.get("brand_focus") or ""), selected_brand):
            continue
        title = _clean_text(row.get("title"))
        body = _clean_text(row.get("body"))
        items.append(
            PreparedRecord(
                source_run_id=run_dir.name,
                source_name=source_name,
                source_partition=str(row.get("source_partition") or "customer"),
                brand_focus=str(row.get("brand_focus") or ""),
                entity_name=_clean_text(row.get("entity_name") or row.get("source_name") or row.get("site") or source_name),
                item_key=f"{source_name}:{normalize_hash_input(row.get('entity_name'), row.get('author'), row.get('published_at') or row.get('date_raw'), title or body[:80])}",
                pillar=str(row.get("review_scope") or ""),
                published_at=str(row.get("published_at") or row.get("date_raw") or ""),
                title=title,
                content_text=_truncate_text(" ".join(part for part in [title, body] if part)),
                author=_clean_text(row.get("author")),
                source_url=str(row.get("source_url") or row.get("product_url") or row.get("google_maps_url") or ""),
                raw_language=str(row.get("language_raw") or ""),
                engagement_score=_safe_int(row.get("aggregate_count")),
                rating=_safe_float(row.get("rating")),
                aggregate_rating=_safe_float(row.get("aggregate_rating")),
                aggregate_count=_safe_int(row.get("aggregate_count")) or None,
                metadata={"site": row.get("site", ""), "entity_level": row.get("entity_level", "")},
            )
        )
    return items


def _prepare_news_items(run_dir: Path, selected_brand: str) -> list[PreparedRecord]:
    articles = _read_jsonl(run_dir / "articles.jsonl")
    items: list[PreparedRecord] = []
    for row in articles:
        if not _brand_matches(str(row.get("brand_focus") or ""), selected_brand):
            continue
        title = _clean_text(row.get("article_title"))
        body = _truncate_text(" ".join(part for part in [title, _clean_text(row.get("description_text"))] if part), limit=1200)
        items.append(
            PreparedRecord(
                source_run_id=run_dir.name,
                source_name="news_article",
                source_partition="news",
                brand_focus=str(row.get("brand_focus") or ""),
                entity_name=_clean_text(row.get("source_name") or row.get("source_domain") or "news"),
                item_key=f"news_article:{normalize_hash_input(row.get('article_id') or row.get('google_news_url'))}",
                pillar=str(row.get("signal_type") or ""),
                published_at=str(row.get("published_at") or ""),
                title=title,
                content_text=body,
                author=_clean_text(row.get("source_name")),
                source_url=str(row.get("google_news_url") or ""),
                raw_language="",
                engagement_score=0,
                metadata={"signal_type": row.get("signal_type", ""), "source_domain": row.get("source_domain", "")},
            )
        )
    return items


def _prepare_excel_items(excel_dir: Path, selected_brand: str) -> tuple[list[PreparedRecord], list[PreparedRecord]]:
    """Normalize the 3 Excel JSONL exports (benchmark_marche, reputation_crise, voix_client_cx) into PreparedRecords."""
    social: list[PreparedRecord] = []
    review: list[PreparedRecord] = []
    source_run_id = "excel_runs"

    def _brand_from_entity(value: str) -> str:
        lowered = (value or "").lower()
        if "intersport" in lowered:
            return "intersport"
        if "decathlon" in lowered:
            return "decathlon"
        return "both"

    def _is_valid_text(text: str) -> bool:
        cleaned = _clean_text(text)
        return bool(cleaned) and len(cleaned.split()) >= 5

    # --- benchmark_marche : mentions comparatives Decathlon vs Intersport ---
    for row in _read_jsonl(excel_dir / "benchmark_marche.jsonl"):
        text = _clean_text(row.get("text"))
        if not _is_valid_text(text):
            continue
        brand_focus = _brand_from_entity(str(row.get("entity_analyzed") or ""))
        if not _brand_matches(brand_focus, selected_brand):
            continue
        item_key = f"excel_benchmark:{normalize_hash_input(row.get('review_id'), text[:80])}"
        engagement = _safe_int(row.get("share_count")) + _safe_int(row.get("reply_count"))
        social.append(PreparedRecord(
            source_run_id=source_run_id,
            source_name="excel_benchmark",
            source_partition="social",
            brand_focus=brand_focus,
            entity_name=_clean_text(row.get("entity_analyzed") or "benchmark"),
            item_key=item_key,
            pillar="benchmark",
            published_at=str(row.get("date") or ""),
            title="",
            content_text=_truncate_text(text),
            author="",
            source_url="",
            raw_language=str(row.get("language") or ""),
            engagement_score=engagement,
            metadata={"topic": row.get("topic"), "platform": row.get("platform"), "is_verified": row.get("is_verified")},
        ))

    # --- reputation_crise : bad buzz vélo 100% Decathlon ---
    for row in _read_jsonl(excel_dir / "reputation_crise.jsonl"):
        text = _clean_text(row.get("text"))
        if not _is_valid_text(text):
            continue
        if not _brand_matches("decathlon", selected_brand):
            continue
        item_key = f"excel_reputation:{normalize_hash_input(row.get('review_id'), text[:80])}"
        likes = _safe_int(row.get("likes"))
        shares = _safe_int(row.get("share_count"))
        followers = _safe_float(row.get("user_followers")) or 0.0
        engagement = likes + shares * 3 + int(followers * 0.01)
        social.append(PreparedRecord(
            source_run_id=source_run_id,
            source_name="excel_reputation",
            source_partition="social",
            brand_focus="decathlon",
            entity_name="reputation_crise",
            item_key=item_key,
            pillar="reputation",
            published_at=str(row.get("date") or ""),
            title="",
            content_text=_truncate_text(text),
            author="",
            source_url="",
            raw_language=str(row.get("language") or ""),
            engagement_score=engagement,
            metadata={"platform": row.get("platform"), "post_type": row.get("post_type"), "is_verified": row.get("is_verified")},
        ))

    # --- voix_client_cx : avis clients Decathlon 1-5★ ---
    for row in _read_jsonl(excel_dir / "voix_client_cx.jsonl"):
        text = _clean_text(row.get("text"))
        if not _is_valid_text(text):
            continue
        if not _brand_matches("decathlon", selected_brand):
            continue
        item_key = f"excel_cx:{normalize_hash_input(row.get('review_id'), text[:80])}"
        rating = _safe_float(row.get("rating"))
        review.append(PreparedRecord(
            source_run_id=source_run_id,
            source_name="excel_cx",
            source_partition="customer",
            brand_focus="decathlon",
            entity_name=_clean_text(str(row.get("platform") or "voix_client")),
            item_key=item_key,
            pillar="cx",
            published_at=str(row.get("date") or ""),
            title="",
            content_text=_truncate_text(text),
            author="",
            source_url="",
            raw_language=str(row.get("language") or ""),
            engagement_score=0,
            rating=rating,
            metadata={"category": row.get("category"), "platform": row.get("platform")},
        ))

    log.info("excel_runs: benchmark=%d reputation=%d cx=%d", sum(1 for r in social if r.source_name == "excel_benchmark"), sum(1 for r in social if r.source_name == "excel_reputation"), len(review))
    return social, review


def _resolve_items(selected_runs: dict[str, Path | None], *, brand: str) -> tuple[list[PreparedRecord], list[PreparedRecord], list[PreparedRecord]]:
    social: list[PreparedRecord] = []
    review: list[PreparedRecord] = []
    news: list[PreparedRecord] = []
    if selected_runs["reddit"]:
        social.extend(_prepare_reddit_items(selected_runs["reddit"], brand))
    if selected_runs["youtube"]:
        social.extend(_prepare_youtube_items(selected_runs["youtube"], brand))
    if selected_runs["tiktok"]:
        social.extend(_prepare_tiktok_items(selected_runs["tiktok"], brand))
    if selected_runs["x"]:
        social.extend(_prepare_x_items(selected_runs["x"], brand))
    if selected_runs["review"]:
        review.extend(_prepare_review_items_from_rows(selected_runs["review"], _read_jsonl(selected_runs["review"] / "reviews.jsonl"), "review_site", brand))
    if selected_runs["store"]:
        review.extend(_prepare_review_items_from_rows(selected_runs["store"], _read_jsonl(selected_runs["store"] / "reviews.jsonl"), "store_review", brand))
    if selected_runs["product"]:
        review.extend(_prepare_review_items_from_rows(selected_runs["product"], _read_jsonl(selected_runs["product"] / "reviews.jsonl"), "product_review", brand))
    if selected_runs["news"]:
        news.extend(_prepare_news_items(selected_runs["news"], brand))
    excel_dir = Path("data/excel_runs")
    if excel_dir.exists():
        excel_social, excel_review = _prepare_excel_items(excel_dir, brand)
        social.extend(excel_social)
        review.extend(excel_review)
    return social, review, news


def _split_sentences(text: str) -> list[str]:
    cleaned = _clean_text(text)
    if not cleaned:
        return []
    return [chunk.strip() for chunk in re.split(r"(?<=[.!?])\s+", cleaned) if chunk.strip()]


def _extract_themes(text: str) -> list[str]:
    lowered = f" {repair_mojibake(text).lower()} "
    themes = [name for name, keywords in _THEME_RULES if any(keyword in lowered for keyword in keywords)]
    if not themes:
        themes.append("general_brand_signal")
    return themes[:5]


def _score_sentiment(text: str, rating: float | None) -> tuple[str, float]:
    if rating is not None:
        if rating <= 2:
            return "negative", 0.95
        if rating >= 4:
            return "positive", 0.95
        return "neutral", 0.75
    lowered = repair_mojibake(text).lower()
    negative = sum(1 for token in _NEGATIVE_HINTS if token in lowered)
    positive = sum(1 for token in _POSITIVE_HINTS if token in lowered)
    if negative and positive:
        return "mixed", min(0.9, 0.55 + (negative + positive) * 0.05)
    if negative:
        return "negative", min(0.9, 0.55 + negative * 0.07)
    if positive:
        return "positive", min(0.9, 0.55 + positive * 0.07)
    return "neutral", 0.55


def _risk_flags(themes: list[str], sentiment_label: str) -> list[str]:
    if sentiment_label not in {"negative", "mixed"}:
        return []
    flags = [_RISK_THEME_MAP[theme] for theme in themes if theme in _RISK_THEME_MAP]
    if not flags and sentiment_label == "negative":
        flags.append("general_reputation_risk")
    return list(dict.fromkeys(flags))[:5]


def _opportunity_flags(themes: list[str], sentiment_label: str) -> list[str]:
    if sentiment_label not in {"positive", "mixed", "neutral"}:
        return []
    flags = [_OPPORTUNITY_THEME_MAP[theme] for theme in themes if theme in _OPPORTUNITY_THEME_MAP]
    return list(dict.fromkeys(flags))[:5]


def _priority_score(record: PreparedRecord, sentiment_label: str, themes: list[str], risks: list[str]) -> int:
    score = 15
    if sentiment_label == "negative":
        score += 35
    elif sentiment_label == "mixed":
        score += 30
    elif sentiment_label == "positive":
        score += 20
    else:
        score += 12
    if record.rating is not None:
        score += max(0, int((3.5 - record.rating) * 12))
    if risks:
        score += 10
    if "brand_controversy" in themes:
        score += 15
    score += min(25, int(math.log1p(max(record.engagement_score, 0)) * 5))
    if record.brand_focus == "both":
        score += 5
    return max(0, min(100, score))


def _summary_short(record: PreparedRecord) -> str:
    base = " ".join(part for part in [record.title, record.content_text] if part).strip()
    if not base:
        return ""
    return base[:220]


def _evidence_spans(record: PreparedRecord, themes: list[str]) -> list[str]:
    sentences = _split_sentences(record.content_text or record.title)
    if not sentences:
        return []
    picks: list[str] = []
    keyword_map = dict(_THEME_RULES)
    lowered_sentences = [(sentence, sentence.lower()) for sentence in sentences]
    for theme in themes:
        for sentence, lowered in lowered_sentences:
            if any(keyword in lowered for keyword in keyword_map.get(theme, ())):
                candidate = sentence[:140]
                if candidate not in picks:
                    picks.append(candidate)
                break
        if len(picks) >= 3:
            break
    if not picks:
        picks = [sentence[:140] for sentence in sentences[:2]]
    return picks[:3]


def _heuristic_enrichment(record: PreparedRecord, *, run_id: str, provider: str, model: str) -> EnrichedRecord:
    language = _normalize_language(record.raw_language, record.content_text or record.title)
    combined = " ".join(part for part in [record.title, record.content_text] if part)
    sentiment_label, sentiment_confidence = _score_sentiment(combined, record.rating)
    themes = _extract_themes(combined)
    risks = _risk_flags(themes, sentiment_label)
    opportunities = _opportunity_flags(themes, sentiment_label)
    return EnrichedRecord(
        run_id=run_id,
        source_run_id=record.source_run_id,
        source_partition=record.source_partition,
        brand_focus=record.brand_focus,
        entity_name=record.entity_name,
        item_key=record.item_key,
        language=language,
        sentiment_label=sentiment_label,
        sentiment_confidence=round(sentiment_confidence, 3),
        themes=themes,
        risk_flags=risks,
        opportunity_flags=opportunities,
        priority_score=_priority_score(record, sentiment_label, themes, risks),
        summary_short=_summary_short(record),
        evidence_spans=_evidence_spans(record, themes),
        pillar=record.pillar,
        source_name=record.source_name,
        published_at=record.published_at,
        provider=provider,
        model=model,
    )


_BATCH_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "item_key": {"type": "string"},
                    "language": {"type": "string"},
                    "sentiment_label": {"type": "string", "enum": ["positive", "neutral", "negative", "mixed"]},
                    "sentiment_confidence": {"type": "number"},
                    "themes": {"type": "array", "items": {"type": "string"}},
                    "risk_flags": {"type": "array", "items": {"type": "string"}},
                    "opportunity_flags": {"type": "array", "items": {"type": "string"}},
                    "priority_score": {"type": "integer"},
                    "summary_short": {"type": "string"},
                    "evidence_spans": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "item_key",
                    "language",
                    "sentiment_label",
                    "sentiment_confidence",
                    "themes",
                    "risk_flags",
                    "opportunity_flags",
                    "priority_score",
                    "summary_short",
                    "evidence_spans",
                ],
            },
        }
    },
    "required": ["items"],
}


def _chunk_records(records: list[PreparedRecord], chunk_size: int) -> list[list[PreparedRecord]]:
    if chunk_size <= 0:
        return [records]
    return [records[index : index + chunk_size] for index in range(0, len(records), chunk_size)]


def _openai_instructions(partition_name: str) -> str:
    return (
        "You enrich brand-monitoring records for Decathlon and Intersport.\n"
        "Work item by item.\n"
        f"Current partition: {partition_name}.\n"
        "Do not mix source partitions or infer customer satisfaction from social awareness.\n"
        "Return short lowercase snake_case themes and flags.\n"
        "Use only evidence from the provided record.\n"
        "Keep summaries concise and factual.\n"
    )


def _openai_user_text(partition_name: str, records: list[PreparedRecord]) -> str:
    payload = {
        "partition": partition_name,
        "items": [record.to_prompt_payload() for record in records],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _coerce_openai_item(
    item: dict[str, Any],
    *,
    record_lookup: dict[str, PreparedRecord],
    run_id: str,
    provider: str,
    model: str,
) -> EnrichedRecord | None:
    item_key = str(item.get("item_key") or "")
    record = record_lookup.get(item_key)
    # Fuzzy match: LLMs sometimes truncate or slightly modify item_keys
    if record is None and item_key:
        for candidate_key, candidate_record in record_lookup.items():
            if candidate_key.startswith(item_key[:40]) or item_key.startswith(candidate_key[:40]):
                record = candidate_record
                break
    if record is None:
        return None
    language = _normalize_language(str(item.get("language") or record.raw_language or ""), record.content_text)
    sentiment_label = str(item.get("sentiment_label") or "neutral")
    if sentiment_label not in {"positive", "neutral", "negative", "mixed"}:
        sentiment_label = "neutral"
    themes = [str(value).strip() for value in item.get("themes") or [] if str(value).strip()][:5]
    if not themes:
        themes = _extract_themes(record.content_text)
    risks = [str(value).strip() for value in item.get("risk_flags") or [] if str(value).strip()][:5]
    opportunities = [str(value).strip() for value in item.get("opportunity_flags") or [] if str(value).strip()][:5]
    priority_score = _safe_int(item.get("priority_score"))
    if not priority_score:
        priority_score = _priority_score(record, sentiment_label, themes, risks)
    evidence_spans = [str(value).strip() for value in item.get("evidence_spans") or [] if str(value).strip()][:3]
    if not evidence_spans:
        evidence_spans = _evidence_spans(record, themes)
    return EnrichedRecord(
        run_id=run_id,
        source_run_id=record.source_run_id,
        source_partition=record.source_partition,
        brand_focus=record.brand_focus,
        entity_name=record.entity_name,
        item_key=record.item_key,
        language=language,
        sentiment_label=sentiment_label,
        sentiment_confidence=round(float(item.get("sentiment_confidence") or 0.5), 3),
        themes=themes,
        risk_flags=risks,
        opportunity_flags=opportunities,
        priority_score=max(0, min(100, priority_score)),
        summary_short=_clean_text(item.get("summary_short"))[:220] or _summary_short(record),
        evidence_spans=evidence_spans,
        pillar=record.pillar,
        source_name=record.source_name,
        published_at=record.published_at,
        provider=provider,
        model=model,
    )


def _enrich_with_openai(
    *,
    client: OpenAIResponsesClient,
    records: list[PreparedRecord],
    partition_name: str,
    run_id: str,
    model: str,
    chunk_size: int,
    background_threshold: int,
    warnings: list[str],
) -> list[EnrichedRecord]:
    enriched: list[EnrichedRecord] = []
    for chunk in _chunk_records(records, chunk_size):
        payload = client.create_structured_response(
            instructions=_openai_instructions(partition_name),
            user_text=_openai_user_text(partition_name, chunk),
            schema_name=f"{partition_name}_enrichment_batch",
            schema=_BATCH_SCHEMA,
            background=len(chunk) >= background_threshold,
        )
        if payload.get("status") in {"queued", "in_progress"}:
            response_id = str(payload.get("id") or "")
            if not response_id:
                raise RuntimeError("OpenAI background response missing id")
            payload = client.wait_for_response(response_id)
        if payload.get("status") not in {"completed", None, ""} and payload.get("error"):
            raise RuntimeError(str(payload.get("error")))
        raw_text = client.extract_output_text(payload)
        parsed = json.loads(raw_text) if raw_text else {"items": []}
        record_lookup = {row.item_key: row for row in chunk}
        chunk_enriched: list[EnrichedRecord] = []
        for item in parsed.get("items") or []:
            if not isinstance(item, dict):
                continue
            enriched_row = _coerce_openai_item(item, record_lookup=record_lookup, run_id=run_id, provider="openai", model=model)
            if enriched_row is not None:
                chunk_enriched.append(enriched_row)
        seen_keys = {row.item_key for row in chunk_enriched}
        for record in chunk:
            if record.item_key not in seen_keys:
                warnings.append(f"{partition_name}: missing OpenAI item for {record.item_key}, using heuristic fallback.")
                chunk_enriched.append(_heuristic_enrichment(record, run_id=run_id, provider="heuristic_fallback", model=model))
        enriched.extend(chunk_enriched)
    return enriched


def _enrich_partition(
    *,
    records: list[PreparedRecord],
    partition_name: str,
    run_id: str,
    provider: str,
    model: str,
    chunk_size: int,
    background_threshold: int,
    strict_openai: bool,
    warnings: list[str],
) -> list[EnrichedRecord]:
    if not records:
        return []

    # --- Mistral branch ---
    if provider == "mistral":
        import os as _os
        mistral_key = _os.environ.get("MISTRAL_API_KEY", "")
        mistral_model = _os.environ.get("MISTRAL_MODEL") or model or "mistral-small-latest"
        if not mistral_key:
            message = "MISTRAL_API_KEY is missing. Falling back to heuristic enrichment."
            warnings.append(message)
        else:
            mistral_client = MistralChatClient(api_key=mistral_key, model=mistral_model)
            try:
                return _enrich_with_openai(
                    client=mistral_client,
                    records=records,
                    partition_name=partition_name,
                    run_id=run_id,
                    model=mistral_model,
                    chunk_size=chunk_size,
                    background_threshold=background_threshold,
                    warnings=warnings,
                )
            except Exception as exc:
                warnings.append(f"{partition_name}: Mistral enrichment failed ({exc}), using heuristic fallback.")

    # --- OpenRouter branch ---
    if provider == "openrouter":
        import os as _os
        openrouter_key = _os.environ.get("OPENROUTER_API_KEY", "")
        openrouter_model = _os.environ.get("OPENROUTER_MODEL") or model
        if not openrouter_key:
            message = "OPENROUTER_API_KEY is missing. Falling back to heuristic enrichment."
            warnings.append(message)
        else:
            openrouter_client = OpenRouterChatClient(api_key=openrouter_key, model=openrouter_model)
            try:
                return _enrich_with_openai(
                    client=openrouter_client,
                    records=records,
                    partition_name=partition_name,
                    run_id=run_id,
                    model=openrouter_model,
                    chunk_size=chunk_size,
                    background_threshold=background_threshold,
                    warnings=warnings,
                )
            except Exception as exc:
                warnings.append(f"{partition_name}: OpenRouter enrichment failed ({exc}), using heuristic fallback.")

    # --- OpenAI branch ---
    api_key = resolve_openai_api_key()
    use_openai = provider == "openai" or (provider == "auto" and api_key)
    if use_openai and not api_key:
        message = "OPENAI_API_KEY is missing. Falling back to heuristic enrichment."
        if strict_openai:
            raise RuntimeError(message)
        warnings.append(message)
        use_openai = False

    if use_openai:
        client = OpenAIResponsesClient(api_key=api_key, model=model)
        try:
            return _enrich_with_openai(
                client=client,
                records=records,
                partition_name=partition_name,
                run_id=run_id,
                model=model,
                chunk_size=chunk_size,
                background_threshold=background_threshold,
                warnings=warnings,
            )
        except Exception as exc:
            if strict_openai or provider == "openai":
                raise
            warnings.append(f"{partition_name}: OpenAI enrichment failed ({exc}), using heuristic fallback.")

    provider_name = "heuristic"
    if provider == "auto" and api_key:
        provider_name = "heuristic_fallback"
    return [_heuristic_enrichment(record, run_id=run_id, provider=provider_name, model=model) for record in records]


def _build_entity_summaries(records: list[EnrichedRecord]) -> list[EntitySummaryRecord]:
    grouped: dict[tuple[str, str, str], list[EnrichedRecord]] = defaultdict(list)
    for record in records:
        grouped[(record.brand_focus, record.source_partition, record.entity_name)].append(record)

    summaries: list[EntitySummaryRecord] = []
    for (brand_focus, source_partition, entity_name), group in sorted(grouped.items()):
        published_dates = [parse_published_at(row.published_at) for row in group if row.published_at]
        normalized_dates = [value for value in published_dates if value]
        theme_counter = Counter(theme for row in group for theme in row.themes)
        risk_counter = Counter(flag for row in group for flag in row.risk_flags)
        opp_counter = Counter(flag for row in group for flag in row.opportunity_flags)
        sentiment_counter = Counter(row.sentiment_label for row in group)
        dominant_sentiment = sentiment_counter.most_common(1)[0][0] if sentiment_counter else "neutral"
        top_themes = [name for name, _ in theme_counter.most_common(5)]
        top_risks = [name for name, _ in risk_counter.most_common(5)]
        top_opportunities = [name for name, _ in opp_counter.most_common(5)]
        takeaway_parts = [f"{len(group)} items, dominant sentiment {dominant_sentiment}."]
        if top_risks:
            takeaway_parts.append(f"Main risks: {', '.join(top_risks[:3])}.")
        if top_opportunities:
            takeaway_parts.append(f"Main opportunities: {', '.join(top_opportunities[:3])}.")
        if top_themes:
            takeaway_parts.append(f"Top themes: {', '.join(top_themes[:3])}.")
        summaries.append(
            EntitySummaryRecord(
                brand_focus=brand_focus,
                source_partition=source_partition,
                entity_name=entity_name,
                period_start=min(normalized_dates) if normalized_dates else "",
                period_end=max(normalized_dates) if normalized_dates else "",
                volume_items=len(group),
                top_themes=top_themes,
                top_risks=top_risks,
                top_opportunities=top_opportunities,
                executive_takeaway=" ".join(takeaway_parts),
            )
        )
    return summaries


def _build_executive_summary(
    *,
    run_id: str,
    input_runs: dict[str, Path | None],
    provider: str,
    model: str,
    social_records: list[EnrichedRecord],
    review_records: list[EnrichedRecord],
    news_records: list[EnrichedRecord],
    entity_summaries: list[EntitySummaryRecord],
) -> str:
    partition_totals = {
        "social": len(social_records),
        "review": len(review_records),
        "news": len(news_records),
    }
    all_records = social_records + review_records + news_records
    overall_risks = Counter(flag for row in all_records for flag in row.risk_flags)
    overall_opps = Counter(flag for row in all_records for flag in row.opportunity_flags)
    by_brand = Counter(row.brand_focus for row in all_records)
    highest_priority = sorted(all_records, key=lambda row: row.priority_score, reverse=True)[:8]
    lines = [
        f"# AI batch enrichment - {run_id}",
        "",
        "## Execution",
        "",
        f"- provider: `{provider}`",
        f"- model: `{model}`",
        f"- social records: `{partition_totals['social']}`",
        f"- review records: `{partition_totals['review']}`",
        f"- news records: `{partition_totals['news']}`",
        f"- entities summarized: `{len(entity_summaries)}`",
        f"- brand distribution: {', '.join(f'`{brand}`={count}' for brand, count in sorted(by_brand.items())) or '`none`'}",
        "",
        "## Input runs",
        "",
    ]
    for name, path in input_runs.items():
        lines.append(f"- {name}: `{path}`" if path else f"- {name}: non disponible")
    lines.extend(
        [
            "",
            "## Cross-source watchouts",
            "",
            f"- Top risks: {', '.join(f'`{name}`={count}' for name, count in overall_risks.most_common(6)) or '`none`'}",
            f"- Top opportunities: {', '.join(f'`{name}`={count}' for name, count in overall_opps.most_common(6)) or '`none`'}",
            "",
            "## Highest-priority items",
            "",
            "| Partition | Brand | Entity | Priority | Sentiment | Summary |",
            "| --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in highest_priority:
        lines.append(
            f"| {row.source_partition} | {row.brand_focus} | {row.entity_name.replace('|', ' ')[:60]} | {row.priority_score} | {row.sentiment_label} | {row.summary_short.replace('|', ' ')[:180]} |"
        )
    lines.extend(["", "## Entity takeaways", ""])
    for summary in sorted(entity_summaries, key=lambda row: (-row.volume_items, row.brand_focus, row.entity_name))[:20]:
        lines.append(
            f"- `{summary.brand_focus}` / `{summary.source_partition}` / `{summary.entity_name}`: {summary.executive_takeaway}"
        )
    global_run = input_runs.get("global")
    if global_run and (global_run / "global_summary.md").exists():
        excerpt = (global_run / "global_summary.md").read_text(encoding="utf-8")[:1200].strip()
        lines.extend(["", "## Global Summary Context", "", excerpt])
    return "\n".join(lines) + "\n"


def run_batch_sync(
    *,
    brand: str = "both",
    input_run: str = "latest",
    output_dir: str = "data/ai_runs",
    provider: str = "auto",
    model: str = DEFAULT_OPENAI_MODEL,
    chunk_size: int = 8,
    background_threshold: int = 12,
    strict_openai: bool = False,
    review_run: str | None = None,
    store_run: str | None = None,
    product_run: str | None = None,
    news_run: str | None = None,
    reddit_run: str | None = None,
    youtube_run: str | None = None,
    tiktok_run: str | None = None,
    x_run: str | None = None,
    global_run: str | None = None,
) -> BatchRunResult:
    load_workspace_env(Path(__file__).resolve().parent.parent)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid.uuid4().hex[:6]
    run_dir = Path(output_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []

    selected_runs = _resolve_input_runs(
        input_run=input_run,
        review_run=review_run,
        store_run=store_run,
        product_run=product_run,
        news_run=news_run,
        reddit_run=reddit_run,
        youtube_run=youtube_run,
        tiktok_run=tiktok_run,
        x_run=x_run,
        global_run=global_run,
    )
    social_items, review_items, news_items = _resolve_items(selected_runs, brand=brand)
    log.info(
        "ai_batch start - social=%d review=%d news=%d provider=%s model=%s",
        len(social_items),
        len(review_items),
        len(news_items),
        provider,
        model,
    )

    social_records = _enrich_partition(
        records=social_items,
        partition_name="social",
        run_id=run_id,
        provider=provider,
        model=model,
        chunk_size=chunk_size,
        background_threshold=background_threshold,
        strict_openai=strict_openai,
        warnings=warnings,
    )
    review_records = _enrich_partition(
        records=review_items,
        partition_name="review",
        run_id=run_id,
        provider=provider,
        model=model,
        chunk_size=chunk_size,
        background_threshold=background_threshold,
        strict_openai=strict_openai,
        warnings=warnings,
    )
    news_records = _enrich_partition(
        records=news_items,
        partition_name="news",
        run_id=run_id,
        provider=provider,
        model=model,
        chunk_size=chunk_size,
        background_threshold=background_threshold,
        strict_openai=strict_openai,
        warnings=warnings,
    )

    entity_summaries = _build_entity_summaries(social_records + review_records + news_records)
    input_runs_for_output = {name: str(path) for name, path in selected_runs.items() if path}

    _write_jsonl(run_dir / "social_enriched.jsonl", social_records)
    _write_jsonl(run_dir / "review_enriched.jsonl", review_records)
    _write_jsonl(run_dir / "news_enriched.jsonl", news_records)
    _write_jsonl(run_dir / "entity_summary.jsonl", entity_summaries)
    (run_dir / "executive_summary.md").write_text(
        _build_executive_summary(
            run_id=run_id,
            input_runs=selected_runs,
            provider=provider if provider not in {"auto"} else ("openai" if resolve_openai_api_key() else "heuristic"),
            model=model,
            social_records=social_records,
            review_records=review_records,
            news_records=news_records,
            entity_summaries=entity_summaries,
        ),
        encoding="utf-8",
    )
    (run_dir / "metadata.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "provider": provider,
                "model": model,
                "input_runs": input_runs_for_output,
                "counts": {
                    "social": len(social_records),
                    "review": len(review_records),
                    "news": len(news_records),
                    "entities": len(entity_summaries),
                },
                "warnings": warnings,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return BatchRunResult(
        run_id=run_id,
        run_dir=str(run_dir),
        provider=provider,
        model=model,
        input_runs=input_runs_for_output,
        social_records=social_records,
        review_records=review_records,
        news_records=news_records,
        entity_summaries=entity_summaries,
        warnings=warnings,
    )
