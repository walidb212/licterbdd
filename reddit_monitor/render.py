from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import CommentRecord, MonitorResult, PostRecord, SeedReport


def build_console() -> Console:
    return Console(highlight=False)


def render_run_header(console: Console, selected_brand: str, run_id: str, run_dir: str, headless: bool) -> None:
    body = Text()
    body.append("Reddit monitor run\n", style="bold")
    body.append(f"brand: {selected_brand}\n")
    body.append(f"run_id: {run_id}\n")
    body.append(f"headless: {headless}\n")
    body.append(f"output: {Path(run_dir)}")
    console.print(Panel(body, title="Execution", border_style="cyan"))


def render_seed_table(console: Console, reports: list[SeedReport]) -> None:
    table = Table(title="Seed Discovery", box=box.SIMPLE_HEAVY)
    table.add_column("Seed")
    table.add_column("Brand")
    table.add_column("Type")
    table.add_column("Found", justify="right")
    table.add_column("Unique", justify="right")
    table.add_column("Dup", justify="right")
    table.add_column("Filtered", justify="right")
    table.add_column("Blank", justify="right")
    table.add_column("Status")
    for report in reports:
        status = "ok" if not report.error else f"error: {report.error}"
        table.add_row(
            report.seed_name,
            report.brand_focus,
            report.seed_type,
            str(report.discovered_count),
            str(report.unique_count),
            str(report.duplicate_count),
            str(report.filtered_count),
            str(report.blank_anchor_count),
            status,
        )
    console.print(table)


def render_brand_table(console: Console, posts: list[PostRecord]) -> None:
    if not posts:
        return
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for post in posts:
        counts[(post.brand_focus, post.subreddit)] += 1
    table = Table(title="Posts by Brand and Subreddit", box=box.SIMPLE)
    table.add_column("Brand")
    table.add_column("Subreddit")
    table.add_column("Posts", justify="right")
    for (brand_focus, subreddit), count in sorted(counts.items(), key=lambda item: (-item[1], item[0][0], item[0][1])):
        table.add_row(brand_focus, subreddit or "-", str(count))
    console.print(table)


def render_top_posts(console: Console, posts: list[PostRecord], limit: int = 8) -> None:
    if not posts:
        return
    ranked = sorted(
        posts,
        key=lambda post: (
            post.comment_count or 0,
            post.score or 0,
            post.relevance_score,
        ),
        reverse=True,
    )[:limit]
    table = Table(title="Top Posts", box=box.SIMPLE)
    table.add_column("Brand")
    table.add_column("Subreddit")
    table.add_column("Comments", justify="right")
    table.add_column("Score", justify="right")
    table.add_column("Rel.", justify="right")
    table.add_column("Title")
    for post in ranked:
        table.add_row(
            post.brand_focus,
            post.subreddit or "-",
            str(post.comment_count or 0),
            str(post.score or 0),
            f"{post.relevance_score:.3f}",
            post.post_title[:110],
        )
    console.print(table)


def render_comment_samples(console: Console, comments: list[CommentRecord], limit: int = 5) -> None:
    if not comments:
        return
    table = Table(title="Comment Samples", box=box.SIMPLE)
    table.add_column("Brand")
    table.add_column("Subreddit")
    table.add_column("Author")
    table.add_column("Excerpt")
    for comment in comments[:limit]:
        table.add_row(
            comment.brand_focus,
            comment.subreddit or "-",
            comment.comment_author or "-",
            comment.comment_text[:140],
        )
    console.print(table)


def render_summary(console: Console, result: MonitorResult) -> None:
    brand_counter = Counter(post.brand_focus for post in result.posts)
    body = Text()
    body.append(f"posts: {len(result.posts)}\n")
    body.append(f"comments: {len(result.comments)}\n")
    body.append("brand mix: ")
    body.append(", ".join(f"{brand}={count}" for brand, count in sorted(brand_counter.items())) or "none")
    console.print(Panel(body, title="Summary", border_style="green"))


def render_warnings(console: Console, warnings: list[str]) -> None:
    if not warnings:
        return
    body = Text()
    for warning in warnings:
        body.append(f"- {warning}\n")
    console.print(Panel(body, title="Warnings", border_style="yellow"))
