from __future__ import annotations

import unittest

from product_monitor.models import ProductCandidate
from product_monitor.parser import extract_product_candidates, parse_product_page, pick_balanced_candidates


class ProductMonitorTests(unittest.TestCase):
    def test_extract_intersport_product_candidates(self) -> None:
        html = """
        <html><body>
            <a href="/chaussure_running-test-p-111/">Chaussure Running Test</a>
            <div>4,6 étoiles 12 avis</div>
            <a href="/maillot-foot-test-p-222/">Maillot Foot Test</a>
            <div>8 avis</div>
        </body></html>
        """
        candidates = extract_product_candidates(
            html,
            brand_focus="intersport",
            category="running",
            source_url="https://www.intersport.fr/ope/sporting-days/running/",
        )
        self.assertEqual(len(candidates), 2)
        self.assertTrue(candidates[0].product_url.startswith("https://www.intersport.fr/"))

    def test_pick_balanced_candidates_caps_per_brand(self) -> None:
        candidates: list[ProductCandidate] = []
        for category in ("running", "cycling", "fitness", "outdoor", "football"):
            for index in range(6):
                candidates.append(
                    ProductCandidate(
                        brand_focus="intersport",
                        category=category,
                        product_url=f"https://example.com/{category}-{index}",
                        product_name=f"{category}-{index}",
                        review_count_hint=20 - index,
                    )
                )
        selected = pick_balanced_candidates(candidates, max_products_per_brand=20)
        self.assertEqual(len(selected), 20)
        counts = {}
        for row in selected:
            counts[row.category] = counts.get(row.category, 0) + 1
        self.assertTrue(all(value >= 4 for value in counts.values()))

    def test_parse_product_page_emits_product_partition(self) -> None:
        html = """
        <html><body>
            <script type="application/ld+json">
                {"@context":"https://schema.org","@type":"Product","aggregateRating":{"@type":"AggregateRating","ratingValue":"4.4","reviewCount":"18"}}
            </script>
            <h1>Chaussure Running Test</h1>
            <article>
                <h3>Confortable</h3>
                <span class="author">Alice</span>
                <time datetime="2026-03-10T10:00:00Z"></time>
                <span aria-label="5 étoiles"></span>
                <p>Très bonne paire, amorti propre et maintien correct sur route.</p>
            </article>
        </body></html>
        """
        candidate = ProductCandidate(
            brand_focus="intersport",
            category="running",
            product_url="https://example.com/product",
            product_name="Chaussure Running Test",
            discovery_source="https://example.com/category",
        )
        product, reviews, warning = parse_product_page(run_id="run1", candidate=candidate, html=html, fetch_mode="cloudflare")
        self.assertEqual(warning, "")
        self.assertEqual(product.source_partition, "product")
        self.assertEqual(product.aggregate_count, 18)
        self.assertEqual(reviews[0].source_partition, "product")


if __name__ == "__main__":
    unittest.main()
