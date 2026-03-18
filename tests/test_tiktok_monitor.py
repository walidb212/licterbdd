from __future__ import annotations

import dataclasses
import json
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch


class TikTokMonitorTests(unittest.TestCase):
    def test_normalize_video_fields(self) -> None:
        from tiktok_monitor.extractor import TikTokExtractor

        extractor = TikTokExtractor(quiet=True)
        record = extractor.normalize_video(
            {
                "id": "123",
                "webpage_url": "https://www.tiktok.com/@decathlon/video/123",
                "title": "Decathlon video",
                "description": "Desc",
                "uploader": "decathlon",
                "uploader_id": "@decathlon",
                "timestamp": 1709251200,
                "duration": 12,
                "view_count": 100,
                "like_count": 5,
                "comment_count": 2,
                "repost_count": 1,
                "save_count": 3,
                "thumbnail": "https://example.com/thumb.jpg",
            },
            run_id="r",
            brand_focus="decathlon",
            source_type="account",
            query_name="decathlon_official_account",
            query_text="https://www.tiktok.com/@decathlon",
            pillar="reputation",
            production_status="supported",
        )
        self.assertEqual(record.video_id, "123")
        self.assertEqual(record.brand_focus, "decathlon")
        self.assertEqual(record.source_partition, "social")
        self.assertEqual(record.view_count, 100)
        self.assertEqual(record.production_status, "supported")

    def test_select_sources(self) -> None:
        from tiktok_monitor.config import list_sources, select_sources

        decathlon_sources = select_sources("decathlon")
        self.assertTrue(all(row.production_status == "supported" for row in decathlon_sources))
        both_sources = list_sources("both")
        self.assertTrue(any(row.brand_focus == "both" for row in both_sources))
        self.assertTrue(any(row.production_status == "experimental" for row in both_sources))

    def test_run_writes_expected_files(self) -> None:
        from tiktok_monitor.__main__ import run

        with TemporaryDirectory() as tmp_dir:
            with patch("tiktok_monitor.__main__.TikTokExtractor") as extractor_cls:
                extractor = extractor_cls.return_value
                extractor.extract_source.return_value = [
                    {
                        "id": "123",
                        "webpage_url": "https://www.tiktok.com/@decathlon/video/123",
                        "title": "Decathlon video",
                        "description": "Desc",
                        "uploader": "decathlon",
                        "uploader_id": "@decathlon",
                        "timestamp": 1709251200,
                        "duration": 12,
                        "view_count": 100,
                        "like_count": 5,
                        "comment_count": 2,
                        "repost_count": 1,
                        "save_count": 3,
                        "thumbnail": "https://example.com/thumb.jpg",
                    }
                ]
                from tiktok_monitor.extractor import VideoRecord

                extractor.normalize_video.return_value = VideoRecord(
                    run_id="r",
                    brand_focus="decathlon",
                    source_type="account",
                    query_name="decathlon_official_account",
                    query_text="https://www.tiktok.com/@decathlon",
                    pillar="reputation",
                    production_status="supported",
                    video_id="123",
                    video_url="https://www.tiktok.com/@decathlon/video/123",
                    title="Decathlon video",
                    description="Desc",
                    author_name="decathlon",
                    author_id="@decathlon",
                    published_at="2025-03-01T00:00:00+00:00",
                    duration_seconds=12,
                    view_count=100,
                    like_count=5,
                    comment_count=2,
                    repost_count=1,
                    save_count=3,
                    thumbnail_url="https://example.com/thumb.jpg",
                )
                run_dir = run(brand="decathlon", max_items_per_source=1, output_dir=tmp_dir, quiet=True)
                self.assertTrue((run_dir / "videos.jsonl").exists())
                self.assertTrue((run_dir / "comments.jsonl").exists())
                self.assertTrue((run_dir / "sources.jsonl").exists())
                self.assertTrue((run_dir / "results.md").exists())
                payload = (run_dir / "videos.jsonl").read_text(encoding="utf-8")
                self.assertIn("Decathlon video", payload)
                sources_payload = (run_dir / "sources.jsonl").read_text(encoding="utf-8")
                self.assertIn("\"production_status\": \"supported\"", sources_payload)


if __name__ == "__main__":
    unittest.main()
