from __future__ import annotations

import logging
import os
import re
import time
from collections import Counter
from pathlib import Path

from .exporter import build_run_artifacts, export_markdown, export_run
from .models import NormalizedTweetRecord, QueryRun, QuerySpec, RawTweetRecord, RunResult
from .queries import build_queries


log = logging.getLogger("x_monitor")

INTER_QUERY_DELAY_SECONDS = 5.0
MAX_SCROLLS = 3
SCROLL_PAUSE_SECONDS = 2.5


class AuthError(RuntimeError):
    pass


def _get_auth_tokens() -> tuple[str, str]:
    auth_token = os.environ.get("X_AUTH_TOKEN") or os.environ.get("TWITTER_AUTH_TOKEN") or ""
    ct0 = os.environ.get("X_CT0") or os.environ.get("TWITTER_CT0") or ""
    if not auth_token or not ct0:
        raise AuthError("Missing X auth cookies. Set X_AUTH_TOKEN and X_CT0.")
    return auth_token, ct0


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


def _extract_tweets_from_page(page) -> list[dict]:
    """Extract tweet data from the current page DOM."""
    tweets = []
    seen_ids: set[str] = set()

    articles = page.query_selector_all('article[data-testid="tweet"]')
    for article in articles:
        try:
            tweet: dict = {}

            # Author handle
            user_link = article.query_selector('a[role="link"][href*="/"]')
            if user_link:
                href = user_link.get_attribute("href") or ""
                tweet["author_handle"] = href.strip("/").split("/")[-1] if href else ""
            else:
                tweet["author_handle"] = ""

            # Author name
            author_name_el = article.query_selector('a[role="link"] span')
            tweet["author_name"] = (author_name_el.inner_text() if author_name_el else "").strip()

            # Tweet text
            text_el = article.query_selector('div[data-testid="tweetText"]')
            tweet["text"] = (text_el.inner_text() if text_el else "").strip()
            if not tweet["text"]:
                continue

            # Timestamp
            time_el = article.query_selector("time")
            tweet["created_at"] = time_el.get_attribute("datetime") if time_el else ""

            # Tweet URL / ID
            time_link = article.query_selector('a[href*="/status/"]')
            if time_link:
                href = time_link.get_attribute("href") or ""
                tweet["tweet_url"] = f"https://x.com{href}" if href.startswith("/") else href
                match = re.search(r"/status/(\d+)", href)
                tweet["id"] = match.group(1) if match else ""
            else:
                tweet["id"] = ""
                tweet["tweet_url"] = ""

            if not tweet["id"] or tweet["id"] in seen_ids:
                continue
            seen_ids.add(tweet["id"])

            # Engagement metrics
            tweet["engagement"] = {"likes": 0, "retweets": 0, "replies": 0, "quotes": 0, "views": 0}
            metrics = article.query_selector_all("button[data-testid]")
            for btn in metrics:
                testid = btn.get_attribute("data-testid") or ""
                aria = btn.get_attribute("aria-label") or ""
                numbers = re.findall(r"[\d,]+", aria)
                count = int(numbers[0].replace(",", "")) if numbers else 0
                if "reply" in testid:
                    tweet["engagement"]["replies"] = count
                elif "retweet" in testid:
                    tweet["engagement"]["retweets"] = count
                elif "like" in testid:
                    tweet["engagement"]["likes"] = count

            # Views
            analytics = article.query_selector('a[href*="/analytics"]')
            if analytics:
                aria = analytics.get_attribute("aria-label") or ""
                numbers = re.findall(r"[\d,]+", aria)
                tweet["engagement"]["views"] = int(numbers[0].replace(",", "")) if numbers else 0

            tweets.append(tweet)
        except Exception:
            continue

    return tweets


def _scrape_query_playwright(page, run_id: str, spec: QuerySpec) -> tuple[QueryRun, list[RawTweetRecord], list[NormalizedTweetRecord]]:
    """Run a single search query via Playwright and extract tweets."""
    # Build search URL
    search_filter = "live" if spec.search_type == "latest" else "top"
    # Use the raw query keyword (strip advanced operators for browser search)
    raw_query = spec.query_text.split('"')[1] if '"' in spec.query_text else spec.query_text
    url = f"https://x.com/search?q={raw_query}&src=typed_query&f={search_filter}"

    query_run = QueryRun(
        run_id=run_id,
        query_name=spec.name,
        brand_focus=spec.brand_focus,
        query_text=spec.query_text,
        search_type=spec.search_type,
        count=spec.count,
        pages=spec.pages,
        command=f"playwright: {url}",
    )

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        time.sleep(3)

        all_raw: list[dict] = []
        seen_ids: set[str] = set()

        for _ in range(MAX_SCROLLS):
            page_tweets = _extract_tweets_from_page(page)
            for t in page_tweets:
                if t["id"] not in seen_ids:
                    all_raw.append(t)
                    seen_ids.add(t["id"])
            page.evaluate("window.scrollBy(0, window.innerHeight * 2)")
            time.sleep(SCROLL_PAUSE_SECONDS)

        raw_rows: list[RawTweetRecord] = []
        normalized_rows: list[NormalizedTweetRecord] = []

        for tweet in all_raw:
            tweet_id = str(tweet.get("id", ""))
            raw_rows.append(RawTweetRecord(
                run_id=run_id,
                query_name=spec.name,
                query_text=spec.query_text,
                search_type=spec.search_type,
                brand_focus=spec.brand_focus,
                tweet_id=tweet_id,
                raw_tweet=tweet,
            ))
            normalized = _normalize_playwright_tweet(run_id, spec, tweet)
            if normalized:
                normalized_rows.append(normalized)

        query_run.raw_count = len(raw_rows)
        query_run.retained_count = len(normalized_rows)
        log.info("[%s] %s %s -> %d tweets", spec.brand_focus, spec.name, spec.search_type, len(normalized_rows))

    except Exception as exc:
        query_run.error = str(exc)
        log.warning("[%s] %s failed: %s", spec.brand_focus, spec.name, exc)
        raw_rows = []
        normalized_rows = []

    return query_run, raw_rows, normalized_rows


