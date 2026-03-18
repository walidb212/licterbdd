from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class StoreRecord:
    run_id: str
    brand_focus: str
    store_name: str
    store_url: str
    address: str
    postal_code: str
    city: str
    google_maps_url: str
    discovery_source: str
    status: str
    source_partition: str = "store"
    source_symmetry: str = "common"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StoreReviewRecord:
    run_id: str
    brand_focus: str
    site: str
    review_scope: str
    entity_level: str
    entity_name: str
    location: str
    rating: float | None
    date_raw: str
    author: str
    body: str
    aggregate_rating: float | None
    aggregate_count: int | None
    source_url: str
    source_symmetry: str
    store_url: str
    google_maps_url: str
    language_raw: str = "fr"
    source_partition: str = "store"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RunArtifacts:
    run_id: str
    run_dir: str
    stores_path: str
    reviews_path: str
    results_md_path: str


@dataclass
class RunResult:
    run_id: str
    run_dir: str
    selected_brand: str
    selected_stage: str
    stores: list[StoreRecord]
    reviews: list[StoreReviewRecord]
    warnings: list[str] = field(default_factory=list)
