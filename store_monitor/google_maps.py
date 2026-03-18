from __future__ import annotations

import asyncio
import json
import random
import re
from pathlib import Path
from typing import Callable, Any

from monitor_core import StateStore, build_content_hash, normalize_hash_input
from .models import StoreRecord, StoreReviewRecord


ROOT_DIR = Path(__file__).resolve().parent.parent
DECATHLON_LEGACY_REVIEWS_PATH = ROOT_DIR / "decathlon_avis.json"

DEFAULT_MAX_REVIEWS = 40
SCROLL_PAUSE_MS = 1800
MAX_SCROLLS = 15
NAV_TIMEOUT_MS = 60000
PAUSE_BETWEEN_STORES = 5.0
MAX_RETRIES = 3
BROWSER_RESTART_EVERY = 25
STORE_MONITOR_REVIEWS_SOURCE = "google_maps_reviews"

SEL_REVIEWS_TAB = [
    'button[aria-label*="Avis"]',
    'button[aria-label*="Reviews"]',
    'div[role="tab"][aria-label*="Avis"]',
]
SEL_REVIEWS_FEED = 'div[role="feed"]'
SEL_REVIEW_ITEM = [
    "div.jftiEf",
    "div[data-review-id]",
    'div[jsaction*="pane.review"]',
]
SEL_AUTHOR = [".d4r55", ".kvMYJc", 'button[aria-label*="Photo de profil"]']
SEL_RATING = ['span[aria-label*="étoile"]', 'span[aria-label*="star"]']
SEL_DATE = [".rsqaWe", ".xRkPPb", 'span[class*="date"]']
SEL_TEXT = [".wiI7pd", ".MyEned", 'span[class*="text"]']
SEL_EXPAND_BTN = [
    'button[jsaction*="pane.review.expandReview"]',
    'button[aria-label*="Voir plus"]',
    'button[aria-label*="See more"]',
]
SEL_GLOBAL_RATING = ["div.F7nice span", "span.ceNzKf", 'div[aria-label*="étoile"] span']
SEL_NB_AVIS = ["span.F7nice + span", 'button[jsaction*="pane.rating.moreReviews"] span']
SEL_CONSENT_BTN = [
    'button[aria-label*="Tout accepter"]',
    'button[aria-label*="Accept all"]',
    'button[aria-label*="Accepter tout"]',
    'form[action*="consent"] button',
    "#L2AGLb",
]


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _repair_mojibake(value: str) -> str:
    if not value:
        return value
    if not any(token in value for token in ("Ã", "Â", "â", "ð")):
        return value
    try:
        repaired = value.encode("latin1").decode("utf-8")
    except Exception:
        return value
    suspicious_before = sum(value.count(token) for token in ("Ã", "Â", "â", "ð"))
    suspicious_after = sum(repaired.count(token) for token in ("Ã", "Â", "â", "ð"))
    return repaired if suspicious_after < suspicious_before else value


def _parse_rating_from_label(label: str) -> float | None:
    if not label:
        return None
    match = re.search(r"(\d+[.,]?\d*)\s*(étoile|star)", label, re.I)
    if match:
        return float(match.group(1).replace(",", "."))
    match = re.search(r"^(\d+[.,]?\d*)", label.strip())
    if match:
        return float(match.group(1).replace(",", "."))
    return None


def _store_entity_key(store: StoreRecord) -> str:
    return normalize_hash_input(store.brand_focus, store.store_name, store.google_maps_url or store.city)


def _payload_signature_hash(payloads: list[dict]) -> str:
    return build_content_hash(*(normalize_hash_input(row.get("author"), row.get("date_raw"), row.get("body")) for row in payloads))


