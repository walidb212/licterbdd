from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class QuerySpec:
    name: str
    brand_focus: str
    query_text: str
    search_type: str
    count: int
    pages: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QueryRun:
    run_id: str
    query_name: str
    brand_focus: str
    query_text: str
    search_type: str
    count: int
    pages: int
    command: str
    raw_count: int = 0
    retained_count: int = 0
    added_count: int = 0
    warning: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RawTweetRecord:
    run_id: str
    query_name: str
    query_text: str
    search_type: str
    brand_focus: str
    tweet_id: str
    raw_tweet: dict[str, Any]
    source_partition: str = "social"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NormalizedTweetRecord:
    run_id: str
    query_name: str
    query_text: str
    search_type: str
    query_names: list[str]
    query_texts: list[str]
    search_types: list[str]
    brand_focus: str
    source_brand_focuses: list[str]
    review_id: str
    platform: str
    brand: str
    post_type: str
    text: str
    date: str
    rating: int
    likes: int
    share_count: int
    reply_count: int
    quote_count: int
    view_count: int
    sentiment: str
    user_followers: int | None
    is_verified: bool
    language: str
    location: str
    tweet_url: str
    author_name: str
    author_handle: str
    conversation_id: str
    reply_to_id: str
    reply_to_handle: str
    source_partition: str = "social"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def engagement_score(self) -> int:
        return self.likes + self.share_count + self.reply_count + self.quote_count


@dataclass
class RunArtifacts:
    run_id: str
    run_dir: str
    queries_path: str
    raw_tweets_path: str
    normalized_tweets_path: str
    results_md_path: str


@dataclass
class RunResult:
    run_id: str
    run_dir: str
    selected_brand: str
    clix_bin: str
    auth_mode: str
    query_runs: list[QueryRun]
    raw_tweets: list[RawTweetRecord]
    tweets: list[NormalizedTweetRecord]
    warnings: list[str] = field(default_factory=list)
