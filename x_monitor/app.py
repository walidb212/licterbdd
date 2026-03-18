from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from collections import Counter
from pathlib import Path

from .exporter import build_run_artifacts, export_markdown, export_run
from .models import NormalizedTweetRecord, QueryRun, QuerySpec, RawTweetRecord, RunResult
from .queries import build_queries


INTER_QUERY_DELAY_SECONDS = 3.0


class AuthError(RuntimeError):
    pass


def _workspace_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _stringify_command(command: list[str]) -> str:
    return subprocess.list2cmdline(command)


def _resolve_clix_bin(clix_bin: str) -> str:
    explicit_path = Path(clix_bin).expanduser()
    if explicit_path.exists():
        return str(explicit_path.resolve())

    found = shutil.which(clix_bin)
    if found:
        return found

    workspace_root = _workspace_root()
    local_candidates = [
        workspace_root / ".venv-x" / "Scripts" / "clix.exe",
        workspace_root / ".venv-x" / "bin" / "clix",
    ]
    for candidate in local_candidates:
        if candidate.exists():
            return str(candidate.resolve())

    raise RuntimeError(
        "clix executable not found. Install it in .venv-x or pass --clix-bin "
        "with an explicit path."
    )


def _detect_auth_mode() -> str:
    has_x_pair = bool(os.environ.get("X_AUTH_TOKEN")) and bool(os.environ.get("X_CT0"))
    has_twitter_pair = bool(os.environ.get("TWITTER_AUTH_TOKEN")) and bool(os.environ.get("TWITTER_CT0"))
    if has_x_pair or has_twitter_pair:
        return "env_vars"
    raise AuthError(
        "Missing X auth cookies. Set X_AUTH_TOKEN and X_CT0 before running the monitor."
    )


def _build_command(spec: QuerySpec, clix_bin: str) -> list[str]:
    return [
        clix_bin,
        "search",
        spec.query_text,
        "--type",
        spec.search_type,
        "--count",
        str(spec.count),
        "--pages",
        str(spec.pages),
        "--json",
    ]


def _value_as_int(value: object) -> int:
    if value is None or value == "":
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip().replace(",", "")
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def _infer_brand(text: str, spec_brand_focus: str) -> str:
    if spec_brand_focus in {"decathlon", "intersport"}:
        return spec_brand_focus
    lowered = text.lower()
    has_decathlon = "decathlon" in lowered
    has_intersport = "intersport" in lowered
    if has_decathlon and has_intersport:
        return "both"
    if has_decathlon:
        return "decathlon"
    if has_intersport:
        return "intersport"
    return spec_brand_focus


def normalize_tweet(run_id: str, spec: QuerySpec, tweet: dict) -> NormalizedTweetRecord | None:
    review_id = str(tweet.get("id", "")).strip()
    if not review_id:
        return None

    engagement = tweet.get("engagement") or {}
    text = str(tweet.get("text", "") or "").strip()
    reply_to_id = str(tweet.get("reply_to_id", "") or "").strip()
    tweet_url = str(tweet.get("tweet_url", "") or tweet.get("url", "") or "").strip()
    brand = _infer_brand(text, spec.brand_focus)

    return NormalizedTweetRecord(
        run_id=run_id,
        query_name=spec.name,
        query_text=spec.query_text,
        search_type=spec.search_type,
        query_names=[spec.name],
        query_texts=[spec.query_text],
        search_types=[spec.search_type],
        brand_focus=spec.brand_focus,
        source_brand_focuses=[spec.brand_focus],
        review_id=review_id,
        platform="X",
        brand=brand,
        post_type="reply" if reply_to_id else "tweet",
        text=text,
        date=str(tweet.get("created_at", "") or ""),
        rating=-1,
        likes=_value_as_int(engagement.get("likes")),
        share_count=_value_as_int(engagement.get("retweets")),
        reply_count=_value_as_int(engagement.get("replies")),
        quote_count=_value_as_int(engagement.get("quotes")),
        view_count=_value_as_int(engagement.get("views")),
        sentiment="",
        user_followers=None,
        is_verified=bool(tweet.get("author_verified", False)),
        language=str(tweet.get("language", "") or ""),
        location="",
        tweet_url=tweet_url,
        author_name=str(tweet.get("author_name", "") or ""),
        author_handle=str(tweet.get("author_handle", "") or ""),
        conversation_id=str(tweet.get("conversation_id", "") or ""),
        reply_to_id=reply_to_id,
        reply_to_handle=str(tweet.get("reply_to_handle", "") or ""),
    )


