from __future__ import annotations

from .models import Seed


DEFAULT_SEEDS: tuple[Seed, ...] = (
    Seed(
        name="decathlon_subreddit",
        brand_focus="decathlon",
        seed_type="subreddit",
        url="https://www.reddit.com/r/Decathlon/",
        description="Brand-owned or brand-focused subreddit index.",
    ),
    Seed(
        name="search_decathlon",
        brand_focus="decathlon",
        seed_type="search",
        url="https://www.reddit.com/search/?q=decathlon",
        description="Generic Reddit search for Decathlon mentions.",
    ),
    Seed(
        name="search_intersport",
        brand_focus="intersport",
        seed_type="search",
        url="https://www.reddit.com/search/?q=intersport",
        description="Generic Reddit search for Intersport mentions.",
    ),
    Seed(
        name="search_decathlon_vs_intersport",
        brand_focus="both",
        seed_type="search",
        url="https://www.reddit.com/search/?q=decathlon+vs+intersport",
        description="Benchmark-oriented seed for direct comparisons.",
    ),
    Seed(
        name="search_decathlon_quality",
        brand_focus="decathlon",
        seed_type="search",
        url="https://www.reddit.com/search/?q=%22decathlon%22+quality",
        description="Product quality and perception seed.",
    ),
    Seed(
        name="search_decathlon_return",
        brand_focus="decathlon",
        seed_type="search",
        url="https://www.reddit.com/search/?q=%22decathlon%22+return",
        description="Returns, service, and CX friction seed.",
    ),
    Seed(
        name="search_intersport_service",
        brand_focus="intersport",
        seed_type="search",
        url="https://www.reddit.com/search/?q=%22intersport%22+service",
        description="Service and CX seed for Intersport.",
    ),
)


def select_seeds(brand: str) -> list[Seed]:
    if brand == "both":
        return list(DEFAULT_SEEDS)
    return [seed for seed in DEFAULT_SEEDS if seed.brand_focus in {brand, "both"}]
