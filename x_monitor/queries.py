from __future__ import annotations

from .models import QuerySpec


def build_queries(
    brand: str,
    latest_count: int,
    latest_pages: int,
    top_count: int,
    top_pages: int,
) -> list[QuerySpec]:
    queries: list[QuerySpec] = []

    if brand in {"both", "decathlon"}:
        queries.extend(
            [
                QuerySpec(
                    name="decathlon_mentions_latest",
                    brand_focus="decathlon",
                    query_text='"Decathlon" OR "@Decathlon" OR "#Decathlon" -is:retweet',
                    search_type="latest",
                    count=latest_count,
                    pages=latest_pages,
                ),
                QuerySpec(
                    name="decathlon_mentions_top",
                    brand_focus="decathlon",
                    query_text='"Decathlon" OR "@Decathlon" OR "#Decathlon" -is:retweet',
                    search_type="top",
                    count=top_count,
                    pages=top_pages,
                ),
            ]
        )

    if brand in {"both", "intersport"}:
        queries.extend(
            [
                QuerySpec(
                    name="intersport_mentions_latest",
                    brand_focus="intersport",
                    query_text='"Intersport" OR "@Intersport" OR "#Intersport" -is:retweet',
                    search_type="latest",
                    count=latest_count,
                    pages=latest_pages,
                ),
                QuerySpec(
                    name="intersport_mentions_top",
                    brand_focus="intersport",
                    query_text='"Intersport" OR "@Intersport" OR "#Intersport" -is:retweet',
                    search_type="top",
                    count=top_count,
                    pages=top_pages,
                ),
            ]
        )

    return queries
