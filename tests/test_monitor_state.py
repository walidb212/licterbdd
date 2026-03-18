from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from monitor_core.state import StateStore


class MonitorStateTests(unittest.TestCase):
    def test_record_item_is_incremental(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            state = StateStore(str(Path(tmp_dir) / "state.sqlite3"))
            first = state.record_item(
                monitor_name="review_monitor",
                source_name="trustpilot_decathlon",
                source_partition="customer",
                entity_key="decathlon",
                item_key="row-1",
                content_hash="hash-a",
                published_at="2026-03-12T10:00:00+00:00",
                metadata={},
            )
            second = state.record_item(
                monitor_name="review_monitor",
                source_name="trustpilot_decathlon",
                source_partition="customer",
                entity_key="decathlon",
                item_key="row-1",
                content_hash="hash-a",
                published_at="2026-03-12T10:00:00+00:00",
                metadata={},
            )
            changed = state.record_item(
                monitor_name="review_monitor",
                source_name="trustpilot_decathlon",
                source_partition="customer",
                entity_key="decathlon",
                item_key="row-1",
                content_hash="hash-b",
                published_at="2026-03-12T10:00:00+00:00",
                metadata={},
            )
            self.assertTrue(first)
            self.assertFalse(second)
            self.assertTrue(changed)
            state.close()

    def test_watermark_tracks_latest_published_at(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            state = StateStore(str(Path(tmp_dir) / "state.sqlite3"))
            state.update_watermark("review_monitor", "trustpilot_decathlon", "decathlon", "2026-03-10T10:00:00+00:00")
            state.update_watermark("review_monitor", "trustpilot_decathlon", "decathlon", "2026-03-09T10:00:00+00:00")
            state.update_watermark("review_monitor", "trustpilot_decathlon", "decathlon", "2026-03-12T10:00:00+00:00")
            self.assertEqual(
                state.get_watermark("review_monitor", "trustpilot_decathlon", "decathlon"),
                "2026-03-12T10:00:00+00:00",
            )
            state.close()

    def test_entity_requires_refresh_on_hash_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            state = StateStore(str(Path(tmp_dir) / "state.sqlite3"))
            state.upsert_entity(
                monitor_name="store_monitor",
                source_name="google_maps_reviews",
                entity_key="store-1",
                entity_name="Store 1",
                entity_url="https://example.com/store-1",
                content_hash="hash-a",
                metadata={},
                mark_scraped=True,
            )
            self.assertFalse(
                state.entity_requires_refresh(
                    monitor_name="store_monitor",
                    source_name="google_maps_reviews",
                    entity_key="store-1",
                    content_hash="hash-a",
                    stale_after_days=30,
                )
            )
            self.assertTrue(
                state.entity_requires_refresh(
                    monitor_name="store_monitor",
                    source_name="google_maps_reviews",
                    entity_key="store-1",
                    content_hash="hash-b",
                    stale_after_days=30,
                )
            )
            state.close()


if __name__ == "__main__":
    unittest.main()
