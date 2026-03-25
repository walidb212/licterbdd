from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from collections import Counter
from typing import Any

from .exporter import build_run_artifacts, export_markdown, export_run
from .models import NewsArticleRecord, QueryRun, RunResult
from .parser import build_article_record, is_relevant_article, merge_article, parse_rss_feed
from .queries import build_queries


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
)


def _fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.7"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", "replace")


def _load_wrangler_account_id() -> str:
    command = [r"C:\Users\walid\AppData\Roaming\npm\wrangler.cmd", "whoami"]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    except Exception:
        return ""
    if completed.returncode != 0:
        return ""
    for line in completed.stdout.splitlines():
        if "Account ID" in line:
            parts = [part.strip() for part in line.split("│") if part.strip()]
            if parts:
                candidate = parts[-1]
                if len(candidate) == 32:
                    return candidate
    return ""


def _resolve_cloudflare_credentials() -> tuple[str, str]:
    token = (
        os.environ.get("CLOUDFLARE_API_TOKEN")
        or os.environ.get("CF_API_TOKEN")
        or os.environ.get("CLOUDFLARE_BROWSER_RENDERING_TOKEN")
        or ""
    ).strip()
    account_id = (
        os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        or os.environ.get("CF_ACCOUNT_ID")
        or _load_wrangler_account_id()
    ).strip()
    return token, account_id


def _fetch_cloudflare_markdown(url: str, token: str, account_id: str) -> tuple[str, str]:
    endpoint = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/browser-rendering/markdown"
    payload = json.dumps({"url": url}).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        data = json.loads(response.read().decode("utf-8", "replace"))
    result = data.get("result")
    if isinstance(result, str):
        markdown = result
        snapshot_url = url
    else:
        result = result or {}
        markdown = result.get("markdown") or result.get("content") or ""
        snapshot_url = result.get("url") or url
    return markdown, snapshot_url


def _enrich_articles(
    articles: list[NewsArticleRecord],
    *,
    enrich_mode: str,
    max_enriched_items: int,
    warnings: list[str],
) -> str:
    token, account_id = _resolve_cloudflare_credentials()
    if enrich_mode == "none":
        return "none"
    if not token:
        warnings.append(
            "Cloudflare Browser Rendering disabled: CLOUDFLARE_API_TOKEN/CF_API_TOKEN missing. Wrangler OAuth login is not enough for the REST endpoint."
        )
        return "disabled"
    if not account_id:
        warnings.append("Cloudflare Browser Rendering disabled: account id not found.")
        return "disabled"

    mode_used = "cloudflare"
    for article in articles[:max_enriched_items]:
        try:
            markdown, snapshot_url = _fetch_cloudflare_markdown(article.google_news_url, token, account_id)
            article.article_markdown = markdown[:12000]
            article.article_snapshot_url = snapshot_url
            article.enrichment_mode = mode_used
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                warnings.append(
                    "Cloudflare Browser Rendering returned 401. The provided token is valid but not authorized for Browser Rendering on this account."
                )
                return "disabled"
            warnings.append(f"Cloudflare markdown failed for {article.google_news_url}: HTTP {exc.code}")
        except Exception as exc:
            warnings.append(f"Cloudflare markdown failed for {article.google_news_url}: {exc}")
    return mode_used


