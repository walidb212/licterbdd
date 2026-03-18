"""Fonctions de calcul KPI — aucune dépendance externe."""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Helpers plateforme
# ---------------------------------------------------------------------------

def platform_from_source_name(source_name: str) -> str:
    s = source_name.lower()
    if "reddit" in s:
        return "Reddit"
    if "tiktok" in s:
        return "TikTok"
    if "youtube" in s:
        return "YouTube"
    if "twitter" in s or "tweet" in s or "x_" in s:
        return "Twitter/X"
    if "news" in s or "article" in s:
        return "Presse"
    if "review" in s or "trustpilot" in s or "glassdoor" in s:
        return "Avis"
    return "Autre"


# ---------------------------------------------------------------------------
# Gravity score
# ---------------------------------------------------------------------------

def gravity_score(records: list[dict]) -> float:
    if not records:
        return 0.0
    neg = sum(1 for r in records if r.get("sentiment_label") == "negative")
    neg_pct = neg / len(records)
    avg_prio = sum(r.get("priority_score", 0) for r in records) / len(records)
    # Ratio volume vs. baseline (1 record/day over 30 days = 30)
    baseline = 30.0
    spike = min(len(records) / baseline, 10.0)
    score = spike * neg_pct * (avg_prio / 100) * 10
    return round(min(score, 10.0), 1)


# ---------------------------------------------------------------------------
# Share of Voice
# ---------------------------------------------------------------------------

def sov(records: list[dict]) -> dict[str, float]:
    dec = sum(1 for r in records if r.get("brand_focus") == "decathlon")
    inter = sum(1 for r in records if r.get("brand_focus") == "intersport")
    total = dec + inter
    if total == 0:
        return {"decathlon": 0.5, "intersport": 0.5}
    return {
        "decathlon": round(dec / total, 3),
        "intersport": round(inter / total, 3),
    }


# ---------------------------------------------------------------------------
# Radar topics — mappe les themes vers des axes lisibles
# ---------------------------------------------------------------------------

_THEME_TO_TOPIC: dict[str, str] = {
    "prix_promo": "Prix",
    "service_client": "SAV",
    "qualite_produit": "Qualité",
    "community_engagement": "Engagement",
    "sponsoring_partnership": "Marques propres",
    "magasin_experience": "Service",
    "retour_remboursement": "SAV",
    "livraison_stock": "Livraison",
    "velo_mobilite": "Mobilité",
    "running_fitness": "Sport",
    "football_teamwear": "Marques propres",
    "brand_controversy": "Image",
}

_RADAR_AXES = ["Prix", "SAV", "Qualité", "Engagement", "Marques propres", "Service"]


def radar_topics(records: list[dict]) -> list[dict]:
    """Calcule pour chaque axe radar le % de mentions positives par marque."""
    by_brand: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for r in records:
        brand = r.get("brand_focus", "")
        if brand not in ("decathlon", "intersport"):
            continue
        sentiment = r.get("sentiment_label", "neutral")
        for theme in r.get("themes", []):
            topic = _THEME_TO_TOPIC.get(theme)
            if topic:
                by_brand[brand][topic].append(sentiment)

    result = []
    for axis in _RADAR_AXES:
        row: dict[str, Any] = {"topic": axis}
        for brand in ("decathlon", "intersport"):
            sentiments = by_brand[brand].get(axis, [])
            if not sentiments:
                row[brand] = 50  # neutre par défaut
            else:
                pos = sum(1 for s in sentiments if s == "positive")
                row[brand] = round(pos / len(sentiments) * 100)
        result.append(row)
    return result


# ---------------------------------------------------------------------------
# SOV par mois
# ---------------------------------------------------------------------------

def sov_by_month(records: list[dict]) -> list[dict]:
    monthly: dict[str, dict[str, int]] = defaultdict(lambda: {"decathlon": 0, "intersport": 0})
    for r in records:
        brand = r.get("brand_focus", "")
        if brand not in ("decathlon", "intersport"):
            continue
        pub = r.get("published_at", "")
        if not pub:
            continue
        try:
            dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            month_key = dt.strftime("%b %Y")
            monthly[month_key][brand] += 1
        except (ValueError, TypeError):
            pass

    result = []
    for month, counts in sorted(monthly.items(), key=lambda x: x[0]):
        total = counts["decathlon"] + counts["intersport"]
        if total == 0:
            continue
        result.append({
            "month": month,
            "decathlon": round(counts["decathlon"] / total * 100),
            "intersport": round(counts["intersport"] / total * 100),
        })
    return result


# ---------------------------------------------------------------------------
# Volume par jour
# ---------------------------------------------------------------------------

def volume_by_day(records: list[dict]) -> list[dict]:
    daily: Counter = Counter()
    for r in records:
        pub = r.get("published_at", "")
        if not pub:
            continue
        try:
            dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            daily[dt.strftime("%Y-%m-%d")] += 1
        except (ValueError, TypeError):
            pass
    return [{"date": d, "volume": c} for d, c in sorted(daily.items())]


# ---------------------------------------------------------------------------
# NPS proxy
# ---------------------------------------------------------------------------

