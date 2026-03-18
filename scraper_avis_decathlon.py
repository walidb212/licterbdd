"""
Scraper des avis Google Maps â€“ Magasins Decathlon France
=========================================================
Ce script est le DEUXIÃˆME script du projet. Il lit le fichier
decathlon_france.json produit par scraper_decathlon.py, puis pour
chaque magasin va chercher ses avis sur Google Maps.

DonnÃ©es extraites par magasin :
  - nom            : nom du magasin
  - adresse        : adresse complÃ¨te
  - google_maps    : URL Google Maps source
  - note_globale   : note moyenne (ex : 4.2)
  - nb_avis_total  : nombre total d'avis indiquÃ© par Google
  - avis           : liste des avis individuels contenant :
        * auteur   : nom du rÃ©dacteur
        * note     : nombre d'Ã©toiles (1-5)
        * date     : date telle qu'affichÃ©e ("il y a 3 mois", etc.)
        * texte    : contenu de l'avis

PrÃ©requis :
    pip install playwright
    playwright install chromium

Usage :
    python3 scraper_avis_decathlon.py
    python3 scraper_avis_decathlon.py --limit 10        # tester sur 10 magasins
    python3 scraper_avis_decathlon.py --max-avis 20     # 20 avis max par magasin
    python3 scraper_avis_decathlon.py --resume          # reprendre oÃ¹ on s'est arrÃªtÃ©
"""

import argparse
import asyncio
import json
import random
import re
import sys
from datetime import date
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

# â”€â”€â”€ Configuration â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

INPUT_FILE   = "decathlon_france.json"
OUTPUT_FILE  = "decathlon_avis.json"

DEFAULT_MAX_AVIS    = 40     # avis rÃ©cupÃ©rÃ©s par magasin
SCROLL_PAUSE_MS     = 1800   # pause entre chaque scroll (ms)
MAX_SCROLLS         = 15     # scrolls max pour charger les avis
NAV_TIMEOUT_MS      = 60_000 # timeout navigation (60s au lieu de 30s)
PAUSE_ENTRE_STORES  = 5.0    # pause (s) entre deux magasins (anti-throttle)
MAX_RETRIES         = 3      # nombre de tentatives par magasin
BROWSER_RESTART_EVERY = 25   # redÃ©marrer le navigateur tous les N magasins

# SÃ©lecteurs CSS Google Maps (plusieurs fallbacks pour chaque Ã©lÃ©ment)
SEL_REVIEWS_TAB   = [
    'button[aria-label*="Avis"]',
    'button[aria-label*="Reviews"]',
    'div[role="tab"][aria-label*="Avis"]',
]
SEL_REVIEWS_FEED  = 'div[role="feed"]'
SEL_REVIEW_ITEM   = [
    'div.jftiEf',
    'div[data-review-id]',
    'div[jsaction*="pane.review"]',
]
SEL_AUTHOR        = ['.d4r55', '.kvMYJc', 'button[aria-label*="Photo de profil"]']
SEL_RATING        = ['span[aria-label*="Ã©toile"]', 'span[aria-label*="star"]']
SEL_DATE          = ['.rsqaWe', '.xRkPPb', 'span[class*="date"]']
SEL_TEXT          = ['.wiI7pd', '.MyEned', 'span[class*="text"]']
SEL_EXPAND_BTN    = [
    'button[jsaction*="pane.review.expandReview"]',
    'button[aria-label*="Voir plus"]',
    'button[aria-label*="See more"]',
]
SEL_GLOBAL_RATING = ['div.F7nice span', 'span.ceNzKf', 'div[aria-label*="Ã©toile"] span']
SEL_NB_AVIS       = ['span.F7nice + span', 'button[jsaction*="pane.rating.moreReviews"] span']
SEL_CONSENT_BTN   = [
    'button[aria-label*="Tout accepter"]',
    'button[aria-label*="Accept all"]',
    'button[aria-label*="Accepter tout"]',
    'form[action*="consent"] button',
    '#L2AGLb',   # id classique de Google Consent
]

# â”€â”€â”€ Utilitaires â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def first_text(el_list):
    """Retourne le premier texte non-vide d'une liste de rÃ©sultats locator."""
    return el_list[0] if el_list else ""


