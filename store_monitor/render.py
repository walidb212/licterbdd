from __future__ import annotations

from collections import Counter
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import RunResult, StoreRecord, StoreReviewRecord


def build_console() -> Console:
    return Console(highlight=False)


def render_header(console: Console, run_id: str, run_dir: str, selected_brand: str, selected_stage: str) -> None:
    body = Text()
    body.append("Store monitor run\n", style="bold")
    body.append(f"brand: {selected_brand}\n")
    body.append(f"stage: {selected_stage}\n")
    body.append(f"run_id: {run_id}\n")
    body.append(f"output: {Path(run_dir)}")
    console.print(Panel(body, title="Execution", border_style="cyan"))


def render_stores(console: Console, stores: list[StoreRecord], limit: int = 12) -> None:
    table = Table(title="Stores", box=box.SIMPLE_HEAVY)
    table.add_column("Brand")
    table.add_column("Store")
    table.add_column("Postal")
    table.add_column("City")
    table.add_column("Discovery")
    table.add_column("Status")
    for store in stores[:limit]:
        table.add_row(
            store.brand_focus,
            store.store_name[:48],
            store.postal_code or "-",
            store.city or "-",
            store.discovery_source,
            store.status,
        )
    console.print(table)


def render_reviews(console: Console, reviews: list[StoreReviewRecord], limit: int = 10) -> None:
    if not reviews:
        return
    ranked = sorted(reviews, key=lambda review: (review.rating or 0, len(review.body)), reverse=True)[:limit]
    table = Table(title="Sample Store Reviews", box=box.SIMPLE)
    table.add_column("Brand")
    table.add_column("Store")
    table.add_column("Rating", justify="right")
    table.add_column("Author")
    table.add_column("Excerpt")
    for review in ranked:
        rating = "-" if review.rating is None else f"{review.rating:.1f}"
        table.add_row(review.brand_focus, review.entity_name[:36], rating, review.author or "-", review.body[:140])
    console.print(table)


def render_summary(console: Console, result: RunResult) -> None:
    by_brand = Counter(store.brand_focus for store in result.stores)
    by_status = Counter(store.status for store in result.stores)
    review_brands = Counter(review.brand_focus for review in result.reviews)
    body = Text()
    body.append(f"stores: {len(result.stores)}\n")
    body.append("store brands: " + (", ".join(f"{brand}={count}" for brand, count in sorted(by_brand.items())) or "none") + "\n")
    body.append("store statuses: " + (", ".join(f"{status}={count}" for status, count in sorted(by_status.items())) or "none") + "\n")
    body.append("reviews: " + str(len(result.reviews)) + "\n")
    body.append("review brands: " + (", ".join(f"{brand}={count}" for brand, count in sorted(review_brands.items())) or "none"))
    console.print(Panel(body, title="Summary", border_style="green"))


def render_warnings(console: Console, warnings: list[str]) -> None:
    if not warnings:
        return
    body = Text()
    for warning in warnings:
        body.append(f"- {warning}\n")
    console.print(Panel(body, title="Warnings", border_style="yellow"))
