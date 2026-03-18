from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Iterable

from bs4 import BeautifulSoup

from monitor_core.cloudflare import fetch_cloudflare_content, resolve_cloudflare_credentials

from .models import StoreRecord


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
)

ROOT_DIR = Path(__file__).resolve().parent.parent
DECATHLON_CANONICAL_PATH = ROOT_DIR / "decathlon_france.json"
DECATHLON_LEGACY_PATH = ROOT_DIR / "decatlhon_france.json"
INTERSPORT_CANONICAL_PATH = ROOT_DIR / "intersport_france.json"

DECATHLON_BASE_URL = "https://www.decathlon.fr"
DECATHLON_LOCATOR_URL = f"{DECATHLON_BASE_URL}/store-locator"
INTERSPORT_STORE_LOCATOR_URL = "https://www.intersport.fr/nos-magasins/"
DEFAULT_INTERSPORT_CITY_SEEDS = (
    "Paris",
    "Lyon",
    "Marseille",
    "Lille",
    "Toulouse",
    "Bordeaux",
    "Nantes",
    "Nice",
    "Strasbourg",
    "Rennes",
    "Montpellier",
)


def _fetch_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", "replace")


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


def _normalise_google_maps_url(store_name: str, address: str, existing_url: str = "") -> str:
    if existing_url:
        return existing_url
    query = urllib.parse.quote(_clean_text(f"{store_name} {address}"))
    return f"https://www.google.com/maps/search/?api=1&query={query}"


def _store_from_payload(run_id: str, brand_focus: str, payload: dict, discovery_source: str) -> StoreRecord:
    store_name = _repair_mojibake(payload.get("nom") or payload.get("store_name") or "")
    address = _repair_mojibake(payload.get("adresse_complete") or payload.get("address") or payload.get("adresse") or "")
    postal_code = _repair_mojibake(payload.get("code_postal") or payload.get("postal_code") or "")
    city = _repair_mojibake(payload.get("ville") or payload.get("city") or "")
    store_url = payload.get("url_page") or payload.get("store_url") or ""
    google_maps_url = _normalise_google_maps_url(store_name, address, payload.get("google_maps") or payload.get("google_maps_url") or "")
    return StoreRecord(
        run_id=run_id,
        brand_focus=brand_focus,
        store_name=_clean_text(store_name),
        store_url=_clean_text(store_url),
        address=_clean_text(address),
        postal_code=_clean_text(postal_code),
        city=_clean_text(city),
        google_maps_url=_clean_text(google_maps_url),
        discovery_source=discovery_source,
        status="discovered",
    )


def _store_from_google_maps_candidate(run_id: str, label: str, href: str) -> StoreRecord | None:
    store_name = _clean_text(_repair_mojibake(label))
    google_maps_url = _clean_text(urllib.parse.urljoin("https://www.google.com", href))
    if not store_name or "intersport" not in store_name.lower():
        return None
    if not google_maps_url:
        return None
    return StoreRecord(
        run_id=run_id,
        brand_focus="intersport",
        store_name=store_name,
        store_url="",
        address="",
        postal_code="",
        city="",
        google_maps_url=google_maps_url,
        discovery_source="intersport_google_maps_search",
        status="discovered",
    )


def _looks_like_pagesjaunes_challenge(html: str) -> bool:
    lowered = (html or "").lower()
    return "challenge-platform" in lowered or "captcha" in lowered or "trouvez plus que des coordonnées" in lowered


def build_intersport_google_maps_queries(city_seeds: list[str] | tuple[str, ...] | None = None) -> tuple[str, ...]:
    seeds = list(city_seeds or DEFAULT_INTERSPORT_CITY_SEEDS)
    queries = ["Intersport France"]
    queries.extend(f"Intersport {city} France" for city in seeds)
    return tuple(dict.fromkeys(queries))


