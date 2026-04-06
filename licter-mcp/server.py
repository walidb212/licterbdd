"""
LICTER Brand Intelligence — MCP Server
Connects Claude Desktop / ChatGPT / Cursor to our real-time brand monitoring data.

Usage:
  python server.py                          # local mode (reads SQLite)
  LICTER_API_URL=https://... python server.py  # remote mode (reads from Workers API)

Claude Desktop config (~/.claude/claude_desktop_config.json):
  {
    "mcpServers": {
      "licter": {
        "command": "python",
        "args": ["C:/Users/walid/Desktop/DEV/EugeniaSchool/LICTER/licter-mcp/server.py"]
      }
    }
  }
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from fastmcp import FastMCP

# ── Config ──
API_URL = os.environ.get("LICTER_API_URL", "http://localhost:8000")
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "dashboard.sqlite3"

mcp = FastMCP(
    "LICTER Brand Intelligence",
    description="Real-time brand monitoring data for Decathlon & Intersport. 13 sources, 8000+ records, sentiment analysis, crisis detection.",
)


# ── Helpers ──
def _fetch_api(endpoint: str) -> dict:
    """Fetch from the LICTER API (local Express or remote Worker)."""
    import urllib.request
    url = f"{API_URL}{endpoint}"
    req = urllib.request.Request(url, headers={"User-Agent": "LICTER-MCP/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def _query_db(sql: str, params: tuple = ()) -> list[dict]:
    """Direct SQLite query (local mode only)."""
    import sqlite3
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Tools ──

@mcp.tool()
def get_brand_kpis(brand: str = "decathlon", period: str = "all") -> str:
    """Get key KPIs for a brand: Share of Voice, sentiment distribution, NPS proxy, Gravity Score.

    Args:
        brand: "decathlon" or "intersport"
        period: "all", "week", or "month"
    """
    rep = _fetch_api("/api/reputation")
    bench = _fetch_api("/api/benchmark")
    cx = _fetch_api("/api/cx")

    return json.dumps({
        "brand": brand,
        "gravity_score": rep["kpis"]["gravity_score"],
        "volume_total": rep["kpis"]["volume_total"],
        "sentiment_negatif_pct": round(rep["kpis"]["sentiment_negatif_pct"] * 100, 1),
        "share_of_voice_decathlon": round(bench["kpis"]["share_of_voice_decathlon"] * 100, 1),
        "share_of_voice_intersport": round(bench["kpis"]["share_of_voice_intersport"] * 100, 1),
        "nps_proxy": cx["kpis"]["nps_proxy"],
        "avg_rating": cx["kpis"]["avg_rating"],
        "total_reviews": cx["kpis"]["total_reviews"],
        "alert_active": rep["alert"]["active"],
        "alert_message": rep["alert"]["message"],
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def search_mentions(keyword: str, brand: str = "", limit: int = 20) -> str:
    """Search brand mentions across all collected data (social, reviews, news).

    Args:
        keyword: Search term (e.g. "SAV", "vélo", "boycott")
        brand: Filter by "decathlon" or "intersport" (empty = both)
        limit: Max results (default 20)
    """
    results = _query_db(
        f"""SELECT source_name, brand_focus, sentiment_label, priority_score, summary_short, published_at, topic, post_type
        FROM social_enriched
        WHERE summary_short LIKE ? {'AND brand_focus = ?' if brand else ''}
        ORDER BY priority_score DESC LIMIT ?""",
        (f"%{keyword}%", brand, limit) if brand else (f"%{keyword}%", limit)
    )

    if not results:
        # Fallback: try review_enriched
        results = _query_db(
            f"""SELECT source_name, brand_focus, sentiment_label, priority_score, summary_short, published_at
            FROM review_enriched WHERE summary_short LIKE ? LIMIT ?""",
            (f"%{keyword}%", limit)
        )

    return json.dumps({
        "keyword": keyword,
        "brand": brand or "both",
        "count": len(results),
        "mentions": results,
    }, ensure_ascii=False, indent=2, default=str)


@mcp.tool()
def get_crisis_alerts(threshold: float = 6.0) -> str:
    """Get active crisis alerts. Returns crisis severity, timeline, and warnings.

    Args:
        threshold: Gravity Score threshold (default 6.0, max 10)
    """
    crisis = _fetch_api("/api/crisis")
    rep = _fetch_api("/api/reputation")

    return json.dumps({
        "gravity_score": rep["kpis"]["gravity_score"],
        "severity": crisis["severity"],
        "is_escalating": crisis["is_escalating"],
        "avg_daily_volume": crisis["avg_daily_volume"],
        "peak_day": crisis.get("peak_day"),
        "warnings": crisis.get("warnings", []),
        "alert_active": rep["kpis"]["gravity_score"] >= threshold,
        "timeline_last_7_days": crisis.get("timeline", [])[-7:],
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def compare_brands(topic: str = "all") -> str:
    """Compare Decathlon vs Intersport on a specific topic or overall.

    Args:
        topic: "prix", "sav", "qualite", "all" for overall comparison
    """
    bench = _fetch_api("/api/benchmark")

    result = {
        "topic": topic,
        "share_of_voice": {
            "decathlon": round(bench["kpis"]["share_of_voice_decathlon"] * 100, 1),
            "intersport": round(bench["kpis"]["share_of_voice_intersport"] * 100, 1),
        },
        "brand_scores": bench.get("brand_scores", {}),
        "total_mentions": bench["kpis"]["total_mentions"],
    }

    if bench.get("radar"):
        if topic != "all":
            result["radar"] = [r for r in bench["radar"] if topic.lower() in r.get("topic", "").lower()]
        else:
            result["radar"] = bench["radar"]

    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def get_top_irritants(brand: str = "decathlon", limit: int = 5) -> str:
    """Get top customer irritants (negative themes from reviews).

    Args:
        brand: "decathlon" or "intersport"
        limit: Number of irritants to return
    """
    cx = _fetch_api("/api/cx")

    return json.dumps({
        "brand": brand,
        "nps_proxy": cx["kpis"]["nps_proxy"],
        "avg_rating": cx["kpis"]["avg_rating"],
        "irritants": cx.get("irritants", [])[:limit],
        "enchantements": cx.get("enchantements", []),
        "recommendation": "Déployer un chatbot SAV de première réponse pour absorber 60% des cas simples.",
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def get_trending_topics(brand: str = "decathlon", days: int = 7) -> str:
    """Get emerging/trending topics detected in brand monitoring data.

    Args:
        brand: "decathlon" or "intersport"
        days: Lookback period in days
    """
    trending = _fetch_api("/api/trending")
    autodiscover = _fetch_api("/api/autodiscover")

    return json.dumps({
        "brand": brand,
        "trends": trending[:10] if isinstance(trending, list) else [],
        "new_sources_discovered": autodiscover.get("suggestions", [])[:5],
        "texts_scanned": autodiscover.get("stats", {}).get("texts_scanned", 0),
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def get_influencers(brand: str = "", limit: int = 10) -> str:
    """Get top influencers talking about the brand, classified as ambassador/neutral/detractor.

    Args:
        brand: Filter by "decathlon" or "intersport" (empty = both)
        limit: Number of influencers to return
    """
    influencers = _fetch_api("/api/influencers")
    if brand:
        influencers = [i for i in influencers if i.get("brand_focus") == brand]

    return json.dumps({
        "brand": brand or "both",
        "total": len(influencers),
        "influencers": influencers[:limit],
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def get_content_strategy_comparison() -> str:
    """Get AI-powered comparison of Decathlon vs Intersport content strategy across Instagram, TikTok, and Facebook Ads."""
    data = _fetch_api("/api/content-compare")
    return json.dumps(data, ensure_ascii=False, indent=2)


# ── Resources ──

@mcp.resource("licter://status")
def get_status() -> str:
    """Current system status and data freshness."""
    health = _fetch_api("/api/health")
    return json.dumps(health, indent=2)


@mcp.resource("licter://sources")
def get_sources() -> str:
    """List of all 13 data sources monitored."""
    return json.dumps({
        "sources": [
            {"name": "Google Maps", "type": "store reviews", "partition": "store"},
            {"name": "Trustpilot", "type": "customer reviews", "partition": "customer"},
            {"name": "Reddit", "type": "posts + comments", "partition": "community"},
            {"name": "YouTube", "type": "videos + comments + transcripts", "partition": "social"},
            {"name": "TikTok", "type": "videos + transcripts", "partition": "social"},
            {"name": "Instagram", "type": "posts", "partition": "social"},
            {"name": "X/Twitter", "type": "tweets", "partition": "social"},
            {"name": "Google News", "type": "articles", "partition": "news"},
            {"name": "Facebook Groups", "type": "posts", "partition": "community"},
            {"name": "Facebook Ads", "type": "ad library", "partition": "social"},
            {"name": "App Store", "type": "iOS reviews", "partition": "customer"},
            {"name": "Forums FR", "type": "posts", "partition": "community"},
            {"name": "CGV/Docs", "type": "official documents", "partition": "context"},
        ],
        "total": 13,
    }, indent=2)


if __name__ == "__main__":
    mcp.run()
