#!/usr/bin/env python3
"""
Licteur - LinkedIn #Decathlon Scraper
RÃ©cupÃ¨re les posts publics LinkedIn mentionnant #Decathlon
postÃ©s par des personnes EXTERNES Ã  Decathlon.

StratÃ©gie :
1. Recherche via DuckDuckGo + Google pour trouver les posts LinkedIn publics
2. Scrape le contenu public de chaque post (meta tags, JSON-LD, HTML)
3. Filtre les posts venant de Decathlon ou ses employÃ©s
4. TÃ©lÃ©charge les images
5. RÃ©sume chaque post via Claude AI
6. Exporte le tout en JSON
"""

import json
import os
import re
import time
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse, urljoin

from dotenv import load_dotenv

load_dotenv()

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from anthropic import Anthropic

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HASHTAGS = [
    "decathlon",
    "DecathlonFrance",
    "DecathlonSport",
    "DecathlonIndia",
    "DecathlonItalia",
    "DecathlonBelgium",
    "DecathlonPolska",
    "DecathlonDeutschland",
    "DecathlonUK",
    "DecathlonBrasil",
    "DecathlonCanada",
]

# Recherches sur LinkedIn (utilise site:linkedin.com sans /posts pour compatibilitÃ©)
SEARCH_QUERIES = [
    # Hashtags principaux
    'site:linkedin.com decathlon #decathlon',
    'site:linkedin.com #DecathlonFrance',
    'site:linkedin.com #DecathlonSport',
    'site:linkedin.com #DecathlonIndia',
    'site:linkedin.com #DecathlonItalia',
    'site:linkedin.com #DecathlonBelgium',
    'site:linkedin.com #DecathlonPolska',
    'site:linkedin.com #DecathlonDeutschland',
    'site:linkedin.com #DecathlonUK',
    'site:linkedin.com #DecathlonBrasil',
    'site:linkedin.com #DecathlonCanada',
    # Recherches gÃ©nÃ©rales
    'site:linkedin.com decathlon avis client',
    'site:linkedin.com decathlon review experience',
    'site:linkedin.com decathlon partenariat collaboration',
    'site:linkedin.com decathlon partnership',
    'site:linkedin.com decathlon innovation sport',
    'site:linkedin.com decathlon magasin ouverture',
    'site:linkedin.com decathlon store opening',
    'site:linkedin.com decathlon produit product',
    'site:linkedin.com decathlon event hackathon startup',
    'site:linkedin.com decathlon sustainability digital',
    'site:linkedin.com decathlon marketplace',
    # Marques propres Decathlon
    'site:linkedin.com quechua kipsta domyos',
    'site:linkedin.com btwin forclaz kalenji',
    'site:linkedin.com tribord nabaiji rockrider',
]

SEARCH_TIMEOUT = 15  # secondes par requÃªte

# Mots-clÃ©s indiquant un lien avec Decathlon (employÃ©, page officielle)
DECATHLON_KEYWORDS = [
    "decathlon",
    "dÃ©cathlon",
    "decathlon france",
    "decathlon sport",
    "decathlon.fr",
    "decathlon.com",
    "oxylane",  # ancien nom du groupe
]

# Titres/postes indiquant un employÃ© Decathlon
EMPLOYEE_INDICATORS = [
    "decathlon",
    "dÃ©cathlon",
    "oxylane",
    "@ decathlon",
    "chez decathlon",
    "at decathlon",
    "decathlon leader",
    "decathlon manager",
    "decathlon director",
    "decathlon ceo",
    "decathlon cto",
    "decathlon cfo",
    "decathlon head of",
    "decathlon vp",
    "decathlon responsable",
    "decathlon directeur",
    "decathlon chef",
]

DAYS_LOOKBACK = 21
OUTPUT_FILE = "resultats_decathlon.json"
IMAGES_DIR = "images"
MAX_RESULTS_PER_SEARCH = 30
REQUEST_DELAY = (2, 5)  # dÃ©lai alÃ©atoire entre requÃªtes (min, max)

# Headers simulant un navigateur classique
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("licteur")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

import random


def random_delay():
    """Pause alÃ©atoire pour Ã©viter le blocage."""
    delay = random.uniform(*REQUEST_DELAY)
    time.sleep(delay)


