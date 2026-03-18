from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from monitor_core import repair_mojibake


log = logging.getLogger("youtube_monitor.extractor")


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
    video_id: str
    video_url: str
    title: str
    description: str
    channel_name: str
    channel_id: str
    channel_url: str
    published_at: str
    duration_seconds: int
    view_count: int
    like_count: int
    comment_count: int
    thumbnail_url: str
    tags: list[str] = field(default_factory=list)
    language: str = ""
    source_partition: str = "social"


@dataclass
class CommentRecord:
    run_id: str
    brand_focus: str
    video_id: str
    video_url: str
    video_title: str
    pillar: str
    comment_id: str
    parent_id: str
    author: str
    text: str
    published_at: str
    like_count: int
    is_reply: bool
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


class YouTubeExtractor:
    def __init__(
        self,
        max_comments: int = 100,
        max_replies: int = 10,
        quiet: bool = True,
    ) -> None:
        self.max_comments = max_comments
        self.max_replies = max_replies
        self.quiet = quiet

    def search_videos(self, query: str, max_results: int = 15) -> list[dict]:
        return self._extract_playlist(f"ytsearch{max_results}:{query}", flat=False)

    def channel_videos(self, channel_url: str, max_videos: int = 20) -> list[dict]:
        base_url = channel_url.rstrip("/")
        results = self._extract_playlist(
            f"{base_url}/videos",
            flat=True,
            playlist_items=f"1:{max(max_videos * 5, max_videos)}",
        )
        return results[:max_videos]

    def _ydl_opts(self, *, flat: bool = False, playlist_items: str | None = None) -> dict[str, Any]:
        options: dict[str, Any] = {
            "quiet": self.quiet,
            "no_warnings": self.quiet,
            "ignoreerrors": True,
            "logger": _YDLLogger(),
            "extract_flat": "in_playlist" if flat else False,
            "skip_download": True,
            "noplaylist": False,
            "getcomments": True,
            "writecomments": False,
            "extractor_args": {
                "youtube": {
                    "max_comments": [
                        str(self.max_comments),
                        "10",
                        str(self.max_replies),
                        "5",
                    ],
                    "comment_sort": ["top"],
                }
            },
        }
        if playlist_items:
            options["playlist_items"] = playlist_items
        return options

    def _extract_playlist(self, url: str, *, flat: bool = False, playlist_items: str | None = None) -> list[dict]:
        try:
            import yt_dlp
        except ImportError as exc:
            raise RuntimeError("yt-dlp is not installed. Run: pip install yt-dlp") from exc

        results: list[dict] = []
        with yt_dlp.YoutubeDL(self._ydl_opts(flat=flat, playlist_items=playlist_items)) as ydl:
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
                if flat and entry.get("_type") == "url":
                    try:
                        full = ydl.extract_info(entry["url"], download=False)
                    except Exception as exc:
                        log.debug("Re-extract failed for %s: %s", entry.get("url"), exc)
                        continue
                    if full:
                        results.append(full)
                else:
                    results.append(entry)
        return results

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
    ) -> VideoRecord:
        video_id = str(raw.get("id") or raw.get("display_id") or "")
        title = _clean_text(raw.get("title"))
        return VideoRecord(
            run_id=run_id,
            brand_focus=brand_focus,
            source_type=source_type,
            query_name=query_name,
            query_text=_clean_text(query_text),
            pillar=pillar,
            video_id=video_id,
            video_url=raw.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}",
            title=title,
            description=_clean_text((raw.get("description") or "")[:2000]),
            channel_name=_clean_text(raw.get("uploader") or raw.get("channel")),
            channel_id=_clean_text(raw.get("channel_id") or raw.get("uploader_id")),
            channel_url=_clean_text(raw.get("channel_url") or raw.get("uploader_url")),
            published_at=_iso(raw.get("timestamp") or raw.get("upload_date")),
            duration_seconds=_safe_int(raw.get("duration")),
            view_count=_safe_int(raw.get("view_count")),
            like_count=_safe_int(raw.get("like_count")),
            comment_count=_safe_int(raw.get("comment_count")),
            thumbnail_url=_clean_text(raw.get("thumbnail")),
            tags=[_clean_text(tag) for tag in (raw.get("tags") or []) if _clean_text(tag)],
            language=_clean_text(raw.get("language")),
        )

    def normalize_comments(
        self,
        raw: dict,
        *,
        run_id: str,
        brand_focus: str,
        pillar: str,
    ) -> list[CommentRecord]:
        video_id = str(raw.get("id") or "")
        video_url = raw.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}"
        video_title = _clean_text(raw.get("title"))
        comments = raw.get("comments") or []
        records: list[CommentRecord] = []
        for comment in comments:
            if not comment:
                continue
            parent_id = str(comment.get("parent") or "")
            records.append(
                CommentRecord(
                    run_id=run_id,
                    brand_focus=brand_focus,
                    video_id=video_id,
                    video_url=video_url,
                    video_title=video_title,
                    pillar=pillar,
                    comment_id=str(comment.get("id") or ""),
                    parent_id=parent_id,
                    author=_clean_text(comment.get("author")),
                    text=_clean_text(comment.get("text")),
                    published_at=_iso(comment.get("timestamp")),
                    like_count=_safe_int(comment.get("like_count")),
                    is_reply=bool(parent_id and parent_id != "root"),
                )
            )
        return records
