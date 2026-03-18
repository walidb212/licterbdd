from __future__ import annotations

from reddit_monitor.bootstrap import ensure_utf8_console


def main() -> int:
    ensure_utf8_console()
    from .cli import main as cli_main

    return cli_main()
