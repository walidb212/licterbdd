from __future__ import annotations

import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from monitor_core import StateStore, build_content_hash, repair_mojibake
from monitor_core.cloudflare import (
    fetch_cloudflare_content,
    fetch_cloudflare_markdown,
    fetch_direct_bytes,
    html_to_text,
    resolve_cloudflare_credentials,
)

from .exporter import build_run_artifacts, export_markdown, export_run
from .models import ContextDocumentRecord, RunResult
from .sources import select_sources


MONITOR_NAME = "context_monitor"


def _looks_like_low_signal_document(text: str) -> bool:
    lowered = (text or "").casefold()
    patterns = (
        "just a moment",
        "enable javascript and cookies to continue",
        "activation de javascript",
        "captcha",
        "datadome",
        "non trouvé | intersport",
        "désolé ce site requiert l'activation de javascript",
    )
    return any(pattern in lowered for pattern in patterns)


def _extract_pdf_text(url: str) -> str:
    pdf_bytes = fetch_direct_bytes(url)
    with tempfile.TemporaryDirectory() as tmp_dir:
        pdf_path = Path(tmp_dir) / "document.pdf"
        txt_path = Path(tmp_dir) / "document.txt"
        pdf_path.write_bytes(pdf_bytes)
        completed = subprocess.run(["pdftotext", str(pdf_path), str(txt_path)], capture_output=True, text=True, timeout=120)
        if completed.returncode != 0 or not txt_path.exists():
            raise RuntimeError(completed.stderr.strip() or "pdftotext failed")
        return txt_path.read_text(encoding="utf-8", errors="replace")


def _fetch_document(url: str) -> tuple[str, str]:
    if url.lower().endswith(".pdf"):
        return _extract_pdf_text(url), "pdf"
    token, account_id = resolve_cloudflare_credentials()
    if not token or not account_id:
        raise RuntimeError("Cloudflare credentials missing for context monitor.")
    markdown, _ = fetch_cloudflare_markdown(url, token=token, account_id=account_id)
    normalized_markdown = " ".join(repair_mojibake(markdown or "").split())
    if len(normalized_markdown) >= 80 and not _looks_like_low_signal_document(normalized_markdown):
        return markdown, "cloudflare_markdown"
    html = fetch_cloudflare_content(url, token=token, account_id=account_id)
    html_text = html_to_text(html)
    normalized_html_text = " ".join(repair_mojibake(html_text or "").split())
    if len(normalized_html_text) >= 80 and not _looks_like_low_signal_document(normalized_html_text):
        return html_text, "cloudflare_content_text"
    return markdown or html_text, "cloudflare_markdown"


def _build_markdown(result: RunResult) -> str:
    brand_counts = Counter(row.brand_focus for row in result.documents)
    type_counts = Counter(row.document_type for row in result.documents)
    lines = [
        f"# Context monitor - Run {result.run_id}",
        "",
        "## Scope",
        "",
        f"- brand: `{result.selected_brand}`",
        f"- document types: `{result.selected_document_types}`",
        f"- documents exported: `{len(result.documents)}`",
        f"- brands: {', '.join(f'`{name}`={count}' for name, count in sorted(brand_counts.items())) or '`none`'}",
        f"- types: {', '.join(f'`{name}`={count}' for name, count in sorted(type_counts.items())) or '`none`'}",
        "",
        "## Documents",
        "",
        "| Brand | Type | Title | Fetch | Size |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for row in result.documents:
        lines.append(f"| {row.brand_focus} | {row.document_type} | {row.title.replace('|', ' ')[:160]} | {row.fetch_mode} | {len(row.content_text)} |")
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in result.warnings:
            lines.append(f"- {warning}")
    return "\n".join(lines) + "\n"


def run_monitor(
    *,
    brand: str,
    document_types: str,
    output_dir: str,
    incremental: bool,
    state_db: str,
    debug: bool,
) -> RunResult:
    artifacts = build_run_artifacts(output_dir)
    warnings: list[str] = []
    documents: list[ContextDocumentRecord] = []
    state_store = StateStore(state_db) if incremental else None
    if state_store is not None:
        state_store.log_run_start(
            artifacts.run_id,
            MONITOR_NAME,
            artifacts.run_dir,
            config={"brand": brand, "document_types": document_types, "incremental": incremental},
        )
    try:
        for source in select_sources(brand, document_types):
            try:
                text, fetch_mode = _fetch_document(source.url)
                normalized = " ".join(repair_mojibake(text or "").split())
                if len(normalized) < 40 or _looks_like_low_signal_document(normalized):
                    warnings.append(f"{source.name}: empty or low-signal document skipped.")
                    continue
                title = normalized.splitlines()[0][:180] if normalized else source.name
                content_hash = build_content_hash(source.url, normalized)
                entity_key = source.url
                if state_store is not None:
                    state_store.upsert_entity(
                        monitor_name=MONITOR_NAME,
                        source_name=source.name,
                        entity_key=entity_key,
                        entity_name=source.name,
                        entity_url=source.url,
                        content_hash=content_hash,
                        metadata={"document_type": source.document_type},
                        mark_scraped=True,
                    )
                    is_new = state_store.record_item(
                        monitor_name=MONITOR_NAME,
                        source_name=source.name,
                        source_partition="context",
                        entity_key=entity_key,
                        item_key=source.url,
                        content_hash=content_hash,
                        published_at=None,
                        metadata={"document_type": source.document_type},
                    )
                    if not is_new:
                        warnings.append(f"{source.name}: unchanged document skipped by incremental state.")
                        continue
                documents.append(
                    ContextDocumentRecord(
                        run_id=artifacts.run_id,
                        brand_focus=source.brand_focus,
                        source_partition="context",
                        document_type=source.document_type,
                        source_name=source.name,
                        source_url=source.url,
                        title=title,
                        fetch_mode=fetch_mode,
                        content_hash=content_hash,
                        content_text=text[:30000],
                    )
                )
            except Exception as exc:
                warnings.append(f"{source.name} failed: {exc}")
        export_run(artifacts, documents)
        export_markdown(artifacts, _build_markdown(RunResult(artifacts.run_id, artifacts.run_dir, brand, document_types, documents, warnings)))
        if state_store is not None:
            state_store.log_run_end(artifacts.run_id, status="ok", stats={"documents": len(documents)})
    except Exception as exc:
        if state_store is not None:
            state_store.log_run_end(artifacts.run_id, status="error", error=str(exc))
        raise
    finally:
        if state_store is not None:
            state_store.close()
    return RunResult(
        run_id=artifacts.run_id,
        run_dir=artifacts.run_dir,
        selected_brand=brand,
        selected_document_types=document_types,
        documents=documents,
        warnings=warnings,
    )


def run_monitor_sync(**kwargs) -> RunResult:
    return run_monitor(**kwargs)
