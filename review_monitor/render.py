from __future__ import annotations

from collections import Counter
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import ReviewRecord, RunResult, SourceSummary


def build_console() -> Console:
    return Console(highlight=False)


def render_header(console: Console, run_id: str, run_dir: str, selected_brand: str, selected_site: str, selected_scope: str) -> None:
    body = Text()
    body.append("Review monitor run\n", style="bold")
    body.append(f"brand: {selected_brand}\n")
    body.append(f"site: {selected_site}\n")
    body.append(f"scope: {selected_scope}\n")
    body.append(f"run_id: {run_id}\n")
    body.append(f"output: {Path(run_dir)}")
    console.print(Panel(body, title="Execution", border_style="cyan"))


def render_sources(console: Console, sources: list[SourceSummary]) -> None:
    table = Table(title="Source Summary", box=box.SIMPLE_HEAVY)
    table.add_column("Source")
    table.add_column("Site")
    table.add_column("Brand")
    table.add_column("Scope")
    table.add_column("Fetch")
    table.add_column("Agg.", justify="right")
    table.add_column("Count", justify="right")
    table.add_column("Rows", justify="right")
    table.add_column("Status")
    for source in sources:
        agg = "-" if source.aggregate_rating is None else f"{source.aggregate_rating:.2f}"
        count = "-" if source.aggregate_count is None else str(source.aggregate_count)
        status = "ok" if not source.error else f"error: {source.error}"
        table.add_row(
            source.source_name,
            source.site,
            source.brand_focus,
            source.review_scope,
            source.fetch_mode or "-",
            agg,
            count,
            str(source.extracted_reviews),
            status,
        )
    console.print(table)


def render_reviews(console: Console, reviews: list[ReviewRecord], limit: int = 10) -> None:
    if not reviews:
        return
    ranked = sorted(reviews, key=lambda review: (review.rating or 0, len(review.body)), reverse=True)[:limit]
    table = Table(title="Sample Reviews", box=box.SIMPLE)
    table.add_column("Site")
    table.add_column("Brand")
    table.add_column("Scope")
    table.add_column("Rating", justify="right")
    table.add_column("Author")
    table.add_column("Excerpt")
    for review in ranked:
        rating = "-" if review.rating is None else f"{review.rating:.1f}"
        table.add_row(review.site, review.brand_focus, review.review_scope, rating, review.author or "-", review.body[:140])
    console.print(table)


def render_summary(console: Console, result: RunResult) -> None:
    site_counts = Counter(review.site for review in result.reviews)
    brand_counts = Counter(review.brand_focus for review in result.reviews)
    scope_counts = Counter(review.review_scope for review in result.reviews)
    body = Text()
    body.append(f"reviews: {len(result.reviews)}\n")
    body.append("sites: " + (", ".join(f"{site}={count}" for site, count in sorted(site_counts.items())) or "none") + "\n")
    body.append("brands: " + (", ".join(f"{brand}={count}" for brand, count in sorted(brand_counts.items())) or "none") + "\n")
    body.append("scopes: " + (", ".join(f"{scope}={count}" for scope, count in sorted(scope_counts.items())) or "none"))
    console.print(Panel(body, title="Summary", border_style="green"))


def render_warnings(console: Console, warnings: list[str]) -> None:
    if not warnings:
        return
    body = Text()
    for warning in warnings:
        body.append(f"- {warning}\n")
    console.print(Panel(body, title="Warnings", border_style="yellow"))
