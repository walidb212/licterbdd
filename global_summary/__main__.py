from __future__ import annotations

import argparse
import json
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


SOURCE_DIRS = {
    "reddit": Path("data/reddit_runs"),
    "news": Path("data/news_runs"),
    "review": Path("data/review_runs"),
    "store": Path("data/store_runs"),
    "youtube": Path("data/youtube_runs"),
    "tiktok": Path("data/tiktok_runs"),
    "x": Path("data/x_runs"),
}

PRIMARY_FILES = {
    "reddit": "posts.jsonl",
    "news": "articles.jsonl",
    "review": "reviews.jsonl",
    "store": "reviews.jsonl",
    "youtube": "videos.jsonl",
    "tiktok": "videos.jsonl",
    "x": "tweets_normalized.jsonl",
}


def _latest_run_dir(base_dir: Path, *, primary_file: str | None = None) -> Path | None:
    if not base_dir.exists():
        return None
    candidates = [row for row in base_dir.iterdir() if row.is_dir()]
    if not candidates:
        return None
    if primary_file:
        non_empty = []
        for candidate in candidates:
            primary_path = candidate / primary_file
            if primary_path.exists() and primary_path.stat().st_size > 0:
                non_empty.append(candidate)
        if non_empty:
            return max(non_empty, key=lambda row: row.stat().st_mtime)
    return max(candidates, key=lambda row: row.stat().st_mtime)


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _counter_line(counter: Counter) -> str:
    return ", ".join(f"`{name}`={count}" for name, count in sorted(counter.items())) or "`none`"


