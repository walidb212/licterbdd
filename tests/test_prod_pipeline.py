from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


class ProdPipelineTests(unittest.TestCase):
    def test_run_pipeline_writes_report_and_uses_selected_steps(self) -> None:
        from prod_pipeline.app import run_pipeline

        with TemporaryDirectory() as tmp_dir:
            temp_root = Path(tmp_dir)
            output_roots = {
                "review_monitor": (temp_root / "review_runs", "results.md"),
                "global_summary": (temp_root / "global_runs", "global_summary.md"),
                "ai_batch": (temp_root / "ai_runs", "executive_summary.md"),
            }

            def fake_subprocess_run(command, **kwargs):
                module = command[2]
                output_root, marker = output_roots[module]
                run_dir = output_root / f"{module}_run"
                run_dir.mkdir(parents=True, exist_ok=True)
                (run_dir / marker).write_text("ok", encoding="utf-8")
                return type("Completed", (), {"returncode": 0, "stdout": f"{module} ok", "stderr": ""})()

            with patch("prod_pipeline.app.subprocess.run", side_effect=fake_subprocess_run), patch.dict(
                "prod_pipeline.app._OUTPUT_ROOTS",
                output_roots,
                clear=False,
            ):
                exit_code, artifact_dir = run_pipeline(
                    brand="both",
                    steps="review_monitor,global_summary,ai_batch",
                    output_dir=str(temp_root / "pipeline"),
                    continue_on_error=False,
                )

            self.assertEqual(exit_code, 0)
            report_path = artifact_dir / "pipeline_report.json"
            self.assertTrue(report_path.exists())
            self.assertTrue((artifact_dir / "pipeline.log").exists())
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual([row["name"] for row in report["steps"]], ["review_monitor", "global_summary", "ai_batch"])


if __name__ == "__main__":
    unittest.main()