def load_legacy_google_maps_reviews(run_id: str, brand_focus: str) -> tuple[list[StoreRecord], list[StoreReviewRecord]]:
    if brand_focus != "decathlon" or not DECATHLON_LEGACY_REVIEWS_PATH.exists():
        return [], []
    payload = json.loads(DECATHLON_LEGACY_REVIEWS_PATH.read_text(encoding="utf-8"))
    stores: list[StoreRecord] = []
    reviews: list[StoreReviewRecord] = []
    for store in payload.get("magasins", []):
        store_name = _clean_text(_repair_mojibake(store.get("nom", "")))
        address = _clean_text(_repair_mojibake(store.get("adresse", "")))
        google_maps_url = store.get("google_maps", "")
        aggregate_rating = store.get("note_globale")
        aggregate_count = store.get("nb_avis_total")
        stores.append(
            StoreRecord(
                run_id=run_id,
                brand_focus="decathlon",
                store_name=store_name,
                store_url="",
                address=address,
                postal_code="",
                city="",
                google_maps_url=google_maps_url,
                discovery_source="decathlon_legacy_google_maps_reviews",
                status="legacy_review_loaded",
            )
        )
        for review in store.get("avis", []):
            reviews.append(
                StoreReviewRecord(
                    run_id=run_id,
                    brand_focus="decathlon",
                    site="google_maps",
                    review_scope="store",
                    entity_level="store",
                    entity_name=store_name,
                    location=address,
                    rating=review.get("note"),
                    date_raw=_clean_text(_repair_mojibake(review.get("date", ""))),
                    author=_clean_text(_repair_mojibake(review.get("auteur", ""))),
                    body=_clean_text(_repair_mojibake(review.get("texte", ""))),
                    aggregate_rating=aggregate_rating,
                    aggregate_count=aggregate_count,
                    source_url=google_maps_url,
                    source_symmetry="common",
                    store_url="",
                    google_maps_url=google_maps_url,
                )
            )
    return stores, reviews


async def _try_text(locator, selector: str) -> str:
    try:
        node = locator.locator(selector).first
        if await node.count() > 0:
            return _clean_text(await node.inner_text())
    except Exception:
        return ""
    return ""


async def _try_attr(locator, selector: str, attr: str) -> str:
    try:
        node = locator.locator(selector).first
        if await node.count() > 0:
            value = await node.get_attribute(attr)
            return _clean_text(value or "")
    except Exception:
        return ""
    return ""


async def handle_consent(page) -> bool:
    try:
        for selector in SEL_CONSENT_BTN:
            button = page.locator(selector).first
            if await button.count() > 0:
                await button.click()
                await page.wait_for_timeout(2500)
                return True
    except Exception:
        pass
    return False


async def get_global_info(page) -> tuple[float | None, int | None]:
    aggregate_rating = None
    aggregate_count = None
    for selector in SEL_GLOBAL_RATING:
        try:
            texts = await page.locator(selector).all_inner_texts()
        except Exception:
            continue
        for text in texts:
            match = re.search(r"(\d+[.,]\d+|\d+)", text)
            if match:
                value = float(match.group(1).replace(",", "."))
                if 1.0 <= value <= 5.0:
                    aggregate_rating = value
                    break
        if aggregate_rating is not None:
            break
    for selector in SEL_NB_AVIS:
        try:
            texts = await page.locator(selector).all_inner_texts()
        except Exception:
            continue
        for text in texts:
            match = re.search(r"([\d\s]+)", text)
            if match:
                digits = re.sub(r"\s", "", match.group(1))
                if digits.isdigit():
                    aggregate_count = int(digits)
                    break
        if aggregate_count is not None:
            break
    return aggregate_rating, aggregate_count


async def click_reviews_tab(page) -> bool:
    for selector in SEL_REVIEWS_TAB:
        try:
            tab = page.locator(selector).first
            if await tab.count() > 0:
                await tab.click()
                await page.wait_for_timeout(2500)
                return True
        except Exception:
            continue
    try:
        tab = page.get_by_role("tab", name=re.compile(r"Avis|Reviews", re.I)).first
        if await tab.count() > 0:
            await tab.click()
            await page.wait_for_timeout(2500)
            return True
    except Exception:
        pass
    return False


async def sort_by_recent(page) -> None:
    try:
        button = page.locator(
            'button[aria-label*="Trier"], button[aria-label*="Sort"], div[jsaction*="pane.review.sort"]'
        ).first
        if await button.count() > 0:
            await button.click()
            await page.wait_for_timeout(1000)
            option = page.get_by_text(re.compile(r"Plus récent|Most recent", re.I)).first
            if await option.count() > 0:
                await option.click()
                await page.wait_for_timeout(2000)
    except Exception:
        pass


async def expand_reviews(page) -> None:
    for selector in SEL_EXPAND_BTN:
        try:
            buttons = page.locator(selector)
            count = await buttons.count()
            for index in range(count):
                try:
                    await buttons.nth(index).click()
                    await page.wait_for_timeout(250)
                except Exception:
                    pass
        except Exception:
            continue


async def collect_review_elements(page, max_reviews_per_store: int) -> list:
    for selector in SEL_REVIEW_ITEM:
        try:
            elements = page.locator(selector)
            count = await elements.count()
            if count > 0:
                return [elements.nth(index) for index in range(min(count, max_reviews_per_store))]
        except Exception:
            continue
    return []


