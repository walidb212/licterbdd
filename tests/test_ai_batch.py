from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


class AIBatchTests(unittest.TestCase):
    def test_run_batch_writes_expected_artifacts_with_heuristics(self) -> None:
        from ai_batch.app import run_batch_sync

        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            review_run = root / "review" / "run1"
            news_run = root / "news" / "run1"
            review_run.mkdir(parents=True)
            news_run.mkdir(parents=True)

            (review_run / "reviews.jsonl").write_text(
                json.dumps(
                    {
                        "brand_focus": "decathlon",
                        "source_partition": "customer",
                        "entity_name": "Decathlon France",
                        "author": "Alice",
                        "published_at": "2026-03-10T10:00:00+00:00",
                        "rating": 1.0,
                        "aggregate_rating": 1.7,
                        "aggregate_count": 2913,
                        "title": "Service nul",
                        "body": "Support client inefficace et remboursement impossible.",
                        "language_raw": "fr",
                        "source_url": "https://example.com/review",
                        "review_scope": "customer",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (news_run / "articles.jsonl").write_text(
                json.dumps(
                    {
                        "brand_focus": "intersport",
                        "source_name": "Frandroid",
                        "source_domain": "www.frandroid.com",
                        "article_id": "n1",
                        "article_title": "Intersport accelere sur le velo",
                        "description_text": "Une nouvelle offensive produit et prix dans le velo.",
                        "published_at": "2026-03-11T08:00:00+00:00",
                        "google_news_url": "https://news.google.com/rss/articles/n1",
                        "signal_type": "product",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = run_batch_sync(
                brand="both",
                output_dir=str(root / "ai"),
                provider="heuristic",
                review_run=str(review_run),
                news_run=str(news_run),
            )

            run_dir = Path(result.run_dir)
            self.assertTrue((run_dir / "social_enriched.jsonl").exists())
            self.assertTrue((run_dir / "review_enriched.jsonl").exists())
            self.assertTrue((run_dir / "news_enriched.jsonl").exists())
            self.assertTrue((run_dir / "entity_summary.jsonl").exists())
            self.assertTrue((run_dir / "executive_summary.md").exists())
            review_payload = (run_dir / "review_enriched.jsonl").read_text(encoding="utf-8")
            self.assertIn("sentiment_label", review_payload)
            self.assertIn("Decathlon France", review_payload)

    def test_tiktok_global_summary_to_ai_batch_chain(self) -> None:
        from ai_batch.app import run_batch_sync
        from global_summary.__main__ import build_global_summary
        from tiktok_monitor.__main__ import run as run_tiktok

        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            with patch("tiktok_monitor.__main__.TikTokExtractor") as extractor_cls:
                extractor = extractor_cls.return_value
                extractor.extract_source.return_value = [
                    {
                        "id": "123",
                        "webpage_url": "https://www.tiktok.com/@decathlon/video/123",
                        "title": "Decathlon video",
                        "description": "Concours communautaire super engageant.",
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
                    description="Concours communautaire super engageant.",
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
                tiktok_run = run_tiktok(brand="decathlon", max_items_per_source=1, output_dir=str(root / "tiktok"), quiet=True)

            global_summary = build_global_summary(output_dir=str(root / "global"), tiktok_run=str(tiktok_run))
            global_run = global_summary.parent
            ai_result = run_batch_sync(
                brand="decathlon",
                input_run="explicit",
                output_dir=str(root / "ai"),
                provider="heuristic",
                tiktok_run=str(tiktok_run),
                global_run=str(global_run),
            )
            executive_summary = Path(ai_result.run_dir) / "executive_summary.md"
            content = executive_summary.read_text(encoding="utf-8")
            self.assertIn("Decathlon video", content)
            self.assertIn("Global Summary Context", content)


if __name__ == "__main__":
    unittest.main()
