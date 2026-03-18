from __future__ import annotations

import asyncio
from collections import Counter

from monitor_core import StateStore, build_content_hash, normalize_hash_input

from .discovery import (
    enrich_missing_store_metadata_pagesjaunes,
    discover_decathlon_inventory_http,
    discover_intersport_inventory_browser,
    load_legacy_decathlon_inventory,
    load_manual_inventory,
    merge_store_lists,
)
from .exporter import build_run_artifacts, export_markdown, export_run
from .google_maps import load_legacy_google_maps_reviews, scrape_google_maps_reviews
from .models import RunResult, StoreRecord, StoreReviewRecord

MONITOR_NAME = "store_monitor"


def _build_markdown(result: RunResult) -> str:
    by_brand = Counter(store.brand_focus for store in result.stores)
    by_status = Counter(store.status for store in result.stores)
    review_brands = Counter(review.brand_focus for review in result.reviews)
    top_reviews = sorted(result.reviews, key=lambda review: (review.rating or 0, len(review.body)), reverse=True)[:12]
    lines = [
        f"# Store monitor - Run {result.run_id}",
        "",
        "## Scope",
        "",
        f"- brand: `{result.selected_brand}`",
        f"- stage: `{result.selected_stage}`",
        f"- stores: `{len(result.stores)}`",
        f"- reviews: `{len(result.reviews)}`",
        f"- store brands: {', '.join(f'`{brand}`={count}' for brand, count in sorted(by_brand.items())) or '`none`'}",
        f"- store statuses: {', '.join(f'`{status}`={count}' for status, count in sorted(by_status.items())) or '`none`'}",
        f"- review brands: {', '.join(f'`{brand}`={count}' for brand, count in sorted(review_brands.items())) or '`none`'}",
        "",
        "## Store Sample",
        "",
        "| Brand | Store | Postal | City | Discovery | Status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for store in result.stores[:15]:
        lines.append(
            f"| {store.brand_focus} | {store.store_name.replace('|', ' ')[:100]} | {store.postal_code or '-'} | {store.city or '-'} | {store.discovery_source} | {store.status} |"
        )
    if top_reviews:
        lines.extend(
            [
                "",
                "## Review Sample",
                "",
                "| Brand | Store | Rating | Author | Excerpt |",
                "| --- | --- | ---: | --- | --- |",
            ]
        )
        for review in top_reviews:
            rating = "-" if review.rating is None else f"{review.rating:.1f}"
            lines.append(
                f"| {review.brand_focus} | {review.entity_name.replace('|', ' ')[:90]} | {rating} | {(review.author or '-').replace('|', ' ')[:50]} | {review.body.replace('|', ' ')[:180]} |"
            )
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in result.warnings:
            lines.append(f"- {warning}")
    return "\n".join(lines) + "\n"


def _store_entity_key(store: StoreRecord) -> str:
    return normalize_hash_input(store.brand_focus, store.store_name, store.google_maps_url or store.store_url or store.city)


def _store_review_item_key(review: StoreReviewRecord) -> str:
    return normalize_hash_input(review.entity_name, review.author, review.date_raw, review.body[:80])


def _apply_incremental_store_reviews(
    *,
    state_store: StateStore,
    reviews: list[StoreReviewRecord],
) -> tuple[list[StoreReviewRecord], int]:
    filtered: list[StoreReviewRecord] = []
    skipped = 0
    for review in reviews:
        entity_key = normalize_hash_input(review.brand_focus, review.entity_name, review.google_maps_url or review.store_url)
        is_new = state_store.record_item(
            monitor_name=MONITOR_NAME,
            source_name="google_maps_legacy",
            source_partition=review.source_partition,
            entity_key=entity_key,
            item_key=_store_review_item_key(review),
            content_hash=build_content_hash(review.author, review.date_raw, review.body),
            published_at=None,
            metadata={"rating": review.rating},
        )
        if not is_new:
            skipped += 1
            continue
        filtered.append(review)
    return filtered, skipped


async def run_monitor(
    *,
    brand: str,
    stage: str,
    output_dir: str,
    incremental: bool,
    state_db: str,
    city_seeds: list[str],
    stale_after_days: int,
    headless: bool,
    debug: bool,
    limit_stores: int | None,
    max_reviews_per_store: int,
    resume: bool,
) -> RunResult:
    artifacts = build_run_artifacts(output_dir)
    warnings: list[str] = []
    stores: list[StoreRecord] = []
    reviews: list[StoreReviewRecord] = []
    state_store = StateStore(state_db) if incremental else None
    if state_store is not None:
        state_store.log_run_start(
            artifacts.run_id,
            MONITOR_NAME,
            artifacts.run_dir,
            config={
                "brand": brand,
                "stage": stage,
                "incremental": incremental,
                "city_seeds": city_seeds,
                "stale_after_days": stale_after_days,
            },
        )

    try:
        if brand in {"both", "decathlon"}:
            decathlon_stores, decathlon_warnings = load_legacy_decathlon_inventory(artifacts.run_id)
            warnings.extend(decathlon_warnings)
            if not decathlon_stores:
                try:
                    decathlon_stores = discover_decathlon_inventory_http(artifacts.run_id)
                except Exception as exc:
                    warnings.append(f"Decathlon store discovery failed: {exc}")
            stores.extend(decathlon_stores)

        if brand in {"both", "intersport"}:
            manual_intersport_stores, manual_warnings = load_manual_inventory(artifacts.run_id, "intersport")
            warnings.extend(manual_warnings)
            discovered_intersport_stores = manual_intersport_stores
            if not discovered_intersport_stores:
                try:
                    discovered_intersport_stores, intersport_warnings = await discover_intersport_inventory_browser(
                        artifacts.run_id,
                        headless=headless,
                        debug=debug,
                        city_seeds=city_seeds,
                    )
                    warnings.extend(intersport_warnings)
                except Exception as exc:
                    warnings.append(f"Intersport store discovery failed: {exc}")
            discovered_intersport_stores, pagesjaunes_warnings = enrich_missing_store_metadata_pagesjaunes(discovered_intersport_stores)
            warnings.extend(pagesjaunes_warnings)
            stores.extend(discovered_intersport_stores)

        stores = merge_store_lists(stores)
        if state_store is not None:
            for store in stores:
                state_store.upsert_entity(
                    monitor_name=MONITOR_NAME,
                    source_name="store_discovery",
                    entity_key=_store_entity_key(store),
                    entity_name=store.store_name,
                    entity_url=store.google_maps_url or store.store_url,
                    metadata={
                        "brand_focus": store.brand_focus,
                        "city": store.city,
                        "postal_code": store.postal_code,
                    },
                    mark_scraped=False,
                )

        if stage in {"all", "reviews"}:
            baseline_stores: list[StoreRecord] = []
            baseline_reviews: list[StoreReviewRecord] = []
            known_store_names: set[tuple[str, str]] = set()
            if resume and brand in {"both", "decathlon"}:
                baseline_stores, baseline_reviews = load_legacy_google_maps_reviews(artifacts.run_id, "decathlon")
                if state_store is not None:
                    baseline_reviews, skipped = _apply_incremental_store_reviews(state_store=state_store, reviews=baseline_reviews)
                    if skipped:
                        warnings.append(f"Skipped {skipped} legacy Google Maps review rows already present in incremental state.")
                reviews.extend(baseline_reviews)
                for row in baseline_stores:
                    known_store_names.add((row.brand_focus, row.store_name))
                warnings.append(f"Loaded {len(baseline_stores)} Decathlon stores and {len(baseline_reviews)} reviews from legacy Google Maps JSON.")
            stores = merge_store_lists(stores, baseline_stores)
            pending_stores = [store for store in stores if (store.brand_focus, store.store_name) not in known_store_names]
            if limit_stores is not None:
                pending_stores = pending_stores[:limit_stores]

            def checkpoint_callback(snapshot_stores: list[StoreRecord], snapshot_reviews: list[StoreReviewRecord]) -> None:
                export_run(artifacts, merge_store_lists([store for store in stores if (store.brand_focus, store.store_name) in known_store_names], snapshot_stores), reviews + snapshot_reviews)

            scraped_stores, scraped_reviews, scrape_warnings = await scrape_google_maps_reviews(
                pending_stores,
                max_reviews_per_store=max_reviews_per_store,
                headless=headless,
                debug=debug,
                incremental=incremental,
                state_store=state_store,
                stale_after_days=stale_after_days,
                checkpoint_every=10,
                checkpoint_callback=checkpoint_callback,
            )
            warnings.extend(scrape_warnings)
            reviews.extend(scraped_reviews)
            stores = merge_store_lists([store for store in stores if (store.brand_focus, store.store_name) in known_store_names], scraped_stores)
        elif limit_stores is not None:
            stores = stores[:limit_stores]

        export_run(artifacts, stores, reviews)
        result = RunResult(
            run_id=artifacts.run_id,
            run_dir=artifacts.run_dir,
            selected_brand=brand,
            selected_stage=stage,
            stores=stores,
            reviews=reviews,
            warnings=warnings,
        )
        export_markdown(artifacts, _build_markdown(result))
        if state_store is not None:
            state_store.log_run_end(
                artifacts.run_id,
                status="ok",
                stats={"stores": len(stores), "reviews": len(reviews)},
            )
        return result
    except Exception as exc:
        if state_store is not None:
            state_store.log_run_end(artifacts.run_id, status="error", error=str(exc))
        raise
    finally:
        if state_store is not None:
            state_store.close()


def run_monitor_sync(**kwargs) -> RunResult:
    return asyncio.run(run_monitor(**kwargs))
