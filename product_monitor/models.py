from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class CategorySource:
    brand_focus: str
    category: str
    url: str
    seed_products: tuple[str, ...] = ()


@dataclass
class ProductCandidate:
    brand_focus: str
    category: str
    product_url: str
    product_name: str
    review_count_hint: int | None = None
    rating_hint: float | None = None
    discovery_source: str = ""


@dataclass
class ProductRecord:
    run_id: str
    brand_focus: str
    category: str
    source_partition: str
    entity_level: str
    entity_name: str
    product_url: str
    discovery_source: str
    aggregate_rating: float | None
    aggregate_count: int | None
    rating_hint: float | None
    review_count_hint: int | None
    fetch_mode: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProductReviewRecord:
    run_id: str
    brand_focus: str
    category: str
    source_partition: str
    entity_level: str
    entity_name: str
    product_url: str
    author: str
    published_at: str
    rating: float | None
    aggregate_rating: float | None
    aggregate_count: int | None
    title: str
    body: str
    language_raw: str = "fr"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RunArtifacts:
    run_id: str
    run_dir: str
    products_path: str
    reviews_path: str
    results_md_path: str


@dataclass
class RunResult:
    run_id: str
    run_dir: str
    selected_brand: str
    max_products_per_brand: int
    products: list[ProductRecord]
    reviews: list[ProductReviewRecord]
    warnings: list[str] = field(default_factory=list)
