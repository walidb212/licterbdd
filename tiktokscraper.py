#!/usr/bin/env python3
"""
=============================================================
 TikTok Hashtag Scraper - Decathlon & Intersport
 Utilise DrissionPage (PAS Playwright, PAS Selenium)
 Chrome headless en mode furtif - aucune config necessaire
=============================================================

 Utilisation :
   python tiktok_scraper.py

 Le fichier JSON est genere automatiquement dans le dossier courant.
 Pour le lire : python -m json.tool tiktok_data_YYYY-MM-DD.json

 Dependances :
   pip install DrissionPage

=============================================================
"""

import json
import re
import time
import random
import logging
from datetime import datetime, timezone
from pathlib import Path

from DrissionPage import ChromiumPage, ChromiumOptions

# ============================================================
#  CONFIGURATION
# ============================================================

LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("tiktok_scraper")

# --- Hashtags a scraper ---
HASHTAGS_DECATHLON = [
    "decathlon",
    "decathlonfrance",
    "decathlonsport",
    "decathlonfr",
    "decathloncoach",
    "decathloncommunity",
    "decathlonbelgique",
    "decathlonmaroc",
]

HASHTAGS_INTERSPORT = [
    "intersport",
    "intersportfrance",
    "intersportfr",
    "intersportsport",
]

ALL_HASHTAGS = HASHTAGS_DECATHLON + HASHTAGS_INTERSPORT

# --- Parametres de scraping ---
DELAY_MIN = 4          # Delai min entre chaque hashtag (secondes)
DELAY_MAX = 8          # Delai max
SCROLL_PAUSE = 2       # Pause entre les scrolls pour charger + de videos
MAX_SCROLLS = 5        # Nombre de scrolls par page de hashtag
PAGE_LOAD_WAIT = 5     # Attente chargement initial de la page (secondes)


# ============================================================
#  EXTRACTION DES DONNEES
# ============================================================

def parse_video_elements(page, hashtag: str) -> list[dict]:
    """
    Extrait les videos depuis le DOM de la page TikTok.
    Intercepte aussi les requetes API pour recuperer le JSON brut.
    """
    videos = []
    seen_ids = set()

    # --- Methode 1: Intercepter les donnees JSON dans le DOM ---
    try:
        # TikTok stocke les donnees dans __UNIVERSAL_DATA_FOR_REHYDRATION__
        script_data = page.run_js("""
            const el = document.getElementById('__UNIVERSAL_DATA_FOR_REHYDRATION__');
            return el ? el.textContent : null;
        """)

        if script_data:
            ssr_data = json.loads(script_data)
            videos_from_ssr = _extract_from_ssr(ssr_data, hashtag)
            for v in videos_from_ssr:
                if v["video_id"] not in seen_ids:
                    seen_ids.add(v["video_id"])
                    videos.append(v)

            if videos:
                logger.info(f"  SSR: {len(videos)} videos extraites du JSON embarque")
    except Exception as e:
        logger.debug(f"  SSR extraction echouee: {e}")

    # --- Methode 2: Intercepter les appels API XHR ---
    try:
        # Recuperer les reponses des appels API challenge/item_list
        api_data = page.run_js("""
            return window.__tiktokApiData || null;
        """)

        if api_data and isinstance(api_data, list):
            for item_data in api_data:
                v = _parse_video_item(item_data, hashtag)
                if v and v["video_id"] not in seen_ids:
                    seen_ids.add(v["video_id"])
                    videos.append(v)
    except Exception as e:
        logger.debug(f"  API interception echouee: {e}")

    # --- Methode 3: Extraire depuis le SIGI_STATE ---
    try:
        sigi_data = page.run_js("""
            const el = document.getElementById('SIGI_STATE');
            return el ? el.textContent : null;
        """)
        if sigi_data:
            sigi = json.loads(sigi_data)
            item_module = sigi.get("ItemModule", {})
            for vid, item_data in item_module.items():
                v = _parse_video_item(item_data, hashtag)
                if v and v["video_id"] not in seen_ids:
                    seen_ids.add(v["video_id"])
                    videos.append(v)

            if len(videos) > 0:
                logger.info(f"  SIGI: extraction reussie")
    except Exception as e:
        logger.debug(f"  SIGI extraction echouee: {e}")

    # --- Methode 4: Parser le DOM directement ---
    if not videos:
        try:
            dom_videos = _extract_from_dom(page, hashtag)
            for v in dom_videos:
                if v["video_id"] not in seen_ids:
                    seen_ids.add(v["video_id"])
                    videos.append(v)
            if videos:
                logger.info(f"  DOM: {len(videos)} videos extraites du DOM")
        except Exception as e:
            logger.debug(f"  DOM extraction echouee: {e}")

    return videos


