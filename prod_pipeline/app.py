from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from monitor_core import load_workspace_env


log = logging.getLogger("prod_pipeline")

# ── Styled console output ──────────────────────────────────
_R = "\033[0m"; _B = "\033[1m"; _D = "\033[2m"; _BOLD = _B; _DIM = _D
_GREEN = "\033[92m"; _RED = "\033[91m"; _YELLOW = "\033[93m"
_CYAN = "\033[96m"; _BLUE = "\033[94m"; _WHITE = "\033[97m"

_STEP_ICONS = {
    "store_monitor": "S", "review_monitor": "R", "news_monitor": "N",
    "reddit_monitor": "r", "youtube_monitor": "Y", "tiktok_monitor": "T",
    "x_monitor": "X", "context_monitor": "C", "product_monitor": "P",
    "global_summary": "G", "ai_batch": "A",
}

def _banner():
    print(f"\n{_CYAN}{_B}{'='*50}")
    print(f"  LICTER Brand Intelligence Pipeline")
    print(f"{'='*50}{_R}\n")

def _log_header(msg):
    print(f"{_CYAN}{_B}  {msg}{_R}")

def _log_step_start(name, idx, total):
    icon = _STEP_ICONS.get(name, "?")
    print(f"\n{_BLUE}{_B}  [{idx}/{total}] [{icon}] {name.upper()}{_R}")

def _log_step_done(name, result):
    icon = _STEP_ICONS.get(name, "?")
    if result.status == "ok":
        badge = f"{_GREEN}OK{_R}"
    elif result.status == "failed_optional":
        badge = f"{_YELLOW}SKIP{_R}"
    else:
        badge = f"{_RED}FAIL{_R}"
    print(f"  [{icon}] {badge} {name} {_D}{result.duration_s:.1f}s{_R} {result.output_run_dir or ''}")
    if result.error:
        print(f"  {_RED}  error: {result.error}{_R}")

def _log_summary(results, total_s):
    ok = sum(1 for r in results if r.status == "ok")
    fail = sum(1 for r in results if r.status == "failed")
    skip = sum(1 for r in results if r.status == "failed_optional")
    print(f"\n{_CYAN}{_B}{'='*50}")
    print(f"  PIPELINE COMPLETE")
    print(f"{'='*50}{_R}")
    print(f"  {_GREEN}{ok} OK{_R}  {_RED}{fail} FAIL{_R}  {_YELLOW}{skip} SKIP{_R}  {_D}in {total_s:.1f}s{_R}\n")


@dataclass(frozen=True)
class StepConfig:
    name: str
    module: str
    args: tuple[str, ...]
    timeout_s: int
    retries: int
    optional: bool = False


@dataclass
class StepResult:
    name: str
    status: str
    command: list[str]
    started_at: str
    completed_at: str
    duration_s: float
    exit_code: int
    output_run_dir: str
    stdout_path: str
    stderr_path: str
    optional: bool
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _latest_run_dir(base_dir: Path, primary_file: str | None = None) -> Path | None:
    if not base_dir.exists():
        return None
    candidates = [row for row in base_dir.iterdir() if row.is_dir()]
    if not candidates:
        return None
    if primary_file:
        with_primary = [row for row in candidates if (row / primary_file).exists()]
        if with_primary:
            return max(with_primary, key=lambda row: row.stat().st_mtime)
    return max(candidates, key=lambda row: row.stat().st_mtime)


_OUTPUT_ROOTS = {
    "store_monitor": (Path("data/store_runs"), "results.md"),
    "review_monitor": (Path("data/review_runs"), "results.md"),
    "news_monitor": (Path("data/news_runs"), "results.md"),
    "reddit_monitor": (Path("data/reddit_runs"), "results.md"),
    "youtube_monitor": (Path("data/youtube_runs"), "results.md"),
    "tiktok_monitor": (Path("data/tiktok_runs"), "results.md"),
    "x_monitor": (Path("data/x_runs"), "results.md"),
    "instagram_monitor": (Path("data/instagram_runs"), "results.md"),
    "context_monitor": (Path("data/context_runs"), "results.md"),
    "product_monitor": (Path("data/product_runs"), "results.md"),
    "global_summary": (Path("data/global_runs"), "global_summary.md"),
    "ai_batch": (Path("data/ai_runs"), "executive_summary.md"),
}


def _resolve_clix_bin(candidate: str) -> str:
    if candidate:
        return candidate
    default_bin = Path(".venv-x") / "Scripts" / "clix.exe"
    if default_bin.exists():
        return str(default_bin)
    return "clix"


