"""GET /api/benchmark — Pilier Benchmark Marché."""
from __future__ import annotations

from fastapi import APIRouter

from ..loaders import load_ai_latest, load_excel_benchmark
from ..kpis import radar_topics, sov, sov_by_month

router = APIRouter()


@router.get("/benchmark")
def get_benchmark():
    ai = load_ai_latest()
    social = ai.get("social", [])
    excel_bench = load_excel_benchmark()

    # Records with brand_focus populated (from ai_runs or excel benchmark)
    # Excel benchmark: use sentiment_detected as sentiment_label if present
    excel_normalized = []
    for r in excel_bench:
        rec = dict(r)
        if "sentiment_label" not in rec:
            rec["sentiment_label"] = rec.get("sentiment_detected") or "neutral"
        # Map 'brand' column to brand_focus if needed
        if "brand_focus" not in rec:
            brand_raw = (rec.get("brand") or "").lower()
            if "intersport" in brand_raw:
                rec["brand_focus"] = "intersport"
            elif "decathlon" in brand_raw:
                rec["brand_focus"] = "decathlon"
        excel_normalized.append(rec)

    all_records = social + excel_normalized

    # Filter only records that have brand_focus
    branded = [r for r in all_records if r.get("brand_focus") in ("decathlon", "intersport")]

    # ── KPIs ────────────────────────────────────────────────────────────────
    sov_data = sov(branded)
    dec_records = [r for r in branded if r.get("brand_focus") == "decathlon"]
    int_records = [r for r in branded if r.get("brand_focus") == "intersport"]

    def _pos_pct(records):
        if not records:
            return 0.0
        pos = sum(1 for r in records if r.get("sentiment_label") == "positive")
        return round(pos / len(records), 3)

    # ── Brand scores per topic ───────────────────────────────────────────────
    radar = radar_topics(branded)

    # ── SOV par mois ────────────────────────────────────────────────────────
    sov_monthly = sov_by_month(branded)

    # ── Scores synthétiques par marque ──────────────────────────────────────
    def _brand_summary(records):
        total = len(records)
        pos = sum(1 for r in records if r.get("sentiment_label") == "positive")
        neg = sum(1 for r in records if r.get("sentiment_label") == "negative")
        neu = total - pos - neg
        return {
            "total_mentions": total,
            "positive_pct": round(pos / total * 100) if total else 0,
            "negative_pct": round(neg / total * 100) if total else 0,
            "neutral_pct": round(neu / total * 100) if total else 0,
        }

    return {
        "kpis": {
            "share_of_voice_decathlon": sov_data["decathlon"],
            "share_of_voice_intersport": sov_data["intersport"],
            "sentiment_decathlon_positive_pct": _pos_pct(dec_records),
            "sentiment_intersport_positive_pct": _pos_pct(int_records),
            "total_mentions": len(branded),
        },
        "radar": radar,
        "sov_by_month": sov_monthly,
        "brand_scores": {
            "decathlon": _brand_summary(dec_records),
            "intersport": _brand_summary(int_records),
        },
    }
