# tiktok_monitor - run `20260318T101435630933Z_e9f12c`

## Scope

- brand: `decathlon`
- include_experimental: `false`
- duration_s: `211.3`
- videos: `5`
- video brands: `decathlon`=5
- pillars: `reputation`=5
- configured_sources: `6`
- enabled_sources: `3`
- source_statuses: `experimental`=3, `supported`=3

## Sources

| Brand | Source | Type | Pillar | Status | Enabled | Videos | Note |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| decathlon | decathlon_official_account | account | reputation | supported | yes | 5 | Official account extraction is the supported V1 production path. |
| decathlon | decathlon_tag | hashtag | reputation | experimental | no | 0 | Hashtag extraction remains experimental and is excluded from V1 production runs by default. |
| decathlon | rockrider_tag | hashtag | cx | experimental | no | 0 | Hashtag extraction remains experimental and is excluded from V1 production runs by default. |
| both | sportpascher_tag | hashtag | benchmark | experimental | no | 0 | Hashtag extraction remains experimental and is excluded from V1 production runs by default. |
| decathlon | decathlon_search | search | reputation | supported | yes | 0 | Playwright search for recent Decathlon mentions. |
| decathlon | decathlon_avis_search | search | cx | supported | yes | 0 | Playwright search for Decathlon customer reviews/opinions. |

## Warnings

- decathlon_search search failed: Page.goto: Target page, context or browser has been closed
Call log:
  - navigating to "https://www.tiktok.com/search/video?q=decathlon&t=1773829081", waiting until "domcontentloaded"

- decathlon_search: no search results found.
- decathlon_avis_search search failed: Page.goto: Target page, context or browser has been closed
- decathlon_avis_search: no search results found.
