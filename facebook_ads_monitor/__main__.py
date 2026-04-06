"""Facebook Ads Library monitor — scrapes Meta Ad Library for Decathlon/Intersport ads.

Uses the facebook-ads-scraper from apifybots (DrissionPage, no login required).
The Meta Ad Library is public by law (EU Digital Services Act).
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("facebook_ads_monitor")

# Add apifybots to path
APIFYBOTS_PATH = Path(__file__).resolve().parent.parent / ".." / "apifybots" / "facebook-ads-scraper"
if not APIFYBOTS_PATH.exists():
    APIFYBOTS_PATH = Path("c:/Users/walid/Desktop/DEV/apifybots/facebook-ads-scraper")

sys.path.insert(0, str(APIFYBOTS_PATH / "src"))

BRANDS = {
    "decathlon": {
        "search_terms": "Decathlon",
        "country": "FR",
        "name": "Decathlon France",
    },
    "intersport": {
        "search_terms": "Intersport",
        "country": "FR",
        "name": "Intersport France",
    },
}


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")


def run(
    *,
    brand: str = "both",
    max_ads: int = 20,
    output_dir: str = "data/facebook_ads_runs",
) -> Path:
    t0 = time.time()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid.uuid4().hex[:6]
    run_dir = Path(output_dir) / run_id
    brands = ["decathlon", "intersport"] if brand == "both" else [brand]

    try:
        from ads_scraper import scrape_facebook_ads
    except ImportError:
        log.error("Cannot import ads_scraper from apifybots. Make sure apifybots/facebook-ads-scraper exists.")
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "results.md").write_text(f"# facebook_ads_monitor - {run_id}\n\nImport error: ads_scraper not found\n", encoding="utf-8")
        return run_dir

    all_ads = []
    for b in brands:
        config = BRANDS[b]
        log.info("[%s] Scraping Meta Ad Library for '%s'...", b, config["search_terms"])
        try:
            ads, page_info = scrape_facebook_ads(
                search_terms=config["search_terms"],
                country=config["country"],
                max_results=max_ads,
                log_fn=lambda msg: log.info("[%s] %s", b, msg),
            )
            log.info("[%s] Found %d ads", b, len(ads))

            for ad in ads:
                ad["brand_focus"] = b
                ad["run_id"] = run_id
                ad["source_partition"] = "social"
                all_ads.append(ad)

        except Exception as exc:
            log.warning("[%s] Facebook Ads scraping failed: %s", b, exc)

        time.sleep(3)

    # Export
    _write_jsonl(run_dir / "ads.jsonl", all_ads)

    # Results markdown
    duration = time.time() - t0
    results = f"""# facebook_ads_monitor - run `{run_id}`

## Scope
- brand: `{brand}`
- duration_s: `{duration:.1f}`
- ads: `{len(all_ads)}`

## Ads by brand
| Brand | Ads found |
| --- | ---: |
"""
    for b in brands:
        count = sum(1 for a in all_ads if a.get("brand_focus") == b)
        results += f"| {b} | {count} |\n"

    if all_ads:
        results += "\n## Sample ads\n\n| Brand | Text | Start date |\n| --- | --- | --- |\n"
        for ad in all_ads[:10]:
            text = (ad.get("ad_text") or ad.get("body_text") or "")[:80].replace("|", " ")
            start = ad.get("start_date") or ad.get("started_running_on") or ""
            results += f"| {ad.get('brand_focus','')} | {text} | {start} |\n"

    (run_dir / "results.md").write_text(results, encoding="utf-8")
    log.info("facebook_ads_monitor done — %d ads in %.1fs → %s", len(all_ads), duration, run_dir)
    return run_dir


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Facebook Ads Library monitor for Decathlon/Intersport.")
    parser.add_argument("--brand", default="both", choices=["decathlon", "intersport", "both"])
    parser.add_argument("--max-ads", type=int, default=20)
    parser.add_argument("--output-dir", default="data/facebook_ads_runs")
    args = parser.parse_args()
    run(brand=args.brand, max_ads=args.max_ads, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