def _normalize_playwright_tweet(run_id: str, spec: QuerySpec, tweet: dict) -> NormalizedTweetRecord | None:
    review_id = str(tweet.get("id", "")).strip()
    if not review_id:
        return None

    engagement = tweet.get("engagement") or {}
    text = str(tweet.get("text", "") or "").strip()
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
        post_type="tweet",
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
        is_verified=False,
        language="",
        location="",
        tweet_url=str(tweet.get("tweet_url", "") or ""),
        author_name=str(tweet.get("author_name", "") or ""),
        author_handle=str(tweet.get("author_handle", "") or ""),
        conversation_id="",
        reply_to_id="",
        reply_to_handle="",
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
    top_tweets = sorted(
        result.tweets,
        key=lambda tweet: (tweet.engagement_score, tweet.view_count, tweet.likes),
        reverse=True,
    )[:10]

    lines = [
        f"# X monitor results - Run {result.run_id}",
        "",
        "## Scope",
        "",
        f"- brand: `{result.selected_brand}`",
        f"- auth: `{result.auth_mode}`",
        f"- backend: `playwright`",
        f"- raw tweets: `{len(result.raw_tweets)}`",
        f"- normalized tweets: `{len(result.tweets)}`",
        "",
        "## Query Summary",
        "",
        "| Query | Brand | Type | Raw | Valid | Added | Status |",
        "| --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for qr in result.query_runs:
        status = "ok"
        if qr.error:
            status = f"error: {qr.error}"
        elif qr.warning:
            status = f"warning: {qr.warning}"
        lines.append(f"| {qr.query_name} | {qr.brand_focus} | {qr.search_type} | {qr.raw_count} | {qr.retained_count} | {qr.added_count} | {status} |")

    lines.extend([
        "",
        "## Distribution",
        "",
        f"- brands: {', '.join(f'`{b}`={c}' for b, c in sorted(brand_counts.items())) or '`none`'}",
        "",
        "## Top Tweets",
        "",
        "| Brand | Engagement | Views | Author | Excerpt |",
        "| --- | ---: | ---: | --- | --- |",
    ])
    for tweet in top_tweets:
        excerpt = tweet.text.replace("|", " ").replace("\n", " ")[:150]
        lines.append(f"| {tweet.brand} | {tweet.engagement_score} | {tweet.view_count} | @{tweet.author_handle or '-'} | {excerpt} |")

    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        for w in result.warnings:
            lines.append(f"- {w}")

    return "\n".join(lines) + "\n"


def run_monitor(
    *,
    brand: str,
    latest_count: int,
    latest_pages: int,
    top_count: int,
    top_pages: int,
    output_dir: str,
    clix_bin: str = "",
    debug: bool = False,
) -> RunResult:
    from playwright.sync_api import sync_playwright

    auth_token, ct0 = _get_auth_tokens()
    artifacts = build_run_artifacts(output_dir)
    warnings: list[str] = []
    query_runs: list[QueryRun] = []
    raw_tweets: list[RawTweetRecord] = []
    normalized_tweets: list[NormalizedTweetRecord] = []
    query_specs = build_queries(brand, latest_count, latest_pages, top_count, top_pages)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s", datefmt="%H:%M:%S")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            locale="en-US",
        )
        context.add_cookies([
            {"name": "auth_token", "value": auth_token, "domain": ".x.com", "path": "/"},
            {"name": "ct0", "value": ct0, "domain": ".x.com", "path": "/"},
        ])

        page = context.new_page()

        # Verify login
        page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=20000)
        time.sleep(3)
        if "/login" in page.url:
            browser.close()
            raise AuthError("Playwright login failed — cookies may be expired.")

        log.info("Logged in via Playwright, running %d queries", len(query_specs))

        for index, spec in enumerate(query_specs):
            qr, raw, norm = _scrape_query_playwright(page, artifacts.run_id, spec)
            query_runs.append(qr)
            raw_tweets.extend(raw)
            normalized_tweets.extend(norm)
            if qr.warning:
                warnings.append(f"{qr.query_name}: {qr.warning}")
            if qr.error:
                warnings.append(f"{qr.query_name}: {qr.error}")
            if index < len(query_specs) - 1:
                time.sleep(INTER_QUERY_DELAY_SECONDS)

        browser.close()

    deduped_tweets = _dedupe_tweets(normalized_tweets, query_runs)
    export_run(artifacts, query_runs, raw_tweets, deduped_tweets)
    result = RunResult(
        run_id=artifacts.run_id,
        run_dir=artifacts.run_dir,
        selected_brand=brand,
        clix_bin="playwright",
        auth_mode="env_vars",
        query_runs=query_runs,
        raw_tweets=raw_tweets,
        tweets=deduped_tweets,
        warnings=warnings,
    )
    export_markdown(artifacts, _build_markdown(result))
    return result


def run_monitor_sync(**kwargs) -> RunResult:
    return run_monitor(**kwargs)
