from __future__ import annotations

from .models import ContextSource


DEFAULT_SOURCES: tuple[ContextSource, ...] = (
    ContextSource("decathlon_avis_policy", "decathlon", "avis-policy", "https://www.decathlon.fr/help/services/_/R-a-reviews-terms-and-conditions"),
    ContextSource("decathlon_returns", "decathlon", "retours", "https://support.decathlon.fr/echange-et-remboursement"),
    ContextSource("decathlon_delivery", "decathlon", "livraison", "https://www.decathlon.fr/lp/i/modes-livraison"),
    ContextSource("decathlon_atelier", "decathlon", "atelier", "https://support.decathlon.fr/notre-mission-sav"),
    ContextSource("decathlon_services", "decathlon", "services", "https://support.decathlon.fr/contact"),
    ContextSource("intersport_cgv", "intersport", "cgv", "https://media.intersport.fr/is/content/intersportfr/pdf/cgv/Conditions%20g%C3%A9n%C3%A9rales%20de%20vente%20sur%20internet%20Intersport.pdf"),
    ContextSource("intersport_returns", "intersport", "retours", "https://www.intersport.fr/faq-retours-et-remboursements/"),
    ContextSource("intersport_delivery", "intersport", "livraison", "https://www.intersport.fr/faq-livraison/"),
    ContextSource("intersport_sav", "intersport", "sav", "https://www.intersport.fr/contact/"),
    ContextSource("intersport_atelier", "intersport", "atelier", "https://www.intersport.fr/ateliers-reparation-velo/"),
)


def select_sources(brand: str, document_types: str) -> list[ContextSource]:
    sources = list(DEFAULT_SOURCES)
    if brand != "both":
        sources = [row for row in sources if row.brand_focus == brand]
    if document_types != "all":
        allowed = {item.strip() for item in document_types.split(",") if item.strip()}
        sources = [row for row in sources if row.document_type in allowed]
    return sources
