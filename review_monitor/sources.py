from __future__ import annotations

from .models import SourceConfig


DEFAULT_SOURCES: tuple[SourceConfig, ...] = (
    SourceConfig(
        name="trustpilot_decathlon",
        site="trustpilot",
        brand_focus="decathlon",
        review_scope="customer",
        url="https://fr.trustpilot.com/review/www.decathlon.fr",
        entity_name="Decathlon France",
    ),
    SourceConfig(
        name="trustpilot_intersport",
        site="trustpilot",
        brand_focus="intersport",
        review_scope="customer",
        url="https://fr.trustpilot.com/review/www.intersport.fr",
        entity_name="Intersport France",
    ),
    SourceConfig(
        name="custplace_decathlon",
        site="custplace",
        brand_focus="decathlon",
        review_scope="customer",
        url="https://fr.custplace.com/decathlon",
        entity_name="Decathlon France",
    ),
    SourceConfig(
        name="custplace_intersport",
        site="custplace",
        brand_focus="intersport",
        review_scope="customer",
        url="https://fr.custplace.com/intersport",
        entity_name="Intersport France",
    ),
    SourceConfig(
        name="glassdoor_decathlon",
        site="glassdoor",
        brand_focus="decathlon",
        review_scope="employee",
        url="https://www.glassdoor.fr/Avis/Decathlon-Avis-E41180.htm",
        entity_name="Decathlon",
    ),
    SourceConfig(
        name="glassdoor_intersport",
        site="glassdoor",
        brand_focus="intersport",
        review_scope="employee",
        url="https://www.glassdoor.fr/Avis/Intersport-France-Avis-E3142277.htm",
        entity_name="Intersport France",
    ),
    SourceConfig(
        name="indeed_decathlon",
        site="indeed",
        brand_focus="decathlon",
        review_scope="employee",
        url="https://fr.indeed.com/cmp/Decathlon/reviews",
        entity_name="Decathlon",
    ),
    SourceConfig(
        name="indeed_intersport",
        site="indeed",
        brand_focus="intersport",
        review_scope="employee",
        url="https://fr.indeed.com/cmp/Intersport-8/reviews",
        entity_name="Intersport France",
    ),
    SourceConfig(
        name="poulpeo_decathlon",
        site="poulpeo",
        brand_focus="decathlon",
        review_scope="customer",
        url="https://www.poulpeo.com/avis/decathlon.htm",
        entity_name="Decathlon France",
    ),
    SourceConfig(
        name="poulpeo_intersport",
        site="poulpeo",
        brand_focus="intersport",
        review_scope="customer",
        url="https://www.poulpeo.com/avis/intersport.htm",
        entity_name="Intersport France",
    ),
    SourceConfig(
        name="ebuyclub_decathlon",
        site="ebuyclub",
        brand_focus="decathlon",
        review_scope="customer",
        url="https://www.ebuyclub.com/avis/decathlon-880",
        entity_name="Decathlon France",
    ),
    SourceConfig(
        name="ebuyclub_intersport",
        site="ebuyclub",
        brand_focus="intersport",
        review_scope="customer",
        url="https://www.ebuyclub.com/avis/intersport-1251",
        entity_name="Intersport France",
    ),
    SourceConfig(
        name="dealabs_decathlon",
        site="dealabs",
        brand_focus="decathlon",
        review_scope="promo",
        url="https://www.dealabs.com/search?q=decathlon",
        entity_name="Decathlon France",
    ),
    SourceConfig(
        name="dealabs_intersport",
        site="dealabs",
        brand_focus="intersport",
        review_scope="promo",
        url="https://www.dealabs.com/search?q=intersport",
        entity_name="Intersport France",
    ),
    SourceConfig(
        name="appstore_decathlon",
        site="appstore",
        brand_focus="decathlon",
        review_scope="customer",
        url="https://apps.apple.com/fr/app/id583732498",
        entity_name="Decathlon App",
    ),
    SourceConfig(
        name="appstore_intersport",
        site="appstore",
        brand_focus="intersport",
        review_scope="customer",
        url="https://apps.apple.com/fr/app/id1579487998",
        entity_name="Intersport App",
    ),
    SourceConfig(
        name="avis_verifies_decathlon",
        site="avis_verifies",
        brand_focus="decathlon",
        review_scope="customer",
        url="https://www.avis-verifies.com/avis-clients/decathlon.fr",
        entity_name="Decathlon France",
    ),
    SourceConfig(
        name="avis_verifies_intersport",
        site="avis_verifies",
        brand_focus="intersport",
        review_scope="customer",
        url="https://www.avis-verifies.com/avis-clients/intersport.fr",
        entity_name="Intersport France",
    ),
    SourceConfig(
        name="forums_decathlon",
        site="forum",
        brand_focus="decathlon",
        review_scope="community",
        url="",
        entity_name="Decathlon (forums)",
    ),
    SourceConfig(
        name="forums_intersport",
        site="forum",
        brand_focus="intersport",
        review_scope="community",
        url="",
        entity_name="Intersport (forums)",
    ),
)


def select_sources(site: str, brand: str, scope: str) -> list[SourceConfig]:
    sources = list(DEFAULT_SOURCES)
    if site != "all":
        sources = [source for source in sources if source.site == site]
    if brand != "both":
        sources = [source for source in sources if source.brand_focus == brand]
    if scope != "all":
        sources = [source for source in sources if source.review_scope == scope]
    return sources