def build_default_steps(*, brand: str, state_db: str, clix_bin: str) -> list[StepConfig]:
    return [
        StepConfig("store_monitor", "store_monitor", ("--brand", brand, "--stage", "all", "--incremental", "true", "--state-db", state_db, "--stale-after-days", "30"), 5400, 0),
        StepConfig("review_monitor", "review_monitor", ("--brand", brand, "--site", "all", "--scope", "all", "--incremental", "true", "--state-db", state_db), 3600, 0),
        StepConfig("news_monitor", "news_monitor", ("--brand", brand, "--days-back", "7", "--enrich-mode", "auto", "--max-enriched-items", "5"), 1800, 1),
        StepConfig("reddit_monitor", "reddit_monitor", ("--brand", brand), 3600, 0),
        StepConfig("youtube_monitor", "youtube_monitor", ("--brand", brand, "--max-search-results", "10"), 1800, 1),
        StepConfig("tiktok_monitor", "tiktok_monitor", ("--brand", brand, "--max-items-per-source", "10"), 1800, 1),
        StepConfig("instagram_monitor", "instagram_monitor", ("--brand", brand), 300, 0),
        StepConfig("x_monitor", "x_monitor", ("--brand", brand, "--clix-bin", clix_bin), 1800, 0, optional=True),
        StepConfig("context_monitor", "context_monitor", ("--brand", brand, "--document-types", "all", "--incremental", "true", "--state-db", state_db), 3600, 0),
        StepConfig("product_monitor", "product_monitor", ("--brand", brand, "--max-products-per-brand", "20", "--incremental", "true", "--state-db", state_db), 3600, 0, optional=True),
        StepConfig("global_summary", "global_summary", tuple(), 600, 0),
        StepConfig("ai_batch", "ai_batch", ("--brand", brand, "--input-run", "latest", "--provider", "auto"), 3600, 0),
    ]


def _select_steps(all_steps: list[StepConfig], selected_names: str) -> list[StepConfig]:
    if not selected_names or selected_names == "all":
        return all_steps
    wanted = {name.strip() for name in selected_names.split(",") if name.strip()}
    return [step for step in all_steps if step.name in wanted]


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _run_step(step: StepConfig, *, artifact_dir: Path, env: dict[str, str]) -> StepResult:
    started_at = datetime.now(timezone.utc).isoformat()
    stdout_path = artifact_dir / "steps" / f"{step.name}.stdout.log"
    stderr_path = artifact_dir / "steps" / f"{step.name}.stderr.log"
    command = [sys.executable, "-m", step.module, *step.args]
    output_root, primary_file = _OUTPUT_ROOTS[step.name]
    t0 = time.time()
    last_error = ""
    completed_process = None

    for attempt in range(step.retries + 1):
        try:
            completed_process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=step.timeout_s,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            last_error = f"timeout after {step.timeout_s}s"
            _write_text(stdout_path, exc.stdout or "")
            _write_text(stderr_path, (exc.stderr or "") + f"\n{last_error}\n")
            if attempt >= step.retries:
                break
            continue

        _write_text(stdout_path, completed_process.stdout or "")
        _write_text(stderr_path, completed_process.stderr or "")
        if completed_process.returncode == 0:
            last_error = ""
            break
        last_error = f"exit code {completed_process.returncode}"
        if attempt >= step.retries:
            break

    output_run = _latest_run_dir(output_root, primary_file=primary_file)
    status = "ok"
    exit_code = 0
    if completed_process is None or completed_process.returncode != 0 or last_error:
        status = "failed_optional" if step.optional else "failed"
        exit_code = completed_process.returncode if completed_process is not None else 1
    completed_at = datetime.now(timezone.utc).isoformat()
    return StepResult(
        name=step.name,
        status=status,
        command=command,
        started_at=started_at,
        completed_at=completed_at,
        duration_s=round(time.time() - t0, 2),
        exit_code=exit_code,
        output_run_dir=str(output_run) if output_run else "",
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
        optional=step.optional,
        error=last_error,
    )


# ── Parallel execution ───────────────────────────────────────
# Steps that can run in parallel (no dependencies between them)
_PARALLEL_GROUP = {
    "news_monitor", "reddit_monitor", "youtube_monitor",
    "tiktok_monitor", "x_monitor", "instagram_monitor", "context_monitor",
}
# Steps that MUST run after parallel group (depend on scraper outputs)
_SEQUENTIAL_AFTER = {"global_summary", "ai_batch"}
# Steps that are heavy and run alone (use browser, can't share)
_HEAVY_SEQUENTIAL = {"store_monitor", "review_monitor", "product_monitor"}


