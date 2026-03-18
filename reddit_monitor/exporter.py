from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .models import CommentRecord, PostRecord, RunArtifacts


def build_run_artifacts(base_output_dir: str) -> RunArtifacts:
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}_{uuid4().hex[:6]}"
    run_dir = Path(base_output_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return RunArtifacts(
        run_id=run_id,
        run_dir=str(run_dir),
        posts_path=str(run_dir / "posts.jsonl"),
        comments_path=str(run_dir / "comments.jsonl"),
    )


def _write_jsonl(path: str, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def export_jsonl(artifacts: RunArtifacts, posts: list[PostRecord], comments: list[CommentRecord]) -> None:
    _write_jsonl(artifacts.posts_path, [post.to_dict() for post in posts])
    _write_jsonl(artifacts.comments_path, [comment.to_dict() for comment in comments])
