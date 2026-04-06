"""Instagram monitor — scrapes public profiles via GraphQL API (no login required)."""
from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("instagram_monitor")

# ── Config ───────────────────────────────────────────────────
ACCOUNTS = {
    "decathlon": [
        {"username": "decathlon", "name": "Decathlon Global", "pillar": "reputation"},
    ],
    "intersport": [
        {"username": "intersportfr", "name": "Intersport France", "pillar": "reputation"},
    ],
}

HASHTAG_SEARCHES = {
    "decathlon": ["decathlon", "decathlonfrance", "rockrider", "quechua", "domyos"],
    "intersport": ["intersport", "intersportfrance"],
}

IG_APP_ID = "936619743392459"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"


# ── Models ───────────────────────────────────────────────────
@dataclasses.dataclass
class PostRecord:
    run_id: str
    brand_focus: str
    source_type: str  # account | hashtag
    query_name: str
    post_id: str
    post_url: str
    post_type: str  # GraphImage | GraphVideo | GraphSidecar
    caption: str
    author: str
    published_at: str
    like_count: int
    comment_count: int
    thumbnail_url: str
    is_video: bool
    video_view_count: int
    source_partition: str = "social"


# ── Fetch ────────────────────────────────────────────────────
import urllib.request
import urllib.error


def _fetch_json(url: str, headers: dict | None = None) -> dict:
    hdrs = {"User-Agent": USER_AGENT, "X-IG-App-ID": IG_APP_ID}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def fetch_profile_posts(username: str) -> tuple[list[dict], dict]:
    """Fetch recent posts from a public Instagram profile."""
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    data = _fetch_json(url)
    user = data.get("data", {}).get("user", {})
    edges = user.get("edge_owner_to_timeline_media", {}).get("edges", [])
    profile_info = {
        "username": user.get("username"),
        "full_name": user.get("full_name"),
        "followers": user.get("edge_followed_by", {}).get("count"),
        "following": user.get("edge_follow", {}).get("count"),
        "posts_count": user.get("edge_owner_to_timeline_media", {}).get("count"),
        "is_verified": user.get("is_verified"),
        "biography": user.get("biography"),
    }
    return [e["node"] for e in edges], profile_info


def fetch_hashtag_posts(tag: str) -> list[dict]:
    """Fetch recent posts from a public hashtag page."""
    url = f"https://www.instagram.com/api/v1/tags/web_info/?tag_name={tag}"
    try:
        data = _fetch_json(url)
        sections = data.get("data", {}).get("recent", {}).get("sections", [])
        posts = []
        for section in sections:
            for media in section.get("layout_content", {}).get("medias", []):
                node = media.get("media", {})
                if node:
                    posts.append(node)
        return posts
    except Exception as exc:
        log.warning("Hashtag #%s failed: %s", tag, exc)
        return []


def _extract_caption(node: dict) -> str:
    """Extract caption text from a post node (handles both API formats)."""
    # GraphQL format
    edges = node.get("edge_media_to_caption", {}).get("edges", [])
    if edges:
        return edges[0].get("node", {}).get("text", "")
    # v1 API format
    caption = node.get("caption", {})
    if isinstance(caption, dict):
        return caption.get("text", "")
    return ""


def _extract_post(node: dict, *, run_id: str, brand_focus: str, source_type: str, query_name: str) -> PostRecord:
    """Convert a raw Instagram node to PostRecord."""
    post_id = str(node.get("id") or node.get("pk") or "")
    shortcode = node.get("shortcode") or node.get("code") or ""
    caption = _extract_caption(node)
    is_video = node.get("is_video", False) or node.get("media_type") == 2

    # Likes
    like_count = (
        node.get("edge_liked_by", {}).get("count")
        or node.get("edge_media_preview_like", {}).get("count")
        or node.get("like_count")
        or 0
    )
    # Comments
    comment_count = (
        node.get("edge_media_to_comment", {}).get("count")
        or node.get("comment_count")
        or 0
    )
    # Timestamp
    ts = node.get("taken_at_timestamp") or node.get("taken_at") or 0
    published = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else ""

    # Thumbnail
    thumb = node.get("thumbnail_src") or node.get("display_url") or node.get("image_versions2", {}).get("candidates", [{}])[0].get("url", "")

    return PostRecord(
        run_id=run_id,
        brand_focus=brand_focus,
        source_type=source_type,
        query_name=query_name,
        post_id=post_id,
        post_url=f"https://www.instagram.com/p/{shortcode}/" if shortcode else "",
        post_type=node.get("__typename") or ("video" if is_video else "image"),
        caption=caption[:2000],
        author=node.get("owner", {}).get("username") or query_name,
        published_at=published,
        like_count=like_count,
        comment_count=comment_count,
        thumbnail_url=thumb[:500] if thumb else "",
        is_video=is_video,
        video_view_count=node.get("video_view_count") or 0,
    )


