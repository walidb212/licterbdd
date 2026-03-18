from __future__ import annotations

from collections import Counter
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import ContextDocumentRecord, RunResult


def build_console() -> Console:
    return Console(highlight=False)


def render_header(console: Console, run_id: str, run_dir: str, selected_brand: str, selected_document_types: str) -> None:
    body = Text()
    body.append("Context monitor run\n", style="bold")
    body.append(f"brand: {selected_brand}\n")
    body.append(f"document types: {selected_document_types}\n")
    body.append(f"run_id: {run_id}\n")
    body.append(f"output: {Path(run_dir)}")
    console.print(Panel(body, title="Execution", border_style="cyan"))


def render_documents(console: Console, documents: list[ContextDocumentRecord]) -> None:
    table = Table(title="Context Documents", box=box.SIMPLE_HEAVY)
    table.add_column("Brand")
    table.add_column("Type")
    table.add_column("Title")
    table.add_column("Fetch")
    table.add_column("Size", justify="right")
    for row in documents[:15]:
        table.add_row(row.brand_focus, row.document_type, row.title[:80], row.fetch_mode, str(len(row.content_text)))
    console.print(table)


def render_summary(console: Console, result: RunResult) -> None:
    brand_counts = Counter(row.brand_focus for row in result.documents)
    type_counts = Counter(row.document_type for row in result.documents)
    body = Text()
    body.append(f"documents: {len(result.documents)}\n")
    body.append("brands: " + (", ".join(f"{name}={count}" for name, count in sorted(brand_counts.items())) or "none") + "\n")
    body.append("types: " + (", ".join(f"{name}={count}" for name, count in sorted(type_counts.items())) or "none"))
    console.print(Panel(body, title="Summary", border_style="green"))


def render_warnings(console: Console, warnings: list[str]) -> None:
    if not warnings:
        return
    body = Text()
    for warning in warnings:
        body.append(f"- {warning}\n")
    console.print(Panel(body, title="Warnings", border_style="yellow"))