def _build_markdown(result: RunResult) -> str:
    brand_counts = Counter(article.brand_detected for article in result.articles)
    signal_counts = Counter(article.signal_type for article in result.articles)
    source_counts = Counter(article.source_name for article in result.articles if article.source_name)
    top_sources = sorted(source_counts.items(), key=lambda item: (-item[1], item[0]))[:10]
    top_articles = sorted(result.articles, key=lambda article: (article.published_at, article.source_name), reverse=True)[:12]

    lines = [
        f"# Google News monitor - Run {result.run_id}",
        "",
        "## Scope",
        "",
        f"- brand: `{result.selected_brand}`",
        f"- region: `{result.selected_region}`",
        f"- cloudflare enrichment: `{result.cloudflare_mode}`",
        f"- retained articles: `{len(result.articles)}`",
        "",
        "## Query Summary",
        "",
        "| Query | Brand | Fetched | Retained | Added | Status |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for query_run in result.query_runs:
        status = "ok"
        if query_run.error:
            status = f"error: {query_run.error}"
        elif query_run.warning:
            status = f"warning: {query_run.warning}"
        lines.append(
            f"| {query_run.query_name} | {query_run.brand_focus} | {query_run.fetched_count} | {query_run.retained_count} | {query_run.added_count} | {status} |"
        )

    lines.extend(
        [
            "",
            "## Distribution",
            "",
            f"- brands: {', '.join(f'`{brand}`={count}' for brand, count in sorted(brand_counts.items())) or '`none`'}",
            f"- signals: {', '.join(f'`{signal}`={count}' for signal, count in sorted(signal_counts.items())) or '`none`'}",
            f"- top sources: {', '.join(f'`{name}`={count}' for name, count in top_sources) or '`none`'}",
            "",
            "## Top Articles",
            "",
            "| Published | Brand | Signal | Source | Title |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for article in top_articles:
        lines.append(
            f"| {article.published_at or '-'} | {article.brand_detected} | {article.signal_type} | {article.source_name or '-'} | {article.article_title.replace('|', ' ')[:180]} |"
        )

    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in result.warnings:
            lines.append(f"- {warning}")

    return "\n".join(lines) + "\n"


def run_monitor(
    *,
    brand: str,
    language: str,
    region: str,
    days_back: int,
    max_items_per_query: int,
    output_dir: str,
    enrich_mode: str,
    max_enriched_items: int,
) -> RunResult:
    artifacts = build_run_artifacts(output_dir)
    query_specs = build_queries(brand, language=language, region=region, days_back=days_back)
    query_runs: list[QueryRun] = []
    warnings: list[str] = []
    by_id: dict[str, NewsArticleRecord] = {}

    for spec in query_specs:
        query_run = QueryRun(
            run_id=artifacts.run_id,
            query_name=spec.name,
            brand_focus=spec.brand_focus,
            query_text=spec.query_text,
            rss_url=spec.rss_url,
        )
        try:
            xml_text = _fetch_text(spec.rss_url)
            _, items = parse_rss_feed(xml_text)
            query_run.fetched_count = len(items)
            retained = []
            for item in items[:max_items_per_query]:
                article = build_article_record(artifacts.run_id, spec, item)
                if not is_relevant_article(article):
                    continue
                retained.append(article)
            query_run.retained_count = len(retained)
            for article in retained:
                if article.article_id not in by_id:
                    by_id[article.article_id] = article
                    query_run.added_count += 1
                else:
                    merge_article(by_id[article.article_id], article)
        except Exception as exc:
            query_run.error = str(exc)
            warnings.append(f"{spec.name}: {exc}")
        query_runs.append(query_run)

    articles = list(by_id.values())
    articles.sort(key=lambda a: (0 if a.signal_type == "reputation" else 1, a.published_at or ""), reverse=False)
    cloudflare_mode = _enrich_articles(
        articles,
        enrich_mode=enrich_mode,
        max_enriched_items=max_enriched_items,
        warnings=warnings,
    )
    export_run(artifacts, query_runs, articles)
    result = RunResult(
        run_id=artifacts.run_id,
        run_dir=artifacts.run_dir,
        selected_brand=brand,
        selected_region=region,
        query_runs=query_runs,
        articles=articles,
        cloudflare_mode=cloudflare_mode,
        warnings=warnings,
    )
    export_markdown(artifacts, _build_markdown(result))
    return result


def run_monitor_sync(**kwargs) -> RunResult:
    return run_monitor(**kwargs)
