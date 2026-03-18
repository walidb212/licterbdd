from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ContextSource:
    name: str
    brand_focus: str
    document_type: str
    url: str


@dataclass
class ContextDocumentRecord:
    run_id: str
    brand_focus: str
    source_partition: str
    document_type: str
    source_name: str
    source_url: str
    title: str
    fetch_mode: str
    content_hash: str
    content_text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RunArtifacts:
    run_id: str
    run_dir: str
    documents_path: str
    results_md_path: str


@dataclass
class RunResult:
    run_id: str
    run_dir: str
    selected_brand: str
    selected_document_types: str
    documents: list[ContextDocumentRecord]
    warnings: list[str] = field(default_factory=list)