def merge_tweets(existing: NormalizedTweetRecord, incoming: NormalizedTweetRecord) -> NormalizedTweetRecord:
    if incoming.query_name not in existing.query_names:
        existing.query_names.append(incoming.query_name)
    if incoming.query_text not in existing.query_texts:
        existing.query_texts.append(incoming.query_text)
    if incoming.search_type not in existing.search_types:
        existing.search_types.append(incoming.search_type)
    if incoming.brand_focus not in existing.source_brand_focuses:
        existing.source_brand_focuses.append(incoming.brand_focus)

    if existing.brand != incoming.brand:
        existing.brand = "both"

    if incoming.post_type == "reply":
        existing.post_type = "reply"
    if incoming.is_verified:
        existing.is_verified = True
    if incoming.language and not existing.language:
        existing.language = incoming.language
    if incoming.tweet_url and not existing.tweet_url:
        existing.tweet_url = incoming.tweet_url
    if incoming.author_name and not existing.author_name:
        existing.author_name = incoming.author_name
    if incoming.author_handle and not existing.author_handle:
        existing.author_handle = incoming.author_handle
    if incoming.conversation_id and not existing.conversation_id:
        existing.conversation_id = incoming.conversation_id
    if incoming.reply_to_id and not existing.reply_to_id:
        existing.reply_to_id = incoming.reply_to_id
    if incoming.reply_to_handle and not existing.reply_to_handle:
        existing.reply_to_handle = incoming.reply_to_handle
    if len(incoming.text) > len(existing.text):
        existing.text = incoming.text
    if incoming.date and not existing.date:
        existing.date = incoming.date

    existing.likes = max(existing.likes, incoming.likes)
    existing.share_count = max(existing.share_count, incoming.share_count)
    existing.reply_count = max(existing.reply_count, incoming.reply_count)
    existing.quote_count = max(existing.quote_count, incoming.quote_count)
    existing.view_count = max(existing.view_count, incoming.view_count)
    return existing


def _run_query(run_id: str, spec: QuerySpec, clix_bin: str, debug: bool) -> tuple[QueryRun, list[RawTweetRecord], list[NormalizedTweetRecord]]:
    command = _build_command(spec, clix_bin)
    query_run = QueryRun(
        run_id=run_id,
        query_name=spec.name,
        brand_focus=spec.brand_focus,
        query_text=spec.query_text,
        search_type=spec.search_type,
        count=spec.count,
        pages=spec.pages,
        command=_stringify_command(command),
    )
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(_workspace_root()),
    )

    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    combined_error = "\n".join(part for part in [stderr, stdout] if part).lower()

    if completed.returncode != 0:
        if "401" in combined_error or "auth" in combined_error or "login" in combined_error:
            raise AuthError(stderr or stdout or "clix authentication failed")
        if "429" in combined_error or "rate limit" in combined_error:
            query_run.warning = stderr or stdout or "rate limited"
            return query_run, [], []
        query_run.error = stderr or stdout or f"clix exited with code {completed.returncode}"
        return query_run, [], []

    if not stdout:
        query_run.warning = "clix returned no tweets"
        return query_run, [], []

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        query_run.error = f"invalid JSON output: {exc}"
        return query_run, [], []

    if not isinstance(payload, list):
        query_run.error = "clix output was not a tweet list"
        return query_run, [], []

    raw_rows: list[RawTweetRecord] = []
    normalized_rows: list[NormalizedTweetRecord] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        tweet_id = str(item.get("id", "") or "").strip()
        raw_rows.append(
            RawTweetRecord(
                run_id=run_id,
                query_name=spec.name,
                query_text=spec.query_text,
                search_type=spec.search_type,
                brand_focus=spec.brand_focus,
                tweet_id=tweet_id,
                raw_tweet=item,
            )
        )
        normalized = normalize_tweet(run_id, spec, item)
        if normalized is not None:
            normalized_rows.append(normalized)

    query_run.raw_count = len(raw_rows)
    query_run.retained_count = len(normalized_rows)
    if debug and stderr and not query_run.warning:
        query_run.warning = stderr
    return query_run, raw_rows, normalized_rows


def _dedupe_tweets(tweets: list[NormalizedTweetRecord], query_runs: list[QueryRun]) -> list[NormalizedTweetRecord]:
    by_id: dict[str, NormalizedTweetRecord] = {}
    added_counter: Counter[str] = Counter()
    for tweet in tweets:
        if tweet.review_id not in by_id:
            by_id[tweet.review_id] = tweet
            added_counter[tweet.query_name] += 1
            continue
        merge_tweets(by_id[tweet.review_id], tweet)

    for query_run in query_runs:
        query_run.added_count = added_counter.get(query_run.query_name, 0)

    return list(by_id.values())


