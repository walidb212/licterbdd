from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class QuerySpec:
    name: str
    brand_focus: str
    query_text: str
    rss_url: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QueryRun:
    run_id: str
    query_name: str
    brand_focus: str
    query_text: str
    rss_url: str
    fetched_count: int = 0
    retained_count: int = 0
    added_count: int = 0
    warning: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NewsArticleRecord:
    run_id: str
    query_name: str
    query_text: str
    query_names: list[str]
    brand_focus: str
    source_brand_focuses: list[str]
    article_id: str
    article_title: str
    published_at: str
    source_name: str
    source_domain: str
    google_news_url: str
    description_html: str
    description_text: str
    signal_type: str
    brand_detected: str
    article_markdown: str = ""
    article_snapshot_url: str = ""
    enrichment_mode: str = "none"
    source_partition: str = "news"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RunArtifacts:
    run_id: str
    run_dir: str
    queries_path: str
    articles_path: str
    results_md_path: str


@dataclass
class RunResult:
    run_id: str
    run_dir: str
    selected_brand: str
    selected_region: str
    query_runs: list[QueryRun]
    articles: list[NewsArticleRecord]
    cloudflare_mode: str
    warnings: list[str] = field(default_factory=list)
