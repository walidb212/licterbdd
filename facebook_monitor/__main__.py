"""Facebook monitor — scrapes groups + search via DrissionPage with saved cookies."""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("facebook_monitor")

COOKIES_PATH = Path(__file__).resolve().parent.parent / "data" / "fb_cookies.json"

# Groups to monitor
GROUPS = [
    {"id": "25042929842073061", "name": "Running Club France", "brand": "both"},
    {"id": "1723389974777498", "name": "DECATHLON", "brand": "decathlon"},
    {"id": "1113273562426921", "name": "Bref je fais du running", "brand": "both"},
]

# Search queries
SEARCHES = {
    "decathlon": ["decathlon france", "decathlon avis SAV"],
    "intersport": ["intersport france"],
}

DELAY_BETWEEN_PAGES = 4  # seconds — stay polite


def _safe_decode(text: str) -> str:
    try:
        return text.encode("utf-8", errors="replace").decode("unicode_escape", errors="replace").encode("utf-8", errors="replace").decode("utf-8", errors="replace")
    except Exception:
        return text


def _extract_posts(html: str) -> tuple[list[str], list[int], list[str]]:
    """Extract posts text, reactions, timestamps from Facebook relay store HTML."""
    texts = re.findall(r'"message":\{"text":"(.*?)"\}', html)
    reactions = [int(x) for x in re.findall(r'"reaction_count":\{"count":(\d+)', html)]
    timestamps = re.findall(r'"creation_time":(\d+)', html)
    return texts, reactions, timestamps


def run(
    *,
    brand: str = "both",
    output_dir: str = "data/facebook_runs",
) -> Path:
    t0 = time.time()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid.uuid4().hex[:6]
    run_dir = Path(output_dir) / run_id
    brands = ["decathlon", "intersport"] if brand == "both" else [brand]

    # Check cookies
    if not COOKIES_PATH.exists():
        log.error("No Facebook cookies found at %s. Log in manually first.", COOKIES_PATH)
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "results.md").write_text(f"# facebook_monitor - {run_id}\n\nNo cookies.\n", encoding="utf-8")
        return run_dir

    cookies = json.loads(COOKIES_PATH.read_text(encoding="utf-8"))

    # Launch browser
    from DrissionPage import ChromiumPage, ChromiumOptions
    co = ChromiumOptions()
    co.headless()
    co.set_argument("--no-sandbox")
    co.set_argument("--window-size=1280,900")

    page = None
    results = []

    try:
        page = ChromiumPage(co)

        # Load Facebook and set cookies
        page.get("https://www.facebook.com/")
        time.sleep(2)
        for c in cookies:
            try:
                page.set.cookies(c)
            except Exception:
                pass

        # Verify login
        page.get("https://www.facebook.com/")
        time.sleep(2)
        if "login" in page.url.lower():
            log.error("Not logged in — cookies expired. Re-login manually.")
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "results.md").write_text(f"# facebook_monitor - {run_id}\n\nCookies expired.\n", encoding="utf-8")
            return run_dir

        log.info("Logged in to Facebook")

        # Phase 1: Groups
        for group in GROUPS:
            if brand != "both" and group["brand"] not in (brand, "both"):
                continue
            log.info("[group] %s...", group["name"])
            page.get(f"https://www.facebook.com/groups/{group['id']}/")
            time.sleep(DELAY_BETWEEN_PAGES)

            html = page.html
            texts, reactions, timestamps = _extract_posts(html)
            log.info("[group] %s: %d posts", group["name"], len(texts))

            for i, t in enumerate(texts[:10]):
                text = _safe_decode(t)
                results.append({
                    "run_id": run_id,
                    "source": "fb_group",
                    "group_id": group["id"],
                    "group_name": group["name"],
                    "text": text[:1000],
                    "reactions": reactions[i] if i < len(reactions) else 0,
                    "timestamp": timestamps[i] if i < len(timestamps) else "",
                    "brand_focus": group["brand"] if "decathlon" in text.lower() or "intersport" in text.lower() else group["brand"],
                    "source_partition": "community",
                })

            time.sleep(DELAY_BETWEEN_PAGES)

        # Phase 2: Search
        for b in brands:
            for query in SEARCHES.get(b, []):
                log.info("[search] %s...", query)
                encoded = query.replace(" ", "%20")
                page.get(f"https://www.facebook.com/search/posts/?q={encoded}")
                time.sleep(DELAY_BETWEEN_PAGES + 1)  # Extra wait for search

                html = page.html
                texts, reactions, timestamps = _extract_posts(html)
                log.info("[search] '%s': %d posts", query, len(texts))

                for i, t in enumerate(texts[:15]):
                    text = _safe_decode(t)
                    results.append({
                        "run_id": run_id,
                        "source": "fb_search",
                        "query": query,
                        "text": text[:1000],
                        "reactions": reactions[i] if i < len(reactions) else 0,
                        "timestamp": timestamps[i] if i < len(timestamps) else "",
                        "brand_focus": b,
                        "source_partition": "social",
                    })

                time.sleep(DELAY_BETWEEN_PAGES)

    except Exception as exc:
        log.error("Facebook scraping failed: %s", exc)
    finally:
        if page:
            try:
                page.quit()
            except Exception:
                pass

    # Export
    run_dir.mkdir(parents=True, exist_ok=True)
    with (run_dir / "posts.jsonl").open("w", encoding="utf-8", errors="replace") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")

    # Results markdown
    duration = time.time() - t0
    group_count = sum(1 for r in results if r["source"] == "fb_group")
    search_count = sum(1 for r in results if r["source"] == "fb_search")
    md = f"""# facebook_monitor - run `{run_id}`

## Scope
- brand: `{brand}`
- duration_s: `{duration:.1f}`
- posts: `{len(results)}` (groups={group_count}, search={search_count})

## Groups
| Group | Posts |
| --- | ---: |
"""
    for g in GROUPS:
        count = sum(1 for r in results if r.get("group_id") == g["id"])
        md += f"| {g['name']} | {count} |\n"

    (run_dir / "results.md").write_text(md, encoding="utf-8")
    log.info("facebook_monitor done — %d posts in %.1fs -> %s", len(results), duration, run_dir)
    return run_dir


def _parse_args():
    parser = argparse.ArgumentParser(description="Facebook monitor for Decathlon/Intersport (groups + search).")
    parser.add_argument("--brand", default="both", choices=["decathlon", "intersport", "both"])
    parser.add_argument("--output-dir", default="data/facebook_runs")
    return parser.parse_args()


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    args = _parse_args()
    run(brand=args.brand, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
