from __future__ import annotations

import unittest

from reddit_monitor.models import CandidateLink, Seed
from reddit_monitor.parser import (
    normalize_reddit_post_url,
    parse_post_page,
    parse_seed_page,
)
from reddit_monitor.relevance import (
    detect_brand_focus,
    score_post_relevance,
    should_filter_candidate,
)


class RedditMonitorLogicTests(unittest.TestCase):
    def test_normalize_comment_permalink_to_post_permalink(self) -> None:
        url = "https://www.reddit.com/r/skiing/comments/1fxnao0/decathlon_vs_intersport/comment/lqqsyd4/?foo=bar"
        self.assertEqual(
            normalize_reddit_post_url(url),
            "https://www.reddit.com/r/skiing/comments/1fxnao0/",
        )

    def test_candidate_filter_blocks_academic_decathlon(self) -> None:
        self.assertTrue(
            should_filter_candidate(
                anchor_text="State academic decathlon results",
                title_hint="Academic Decathlon finals",
                subreddit_hint="AcademicDecathlon",
                url="https://www.reddit.com/r/AcademicDecathlon/comments/12345/finals/",
            )
        )

    def test_detect_brand_focus_handles_benchmark_threads(self) -> None:
        self.assertEqual(
            detect_brand_focus("Decathlon vs Intersport for ski gear", "decathlon"),
            "both",
        )

    def test_post_relevance_rewards_retail_context(self) -> None:
        score = score_post_relevance(
            title="Decathlon return policy changes",
            body="Customer service and refunds in store are getting worse.",
            subreddit="singapore",
            brand_focus="decathlon",
        )
        self.assertGreaterEqual(score, 0.35)

    def test_parse_seed_page_handles_blank_anchor_text(self) -> None:
        html = """
        <html><body>
            <a href="/r/skiing/comments/1fxnao0/decathlon_vs_intersport/"></a>
            <a href="/r/skiing/comments/1fxnao0/decathlon_vs_intersport/">Duplicate</a>
        </body></html>
        """
        seed = Seed("search_decathlon", "decathlon", "search", "https://example.com", "desc")
        candidates, report = parse_seed_page(html, seed, max_posts_per_seed=10)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(report.blank_anchor_count, 1)

    def test_parse_post_page_extracts_post_and_comment(self) -> None:
        html = """
        <html lang="en">
            <body>
                <shreddit-post
                    author="datagd"
                    created-timestamp="2024-10-06T18:31:19.458000+0000"
                    domain="self.skiing"
                    post-language="en"
                    post-title="Decathlon vs Intersport"
                    score="4"
                    comment-count="8"
                    subreddit-name="skiing"
                >
                    <shreddit-post-text-body slot="text-body">
                        Decathlon is cheaper, Intersport has better big-brand choice.
                    </shreddit-post-text-body>
                </shreddit-post>
                <shreddit-comment
                    author="Jaraxo"
                    created="2024-10-07T07:22:06.127000+0000"
                    depth="0"
                    permalink="/r/skiing/comments/1fxnao0/comment/lqqsyd4/"
                    score="5"
                >
                    <div slot="comment">Decathlon will be cheaper but lower quality.</div>
                </shreddit-comment>
            </body>
        </html>
        """
        candidate = CandidateLink(
            post_url="https://www.reddit.com/r/skiing/comments/1fxnao0/decathlon_vs_intersport/",
            seed_name="search_decathlon_vs_intersport",
            seed_url="https://www.reddit.com/search/?q=decathlon+vs+intersport",
            seed_type="search",
            brand_focus="both",
        )
        post, comments = parse_post_page(html, "run123", candidate, max_comments_per_post=20)
        self.assertIsNotNone(post)
        assert post is not None
        self.assertEqual(post.brand_focus, "both")
        self.assertEqual(post.subreddit, "skiing")
        self.assertEqual(post.score, 4)
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].comment_author, "Jaraxo")


if __name__ == "__main__":
    unittest.main()