def _extract_from_ssr(ssr_data: dict, hashtag: str) -> list[dict]:
    """Extrait les videos depuis les donnees SSR."""
    videos = []
    raw_items = []

    # Format __UNIVERSAL_DATA_FOR_REHYDRATION__
    scope = ssr_data.get("__DEFAULT_SCOPE__", {})

    # Chercher dans webapp.challenge-detail
    challenge_detail = scope.get("webapp.challenge-detail", {})
    items = challenge_detail.get("itemList", [])
    if items:
        raw_items = items

    # Chercher dans d'autres chemins possibles
    if not raw_items:
        for key in scope:
            val = scope[key]
            if isinstance(val, dict):
                if "itemList" in val:
                    raw_items = val["itemList"]
                    break

    for item in raw_items:
        v = _parse_video_item(item, hashtag)
        if v:
            videos.append(v)

    return videos


def _extract_from_dom(page, hashtag: str) -> list[dict]:
    """
    Fallback: extraire les infos videos depuis les elements du DOM.
    Moins precis mais fonctionne si les autres methodes echouent.
    """
    videos = []

    try:
        # Extraire les liens de videos et les metadonnees depuis le DOM
        video_data = page.run_js("""
            const results = [];
            // Chercher les conteneurs de videos
            const videoCards = document.querySelectorAll(
                '[data-e2e="challenge-item"], [class*="DivItemContainer"], [class*="VideoCard"], a[href*="/video/"]'
            );

            videoCards.forEach((card, index) => {
                const link = card.querySelector('a[href*="/video/"]') || (card.tagName === 'A' ? card : null);
                if (!link) return;

                const href = link.getAttribute('href') || '';
                const videoIdMatch = href.match(/video\\/(\\d+)/);
                const userMatch = href.match(/@([^/]+)/);

                if (!videoIdMatch) return;

                // Essayer de recuperer la description
                const descEl = card.querySelector(
                    '[data-e2e="challenge-item-desc"], [class*="desc"], [class*="caption"], [class*="Description"]'
                );

                // Essayer de recuperer les stats
                const statsEl = card.querySelector(
                    '[data-e2e="video-views"], [class*="PlayCount"], [class*="play-count"], strong'
                );

                results.push({
                    video_id: videoIdMatch[1],
                    username: userMatch ? userMatch[1] : '',
                    description: descEl ? descEl.textContent.trim() : '',
                    views_text: statsEl ? statsEl.textContent.trim() : '',
                    url: href.startsWith('http') ? href : 'https://www.tiktok.com' + href,
                });
            });

            return results;
        """)

        if video_data:
            for item in video_data:
                videos.append({
                    "video_id": item.get("video_id", ""),
                    "url": item.get("url", ""),
                    "description": item.get("description", ""),
                    "date_creation": "",
                    "timestamp_unix": 0,
                    "auteur": {
                        "id": "",
                        "nom_utilisateur": item.get("username", ""),
                        "surnom": "",
                    },
                    "statistiques": {
                        "vues": _parse_count_text(item.get("views_text", "")),
                        "likes": 0,
                        "commentaires": 0,
                        "partages": 0,
                    },
                    "hashtags": re.findall(r"#(\w+)", item.get("description", "")),
                    "musique": {},
                    "hashtag_source": f"#{hashtag}",
                })

    except Exception as e:
        logger.debug(f"DOM extraction JS error: {e}")

    return videos