def parse_rating_from_label(label: str) -> float | None:
    """Extrait la note depuis un aria-label comme 'Note de 4 Ã©toiles sur 5'."""
    if not label:
        return None
    # "4 Ã©toiles", "4.5 Ã©toiles", "Note de 4 Ã©toiles sur 5"
    m = re.search(r"(\d+[.,]?\d*)\s*(Ã©toile|star)", label, re.I)
    if m:
        return float(m.group(1).replace(",", "."))
    # Parfois juste un chiffre au dÃ©but
    m = re.search(r"^(\d+[.,]?\d*)", label.strip())
    if m:
        return float(m.group(1).replace(",", "."))
    return None


async def try_locators(page_or_elem, selectors: list[str], attr: str = "inner_text"):
    """
    Essaie chaque sÃ©lecteur CSS dans l'ordre et retourne la valeur de
    inner_text() (par dÃ©faut) ou get_attribute(attr) dÃ¨s qu'un Ã©lÃ©ment
    est trouvÃ©.
    """
    for sel in selectors:
        try:
            loc = page_or_elem.locator(sel).first
            if await loc.count() > 0:
                if attr == "inner_text":
                    return (await loc.inner_text()).strip()
                else:
                    val = await loc.get_attribute(attr)
                    return val.strip() if val else ""
        except Exception:
            continue
    return ""


# â”€â”€â”€ Ã‰tape 0 : consentement Google â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def handle_consent(page):
    """Accepte la page de consentement Google si elle apparaÃ®t."""
    try:
        for sel in SEL_CONSENT_BTN:
            btn = page.locator(sel).first
            if await btn.count() > 0:
                await btn.click()
                await page.wait_for_timeout(2500)
                return True
    except Exception:
        pass
    return False


# â”€â”€â”€ Ã‰tape 1 : note globale et nombre d'avis â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def get_global_info(page) -> tuple[float | None, int | None]:
    """RÃ©cupÃ¨re la note globale et le nombre total d'avis affichÃ©s."""
    # Note globale
    note_globale = None
    for sel in SEL_GLOBAL_RATING:
        try:
            texts = await page.locator(sel).all_inner_texts()
            for t in texts:
                m = re.search(r"(\d+[.,]\d+|\d+)", t)
                if m:
                    val = float(m.group(1).replace(",", "."))
                    if 1.0 <= val <= 5.0:
                        note_globale = val
                        break
            if note_globale:
                break
        except Exception:
            continue

    # Nombre total d'avis
    nb_avis = None
    for sel in SEL_NB_AVIS:
        try:
            texts = await page.locator(sel).all_inner_texts()
            for t in texts:
                m = re.search(r"([\d\s]+)", t)
                if m:
                    nb_str = re.sub(r"\s", "", m.group(1))
                    if nb_str.isdigit():
                        nb_avis = int(nb_str)
                        break
            if nb_avis:
                break
        except Exception:
            continue

    return note_globale, nb_avis


# â”€â”€â”€ Ã‰tape 2 : aller sur l'onglet Avis â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def click_reviews_tab(page) -> bool:
    """Clique sur l'onglet Avis et attend le chargement du panneau."""
    for sel in SEL_REVIEWS_TAB:
        try:
            tab = page.locator(sel).first
            if await tab.count() > 0:
                await tab.click()
                await page.wait_for_timeout(2500)
                return True
        except Exception:
            continue

    # Fallback : chercher par texte visible
    try:
        tab = page.get_by_role("tab", name=re.compile(r"Avis", re.I)).first
        if await tab.count() > 0:
            await tab.click()
            await page.wait_for_timeout(2500)
            return True
    except Exception:
        pass

    return False


# â”€â”€â”€ Ã‰tape 3 : trier par "Plus rÃ©cents" â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def sort_by_recent(page):
    """Tente de trier les avis par date (plus rÃ©cents en premier)."""
    try:
        # Chercher le menu de tri
        sort_btn = page.locator(
            'button[aria-label*="Trier"], button[aria-label*="Sort"], '
            'div[jsaction*="pane.review.sort"]'
        ).first
        if await sort_btn.count() > 0:
            await sort_btn.click()
            await page.wait_for_timeout(1000)
            # Cliquer sur "Plus rÃ©cents"
            recent = page.get_by_text(re.compile(r"Plus rÃ©cent|Most recent", re.I)).first
            if await recent.count() > 0:
                await recent.click()
                await page.wait_for_timeout(2000)
    except Exception:
        pass