def _run_parallel_group(
    steps: list[StepConfig],
    *,
    artifact_dir: Path,
    env: dict[str, str],
) -> list[StepResult]:
    """Launch multiple steps in parallel using Popen, collect results."""
    if not steps:
        return []

    _log_header(f"PARALLEL — {len(steps)} scrapers simultanés")
    for s in steps:
        icon = _STEP_ICONS.get(s.name, "⚙️")
        print(f"  {_BLUE}▸{_R} {icon} {s.name}")

    t0 = time.time()
    processes: list[tuple[StepConfig, subprocess.Popen, float, Path, Path]] = []

    for step in steps:
        stdout_path = artifact_dir / "steps" / f"{step.name}.stdout.log"
        stderr_path = artifact_dir / "steps" / f"{step.name}.stderr.log"
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        command = [sys.executable, "-m", step.module, *step.args]
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        processes.append((step, proc, time.time(), stdout_path, stderr_path))

    # Wait for all to complete
    results: list[StepResult] = []
    for step, proc, step_t0, stdout_path, stderr_path in processes:
        try:
            stdout, stderr = proc.communicate(timeout=step.timeout_s)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            stderr = (stderr or "") + f"\ntimeout after {step.timeout_s}s\n"

        _write_text(stdout_path, stdout or "")
        _write_text(stderr_path, stderr or "")

        output_root, primary_file = _OUTPUT_ROOTS[step.name]
        output_run = _latest_run_dir(output_root, primary_file=primary_file)
        duration = round(time.time() - step_t0, 2)

        status = "ok"
        exit_code = proc.returncode
        error = ""
        if exit_code != 0:
            status = "failed_optional" if step.optional else "failed"
            error = f"exit code {exit_code}"

        result = StepResult(
            name=step.name,
            status=status,
            command=[sys.executable, "-m", step.module],
            started_at=datetime.fromtimestamp(step_t0, tz=timezone.utc).isoformat(),
            completed_at=datetime.now(timezone.utc).isoformat(),
            duration_s=duration,
            exit_code=exit_code,
            output_run_dir=str(output_run) if output_run else "",
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            optional=step.optional,
            error=error,
        )
        _log_step_done(step.name, result)
        results.append(result)

    total = round(time.time() - t0, 1)
    ok = sum(1 for r in results if r.status == "ok")
    print(f"\n  {_GREEN}{_BOLD}{ok}/{len(results)} OK{_R} {_DIM}in {total}s (parallel){_R}\n")

    return results


def run_pipeline(
    *,
    brand: str = "both",
    steps: str = "all",
    output_dir: str = "data/pipeline_runs",
    state_db: str = "data/state/monitor_state.sqlite3",
    clix_bin: str = "",
    continue_on_error: bool = False,
) -> tuple[int, Path]:
    load_workspace_env(Path(__file__).resolve().parent.parent)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid.uuid4().hex[:6]
    artifact_dir = Path(output_dir) / run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%H:%M:%S",
    )

    resolved_clix_bin = _resolve_clix_bin(clix_bin)
    selected_steps = _select_steps(build_default_steps(brand=brand, state_db=state_db, clix_bin=resolved_clix_bin), steps)
    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    pipeline_log_path = artifact_dir / "pipeline.log"

    _banner()
    _log_header(f"Run {run_id}  |  brand={brand}  |  {len(selected_steps)} steps")

    step_results: list[StepResult] = []
    required_failure = False
    pipeline_t0 = time.time()

    # Split into parallel vs sequential
    parallel_steps = [s for s in selected_steps if s.name in _PARALLEL_GROUP]
    heavy_steps = [s for s in selected_steps if s.name in _HEAVY_SEQUENTIAL]
    post_steps = [s for s in selected_steps if s.name in _SEQUENTIAL_AFTER]

    def _log_and_record(result):
        step_results.append(result)
        with pipeline_log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{result.completed_at} step={result.name} status={result.status} exit={result.exit_code} duration_s={result.duration_s:.2f}\n")

    # Phase 1: Heavy sequential (browser-based)
    for step in heavy_steps:
        _log_step_start(step.name, len(step_results) + 1, len(selected_steps))
        result = _run_step(step, artifact_dir=artifact_dir, env=env)
        _log_step_done(step.name, result)
        _log_and_record(result)
        if result.status == "failed" and not continue_on_error:
            required_failure = True
        if result.status == "failed":
            required_failure = True

    # Phase 2: Parallel scrapers (all at once)
    if parallel_steps and not (required_failure and not continue_on_error):
        parallel_results = _run_parallel_group(parallel_steps, artifact_dir=artifact_dir, env=env)
        for result in parallel_results:
            _log_and_record(result)
            if result.status == "failed":
                required_failure = True

    # Phase 3: Post-processing (needs scraper outputs)
    if not (required_failure and not continue_on_error):
        for step in post_steps:
            _log_step_start(step.name, len(step_results) + 1, len(selected_steps))
            result = _run_step(step, artifact_dir=artifact_dir, env=env)
            _log_step_done(step.name, result)
            _log_and_record(result)
            if result.status == "failed" and not continue_on_error:
                required_failure = True
                break
            if result.status == "failed":
                required_failure = True

    _log_summary(step_results, time.time() - pipeline_t0)

    report = {
        "run_id": run_id,
        "brand": brand,
        "artifact_dir": str(artifact_dir),
        "state_db": state_db,
        "steps": [row.to_dict() for row in step_results],
    }
    (artifact_dir / "pipeline_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (artifact_dir / "pipeline_report.md").write_text(
        "\n".join(
            [
                f"# Production pipeline - {run_id}",
                "",
                f"- brand: `{brand}`",
                f"- steps_executed: `{len(step_results)}`",
                "",
                "## Steps",
                "",
                "| Step | Status | Exit | Duration (s) | Output run |",
                "| --- | --- | ---: | ---: | --- |",
                *[
                    f"| {row.name} | {row.status} | {row.exit_code} | {row.duration_s:.2f} | {row.output_run_dir or '-'} |"
                    for row in step_results
                ],
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    exit_code = 1 if required_failure else 0
    return exit_code, artifact_dir
