from __future__ import annotations

from reddit_monitor.bootstrap import ensure_utf8_console


def main() -> int:
    ensure_utf8_console()
    from .__main__ import main as cli_main

    cli_main()
    return 0
