from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SourceConfig:
    name: str
    site: str
    brand_focus: str
    review_scope: str
    url: str
    entity_level: str = "brand"
    entity_name: str = ""
    source_symmetry: str = "common"


@dataclass
class SourceSummary:
    run_id: str
    source_name: str
    site: str
    brand_focus: str
    review_scope: str
    entity_level: str
    entity_name: str
    source_url: str
    source_symmetry: str
    aggregate_rating: float | None
    aggregate_count: int | None
    extracted_reviews: int
    source_partition: str = "customer"
    fetch_mode: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReviewRecord:
    run_id: str
    site: str
    brand_focus: str
    review_scope: str
    entity_level: str
    entity_name: str
    location: str
    source_name: str
    source_url: str
    source_symmetry: str
    review_url: str
    author: str
    published_at: str
    experience_date: str
    rating: float | None
    aggregate_rating: float | None
    aggregate_count: int | None
    title: str
    body: str
    language_raw: str
    source_partition: str = "customer"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RunArtifacts:
    run_id: str
    run_dir: str
    reviews_path: str
    sources_path: str
    results_md_path: str


@dataclass
class RunResult:
    run_id: str
    run_dir: str
    selected_brand: str
    selected_site: str
    selected_scope: str
    sources: list[SourceSummary]
    reviews: list[ReviewRecord]
    warnings: list[str]
