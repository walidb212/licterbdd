from __future__ import annotations

from .models import CategorySource


DEFAULT_CATEGORIES = ("running", "cycling", "fitness", "outdoor", "football")


CATEGORY_SOURCES: tuple[CategorySource, ...] = (
    CategorySource("decathlon", "running", "https://www.decathlon.fr/tous-les-sports/running-route"),
    CategorySource("decathlon", "cycling", "https://www.decathlon.fr/tous-les-sports/velo-cyclisme"),
    CategorySource("decathlon", "fitness", "https://www.decathlon.fr/tous-les-sports/fitness-cardio-training"),
    CategorySource("decathlon", "outdoor", "https://www.decathlon.fr/tous-les-sports/randonnee-trekking"),
    CategorySource("decathlon", "football", "https://www.decathlon.fr/tous-les-sports/football"),
    CategorySource("intersport", "running", "https://www.intersport.fr/ope/sporting-days/running/"),
    CategorySource("intersport", "cycling", "https://www.intersport.fr/sports/cycle/equipement-du-cycliste/chaussettes/"),
    CategorySource("intersport", "fitness", "https://www.intersport.fr/sports/fitness-musculation/"),
    CategorySource("intersport", "outdoor", "https://www.intersport.fr/ope/sporting-days/randonnee/"),
    CategorySource("intersport", "football", "https://www.intersport.fr/sports/football/"),
)


def select_category_sources(brand: str) -> list[CategorySource]:
    if brand == "both":
        return list(CATEGORY_SOURCES)
    return [row for row in CATEGORY_SOURCES if row.brand_focus == brand]
