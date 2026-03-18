from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def normalize_hash_input(*values: Any) -> str:
    parts: list[str] = []
    for value in values:
        if value is None:
            continue
        text = str(value).replace("\r", "\n")
        text = " ".join(text.split())
        if text:
            parts.append(text.casefold())
    return " | ".join(parts)


def repair_mojibake(value: str | None) -> str:
    if not value:
        return ""
    if not any(token in value for token in ("Ã", "Â", "â", "ð")):
        return value
    try:
        repaired = value.encode("latin1", errors="ignore").decode("utf-8", errors="ignore")
    except Exception:
        return value
    suspicious_before = sum(value.count(token) for token in ("Ã", "Â", "â", "ð"))
    suspicious_after = sum(repaired.count(token) for token in ("Ã", "Â", "â", "ð"))
    return repaired if suspicious_after < suspicious_before else value


def build_content_hash(*values: Any) -> str:
    normalized = normalize_hash_input(*values)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def parse_published_at(value: str) -> str | None:
    text = (value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    except Exception:
        pass
    try:
        parsed = parsedate_to_datetime(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    except Exception:
        return None


class StateStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "StateStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS run_log (
                run_id TEXT PRIMARY KEY,
                monitor_name TEXT NOT NULL,
                output_dir TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,
                config_json TEXT NOT NULL DEFAULT '{}',
                stats_json TEXT NOT NULL DEFAULT '{}',
                error TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS watermarks (
                monitor_name TEXT NOT NULL,
                source_name TEXT NOT NULL,
                entity_key TEXT NOT NULL,
                max_published_at TEXT,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (monitor_name, source_name, entity_key)
            );

            CREATE TABLE IF NOT EXISTS seen_items (
                monitor_name TEXT NOT NULL,
                source_name TEXT NOT NULL,
                source_partition TEXT NOT NULL,
                entity_key TEXT NOT NULL,
                item_key TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                published_at TEXT,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                PRIMARY KEY (monitor_name, source_name, entity_key, item_key, content_hash)
            );

            CREATE TABLE IF NOT EXISTS discovered_entities (
                monitor_name TEXT NOT NULL,
                source_name TEXT NOT NULL,
                entity_key TEXT NOT NULL,
                entity_name TEXT NOT NULL,
                entity_url TEXT NOT NULL,
                content_hash TEXT NOT NULL DEFAULT '',
                metadata_json TEXT NOT NULL DEFAULT '{}',
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                last_scraped_at TEXT,
                PRIMARY KEY (monitor_name, source_name, entity_key)
            );
            """
        )
        self.conn.commit()

    def log_run_start(self, run_id: str, monitor_name: str, output_dir: str, *, config: dict[str, Any] | None = None) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO run_log (
                run_id, monitor_name, output_dir, started_at, completed_at, status, config_json, stats_json, error
            ) VALUES (?, ?, ?, ?, NULL, 'running', ?, '{}', '')
            """,
            (run_id, monitor_name, output_dir, utc_now_iso(), json.dumps(config or {}, ensure_ascii=False)),
        )
        self.conn.commit()

    def log_run_end(
        self,
        run_id: str,
        *,
        status: str,
        stats: dict[str, Any] | None = None,
        error: str = "",
    ) -> None:
        self.conn.execute(
            """
            UPDATE run_log
            SET completed_at = ?, status = ?, stats_json = ?, error = ?
            WHERE run_id = ?
            """,
            (utc_now_iso(), status, json.dumps(stats or {}, ensure_ascii=False), error, run_id),
        )
        self.conn.commit()

    def get_watermark(self, monitor_name: str, source_name: str, entity_key: str) -> str | None:
        row = self.conn.execute(
            """
            SELECT max_published_at
            FROM watermarks
            WHERE monitor_name = ? AND source_name = ? AND entity_key = ?
            """,
            (monitor_name, source_name, entity_key),
        ).fetchone()
        return row["max_published_at"] if row else None

    def update_watermark(self, monitor_name: str, source_name: str, entity_key: str, published_at: str | None) -> None:
        if not published_at:
            return
        current = self.get_watermark(monitor_name, source_name, entity_key)
        if current and current >= published_at:
            return
        self.conn.execute(
            """
            INSERT INTO watermarks (monitor_name, source_name, entity_key, max_published_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(monitor_name, source_name, entity_key)
            DO UPDATE SET
                max_published_at = excluded.max_published_at,
                updated_at = excluded.updated_at
            """,
            (monitor_name, source_name, entity_key, published_at, utc_now_iso()),
        )
        self.conn.commit()

    def record_item(
        self,
        *,
        monitor_name: str,
        source_name: str,
        source_partition: str,
        entity_key: str,
        item_key: str,
        content_hash: str,
        published_at: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        now = utc_now_iso()
        existing = self.conn.execute(
            """
            SELECT 1
            FROM seen_items
            WHERE monitor_name = ? AND source_name = ? AND entity_key = ? AND item_key = ? AND content_hash = ?
            """,
            (monitor_name, source_name, entity_key, item_key, content_hash),
        ).fetchone()
        if existing:
            self.conn.execute(
                """
                UPDATE seen_items
                SET last_seen_at = ?, metadata_json = ?
                WHERE monitor_name = ? AND source_name = ? AND entity_key = ? AND item_key = ? AND content_hash = ?
                """,
                (
                    now,
                    json.dumps(metadata or {}, ensure_ascii=False),
                    monitor_name,
                    source_name,
                    entity_key,
                    item_key,
                    content_hash,
                ),
            )
            self.conn.commit()
            return False

        self.conn.execute(
            """
            INSERT INTO seen_items (
                monitor_name, source_name, source_partition, entity_key, item_key, content_hash,
                published_at, first_seen_at, last_seen_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                monitor_name,
                source_name,
                source_partition,
                entity_key,
                item_key,
                content_hash,
                published_at,
                now,
                now,
                json.dumps(metadata or {}, ensure_ascii=False),
            ),
        )
        self.conn.commit()
        self.update_watermark(monitor_name, source_name, entity_key, published_at)
        return True

    def upsert_entity(
        self,
        *,
        monitor_name: str,
        source_name: str,
        entity_key: str,
        entity_name: str,
        entity_url: str,
        content_hash: str = "",
        metadata: dict[str, Any] | None = None,
        mark_scraped: bool = False,
    ) -> None:
        now = utc_now_iso()
        row = self.conn.execute(
            """
            SELECT first_seen_at, last_scraped_at
            FROM discovered_entities
            WHERE monitor_name = ? AND source_name = ? AND entity_key = ?
            """,
            (monitor_name, source_name, entity_key),
        ).fetchone()
        first_seen_at = row["first_seen_at"] if row else now
        last_scraped_at = now if mark_scraped else (row["last_scraped_at"] if row else None)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO discovered_entities (
                monitor_name, source_name, entity_key, entity_name, entity_url, content_hash,
                metadata_json, first_seen_at, last_seen_at, last_scraped_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                monitor_name,
                source_name,
                entity_key,
                entity_name,
                entity_url,
                content_hash,
                json.dumps(metadata or {}, ensure_ascii=False),
                first_seen_at,
                now,
                last_scraped_at,
            ),
        )
        self.conn.commit()

    def get_entity(self, monitor_name: str, source_name: str, entity_key: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            """
            SELECT *
            FROM discovered_entities
            WHERE monitor_name = ? AND source_name = ? AND entity_key = ?
            """,
            (monitor_name, source_name, entity_key),
        ).fetchone()
        if not row:
            return None
        payload = dict(row)
        payload["metadata"] = json.loads(payload.pop("metadata_json") or "{}")
        return payload

    def entity_requires_refresh(
        self,
        *,
        monitor_name: str,
        source_name: str,
        entity_key: str,
        content_hash: str,
        stale_after_days: int,
    ) -> bool:
        row = self.get_entity(monitor_name, source_name, entity_key)
        if row is None:
            return True
        if content_hash and row.get("content_hash") != content_hash:
            return True
        last_scraped_at = row.get("last_scraped_at")
        if not last_scraped_at:
            return True
        try:
            parsed = datetime.fromisoformat(last_scraped_at)
        except Exception:
            return True
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed < (utc_now() - timedelta(days=stale_after_days))