def _parse_video_item(item: dict, hashtag: str) -> dict | None:
    """Parse un objet video TikTok brut en format propre."""
    try:
        if not isinstance(item, dict):
            return None

        # --- Auteur ---
        author_raw = item.get("author", {})
        if isinstance(author_raw, str):
            author = {"id": "", "nom_utilisateur": author_raw, "surnom": author_raw}
        elif isinstance(author_raw, dict):
            author = {
                "id": str(author_raw.get("id", "")),
                "nom_utilisateur": author_raw.get("uniqueId", author_raw.get("unique_id", "")),
                "surnom": author_raw.get("nickname", ""),
            }
        else:
            author = {"id": "", "nom_utilisateur": "", "surnom": ""}

        # --- Stats ---
        stats = item.get("stats", item.get("statistics", {}))
        if not isinstance(stats, dict):
            stats = {}

        statistiques = {
            "vues": _safe_int(stats, ["playCount", "play_count", "viewCount"]),
            "likes": _safe_int(stats, ["diggCount", "digg_count", "likeCount"]),
            "commentaires": _safe_int(stats, ["commentCount", "comment_count"]),
            "partages": _safe_int(stats, ["shareCount", "share_count"]),
        }

        # --- Description et hashtags ---
        desc = item.get("desc", item.get("description", ""))
        hashtags_regex = re.findall(r"#(\w+)", desc)

        challenges = item.get("challenges", item.get("textExtra", []))
        structured_tags = []
        if isinstance(challenges, list):
            for c in challenges:
                if isinstance(c, dict):
                    tag = c.get("title", c.get("hashtagName", ""))
                    if tag:
                        structured_tags.append(tag)

        all_hashtags = sorted(set(h.lower() for h in hashtags_regex + structured_tags))

        # --- Date de creation ---
        create_time = item.get("createTime", item.get("create_time", 0))
        if isinstance(create_time, str):
            try:
                create_time = int(create_time)
            except ValueError:
                create_time = 0

        date_str = ""
        if create_time:
            date_str = datetime.fromtimestamp(create_time, tz=timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )

        # --- Video ID ---
        video_id = str(item.get("id", item.get("video_id", "")))
        if not video_id:
            return None

        # --- URL ---
        username = author.get("nom_utilisateur", "")
        url = (
            f"https://www.tiktok.com/@{username}/video/{video_id}"
            if username and video_id
            else ""
        )

        # --- Musique ---
        music_raw = item.get("music", {})
        musique = {}
        if isinstance(music_raw, dict):
            musique = {
                "titre": music_raw.get("title", ""),
                "auteur": music_raw.get("authorName", ""),
            }

        return {
            "video_id": video_id,
            "url": url,
            "description": desc,
            "date_creation": date_str,
            "timestamp_unix": create_time,
            "auteur": author,
            "statistiques": statistiques,
            "hashtags": all_hashtags,
            "musique": musique,
            "hashtag_source": f"#{hashtag}",
        }
    except Exception as e:
        logger.debug(f"Erreur parsing video: {e}")
        return None


def _safe_int(d: dict, keys: list) -> int:
    """Recupere un entier depuis un dict en essayant plusieurs cles."""
    for key in keys:
        val = d.get(key)
        if val is not None:
            try:
                return int(val)
            except (ValueError, TypeError):
                continue
    return 0


def _parse_count_text(text: str) -> int:
    """Convertit un texte comme '1.2M' ou '345K' en entier."""
    if not text:
        return 0
    text = text.strip().upper().replace(",", ".")
    try:
        if "M" in text:
            return int(float(text.replace("M", "")) * 1_000_000)
        elif "K" in text:
            return int(float(text.replace("K", "")) * 1_000)
        elif "B" in text:
            return int(float(text.replace("B", "")) * 1_000_000_000)
        else:
            return int(text)
    except (ValueError, TypeError):
        return 0