def slugify(text: str, max_len: int = 60) -> str:
    """Transforme un texte en slug pour nom de fichier."""
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_]+", "-", text).strip("-")
    return text[:max_len]


def extract_linkedin_post_id(url: str) -> str | None:
    """Extrait l'ID d'un post LinkedIn depuis son URL."""
    patterns = [
        r"activity[/-](\d+)",
        r"ugcPost[/-](\d+)",
        r"share[/-](\d+)",
        r"pulse/([^/?]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def is_linkedin_post_url(url: str) -> bool:
    """VÃ©rifie si l'URL est un post LinkedIn."""
    if "linkedin.com" not in url:
        return False
    post_patterns = [
        "/posts/",
        "/feed/update/",
        "/pulse/",
        "activity",
    ]
    return any(p in url for p in post_patterns)


def normalize_linkedin_url(url: str) -> str:
    """Normalise une URL LinkedIn."""
    url = url.split("?")[0]
    url = url.rstrip("/")
    return url


# ---------------------------------------------------------------------------
# Phase 1 : Recherche de posts via moteurs de recherche
# ---------------------------------------------------------------------------


def search_all() -> list[str]:
    """Lance toutes les recherches et dÃ©duplique les URLs de posts LinkedIn."""
    all_urls = set()
    ddgs = DDGS(timeout=SEARCH_TIMEOUT)
    total = len(SEARCH_QUERIES)

    for i, query in enumerate(SEARCH_QUERIES, 1):
        try:
            log.info(f"[{i}/{total}] {query[:70]}")
            results = ddgs.text(query, max_results=MAX_RESULTS_PER_SEARCH, backend="auto")
            count = 0
            for r in results:
                url = r.get("href", "")
                if is_linkedin_post_url(url):
                    normalized = normalize_linkedin_url(url)
                    if normalized not in all_urls:
                        all_urls.add(normalized)
                        count += 1
            if count:
                log.info(f"  -> {count} nouveaux posts trouvÃ©s")
            time.sleep(1)
        except Exception as e:
            log.warning(f"  Erreur: {e}")

    log.info(f"TOTAL URLs uniques trouvÃ©es : {len(all_urls)}")
    return list(all_urls)


# ---------------------------------------------------------------------------
# Phase 2 : Scraping du contenu des posts publics
# ---------------------------------------------------------------------------


def fetch_linkedin_post(url: str, session: requests.Session) -> dict | None:
    """
    RÃ©cupÃ¨re le contenu d'un post LinkedIn public.
    LinkedIn injecte beaucoup de donnÃ©es dans les meta tags et JSON-LD.
    """
    try:
        resp = session.get(url, headers=HEADERS, timeout=20, allow_redirects=True, verify=True)
        if resp.status_code == 999:
            log.warning(f"  LinkedIn bloque la requÃªte (999) pour {url}")
            return None
        if resp.status_code != 200:
            log.warning(f"  HTTP {resp.status_code} pour {url}")
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        post_data = {
            "url": url,
            "auteur": None,
            "titre_auteur": None,
            "texte": None,
            "mentions": [],
            "images": [],
            "date": None,
        }

        # --- Extraction depuis les meta tags ---
        og_title = soup.find("meta", property="og:title")
        og_desc = soup.find("meta", property="og:description")
        og_image = soup.find("meta", property="og:image")
        author_meta = soup.find("meta", {"name": "author"})
        date_meta = soup.find("meta", {"name": "date"}) or soup.find(
            "meta", property="article:published_time"
        )

        if og_title:
            title_text = og_title.get("content", "")
            # Format typique : "PrÃ©nom Nom on LinkedIn: texte du post"
            match = re.match(
                r"^(.+?)\s+(?:on|sur|auf|en|no|na)\s+LinkedIn[:\s]*(.*)$",
                title_text,
                re.IGNORECASE,
            )
            if match:
                post_data["auteur"] = match.group(1).strip()
                post_data["texte"] = match.group(2).strip()
            else:
                post_data["texte"] = title_text

        if og_desc:
            desc = og_desc.get("content", "")
            if desc and (not post_data["texte"] or len(desc) > len(post_data["texte"])):
                post_data["texte"] = desc

        if og_image:
            img_url = og_image.get("content", "")
            if img_url and "linkedin.com" in img_url:
                post_data["images"].append(img_url)

        if author_meta:
            post_data["auteur"] = post_data["auteur"] or author_meta.get("content")

        if date_meta:
            post_data["date"] = date_meta.get("content")

        # --- Extraction depuis JSON-LD ---
        json_ld_scripts = soup.find_all("script", type="application/ld+json")
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if "author" in data:
                        author = data["author"]
                        if isinstance(author, dict):
                            post_data["auteur"] = post_data["auteur"] or author.get(
                                "name"
                            )
                            post_data["titre_auteur"] = author.get(
                                "jobTitle", author.get("description", "")
                            )
                    if "articleBody" in data:
                        body = data["articleBody"]
                        if body and (
                            not post_data["texte"]
                            or len(body) > len(post_data["texte"])
                        ):
                            post_data["texte"] = body
                    if "datePublished" in data:
                        post_data["date"] = data["datePublished"]
                    if "image" in data:
                        images = data["image"]
                        if isinstance(images, str):
                            images = [images]
                        if isinstance(images, list):
                            for img in images:
                                if isinstance(img, str) and img not in post_data["images"]:
                                    post_data["images"].append(img)
                                elif isinstance(img, dict) and img.get("url"):
                                    if img["url"] not in post_data["images"]:
                                        post_data["images"].append(img["url"])
                    if "interactionStatistic" in data:
                        for stat in data.get("interactionStatistic", []):
                            if isinstance(stat, dict):
                                itype = stat.get("interactionType", "")
                                if "Comment" in str(itype):
                                    post_data["nb_commentaires"] = stat.get(
                                        "userInteractionCount", 0
                                    )
                                elif "Like" in str(itype):
                                    post_data["nb_likes"] = stat.get(
                                        "userInteractionCount", 0
                                    )
            except (json.JSONDecodeError, TypeError):
                continue

        # --- Extraction des images supplÃ©mentaires dans le HTML ---
        for img_tag in soup.find_all("img"):
            src = img_tag.get("src", "") or img_tag.get("data-delayed-url", "")
            if src and ("media" in src or "dms" in src) and src not in post_data["images"]:
                post_data["images"].append(src)

        # --- Extraction des mentions (@) dans le texte ---
        if post_data["texte"]:
            mentions = re.findall(r"@([\w\s]+?)(?:\s|$|[,.])", post_data["texte"])
            post_data["mentions"] = [m.strip() for m in mentions if m.strip()]

            # Cherche aussi les liens de mentions LinkedIn
            for a_tag in soup.find_all("a", href=True):
                href = a_tag.get("href", "")
                if "linkedin.com/in/" in href or "linkedin.com/company/" in href:
                    name = a_tag.get_text(strip=True)
                    if name and name not in post_data["mentions"]:
                        post_data["mentions"].append(name)

        # --- Extraction depuis le HTML visible (fallback) ---
        if not post_data["texte"]:
            content_divs = soup.find_all(
                "div", class_=re.compile(r"(feed-shared-text|description|post-content)")
            )
            for div in content_divs:
                text = div.get_text(strip=True)
                if text and len(text) > 50:
                    post_data["texte"] = text
                    break

        # Nettoyage
        if post_data["texte"]:
            post_data["texte"] = re.sub(r"\s+", " ", post_data["texte"]).strip()

        # VÃ©rifie qu'on a au moins du texte ou un auteur
        if not post_data["texte"] and not post_data["auteur"]:
            log.warning(f"  Aucun contenu extractible pour {url}")
            return None

        # Filtre les pages de connexion LinkedIn (contenu gÃ©nÃ©rique)
        generic_texts = [
            "plus de 500 millions",
            "gÃ©rez votre image professionnelle",
            "join your colleagues",
            "sign up to see who you already know",
            "over 1 billion members",
            "mÃ¡s de 774 millones",
            "gestiona tu identidad profesional",
            "oltre 1 miliardo di membri",
            "Ã¼ber 1 milliarde mitglieder",
            "mais de 774 milhÃµes",
            "ponad 1 miliard uÅ¼ytkownikÃ³w",
            "manage your professional identity",
            "build and engage with your professional network",
        ]
        if post_data["texte"]:
            texte_lower = post_data["texte"].lower()
            if any(g in texte_lower for g in generic_texts):
                log.warning(f"  Post non public (page de connexion) : {url}")
                return None

        return post_data

    except requests.RequestException as e:
        log.warning(f"  Erreur rÃ©seau pour {url}: {e}")
        return None
    except Exception as e:
        log.warning(f"  Erreur inattendue pour {url}: {e}")
        return None


def scrape_all_posts(urls: list[str]) -> list[dict]:
    """Scrape tous les posts LinkedIn. Conserve toutes les URLs mÃªme si le scraping Ã©choue."""
    posts = []
    session = requests.Session()
    session.headers.update(HEADERS)
    total = len(urls)

    for i, url in enumerate(urls, 1):
        log.info(f"[{i}/{total}] Scraping {url}...")
        post = fetch_linkedin_post(url, session)
        if post:
            posts.append(post)
            log.info(f"  -> OK : {post.get('auteur', 'Inconnu')}")
        else:
            # LinkedIn bloque le scraping mais on garde l'URL dans le rÃ©sultat
            posts.append({
                "url": url,
                "auteur": None,
                "titre_auteur": None,
                "date": None,
                "texte": None,
                "statut": "non_scraped_linkedin_bloque",
            })
            log.info(f"  -> URL conservÃ©e (non scrapÃ©e) : {url}")
        random_delay()

    scraped = sum(1 for p in posts if p.get("texte"))
    log.info(f"Posts scrapÃ©s avec succÃ¨s : {scraped}/{total} | Total URLs conservÃ©es : {total}")
    return posts


# ---------------------------------------------------------------------------
# Phase 3 : Filtrage (exclure Decathlon et ses employÃ©s)
# ---------------------------------------------------------------------------


def is_decathlon_related(post: dict) -> bool:
    """
    DÃ©termine si un post provient de Decathlon ou d'un employÃ©.
    Retourne True si le post doit Ãªtre EXCLU.
    """
    auteur = (post.get("auteur") or "").lower()
    titre = (post.get("titre_auteur") or "").lower()
    url = (post.get("url") or "").lower()

    # VÃ©rifier si l'auteur est la page officielle Decathlon
    if re.search(r"\bdecathlon\b", auteur) and not re.search(
        r"\b(vs|about|loves?|fan|client|review)\b", auteur
    ):
        # L'auteur contient "decathlon" et ce n'est pas juste un fan
        # VÃ©rifie si c'est un nom de personne qui contient "decathlon"
        # ou la page officielle
        if "decathlon" in auteur.split() or auteur.startswith("decathlon"):
            log.info(f"  EXCLU (auteur Decathlon): {auteur}")
            return True

    # VÃ©rifier si le titre/poste de l'auteur mentionne Decathlon
    for indicator in EMPLOYEE_INDICATORS:
        if indicator in titre:
            log.info(f"  EXCLU (employÃ© Decathlon): {auteur} - {titre}")
            return True

    # VÃ©rifier si c'est un post depuis la page company de Decathlon
    if "/company/decathlon" in url:
        log.info(f"  EXCLU (page company Decathlon)")
        return True

    return False


def filter_posts(posts: list[dict]) -> list[dict]:
    """Filtre les posts pour ne garder que ceux externes Ã  Decathlon."""
    filtered = []
    for post in posts:
        if not is_decathlon_related(post):
            filtered.append(post)

    excluded = len(posts) - len(filtered)
    log.info(f"Filtrage : {len(filtered)} gardÃ©s, {excluded} exclus (Decathlon)")
    return filtered


# ---------------------------------------------------------------------------
# Phase 4 : Filtrage par date (7 derniers jours)
# ---------------------------------------------------------------------------


def filter_by_date(posts: list[dict], days: int = DAYS_LOOKBACK) -> list[dict]:
    """Filtre les posts pour ne garder que ceux des N derniers jours."""
    cutoff = datetime.now() - timedelta(days=days)
    filtered = []

    for post in posts:
        date_str = post.get("date")
        if date_str:
            try:
                # Essaie plusieurs formats de date
                for fmt in [
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d",
                    "%Y-%m-%dT%H:%M:%S.%fZ",
                    "%Y-%m-%dT%H:%M:%S%z",
                ]:
                    try:
                        post_date = datetime.strptime(
                            date_str[:19], fmt[:19].replace("%z", "")
                        )
                        if post_date >= cutoff:
                            filtered.append(post)
                        break
                    except ValueError:
                        continue
                else:
                    # Si aucun format ne marche, on garde le post
                    filtered.append(post)
            except Exception:
                filtered.append(post)
        else:
            # Pas de date trouvÃ©e -> on garde (la recherche Ã©tait limitÃ©e Ã  7j)
            filtered.append(post)

    log.info(f"Filtrage date : {len(filtered)} posts dans les {days} derniers jours")
    return filtered


# ---------------------------------------------------------------------------
# Phase 5 : TÃ©lÃ©chargement des images
# ---------------------------------------------------------------------------


def download_images(posts: list[dict], images_dir: str = IMAGES_DIR) -> list[dict]:
    """TÃ©lÃ©charge les images des posts et met Ã  jour les chemins."""
    Path(images_dir).mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update(HEADERS)

    for post in posts:
        local_images = []
        for img_url in post.get("images", []):
            try:
                # GÃ©nÃ¨re un nom de fichier unique
                url_hash = hashlib.md5(img_url.encode()).hexdigest()[:10]
                auteur_slug = slugify(post.get("auteur") or "unknown", 20)
                ext = ".jpg"
                parsed = urlparse(img_url)
                path_ext = os.path.splitext(parsed.path)[1]
                if path_ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
                    ext = path_ext

                filename = f"{auteur_slug}_{url_hash}{ext}"
                filepath = os.path.join(images_dir, filename)

                if os.path.exists(filepath):
                    local_images.append(filepath)
                    continue

                resp = session.get(img_url, timeout=15)
                if resp.status_code == 200:
                    with open(filepath, "wb") as f:
                        f.write(resp.content)
                    local_images.append(filepath)
                    log.info(f"  Image tÃ©lÃ©chargÃ©e : {filename}")
                else:
                    log.warning(
                        f"  Ã‰chec tÃ©lÃ©chargement image ({resp.status_code}): {img_url[:80]}"
                    )
            except Exception as e:
                log.warning(f"  Erreur tÃ©lÃ©chargement image: {e}")

            random_delay()

        post["images_locales"] = local_images

    return posts


# ---------------------------------------------------------------------------
# Phase 6 : RÃ©sumÃ© via Claude AI
# ---------------------------------------------------------------------------


def summarize_with_claude(posts: list[dict]) -> list[dict]:
    """GÃ©nÃ¨re un rÃ©sumÃ© de chaque post via l'API Claude."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        log.warning(
            "ANTHROPIC_API_KEY non dÃ©finie. Les rÃ©sumÃ©s ne seront pas gÃ©nÃ©rÃ©s."
        )
        for post in posts:
            texte = post.get("texte") or ""
            post["resume"] = texte[:200] + "..." if texte else None
        return posts

    client = Anthropic(api_key=api_key)
    total = len(posts)

    for i, post in enumerate(posts, 1):
        texte = post.get("texte") or ""
        if not texte or len(texte) < 30:
            post["resume"] = texte if texte else None
            continue

        try:
            log.info(f"[{i}/{total}] RÃ©sumÃ© Claude pour : {post.get('auteur', 'Inconnu')}")
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "RÃ©sume ce post LinkedIn en 2-3 phrases concises en franÃ§ais. "
                            "Identifie le sujet principal et le ton du message. "
                            "Si le post mentionne Decathlon, prÃ©cise dans quel contexte.\n\n"
                            f"Post de {post.get('auteur', 'Inconnu')}:\n"
                            f"{texte[:2000]}"
                        ),
                    }
                ],
            )
            post["resume"] = message.content[0].text
        except Exception as e:
            log.warning(f"  Erreur Claude API: {e}")
            post["resume"] = texte[:200] + "..." if len(texte) > 200 else texte

        # Petit dÃ©lai pour respecter les rate limits
        time.sleep(0.5)

    return posts


# ---------------------------------------------------------------------------
# Phase 7 : Export JSON
# ---------------------------------------------------------------------------


def export_json(posts: list[dict], output_file: str = OUTPUT_FILE, all_urls: list[str] = None):
    """Exporte les rÃ©sultats en JSON â€” inclut toutes les URLs trouvÃ©es."""
    posts_complets = [p for p in posts if p.get("texte")]
    posts_partiels = [p for p in posts if not p.get("texte")]

    export_data = {
        "metadata": {
            "date_extraction": datetime.now().isoformat(),
            "periode": f"derniers {DAYS_LOOKBACK} jours",
            "hashtags_recherches": [f"#{h}" for h in HASHTAGS],
            "nombre_recherches": len(SEARCH_QUERIES),
            "nombre_urls_trouvees": len(all_urls) if all_urls else len(posts),
            "nombre_posts_scrapes": len(posts_complets),
            "nombre_posts_non_scrapes": len(posts_partiels),
            "nombre_posts_total": len(posts),
        },
        "posts": [],
    }

    for post in posts:
        export_data["posts"].append(
            {
                "url": post.get("url"),
                "auteur": post.get("auteur"),
                "titre_auteur": post.get("titre_auteur"),
                "date": post.get("date"),
                "texte": post.get("texte"),
                "resume": post.get("resume"),
                "statut": post.get("statut", "scraped") if not post.get("texte") else "scraped",
                "mentions": post.get("mentions", []),
                "images": post.get("images", []),
                "images_locales": post.get("images_locales", []),
                "nb_likes": post.get("nb_likes"),
                "nb_commentaires": post.get("nb_commentaires"),
                "commentaires": post.get("commentaires", []),
            }
        )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    log.info(f"RÃ©sultats exportÃ©s dans : {output_file}")
    return output_file


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print("=" * 60)
    print("  LICTEUR - LinkedIn #Decathlon Scraper")
    print("=" * 60)
    print()

    # Ã‰tape 1 : Recherche
    log.info("Ã‰TAPE 1/5 : Recherche de posts LinkedIn (hashtags + recherche directe)...")
    urls = search_all()
    if not urls:
        log.error("Aucun post trouvÃ©. VÃ©rifiez votre connexion internet.")
        return
    log.info(f"Total URLs LinkedIn uniques trouvÃ©es : {len(urls)}")

    # Ã‰tape 2 : Scraping (garde toutes les URLs mÃªme si LinkedIn bloque)
    log.info("Ã‰TAPE 2/5 : Scraping du contenu des posts...")
    posts = scrape_all_posts(urls)

    # Ã‰tape 3 : Filtrage Decathlon (uniquement sur les posts scrapÃ©s)
    log.info("Ã‰TAPE 3/5 : Filtrage des posts Decathlon/employÃ©s...")
    posts_scrapes = [p for p in posts if p.get("texte")]
    posts_non_scrapes = [p for p in posts if not p.get("texte")]
    posts_scrapes_filtres = filter_posts(posts_scrapes)
    # RÃ©unit : posts scrapÃ©s filtrÃ©s + posts non scrapÃ©s (URLs conservÃ©es telles quelles)
    posts = posts_scrapes_filtres + posts_non_scrapes

    # Ã‰tape 4 : TÃ©lÃ©chargement des images (uniquement posts scrapÃ©s)
    log.info("Ã‰TAPE 4/5 : TÃ©lÃ©chargement des images...")
    posts = download_images(posts)

    # Ã‰tape 5 : RÃ©sumÃ©s Claude (uniquement posts scrapÃ©s)
    log.info("Ã‰TAPE 5/5 : GÃ©nÃ©ration des rÃ©sumÃ©s via Claude AI...")
    posts = summarize_with_claude(posts)

    # Export
    log.info("Export final en JSON...")
    output = export_json(posts, all_urls=urls)

    print()
    print("=" * 60)
    print(f"  TERMINÃ‰ ! {len(posts)} posts exportÃ©s")
    print(f"  Fichier : {output}")
    print(f"  Images  : {IMAGES_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()