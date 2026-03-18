from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .models import ContextDocumentRecord, RunArtifacts


def build_run_artifacts(base_output_dir: str) -> RunArtifacts:
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}_{uuid4().hex[:6]}"
    run_dir = Path(base_output_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return RunArtifacts(
        run_id=run_id,
        run_dir=str(run_dir),
        documents_path=str(run_dir / "documents.jsonl"),
        results_md_path=str(run_dir / "results.md"),
    )


def export_run(artifacts: RunArtifacts, documents: list[ContextDocumentRecord]) -> None:
    with open(artifacts.documents_path, "w", encoding="utf-8", newline="\n") as handle:
        for row in documents:
            handle.write(json.dumps(row.to_dict(), ensure_ascii=False) + "\n")


def export_markdown(artifacts: RunArtifacts, markdown: str) -> None:
    Path(artifacts.results_md_path).write_text(markdown, encoding="utf-8")
