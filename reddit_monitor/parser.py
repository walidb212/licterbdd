from __future__ import annotations

import re
from typing import Iterable
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from .models import CandidateLink, CommentRecord, PostRecord, Seed, SeedReport
from .relevance import (
    detect_brand_focus,
    score_candidate_relevance,
    score_post_relevance,
    should_filter_candidate,
    slug_to_title,
)


REDDIT_BASE_URL = "https://www.reddit.com"


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    match = re.search(r"-?\d+", str(value))
    return int(match.group(0)) if match else None


def normalize_reddit_post_url(url: str) -> str:
    parts = urlsplit(url)
    path_parts = [part for part in parts.path.split("/") if part]
    normalized_path = parts.path
    if len(path_parts) >= 4 and path_parts[0] == "r" and path_parts[2] == "comments":
        normalized_path = "/" + "/".join(path_parts[:4]) + "/"
    normalized = parts._replace(
        scheme="https",
        netloc="www.reddit.com",
        path=normalized_path,
        query="",
        fragment="",
    )
    return urlunsplit(normalized)


def extract_subreddit_from_url(url: str) -> str:
    parts = [part for part in urlsplit(url).path.split("/") if part]
    if len(parts) >= 2 and parts[0] == "r":
        return parts[1]
    return ""


def extract_title_hint_from_url(url: str) -> str:
    parts = [part for part in urlsplit(url).path.split("/") if part]
    if len(parts) >= 5 and parts[2] == "comments" and parts[4] != "comment":
        return slug_to_title(parts[4])
    return ""


def parse_seed_page(html: str, seed: Seed, max_posts_per_seed: int) -> tuple[list[CandidateLink], SeedReport]:
    soup = BeautifulSoup(html or "", "html.parser")
    report = SeedReport(
        seed_name=seed.name,
        seed_url=seed.url,
        brand_focus=seed.brand_focus,
        seed_type=seed.seed_type,
    )
    seen_urls: set[str] = set()
    candidates: list[CandidateLink] = []

    for anchor in soup.select("a[href*='/comments/']"):
        href = anchor.get("href")
        if not href:
            continue
        report.discovered_count += 1
        anchor_text = clean_text(anchor.get_text(" ", strip=True))
        if not anchor_text:
            report.blank_anchor_count += 1
        post_url = normalize_reddit_post_url(urljoin(REDDIT_BASE_URL, href))
        if post_url in seen_urls:
            report.duplicate_count += 1
            continue

        subreddit_hint = extract_subreddit_from_url(post_url)
        title_hint = anchor_text or extract_title_hint_from_url(post_url)
        if should_filter_candidate(anchor_text, title_hint, subreddit_hint, post_url):
            report.filtered_count += 1
            continue

        seen_urls.add(post_url)
        candidate = CandidateLink(
            post_url=post_url,
            seed_name=seed.name,
            seed_url=seed.url,
            seed_type=seed.seed_type,
            brand_focus=seed.brand_focus,
            anchor_text=anchor_text,
            title_hint=title_hint,
            subreddit_hint=subreddit_hint,
            candidate_relevance=score_candidate_relevance(anchor_text, title_hint, subreddit_hint, post_url),
        )
        candidates.append(candidate)
        if len(report.samples) < 3:
            report.samples.append(post_url)
        if len(candidates) >= max_posts_per_seed:
            break

    report.unique_count = len(candidates)
    return candidates, report


def _select_post_text_node(post_node) -> BeautifulSoup | None:
    return post_node.select_one("shreddit-post-text-body[slot='text-body'], [slot='text-body']")


def _select_comment_nodes(soup: BeautifulSoup) -> Iterable:
    return soup.select("shreddit-comment, faceplate-comment")


def parse_post_page(
    html: str,
    run_id: str,
    candidate: CandidateLink,
    max_comments_per_post: int,
) -> tuple[PostRecord | None, list[CommentRecord]]:
    soup = BeautifulSoup(html or "", "html.parser")
    post_node = soup.select_one("shreddit-post")
    if post_node is None:
        return None, []

    page_lang = clean_text((soup.html or {}).get("lang", "")) if soup.html else ""
    subreddit = clean_text(post_node.get("subreddit-name") or candidate.subreddit_hint)
    title = clean_text(post_node.get("post-title") or "")
    if not title and soup.title:
        title = clean_text(soup.title.get_text(" ", strip=True).split(": r/")[0])

    body_node = _select_post_text_node(post_node)
    body = clean_text(body_node.get_text(" ", strip=True) if body_node else "")
    brand_focus = detect_brand_focus(f"{title} {body}", candidate.brand_focus)
    language_raw = clean_text(post_node.get("post-language") or page_lang or "unknown")
    relevance_score = score_post_relevance(title, body, subreddit, brand_focus)

    post = PostRecord(
        run_id=run_id,
        brand_focus=brand_focus,
        seed_url=candidate.seed_url,
        seed_type=candidate.seed_type,
        post_url=candidate.post_url,
        subreddit=subreddit,
        post_title=title,
        post_text=body,
        author=clean_text(post_node.get("author") or ""),
        created_at=clean_text(post_node.get("created-timestamp") or ""),
        score=parse_int(post_node.get("score")),
        comment_count=parse_int(post_node.get("comment-count")),
        domain=clean_text(post_node.get("domain") or ""),
        language_raw=language_raw,
        relevance_score=relevance_score,
    )

    comments: list[CommentRecord] = []
    for index, comment_node in enumerate(_select_comment_nodes(soup), start=1):
        if len(comments) >= max_comments_per_post:
            break
        body_slot = comment_node.select_one("[slot='comment']")
        comment_text = clean_text(body_slot.get_text(" ", strip=True) if body_slot else "")
        if not comment_text:
            continue
        comments.append(
            CommentRecord(
                run_id=run_id,
                brand_focus=brand_focus,
                post_url=candidate.post_url,
                subreddit=subreddit,
                comment_index=index,
                comment_author=clean_text(comment_node.get("author") or ""),
                comment_text=comment_text,
                comment_score_raw=clean_text(comment_node.get("score") or ""),
                comment_meta_raw={
                    "created": clean_text(comment_node.get("created") or ""),
                    "depth": clean_text(comment_node.get("depth") or ""),
                    "permalink": normalize_reddit_post_url(
                        urljoin(REDDIT_BASE_URL, comment_node.get("permalink") or candidate.post_url)
                    ),
                    "aria_label": clean_text(
                        comment_node.get("arialabel")
                        or comment_node.get("aria-label")
                        or ""
                    ),
                },
                language_raw=language_raw,
            )
        )
    return post, comments
