from __future__ import annotations

from .models import Seed


DEFAULT_SEEDS: tuple[Seed, ...] = (
    # ── Subreddit ────────────────────────────────────────────────────────────
    Seed(
        name="decathlon_subreddit",
        brand_focus="decathlon",
        seed_type="subreddit",
        url="https://www.reddit.com/r/Decathlon/",
        description="Brand-owned subreddit index — no date filter (homepage).",
    ),

    # ── Benchmark (1 an) ─────────────────────────────────────────────────────
    Seed(
        name="search_decathlon_year",
        brand_focus="decathlon",
        seed_type="search",
        url="https://www.reddit.com/search/?q=decathlon&t=year",
        description="Decathlon mentions sur 1 an — fenêtre benchmark.",
    ),
    Seed(
        name="search_intersport_year",
        brand_focus="intersport",
        seed_type="search",
        url="https://www.reddit.com/search/?q=intersport&t=year",
        description="Intersport mentions sur 1 an — fenêtre benchmark.",
    ),
    Seed(
        name="search_decathlon_vs_intersport_year",
        brand_focus="both",
        seed_type="search",
        url="https://www.reddit.com/search/?q=decathlon+vs+intersport&t=year",
        description="Comparaisons directes sur 1 an — Share of Voice.",
    ),
    Seed(
        name="search_decathlon_quality_year",
        brand_focus="decathlon",
        seed_type="search",
        url="https://www.reddit.com/search/?q=%22decathlon%22+quality&t=year",
        description="Qualité produit sur 1 an.",
    ),
    Seed(
        name="search_decathlon_return_year",
        brand_focus="decathlon",
        seed_type="search",
        url="https://www.reddit.com/search/?q=%22decathlon%22+return&t=year",
        description="Retours / SAV sur 1 an.",
    ),
    Seed(
        name="search_intersport_service_year",
        brand_focus="intersport",
        seed_type="search",
        url="https://www.reddit.com/search/?q=%22intersport%22+service&t=year",
        description="Service Intersport sur 1 an.",
    ),

    # ── Crise vélo (dernier mois) ─────────────────────────────────────────────
    Seed(
        name="search_decathlon_bike_crisis_month",
        brand_focus="decathlon",
        seed_type="search",
        url="https://www.reddit.com/search/?q=decathlon+bike+accident&t=month",
        description="Crise vélo défectueux — dernier mois (fév-mars 2026).",
    ),
    Seed(
        name="search_decathlon_recall_month",
        brand_focus="decathlon",
        seed_type="search",
        url="https://www.reddit.com/search/?q=decathlon+recall&t=month",
        description="Rappel produit Decathlon — dernier mois.",
    ),
    Seed(
        name="search_decathlon_velo_month",
        brand_focus="decathlon",
        seed_type="search",
        url="https://www.reddit.com/search/?q=decathlon+v%C3%A9lo&t=month",
        description="Mentions vélo Decathlon en français — dernier mois.",
    ),

    # ── Pulse live (dernière semaine) ─────────────────────────────────────────
    Seed(
        name="search_decathlon_week",
        brand_focus="decathlon",
        seed_type="search",
        url="https://www.reddit.com/search/?q=decathlon&t=week",
        description="Pulse live Decathlon — 7 derniers jours.",
    ),
    Seed(
        name="search_intersport_week",
        brand_focus="intersport",
        seed_type="search",
        url="https://www.reddit.com/search/?q=intersport&t=week",
        description="Pulse live Intersport — 7 derniers jours.",
    ),

    # ── Europe / France (focus marché principal) ──────────────────────────────
    Seed(
        name="france_decathlon_month",
        brand_focus="decathlon",
        seed_type="subreddit",
        url="https://www.reddit.com/r/france/search/?q=decathlon&t=month&restrict_sr=1",
        description="Mentions Decathlon sur r/france — dernier mois (crise + actualité FR).",
    ),
    Seed(
        name="france_decathlon_year",
        brand_focus="decathlon",
        seed_type="subreddit",
        url="https://www.reddit.com/r/france/search/?q=decathlon&t=year&restrict_sr=1",
        description="Mentions Decathlon sur r/france — 1 an (benchmark FR).",
    ),
    Seed(
        name="velo_decathlon_month",
        brand_focus="decathlon",
        seed_type="subreddit",
        url="https://www.reddit.com/r/velo/search/?q=decathlon&t=month&restrict_sr=1",
        description="Crise vélo — r/velo francophone dernier mois.",
    ),
    Seed(
        name="cyclisme_decathlon_month",
        brand_focus="decathlon",
        seed_type="subreddit",
        url="https://www.reddit.com/r/cyclisme/search/?q=decathlon&t=month&restrict_sr=1",
        description="Crise vélo — r/cyclisme francophone dernier mois.",
    ),
    Seed(
        name="belgium_decathlon_year",
        brand_focus="decathlon",
        seed_type="subreddit",
        url="https://www.reddit.com/r/belgium/search/?q=decathlon&t=year&restrict_sr=1",
        description="Mentions Decathlon sur r/belgium — 1 an.",
    ),
    Seed(
        name="askeurope_decathlon_year",
        brand_focus="both",
        seed_type="subreddit",
        url="https://www.reddit.com/r/AskEurope/search/?q=decathlon+intersport&t=year&restrict_sr=1",
        description="Comparaisons EU Decathlon vs Intersport — r/AskEurope 1 an.",
    ),
    Seed(
        name="germany_decathlon_year",
        brand_focus="decathlon",
        seed_type="subreddit",
        url="https://www.reddit.com/r/germany/search/?q=decathlon&t=year&restrict_sr=1",
        description="Mentions Decathlon sur r/germany — marché DE.",
    ),
    Seed(
        name="italy_decathlon_year",
        brand_focus="decathlon",
        seed_type="subreddit",
        url="https://www.reddit.com/r/italy/search/?q=decathlon&t=year&restrict_sr=1",
        description="Mentions Decathlon sur r/italy — marché IT.",
    ),
    Seed(
        name="spain_decathlon_year",
        brand_focus="decathlon",
        seed_type="subreddit",
        url="https://www.reddit.com/r/spain/search/?q=decathlon&t=year&restrict_sr=1",
        description="Mentions Decathlon sur r/spain — marché ES.",
    ),
)


def select_seeds(brand: str) -> list[Seed]:
    if brand == "both":
        return list(DEFAULT_SEEDS)
    return [seed for seed in DEFAULT_SEEDS if seed.brand_focus in {brand, "both"}]