async def parse_review_element(review_el) -> dict | None:
    author = ""
    for selector in SEL_AUTHOR:
        author = await _try_text(review_el, selector)
        if author:
            break
    rating = None
    for selector in SEL_RATING:
        label = await _try_attr(review_el, selector, "aria-label")
        if not label:
            label = await _try_text(review_el, selector)
        rating = _parse_rating_from_label(label)
        if rating is not None:
            break
    date_raw = ""
    for selector in SEL_DATE:
        date_raw = await _try_text(review_el, selector)
        if date_raw:
            break
    body = ""
    for selector in SEL_TEXT:
        body = await _try_text(review_el, selector)
        if body:
            break
    if not any([author, rating is not None, date_raw, body]):
        return None
    return {
        "author": author,
        "rating": rating,
        "date_raw": date_raw,
        "body": body,
    }


async def probe_store_review_signature(page, store: StoreRecord, *, preview_count: int = 5) -> tuple[str, float | None, int | None, str]:
    try:
        await page.goto(store.google_maps_url, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)
        await handle_consent(page)
        aggregate_rating, aggregate_count = await get_global_info(page)
        if not await click_reviews_tab(page):
            return "", aggregate_rating, aggregate_count, "reviews-tab-not-found"
        await sort_by_recent(page)
        await expand_reviews(page)
        elements = await collect_review_elements(page, preview_count)
        payloads: list[dict] = []
        for review_el in elements:
            payload = await parse_review_element(review_el)
            if payload is not None and payload.get("body"):
                payloads.append(payload)
        return _payload_signature_hash(payloads), aggregate_rating, aggregate_count, ""
    except Exception as exc:
        return "", None, None, str(exc)


