from __future__ import annotations

from urllib.parse import quote_plus

from .models import QuerySpec


def _build_rss_url(query: str, *, language: str, region: str) -> str:
    return (
        "https://news.google.com/rss/search?"
        f"q={quote_plus(query)}&hl={language}&gl={region}&ceid={region}:{language}"
    )


def build_queries(brand: str, *, language: str = "fr", region: str = "FR", days_back: int = 7) -> list[QuerySpec]:
    queries: list[QuerySpec] = []
    freshness = f"when:{days_back}d"
    benchmark_freshness = f"when:{max(days_back, 14)}d"

    # --- Priorité 1 : Crise & Réputation (Decathlon) ---
    if brand in {"both", "decathlon"}:
        queries.extend([
            QuerySpec(
                name="decathlon_crise_securite",
                brand_focus="decathlon",
                query_text=f'"Decathlon" (rappel OR accident OR "blessé" OR "défectueux" OR dangereux) {freshness}',
                rss_url=_build_rss_url(
                    f'"Decathlon" (rappel OR accident OR "blessé" OR "défectueux" OR dangereux) {freshness}',
                    language=language, region=region,
                ),
            ),
            QuerySpec(
                name="decathlon_bad_buzz",
                brand_focus="decathlon",
                query_text=f'"Decathlon" (boycott OR scandale OR "polémique" OR "grève" OR syndicat) {freshness}',
                rss_url=_build_rss_url(
                    f'"Decathlon" (boycott OR scandale OR "polémique" OR "grève" OR syndicat) {freshness}',
                    language=language, region=region,
                ),
            ),
            QuerySpec(
                name="decathlon_ethique",
                brand_focus="decathlon",
                query_text=f'"Decathlon" (Disclose OR "enquête" OR usine OR exploitation OR "éthique") {benchmark_freshness}',
                rss_url=_build_rss_url(
                    f'"Decathlon" (Disclose OR "enquête" OR usine OR exploitation OR "éthique") {benchmark_freshness}',
                    language=language, region=region,
                ),
            ),
        ])

    # --- Priorité 2 : Benchmark stratégique ---
    if brand in {"both", "intersport"}:
        queries.append(QuerySpec(
            name="intersport_expansion",
            brand_focus="intersport",
            query_text=f'"Intersport" ("Go Sport" OR rachat OR ouverture OR expansion OR magasin) {benchmark_freshness}',
            rss_url=_build_rss_url(
                f'"Intersport" ("Go Sport" OR rachat OR ouverture OR expansion OR magasin) {benchmark_freshness}',
                language=language, region=region,
            ),
        ))

    if brand == "both":
        queries.extend([
            QuerySpec(
                name="benchmark_financier",
                brand_focus="both",
                query_text=f'("Decathlon" OR "Intersport") ("parts de marché" OR "chiffre d\'affaires" OR résultats) {benchmark_freshness}',
                rss_url=_build_rss_url(
                    f'("Decathlon" OR "Intersport") ("parts de marché" OR "chiffre d\'affaires" OR résultats) {benchmark_freshness}',
                    language=language, region=region,
                ),
            ),
            QuerySpec(
                name="benchmark_comparatif",
                brand_focus="both",
                query_text=f'("Decathlon" AND "Intersport") OR "Decathlon vs Intersport" OR "Decathlon ou Intersport" {benchmark_freshness}',
                rss_url=_build_rss_url(
                    f'("Decathlon" AND "Intersport") OR "Decathlon vs Intersport" OR "Decathlon ou Intersport" {benchmark_freshness}',
                    language=language, region=region,
                ),
            ),
        ])

    # --- Priorité 3 : CX & Opérationnel ---
    if brand in {"both", "decathlon"}:
        queries.extend([
            QuerySpec(
                name="decathlon_cx_sav",
                brand_focus="decathlon",
                query_text=f'"Decathlon" (SAV OR "service client" OR retour OR remboursement) {benchmark_freshness}',
                rss_url=_build_rss_url(
                    f'"Decathlon" (SAV OR "service client" OR retour OR remboursement) {benchmark_freshness}',
                    language=language, region=region,
                ),
            ),
            QuerySpec(
                name="decathlon_cx_magasins",
                brand_focus="decathlon",
                query_text=f'"Decathlon" (fermeture OR ouverture OR rénovation OR magasin) {benchmark_freshness}',
                rss_url=_build_rss_url(
                    f'"Decathlon" (fermeture OR ouverture OR rénovation OR magasin) {benchmark_freshness}',
                    language=language, region=region,
                ),
            ),
        ])

    # --- Priorité 4 : Signaux faibles ---
    if brand in {"both", "decathlon"}:
        queries.append(QuerySpec(
            name="decathlon_partenariats",
            brand_focus="decathlon",
            query_text=f'"Decathlon" (Nike OR Adidas OR marque OR licence OR partenariat) {benchmark_freshness}',
            rss_url=_build_rss_url(
                f'"Decathlon" (Nike OR Adidas OR marque OR licence OR partenariat) {benchmark_freshness}',
                language=language, region=region,
            ),
        ))

    if brand == "both":
        queries.append(QuerySpec(
            name="sector_distribution",
            brand_focus="both",
            query_text=f'sport ("grande surface" OR distribution OR "sport 2000" OR "Go Sport") {benchmark_freshness}',
            rss_url=_build_rss_url(
                f'sport ("grande surface" OR distribution OR "sport 2000" OR "Go Sport") {benchmark_freshness}',
                language=language, region=region,
            ),
        ))

    return queries
