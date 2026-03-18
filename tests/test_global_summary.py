from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class GlobalSummaryTests(unittest.TestCase):
    def test_build_global_summary_includes_youtube_and_tiktok(self) -> None:
        from global_summary.__main__ import build_global_summary

        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            youtube_run = root / "youtube" / "run1"
            tiktok_run = root / "tiktok" / "run1"
            youtube_run.mkdir(parents=True)
            tiktok_run.mkdir(parents=True)

            (youtube_run / "videos.jsonl").write_text(
                json.dumps({"brand_focus": "decathlon", "pillar": "reputation", "source_type": "account"}) + "\n",
                encoding="utf-8",
            )
            (youtube_run / "comments.jsonl").write_text("", encoding="utf-8")
            (tiktok_run / "videos.jsonl").write_text(
                json.dumps({"brand_focus": "intersport", "pillar": "reputation", "source_type": "account"}) + "\n",
                encoding="utf-8",
            )

            summary_path = build_global_summary(
                output_dir=str(root / "global"),
                youtube_run=str(youtube_run),
                tiktok_run=str(tiktok_run),
            )
            content = summary_path.read_text(encoding="utf-8")
            self.assertIn("YouTube", content)
            self.assertIn("TikTok", content)
            self.assertIn("decathlon", content)
            self.assertIn("intersport", content)


if __name__ == "__main__":
    unittest.main()
