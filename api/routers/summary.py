"""GET /api/summary — Synthèse exécutive COMEX depuis entity_summary.jsonl."""
from __future__ import annotations

from collections import Counter

from fastapi import APIRouter

from ..loaders import load_ai_latest

router = APIRouter()


@router.get("/summary")
def get_summary():
    ai = load_ai_latest()
    entities_raw = ai.get("entity_summary", [])
    social = ai.get("social", [])
    news = ai.get("news", [])
    all_records = social + news

    # Aggregate risk_flags and opportunity_flags across all enriched records
    risk_counter: Counter = Counter()
    opp_counter: Counter = Counter()
    for r in all_records:
        for flag in r.get("risk_flags") or []:
            risk_counter[flag] += 1
        for flag in r.get("opportunity_flags") or []:
            opp_counter[flag] += 1

    top_risks = [{"flag": f, "count": c} for f, c in risk_counter.most_common(5)]
    top_opportunities = [{"flag": f, "count": c} for f, c in opp_counter.most_common(5)]

    # Sort entities by volume descending, keep top 20
    entities_sorted = sorted(entities_raw, key=lambda e: e.get("volume_items", 0), reverse=True)[:20]

    entities = [
        {
            "name": e.get("entity_name", "—"),
            "partition": e.get("source_partition", ""),
            "brand": e.get("brand_focus", "both"),
            "volume": e.get("volume_items", 0),
            "themes": (e.get("top_themes") or [])[:3],
            "risks": (e.get("top_risks") or [])[:3],
            "opportunities": (e.get("top_opportunities") or [])[:3],
            "takeaway": e.get("executive_takeaway", ""),
        }
        for e in entities_sorted
    ]

    return {
        "entities": entities,
        "top_risks": top_risks,
        "top_opportunities": top_opportunities,
    }
