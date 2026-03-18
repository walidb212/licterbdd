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

    if brand in {"both", "decathlon"}:
        queries.extend(
            [
                QuerySpec(
                    name="decathlon_news",
                    brand_focus="decathlon",
                    query_text=f'"Decathlon" {freshness}',
                    rss_url=_build_rss_url(f'"Decathlon" {freshness}', language=language, region=region),
                ),
                QuerySpec(
                    name="decathlon_cx_news",
                    brand_focus="decathlon",
                    query_text=f'"Decathlon" (SAV OR "service client" OR retour OR remboursement OR magasin) {benchmark_freshness}',
                    rss_url=_build_rss_url(
                        f'"Decathlon" (SAV OR "service client" OR retour OR remboursement OR magasin) {benchmark_freshness}',
                        language=language,
                        region=region,
                    ),
                ),
            ]
        )

    if brand in {"both", "intersport"}:
        queries.extend(
            [
                QuerySpec(
                    name="intersport_news",
                    brand_focus="intersport",
                    query_text=f'"Intersport" {freshness}',
                    rss_url=_build_rss_url(f'"Intersport" {freshness}', language=language, region=region),
                ),
                QuerySpec(
                    name="intersport_cx_news",
                    brand_focus="intersport",
                    query_text=f'"Intersport" (SAV OR "service client" OR retour OR remboursement OR magasin) {benchmark_freshness}',
                    rss_url=_build_rss_url(
                        f'"Intersport" (SAV OR "service client" OR retour OR remboursement OR magasin) {benchmark_freshness}',
                        language=language,
                        region=region,
                    ),
                ),
            ]
        )

    if brand == "both":
        queries.append(
            QuerySpec(
                name="benchmark_news",
                brand_focus="both",
                query_text=f'("Decathlon" AND "Intersport") OR "Decathlon vs Intersport" OR "Decathlon ou Intersport" {benchmark_freshness}',
                rss_url=_build_rss_url(
                    f'("Decathlon" AND "Intersport") OR "Decathlon vs Intersport" OR "Decathlon ou Intersport" {benchmark_freshness}',
                    language=language,
                    region=region,
                ),
            )
        )

    return queries
