from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from context_monitor.app import run_monitor_sync


class ContextMonitorTests(unittest.TestCase):
    def test_run_monitor_exports_context_partition(self) -> None:
        def fake_fetch_document(url: str) -> tuple[str, str]:
            return ("Titre Test\nConditions de retour et livraison.", "cloudflare_markdown")

        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch("context_monitor.app._fetch_document", side_effect=fake_fetch_document):
                result = run_monitor_sync(
                    brand="decathlon",
                    document_types="retours,livraison",
                    output_dir=tmp_dir,
                    incremental=False,
                    state_db=str(Path(tmp_dir) / "state.sqlite3"),
                    debug=False,
                )
            self.assertTrue(result.documents)
            self.assertTrue(all(row.source_partition == "context" for row in result.documents))
            self.assertTrue((Path(result.run_dir) / "documents.jsonl").exists())
            self.assertTrue((Path(result.run_dir) / "results.md").exists())


if __name__ == "__main__":
    unittest.main()
