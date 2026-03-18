"""Lecture des fichiers JSONL avec cache mémoire (TTL 5 min)."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

_cache: dict[str, tuple[float, Any]] = {}
_TTL = 300  # 5 minutes


def _cached(key: str, loader_fn):
    now = time.monotonic()
    if key in _cache and (now - _cache[key][0]) < _TTL:
        return _cache[key][1]
    result = loader_fn()
    _cache[key] = (now, result)
    return result


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def latest_run_dir(source: str) -> Path | None:
    base = DATA / f"{source}_runs"
    if not base.exists():
        return None
    dirs = sorted(
        [d for d in base.iterdir() if d.is_dir()],
        key=lambda d: d.name,
        reverse=True,
    )
    return dirs[0] if dirs else None


def load_ai_latest() -> dict[str, list[dict]]:
    def _load():
        run_dir = latest_run_dir("ai")
        if not run_dir:
            return {"social": [], "review": [], "news": [], "entity_summary": []}
        return {
            "social": load_jsonl(run_dir / "social_enriched.jsonl"),
            "review": load_jsonl(run_dir / "review_enriched.jsonl"),
            "news": load_jsonl(run_dir / "news_enriched.jsonl"),
            "entity_summary": load_jsonl(run_dir / "entity_summary.jsonl"),
        }
    return _cached("ai_latest", _load)


def load_store_latest() -> list[dict]:
    def _load():
        run_dir = latest_run_dir("store")
        if not run_dir:
            return []
        return load_jsonl(run_dir / "reviews.jsonl")
    return _cached("store_latest", _load)


def load_excel_benchmark() -> list[dict]:
    def _load():
        return load_jsonl(DATA / "excel_runs" / "benchmark_marche.jsonl")
    return _cached("excel_benchmark", _load)


def load_excel_reputation() -> list[dict]:
    def _load():
        return load_jsonl(DATA / "excel_runs" / "reputation_crise.jsonl")
    return _cached("excel_reputation", _load)


def load_excel_cx() -> list[dict]:
    def _load():
        return load_jsonl(DATA / "excel_runs" / "voix_client_cx.jsonl")
    return _cached("excel_cx", _load)


def load_youtube_url_index() -> dict[str, str]:
    """Returns {video_id_lower: video_url} from the latest youtube_run."""
    def _load():
        run_dir = latest_run_dir("youtube")
        if not run_dir:
            return {}
        videos = load_jsonl(run_dir / "videos.jsonl")
        return {
            r["video_id"].lower(): r["video_url"]
            for r in videos
            if r.get("video_id") and r.get("video_url")
        }
    return _cached("youtube_url_index", _load)


def load_news_url_index() -> dict[str, str]:
    """Returns {article_id_lower: google_news_url} from the latest news_run."""
    def _load():
        run_dir = latest_run_dir("news")
        if not run_dir:
            return {}
        articles = load_jsonl(run_dir / "articles.jsonl")
        return {
            r["article_id"].lower(): r.get("google_news_url") or r.get("article_snapshot_url", "")
            for r in articles
            if r.get("article_id")
        }
    return _cached("news_url_index", _load)


def invalidate_cache() -> None:
    _cache.clear()