def _load_json_payload(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_legacy_decathlon_inventory(run_id: str) -> tuple[list[StoreRecord], list[str]]:
    warnings: list[str] = []
    if DECATHLON_CANONICAL_PATH.exists():
        payload = _load_json_payload(DECATHLON_CANONICAL_PATH)
        stores = [_store_from_payload(run_id, "decathlon", row, "decathlon_inventory_json") for row in payload.get("magasins", [])]
        return stores, warnings
    if DECATHLON_LEGACY_PATH.exists():
        payload = _load_json_payload(DECATHLON_LEGACY_PATH)
        warnings.append("Using legacy inventory file 'decatlhon_france.json'; canonical file 'decathlon_france.json' not found.")
        stores = [_store_from_payload(run_id, "decathlon", row, "decathlon_inventory_legacy_json") for row in payload.get("magasins", [])]
        return stores, warnings
    return [], warnings


def discover_decathlon_inventory_http(run_id: str) -> list[StoreRecord]:
    html = _fetch_text(DECATHLON_LOCATOR_URL)
    soup = BeautifulSoup(html, "html.parser")
    links = sorted({anchor["href"] for anchor in soup.select("a[href^='/store-view/']") if anchor.get("href")})
    stores: list[StoreRecord] = []
    for path in links:
        store_url = f"{DECATHLON_BASE_URL}{path}"
        store_html = _fetch_text(store_url)
        store = parse_decathlon_store_page(run_id, store_html, path)
        if store is not None:
            stores.append(store)
    return stores


def parse_decathlon_store_page(run_id: str, html: str, path: str) -> StoreRecord | None:
    soup = BeautifulSoup(html, "html.parser")
    name_el = soup.select_one(".store-view-side-panel__body-store-title")
    if name_el is not None:
        for button in name_el.select("button"):
            button.decompose()
        store_name = _clean_text(_repair_mojibake(name_el.get_text(" ", strip=True)))
    else:
        store_name = path.rsplit("/", 1)[-1]
    if "decathlon" not in store_name.lower():
        store_name = f"Decathlon {store_name}"

    details_block = soup.select_one(".store-view-side-panel__body-details-block")
    if details_block is None:
        return None
    address_span = details_block.select_one("span.vp-body-s")
    if address_span is None:
        return None
    raw_address = _clean_text(_repair_mojibake(address_span.get_text(" ", strip=True)))
    parts = [part.strip() for part in raw_address.split(",") if part.strip()]
    street = parts[0] if len(parts) > 0 else ""
    postal_code = re.sub(r"\s+", "", parts[1]) if len(parts) > 1 else ""
    city = parts[2] if len(parts) > 2 else ""
    full_address = ", ".join(filter(None, [street, postal_code, city]))
    maps_el = details_block.select_one("a[href*='google.com/maps']")
    google_maps_url = maps_el.get("href", "") if maps_el is not None else ""
    return StoreRecord(
        run_id=run_id,
        brand_focus="decathlon",
        store_name=store_name,
        store_url=f"{DECATHLON_BASE_URL}{path}",
        address=full_address,
        postal_code=postal_code,
        city=_clean_text(_repair_mojibake(city)),
        google_maps_url=_normalise_google_maps_url(store_name, full_address, google_maps_url),
        discovery_source="decathlon_store_locator_http",
        status="discovered",
    )


def load_manual_inventory(run_id: str, brand_focus: str) -> tuple[list[StoreRecord], list[str]]:
    if brand_focus == "intersport" and INTERSPORT_CANONICAL_PATH.exists():
        payload = _load_json_payload(INTERSPORT_CANONICAL_PATH)
        stores = [_store_from_payload(run_id, "intersport", row, "manual_inventory_json") for row in payload.get("magasins", [])]
        return stores, []
    return [], []


async def discover_intersport_inventory_browser(
    run_id: str,
    *,
    headless: bool,
    debug: bool,
    city_seeds: list[str] | None = None,
) -> tuple[list[StoreRecord], list[str]]:
    from playwright.async_api import async_playwright

    warnings: list[str] = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        page = await browser.new_page(locale="fr-FR")
        response = await page.goto(INTERSPORT_STORE_LOCATOR_URL, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)
        content = await page.content()
        try:
            await browser.close()
        except Exception as exc:
            warnings.append(f"Intersport discovery browser close warning: {exc}")

    if response is not None and response.status >= 400:
        warnings.append(f"Intersport official store locator returned HTTP {response.status}.")
    if "captcha-delivery.com" in content.lower() or "datadome" in content.lower():
        warnings.append("Intersport official store locator is protected by DataDome; falling back to Google Maps discovery.")
        google_maps_stores, google_maps_warnings = await discover_intersport_inventory_google_maps(
            run_id,
            headless=headless,
            city_seeds=city_seeds,
        )
        warnings.extend(google_maps_warnings)
        return google_maps_stores, warnings

    soup = BeautifulSoup(content, "html.parser")
    candidate_urls = []
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "")
        if "INTERSPORT-" not in href:
            continue
        candidate_urls.append(urllib.parse.urljoin(INTERSPORT_STORE_LOCATOR_URL, href))
    candidate_urls = list(dict.fromkeys(candidate_urls))
    if not candidate_urls:
        warnings.append("No Intersport store URLs were found on the official store locator page; falling back to Google Maps discovery.")
        google_maps_stores, google_maps_warnings = await discover_intersport_inventory_google_maps(
            run_id,
            headless=headless,
            city_seeds=city_seeds,
        )
        warnings.extend(google_maps_warnings)
        return google_maps_stores, warnings

    stores = [
        StoreRecord(
            run_id=run_id,
            brand_focus="intersport",
            store_name=_clean_text(url.rstrip("/").rsplit("/", 2)[-2].replace("-", " ")),
            store_url=url,
            address="",
            postal_code="",
            city="",
            google_maps_url=_normalise_google_maps_url("Intersport", url),
            discovery_source="intersport_store_locator_browser",
            status="discovered",
        )
        for url in candidate_urls
    ]
    if debug:
        warnings.append(f"Intersport browser discovery extracted {len(stores)} raw store URLs without detailed address parsing.")
    return stores, warnings


