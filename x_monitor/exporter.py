from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .models import NormalizedTweetRecord, QueryRun, RawTweetRecord, RunArtifacts


def build_run_artifacts(base_output_dir: str) -> RunArtifacts:
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}_{uuid4().hex[:6]}"
    run_dir = Path(base_output_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return RunArtifacts(
        run_id=run_id,
        run_dir=str(run_dir),
        queries_path=str(run_dir / "queries.jsonl"),
        raw_tweets_path=str(run_dir / "tweets_raw.jsonl"),
        normalized_tweets_path=str(run_dir / "tweets_normalized.jsonl"),
        results_md_path=str(run_dir / "results.md"),
    )


def _write_jsonl(path: str, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def export_run(
    artifacts: RunArtifacts,
    query_runs: list[QueryRun],
    raw_tweets: list[RawTweetRecord],
    tweets: list[NormalizedTweetRecord],
) -> None:
    _write_jsonl(artifacts.queries_path, [row.to_dict() for row in query_runs])
    _write_jsonl(artifacts.raw_tweets_path, [row.to_dict() for row in raw_tweets])
    _write_jsonl(artifacts.normalized_tweets_path, [row.to_dict() for row in tweets])


def export_markdown(artifacts: RunArtifacts, markdown: str) -> None:
    Path(artifacts.results_md_path).write_text(markdown, encoding="utf-8")
