from __future__ import annotations

import os
import sys


POWERSHELL_UTF8_HINT = (
    "$env:PYTHONIOENCODING='utf-8'; "
    "$env:PYTHONUTF8='1'; "
    "python -m reddit_monitor"
)


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

    stdout_encoding = _normalize_encoding_name(getattr(sys.stdout, "encoding", ""))
    stderr_encoding = _normalize_encoding_name(getattr(sys.stderr, "encoding", ""))
    if stdout_encoding.startswith("utf-8") and stderr_encoding.startswith("utf-8"):
        os.environ.setdefault("PYTHONIOENCODING", "utf-8")
        os.environ.setdefault("PYTHONUTF8", "1")
        return

    message = (
        "UTF-8 console output is required on Windows for crawl4ai and rich.\n"
        "Run this in PowerShell, then retry:\n"
        f"{POWERSHELL_UTF8_HINT}"
    )
    raise SystemExit(message)


def main() -> int:
    ensure_utf8_console()
    from .cli import main as cli_main

    return cli_main()
