from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from x_monitor.app import _build_command, merge_tweets, normalize_tweet, run_monitor_sync
from x_monitor.models import NormalizedTweetRecord, QuerySpec
from x_monitor.queries import build_queries


def _sample_tweet(tweet_id: str = "t1", text: str = "Decathlon service client nul", **overrides) -> dict:
    tweet = {
        "id": tweet_id,
        "text": text,
        "created_at": "2026-03-11T10:00:00Z",
        "author_name": "Alice",
        "author_handle": "alice",
        "author_verified": True,
        "language": "fr",
        "tweet_url": f"https://x.com/alice/status/{tweet_id}",
        "conversation_id": "c1",
        "reply_to_id": "",
        "reply_to_handle": "",
        "engagement": {
            "likes": 10,
            "retweets": 3,
            "replies": 2,
            "quotes": 1,
            "views": 100,
        },
    }
    tweet.update(overrides)
    return tweet


class XMonitorQueryTests(unittest.TestCase):
    def test_build_queries_for_both_includes_benchmark(self) -> None:
        queries = build_queries("both", latest_count=50, latest_pages=2, top_count=25, top_pages=1)
        names = [query.name for query in queries]
        self.assertEqual(len(queries), 8)
        self.assertIn("benchmark_latest", names)
        self.assertIn("benchmark_top", names)

    def test_build_queries_for_single_brand_excludes_benchmark(self) -> None:
        queries = build_queries("decathlon", latest_count=50, latest_pages=2, top_count=25, top_pages=1)
        names = [query.name for query in queries]
        self.assertEqual(names, ["decathlon_mentions_latest", "decathlon_cx_latest", "decathlon_mentions_top"])

    def test_build_command_uses_expected_flags(self) -> None:
        spec = QuerySpec("decathlon_mentions_latest", "decathlon", '"Decathlon"', "latest", 50, 2)
        command = _build_command(spec, "clix")
        self.assertEqual(
            command,
            ["clix", "search", '"Decathlon"', "--type", "latest", "--count", "50", "--pages", "2", "--json"],
        )


class XMonitorNormalizationTests(unittest.TestCase):
    def test_normalize_tweet_defaults_and_reply(self) -> None:
        spec = QuerySpec("decathlon_cx_latest", "decathlon", '"Decathlon"', "latest", 50, 2)
        normalized = normalize_tweet(
            "run1",
            spec,
            _sample_tweet(reply_to_id="root1", reply_to_handle="brand_handle", engagement={}),
        )
        self.assertIsNotNone(normalized)
        assert normalized is not None
        self.assertEqual(normalized.post_type, "reply")
        self.assertEqual(normalized.rating, -1)
        self.assertEqual(normalized.sentiment, "")
        self.assertIsNone(normalized.user_followers)
        self.assertEqual(normalized.location, "")
        self.assertEqual(normalized.share_count, 0)

    def test_merge_tweets_aggregates_sources(self) -> None:
        left = NormalizedTweetRecord(
            run_id="run1",
            query_name="decathlon_mentions_latest",
            query_text="q1",
            search_type="latest",
            query_names=["decathlon_mentions_latest"],
            query_texts=["q1"],
            search_types=["latest"],
            brand_focus="decathlon",
            source_brand_focuses=["decathlon"],
            review_id="t1",
            platform="X",
            brand="decathlon",
            post_type="tweet",
            text="Decathlon",
            date="",
            rating=-1,
            likes=1,
            share_count=1,
            reply_count=0,
            quote_count=0,
            view_count=10,
            sentiment="",
            user_followers=None,
            is_verified=False,
            language="",
            location="",
            tweet_url="",
            author_name="",
            author_handle="",
            conversation_id="",
            reply_to_id="",
            reply_to_handle="",
        )
        right = NormalizedTweetRecord(
            run_id="run1",
            query_name="benchmark_top",
            query_text="q2",
            search_type="top",
            query_names=["benchmark_top"],
            query_texts=["q2"],
            search_types=["top"],
            brand_focus="both",
            source_brand_focuses=["both"],
            review_id="t1",
            platform="X",
            brand="both",
            post_type="reply",
            text="Decathlon ou Intersport",
            date="2026-03-11",
            rating=-1,
            likes=5,
            share_count=2,
            reply_count=1,
            quote_count=0,
            view_count=20,
            sentiment="",
            user_followers=None,
            is_verified=True,
            language="fr",
            location="",
            tweet_url="https://x.com/test/status/t1",
            author_name="Bob",
            author_handle="bob",
            conversation_id="c1",
            reply_to_id="r1",
            reply_to_handle="foo",
        )
        merged = merge_tweets(left, right)
        self.assertEqual(merged.brand, "both")
        self.assertEqual(merged.post_type, "reply")
        self.assertEqual(merged.likes, 5)
        self.assertIn("benchmark_top", merged.query_names)
        self.assertIn("top", merged.search_types)


class XMonitorIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.env_patcher = patch.dict(os.environ, {"X_AUTH_TOKEN": "token", "X_CT0": "ct0"}, clear=False)
        self.env_patcher.start()

    def tearDown(self) -> None:
        self.env_patcher.stop()

    def test_run_monitor_exports_files_with_mocked_clix(self) -> None:
        def fake_run(command, **kwargs):
            query = command[2]
            if "intersport" in query.lower() or "benchmark" in query.lower():
                payload = [_sample_tweet("t2", "Decathlon ou Intersport pour le vélo ?")]
            else:
                payload = [_sample_tweet("t1"), _sample_tweet("t1")]
            return type("Completed", (), {"returncode": 0, "stdout": json.dumps(payload), "stderr": ""})()

        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch("x_monitor.app._resolve_clix_bin", return_value="clix"), patch(
                "x_monitor.app.subprocess.run", side_effect=fake_run
            ), patch("x_monitor.app.time.sleep", return_value=None):
                result = run_monitor_sync(
                    brand="both",
                    latest_count=2,
                    latest_pages=1,
                    top_count=1,
                    top_pages=1,
                    output_dir=tmp_dir,
                    clix_bin="clix",
                    debug=False,
                )

            run_dir = Path(result.run_dir)
            self.assertTrue((run_dir / "queries.jsonl").exists())
            self.assertTrue((run_dir / "tweets_raw.jsonl").exists())
            self.assertTrue((run_dir / "tweets_normalized.jsonl").exists())
            self.assertTrue((run_dir / "results.md").exists())
            self.assertEqual(len(result.tweets), 2)

    def test_run_monitor_handles_invalid_json_and_rate_limit(self) -> None:
        call_index = {"value": 0}

        def fake_run(command, **kwargs):
            call_index["value"] += 1
            if call_index["value"] == 1:
                return type("Completed", (), {"returncode": 0, "stdout": "not-json", "stderr": ""})()
            if call_index["value"] == 2:
                return type("Completed", (), {"returncode": 1, "stdout": "", "stderr": "429 rate limit"})()
            return type("Completed", (), {"returncode": 0, "stdout": "[]", "stderr": ""})()

        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch("x_monitor.app._resolve_clix_bin", return_value="clix"), patch(
                "x_monitor.app.subprocess.run", side_effect=fake_run
            ), patch("x_monitor.app.time.sleep", return_value=None):
                result = run_monitor_sync(
                    brand="decathlon",
                    latest_count=1,
                    latest_pages=1,
                    top_count=1,
                    top_pages=1,
                    output_dir=tmp_dir,
                    clix_bin="clix",
                    debug=False,
                )
        self.assertEqual(len(result.tweets), 0)
        self.assertTrue(any("rate limit" in warning for warning in result.warnings))
        self.assertTrue(any("invalid JSON output" in warning for warning in result.warnings))

    def test_run_monitor_stops_on_auth_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(Exception, "Missing X auth cookies"):
                    run_monitor_sync(
                        brand="decathlon",
                        latest_count=1,
                        latest_pages=1,
                        top_count=1,
                        top_pages=1,
                        output_dir=tmp_dir,
                        clix_bin="clix",
                        debug=False,
                    )


if __name__ == "__main__":
    unittest.main()
