from __future__ import annotations

SEARCH_QUERIES: dict[str, list[dict[str, str]]] = {
    "decathlon": [
        {"name": "rep_velo_defectueux", "query": "Decathlon velo defectueux", "pillar": "reputation"},
        {"name": "rep_accident_velo", "query": "Decathlon accident velo", "pillar": "reputation"},
        {"name": "rep_boycott", "query": "boycott Decathlon", "pillar": "reputation"},
        {"name": "rep_scandale", "query": "Decathlon scandale", "pillar": "reputation"},
        {"name": "bench_vs_intersport", "query": "Decathlon vs Intersport", "pillar": "benchmark"},
        {"name": "bench_comparatif", "query": "Decathlon Intersport comparatif", "pillar": "benchmark"},
        {"name": "cx_avis", "query": "avis Decathlon 2025", "pillar": "cx"},
        {"name": "cx_sav", "query": "SAV Decathlon retour produit", "pillar": "cx"},
        {"name": "cx_qualite", "query": "test produit Decathlon qualite", "pillar": "cx"},
    ],
    "intersport": [
        {"name": "rep_avis", "query": "Intersport avis 2025", "pillar": "reputation"},
        {"name": "rep_probleme", "query": "Intersport probleme", "pillar": "reputation"},
        {"name": "bench_vs_decathlon", "query": "Intersport vs Decathlon", "pillar": "benchmark"},
        {"name": "cx_qualite", "query": "test produit Intersport qualite", "pillar": "cx"},
        {"name": "cx_sav", "query": "SAV Intersport retour", "pillar": "cx"},
    ],
}

OFFICIAL_CHANNELS: dict[str, list[dict[str, str | int]]] = {
    "decathlon": [
        {
            "name": "decathlon_global_official",
            "url": "https://www.youtube.com/channel/UCARu94_0J3Mu6cQMh9lMtXA",
            "pillar": "reputation",
            "max_videos": 20,
        },
    ],
    "intersport": [
        {
            "name": "intersport_france_official",
            "url": "https://www.youtube.com/channel/UCDS_mA4bqfkCp1OqoMh_lGA",
            "pillar": "reputation",
            "max_videos": 20,
        },
    ],
}

DEFAULT_SEARCH_RESULTS = 15
DEFAULT_MAX_COMMENTS = 100
DEFAULT_MAX_REPLIES = 10
SOURCE_PARTITION = "social"