def _build_markdown(result: RunResult) -> str:
    brand_counts = Counter(tweet.brand for tweet in result.tweets)
    language_counts = Counter(tweet.language or "unknown" for tweet in result.tweets)
    top_tweets = sorted(
        result.tweets,
        key=lambda tweet: (tweet.engagement_score, tweet.view_count, tweet.likes),
        reverse=True,
    )[:10]
    reply_samples = [tweet for tweet in result.tweets if tweet.post_type == "reply"][:5]
    benchmark_samples = [tweet for tweet in result.tweets if any(name.startswith("benchmark_") for name in tweet.query_names)][:5]

    lines = [
        f"# X monitor results - Run {result.run_id}",
        "",
        "## Scope",
        "",
        f"- brand: `{result.selected_brand}`",
        f"- auth: `{result.auth_mode}`",
        f"- clix: `{result.clix_bin}`",
        f"- raw tweets: `{len(result.raw_tweets)}`",
        f"- normalized tweets: `{len(result.tweets)}`",
        "",
        "## Query Summary",
        "",
        "| Query | Brand | Type | Raw | Valid | Added | Status |",
        "| --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for query_run in result.query_runs:
        status = "ok"
        if query_run.error:
            status = f"error: {query_run.error}"
        elif query_run.warning:
            status = f"warning: {query_run.warning}"
        lines.append(
            f"| {query_run.query_name} | {query_run.brand_focus} | {query_run.search_type} | "
            f"{query_run.raw_count} | {query_run.retained_count} | {query_run.added_count} | {status} |"
        )

    lines.extend(
        [
            "",
            "## Distribution",
            "",
            f"- brands: {', '.join(f'`{brand}`={count}' for brand, count in sorted(brand_counts.items())) or '`none`'}",
            f"- languages: {', '.join(f'`{language}`={count}' for language, count in sorted(language_counts.items())) or '`none`'}",
            "",
            "## Top Tweets",
            "",
            "| Brand | Lang | Type | Engagement | Views | Author | Excerpt |",
            "| --- | --- | --- | ---: | ---: | --- | --- |",
        ]
    )
    for tweet in top_tweets:
        excerpt = tweet.text.replace("|", " ")[:180]
        lines.append(
            f"| {tweet.brand} | {tweet.language or '-'} | {tweet.post_type} | {tweet.engagement_score} | "
            f"{tweet.view_count} | {tweet.author_handle or '-'} | {excerpt} |"
        )

    lines.extend(["", "## Reply Samples", "", "| Brand | Author | Reply To | Excerpt |", "| --- | --- | --- | --- |"])
    for tweet in reply_samples:
        lines.append(
            f"| {tweet.brand} | {tweet.author_handle or '-'} | {tweet.reply_to_handle or '-'} | "
            f"{tweet.text.replace('|', ' ')[:180]} |"
        )

    lines.extend(["", "## Benchmark Samples", "", "| Author | Type | Excerpt |", "| --- | --- | --- |"])
    for tweet in benchmark_samples:
        lines.append(f"| {tweet.author_handle or '-'} | {tweet.post_type} | {tweet.text.replace('|', ' ')[:180]} |")

    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in result.warnings:
            lines.append(f"- {warning}")

    return "\n".join(lines) + "\n"


def run_monitor(
    *,
    brand: str,
    latest_count: int,
    latest_pages: int,
    top_count: int,
    top_pages: int,
    output_dir: str,
    clix_bin: str,
    debug: bool,
) -> RunResult:
    resolved_clix = _resolve_clix_bin(clix_bin)
    auth_mode = _detect_auth_mode()
    artifacts = build_run_artifacts(output_dir)
    warnings: list[str] = []
    query_runs: list[QueryRun] = []
    raw_tweets: list[RawTweetRecord] = []
    normalized_tweets: list[NormalizedTweetRecord] = []
    query_specs = build_queries(brand, latest_count, latest_pages, top_count, top_pages)

    for index, spec in enumerate(query_specs):
        try:
            query_run, query_raw_rows, query_normalized_rows = _run_query(artifacts.run_id, spec, resolved_clix, debug)
        except AuthError:
            raise
        except Exception as exc:
            query_run = QueryRun(
                run_id=artifacts.run_id,
                query_name=spec.name,
                brand_focus=spec.brand_focus,
                query_text=spec.query_text,
                search_type=spec.search_type,
                count=spec.count,
                pages=spec.pages,
                command=_stringify_command(_build_command(spec, resolved_clix)),
                error=str(exc),
            )
            query_raw_rows = []
            query_normalized_rows = []

        query_runs.append(query_run)
        raw_tweets.extend(query_raw_rows)
        normalized_tweets.extend(query_normalized_rows)

        if query_run.warning:
            warnings.append(f"{query_run.query_name}: {query_run.warning}")
        if query_run.error:
            warnings.append(f"{query_run.query_name}: {query_run.error}")

        if index < len(query_specs) - 1:
            time.sleep(INTER_QUERY_DELAY_SECONDS)

    deduped_tweets = _dedupe_tweets(normalized_tweets, query_runs)
    export_run(artifacts, query_runs, raw_tweets, deduped_tweets)
    result = RunResult(
        run_id=artifacts.run_id,
        run_dir=artifacts.run_dir,
        selected_brand=brand,
        clix_bin=resolved_clix,
        auth_mode=auth_mode,
        query_runs=query_runs,
        raw_tweets=raw_tweets,
        tweets=deduped_tweets,
        warnings=warnings,
    )
    export_markdown(artifacts, _build_markdown(result))
    return result


def run_monitor_sync(**kwargs) -> RunResult:
    return run_monitor(**kwargs)