def extract_challenge_info_from_page(page, hashtag: str) -> dict:
    """Extrait les metadonnees du hashtag (vues totales, etc.) depuis le DOM."""
    info = {"titre": hashtag, "description": "", "total_vues": 0, "total_videos": 0}

    try:
        meta_data = page.run_js("""
            const result = {};
            // Titre du hashtag
            const titleEl = document.querySelector(
                '[data-e2e="challenge-title"], h1, [class*="HashtagTitle"]'
            );
            result.title = titleEl ? titleEl.textContent.trim() : '';

            // Description
            const descEl = document.querySelector(
                '[data-e2e="challenge-desc"], [class*="HashtagDesc"], [class*="challenge-desc"]'
            );
            result.description = descEl ? descEl.textContent.trim() : '';

            // Stats (vues, videos)
            const statsEls = document.querySelectorAll(
                '[data-e2e="challenge-vvcount"], [class*="InfoText"], strong, [class*="stats"]'
            );
            result.stats_texts = Array.from(statsEls).map(el => el.textContent.trim());

            return result;
        """)

        if meta_data:
            if meta_data.get("title"):
                info["titre"] = meta_data["title"]
            if meta_data.get("description"):
                info["description"] = meta_data["description"]

            # Parser les stats
            for text in meta_data.get("stats_texts", []):
                val = _parse_count_text(text)
                if val > 0:
                    if "view" in text.lower() or "vue" in text.lower():
                        info["total_vues"] = val
                    elif "video" in text.lower():
                        info["total_videos"] = val
                    elif info["total_vues"] == 0:
                        info["total_vues"] = val
    except Exception as e:
        logger.debug(f"Challenge info extraction error: {e}")

    return info


# ============================================================
#  SCRAPER PRINCIPAL
# ============================================================

