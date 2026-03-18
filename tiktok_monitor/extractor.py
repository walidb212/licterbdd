from __future__ import annotations

import logging
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
