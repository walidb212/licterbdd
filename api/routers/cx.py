"""GET /api/cx — Pilier Expérience Client."""
from __future__ import annotations

from collections import Counter

from fastapi import APIRouter

from ..loaders import load_ai_latest, load_excel_cx, load_store_latest
from ..kpis import (
    enchantements_from_records,
    irritants_from_records,
    nps_proxy,
    rating_by_month,
    rating_distribution,
)

router = APIRouter()


@router.get("/cx")
def get_cx():
    ai = load_ai_latest()
    review_enriched = ai.get("review", [])
    store_reviews = load_store_latest()
    excel_cx = load_excel_cx()

    # Normalize excel_cx: field names differ from ai_runs schema
    for r in excel_cx:
        if not r.get("published_at") and r.get("date"):
            r["published_at"] = r["date"]
        if not r.get("sentiment_label") and r.get("sentiment"):
            r["sentiment_label"] = r["sentiment"].lower()

    # Exclude employee partition — only customer + store reviews for CX
    cx_enriched = [
        r for r in review_enriched
        if r.get("source_partition") not in ("employee",)
    ]

    # Combine all review-type records
    all_reviews = store_reviews + cx_enriched + excel_cx

    # ── KPIs ────────────────────────────────────────────────────────────────
    ratings = []
    for r in all_reviews:
        try:
            v = float(r.get("rating") or r.get("note") or 0)
            if 1 <= v <= 5:
                ratings.append(v)
        except (ValueError, TypeError):
            pass

    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0.0
    nps = nps_proxy(all_reviews)

    # SAV negative pct — records mentioning SAV themes that are negative
    sav_themes = {"service_client", "retour_remboursement"}
    sav_neg = sum(
        1 for r in all_reviews
        if r.get("sentiment_label") == "negative"
        and any(t in sav_themes for t in (r.get("themes") or []))
    )
    sav_neg_pct = round(sav_neg / len(all_reviews), 3) if all_reviews else 0.0

    # ── Rating par mois ──────────────────────────────────────────────────────
    rbm = rating_by_month(all_reviews)

    # ── Distribution des notes ───────────────────────────────────────────────
    dist = rating_distribution(all_reviews)

    # ── Irritants & Enchantements ─────────────────────────────────────────────
    # Use enriched records with themes — exclude employee partition
    enriched = cx_enriched + [r for r in store_reviews if r.get("themes")]
    irritants = irritants_from_records(enriched, top_n=5)
    enchantements = enchantements_from_records(enriched, top_n=3)

    # ── Sources (with URLs) ───────────────────────────────────────────────────
    source_data: dict[str, dict] = {}
    for r in all_reviews:
        name = (
            r.get("source_name")
            or r.get("platform")
            or r.get("site")
            or r.get("_sheet")
            or "Autre"
        )
        if name not in source_data:
            source_data[name] = {
                "count": 0,
                "url": r.get("source_url") or r.get("google_maps_url") or None,
            }
        source_data[name]["count"] += 1
        # Keep first non-null URL found
        if not source_data[name]["url"]:
            source_data[name]["url"] = r.get("source_url") or r.get("google_maps_url") or None

    sources = [
        {"name": k, "count": v["count"], "url": v["url"]}
        for k, v in sorted(source_data.items(), key=lambda x: -x[1]["count"])[:8]
    ]

    return {
        "kpis": {
            "avg_rating": avg_rating,
            "nps_proxy": nps,
            "total_reviews": len(all_reviews),
            "sav_negative_pct": sav_neg_pct,
        },
        "rating_by_month": rbm,
        "rating_distribution": dist,
        "irritants": irritants,
        "enchantements": enchantements,
        "sources": sources,
    }