def build_global_summary(
    *,
    output_dir: str = "data/global_runs",
    reddit_run: str | None = None,
    news_run: str | None = None,
    review_run: str | None = None,
    store_run: str | None = None,
    youtube_run: str | None = None,
    tiktok_run: str | None = None,
    x_run: str | None = None,
) -> Path:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid.uuid4().hex[:6]
    run_dir = Path(output_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    selected_runs = {
        "reddit": Path(reddit_run) if reddit_run else _latest_run_dir(SOURCE_DIRS["reddit"], primary_file=PRIMARY_FILES["reddit"]),
        "news": Path(news_run) if news_run else _latest_run_dir(SOURCE_DIRS["news"], primary_file=PRIMARY_FILES["news"]),
        "review": Path(review_run) if review_run else _latest_run_dir(SOURCE_DIRS["review"], primary_file=PRIMARY_FILES["review"]),
        "store": Path(store_run) if store_run else _latest_run_dir(SOURCE_DIRS["store"], primary_file=PRIMARY_FILES["store"]),
        "youtube": Path(youtube_run) if youtube_run else _latest_run_dir(SOURCE_DIRS["youtube"], primary_file=PRIMARY_FILES["youtube"]),
        "tiktok": Path(tiktok_run) if tiktok_run else _latest_run_dir(SOURCE_DIRS["tiktok"], primary_file=PRIMARY_FILES["tiktok"]),
        "x": Path(x_run) if x_run else _latest_run_dir(SOURCE_DIRS["x"], primary_file=PRIMARY_FILES["x"]),
    }

    reddit_posts = _read_jsonl((selected_runs["reddit"] or Path()) / "posts.jsonl") if selected_runs["reddit"] else []
    reddit_comments = _read_jsonl((selected_runs["reddit"] or Path()) / "comments.jsonl") if selected_runs["reddit"] else []
    news_articles = _read_jsonl((selected_runs["news"] or Path()) / "articles.jsonl") if selected_runs["news"] else []
    review_rows = _read_jsonl((selected_runs["review"] or Path()) / "reviews.jsonl") if selected_runs["review"] else []
    review_sources = _read_jsonl((selected_runs["review"] or Path()) / "sources.jsonl") if selected_runs["review"] else []
    store_rows = _read_jsonl((selected_runs["store"] or Path()) / "stores.jsonl") if selected_runs["store"] else []
    store_reviews = _read_jsonl((selected_runs["store"] or Path()) / "reviews.jsonl") if selected_runs["store"] else []
    youtube_videos = _read_jsonl((selected_runs["youtube"] or Path()) / "videos.jsonl") if selected_runs["youtube"] else []
    youtube_comments = _read_jsonl((selected_runs["youtube"] or Path()) / "comments.jsonl") if selected_runs["youtube"] else []
    tiktok_videos = _read_jsonl((selected_runs["tiktok"] or Path()) / "videos.jsonl") if selected_runs["tiktok"] else []
    x_tweets = _read_jsonl((selected_runs["x"] or Path()) / "tweets_normalized.jsonl") if selected_runs["x"] else []

    lines = [
        f"# Synthese globale Decathlon / Intersport - {run_id}",
        "",
        "## Perimetre execute",
        "",
    ]
    for source_name, run_path in selected_runs.items():
        if run_path:
            lines.append(f"- {source_name.title()}: `{run_path}`")
        else:
            lines.append(f"- {source_name.title()}: non disponible")

    lines.extend(
        [
            "",
            "## Volumes par source",
            "",
            f"- Reddit: `{len(reddit_posts)}` posts, `{len(reddit_comments)}` commentaires",
            f"- Google News: `{len(news_articles)}` articles",
            f"- Review sites: `{len(review_rows)}` lignes d'avis",
            f"- Google Maps / stores: `{len(store_reviews)}` avis, `{len(store_rows)}` magasins",
            f"- YouTube: `{len(youtube_videos)}` videos, `{len(youtube_comments)}` commentaires",
            f"- TikTok: `{len(tiktok_videos)}` videos",
            f"- X: `{len(x_tweets)}` posts normalises",
            "",
            "## Lecture executive",
            "",
            f"- Review sites: brands {_counter_line(Counter(row.get('brand_focus') for row in review_rows if row.get('brand_focus')))}",
            f"- Stores: brands {_counter_line(Counter(row.get('brand_focus') for row in store_reviews if row.get('brand_focus')))}",
            f"- News: brands {_counter_line(Counter(row.get('brand_focus') for row in news_articles if row.get('brand_focus')))}",
            f"- Reddit: brands {_counter_line(Counter(row.get('brand_focus') for row in reddit_posts if row.get('brand_focus')))}",
            f"- YouTube: pillars {_counter_line(Counter(row.get('pillar') for row in youtube_videos if row.get('pillar')))}",
            f"- TikTok: pillars {_counter_line(Counter(row.get('pillar') for row in tiktok_videos if row.get('pillar')))}",
            f"- X: brands {_counter_line(Counter(row.get('brand_focus') for row in x_tweets if row.get('brand_focus')))}",
            "",
            "## Detail par bloc",
            "",
            "### Review sites",
            "",
            f"- Sources review: {_counter_line(Counter(row.get('site') for row in review_rows if row.get('site')))}",
            f"- Scopes review: {_counter_line(Counter(row.get('review_scope') for row in review_rows if row.get('review_scope')))}",
            f"- Brands review: {_counter_line(Counter(row.get('brand_focus') for row in review_rows if row.get('brand_focus')))}",
            "",
            "### Google Maps / stores",
            "",
            f"- Store statuses: {_counter_line(Counter(row.get('status') for row in store_rows if row.get('status')))}",
            f"- Store review brands: {_counter_line(Counter(row.get('brand_focus') for row in store_reviews if row.get('brand_focus')))}",
            "",
            "### Google News",
            "",
            f"- News brands: {_counter_line(Counter(row.get('brand_focus') for row in news_articles if row.get('brand_focus')))}",
            f"- News signaux: {_counter_line(Counter(row.get('signal_type') for row in news_articles if row.get('signal_type')))}",
            "",
            "### Reddit",
            "",
            f"- Reddit brands: {_counter_line(Counter(row.get('brand_focus') for row in reddit_posts if row.get('brand_focus')))}",
            f"- Reddit subreddits: {_counter_line(Counter(row.get('subreddit') for row in reddit_posts if row.get('subreddit')))}",
            "",
            "### YouTube",
            "",
            f"- YouTube brands: {_counter_line(Counter(row.get('brand_focus') for row in youtube_videos if row.get('brand_focus')))}",
            f"- YouTube pillars: {_counter_line(Counter(row.get('pillar') for row in youtube_videos if row.get('pillar')))}",
            f"- YouTube source types: {_counter_line(Counter(row.get('source_type') for row in youtube_videos if row.get('source_type')))}",
            "",
            "### TikTok",
            "",
            f"- TikTok brands: {_counter_line(Counter(row.get('brand_focus') for row in tiktok_videos if row.get('brand_focus')))}",
            f"- TikTok pillars: {_counter_line(Counter(row.get('pillar') for row in tiktok_videos if row.get('pillar')))}",
            f"- TikTok source types: {_counter_line(Counter(row.get('source_type') for row in tiktok_videos if row.get('source_type')))}",
            "",
            "### X",
            "",
            f"- X brands: {_counter_line(Counter(row.get('brand_focus') for row in x_tweets if row.get('brand_focus')))}",
            f"- X search types: {_counter_line(Counter(row.get('search_type') for row in x_tweets if row.get('search_type')))}",
            "",
            "## Ce que tu as vraiment aujourd'hui",
            "",
            "1. Un aggregateur unifie qui integre maintenant YouTube et TikTok en plus des blocs reviews, stores, news, Reddit et X.",
            "2. Des partitions de sources separees, ce qui permet de construire un dashboard propre sans melanger des semantiques incompatibles.",
            "3. Une lecture rapide des derniers runs disponibles, utile pour un point de situation avant ingestion Sheets ou Supabase.",
            "",
            "## Priorites recommandees",
            "",
            "1. Conserver `source_partition`, `brand_focus`, `entity_level` et `pillar` dans la base cible.",
            "2. Ne pas additionner les signaux sociaux YouTube/TikTok avec les notes clients sans un traitement IA explicite.",
            "3. Traiter les sources sociales comme de l'awareness / benchmark / verbatim, pas comme de la satisfaction client brute.",
        ]
    )

    summary_path = run_dir / "global_summary.md"
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a global markdown summary from the latest monitor runs.")
    parser.add_argument("--output-dir", default="data/global_runs")
    parser.add_argument("--reddit-run", default=None)
    parser.add_argument("--news-run", default=None)
    parser.add_argument("--review-run", default=None)
    parser.add_argument("--store-run", default=None)
    parser.add_argument("--youtube-run", default=None)
    parser.add_argument("--tiktok-run", default=None)
    parser.add_argument("--x-run", default=None)
    args = parser.parse_args()
    summary_path = build_global_summary(
        output_dir=args.output_dir,
        reddit_run=args.reddit_run,
        news_run=args.news_run,
        review_run=args.review_run,
        store_run=args.store_run,
        youtube_run=args.youtube_run,
        tiktok_run=args.tiktok_run,
        x_run=args.x_run,
    )
    print(summary_path)


if __name__ == "__main__":
    main()