# ── Main ─────────────────────────────────────────────────────
def _write_jsonl(path: Path, records: list[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            payload = dataclasses.asdict(r) if dataclasses.is_dataclass(r) else r
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def run(
    *,
    brand: str = "both",
    output_dir: str = "data/instagram_runs",
) -> Path:
    t0 = time.time()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid.uuid4().hex[:6]
    run_dir = Path(output_dir) / run_id
    brands = ["decathlon", "intersport"] if brand == "both" else [brand]

    all_posts: list[PostRecord] = []
    seen_ids: set[str] = set()
    profiles: list[dict] = []

    for b in brands:
        # Phase 1: Official accounts
        for account in ACCOUNTS.get(b, []):
            username = account["username"]
            log.info("[%s] Fetching @%s...", b, username)
            try:
                nodes, profile = fetch_profile_posts(username)
                profiles.append(profile)
                for node in nodes:
                    post = _extract_post(node, run_id=run_id, brand_focus=b, source_type="account", query_name=username)
                    if post.post_id and post.post_id not in seen_ids:
                        seen_ids.add(post.post_id)
                        all_posts.append(post)
                log.info("[%s] @%s: %d posts, %s followers", b, username, len(nodes), profile.get("followers"))
            except Exception as exc:
                log.warning("[%s] @%s failed: %s", b, username, exc)
            time.sleep(2)

        # Phase 2: Hashtags
        for tag in HASHTAG_SEARCHES.get(b, []):
            log.info("[%s] Fetching #%s...", b, tag)
            try:
                nodes = fetch_hashtag_posts(tag)
                added = 0
                for node in nodes:
                    post = _extract_post(node, run_id=run_id, brand_focus=b, source_type="hashtag", query_name=f"#{tag}")
                    if post.post_id and post.post_id not in seen_ids:
                        seen_ids.add(post.post_id)
                        all_posts.append(post)
                        added += 1
                log.info("[%s] #%s: %d new posts", b, tag, added)
            except Exception as exc:
                log.warning("[%s] #%s failed: %s", b, tag, exc)
            time.sleep(2)

    # Export
    _write_jsonl(run_dir / "posts.jsonl", all_posts)
    _write_jsonl(run_dir / "profiles.jsonl", profiles)

    # Results markdown
    duration = time.time() - t0
    results = f"""# instagram_monitor - run `{run_id}`

## Scope
- brand: `{brand}`
- duration_s: `{duration:.1f}`
- posts: `{len(all_posts)}`
- profiles: `{len(profiles)}`
- dedup: `{len(seen_ids)}`

## Accounts
| Account | Followers | Posts fetched |
| --- | ---: | ---: |
"""
    for p in profiles:
        results += f"| @{p.get('username','')} | {p.get('followers',0):,} | 12 |\n"

    results += f"\n## Top posts by engagement\n\n| Author | Likes | Comments | Caption |\n| --- | ---: | ---: | --- |\n"
    for post in sorted(all_posts, key=lambda x: x.like_count, reverse=True)[:10]:
        results += f"| @{post.author} | {post.like_count:,} | {post.comment_count} | {post.caption[:60].replace('|',' ')} |\n"

    (run_dir / "results.md").write_text(results, encoding="utf-8")
    log.info("instagram_monitor done — %d posts in %.1fs → %s", len(all_posts), duration, run_dir)
    return run_dir


def _parse_args():
    parser = argparse.ArgumentParser(description="Instagram monitor for Decathlon/Intersport.")
    parser.add_argument("--brand", default="both", choices=["decathlon", "intersport", "both"])
    parser.add_argument("--output-dir", default="data/instagram_runs")
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
