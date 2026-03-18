from __future__ import annotations

from collections import Counter
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import NormalizedTweetRecord, QueryRun, RunResult


def build_console() -> Console:
    return Console(highlight=False)


def render_header(console: Console, result: RunResult) -> None:
    body = Text()
    body.append("X monitor run\n", style="bold")
    body.append(f"brand: {result.selected_brand}\n")
    body.append(f"run_id: {result.run_id}\n")
    body.append(f"auth: {result.auth_mode}\n")
    body.append(f"clix: {result.clix_bin}\n")
    body.append(f"output: {Path(result.run_dir)}")
    console.print(Panel(body, title="Execution", border_style="cyan"))


def render_queries(console: Console, query_runs: list[QueryRun]) -> None:
    table = Table(title="Query Summary", box=box.SIMPLE_HEAVY)
    table.add_column("Query")
    table.add_column("Brand")
    table.add_column("Type")
    table.add_column("Raw", justify="right")
    table.add_column("Valid", justify="right")
    table.add_column("Added", justify="right")
    table.add_column("Status")
    for query_run in query_runs:
        status = "ok"
        if query_run.error:
            status = f"error: {query_run.error}"
        elif query_run.warning:
            status = f"warning: {query_run.warning}"
        table.add_row(
            query_run.query_name,
            query_run.brand_focus,
            query_run.search_type,
            str(query_run.raw_count),
            str(query_run.retained_count),
            str(query_run.added_count),
            status,
        )
    console.print(table)


def render_distribution(console: Console, tweets: list[NormalizedTweetRecord]) -> None:
    if not tweets:
        return
    brand_counts = Counter(tweet.brand for tweet in tweets)
    language_counts = Counter(tweet.language or "unknown" for tweet in tweets)
    table = Table(title="Brand and Language Mix", box=box.SIMPLE)
    table.add_column("Dimension")
    table.add_column("Value")
    table.add_column("Tweets", justify="right")
    for brand, count in sorted(brand_counts.items()):
        table.add_row("brand", brand, str(count))
    for language, count in sorted(language_counts.items(), key=lambda item: (-item[1], item[0])):
        table.add_row("language", language, str(count))
    console.print(table)


def render_top_tweets(console: Console, tweets: list[NormalizedTweetRecord], limit: int = 8) -> None:
    if not tweets:
        return
    ranked = sorted(
        tweets,
        key=lambda tweet: (tweet.engagement_score, tweet.view_count, tweet.likes),
        reverse=True,
    )[:limit]
    table = Table(title="Top Tweets", box=box.SIMPLE)
    table.add_column("Brand")
    table.add_column("Lang")
    table.add_column("Type")
    table.add_column("Eng.", justify="right")
    table.add_column("Views", justify="right")
    table.add_column("Author")
    table.add_column("Excerpt")
    for tweet in ranked:
        table.add_row(
            tweet.brand,
            tweet.language or "-",
            tweet.post_type,
            str(tweet.engagement_score),
            str(tweet.view_count),
            tweet.author_handle or "-",
            tweet.text[:110],
        )
    console.print(table)


def render_reply_samples(console: Console, tweets: list[NormalizedTweetRecord], limit: int = 6) -> None:
    replies = [tweet for tweet in tweets if tweet.post_type == "reply"][:limit]
    if not replies:
        return
    table = Table(title="Reply Samples", box=box.SIMPLE)
    table.add_column("Brand")
    table.add_column("Author")
    table.add_column("Reply To")
    table.add_column("Excerpt")
    for tweet in replies:
        table.add_row(
            tweet.brand,
            tweet.author_handle or "-",
            tweet.reply_to_handle or "-",
            tweet.text[:120],
        )
    console.print(table)


def render_benchmark_samples(console: Console, tweets: list[NormalizedTweetRecord], limit: int = 6) -> None:
    benchmark_rows = [tweet for tweet in tweets if any(name.startswith("benchmark_") for name in tweet.query_names)][:limit]
    if not benchmark_rows:
        return
    table = Table(title="Benchmark Samples", box=box.SIMPLE)
    table.add_column("Author")
    table.add_column("Type")
    table.add_column("Excerpt")
    for tweet in benchmark_rows:
        table.add_row(tweet.author_handle or "-", tweet.post_type, tweet.text[:130])
    console.print(table)


def render_summary(console: Console, result: RunResult) -> None:
    reply_count = sum(1 for tweet in result.tweets if tweet.post_type == "reply")
    body = Text()
    body.append(f"queries: {len(result.query_runs)}\n")
    body.append(f"raw tweets: {len(result.raw_tweets)}\n")
    body.append(f"normalized tweets: {len(result.tweets)}\n")
    body.append(f"replies: {reply_count}")
    console.print(Panel(body, title="Summary", border_style="green"))


def render_warnings(console: Console, warnings: list[str]) -> None:
    if not warnings:
        return
    body = Text()
    for warning in warnings:
        body.append(f"- {warning}\n")
    console.print(Panel(body, title="Warnings", border_style="yellow"))