def nps_proxy(reviews: list[dict]) -> float:
    ratings = []
    for r in reviews:
        try:
            ratings.append(float(r.get("rating", 0) or 0))
        except (ValueError, TypeError):
            pass
    if not ratings:
        return 0.0
    promoters = sum(1 for r in ratings if r >= 4)
    detractors = sum(1 for r in ratings if r <= 2)
    return round((promoters - detractors) / len(ratings) * 100, 1)


# ---------------------------------------------------------------------------
# Distribution des notes
# ---------------------------------------------------------------------------

def rating_distribution(reviews: list[dict]) -> list[dict]:
    counts: Counter = Counter()
    for r in reviews:
        try:
            star = round(float(r.get("rating", 0) or 0))
            if 1 <= star <= 5:
                counts[star] += 1
        except (ValueError, TypeError):
            pass
    total = sum(counts.values()) or 1
    return [
        {"stars": s, "count": counts.get(s, 0), "pct": round(counts.get(s, 0) / total * 100)}
        for s in range(1, 6)
    ]


# ---------------------------------------------------------------------------
# Rating par mois (approximation depuis date_raw)
# ---------------------------------------------------------------------------

_DATE_RAW_RE = re.compile(r"il y a (\d+)\s*(jour|mois|semaine|an)", re.IGNORECASE)
_MONTHS_FR = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun", "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]


def _approx_date_from_raw(date_raw: str, ref: date) -> date | None:
    m = _DATE_RAW_RE.search(date_raw)
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2).lower()
    if "jour" in unit:
        return ref - timedelta(days=n)
    if "semaine" in unit:
        return ref - timedelta(weeks=n)
    if "mois" in unit:
        month = ref.month - n
        year = ref.year
        while month <= 0:
            month += 12
            year -= 1
        return ref.replace(year=year, month=month, day=1)
    if "an" in unit:
        return ref.replace(year=ref.year - n, day=1)
    return None


def rating_by_month(reviews: list[dict]) -> list[dict]:
    ref = date.today()
    monthly: dict[str, dict[str, list[float]]] = defaultdict(lambda: {"decathlon": [], "intersport": []})
    for r in reviews:
        brand = r.get("brand_focus", "decathlon")
        if brand not in ("decathlon", "intersport"):
            brand = "decathlon"
        try:
            rating = float(r.get("rating", 0) or 0)
        except (ValueError, TypeError):
            continue
        if not (1 <= rating <= 5):
            continue
        # Try published_at first
        pub = r.get("published_at", "")
        d = None
        if pub:
            try:
                d = datetime.fromisoformat(pub.replace("Z", "+00:00")).date()
            except (ValueError, TypeError):
                pass
        if d is None:
            d = _approx_date_from_raw(r.get("date_raw", ""), ref)
        if d is None:
            continue
        key = f"{_MONTHS_FR[d.month - 1]} {d.year}"
        monthly[key][brand].append(rating)

    result = []
    for key, brands in sorted(monthly.items()):
        row: dict[str, Any] = {"month": key}
        for brand in ("decathlon", "intersport"):
            vals = brands[brand]
            row[brand] = round(sum(vals) / len(vals), 2) if vals else None
        result.append(row)
    return result[-12:]  # 12 derniers mois


# ---------------------------------------------------------------------------
# Irritants / Enchantements
# ---------------------------------------------------------------------------

_THEME_LABELS: dict[str, str] = {
    "service_client": "SAV injoignable",
    "retour_remboursement": "Retours complexes",
    "livraison_stock": "Ruptures stock",
    "qualite_produit": "Qualité produit",
    "magasin_experience": "Attente en caisse",
    "prix_promo": "Rapport qualité/prix",
    "community_engagement": "Engagement communauté",
    "sponsoring_partnership": "Partenariats",
    "velo_mobilite": "Vélo / Mobilité",
    "running_fitness": "Running / Sport",
    "brand_controversy": "Image de marque",
    "football_teamwear": "Marques sportives",
}


def irritants_from_records(records: list[dict], top_n: int = 5) -> list[dict]:
    neg = [r for r in records if r.get("sentiment_label") in ("negative", "mixed")]
    theme_counts: Counter = Counter()
    for r in neg:
        for t in r.get("themes", []):
            theme_counts[t] += 1
    total = sum(theme_counts.values()) or 1
    top = theme_counts.most_common(top_n)
    max_count = top[0][1] if top else 1
    return [
        {
            "label": _THEME_LABELS.get(t, t.replace("_", " ").title()),
            "count": c,
            "pct": round(c / total * 100),
            "bar_pct": round(c / max_count * 100),
        }
        for t, c in top
    ]


def enchantements_from_records(records: list[dict], top_n: int = 3) -> list[dict]:
    pos = [r for r in records if r.get("sentiment_label") == "positive"]
    theme_counts: Counter = Counter()
    for r in pos:
        for t in r.get("themes", []):
            theme_counts[t] += 1
    total = sum(theme_counts.values()) or 1
    top = theme_counts.most_common(top_n)
    max_count = top[0][1] if top else 1
    return [
        {
            "label": _THEME_LABELS.get(t, t.replace("_", " ").title()),
            "count": c,
            "pct": round(c / total * 100),
            "bar_pct": round(c / max_count * 100),
        }
        for t, c in top
    ]
