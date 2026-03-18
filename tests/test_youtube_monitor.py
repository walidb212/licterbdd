from __future__ import annotations

import dataclasses
import json
import unittest
from unittest.mock import patch


class TestYouTubeExtractorNormalize(unittest.TestCase):
    def setUp(self) -> None:
        from youtube_monitor.extractor import YouTubeExtractor

        self.extractor = YouTubeExtractor(quiet=True)

    def _raw_video(self, **overrides) -> dict:
        base = {
            "id": "abc123",
            "title": "Test Decathlon velo",
            "description": "Avis sur le velo Decathlon",
            "webpage_url": "https://www.youtube.com/watch?v=abc123",
            "uploader": "TestChain",
            "channel_id": "UC_test",
            "channel_url": "https://www.youtube.com/@test",
            "upload_date": "20250301",
            "duration": 300,
            "view_count": 5000,
            "like_count": 200,
            "comment_count": 45,
            "thumbnail": "https://img.youtube.com/test.jpg",
            "tags": ["decathlon", "velo"],
            "language": "fr",
            "comments": [],
        }
        base.update(overrides)
        return base

    def test_normalize_video_fields(self) -> None:
        raw = self._raw_video()
        rec = self.extractor.normalize_video(
            raw,
            run_id="test_run",
            brand_focus="decathlon",
            source_type="search",
            query_name="crise_velo",
            query_text="Decathlon velo defectueux",
            pillar="reputation",
        )
        self.assertEqual(rec.video_id, "abc123")
        self.assertEqual(rec.title, "Test Decathlon velo")
        self.assertEqual(rec.view_count, 5000)
        self.assertEqual(rec.published_at, "2025-03-01T00:00:00+00:00")
        self.assertEqual(rec.source_partition, "social")
        self.assertEqual(rec.pillar, "reputation")
        self.assertEqual(rec.brand_focus, "decathlon")

    def test_normalize_video_missing_fields(self) -> None:
        rec = self.extractor.normalize_video(
            {"id": "xyz", "title": "No data"},
            run_id="r",
            brand_focus="intersport",
            source_type="channel",
            query_name="q",
            query_text="q",
            pillar="cx",
        )
        self.assertEqual(rec.view_count, 0)
        self.assertEqual(rec.like_count, 0)
        self.assertEqual(rec.description, "")
        self.assertEqual(rec.tags, [])

    def test_normalize_comments_top_level_and_reply(self) -> None:
        raw = self._raw_video(
            comments=[
                {
                    "id": "c1",
                    "parent": "root",
                    "author": "user1",
                    "text": "Super video!",
                    "timestamp": 1709251200,
                    "like_count": 10,
                },
                {
                    "id": "c2",
                    "parent": "c1",
                    "author": "user2",
                    "text": "Tout a fait d'accord",
                    "timestamp": 1709337600,
                    "like_count": 2,
                },
            ]
        )
        comments = self.extractor.normalize_comments(raw, run_id="r", brand_focus="decathlon", pillar="reputation")
        self.assertEqual(len(comments), 2)
        top_level = [row for row in comments if not row.is_reply]
        replies = [row for row in comments if row.is_reply]
        self.assertEqual(len(top_level), 1)
        self.assertEqual(len(replies), 1)
        self.assertEqual(replies[0].parent_id, "c1")
        self.assertEqual(comments[0].source_partition, "social")

    def test_dataclass_is_json_serializable(self) -> None:
        rec = self.extractor.normalize_video(
            self._raw_video(),
            run_id="r",
            brand_focus="decathlon",
            source_type="search",
            query_name="q",
            query_text="q",
            pillar="cx",
        )
        payload = json.dumps(dataclasses.asdict(rec), ensure_ascii=False)
        self.assertIn("abc123", payload)


class TestYouTubeConfig(unittest.TestCase):
    def test_search_queries_have_required_keys(self) -> None:
        from youtube_monitor.config import SEARCH_QUERIES

        for brand, queries in SEARCH_QUERIES.items():
            for query in queries:
                self.assertIn("name", query, f"Missing 'name' in {brand}")
                self.assertIn("query", query, f"Missing 'query' in {brand}")
                self.assertIn("pillar", query, f"Missing 'pillar' in {brand}")
                self.assertIn(query["pillar"], {"reputation", "benchmark", "cx"})

    def test_official_channels_have_required_keys(self) -> None:
        from youtube_monitor.config import OFFICIAL_CHANNELS

        for _, channels in OFFICIAL_CHANNELS.items():
            for channel in channels:
                self.assertIn("name", channel)
                self.assertIn("url", channel)
                self.assertIn("pillar", channel)
                self.assertIn("max_videos", channel)
                self.assertTrue(str(channel["url"]).startswith("https://"))

    def test_run_writes_expected_files(self) -> None:
        from tempfile import TemporaryDirectory

        from youtube_monitor.__main__ import run

        with TemporaryDirectory() as tmp_dir:
            with patch("youtube_monitor.__main__.YouTubeExtractor") as extractor_cls:
                extractor = extractor_cls.return_value
                extractor.search_videos.return_value = [
                    {
                        "id": "abc123",
                        "title": "Test video",
                        "webpage_url": "https://www.youtube.com/watch?v=abc123",
                        "comments": [],
                    }
                ]
                extractor.channel_videos.return_value = []
                from youtube_monitor.extractor import VideoRecord

                extractor.normalize_video.return_value = VideoRecord(
                    run_id="ignored",
                    brand_focus="decathlon",
                    source_type="search",
                    query_name="query",
                    query_text="query text",
                    pillar="reputation",
                    video_id="abc123",
                    video_url="https://www.youtube.com/watch?v=abc123",
                    title="Test video",
                    description="",
                    channel_name="channel",
                    channel_id="cid",
                    channel_url="https://www.youtube.com/@channel",
                    published_at="",
                    duration_seconds=0,
                    view_count=0,
                    like_count=0,
                    comment_count=0,
                    thumbnail_url="",
                    tags=[],
                    language="",
                )
                extractor.normalize_comments.return_value = []
                run_dir = run(brand="decathlon", max_search_results=1, max_comments=1, max_replies=1, max_channel_videos=1, output_dir=tmp_dir, quiet=True)
                self.assertTrue((run_dir / "videos.jsonl").exists())
                self.assertTrue((run_dir / "comments.jsonl").exists())
                self.assertTrue((run_dir / "results.md").exists())


if __name__ == "__main__":
    unittest.main()