# â”€â”€â”€ Ã‰tape 4 : dÃ©rouler les avis tronquÃ©s â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def expand_reviews(page):
    """Clique sur tous les boutons 'Voir plus' visibles pour afficher le texte complet."""
    for sel in SEL_EXPAND_BTN:
        try:
            btns = page.locator(sel)
            count = await btns.count()
            for i in range(count):
                try:
                    await btns.nth(i).click()
                    await page.wait_for_timeout(300)
                except Exception:
                    pass
        except Exception:
            continue


# â”€â”€â”€ Ã‰tape 5 : extraire un avis individuel â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def parse_one_review(review_el) -> dict | None:
    """Extrait les donnÃ©es d'un Ã©lÃ©ment avis."""
    # Auteur
    auteur = ""
    for sel in SEL_AUTHOR:
        try:
            el = review_el.locator(sel).first
            if await el.count() > 0:
                # Pour les boutons "Photo de profil", le nom est dans aria-label
                aria = await el.get_attribute("aria-label")
                if aria and "Photo" not in aria:
                    auteur = aria.strip()
                else:
                    auteur = (await el.inner_text()).strip()
                if auteur:
                    break
        except Exception:
            continue

    # Note
    note = None
    for sel in SEL_RATING:
        try:
            el = review_el.locator(sel).first
            if await el.count() > 0:
                label = await el.get_attribute("aria-label") or ""
                note = parse_rating_from_label(label)
                if note is not None:
                    break
        except Exception:
            continue

    # Date
    date_avis = ""
    for sel in SEL_DATE:
        try:
            el = review_el.locator(sel).first
            if await el.count() > 0:
                date_avis = (await el.inner_text()).strip()
                if date_avis:
                    break
        except Exception:
            continue

    # Texte
    texte = ""
    for sel in SEL_TEXT:
        try:
            el = review_el.locator(sel).first
            if await el.count() > 0:
                texte = (await el.inner_text()).strip()
                if texte:
                    break
        except Exception:
            continue

    # Ignorer les avis sans note ni texte
    if note is None and not texte:
        return None

    return {
        "auteur": auteur,
        "note":   note,
        "date":   date_avis,
        "texte":  texte,
    }


# â”€â”€â”€ Ã‰tape 6 : scroll + collecte de tous les avis â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def collect_reviews(page, max_avis: int) -> list[dict]:
    """Scroll dans le panneau des avis et collecte jusqu'Ã  max_avis avis."""
    reviews    = []
    seen_texts = set()

    feed = page.locator(SEL_REVIEWS_FEED).first

    for scroll_num in range(MAX_SCROLLS):
        # DÃ©rouler les "Voir plus" avant d'extraire
        await expand_reviews(page)

        # Chercher les Ã©lÃ©ments d'avis avec les diffÃ©rents sÃ©lecteurs
        for item_sel in SEL_REVIEW_ITEM:
            items = page.locator(item_sel)
            count = await items.count()
            if count == 0:
                continue

            for i in range(count):
                if len(reviews) >= max_avis:
                    return reviews
                try:
                    rv = await parse_one_review(items.nth(i))
                    if rv is None:
                        continue
                    # DÃ©doublonnage simple basÃ© sur texte + auteur
                    key = (rv["auteur"], rv["texte"][:80])
                    if key not in seen_texts:
                        seen_texts.add(key)
                        reviews.append(rv)
                except Exception:
                    continue
            break  # On a trouvÃ© des Ã©lÃ©ments, on ne teste pas les autres sÃ©lecteurs

        if len(reviews) >= max_avis:
            break

        # Scroll vers le bas dans le panneau des avis
        try:
            if await feed.count() > 0:
                await feed.evaluate("el => el.scrollBy(0, 2000)")
            else:
                await page.keyboard.press("End")
        except Exception:
            try:
                await page.evaluate("window.scrollBy(0, 2000)")
            except Exception:
                break

        await page.wait_for_timeout(SCROLL_PAUSE_MS)

    return reviews


