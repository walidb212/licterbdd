from __future__ import annotations

import os
from pathlib import Path


DEFAULT_OUTPUT_DIR = str(Path("data") / "ai_runs")
DEFAULT_OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5-mini")
DEFAULT_OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")

SOURCE_DIRS = {
    "review": Path("data/review_runs"),
    "store": Path("data/store_runs"),
    "product": Path("data/product_runs"),
    "news": Path("data/news_runs"),
    "reddit": Path("data/reddit_runs"),
    "youtube": Path("data/youtube_runs"),
    "tiktok": Path("data/tiktok_runs"),
    "x": Path("data/x_runs"),
    "global": Path("data/global_runs"),
}

PRIMARY_FILES = {
    "review": "reviews.jsonl",
    "store": "reviews.jsonl",
    "product": "reviews.jsonl",
    "news": "articles.jsonl",
    "reddit": "posts.jsonl",
    "youtube": "videos.jsonl",
    "tiktok": "videos.jsonl",
    "x": "tweets_normalized.jsonl",
    "global": "global_summary.md",
}