async def scrape_one_store(page, store: StoreRecord, *, max_reviews_per_store: int) -> tuple[StoreRecord, list[StoreReviewRecord], str]:
    error = ""
    aggregate_rating = None
    aggregate_count = None
    reviews: list[StoreReviewRecord] = []
    store.status = "review_started"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await page.goto(store.google_maps_url, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
            await page.wait_for_timeout(2500)
            await handle_consent(page)
            aggregate_rating, aggregate_count = await get_global_info(page)
            if not await click_reviews_tab(page):
                store.status = "review_missing_tab"
                return store, [], "reviews-tab-not-found"
            await sort_by_recent(page)
            for _ in range(MAX_SCROLLS):
                await expand_reviews(page)
                elements = await collect_review_elements(page, max_reviews_per_store)
                if len(elements) >= max_reviews_per_store:
                    break
                feed = page.locator(SEL_REVIEWS_FEED).first
                if await feed.count() > 0:
                    await feed.evaluate("(node) => { node.scrollTop = node.scrollHeight; }")
                else:
                    await page.mouse.wheel(0, 1400)
                await page.wait_for_timeout(SCROLL_PAUSE_MS)
            await expand_reviews(page)
            elements = await collect_review_elements(page, max_reviews_per_store)
            seen = set()
            for review_el in elements:
                payload = await parse_review_element(review_el)
                if payload is None:
                    continue
                key = (payload["author"], payload["date_raw"], payload["body"])
                if key in seen or not payload["body"]:
                    continue
                seen.add(key)
                reviews.append(
                    StoreReviewRecord(
                        run_id=store.run_id,
                        brand_focus=store.brand_focus,
                        site="google_maps",
                        review_scope="store",
                        entity_level="store",
                        entity_name=store.store_name,
                        location=store.address or store.city,
                        rating=payload["rating"],
                        date_raw=payload["date_raw"],
                        author=payload["author"],
                        body=payload["body"],
                        aggregate_rating=aggregate_rating,
                        aggregate_count=aggregate_count,
                        source_url=store.google_maps_url,
                        source_symmetry=store.source_symmetry,
                        store_url=store.store_url,
                        google_maps_url=store.google_maps_url,
                    )
                )
            store.status = "review_scraped" if reviews else "review_empty"
            return store, reviews, ""
        except Exception as exc:
            error = str(exc)
            if attempt < MAX_RETRIES:
                await asyncio.sleep(PAUSE_BETWEEN_STORES * attempt + random.uniform(1, 3))
            else:
                store.status = "review_error"
                return store, [], error
    store.status = "review_error"
    return store, [], error


async def scrape_google_maps_reviews(
    stores: list[StoreRecord],
    *,
    max_reviews_per_store: int,
    headless: bool,
    debug: bool,
    incremental: bool = False,
    state_store: StateStore | None = None,
    stale_after_days: int = 30,
    checkpoint_every: int = 10,
    checkpoint_callback: Callable[[list[StoreRecord], list[StoreReviewRecord]], Any] | None = None,
) -> tuple[list[StoreRecord], list[StoreReviewRecord], list[str]]:
    from playwright.async_api import async_playwright

    warnings: list[str] = []
    updated_stores: list[StoreRecord] = []
    reviews: list[StoreReviewRecord] = []
    if not stores:
        return updated_stores, reviews, warnings

    async def new_browser(pw):
        user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        ]
        browser = await pw.chromium.launch(
            headless=headless,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--lang=fr-FR",
            ],
        )
        context = await browser.new_context(
            locale="fr-FR",
            timezone_id="Europe/Paris",
            user_agent=random.choice(user_agents),
            viewport={"width": 1280, "height": 900},
        )
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = await context.new_page()
        return browser, page

    async def safe_close(browser) -> None:
        try:
            await browser.close()
        except Exception as exc:
            warnings.append(f"Browser close warning: {exc}")

    async with async_playwright() as pw:
        browser, page = await new_browser(pw)
        scraped = 0
        for store in stores:
            probe_hash = ""
            if incremental and state_store is not None:
                probe_hash, aggregate_rating, aggregate_count, probe_error = await probe_store_review_signature(page, store)
                if probe_error and probe_error != "reviews-tab-not-found":
                    warnings.append(f"{store.brand_focus}:{store.store_name} review probe failed: {probe_error}")
                entity_key = _store_entity_key(store)
                state_store.upsert_entity(
                    monitor_name="store_monitor",
                    source_name=STORE_MONITOR_REVIEWS_SOURCE,
                    entity_key=entity_key,
                    entity_name=store.store_name,
                    entity_url=store.google_maps_url,
                    content_hash=probe_hash,
                    metadata={
                        "aggregate_rating": aggregate_rating,
                        "aggregate_count": aggregate_count,
                    },
                    mark_scraped=False,
                )
                if probe_hash and not state_store.entity_requires_refresh(
                    monitor_name="store_monitor",
                    source_name=STORE_MONITOR_REVIEWS_SOURCE,
                    entity_key=entity_key,
                    content_hash=probe_hash,
                    stale_after_days=stale_after_days,
                ):
                    store.status = "review_unchanged_skipped"
                    updated_stores.append(store)
                    scraped += 1
                    if checkpoint_callback is not None and checkpoint_every > 0 and scraped % checkpoint_every == 0:
                        checkpoint_callback(updated_stores, reviews)
                    await asyncio.sleep(PAUSE_BETWEEN_STORES + random.uniform(0, 2))
                    continue
            store, store_reviews, error = await scrape_one_store(
                page,
                store,
                max_reviews_per_store=max_reviews_per_store,
            )
            updated_stores.append(store)
            reviews.extend(store_reviews)
            scraped += 1
            if incremental and state_store is not None:
                final_hash = probe_hash or _payload_signature_hash(
                    [{"author": row.author, "date_raw": row.date_raw, "body": row.body} for row in store_reviews[:5]]
                )
                state_store.upsert_entity(
                    monitor_name="store_monitor",
                    source_name=STORE_MONITOR_REVIEWS_SOURCE,
                    entity_key=_store_entity_key(store),
                    entity_name=store.store_name,
                    entity_url=store.google_maps_url,
                    content_hash=final_hash,
                    metadata={
                        "store_url": store.store_url,
                        "status": store.status,
                    },
                    mark_scraped=True,
                )
                for row in store_reviews:
                    state_store.record_item(
                        monitor_name="store_monitor",
                        source_name=STORE_MONITOR_REVIEWS_SOURCE,
                        source_partition=row.source_partition,
                        entity_key=_store_entity_key(store),
                        item_key=normalize_hash_input(row.author, row.date_raw, row.body[:80]),
                        content_hash=build_content_hash(row.author, row.date_raw, row.body),
                        published_at=None,
                        metadata={"rating": row.rating},
                    )
            if error:
                warnings.append(f"{store.brand_focus}:{store.store_name} review crawl failed: {error}")
            if checkpoint_callback is not None and checkpoint_every > 0 and scraped % checkpoint_every == 0:
                checkpoint_callback(updated_stores, reviews)
            if scraped % BROWSER_RESTART_EVERY == 0:
                await safe_close(browser)
                await asyncio.sleep(random.uniform(4, 8))
                browser, page = await new_browser(pw)
            await asyncio.sleep(PAUSE_BETWEEN_STORES + random.uniform(0, 3))
        await safe_close(browser)
    if debug and not reviews:
        warnings.append("Google Maps scraping returned zero review rows for the selected store set.")
    return updated_stores, reviews, warnings