# â”€â”€â”€ Scraping d'un magasin (avec retries) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def scrape_one_store(page, store: dict, max_avis: int) -> dict:
    """Scrape les avis d'un magasin avec retry automatique en cas de timeout."""
    result = {
        "nom":           store["nom"],
        "adresse":       store.get("adresse_complete", ""),
        "google_maps":   store.get("google_maps", ""),
        "date_scraping": date.today().isoformat(),
        "note_globale":  None,
        "nb_avis_total": None,
        "avis":          [],
        "erreur":        None,
    }

    url = store.get("google_maps", "")
    if not url:
        result["erreur"] = "URL Google Maps manquante"
        return result

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await page.goto(url, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000 + random.randint(0, 2000))

            # Consentement cookies Google
            await handle_consent(page)
            await page.wait_for_timeout(1000)

            # Si l'URL Ã©tait une recherche, cliquer sur le premier rÃ©sultat.
            if "maps/search" in page.url or "query=" in page.url:
                try:
                    first_result = page.locator('a[href*="/maps/place/"]').first
                    if await first_result.count() > 0:
                        await first_result.click()
                        await page.wait_for_timeout(3000)
                except Exception:
                    pass

            # Note globale et nb avis
            result["note_globale"], result["nb_avis_total"] = await get_global_info(page)

            # Cliquer sur l'onglet "Avis"
            await click_reviews_tab(page)

            # Trier par plus rÃ©cents
            await sort_by_recent(page)

            # Collecter les avis
            result["avis"] = await collect_reviews(page, max_avis)

            # SuccÃ¨s â†’ pas d'erreur
            result["erreur"] = None
            break

        except PWTimeout:
            wait_time = PAUSE_ENTRE_STORES * (2 ** attempt) + random.uniform(1, 5)
            if attempt < MAX_RETRIES:
                print(f"(timeout, retry {attempt}/{MAX_RETRIES}, pause {wait_time:.0f}s) ", end="", flush=True)
                await asyncio.sleep(wait_time)
            else:
                result["erreur"] = f"Timeout aprÃ¨s {MAX_RETRIES} tentatives"
        except Exception as exc:
            wait_time = PAUSE_ENTRE_STORES * attempt + random.uniform(1, 3)
            if attempt < MAX_RETRIES:
                print(f"(erreur, retry {attempt}/{MAX_RETRIES}) ", end="", flush=True)
                await asyncio.sleep(wait_time)
            else:
                result["erreur"] = str(exc)

    return result