async def _accept_google_maps_consent(page) -> None:
    selectors = (
        'button[aria-label*="Tout accepter"]',
        'button[aria-label*="Accept all"]',
        'button[aria-label*="Accepter tout"]',
        'form[action*="consent"] button',
        "#L2AGLb",
    )
    for selector in selectors:
        try:
            button = page.locator(selector).first
            if await button.count() > 0:
                await button.click()
                await page.wait_for_timeout(2500)
                return
        except Exception:
            continue


async def _collect_google_maps_candidates(page, run_id: str) -> list[StoreRecord]:
    records: list[StoreRecord] = []
    anchors = page.locator("a.hfpxzc, a[href*='/maps/place/']")
    count = min(await anchors.count(), 80)
    for index in range(count):
        anchor = anchors.nth(index)
        try:
            href = await anchor.get_attribute("href") or ""
            label = await anchor.get_attribute("aria-label") or ""
        except Exception:
            continue
        record = _store_from_google_maps_candidate(run_id, label, href)
        if record is not None:
            records.append(record)
    return records


async def discover_intersport_inventory_google_maps(
    run_id: str,
    *,
    headless: bool,
    city_seeds: list[str] | None = None,
) -> tuple[list[StoreRecord], list[str]]:
    from playwright.async_api import async_playwright

    warnings: list[str] = []
    records_by_url: dict[str, StoreRecord] = {}

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        page = await browser.new_page(locale="fr-FR")
        consent_handled = False
        for query in build_intersport_google_maps_queries(city_seeds):
            search_url = f"https://www.google.com/maps/search/{urllib.parse.quote(query)}"
            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(2500)
                if not consent_handled:
                    await _accept_google_maps_consent(page)
                    consent_handled = True
                feed = page.locator("div[role='feed']").first
                if await feed.count() > 0:
                    for _ in range(5):
                        await feed.evaluate("(node) => { node.scrollTop = node.scrollHeight; }")
                        await page.wait_for_timeout(1200)
                for record in await _collect_google_maps_candidates(page, run_id):
                    records_by_url.setdefault(record.google_maps_url, record)
            except Exception as exc:
                warnings.append(f"Google Maps discovery failed for query '{query}': {exc}")
        try:
            await browser.close()
        except Exception as exc:
            warnings.append(f"Google Maps discovery browser close warning: {exc}")

    records = sorted(records_by_url.values(), key=lambda row: row.store_name)
    if not records:
        warnings.append("Google Maps fallback did not return any Intersport store candidates.")
    else:
        warnings.append(f"Google Maps fallback discovered {len(records)} Intersport store candidates.")
    return records, warnings


