from __future__ import annotations

from .models import Seed


DEFAULT_SEEDS: tuple[Seed, ...] = (
    # ── Subreddit officiel ───────────────────────────────────────────
    Seed(
        name="decathlon_subreddit",
        brand_focus="decathlon",
        seed_type="subreddit",
        url="https://www.reddit.com/r/Decathlon/",
        description="Brand-owned subreddit.",
    ),

    # ── France & francophone ─────────────────────────────────────────
    Seed(
        name="france_decathlon_year",
        brand_focus="decathlon",
        seed_type="subreddit",
        url="https://www.reddit.com/r/france/search/?q=decathlon&t=year&restrict_sr=1",
        description="r/france mentions Decathlon — 1 an.",
    ),
    Seed(
        name="france_intersport_year",
        brand_focus="intersport",
        seed_type="subreddit",
        url="https://www.reddit.com/r/france/search/?q=intersport&t=year&restrict_sr=1",
        description="r/france mentions Intersport — 1 an.",
    ),
    Seed(
        name="velo_decathlon_year",
        brand_focus="decathlon",
        seed_type="subreddit",
        url="https://www.reddit.com/r/pedale/search/?q=decathlon&t=year&restrict_sr=1",
        description="r/pedale (vélo FR) mentions Decathlon.",
    ),

    # ── Search global (mais filtre FR côté app.py) ───────────────────
    Seed(
        name="search_decathlon_month",
        brand_focus="decathlon",
        seed_type="search",
        url="https://www.reddit.com/search/?q=decathlon+france&t=month",
        description="Decathlon France — dernier mois.",
    ),
    Seed(
        name="search_intersport_month",
        brand_focus="intersport",
        seed_type="search",
        url="https://www.reddit.com/search/?q=intersport+france&t=month",
        description="Intersport France — dernier mois.",
    ),
    Seed(
        name="search_decathlon_vs_intersport",
        brand_focus="both",
        seed_type="search",
        url="https://www.reddit.com/search/?q=decathlon+vs+intersport&t=year",
        description="Comparaisons directes — benchmark.",
    ),

    # ── Crise vélo ───────────────────────────────────────────────────
    Seed(
        name="search_decathlon_velo_crise",
        brand_focus="decathlon",
        seed_type="search",
        url="https://www.reddit.com/search/?q=decathlon+velo+accident+defectueux&t=month",
        description="Crise vélo — dernier mois.",
    ),

    # ── CX & SAV ────────────────────────────────────────────────────
    Seed(
        name="search_decathlon_sav",
        brand_focus="decathlon",
        seed_type="search",
        url="https://www.reddit.com/search/?q=decathlon+SAV+retour&t=year",
        description="SAV Decathlon.",
    ),

    # ── Pulse live (dernière semaine) ────────────────────────────────
    Seed(
        name="search_decathlon_week",
        brand_focus="decathlon",
        seed_type="search",
        url="https://www.reddit.com/search/?q=decathlon&t=week",
        description="Pulse live Decathlon — 7 jours.",
    ),
    Seed(
        name="search_intersport_week",
        brand_focus="intersport",
        seed_type="search",
        url="https://www.reddit.com/search/?q=intersport&t=week",
        description="Pulse live Intersport — 7 jours.",
    ),
)


def select_seeds(brand: str) -> list[Seed]:
    if brand == "both":
        return list(DEFAULT_SEEDS)
    return [seed for seed in DEFAULT_SEEDS if seed.brand_focus in {brand, "both"}]
