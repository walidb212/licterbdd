from __future__ import annotations

import os
import sys
from pathlib import Path

from monitor_core import load_workspace_env


def _normalize_encoding_name(value: str | None) -> str:
    if not value:
        return ""
    return value.replace("_", "-").lower()


def ensure_utf8_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        encoding = _normalize_encoding_name(getattr(stream, "encoding", ""))
        if encoding.startswith("utf-8"):
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8")
            except Exception:
                pass
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")


def main() -> int:
    ensure_utf8_console()
    load_workspace_env(Path(__file__).resolve().parent.parent)
    from .cli import main as cli_main

    return cli_main()
