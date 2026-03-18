# tiktok_monitor - run `20260318T100030354154Z_963262`

## Scope

- brand: `decathlon`
- include_experimental: `false`
- duration_s: `21.3`
- videos: `3`
- video brands: `decathlon`=3
- pillars: `reputation`=3
- configured_sources: `6`
- enabled_sources: `3`
- source_statuses: `experimental`=3, `supported`=3

## Sources

| Brand | Source | Type | Pillar | Status | Enabled | Videos | Note |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| decathlon | decathlon_official_account | account | reputation | supported | yes | 3 | Official account extraction is the supported V1 production path. |
| decathlon | decathlon_tag | hashtag | reputation | experimental | no | 0 | Hashtag extraction remains experimental and is excluded from V1 production runs by default. |
| decathlon | rockrider_tag | hashtag | cx | experimental | no | 0 | Hashtag extraction remains experimental and is excluded from V1 production runs by default. |
| both | sportpascher_tag | hashtag | benchmark | experimental | no | 0 | Hashtag extraction remains experimental and is excluded from V1 production runs by default. |
| decathlon | decathlon_search | search | reputation | supported | yes | 0 | Error: Missing TIKTOK_USERNAME / TIKTOK_PASSWORD in .env |
| decathlon | decathlon_avis_search | search | cx | supported | yes | 0 | Error: Missing TIKTOK_USERNAME / TIKTOK_PASSWORD in .env |

## Warnings

- Playwright search init failed: Missing TIKTOK_USERNAME / TIKTOK_PASSWORD in .env
