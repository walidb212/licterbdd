from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Seed:
    name: str
    brand_focus: str
    seed_type: str
    url: str
    description: str


@dataclass
class CandidateLink:
    post_url: str
    seed_name: str
    seed_url: str
    seed_type: str
    brand_focus: str
    anchor_text: str = ""
    title_hint: str = ""
    subreddit_hint: str = ""
    candidate_relevance: float = 0.0


@dataclass
class SeedReport:
    seed_name: str
    seed_url: str
    brand_focus: str
    seed_type: str
    discovered_count: int = 0
    unique_count: int = 0
    duplicate_count: int = 0
    filtered_count: int = 0
    blank_anchor_count: int = 0
    error: str = ""
    samples: list[str] = field(default_factory=list)


@dataclass
class PostRecord:
    run_id: str
    brand_focus: str
    seed_url: str
    seed_type: str
    post_url: str
    subreddit: str
    post_title: str
    post_text: str
    author: str
    created_at: str
    score: int | None
    comment_count: int | None
    domain: str
    language_raw: str
    relevance_score: float
    source_partition: str = "community"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CommentRecord:
    run_id: str
    brand_focus: str
    post_url: str
    subreddit: str
    comment_index: int
    comment_author: str
    comment_text: str
    comment_score_raw: str
    comment_meta_raw: dict[str, Any]
    language_raw: str
    source_partition: str = "community"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RunArtifacts:
    run_id: str
    run_dir: str
    posts_path: str
    comments_path: str


@dataclass
class MonitorResult:
    run_id: str
    run_dir: str
    selected_brand: str
    seed_reports: list[SeedReport]
    posts: list[PostRecord]
    comments: list[CommentRecord]
    warnings: list[str]