class TikTokHashtagScraper:
    """
    Scraper TikTok avec DrissionPage.
    Utilise Chrome headless (deja installe sur le systeme).
    PAS Playwright. PAS Selenium.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.page = None

    def _init_browser(self):
        """Initialise le navigateur Chrome headless."""
        logger.info("Initialisation du navigateur Chrome headless...")

        options = ChromiumOptions()

        if self.headless:
            options.headless()

        # Anti-detection
        options.set_argument("--disable-blink-features=AutomationControlled")
        options.set_argument("--no-first-run")
        options.set_argument("--no-default-browser-check")
        options.set_argument("--disable-infobars")
        options.set_argument("--disable-extensions")
        options.set_argument("--disable-gpu")
        options.set_argument("--disable-dev-shm-usage")
        options.set_argument("--no-sandbox")
        options.set_argument("--window-size=1440,900")
        options.set_argument("--lang=fr-FR")

        # User-agent realiste
        options.set_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )

        self.page = ChromiumPage(options)

        # Injecter un script anti-detection
        self.page.run_js("""
            // Masquer le webdriver
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            // Masquer l'automatisation
            window.chrome = {runtime: {}};
        """)

        logger.info("Navigateur Chrome headless pret")

    def _inject_api_interceptor(self):
        """Injecte un intercepteur pour capturer les reponses API TikTok."""
        self.page.run_js("""
            // Intercepter les reponses XHR/fetch pour capturer les donnees API
            window.__tiktokApiData = [];

            // Intercepter fetch
            const originalFetch = window.fetch;
            window.fetch = async function(...args) {
                const response = await originalFetch.apply(this, args);
                const url = typeof args[0] === 'string' ? args[0] : args[0]?.url || '';

                if (url.includes('challenge/item_list') || url.includes('api/post')) {
                    try {
                        const cloned = response.clone();
                        const data = await cloned.json();
                        if (data.itemList) {
                            window.__tiktokApiData.push(...data.itemList);
                        }
                    } catch(e) {}
                }
                return response;
            };

            // Intercepter XMLHttpRequest
            const originalOpen = XMLHttpRequest.prototype.open;
            const originalSend = XMLHttpRequest.prototype.send;
            XMLHttpRequest.prototype.open = function(method, url, ...rest) {
                this._url = url;
                return originalOpen.apply(this, [method, url, ...rest]);
            };
            XMLHttpRequest.prototype.send = function(...args) {
                this.addEventListener('load', function() {
                    if (this._url && (
                        this._url.includes('challenge/item_list') ||
                        this._url.includes('api/post')
                    )) {
                        try {
                            const data = JSON.parse(this.responseText);
                            if (data.itemList) {
                                window.__tiktokApiData.push(...data.itemList);
                            }
                        } catch(e) {}
                    }
                });
                return originalSend.apply(this, args);
            };
        """)

    def scrape_hashtag(self, hashtag: str) -> dict:
        """Scrape un seul hashtag TikTok."""
        url = f"https://www.tiktok.com/tag/{hashtag}"
        logger.info(f"Scraping #{hashtag} -> {url}")

        try:
            # Naviguer vers la page
            self.page.get(url)

            # Injecter l'intercepteur API
            self._inject_api_interceptor()

            # Attendre le chargement
            time.sleep(PAGE_LOAD_WAIT)

            # Verifier si on a un CAPTCHA
            page_html = self.page.html
            if "verify" in page_html.lower() and "captcha" in page_html.lower():
                logger.warning(f"  #{hashtag}: CAPTCHA detecte, attente supplementaire...")
                time.sleep(10)

            # Scroller pour charger plus de videos
            for scroll in range(MAX_SCROLLS):
                self.page.run_js("window.scrollBy(0, window.innerHeight * 2);")
                time.sleep(SCROLL_PAUSE)
                logger.debug(f"  Scroll {scroll + 1}/{MAX_SCROLLS}")

            # Extraire les infos du hashtag
            challenge_info = extract_challenge_info_from_page(self.page, hashtag)

            # Extraire les videos
            videos = parse_video_elements(self.page, hashtag)

            logger.info(f"  #{hashtag}: {len(videos)} videos extraites")

            return {
                "hashtag": f"#{hashtag}",
                "url": url,
                "date_scraping": datetime.now(timezone.utc).isoformat(),
                "infos_hashtag": challenge_info,
                "nombre_videos": len(videos),
                "videos": videos,
            }

        except Exception as e:
            logger.error(f"  #{hashtag}: Erreur - {e}")
            return {
                "hashtag": f"#{hashtag}",
                "url": url,
                "date_scraping": datetime.now(timezone.utc).isoformat(),
                "erreur": str(e),
                "infos_hashtag": {},
                "nombre_videos": 0,
                "videos": [],
            }

    def run(self, hashtags: list[str], filter_today: bool = False) -> dict:
        """Lance le scraping sur tous les hashtags."""
        logger.info("=" * 60)
        logger.info(f"DEMARRAGE - {len(hashtags)} hashtags a scraper")
        logger.info(f"Hashtags : {', '.join('#' + h for h in hashtags)}")
        logger.info(f"Mode headless : {'OUI' if self.headless else 'NON'}")
        logger.info("=" * 60)

        # Initialiser le navigateur
        self._init_browser()

        resultats = {}
        stats = {
            "hashtags_ok": 0,
            "hashtags_erreur": 0,
            "total_videos": 0,
            "total_videos_aujourdhui": 0,
        }

        try:
            for i, hashtag in enumerate(hashtags, 1):
                logger.info(f"\n--- [{i}/{len(hashtags)}] #{hashtag} ---")

                result = self.scrape_hashtag(hashtag)

                # Filtrer les videos du jour
                if filter_today and result.get("videos"):
                    today = datetime.now(timezone.utc).date()
                    videos_today = [
                        v
                        for v in result["videos"]
                        if v.get("timestamp_unix")
                        and datetime.fromtimestamp(
                            v["timestamp_unix"], tz=timezone.utc
                        ).date()
                        == today
                    ]
                    result["videos_aujourdhui"] = videos_today
                    result["nombre_videos_aujourdhui"] = len(videos_today)
                    stats["total_videos_aujourdhui"] += len(videos_today)

                # Stats globales
                if result.get("erreur"):
                    stats["hashtags_erreur"] += 1
                else:
                    stats["hashtags_ok"] += 1
                stats["total_videos"] += result.get("nombre_videos", 0)

                resultats[hashtag] = result

                # Pause entre les hashtags
                if i < len(hashtags):
                    pause = random.uniform(DELAY_MIN, DELAY_MAX)
                    logger.info(f"  Pause de {pause:.1f}s...")
                    time.sleep(pause)

        finally:
            # Toujours fermer le navigateur
            if self.page:
                try:
                    self.page.quit()
                    logger.info("Navigateur ferme")
                except Exception:
                    pass

        # Construire le resultat final
        output = {
            "metadata": {
                "date_scraping": datetime.now(timezone.utc).isoformat(),
                "outil": "TikTok Hashtag Scraper (DrissionPage + Chrome headless)",
                "nombre_hashtags": len(hashtags),
                "filtre_aujourdhui": filter_today,
                "hashtags_cibles": [f"#{h}" for h in hashtags],
            },
            "resume": stats,
            "resultats_par_hashtag": resultats,
        }

        return output

    def close(self):
        """Ferme le navigateur."""
        if self.page:
            try:
                self.page.quit()
            except Exception:
                pass


# ============================================================
#  SAUVEGARDE JSON
# ============================================================

def save_to_json(data: dict, filename: str | None = None) -> str:
    """Sauvegarde les resultats dans un fichier JSON."""
    if not filename:
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"tiktok_data_{ts}.json"

    filepath = Path(filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    size_kb = filepath.stat().st_size / 1024
    logger.info(f"Fichier JSON sauvegarde : {filepath} ({size_kb:.1f} Ko)")
    return str(filepath)


# ============================================================
#  POINT D'ENTREE
# ============================================================

def main():
    print(r"""
  _____ _ _   _____      _      ____
 |_   _(_) | |_   _|__  | | __ / ___|  ___ _ __ __ _ _ __   ___ _ __
   | | | | |/\| | / _ \ | |/ / \___ \ / __| '__/ _` | '_ \ / _ \ '__|
   | | | |   /  | | (_) ||   <   ___) | (__| | | (_| | |_) |  __/ |
   |_| |_|_/\_\ |_|\___/ |_|\_\ |____/ \___|_|  \__,_| .__/ \___|_|
                                                       |_|
    Decathlon & Intersport - TikTok Hashtag Scraper
    (DrissionPage + Chrome headless)
    """)

    # --- Lancer le scraping ---
    scraper = TikTokHashtagScraper(headless=True)
    results = scraper.run(
        hashtags=ALL_HASHTAGS,
        filter_today=True,  # True = ne garder que les videos du jour
    )

    # --- Afficher le resume ---
    r = results["resume"]
    print("\n" + "=" * 60)
    print("  RESUME DU SCRAPING")
    print("=" * 60)
    print(f"  Hashtags OK       : {r['hashtags_ok']}")
    print(f"  Hashtags en erreur: {r['hashtags_erreur']}")
    print(f"  Total videos      : {r['total_videos']}")
    print(f"  Videos du jour    : {r['total_videos_aujourdhui']}")
    print("=" * 60)

    # --- Sauvegarder en JSON ---
    filepath = save_to_json(results)

    print(f"\n  Fichier JSON pret : {filepath}")
    print(f"  Pour le lire      : python -m json.tool {filepath}")
    print()

    return filepath


if __name__ == "__main__":
    main()