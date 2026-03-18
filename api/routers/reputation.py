"""GET /api/reputation — Pilier Réputation."""
from __future__ import annotations

from collections import Counter

from fastapi import APIRouter

from ..loaders import load_ai_latest, load_excel_reputation, load_news_url_index, load_youtube_url_index
from ..kpis import (
    gravity_score,
    platform_from_source_name,
    volume_by_day,
)

router = APIRouter()


@router.get("/reputation")
def get_reputation():
    ai = load_ai_latest()
    social = ai.get("social", [])
    news = ai.get("news", [])
    excel_rep = load_excel_reputation()
    news_urls = load_news_url_index()
    yt_urls = load_youtube_url_index()

    # Normalize excel_rep: field names differ from ai_runs schema
    for r in excel_rep:
        if not r.get("sentiment_label") and r.get("sentiment"):
            r["sentiment_label"] = r["sentiment"].lower()
        if not r.get("published_at") and r.get("date"):
            r["published_at"] = r["date"]
        if not r.get("source_name") and r.get("platform"):
            r["source_name"] = r["platform"]

    # Merge: social + news from ai_runs + excel reputation tab
    all_records = social + news + excel_rep

    # ── KPIs ────────────────────────────────────────────────────────────────
    total = len(all_records)
    neg_count = sum(1 for r in all_records if r.get("sentiment_label") == "negative")
    neg_pct = round(neg_count / total, 3) if total else 0.0

    gscore = gravity_score(all_records)

    # Influenceurs détracteurs: is_verified=True AND sentiment=negative
    detractors = [
        r for r in all_records
        if r.get("sentiment_label") == "negative"
        and (r.get("is_verified") in (True, "True", "true", 1, "1"))
    ]
    influencer_count = len(detractors)

    # ── Volume par jour ──────────────────────────────────────────────────────
    vbd = volume_by_day(all_records)

    # ── Répartition par plateforme ───────────────────────────────────────────
    platform_counts: Counter = Counter()
    for r in all_records:
        p = platform_from_source_name(r.get("source_name", "") or r.get("_sheet", ""))
        platform_counts[p] += 1
    platform_total = sum(platform_counts.values()) or 1
    platform_breakdown = [
        {"platform": p, "count": c, "pct": round(c / platform_total * 100)}
        for p, c in platform_counts.most_common()
    ]

    # ── Top items (détracteurs influents triés par priority_score) ───────────
    top_items_raw = sorted(
        [r for r in all_records if r.get("priority_score") is not None],
        key=lambda r: float(r.get("priority_score", 0)),
        reverse=True,
    )[:10]
    def _extract_url(r: dict) -> str | None:
        item_key = r.get("item_key", "")
        if not item_key:
            return None
        prefix, _, rest = item_key.partition(":")
        # Reddit: "reddit_post:https://... | title" or "reddit_comment:https://... | id"
        if prefix in ("reddit_post", "reddit_comment"):
            url_part = rest.split(" | ")[0]
            if url_part.startswith("http"):
                return url_part
        # YouTube video: "youtube_video:VIDEO_ID"
        if prefix == "youtube_video":
            video_id = rest.split(" | ")[0].strip().lower()
            return yt_urls.get(video_id) or f"https://www.youtube.com/watch?v={rest.split(' | ')[0].strip()}"
        # YouTube comment: "youtube_comment:video_id_lower | comment_id"
        if prefix == "youtube_comment":
            video_id = rest.split(" | ")[0].strip().lower()
            return yt_urls.get(video_id) or None
        # News: "news_article:{article_id_lowercase}"
        if prefix == "news_article":
            return news_urls.get(rest.strip()) or None
        return None

    top_items = [
        {
            "entity": r.get("entity_name") or r.get("user_name") or r.get("author") or "—",
            "summary": r.get("summary_short") or r.get("summary") or r.get("text", "")[:120],
            "priority": r.get("priority_score"),
            "sentiment": r.get("sentiment_label", "neutral"),
            "source": platform_from_source_name(r.get("source_name", "") or r.get("_sheet", "")),
            "followers": r.get("user_followers") or r.get("followers"),
            "url": _extract_url(r),
            "evidence": (r.get("evidence_spans") or [])[:2],
        }
        for r in top_items_raw
    ]

    # ── Alerte ───────────────────────────────────────────────────────────────
    alert_active = gscore > 6 or neg_pct > 0.70
    alert = {
        "active": alert_active,
        "gravity_score": gscore,
        "message": "Crise active — Vélo défectueux" if alert_active else "Situation normale",
    }

    return {
        "kpis": {
            "volume_total": total,
            "sentiment_negatif_pct": neg_pct,
            "gravity_score": gscore,
            "influenceurs_detracteurs": influencer_count,
        },
        "volume_by_day": vbd,
        "platform_breakdown": platform_breakdown,
        "top_items": top_items,
        "alert": alert,
    }
