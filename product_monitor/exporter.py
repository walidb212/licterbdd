from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .models import ProductRecord, ProductReviewRecord, RunArtifacts


def build_run_artifacts(base_output_dir: str) -> RunArtifacts:
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}_{uuid4().hex[:6]}"
    run_dir = Path(base_output_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return RunArtifacts(
        run_id=run_id,
        run_dir=str(run_dir),
        products_path=str(run_dir / "products.jsonl"),
        reviews_path=str(run_dir / "reviews.jsonl"),
        results_md_path=str(run_dir / "results.md"),
    )


def _write_jsonl(path: str, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def export_run(artifacts: RunArtifacts, products: list[ProductRecord], reviews: list[ProductReviewRecord]) -> None:
    _write_jsonl(artifacts.products_path, [row.to_dict() for row in products])
    _write_jsonl(artifacts.reviews_path, [row.to_dict() for row in reviews])


def export_markdown(artifacts: RunArtifacts, markdown: str) -> None:
    Path(artifacts.results_md_path).write_text(markdown, encoding="utf-8")
