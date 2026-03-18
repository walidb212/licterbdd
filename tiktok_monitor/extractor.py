from __future__ import annotations

import json
import logging
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from monitor_core import repair_mojibake


log = logging.getLogger("tiktok_monitor.extractor")


class _YDLLogger:
    def debug(self, message: str) -> None:
        if message and not str(message).startswith("[debug]"):
            log.debug(str(message))

    def info(self, message: str) -> None:
        log.debug(str(message))

    def warning(self, message: str) -> None:
        log.debug(str(message))

    def error(self, message: str) -> None:
        log.debug(str(message))


@dataclass
class VideoRecord:
    run_id: str
    brand_focus: str
    source_type: str
    query_name: str
    query_text: str
    pillar: str
    production_status: str
    video_id: str
    video_url: str
    title: str
    description: str
    author_name: str
    author_id: str
    published_at: str
    duration_seconds: int
    view_count: int
    like_count: int
    comment_count: int
    repost_count: int
    save_count: int
    thumbnail_url: str
    source_partition: str = "social"


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def _clean_text(value: Any) -> str:
    return " ".join(repair_mojibake(str(value or "")).split())


def _iso(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
        except Exception:
            return str(value)
    if isinstance(value, str) and len(value) == 8 and value.isdigit():
        try:
            return datetime.strptime(value, "%Y%m%d").replace(tzinfo=timezone.utc).isoformat()
        except Exception:
            return value
    return str(value)


# ---------------------------------------------------------------------------
# yt-dlp extractor (official accounts)
# ---------------------------------------------------------------------------

class TikTokExtractor:
    def __init__(self, quiet: bool = True) -> None:
        self.quiet = quiet

    def _ydl_opts(self, *, playlist_items: str) -> dict[str, Any]:
        return {
            "quiet": self.quiet,
            "no_warnings": self.quiet,
            "ignoreerrors": True,
            "logger": _YDLLogger(),
            "playlist_items": playlist_items,
        }

    def extract_source(self, url: str, *, max_items: int) -> list[dict]:
        try:
            import yt_dlp
        except ImportError as exc:
            raise RuntimeError("yt-dlp is not installed. Run: pip install yt-dlp") from exc

        results: list[dict] = []
        with yt_dlp.YoutubeDL(self._ydl_opts(playlist_items=f"1:{max(max_items * 5, max_items)}")) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except Exception as exc:
                log.warning("yt-dlp extraction failed for %s: %s", url, exc)
                return results

            if not info:
                return results
            if info.get("_type") != "playlist" and "entries" not in info:
                return [info]

            for entry in info.get("entries") or []:
                if not entry:
                    continue
                if entry.get("id"):
                    results.append(entry)
                elif entry.get("url"):
                    try:
                        full = ydl.extract_info(entry["url"], download=False)
                    except Exception as exc:
                        log.debug("Re-extract failed for %s: %s", entry.get("url"), exc)
                        continue
                    if full and full.get("id"):
                        results.append(full)
                if len(results) >= max_items:
                    break
        return results[:max_items]

    def normalize_video(
        self,
        raw: dict,
        *,
        run_id: str,
        brand_focus: str,
        source_type: str,
        query_name: str,
        query_text: str,
        pillar: str,
        production_status: str,
    ) -> VideoRecord:
        video_id = str(raw.get("id") or raw.get("display_id") or "")
        description = _clean_text(raw.get("description"))
        title = _clean_text(raw.get("title") or description[:160])
        return VideoRecord(
            run_id=run_id,
            brand_focus=brand_focus,
            source_type=source_type,
            query_name=query_name,
            query_text=query_text,
            pillar=pillar,
            production_status=production_status,
            video_id=video_id,
            video_url=raw.get("webpage_url") or f"https://www.tiktok.com/@video/{video_id}",
            title=title,
            description=description[:2000],
            author_name=_clean_text(raw.get("uploader") or raw.get("channel")),
            author_id=_clean_text(raw.get("uploader_id") or raw.get("channel_id")),
            published_at=_iso(raw.get("timestamp") or raw.get("upload_date")),
            duration_seconds=_safe_int(raw.get("duration")),
            view_count=_safe_int(raw.get("view_count")),
            like_count=_safe_int(raw.get("like_count")),
            comment_count=_safe_int(raw.get("comment_count")),
            repost_count=_safe_int(raw.get("repost_count")),
            save_count=_safe_int(raw.get("save_count")),
            thumbnail_url=_clean_text(raw.get("thumbnail")),
        )


# ---------------------------------------------------------------------------
# DrissionPage hashtag scraper (no login required)
# ---------------------------------------------------------------------------

HASHTAG_SCROLL_PAUSE = 2.0
HASHTAG_MAX_SCROLLS = 5
HASHTAG_PAGE_LOAD_WAIT = 5


def _parse_compact_number(text: str) -> int:
    """Parse TikTok compact numbers like '1.2M', '45.3K', '890'."""
    if not text:
        return 0
    text = text.strip().upper().replace(",", ".")
    try:
        if "M" in text:
            return int(float(text.replace("M", "")) * 1_000_000)
        if "K" in text:
            return int(float(text.replace("K", "")) * 1_000)
        if "B" in text:
            return int(float(text.replace("B", "")) * 1_000_000_000)
        return int(float(text))
    except (ValueError, TypeError):
        return 0


def _safe_int_multi(d: dict, keys: list[str]) -> int:
    """Get an int from a dict trying multiple keys."""
    for key in keys:
        val = d.get(key)
        if val is not None:
            try:
                return int(val)
            except (ValueError, TypeError):
                continue
    return 0


def _parse_video_item(item: dict, hashtag: str) -> dict | None:
    """Parse a raw TikTok video item into a clean dict."""
    try:
        if not isinstance(item, dict):
            return None

        # Author
        author_raw = item.get("author", {})
        if isinstance(author_raw, str):
            author_name = author_raw
            author_id = author_raw
        elif isinstance(author_raw, dict):
            author_name = author_raw.get("nickname", "")
            author_id = author_raw.get("uniqueId", author_raw.get("unique_id", ""))
        else:
            author_name = ""
            author_id = ""

        # Stats
        stats = item.get("stats", item.get("statistics", {}))
        if not isinstance(stats, dict):
            stats = {}

        view_count = _safe_int_multi(stats, ["playCount", "play_count", "viewCount"])
        like_count = _safe_int_multi(stats, ["diggCount", "digg_count", "likeCount"])
        comment_count = _safe_int_multi(stats, ["commentCount", "comment_count"])
        share_count = _safe_int_multi(stats, ["shareCount", "share_count"])

        # Description
        desc = str(item.get("desc", item.get("description", "")))

        # Date
        create_time = item.get("createTime", item.get("create_time", 0))
        if isinstance(create_time, str):
            try:
                create_time = int(create_time)
            except ValueError:
                create_time = 0

        published_at = ""
        if create_time:
            published_at = datetime.fromtimestamp(create_time, tz=timezone.utc).isoformat()

        # Video ID
        video_id = str(item.get("id", item.get("video_id", "")))
        if not video_id:
            return None

        # URL
        url = ""
        if author_id and video_id:
            url = f"https://www.tiktok.com/@{author_id}/video/{video_id}"

        return {
            "video_id": video_id,
            "video_url": url,
            "title": desc[:160],
            "description": desc[:2000],
            "author_name": author_name,
            "author_id": author_id,
            "published_at": published_at,
            "view_count": view_count,
            "like_count": like_count,
            "comment_count": comment_count,
            "repost_count": share_count,
            "save_count": 0,
            "duration_seconds": 0,
            "thumbnail_url": "",
            "hashtag_source": f"#{hashtag}",
        }
    except Exception as exc:
        log.debug("Error parsing video item: %s", exc)
        return None


def _extract_from_ssr(ssr_data: dict, hashtag: str) -> list[dict]:
    """Extract videos from TikTok SSR data (__UNIVERSAL_DATA_FOR_REHYDRATION__)."""
    videos: list[dict] = []
    scope = ssr_data.get("__DEFAULT_SCOPE__", {})

    # Look in webapp.challenge-detail
    challenge_detail = scope.get("webapp.challenge-detail", {})
    items = challenge_detail.get("itemList", [])

    # Fallback: search other paths
    if not items:
        for key in scope:
            val = scope[key]
            if isinstance(val, dict) and "itemList" in val:
                items = val["itemList"]
                break

    for item in items:
        v = _parse_video_item(item, hashtag)
        if v:
            videos.append(v)

    return videos


def _extract_from_dom(page, hashtag: str) -> list[dict]:
    """Fallback: extract video info from DOM elements via JS."""
    videos: list[dict] = []
    try:
        video_data = page.run_js("""
            const results = [];
            const videoCards = document.querySelectorAll(
                '[data-e2e="challenge-item"], [class*="DivItemContainer"], [class*="VideoCard"], a[href*="/video/"]'
            );
            videoCards.forEach((card) => {
                const link = card.querySelector('a[href*="/video/"]') || (card.tagName === 'A' ? card : null);
                if (!link) return;
                const href = link.getAttribute('href') || '';
                const videoIdMatch = href.match(/video\\/([0-9]+)/);
                const userMatch = href.match(/@([^/]+)/);
                if (!videoIdMatch) return;
                const descEl = card.querySelector(
                    '[data-e2e="challenge-item-desc"], [class*="desc"], [class*="caption"], [class*="Description"]'
                );
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
                    "video_url": item.get("url", ""),
                    "title": (item.get("description") or "")[:160],
                    "description": (item.get("description") or "")[:2000],
                    "author_name": item.get("username", ""),
                    "author_id": item.get("username", ""),
                    "published_at": "",
                    "view_count": _parse_compact_number(item.get("views_text", "")),
                    "like_count": 0,
                    "comment_count": 0,
                    "repost_count": 0,
                    "save_count": 0,
                    "duration_seconds": 0,
                    "thumbnail_url": "",
                    "hashtag_source": f"#{hashtag}",
                })
    except Exception as exc:
        log.debug("DOM extraction JS error: %s", exc)

    return videos


class TikTokHashtagScraper:
    """DrissionPage-based scraper for TikTok hashtag pages. No login required."""

    def __init__(self, headless: bool = True) -> None:
        self.headless = headless
        self.page = None

    def start(self) -> None:
        """Initialize Chrome browser via DrissionPage."""
        from DrissionPage import ChromiumPage, ChromiumOptions

        log.info("Initializing Chrome via DrissionPage (headless=%s)...", self.headless)

        options = ChromiumOptions()
        if self.headless:
            options.headless()

        # Anti-detection flags
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
        options.set_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )

        self.page = ChromiumPage(options)

        # Inject anti-detection JS
        self.page.run_js("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = {runtime: {}};
        """)

        # Inject API interceptor to capture XHR responses
        self._inject_api_interceptor()

        log.info("Chrome browser ready")

    def _inject_api_interceptor(self) -> None:
        """Inject JS to capture TikTok API responses from XHR/fetch."""
        self.page.run_js("""
            window.__tiktokApiData = [];

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

    def scrape_hashtag(self, hashtag: str, *, max_items: int = 10) -> list[dict]:
        """Scrape a single TikTok hashtag page and return video dicts."""
        url = f"https://www.tiktok.com/tag/{hashtag}"
        log.info("Scraping #%s -> %s", hashtag, url)

        try:
            self.page.get(url)
            # Re-inject interceptor on new page
            self._inject_api_interceptor()
            time.sleep(HASHTAG_PAGE_LOAD_WAIT)

            # Scroll to load more videos
            for scroll in range(HASHTAG_MAX_SCROLLS):
                self.page.run_js("window.scrollBy(0, window.innerHeight * 2);")
                time.sleep(HASHTAG_SCROLL_PAUSE)

            videos = self._extract_videos(hashtag)
            log.info("#%s: %d videos extracted", hashtag, len(videos))
            return videos[:max_items]

        except Exception as exc:
            log.warning("#%s: scraping failed — %s", hashtag, exc)
            return []

    def _extract_videos(self, hashtag: str) -> list[dict]:
        """Extract videos from page using multiple methods (SSR, API, SIGI, DOM)."""
        videos: list[dict] = []
        seen_ids: set[str] = set()

        # Method 1: SSR data (__UNIVERSAL_DATA_FOR_REHYDRATION__)
        try:
            script_data = self.page.run_js("""
                const el = document.getElementById('__UNIVERSAL_DATA_FOR_REHYDRATION__');
                return el ? el.textContent : null;
            """)
            if script_data:
                ssr_data = json.loads(script_data)
                for v in _extract_from_ssr(ssr_data, hashtag):
                    if v["video_id"] not in seen_ids:
                        seen_ids.add(v["video_id"])
                        videos.append(v)
                if videos:
                    log.info("  SSR: %d videos from embedded JSON", len(videos))
        except Exception as exc:
            log.debug("  SSR extraction failed: %s", exc)

        # Method 2: Intercepted API data
        try:
            api_data = self.page.run_js("return window.__tiktokApiData || null;")
            if api_data and isinstance(api_data, list):
                api_count = 0
                for item_data in api_data:
                    v = _parse_video_item(item_data, hashtag)
                    if v and v["video_id"] not in seen_ids:
                        seen_ids.add(v["video_id"])
                        videos.append(v)
                        api_count += 1
                if api_count:
                    log.info("  API: %d videos from intercepted requests", api_count)
        except Exception as exc:
            log.debug("  API interception failed: %s", exc)

        # Method 3: SIGI_STATE
        try:
            sigi_data = self.page.run_js("""
                const el = document.getElementById('SIGI_STATE');
                return el ? el.textContent : null;
            """)
            if sigi_data:
                sigi = json.loads(sigi_data)
                item_module = sigi.get("ItemModule", {})
                sigi_count = 0
                for vid, item_data in item_module.items():
                    v = _parse_video_item(item_data, hashtag)
                    if v and v["video_id"] not in seen_ids:
                        seen_ids.add(v["video_id"])
                        videos.append(v)
                        sigi_count += 1
                if sigi_count:
                    log.info("  SIGI: %d videos", sigi_count)
        except Exception as exc:
            log.debug("  SIGI extraction failed: %s", exc)

        # Method 4: DOM fallback
        if not videos:
            try:
                dom_videos = _extract_from_dom(self.page, hashtag)
                for v in dom_videos:
                    if v["video_id"] not in seen_ids:
                        seen_ids.add(v["video_id"])
                        videos.append(v)
                if videos:
                    log.info("  DOM: %d videos from DOM elements", len(videos))
            except Exception as exc:
                log.debug("  DOM extraction failed: %s", exc)

        return videos

    def close(self) -> None:
        if self.page:
            try:
                self.page.quit()
            except Exception:
                pass
