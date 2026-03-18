"""
db/loader.py — Ingest all JSONL + Excel data into PostgreSQL (Supabase).

Usage:
    py -3.10 -m db.loader                          # load everything
    py -3.10 -m db.loader --only social_posts       # load one table
    py -3.10 -m db.loader --schema-only             # just run schema.sql
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    from monitor_core import load_workspace_env
    load_workspace_env(ROOT)
except Exception:
    pass

import psycopg2
from psycopg2.extras import execute_values

log = logging.getLogger("db.loader")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DATA_DIR = ROOT / "data"
SCHEMA_FILE = Path(__file__).resolve().parent / "schema.sql"

SOURCE_DIRS = {
    "reddit_posts":     DATA_DIR / "reddit_runs",
    "reddit_comments":  DATA_DIR / "reddit_runs",
    "youtube_videos":   DATA_DIR / "youtube_runs",
    "youtube_comments": DATA_DIR / "youtube_runs",
    "tiktok_videos":    DATA_DIR / "tiktok_runs",
    "x_tweets":         DATA_DIR / "x_runs",
    "news":             DATA_DIR / "news_runs",
    "reviews":          DATA_DIR / "review_runs",
    "store_reviews":    DATA_DIR / "store_runs",
    "stores":           DATA_DIR / "store_runs",
    "context":          DATA_DIR / "context_runs",
    "ai_social":        DATA_DIR / "ai_runs",
    "ai_review":        DATA_DIR / "ai_runs",
    "ai_news":          DATA_DIR / "ai_runs",
    "ai_entities":      DATA_DIR / "ai_runs",
}

JSONL_FILES = {
    "reddit_posts":     "posts.jsonl",
    "reddit_comments":  "comments.jsonl",
    "youtube_videos":   "videos.jsonl",
    "youtube_comments": "comments.jsonl",
    "tiktok_videos":    "videos.jsonl",
    "x_tweets":         "tweets_normalized.jsonl",
    "news":             "articles.jsonl",
    "reviews":          "reviews.jsonl",
    "store_reviews":    "reviews.jsonl",
    "stores":           "stores.jsonl",
    "context":          "documents.jsonl",
    "ai_social":        "social_enriched.jsonl",
    "ai_review":        "review_enriched.jsonl",
    "ai_news":          "news_enriched.jsonl",
    "ai_entities":      "entity_summary.jsonl",
}

EXCEL_DIR = DATA_DIR / "excel_runs"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_db_url() -> str:
    url = os.environ.get("SUPABASE_DB_URL", "")
    if not url:
        sys.exit("SUPABASE_DB_URL not set in .env")
    return url


def _find_latest_run(base_dir: Path) -> Path | None:
    """Find the most recent run directory (sorted lexicographically)."""
    if not base_dir.exists():
        return None
    # First check for a 'latest' symlink / alias
    latest = base_dir / "latest"
    if latest.exists():
        return latest
    # Otherwise pick the most recent timestamped directory
    dirs = sorted(
        [d for d in base_dir.iterdir() if d.is_dir() and not d.name.startswith(".")],
        reverse=True,
    )
    return dirs[0] if dirs else None


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        log.warning("File not found: %s", path)
        return []
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    log.info("Loaded %d records from %s", len(records), path)
    return records


def _safe(val: object) -> str | None:
    if val is None or val == "":
        return None
    s = str(val).strip()
    return None if s.lower() in {"none", "nan", "n/a", "#n/a"} else s


def _safe_int(val: object) -> int:
    if val is None or val == "":
        return 0
    try:
        return int(float(str(val).replace(",", "").strip()))
    except (ValueError, TypeError):
        return 0


def _safe_float(val: object) -> float | None:
    if val is None or val == "":
        return None
    try:
        return float(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def _safe_ts(val: object) -> str | None:
    """Convert date string to ISO timestamp or None."""
    if val is None or val == "":
        return None
    s = str(val).strip()
    if not s or s.lower() in {"none", "nan"}:
        return None
    return s


def _safe_json(val: object) -> str:
    """Ensure val is a JSON string (for JSONB columns)."""
    if isinstance(val, (list, dict)):
        return json.dumps(val, ensure_ascii=False)
    if isinstance(val, str):
        try:
            json.loads(val)
            return val
        except json.JSONDecodeError:
            return json.dumps([val], ensure_ascii=False)
    return "[]"


def _brand_enum(val: object) -> str:
    s = str(val or "").strip().lower()
    if s in ("decathlon", "intersport", "both"):
        return s
    if "decathlon" in s:
        return "decathlon"
    if "intersport" in s:
        return "intersport"
    return "both"


def _partition_enum(val: object) -> str:
    s = str(val or "").strip().lower()
    valid = {"customer", "employee", "store", "promo", "product", "context", "news", "community", "social"}
    return s if s in valid else "social"


def _make_item_key(prefix: str, *parts: str) -> str:
    """Generate a deterministic item_key from parts."""
    raw = "|".join(str(p) for p in parts if p)
    return f"{prefix}:{hashlib.md5(raw.encode()).hexdigest()[:12]}"


# ---------------------------------------------------------------------------
# Upsert functions per table
# ---------------------------------------------------------------------------

def _upsert_social_posts(cur, records: list[dict], platform: str, default_partition: str) -> int:
    if not records:
        return 0
    rows = []
    for r in records:
        # Build item_key depending on platform
        if platform == "x":
            post_id = _safe(r.get("review_id")) or _safe(r.get("tweet_id")) or ""
            item_key = f"x:{post_id}" if post_id else _make_item_key("x", r.get("text", "")[:100])
        elif platform == "reddit":
            post_id = _safe(r.get("post_url")) or ""
            item_key = f"reddit:{hashlib.md5(post_id.encode()).hexdigest()[:12]}" if post_id else _make_item_key("reddit", r.get("post_title", "")[:100])
        elif platform == "youtube":
            post_id = _safe(r.get("video_id")) or ""
            item_key = f"yt:{post_id}" if post_id else _make_item_key("yt", r.get("title", "")[:100])
        elif platform == "tiktok":
            post_id = _safe(r.get("video_id")) or ""
            item_key = f"tt:{post_id}" if post_id else _make_item_key("tt", r.get("title", "")[:100])
        else:
            post_id = ""
            item_key = _make_item_key(platform, r.get("text", "")[:100])

        partition = _partition_enum(r.get("source_partition", default_partition))
        brand = _brand_enum(r.get("brand_focus", "both"))

        rows.append((
            item_key,
            _safe(r.get("run_id")),
            partition,
            platform,
            brand,
            post_id,
            _safe(r.get("post_url") or r.get("tweet_url") or r.get("video_url")),
            _safe(r.get("author_name") or r.get("author") or r.get("channel_name")),
            _safe(r.get("author_handle")),
            _safe(r.get("subreddit")),
            _safe(r.get("channel_name")),
            _safe(r.get("channel_id")),
            _safe(r.get("title") or r.get("post_title")),
            _safe(r.get("text") or r.get("post_text")),
            _safe(r.get("description")),
            _safe_json(r.get("tags", [])),
            _safe_ts(r.get("published_at") or r.get("created_at") or r.get("date")),
            _safe(r.get("date") or r.get("date_raw") or r.get("created_at")),
            _safe_int(r.get("likes") or r.get("like_count", 0)),
            _safe_int(r.get("view_count", 0)),
            _safe_int(r.get("share_count") or r.get("repost_count", 0)),
            _safe_int(r.get("reply_count", 0)),
            _safe_int(r.get("comment_count", 0)),
            _safe_int(r.get("quote_count", 0)),
            _safe_int(r.get("score", 0)),
            _safe_int(r.get("save_count", 0)),
            _safe_int(r.get("duration_seconds")),
            _safe(r.get("thumbnail_url")),
            _safe(r.get("language") or r.get("language_raw")),
            _safe(r.get("location")),
            bool(r.get("is_verified", False)),
            _safe_int(r.get("user_followers")),
            _safe_int(r.get("rating", -1)),
            _safe(r.get("brand")),
            _safe(r.get("post_type")),
            _safe(r.get("search_type")),
            _safe(r.get("query_name")),
            _safe_json(r.get("query_names", [])),
            _safe_json(r.get("source_brand_focuses", [])),
            _safe(r.get("pillar")),
            _safe_float(r.get("relevance_score")),
        ))

    sql = """
        INSERT INTO social_posts (
            item_key, run_id, source_partition, platform, brand_focus,
            post_id, post_url, author_name, author_handle, subreddit,
            channel_name, channel_id, title, text, description,
            tags, published_at, date_raw, likes, view_count,
            share_count, reply_count, comment_count, quote_count, score,
            save_count, duration_seconds, thumbnail_url, language, location,
            is_verified, user_followers, rating, brand, post_type,
            search_type, query_name, query_names, source_brand_focuses, pillar,
            relevance_score
        ) VALUES %s
        ON CONFLICT (item_key) DO UPDATE SET
            likes = GREATEST(social_posts.likes, EXCLUDED.likes),
            view_count = GREATEST(social_posts.view_count, EXCLUDED.view_count),
            share_count = GREATEST(social_posts.share_count, EXCLUDED.share_count),
            comment_count = GREATEST(social_posts.comment_count, EXCLUDED.comment_count),
            run_id = EXCLUDED.run_id
    """
    execute_values(cur, sql, rows, page_size=200)
    return len(rows)


def _upsert_social_comments(cur, records: list[dict], platform: str, default_partition: str) -> int:
    if not records:
        return 0
    rows = []
    for r in records:
        if platform == "reddit":
            comment_id = str(r.get("comment_index", ""))
            post_id = _safe(r.get("post_url")) or ""
            item_key = _make_item_key("reddit_c", post_id, comment_id)
        else:  # youtube
            comment_id = _safe(r.get("comment_id")) or ""
            post_id = _safe(r.get("video_id")) or ""
            item_key = f"yt_c:{comment_id}" if comment_id else _make_item_key("yt_c", post_id, r.get("text", "")[:80])

        rows.append((
            item_key,
            _safe(r.get("run_id")),
            _partition_enum(r.get("source_partition", default_partition)),
            platform,
            _brand_enum(r.get("brand_focus", "both")),
            post_id,
            _safe(r.get("post_url") or r.get("video_url")),
            _safe(r.get("video_title") or r.get("post_title")),
            comment_id,
            _safe(r.get("parent_id")),
            _safe(r.get("author") or r.get("comment_author")),
            _safe(r.get("text") or r.get("comment_text")),
            _safe_int(r.get("score") or r.get("comment_score_raw", 0)),
            _safe_int(r.get("like_count", 0)),
            bool(r.get("is_reply", False)),
            _safe_ts(r.get("published_at")),
            _safe(r.get("language") or r.get("language_raw")),
            _safe(r.get("subreddit")),
            _safe(r.get("pillar")),
        ))

    sql = """
        INSERT INTO social_comments (
            item_key, run_id, source_partition, platform, brand_focus,
            post_id, post_url, post_title, comment_id, parent_id,
            author, text, score, like_count, is_reply,
            published_at, language, subreddit, pillar
        ) VALUES %s
        ON CONFLICT (item_key) DO UPDATE SET
            score = GREATEST(social_comments.score, EXCLUDED.score),
            like_count = GREATEST(social_comments.like_count, EXCLUDED.like_count)
    """
    execute_values(cur, sql, rows, page_size=200)
    return len(rows)


def _upsert_reviews(cur, records: list[dict], source_label: str) -> int:
    if not records:
        return 0
    rows = []
    for r in records:
        site = _safe(r.get("site")) or source_label
        entity = _safe(r.get("entity_name")) or ""
        author = _safe(r.get("author")) or ""
        body = _safe(r.get("body")) or ""
        item_key = _make_item_key("rev", site, entity, author, body[:80])

        partition = _partition_enum(r.get("source_partition", "customer"))
        if site and "glassdoor" in site.lower() or "indeed" in site.lower():
            partition = "employee"
        elif site and "google_maps" in site.lower():
            partition = "store"
        elif site and "dealabs" in site.lower():
            partition = "promo"

        rows.append((
            item_key,
            _safe(r.get("run_id")),
            partition,
            _brand_enum(r.get("brand_focus", "both")),
            site,
            _safe(r.get("review_scope")),
            _safe(r.get("entity_level")),
            entity,
            _safe(r.get("location")),
            _safe_float(r.get("rating")),
            _safe(r.get("date_raw")),
            _safe_ts(r.get("published_at") or r.get("date_raw")),
            author,
            body,
            _safe_float(r.get("aggregate_rating")),
            _safe_int(r.get("aggregate_count")),
            _safe(r.get("source_url")),
            _safe(r.get("store_url")),
            _safe(r.get("google_maps_url")),
            _safe(r.get("source_symmetry")),
            _safe(r.get("language") or r.get("language_raw")),
        ))

    sql = """
        INSERT INTO reviews (
            item_key, run_id, source_partition, brand_focus,
            site, review_scope, entity_level, entity_name, location,
            rating, date_raw, published_at, author, body,
            aggregate_rating, aggregate_count, source_url, store_url,
            google_maps_url, source_symmetry, language
        ) VALUES %s
        ON CONFLICT (item_key) DO UPDATE SET
            rating = COALESCE(EXCLUDED.rating, reviews.rating),
            aggregate_rating = COALESCE(EXCLUDED.aggregate_rating, reviews.aggregate_rating),
            aggregate_count = GREATEST(reviews.aggregate_count, EXCLUDED.aggregate_count)
    """
    execute_values(cur, sql, rows, page_size=200)
    return len(rows)


def _upsert_news(cur, records: list[dict]) -> int:
    if not records:
        return 0
    rows = []
    for r in records:
        article_id = _safe(r.get("article_id")) or ""
        item_key = f"news:{article_id}" if article_id else _make_item_key("news", r.get("article_title", "")[:100])

        rows.append((
            item_key,
            _safe(r.get("run_id")),
            "news",
            _brand_enum(r.get("brand_focus", "both")),
            article_id,
            _safe(r.get("article_title")),
            _safe_ts(r.get("published_at")),
            _safe(r.get("source_name")),
            _safe(r.get("source_domain")),
            _safe(r.get("google_news_url")),
            _safe(r.get("description_text")),
            _safe(r.get("description_html")),
            _safe(r.get("article_markdown")),
            _safe(r.get("article_snapshot_url")),
            _safe(r.get("signal_type")),
            _safe(r.get("brand_detected")),
            _safe(r.get("enrichment_mode")),
            _safe(r.get("query_name")),
            _safe_json(r.get("query_names", [])),
            _safe_json(r.get("source_brand_focuses", [])),
        ))

    sql = """
        INSERT INTO news_articles (
            item_key, run_id, source_partition, brand_focus,
            article_id, article_title, published_at, source_name, source_domain,
            google_news_url, description_text, description_html, article_markdown,
            article_snapshot_url, signal_type, brand_detected, enrichment_mode,
            query_name, query_names, source_brand_focuses
        ) VALUES %s
        ON CONFLICT (item_key) DO UPDATE SET
            article_markdown = COALESCE(EXCLUDED.article_markdown, news_articles.article_markdown),
            run_id = EXCLUDED.run_id
    """
    execute_values(cur, sql, rows, page_size=200)
    return len(rows)


def _upsert_context(cur, records: list[dict]) -> int:
    if not records:
        return 0
    rows = []
    for r in records:
        content_hash = _safe(r.get("content_hash")) or ""
        item_key = f"ctx:{content_hash}" if content_hash else _make_item_key("ctx", r.get("source_url", ""), r.get("title", ""))

        rows.append((
            item_key,
            _safe(r.get("run_id")),
            "context",
            _brand_enum(r.get("brand_focus", "both")),
            _safe(r.get("document_type")),
            _safe(r.get("source_name")),
            _safe(r.get("source_url")),
            _safe(r.get("title")),
            _safe(r.get("fetch_mode")),
            content_hash,
            _safe(r.get("content_text")),
        ))

    sql = """
        INSERT INTO context_documents (
            item_key, run_id, source_partition, brand_focus,
            document_type, source_name, source_url, title,
            fetch_mode, content_hash, content_text
        ) VALUES %s
        ON CONFLICT (item_key) DO UPDATE SET
            content_text = EXCLUDED.content_text,
            content_hash = EXCLUDED.content_hash,
            run_id = EXCLUDED.run_id
    """
    execute_values(cur, sql, rows, page_size=200)
    return len(rows)


def _upsert_stores(cur, records: list[dict]) -> int:
    if not records:
        return 0
    rows = []
    for r in records:
        gmap_url = _safe(r.get("google_maps_url")) or ""
        if not gmap_url:
            continue
        rows.append((
            _safe(r.get("run_id")),
            _brand_enum(r.get("brand_focus", "both")),
            _safe(r.get("store_name")),
            _safe(r.get("store_url")),
            _safe(r.get("address")),
            _safe(r.get("postal_code")),
            _safe(r.get("city")),
            gmap_url,
            _safe(r.get("discovery_source")),
            _safe(r.get("status")),
            _safe(r.get("source_symmetry")),
        ))

    sql = """
        INSERT INTO stores (
            run_id, brand_focus, store_name, store_url, address,
            postal_code, city, google_maps_url, discovery_source, status, source_symmetry
        ) VALUES %s
        ON CONFLICT (google_maps_url) DO UPDATE SET
            status = EXCLUDED.status,
            run_id = EXCLUDED.run_id
    """
    execute_values(cur, sql, rows, page_size=200)
    return len(rows)


def _upsert_excel_reputation(cur, records: list[dict]) -> int:
    if not records:
        return 0
    rows = []
    for r in records:
        review_id = _safe(r.get("review_id")) or ""
        item_key = f"xls_rep:{review_id}" if review_id else _make_item_key("xls_rep", r.get("text", "")[:100])

        # Collect extra columns not in our schema
        known = {"review_id", "platform", "brand", "post_type", "text", "date", "rating",
                 "likes", "sentiment", "user_followers", "is_verified", "language", "location",
                 "share_count", "reply_count", "_sheet", "_run_id",
                 "scraping_server_ip", "user_agent_string", "deprecated_field_v2", "processing_time_ms"}
        extra = {k: v for k, v in r.items() if k not in known and v}

        rows.append((
            item_key,
            _brand_enum(r.get("brand", "decathlon")),
            _safe(r.get("platform")),
            _safe(r.get("review_id")),  # author placeholder
            _safe(r.get("text")),
            _safe_ts(r.get("date")),
            _safe(r.get("date")),
            _safe(r.get("tweet_url") or r.get("url")),
            _safe_int(r.get("likes")),
            _safe_int(r.get("share_count")),
            _safe_int(r.get("reply_count")),
            0,  # views
            _safe_int(r.get("user_followers")),
            _safe(r.get("sentiment")),
            _safe(r.get("language")),
            json.dumps(extra, ensure_ascii=False) if extra else "{}",
        ))

    sql = """
        INSERT INTO excel_reputation (
            item_key, brand_focus, platform, author, text,
            published_at, date_raw, url, likes, shares,
            comments, views, followers, sentiment, language, extra
        ) VALUES %s
        ON CONFLICT (item_key) DO NOTHING
    """
    execute_values(cur, sql, rows, page_size=200)
    return len(rows)


def _upsert_excel_benchmark(cur, records: list[dict]) -> int:
    if not records:
        return 0
    rows = []
    for r in records:
        review_id = _safe(r.get("review_id")) or ""
        item_key = f"xls_bench:{review_id}" if review_id else _make_item_key("xls_bench", r.get("text", "")[:100])

        brand_raw = _safe(r.get("target_brand_vs_competitor")) or _safe(r.get("entity_analyzed")) or ""
        brand = _brand_enum(brand_raw)

        known = {"review_id", "platform", "entity_analyzed", "topic", "text", "date",
                 "target_brand_vs_competitor", "sentiment_detected", "user_followers",
                 "is_verified", "language", "location", "share_count", "reply_count",
                 "_sheet", "_run_id",
                 "scraping_server_ip", "user_agent_string", "deprecated_field_v2", "processing_time_ms"}
        extra = {k: v for k, v in r.items() if k not in known and v}

        rows.append((
            item_key,
            brand,
            _safe(r.get("platform")),
            None,  # author
            _safe(r.get("text")),
            _safe_ts(r.get("date")),
            _safe(r.get("date")),
            None,  # url
            _safe(r.get("topic")),
            _safe(r.get("sentiment_detected")),
            _safe_int(r.get("likes", 0)),
            _safe_int(r.get("share_count", 0)),
            _safe_int(r.get("reply_count", 0)),
            0,  # views
            json.dumps(extra, ensure_ascii=False) if extra else "{}",
        ))

    sql = """
        INSERT INTO excel_benchmark (
            item_key, brand_focus, platform, author, text,
            published_at, date_raw, url, topic, sentiment_detected,
            likes, shares, comments, views, extra
        ) VALUES %s
        ON CONFLICT (item_key) DO UPDATE SET
            sentiment_detected = COALESCE(EXCLUDED.sentiment_detected, excel_benchmark.sentiment_detected)
    """
    execute_values(cur, sql, rows, page_size=200)
    return len(rows)


def _upsert_excel_cx(cur, records: list[dict]) -> int:
    if not records:
        return 0
    rows = []
    for r in records:
        review_id = _safe(r.get("review_id")) or ""
        item_key = f"xls_cx:{review_id}" if review_id else _make_item_key("xls_cx", r.get("text", "")[:100])

        known = {"review_id", "platform", "brand", "category", "text", "date", "rating",
                 "sentiment", "user_followers", "is_verified", "language", "location",
                 "share_count", "reply_count", "_sheet", "_run_id",
                 "scraping_server_ip", "user_agent_string", "deprecated_field_v2", "processing_time_ms"}
        extra = {k: v for k, v in r.items() if k not in known and v}

        rows.append((
            item_key,
            _brand_enum(r.get("brand", "decathlon")),
            _safe(r.get("platform")),
            _safe_float(r.get("rating")),
            None,  # author
            _safe(r.get("text")),
            _safe_ts(r.get("date")),
            _safe(r.get("date")),
            _safe(r.get("category")),
            _safe(r.get("sentiment")),
            _safe(r.get("language")),
            json.dumps(extra, ensure_ascii=False) if extra else "{}",
        ))

    sql = """
        INSERT INTO excel_cx (
            item_key, brand_focus, site, rating, author, text,
            published_at, date_raw, category, sentiment, language, extra
        ) VALUES %s
        ON CONFLICT (item_key) DO NOTHING
    """
    execute_values(cur, sql, rows, page_size=200)
    return len(rows)


def _upsert_ai_enrichments(cur, records: list[dict]) -> int:
    if not records:
        return 0
    rows = []
    for r in records:
        item_key = _safe(r.get("item_key"))
        if not item_key:
            continue

        sentiment = _safe(r.get("sentiment_label")) or "neutral"
        if sentiment not in ("positive", "negative", "neutral", "mixed"):
            sentiment = "neutral"

        rows.append((
            _safe(r.get("run_id")),
            _safe(r.get("source_run_id")),
            item_key,
            _partition_enum(r.get("source_partition", "social")),
            _brand_enum(r.get("brand_focus", "both")),
            _safe(r.get("entity_name")),
            _safe(r.get("language")),
            sentiment,
            _safe_float(r.get("sentiment_confidence")),
            _safe_json(r.get("themes", [])),
            _safe_json(r.get("risk_flags", [])),
            _safe_json(r.get("opportunity_flags", [])),
            _safe_float(r.get("priority_score")) or 0,
            _safe(r.get("summary_short")),
            _safe_json(r.get("evidence_spans", [])),
            _safe(r.get("pillar")),
            _safe(r.get("source_name")),
            _safe_ts(r.get("published_at")),
            _safe(r.get("provider")),
            _safe(r.get("model")),
        ))

    sql = """
        INSERT INTO ai_enrichments (
            run_id, source_run_id, item_key, source_partition, brand_focus,
            entity_name, language, sentiment_label, sentiment_confidence,
            themes, risk_flags, opportunity_flags, priority_score,
            summary_short, evidence_spans, pillar, source_name,
            published_at, provider, model
        ) VALUES %s
        ON CONFLICT (item_key) DO UPDATE SET
            sentiment_label = EXCLUDED.sentiment_label,
            sentiment_confidence = EXCLUDED.sentiment_confidence,
            themes = EXCLUDED.themes,
            risk_flags = EXCLUDED.risk_flags,
            opportunity_flags = EXCLUDED.opportunity_flags,
            priority_score = EXCLUDED.priority_score,
            summary_short = EXCLUDED.summary_short,
            provider = EXCLUDED.provider,
            model = EXCLUDED.model,
            run_id = EXCLUDED.run_id
    """
    execute_values(cur, sql, rows, page_size=200)
    return len(rows)


def _upsert_entity_summaries(cur, records: list[dict]) -> int:
    if not records:
        return 0
    rows = []
    for r in records:
        rows.append((
            _brand_enum(r.get("brand_focus", "both")),
            _partition_enum(r.get("source_partition", "social")),
            _safe(r.get("entity_name")) or "unknown",
            _safe(r.get("period_start")),
            _safe(r.get("period_end")),
            _safe_int(r.get("volume_items")),
            _safe_json(r.get("top_themes", [])),
            _safe_json(r.get("top_risks", [])),
            _safe_json(r.get("top_opportunities", [])),
            _safe(r.get("executive_takeaway")),
        ))

    sql = """
        INSERT INTO entity_summaries (
            brand_focus, source_partition, entity_name,
            period_start, period_end, volume_items,
            top_themes, top_risks, top_opportunities, executive_takeaway
        ) VALUES %s
        ON CONFLICT (brand_focus, source_partition, entity_name) DO UPDATE SET
            volume_items = EXCLUDED.volume_items,
            top_themes = EXCLUDED.top_themes,
            top_risks = EXCLUDED.top_risks,
            top_opportunities = EXCLUDED.top_opportunities,
            executive_takeaway = EXCLUDED.executive_takeaway
    """
    execute_values(cur, sql, rows, page_size=200)
    return len(rows)


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def run_schema(conn) -> None:
    """Execute schema.sql to create/reset all tables."""
    sql = SCHEMA_FILE.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    log.info("Schema applied from %s", SCHEMA_FILE)


def load_all(conn, only: str | None = None) -> dict[str, int]:
    """Load all JSONL + Excel data. Returns counts per table."""
    counts: dict[str, int] = {}

    with conn.cursor() as cur:
        # --- Social posts ---
        if not only or only == "social_posts":
            for source, platform, partition in [
                ("reddit_posts", "reddit", "community"),
                ("youtube_videos", "youtube", "social"),
                ("tiktok_videos", "tiktok", "social"),
                ("x_tweets", "x", "social"),
            ]:
                run_dir = _find_latest_run(SOURCE_DIRS[source])
                if run_dir:
                    records = _load_jsonl(run_dir / JSONL_FILES[source])
                    n = _upsert_social_posts(cur, records, platform, partition)
                    counts[f"social_posts/{platform}"] = n

        # --- Social comments ---
        if not only or only == "social_comments":
            for source, platform, partition in [
                ("reddit_comments", "reddit", "community"),
                ("youtube_comments", "youtube", "social"),
            ]:
                run_dir = _find_latest_run(SOURCE_DIRS[source])
                if run_dir:
                    records = _load_jsonl(run_dir / JSONL_FILES[source])
                    n = _upsert_social_comments(cur, records, platform, partition)
                    counts[f"social_comments/{platform}"] = n

        # --- Reviews (review_monitor + store_monitor) ---
        if not only or only == "reviews":
            for source in ("reviews", "store_reviews"):
                run_dir = _find_latest_run(SOURCE_DIRS[source])
                if run_dir:
                    records = _load_jsonl(run_dir / JSONL_FILES[source])
                    n = _upsert_reviews(cur, records, source)
                    counts[f"reviews/{source}"] = n

        # --- News ---
        if not only or only == "news_articles":
            run_dir = _find_latest_run(SOURCE_DIRS["news"])
            if run_dir:
                records = _load_jsonl(run_dir / JSONL_FILES["news"])
                counts["news_articles"] = _upsert_news(cur, records)

        # --- Context ---
        if not only or only == "context_documents":
            run_dir = _find_latest_run(SOURCE_DIRS["context"])
            if run_dir:
                records = _load_jsonl(run_dir / JSONL_FILES["context"])
                counts["context_documents"] = _upsert_context(cur, records)

        # --- Stores ---
        if not only or only == "stores":
            run_dir = _find_latest_run(SOURCE_DIRS["stores"])
            if run_dir:
                records = _load_jsonl(run_dir / JSONL_FILES["stores"])
                counts["stores"] = _upsert_stores(cur, records)

        # --- Excel sheets ---
        if not only or only == "excel":
            rep_path = EXCEL_DIR / "reputation_crise.jsonl"
            if rep_path.exists():
                counts["excel_reputation"] = _upsert_excel_reputation(cur, _load_jsonl(rep_path))

            bench_path = EXCEL_DIR / "benchmark_marche.jsonl"
            if bench_path.exists():
                counts["excel_benchmark"] = _upsert_excel_benchmark(cur, _load_jsonl(bench_path))

            cx_path = EXCEL_DIR / "voix_client_cx.jsonl"
            if cx_path.exists():
                counts["excel_cx"] = _upsert_excel_cx(cur, _load_jsonl(cx_path))

        # --- AI enrichments ---
        if not only or only == "ai_enrichments":
            for ai_source in ("ai_social", "ai_review", "ai_news"):
                run_dir = _find_latest_run(SOURCE_DIRS[ai_source])
                if run_dir:
                    records = _load_jsonl(run_dir / JSONL_FILES[ai_source])
                    n = _upsert_ai_enrichments(cur, records)
                    counts[f"ai_enrichments/{ai_source}"] = n

        # --- Entity summaries ---
        if not only or only == "entity_summaries":
            run_dir = _find_latest_run(SOURCE_DIRS["ai_entities"])
            if run_dir:
                records = _load_jsonl(run_dir / JSONL_FILES["ai_entities"])
                counts["entity_summaries"] = _upsert_entity_summaries(cur, records)

    conn.commit()

    # Refresh materialized views
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT refresh_materialized_views()")
        conn.commit()
        log.info("Materialized views refreshed")
    except Exception as exc:
        log.warning("Could not refresh materialized views: %s", exc)
        conn.rollback()

    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Load JSONL + Excel data into PostgreSQL")
    parser.add_argument("--schema-only", action="store_true", help="Only run schema.sql, don't load data")
    parser.add_argument("--only", type=str, default=None,
                        help="Load only one table group: social_posts, social_comments, reviews, news_articles, context_documents, stores, excel, ai_enrichments, entity_summaries")
    parser.add_argument("--skip-schema", action="store_true", help="Skip schema creation, load data only")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%H:%M:%S",
    )

    db_url = _get_db_url()
    log.info("Connecting to database...")
    conn = psycopg2.connect(db_url)

    try:
        if not args.skip_schema:
            log.info("Applying schema...")
            run_schema(conn)

        if args.schema_only:
            log.info("Schema-only mode, done.")
            return

        log.info("Loading data...")
        counts = load_all(conn, only=args.only)

        log.info("=== Load Summary ===")
        total = 0
        for table, n in sorted(counts.items()):
            log.info("  %-35s %d rows", table, n)
            total += n
        log.info("  %-35s %d rows", "TOTAL", total)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
