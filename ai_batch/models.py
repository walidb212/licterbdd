from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PreparedRecord:
    source_run_id: str
    source_name: str
    source_partition: str
    brand_focus: str
    entity_name: str
    item_key: str
    pillar: str
    published_at: str
    title: str
    content_text: str
    author: str
    source_url: str
    raw_language: str
    engagement_score: int
    rating: float | None = None
    aggregate_rating: float | None = None
    aggregate_count: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_prompt_payload(self) -> dict[str, Any]:
        return {
            "item_key": self.item_key,
            "brand_focus": self.brand_focus,
            "entity_name": self.entity_name,
            "source_partition": self.source_partition,
            "source_name": self.source_name,
            "pillar": self.pillar,
            "published_at": self.published_at,
            "title": self.title,
            "content_text": self.content_text,
            "author": self.author,
            "source_url": self.source_url,
            "raw_language": self.raw_language,
            "engagement_score": self.engagement_score,
            "rating": self.rating,
            "aggregate_rating": self.aggregate_rating,
            "aggregate_count": self.aggregate_count,
            "metadata": self.metadata,
        }


@dataclass
class EnrichedRecord:
    run_id: str
    source_run_id: str
    source_partition: str
    brand_focus: str
    entity_name: str
    item_key: str
    language: str
    sentiment_label: str
    sentiment_confidence: float
    themes: list[str]
    risk_flags: list[str]
    opportunity_flags: list[str]
    priority_score: int
    summary_short: str
    evidence_spans: list[str]
    pillar: str = ""
    source_name: str = ""
    published_at: str = ""
    provider: str = ""
    model: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EntitySummaryRecord:
    brand_focus: str
    source_partition: str
    entity_name: str
    period_start: str
    period_end: str
    volume_items: int
    top_themes: list[str]
    top_risks: list[str]
    top_opportunities: list[str]
    executive_takeaway: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BatchRunResult:
    run_id: str
    run_dir: str
    provider: str
    model: str
    input_runs: dict[str, str]
    social_records: list[EnrichedRecord]
    review_records: list[EnrichedRecord]
    news_records: list[EnrichedRecord]
    entity_summaries: list[EntitySummaryRecord]
    warnings: list[str]
