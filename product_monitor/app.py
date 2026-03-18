from __future__ import annotations

import urllib.error
from collections import Counter

from monitor_core import StateStore, build_content_hash, parse_published_at
from monitor_core.cloudflare import fetch_cloudflare_content, resolve_cloudflare_credentials

from .exporter import build_run_artifacts, export_markdown, export_run
from .models import ProductCandidate, ProductRecord, ProductReviewRecord, RunResult
from .parser import extract_product_candidates, parse_product_page, pick_balanced_candidates
from .sources import select_category_sources


MONITOR_NAME = "product_monitor"


def _fetch_html(url: str) -> tuple[str, str]:
    token, account_id = resolve_cloudflare_credentials()
    if not token or not account_id:
        raise RuntimeError("Cloudflare credentials missing for product monitor.")
    return fetch_cloudflare_content(url, token=token, account_id=account_id), "cloudflare"


def _item_key(review: ProductReviewRecord) -> str:
    return review.product_url + "|" + review.author + "|" + review.published_at + "|" + review.title[:80]


def _build_markdown(result: RunResult) -> str:
    brand_counts = Counter(row.brand_focus for row in result.products)
    category_counts = Counter(row.category for row in result.products)
    lines = [
        f"# Product monitor - Run {result.run_id}",
        "",
        "## Scope",
        "",
        f"- brand: `{result.selected_brand}`",
        f"- max products/brand: `{result.max_products_per_brand}`",
        f"- products exported: `{len(result.products)}`",
        f"- reviews exported: `{len(result.reviews)}`",
        f"- brands: {', '.join(f'`{name}`={count}' for name, count in sorted(brand_counts.items())) or '`none`'}",
        f"- categories: {', '.join(f'`{name}`={count}' for name, count in sorted(category_counts.items())) or '`none`'}",
        "",
        "## Product Sample",
        "",
        "| Brand | Category | Product | Agg. | Count | Status |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in result.products[:20]:
        agg = "-" if row.aggregate_rating is None else f"{row.aggregate_rating:.2f}"
        count = "-" if row.aggregate_count is None else str(row.aggregate_count)
        lines.append(f"| {row.brand_focus} | {row.category} | {row.entity_name.replace('|', ' ')[:120]} | {agg} | {count} | {row.status} |")
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in result.warnings:
            lines.append(f"- {warning}")
    return "\n".join(lines) + "\n"


def run_monitor(
    *,
    brand: str,
    max_products_per_brand: int,
    output_dir: str,
    incremental: bool,
    state_db: str,
    debug: bool,
) -> RunResult:
    artifacts = build_run_artifacts(output_dir)
    warnings: list[str] = []
    products: list[ProductRecord] = []
    reviews: list[ProductReviewRecord] = []
    state_store = StateStore(state_db) if incremental else None
    if state_store is not None:
        state_store.log_run_start(
            artifacts.run_id,
            MONITOR_NAME,
            artifacts.run_dir,
            config={"brand": brand, "max_products_per_brand": max_products_per_brand, "incremental": incremental},
        )
    try:
        candidates: list[ProductCandidate] = []
        for source in select_category_sources(brand):
            try:
                html, fetch_mode = _fetch_html(source.url)
                extracted = extract_product_candidates(html, brand_focus=source.brand_focus, category=source.category, source_url=source.url)
                if not extracted:
                    warnings.append(f"{source.brand_focus}:{source.category} returned no product candidates from {fetch_mode}.")
                candidates.extend(extracted)
            except urllib.error.HTTPError as exc:
                warnings.append(f"{source.brand_focus}:{source.category} failed with HTTP {exc.code}.")
            except Exception as exc:
                warnings.append(f"{source.brand_focus}:{source.category} discovery failed: {exc}")

        selected = pick_balanced_candidates(candidates, max_products_per_brand=max_products_per_brand)
        for candidate in selected:
            try:
                html, fetch_mode = _fetch_html(candidate.product_url)
            except Exception as exc:
                warnings.append(f"{candidate.brand_focus}:{candidate.product_name} fetch failed: {exc}")
                products.append(
                    ProductRecord(
                        run_id=artifacts.run_id,
                        brand_focus=candidate.brand_focus,
                        category=candidate.category,
                        source_partition="product",
                        entity_level="product",
                        entity_name=candidate.product_name,
                        product_url=candidate.product_url,
                        discovery_source=candidate.discovery_source,
                        aggregate_rating=None,
                        aggregate_count=None,
                        rating_hint=candidate.rating_hint,
                        review_count_hint=candidate.review_count_hint,
                        fetch_mode="",
                        status="fetch_error",
                    )
                )
                continue
            product_row, review_rows, warning = parse_product_page(
                run_id=artifacts.run_id,
                candidate=candidate,
                html=html,
                fetch_mode=fetch_mode,
            )
            if warning:
                warnings.append(f"{candidate.brand_focus}:{candidate.product_name}: {warning}")
            if state_store is not None:
                entity_key = candidate.product_url
                state_store.upsert_entity(
                    monitor_name=MONITOR_NAME,
                    source_name=candidate.category,
                    entity_key=entity_key,
                    entity_name=product_row.entity_name,
                    entity_url=product_row.product_url,
                    content_hash=build_content_hash(product_row.entity_name, product_row.aggregate_rating, product_row.aggregate_count),
                    metadata={"category": candidate.category, "status": product_row.status},
                    mark_scraped=True,
                )
                filtered_reviews: list[ProductReviewRecord] = []
                skipped = 0
                for row in review_rows:
                    published_at = parse_published_at(row.published_at)
                    is_new = state_store.record_item(
                        monitor_name=MONITOR_NAME,
                        source_name=candidate.category,
                        source_partition=row.source_partition,
                        entity_key=entity_key,
                        item_key=_item_key(row),
                        content_hash=build_content_hash(row.author, row.title, row.body),
                        published_at=published_at,
                        metadata={"rating": row.rating},
                    )
                    if is_new:
                        filtered_reviews.append(row)
                    else:
                        skipped += 1
                if skipped:
                    warnings.append(f"{candidate.brand_focus}:{candidate.product_name}: skipped {skipped} already-seen product reviews.")
                review_rows = filtered_reviews
            products.append(product_row)
            reviews.extend(review_rows)

        export_run(artifacts, products, reviews)
        export_markdown(artifacts, _build_markdown(RunResult(artifacts.run_id, artifacts.run_dir, brand, max_products_per_brand, products, reviews, warnings)))
        if state_store is not None:
            state_store.log_run_end(artifacts.run_id, status="ok", stats={"products": len(products), "reviews": len(reviews)})
    except Exception as exc:
        if state_store is not None:
            state_store.log_run_end(artifacts.run_id, status="error", error=str(exc))
        raise
    finally:
        if state_store is not None:
            state_store.close()
    return RunResult(
        run_id=artifacts.run_id,
        run_dir=artifacts.run_dir,
        selected_brand=brand,
        max_products_per_brand=max_products_per_brand,
        products=products,
        reviews=reviews,
        warnings=warnings,
    )


def run_monitor_sync(**kwargs) -> RunResult:
    return run_monitor(**kwargs)