# â”€â”€â”€ Sauvegarde JSON â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def save_json(results: list[dict], path: str = OUTPUT_FILE) -> None:
    output = {
        "source":        "Google Maps â€“ Avis Decathlon France",
        "date_scraping": date.today().isoformat(),
        "total_magasins": len(results),
        "magasins":      results,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


# â”€â”€â”€ Chargement des donnÃ©es existantes (reprise) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def load_existing_results(path: str) -> tuple[dict[str, dict], set[str]]:
    """
    Charge les rÃ©sultats dÃ©jÃ  scrappÃ©s.
    Retourne :
      - ok   : dict[nom] â†’ data pour les magasins rÃ©ussis (Ã  conserver)
      - retry: set de noms de magasins en erreur (Ã  retenter)
    """
    if not Path(path).exists():
        return {}, set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        ok    = {}
        retry = set()
        for m in data.get("magasins", []):
            if m.get("erreur") or (not m.get("avis") and m.get("note_globale") is None):
                retry.add(m["nom"])     # erreur â†’ on retente
            else:
                ok[m["nom"]] = m        # OK â†’ on garde
        return ok, retry
    except Exception:
        return {}, set()


# â”€â”€â”€ Boucle principale â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def main(args):
    # 1. Charger la liste des magasins
    if not Path(INPUT_FILE).exists():
        print(f"Fichier introuvable : {INPUT_FILE}")
        print("Lancez d'abord scraper_decathlon.py pour le gÃ©nÃ©rer.")
        sys.exit(1)

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    stores = data.get("magasins", [])
    if args.limit:
        stores = stores[: args.limit]

    total = len(stores)
    print("=" * 60)
    print("  Scraper Avis Google Maps â€“ Decathlon France")
    print("=" * 60)
    print(f"  Magasins Ã  traiter  : {total}")
    print(f"  Avis max par magasin: {args.max_avis}")
    print(f"  Fichier de sortie   : {OUTPUT_FILE}")
    print("=" * 60)

    # Reprise Ã©ventuelle
    existing = {}
    retry_set = set()
    if args.resume:
        existing, retry_set = load_existing_results(OUTPUT_FILE)
        print(f"  Reprise : {len(existing)} OK (conservÃ©s), {len(retry_set)} en erreur (Ã  retenter).")

    results: list[dict] = list(existing.values()) if args.resume else []

    # â”€â”€â”€ Fonction pour crÃ©er un navigateur frais â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    async def new_browser(pw):
        user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        ]
        browser = await pw.chromium.launch(
            headless=True,
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

    async with async_playwright() as pw:
        browser, page = await new_browser(pw)
        scraped = 0

        for idx, store in enumerate(stores, start=1):
            nom = store["nom"]

            # Passer si dÃ©jÃ  traitÃ© avec succÃ¨s (mode reprise)
            if args.resume and nom in existing:
                print(f"[{idx}/{total}] SKIP (dÃ©jÃ  OK) : {nom}")
                continue

            # Signaler si c'est un retry
            is_retry = nom in retry_set
            prefix = "RETRY" if is_retry else "â†’"
            print(f"[{idx}/{total}] {prefix} {nom}", end=" ", flush=True)

            store_data = await scrape_one_store(page, store, args.max_avis)
            results.append(store_data)
            scraped += 1

            nb = len(store_data["avis"])
            note = store_data["note_globale"]
            err  = store_data["erreur"]

            if err:
                print(f"| ERREUR : {err}")
            else:
                print(f"| {nb} avis  |  note globale : {note}")

            # Sauvegarde intermÃ©diaire toutes les 10 magasins
            if scraped % 10 == 0:
                save_json(results)
                print(f"  [sauvegarde intermÃ©diaire â€“ {len(results)} magasins]")

            # RedÃ©marrer le navigateur tous les N magasins (anti-dÃ©tection)
            if scraped % BROWSER_RESTART_EVERY == 0:
                print("  [redÃ©marrage navigateur â€“ anti-throttle]")
                await browser.close()
                await asyncio.sleep(random.uniform(5, 10))
                browser, page = await new_browser(pw)

            # Pause alÃ©atoire entre les magasins
            pause = PAUSE_ENTRE_STORES + random.uniform(0, 3)
            await asyncio.sleep(pause)

        await browser.close()

    # Sauvegarde finale
    save_json(results)

    total_avis = sum(len(m["avis"]) for m in results)
    print("\n" + "=" * 60)
    print(f"  TerminÃ© !  {len(results)} magasin(s) traitÃ©(s)")
    print(f"  Total avis collectÃ©s : {total_avis}")
    print(f"  Fichier JSON         : {OUTPUT_FILE}")
    print("=" * 60)

    # AperÃ§u
    print("\nAperÃ§u (3 premiers magasins) :")
    for m in results[:3]:
        print(f"\n  â–¸ {m['nom']}")
        print(f"    Note globale : {m['note_globale']}  ({m['nb_avis_total']} avis au total)")
        for av in m["avis"][:2]:
            texte_court = (av["texte"] or "â€”")[:80]
            print(f"    â€¢ [{av['note']}â˜…] {av['date']}  â€” {texte_court}")


# â”€â”€â”€ Point d'entrÃ©e â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape les avis Google Maps des magasins Decathlon."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Limiter Ã  N magasins (utile pour tester).",
    )
    parser.add_argument(
        "--max-avis",
        type=int,
        default=DEFAULT_MAX_AVIS,
        metavar="N",
        help=f"Nombre maximum d'avis par magasin (dÃ©faut : {DEFAULT_MAX_AVIS}).",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reprendre un scraping interrompu (ignore les magasins dÃ©jÃ  dans le JSON de sortie).",
    )

    asyncio.run(main(parser.parse_args()))