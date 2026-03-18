"""
Scraper des magasins Decathlon en France
=========================================
StratÃ©gie :
  1. Charge la page /store-locator pour rÃ©cupÃ©rer les 335 liens /store-view/...
  2. Visite chaque page magasin et extrait :
       - Nom du magasin
       - Adresse (rue)
       - Code postal
       - Ville
       - Lien Google Maps (fourni directement par Decathlon)
  3. Sauvegarde le tout dans decathlon_france.json

Usage :
    pip install requests beautifulsoup4
    python3 scraper_decathlon.py
"""

import re
import json
import time
import sys
from datetime import date

import requests
from bs4 import BeautifulSoup

# â”€â”€â”€ Configuration â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

BASE_URL    = "https://www.decathlon.fr"
LOCATOR_URL = f"{BASE_URL}/store-locator"
OUTPUT_FILE = "decathlon_france.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

DELAY_BETWEEN_REQUESTS = 0.8   # secondes entre chaque requÃªte (politesse)
REQUEST_TIMEOUT        = 20    # secondes

# â”€â”€â”€ Session HTTP â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

session = requests.Session()
session.headers.update(HEADERS)

# â”€â”€â”€ Ã‰tape 1 : rÃ©cupÃ©rer la liste des liens /store-view/ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_store_links() -> list[str]:
    """Charge la page store-locator et retourne les URLs uniques des magasins."""
    print(f"Chargement de la page store-locatorâ€¦")
    resp = session.get(LOCATOR_URL, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    links = soup.find_all("a", href=re.compile(r"^/store-view/"))
    unique = sorted(set(a["href"] for a in links))
    print(f"  â†’ {len(unique)} liens magasins trouvÃ©s.")
    return unique


# â”€â”€â”€ Ã‰tape 2 : extraire les donnÃ©es d'une page magasin â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def parse_store_page(html: str, url: str) -> dict | None:
    """
    Extrait nom, adresse, code postal, ville, lien Google Maps
    depuis la page HTML d'un magasin individuel.
    """
    soup = BeautifulSoup(html, "html.parser")

    # â”€â”€ Nom â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    name_el = soup.find(class_="store-view-side-panel__body-store-title")
    if name_el:
        # Le bouton "Changer de magasin prÃ©fÃ©rÃ©" est dans le mÃªme Ã©lÃ©ment, on le retire
        for btn in name_el.find_all("button"):
            btn.decompose()
        name = name_el.get_text(strip=True)
    else:
        # Fallback : h3 ou h2 contenant un texte plausible
        h3 = soup.find("h3", class_=re.compile(r"store", re.I))
        name = h3.get_text(strip=True) if h3 else url.split("/")[-1]

    # PrÃ©fixer avec "Decathlon" si absent
    if "decathlon" not in name.lower():
        name = f"Decathlon {name}"

    # â”€â”€ Bloc adresse â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    addr_block = soup.find(class_="store-view-side-panel__body-details-block")
    if not addr_block:
        return None   # Page sans donnÃ©es exploitables

    # â”€â”€ Adresse texte â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    addr_span = addr_block.find("span", class_="vp-body-s")
    if not addr_span:
        return None

    raw_addr = addr_span.get_text(separator=" ").strip()
    # Format attendu : "Rue Prosper Guilhem ,  49070 ,   BeaucouzÃ©"
    parts = [p.strip() for p in raw_addr.split(",") if p.strip()]

    street      = parts[0] if len(parts) > 0 else ""
    postal_code = parts[1] if len(parts) > 1 else ""
    city        = parts[2] if len(parts) > 2 else ""

    # Nettoyage du code postal (parfois des espaces internes)
    postal_code = re.sub(r"\s+", "", postal_code)

    full_address = ", ".join(filter(None, [street, postal_code, city]))

    # â”€â”€ Lien Google Maps â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    gmaps_el = addr_block.find("a", href=re.compile(r"google\.com/maps", re.I))
    google_maps = gmaps_el["href"] if gmaps_el else (
        f"https://www.google.com/maps/search/?api=1&query="
        + requests.utils.quote(f"{name} {full_address}")
    )

    return {
        "nom":             name,
        "adresse":         street,
        "code_postal":     postal_code,
        "ville":           city,
        "adresse_complete": full_address,
        "google_maps":     google_maps,
        "url_page":        f"{BASE_URL}{url}",
    }


# â”€â”€â”€ Ã‰tape 3 : boucle principale â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def scrape_all_stores(links: list[str]) -> list[dict]:
    """Visite chaque page magasin et collecte les donnÃ©es."""
    stores = []
    total  = len(links)

    for i, path in enumerate(links, start=1):
        url = f"{BASE_URL}{path}"
        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            store = parse_store_page(resp.text, path)
            if store:
                stores.append(store)
                status = f"[{i}/{total}] OK    {store['nom'][:50]}"
            else:
                status = f"[{i}/{total}] SKIP  {path}"
        except requests.RequestException as e:
            status = f"[{i}/{total}] ERR   {path} â†’ {e}"

        # Affichage avec retour chariot pour ne pas inonder le terminal
        print(f"\r{status:<80}", end="", flush=True)
        if i % 20 == 0:
            print()   # saut de ligne toutes les 20 lignes

        time.sleep(DELAY_BETWEEN_REQUESTS)

    print()  # saut de ligne final
    return stores


# â”€â”€â”€ Sauvegarde JSON â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def save_json(stores: list[dict]) -> None:
    stores_sorted = sorted(stores, key=lambda s: (s["code_postal"], s["ville"]))

    output = {
        "source":         "Decathlon France â€“ store-locator",
        "date_scraping":  date.today().isoformat(),
        "total_magasins": len(stores_sorted),
        "magasins":       stores_sorted,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Fichier sauvegardÃ© : {OUTPUT_FILE}")


# â”€â”€â”€ Point d'entrÃ©e â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def main() -> None:
    print("=" * 60)
    print("  Scraper Decathlon France")
    print("=" * 60)

    # 1. Liste des liens
    try:
        links = get_store_links()
    except Exception as e:
        print(f"Erreur lors du chargement de la page principale : {e}")
        sys.exit(1)

    if not links:
        print("Aucun lien trouvÃ©. Le site a peut-Ãªtre changÃ© sa structure.")
        sys.exit(1)

    # 2. Scraping de chaque magasin
    print(f"\nScraping de {len(links)} pages magasinsâ€¦")
    stores = scrape_all_stores(links)

    print(f"\n{len(stores)} magasin(s) rÃ©cupÃ©rÃ©(s) avec succÃ¨s.")

    if not stores:
        print("Aucune donnÃ©e extraite.")
        sys.exit(1)

    # 3. Sauvegarde
    save_json(stores)
    print("=" * 60)

    # 4. AperÃ§u
    print("\nAperÃ§u des 5 premiers magasins :")
    for s in stores[:5]:
        print(f"  â€¢ {s['nom']}")
        print(f"    {s['adresse_complete']}")
        print(f"    {s['google_maps']}")
        print()


if __name__ == "__main__":
    main()
