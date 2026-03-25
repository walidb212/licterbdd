"""
Scrape all Intersport France stores via DrissionPage (bypasses DataDome).
Outputs intersport_france.json in the same format as decathlon_france.json.

Usage:
    py -3.10 scrape_intersport_stores.py
    py -3.10 scrape_intersport_stores.py --no-headless   # show browser
"""
from __future__ import annotations

import argparse
import json
import re
import time
import random
from datetime import date
from pathlib import Path

from DrissionPage import ChromiumPage, ChromiumOptions


ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "intersport_france.json"
STORE_FINDER_URL = "https://www.intersport.fr/store-finder/"


def make_browser(headless: bool = True) -> ChromiumPage:
    opts = ChromiumOptions()
    if headless:
        opts.headless()
    opts.set_argument("--no-sandbox")
    opts.set_argument("--disable-blink-features=AutomationControlled")
    opts.set_argument("--lang=fr-FR")
    opts.set_user_agent(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    return ChromiumPage(opts)


def get_department_links(page: ChromiumPage) -> list[dict]:
    """Navigate to store-finder and collect all department links."""
    print(f"[1/3] Loading {STORE_FINDER_URL} ...")
    page.get(STORE_FINDER_URL)
    time.sleep(4)

    # Accept cookies if present
    try:
        consent = page.ele('xpath://button[contains(text(),"Tout accepter") or contains(text(),"Accepter")]', timeout=3)
        if consent:
            consent.click()
            time.sleep(1)
    except Exception:
        pass

    # Collect department links
    links = page.eles('xpath://a[contains(@href,"/departement/")]')
    departments = []
    seen = set()
    for link in links:
        href = link.attr("href") or ""
        text = link.text.strip()
        if "/departement/" not in href:
            continue
        # Normalize to full URL
        if href.startswith("/"):
            href = f"https://www.intersport.fr{href}"
        if href in seen:
            continue
        seen.add(href)
        departments.append({"url": href, "name": text})

    print(f"    Found {len(departments)} departments")
    return departments


def parse_store_from_element(el) -> dict | None:
    """Extract store info from a store card/link element on a department page."""
    # Try to find store name and address from the element or its children
    text = el.text.strip()
    href = el.attr("href") or ""

    if not text or len(text) < 5:
        return None

    # Store name is usually the first line or the link text
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return None

    store_name = lines[0]
    # Sometimes the name has extra info, clean it
    if not any(kw in store_name.lower() for kw in ("intersport", "sport")):
        store_name = f"Intersport {store_name}"

    address = ""
    city = ""
    postal_code = ""

    # Try to extract address from remaining lines
    for line in lines[1:]:
        # Postal code pattern
        match = re.search(r"(\d{5})", line)
        if match and not postal_code:
            postal_code = match.group(1)
            # City is usually after the postal code
            after = line[match.end():].strip().lstrip(",").strip()
            if after:
                city = after
            # Address is before
            before = line[:match.start()].strip().rstrip(",").strip()
            if before and not address:
                address = before
        elif not address and line and not line.startswith("0") and not line.startswith("+"):
            address = line

    return {
        "nom": store_name,
        "adresse": address,
        "code_postal": postal_code,
        "ville": city,
        "adresse_complete": ", ".join(filter(None, [address, postal_code, city])),
        "url_page": href if "/magasin/" in href else "",
    }


def scrape_department(page: ChromiumPage, dept: dict) -> list[dict]:
    """Scrape all stores from one department page."""
    page.get(dept["url"])
    time.sleep(2 + random.uniform(0, 1.5))

    stores = []

    # Strategy 1: look for store links (a[href*="/magasin/"])
    store_links = page.eles('xpath://a[contains(@href,"/magasin/")]')
    seen_hrefs = set()
    for link in store_links:
        href = link.attr("href") or ""
        if href in seen_hrefs:
            continue
        seen_hrefs.add(href)
        text = link.text.strip()
        if not text or len(text) < 3:
            continue

        store = parse_store_from_element(link)
        if store:
            if href.startswith("/"):
                href = f"https://www.intersport.fr{href}"
            store["url_page"] = href
            stores.append(store)

    # Strategy 2: if no /magasin/ links, try store cards or structured data
    if not stores:
        # Try JSON-LD
        scripts = page.eles('xpath://script[@type="application/ld+json"]')
        for script in scripts:
            try:
                data = json.loads(script.text)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if item.get("@type") in ("Store", "LocalBusiness", "SportingGoodsStore"):
                        addr = item.get("address", {})
                        stores.append({
                            "nom": item.get("name", ""),
                            "adresse": addr.get("streetAddress", ""),
                            "code_postal": addr.get("postalCode", ""),
                            "ville": addr.get("addressLocality", ""),
                            "adresse_complete": ", ".join(filter(None, [
                                addr.get("streetAddress", ""),
                                addr.get("postalCode", ""),
                                addr.get("addressLocality", ""),
                            ])),
                            "url_page": item.get("url", ""),
                        })
            except (json.JSONDecodeError, TypeError):
                continue

    # Strategy 3: parse visible store blocks from page text
    if not stores:
        body_text = page.html
        # Look for patterns like store name + address blocks
        store_blocks = re.findall(
            r'class="[^"]*store[^"]*"[^>]*>.*?</(?:div|article|section)>',
            body_text, re.DOTALL | re.IGNORECASE
        )
        # This is a fallback — we'll parse what we can
        for block in store_blocks[:50]:
            from bs4 import BeautifulSoup
            mini_soup = BeautifulSoup(block, "html.parser")
            text = mini_soup.get_text("\n", strip=True)
            if "intersport" in text.lower():
                lines = [l for l in text.split("\n") if l.strip()]
                if lines:
                    store = {
                        "nom": lines[0],
                        "adresse": lines[1] if len(lines) > 1 else "",
                        "code_postal": "",
                        "ville": "",
                        "adresse_complete": " ".join(lines[1:3]),
                        "url_page": "",
                    }
                    match = re.search(r"(\d{5})", store["adresse_complete"])
                    if match:
                        store["code_postal"] = match.group(1)
                    stores.append(store)

    return stores


def add_google_maps_url(store: dict) -> dict:
    """Generate a Google Maps search URL for the store."""
    query = f"{store['nom']} {store['adresse_complete']}".strip()
    if not query:
        query = store["nom"]
    from urllib.parse import quote
    store["google_maps"] = f"https://www.google.com/maps/search/?api=1&query={quote(query)}"
    return store


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-headless", action="store_true")
    args = parser.parse_args()

    page = make_browser(headless=not args.no_headless)

    try:
        # Step 1: Get all departments
        departments = get_department_links(page)
        if not departments:
            print("ERROR: No departments found. DataDome may have blocked. Try --no-headless")
            return

        # Step 2: Scrape each department
        all_stores = []
        seen_names = set()
        for i, dept in enumerate(departments):
            print(f"[2/3] ({i+1}/{len(departments)}) {dept['name']} — {dept['url']}")
            try:
                dept_stores = scrape_department(page, dept)
                for store in dept_stores:
                    key = (store["nom"].lower().strip(), store.get("code_postal", ""))
                    if key not in seen_names:
                        seen_names.add(key)
                        store = add_google_maps_url(store)
                        all_stores.append(store)
                print(f"    -> {len(dept_stores)} stores ({len(all_stores)} total unique)")
            except Exception as exc:
                print(f"    ERROR: {exc}")

            # Anti-detection pause
            if i < len(departments) - 1:
                time.sleep(random.uniform(1.5, 3.5))

        # Step 3: Save
        output = {
            "source": "Intersport France — store-finder/departement",
            "date_scraping": str(date.today()),
            "total_magasins": len(all_stores),
            "magasins": sorted(all_stores, key=lambda s: (s.get("code_postal", ""), s.get("nom", ""))),
        }
        OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[3/3] Done! {len(all_stores)} stores saved to {OUTPUT_PATH}")

    finally:
        try:
            page.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
