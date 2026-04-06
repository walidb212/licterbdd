from __future__ import annotations

SEARCH_QUERIES: dict[str, list[dict[str, str]]] = {
    "decathlon": [
        {"name": "rep_crise_velo", "query": "Decathlon velo accident defectueux", "pillar": "reputation"},
        {"name": "rep_scandale", "query": "Decathlon scandale boycott", "pillar": "reputation"},
        {"name": "bench_vs_intersport", "query": "Decathlon vs Intersport", "pillar": "benchmark"},
        {"name": "cx_avis_sav", "query": "avis Decathlon SAV retour", "pillar": "cx"},
        {"name": "cx_qualite", "query": "test produit Decathlon qualite", "pillar": "cx"},
    ],
    "intersport": [
        {"name": "rep_avis", "query": "Intersport avis probleme", "pillar": "reputation"},
        {"name": "bench_vs_decathlon", "query": "Intersport vs Decathlon", "pillar": "benchmark"},
        {"name": "cx_sav", "query": "SAV Intersport qualite retour", "pillar": "cx"},
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
DEFAULT_DATE_FILTER = "month"  # hour, today, week, month, year, or "" for no filter
DEFAULT_MAX_CHANNEL_SHORTS = 20
SOURCE_PARTITION = "social"