def enrich_missing_store_metadata_pagesjaunes(stores: list[StoreRecord]) -> tuple[list[StoreRecord], list[str]]:
    token, account_id = resolve_cloudflare_credentials()
    warnings: list[str] = []
    if not token or not account_id:
        warnings.append("PagesJaunes metadata enrichment skipped: Cloudflare credentials missing.")
        return stores, warnings

    enriched: list[StoreRecord] = []
    for store in stores:
        if store.address and store.postal_code and store.city:
            enriched.append(store)
            continue
        query = store.store_name
        if store.city:
            query = f"{query} {store.city}"
        search_url = "https://www.pagesjaunes.fr/recherche?quoiqui=" + urllib.parse.quote(query)
        try:
            html = fetch_cloudflare_content(search_url, token=token, account_id=account_id)
            if _looks_like_pagesjaunes_challenge(html):
                warnings.append(f"PagesJaunes challenge for {store.store_name}; metadata not enriched.")
                enriched.append(store)
                continue
            soup = BeautifulSoup(html or "", "html.parser")
            href = ""
            address = ""
            postal_code = ""
            city = ""
            for anchor in soup.select("a[href*='/pros/']"):
                href = urllib.parse.urljoin("https://www.pagesjaunes.fr", anchor.get("href") or "")
                if href:
                    break
            address = _clean_text(
                " ".join(
                    node.get_text(" ", strip=True)
                    for node in soup.select("[itemprop='streetAddress'], [itemprop='postalCode'], [itemprop='addressLocality']")
                )
            )
            postal_match = re.search(r"\b(\d{5})\b", address)
            if postal_match:
                postal_code = postal_match.group(1)
                city = _clean_text(address[postal_match.end() :])
            if href and not store.store_url:
                store.store_url = href
            if address and not store.address:
                store.address = address
            if postal_code and not store.postal_code:
                store.postal_code = postal_code
            if city and not store.city:
                store.city = city
        except Exception as exc:
            warnings.append(f"PagesJaunes enrichment failed for {store.store_name}: {exc}")
        enriched.append(store)
    return enriched, warnings


def merge_store_lists(*groups: Iterable[StoreRecord]) -> list[StoreRecord]:
    by_key: dict[tuple[str, str], StoreRecord] = {}
    for group in groups:
        for store in group:
            key = (store.brand_focus, store.store_name)
            existing = by_key.get(key)
            if existing is None:
                by_key[key] = store
                continue
            if not existing.address and store.address:
                existing.address = store.address
            if not existing.postal_code and store.postal_code:
                existing.postal_code = store.postal_code
            if not existing.city and store.city:
                existing.city = store.city
            if not existing.store_url and store.store_url:
                existing.store_url = store.store_url
            if not existing.google_maps_url and store.google_maps_url:
                existing.google_maps_url = store.google_maps_url
            if existing.status == "discovered" and store.status != "discovered":
                existing.status = store.status
    return sorted(by_key.values(), key=lambda row: (row.brand_focus, row.postal_code, row.city, row.store_name))
