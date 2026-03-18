from __future__ import annotations

from collections import Counter
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import ProductRecord, ProductReviewRecord, RunResult


def build_console() -> Console:
    return Console(highlight=False)


def render_header(console: Console, run_id: str, run_dir: str, selected_brand: str, max_products_per_brand: int) -> None:
    body = Text()
    body.append("Product monitor run\n", style="bold")
    body.append(f"brand: {selected_brand}\n")
    body.append(f"max products/brand: {max_products_per_brand}\n")
    body.append(f"run_id: {run_id}\n")
    body.append(f"output: {Path(run_dir)}")
    console.print(Panel(body, title="Execution", border_style="cyan"))


def render_products(console: Console, products: list[ProductRecord]) -> None:
    table = Table(title="Products", box=box.SIMPLE_HEAVY)
    table.add_column("Brand")
    table.add_column("Category")
    table.add_column("Product")
    table.add_column("Agg.", justify="right")
    table.add_column("Count", justify="right")
    table.add_column("Status")
    for row in products[:20]:
        agg = "-" if row.aggregate_rating is None else f"{row.aggregate_rating:.2f}"
        count = "-" if row.aggregate_count is None else str(row.aggregate_count)
        table.add_row(row.brand_focus, row.category, row.entity_name[:70], agg, count, row.status)
    console.print(table)


def render_reviews(console: Console, reviews: list[ProductReviewRecord], limit: int = 10) -> None:
    if not reviews:
        return
    table = Table(title="Sample Product Reviews", box=box.SIMPLE)
    table.add_column("Brand")
    table.add_column("Category")
    table.add_column("Product")
    table.add_column("Rating", justify="right")
    table.add_column("Excerpt")
    for row in reviews[:limit]:
        rating = "-" if row.rating is None else f"{row.rating:.1f}"
        table.add_row(row.brand_focus, row.category, row.entity_name[:40], rating, row.body[:140])
    console.print(table)


def render_summary(console: Console, result: RunResult) -> None:
    brands = Counter(row.brand_focus for row in result.products)
    categories = Counter(row.category for row in result.products)
    body = Text()
    body.append(f"products: {len(result.products)}\n")
    body.append(f"reviews: {len(result.reviews)}\n")
    body.append("brands: " + (", ".join(f"{name}={count}" for name, count in sorted(brands.items())) or "none") + "\n")
    body.append("categories: " + (", ".join(f"{name}={count}" for name, count in sorted(categories.items())) or "none"))
    console.print(Panel(body, title="Summary", border_style="green"))


def render_warnings(console: Console, warnings: list[str]) -> None:
    if not warnings:
        return
    body = Text()
    for warning in warnings:
        body.append(f"- {warning}\n")
    console.print(Panel(body, title="Warnings", border_style="yellow"))
