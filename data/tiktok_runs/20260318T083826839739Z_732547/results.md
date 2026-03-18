# tiktok_monitor - run `20260318T083826839739Z_732547`

## Scope

- brand: `both`
- include_experimental: `false`
- duration_s: `68.7`
- videos: `20`
- video brands: `decathlon`=10, `intersport`=10
- pillars: `reputation`=20
- configured_sources: `7`
- enabled_sources: `2`
- source_statuses: `experimental`=5, `supported`=2

## Sources

| Brand | Source | Type | Pillar | Status | Enabled | Videos | Note |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| decathlon | decathlon_official_account | account | reputation | supported | yes | 10 | Official account extraction is the supported V1 production path. |
| intersport | intersport_fr_official_account | account | reputation | supported | yes | 10 | Official account extraction is the supported V1 production path. |
| decathlon | decathlon_tag | hashtag | reputation | experimental | no | 0 | Hashtag extraction remains experimental and is excluded from V1 production runs by default. |
| intersport | intersport_tag | hashtag | reputation | experimental | no | 0 | Hashtag extraction remains experimental and is excluded from V1 production runs by default. |
| decathlon | rockrider_tag | hashtag | cx | experimental | no | 0 | Hashtag extraction remains experimental and is excluded from V1 production runs by default. |
| intersport | nakamura_tag | hashtag | cx | experimental | no | 0 | Hashtag extraction remains experimental and is excluded from V1 production runs by default. |
| both | sportpascher_tag | hashtag | benchmark | experimental | no | 0 | Hashtag extraction remains experimental and is excluded from V1 production runs by default. |
