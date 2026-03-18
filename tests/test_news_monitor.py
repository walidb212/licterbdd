from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from news_monitor.app import run_monitor_sync
from news_monitor.parser import build_article_record, is_relevant_article, merge_article, parse_rss_feed
from news_monitor.queries import build_queries


SAMPLE_RSS = """
<rss version="2.0"><channel><title>Google News</title>
<item>
<title>Decathlon ouvre un nouveau magasin</title>
<link>https://news.google.com/rss/articles/a1</link>
<guid isPermaLink="false">a1</guid>
<pubDate>Thu, 12 Mar 2026 08:00:00 GMT</pubDate>
<description><![CDATA[<a href="https://news.google.com/rss/articles/a1">Decathlon ouvre un nouveau magasin</a>&nbsp;&nbsp;<font color="#6f6f6f">LSA</font>]]></description>
<source url="https://www.lsa-conso.fr">LSA</source>
</item>
<item>
<title>Decathlon ou Intersport : lequel choisir ?</title>
<link>https://news.google.com/rss/articles/a2</link>
<guid isPermaLink="false">a2</guid>
<pubDate>Thu, 12 Mar 2026 09:00:00 GMT</pubDate>
<description><![CDATA[<a href="https://news.google.com/rss/articles/a2">Decathlon ou Intersport : lequel choisir ?</a>&nbsp;&nbsp;<font color="#6f6f6f">Capital</font>]]></description>
<source url="https://www.capital.fr">Capital</source>
</item>
</channel></rss>
"""


class NewsMonitorParserTests(unittest.TestCase):
    def test_build_queries_for_both(self) -> None:
        queries = build_queries("both", language="fr", region="FR", days_back=7)
        names = [query.name for query in queries]
        self.assertEqual(len(queries), 5)
        self.assertIn("benchmark_news", names)

    def test_parse_rss_feed(self) -> None:
        title, items = parse_rss_feed(SAMPLE_RSS)
        self.assertEqual(title, "Google News")
        self.assertEqual(len(items), 2)

    def test_build_article_record_extracts_fields(self) -> None:
        spec = build_queries("decathlon", language="fr", region="FR", days_back=7)[0]
        _, items = parse_rss_feed(SAMPLE_RSS)
        article = build_article_record("run1", spec, items[0])
        self.assertEqual(article.article_id, "a1")
        self.assertEqual(article.source_name, "LSA")
        self.assertEqual(article.signal_type, "store_network")
        self.assertEqual(article.brand_detected, "decathlon")

    def test_sports_team_noise_is_not_relevant(self) -> None:
        sports_rss = """
        <rss version="2.0"><channel><title>Google News</title>
        <item>
        <title>Decathlon CMA CGM remporte une étape</title>
        <link>https://news.google.com/rss/articles/a3</link>
        <guid isPermaLink="false">a3</guid>
        <pubDate>Thu, 12 Mar 2026 08:00:00 GMT</pubDate>
        <description><![CDATA[<a href="https://news.google.com/rss/articles/a3">Decathlon CMA CGM remporte une étape</a>&nbsp;&nbsp;<font color="#6f6f6f">L'Équipe</font>]]></description>
        <source url="https://www.lequipe.fr">L'Équipe</source>
        </item>
        </channel></rss>
        """
        spec = build_queries("decathlon", language="fr", region="FR", days_back=7)[0]
        _, items = parse_rss_feed(sports_rss)
        article = build_article_record("run1", spec, items[0])
        self.assertEqual(article.signal_type, "sports_team")
        self.assertFalse(is_relevant_article(article))

    def test_merge_article_combines_queries(self) -> None:
        spec_a = build_queries("decathlon", language="fr", region="FR", days_back=7)[0]
        spec_b = build_queries("both", language="fr", region="FR", days_back=7)[-1]
        _, items = parse_rss_feed(SAMPLE_RSS)
        left = build_article_record("run1", spec_a, items[1])
        right = build_article_record("run1", spec_b, items[1])
        merged = merge_article(left, right)
        self.assertIn(spec_b.name, merged.query_names)
        self.assertIn("both", merged.source_brand_focuses)
        self.assertEqual(merged.signal_type, "benchmark")


class NewsMonitorIntegrationTests(unittest.TestCase):
    def test_run_monitor_exports_results(self) -> None:
        def fake_fetch(url: str) -> str:
            return SAMPLE_RSS

        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch("news_monitor.app._fetch_text", side_effect=fake_fetch):
                result = run_monitor_sync(
                    brand="both",
                    language="fr",
                    region="FR",
                    days_back=7,
                    max_items_per_query=5,
                    output_dir=tmp_dir,
                    enrich_mode="none",
                    max_enriched_items=0,
                )
            run_dir = Path(result.run_dir)
            self.assertTrue((run_dir / "queries.jsonl").exists())
            self.assertTrue((run_dir / "articles.jsonl").exists())
            self.assertTrue((run_dir / "results.md").exists())
            self.assertEqual(len(result.articles), 2)
            self.assertEqual(result.cloudflare_mode, "none")


if __name__ == "__main__":
    unittest.main()
