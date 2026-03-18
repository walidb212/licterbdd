from __future__ import annotations

from dataclasses import asdict, dataclass

SOURCE_PARTITION = "social"
DEFAULT_MAX_ITEMS_PER_SOURCE = 5

@dataclass(frozen=True)
class SourceConfig:
    name: str
    brand_focus: str
    source_type: str
    query_text: str
    pillar: str
    production_status: str
    coverage_note: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


SOURCE_CONFIGS: tuple[SourceConfig, ...] = (
    SourceConfig(
        name="decathlon_official_account",
        brand_focus="decathlon",
        source_type="account",
        query_text="https://www.tiktok.com/@decathlon",
        pillar="reputation",
        production_status="supported",
        coverage_note="Official account extraction is the supported V1 production path.",
    ),
    SourceConfig(
        name="intersport_fr_official_account",
        brand_focus="intersport",
        source_type="account",
        query_text="https://www.tiktok.com/@intersportfr",
        pillar="reputation",
        production_status="supported",
        coverage_note="Official account extraction is the supported V1 production path.",
    ),
    SourceConfig(
        name="decathlon_tag",
        brand_focus="decathlon",
        source_type="hashtag",
        query_text="https://www.tiktok.com/tag/decathlon",
        pillar="reputation",
        production_status="experimental",
        coverage_note="Hashtag extraction remains experimental and is excluded from V1 production runs by default.",
    ),
    SourceConfig(
        name="intersport_tag",
        brand_focus="intersport",
        source_type="hashtag",
        query_text="https://www.tiktok.com/tag/intersport",
        pillar="reputation",
        production_status="experimental",
        coverage_note="Hashtag extraction remains experimental and is excluded from V1 production runs by default.",
    ),
    SourceConfig(
        name="rockrider_tag",
        brand_focus="decathlon",
        source_type="hashtag",
        query_text="https://www.tiktok.com/tag/rockrider",
        pillar="cx",
        production_status="experimental",
        coverage_note="Hashtag extraction remains experimental and is excluded from V1 production runs by default.",
    ),
    SourceConfig(
        name="nakamura_tag",
        brand_focus="intersport",
        source_type="hashtag",
        query_text="https://www.tiktok.com/tag/nakamura",
        pillar="cx",
        production_status="experimental",
        coverage_note="Hashtag extraction remains experimental and is excluded from V1 production runs by default.",
    ),
    SourceConfig(
        name="sportpascher_tag",
        brand_focus="both",
        source_type="hashtag",
        query_text="https://www.tiktok.com/tag/sportpascher",
        pillar="benchmark",
        production_status="experimental",
        coverage_note="Hashtag extraction remains experimental and is excluded from V1 production runs by default.",
    ),
)


def list_sources(brand: str) -> list[SourceConfig]:
    if brand == "both":
        return list(SOURCE_CONFIGS)
    return [row for row in SOURCE_CONFIGS if row.brand_focus in {brand, "both"}]


def is_source_enabled(source: SourceConfig, *, include_experimental: bool = False) -> bool:
    return source.production_status == "supported" or include_experimental


def select_sources(brand: str, *, include_experimental: bool = False) -> list[SourceConfig]:
    return [row for row in list_sources(brand) if is_source_enabled(row, include_experimental=include_experimental)]
