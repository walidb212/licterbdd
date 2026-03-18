from __future__ import annotations

import unittest

from review_monitor.models import SourceConfig
from review_monitor.parsers import (
    parse_custplace,
    parse_ebuyclub,
    parse_glassdoor,
    parse_indeed,
    parse_poulpeo,
    parse_trustpilot,
)
from review_monitor.sources import select_sources


class ReviewMonitorParserTests(unittest.TestCase):
    def test_parse_trustpilot_minimal_card(self) -> None:
        html = """
        <html><body>
            <script type="application/ld+json">{"@context":["https://schema.org"],"@graph":{"@type":"Dataset","mainEntity":{"csvw:tableSchema":{"csvw:columns":[{"csvw:name":"5 étoiles","csvw:cells":[{"csvw:value":"10"}]},{"csvw:name":"Total","csvw:cells":[{"csvw:value":"10"}]}]}}}}</script>
            <article>
                <span data-consumer-name-typography="true">Alice</span>
                <time data-service-review-date-time-ago="true" datetime="2026-03-01T10:00:00.000Z"></time>
                <img class="CDS_StarRating_starRating__614d2e" alt="Noté 5 sur 5 étoiles" />
                <p data-relevant-review-text-typography="true">Excellent service Voir plus</p>
            </article>
        </body></html>
        """
        source = SourceConfig("trustpilot_decathlon", "trustpilot", "decathlon", "customer", "https://example.com")
        summary, reviews = parse_trustpilot(html, "run1", source)
        self.assertEqual(summary.aggregate_count, 10)
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0].author, "Alice")
        self.assertEqual(reviews[0].rating, 5.0)

    def test_parse_custplace_minimal_card(self) -> None:
        html = """
        <html><head><title>Avis clients Decathlon - 117 avis - Custplace</title></head><body>
            <article class="topic-sample">
                <div class="aggregateRating s-4"></div>
                <h3><a href="/decathlon/test">Bon SAV</a></h3>
                <p class="mb-3">Service rapide en magasin.</p>
                <div class="flex items-center text-xs text-black">
                    <span><span>Par Martin</span></span>
                    <span>il y a 2 semaines</span>
                </div>
                <div class="text-xs text-black opacity-60"><span>Date d'expérience le 24/02/2026</span></div>
            </article>
        </body></html>
        """
        source = SourceConfig("custplace_decathlon", "custplace", "decathlon", "customer", "https://fr.custplace.com/decathlon")
        summary, reviews = parse_custplace(html, "run1", source)
        self.assertEqual(summary.aggregate_count, 117)
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0].title, "Bon SAV")
        self.assertEqual(reviews[0].rating, 4.0)

    def test_parse_glassdoor_jsonld_reviews(self) -> None:
        html = """
        <html><body>
            <script type="application/ld+json">{"@context":"https://schema.org/","@type":"EmployerAggregateRating","ratingValue":"3.3","ratingCount":"107"}</script>
            <script type="application/ld+json">[{"@context":"https://schema.org/","@type":"Review","reviewRating":{"@type":"Rating","ratingValue":"4"},"author":{"@type":"Person","name":"Employé - Vendeur"},"reviewBody":"Bonne formation"}]</script>
        </body></html>
        """
        source = SourceConfig("glassdoor_intersport", "glassdoor", "intersport", "employee", "https://example.com")
        summary, reviews = parse_glassdoor(html, "run1", source)
        self.assertEqual(summary.aggregate_rating, 3.3)
        self.assertEqual(summary.aggregate_count, 107)
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0].body, "Bonne formation")

    def test_parse_indeed_dom_review(self) -> None:
        html = """
        <html><body>
            <div data-testid="review">
                <h2>Bonne équipe</h2>
                <div data-testid="reviewText">Magasin bien organisé et bonne ambiance.</div>
                <span data-testid="author">Employé anonyme</span>
                <time>2026-03-10</time>
                <span aria-label="4 stars"></span>
            </div>
        </body></html>
        """
        source = SourceConfig("indeed_decathlon", "indeed", "decathlon", "employee", "https://example.com")
        summary, reviews = parse_indeed(html, "run1", source)
        self.assertEqual(summary.extracted_reviews, 1)
        self.assertEqual(reviews[0].title, "Bonne équipe")
        self.assertEqual(reviews[0].rating, 4.0)

    def test_parse_indeed_challenge_page_returns_no_reviews(self) -> None:
        html = """
        <html>
            <head><title>Security Check - Indeed.com</title></head>
            <body><h1>Verify you are human</h1></body>
        </html>
        """
        source = SourceConfig("indeed_decathlon", "indeed", "decathlon", "employee", "https://example.com")
        summary, reviews = parse_indeed(html, "run1", source)
        self.assertEqual(summary.extracted_reviews, 0)
        self.assertIsNone(summary.aggregate_count)
        self.assertTrue(summary.error)
        self.assertEqual(reviews, [])

    def test_parse_poulpeo_ignores_review_count_as_rating(self) -> None:
        html = """
        <html>
            <head><title>Avis Decathlon - 97 avis - Poulpeo</title></head>
            <body>
                <article>
                    <h3>Bon cashback</h3>
                    <p>Cashback bien reÃ§u.</p>
                    <span class="author">Julie</span>
                    <span class="date">2026-03-05</span>
                </article>
            </body>
        </html>
        """
        source = SourceConfig("poulpeo_decathlon", "poulpeo", "decathlon", "customer", "https://example.com")
        summary, reviews = parse_poulpeo(html, "run1", source)
        self.assertEqual(summary.aggregate_count, 97)
        self.assertIsNone(summary.aggregate_rating)
        self.assertEqual(len(reviews), 1)

    def test_parse_ebuyclub_scales_ten_point_rating(self) -> None:
        html = """
        <html><head><title>Decathlon - 5184 avis clients</title></head><body>
            <article>
                <h3>Livraison rapide</h3>
                <p>Commande reçue rapidement.</p>
                <span class="author">Camille</span>
                <span class="date">2026-03-05</span>
                <span class="note">10/10</span>
            </article>
        </body></html>
        """
        source = SourceConfig("ebuyclub_decathlon", "ebuyclub", "decathlon", "customer", "https://example.com")
        summary, reviews = parse_ebuyclub(html, "run1", source)
        self.assertEqual(summary.aggregate_count, 5184)
        self.assertEqual(reviews[0].rating, 5.0)

    def test_parse_ebuyclub_filters_coupon_rows(self) -> None:
        html = """
        <html><head><title>Intersport - 44 avis clients</title></head><body>
            <article>
                <h3>Pantalon</h3>
                <p>Produit conforme.</p>
                <span class="author">Sheila</span>
                <span class="date">Sheila , le 15.07.2023 , achat du 15.07.2023</span>
                <span class="note">10/10</span>
            </article>
            <article>
                <h3>26% de réduction sur une sélection</h3>
                <p>Expire le 30/12/2025</p>
                <span class="author">%</span>
            </article>
        </body></html>
        """
        source = SourceConfig("ebuyclub_intersport", "ebuyclub", "intersport", "customer", "https://example.com")
        summary, reviews = parse_ebuyclub(html, "run1", source)
        self.assertEqual(summary.extracted_reviews, 1)
        self.assertEqual(reviews[0].author, "Sheila")

    def test_select_sources_filters_scope(self) -> None:
        employee_sources = select_sources("all", "both", "employee")
        self.assertTrue(employee_sources)
        self.assertTrue(all(source.review_scope == "employee" for source in employee_sources))


if __name__ == "__main__":
    unittest.main()
