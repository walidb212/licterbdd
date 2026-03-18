from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from store_monitor.discovery import (
    _store_from_google_maps_candidate,
    build_intersport_google_maps_queries,
    load_legacy_decathlon_inventory,
    merge_store_lists,
)
from store_monitor.google_maps import load_legacy_google_maps_reviews


class StoreMonitorTests(unittest.TestCase):
    def test_loads_legacy_decathlon_inventory_from_misspelled_file(self) -> None:
        payload = {
            "magasins": [
                {
                    "nom": "Decathlon Test",
                    "adresse_complete": "1 rue Test, 75000, Paris",
                    "code_postal": "75000",
                    "ville": "Paris",
                    "google_maps": "https://maps.example/test",
                    "url_page": "https://example.com/store",
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            legacy_path = Path(tmp_dir) / "decatlhon_france.json"
            legacy_path.write_text(json.dumps(payload), encoding="utf-8")
            with patch("store_monitor.discovery.DECATHLON_CANONICAL_PATH", Path(tmp_dir) / "missing.json"), patch(
                "store_monitor.discovery.DECATHLON_LEGACY_PATH", legacy_path
            ):
                stores, warnings = load_legacy_decathlon_inventory("run1")
        self.assertEqual(len(stores), 1)
        self.assertIn("legacy inventory file", warnings[0])
        self.assertEqual(stores[0].store_name, "Decathlon Test")

    def test_loads_legacy_google_maps_reviews(self) -> None:
        payload = {
            "magasins": [
                {
                    "nom": "Decathlon Test",
                    "adresse": "1 rue Test, 75000, Paris",
                    "google_maps": "https://maps.example/test",
                    "note_globale": 4.3,
                    "nb_avis_total": 12,
                    "avis": [
                        {
                            "auteur": "Alice",
                            "note": 5,
                            "date": "il y a 2 jours",
                            "texte": "Très bien",
                        }
                    ],
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            reviews_path = Path(tmp_dir) / "decathlon_avis.json"
            reviews_path.write_text(json.dumps(payload), encoding="utf-8")
            with patch("store_monitor.google_maps.DECATHLON_LEGACY_REVIEWS_PATH", reviews_path):
                stores, reviews = load_legacy_google_maps_reviews("run1", "decathlon")
        self.assertEqual(len(stores), 1)
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0].aggregate_count, 12)
        self.assertEqual(reviews[0].entity_name, "Decathlon Test")

    def test_merge_store_lists_enriches_existing_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            payload = {
                "magasins": [
                    {
                        "nom": "Decathlon Test",
                        "adresse_complete": "",
                        "code_postal": "",
                        "ville": "",
                        "google_maps": "",
                        "url_page": "",
                    }
                ]
            }
            legacy_path = Path(tmp_dir) / "decatlhon_france.json"
            legacy_path.write_text(json.dumps(payload), encoding="utf-8")
            with patch("store_monitor.discovery.DECATHLON_CANONICAL_PATH", Path(tmp_dir) / "missing.json"), patch(
                "store_monitor.discovery.DECATHLON_LEGACY_PATH", legacy_path
            ):
                stores_a, _ = load_legacy_decathlon_inventory("run1")
        enriched = merge_store_lists(
            stores_a,
            [
                type(stores_a[0])(
                    run_id="run1",
                    brand_focus=stores_a[0].brand_focus,
                    store_name=stores_a[0].store_name,
                    store_url="https://example.com/store",
                    address="1 rue Test, 75000, Paris",
                    postal_code="75000",
                    city="Paris",
                    google_maps_url="https://maps.example/test",
                    discovery_source="manual",
                    status="legacy_review_loaded",
                )
            ],
        )
        self.assertEqual(len(enriched), 1)
        self.assertEqual(enriched[0].postal_code, "75000")
        self.assertEqual(enriched[0].status, "legacy_review_loaded")

    def test_builds_intersport_store_from_google_maps_candidate(self) -> None:
        store = _store_from_google_maps_candidate(
            "run1",
            "INTERSPORT PARIS REPUBLIQUE",
            "/maps/place/INTERSPORT+PARIS+REPUBLIQUE/data=!4m2!3m1!1s0x0:0x123",
        )
        self.assertIsNotNone(store)
        assert store is not None
        self.assertEqual(store.brand_focus, "intersport")
        self.assertEqual(store.discovery_source, "intersport_google_maps_search")
        self.assertTrue(store.google_maps_url.startswith("https://www.google.com/maps/place/"))

    def test_build_intersport_queries_from_city_seeds(self) -> None:
        queries = build_intersport_google_maps_queries(["Paris", "Lyon"])
        self.assertEqual(queries[0], "Intersport France")
        self.assertIn("Intersport Paris France", queries)
        self.assertIn("Intersport Lyon France", queries)


if __name__ == "__main__":
    unittest.main()
