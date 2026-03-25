# AI batch enrichment - 20260325T082514410054Z_e9ce7a

## Execution

- provider: `mistral`
- model: `gpt-5-mini`
- social records: `4143`
- review records: `2019`
- news records: `87`
- entities summarized: `213`
- brand distribution: `both`=43, `decathlon`=4349, `intersport`=1857

## Input runs

- review: `data\review_runs\20260318T083831998034Z_45415a`
- store: `data\store_runs\20260318T154258227271Z_628005`
- product: `data\product_runs\20260312T140641173832Z_365232`
- news: `data\news_runs\20260318T131227880363Z_bedca3`
- reddit: `data\reddit_runs\20260318T083831999042Z_dcc59a`
- youtube: `data\youtube_runs\20260318T110843335283Z_cd1af6`
- tiktok: `data\tiktok_runs\20260318T112758457921Z_2140a9`
- x: `data\x_runs\20260318T092629071799Z_1938ba`
- global: `data\global_runs\20260312T171447444589Z_322ba7`

## Cross-source watchouts

- Top risks: `general_reputation_risk`=764, `brand_controversy`=309, `store_operations_issue`=261, `refund_friction`=140, `customer_service_issue`=45, `availability_risk`=23
- Top opportunities: `promo_engagement`=1223, `sport_category_interest`=105, `product_interest`=43, `brand_visibility_opportunity`=19, `community_momentum`=2

## Highest-priority items

| Partition | Brand | Entity | Priority | Sentiment | Summary |
| --- | --- | --- | ---: | --- | --- |
| social | decathlon | Erwan Aumont | 100 | negative | Décathlon a conquis le monde, et c'est une mauvaise nouvelle Décathlon a conquis le monde, et c'est une mauvaise nouvelle Avant de retourner chez décathlon, vous devriez regarder c |
| social | decathlon | reputation_crise | 100 | negative | Scandaleux, Decathlon qui tente de cacher 'Accident vélo défectueux'. Plus jamais je n'achète. #alerte |
| social | decathlon | reputation_crise | 100 | negative | Boycott total : Decathlon responsable de 'Accident vélo défectueux'. Je supprime mon compte. #crise |
| social | decathlon | reputation_crise | 100 | negative | Boycott total : Decathlon démasqué concernant 'Accident vélo défectueux'. N'y allez plus. #omg |
| social | decathlon | reputation_crise | 100 | negative | Scandale ! Decathlon démasqué concernant 'Accident vélo défectueux'. Partagez svp. #boycott |
| social | decathlon | reputation_crise | 100 | negative | Scandale ! Decathlon démasqué concernant 'Accident vélo défectueux'. Plus jamais je n'achète. #badbuzz |
| social | decathlon | reputation_crise | 100 | negative | Scandale ! Decathlon pris en flagrant délit de 'Accident vélo défectueux'. Retweetez en masse. #fail |
| social | decathlon | reputation_crise | 100 | negative | Urgent : Decathlon qui ne dit rien sur 'Accident vélo défectueux'. Faites passer le message. #boycott |

## Entity takeaways

- `decathlon` / `social` / `Decathlon`: 1469 items, dominant sentiment neutral. Main risks: general_reputation_risk, store_operations_issue, refund_friction. Main opportunities: promo_engagement. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `intersport` / `social` / `Intersport`: 1159 items, dominant sentiment neutral. Main risks: general_reputation_risk, store_operations_issue, refund_friction. Main opportunities: promo_engagement. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `decathlon` / `social` / `reputation_crise`: 767 items, dominant sentiment negative. Main risks: brand_controversy, general_reputation_risk. Main opportunities: promo_engagement. Top themes: general_brand_signal, brand_controversy, prix_promo.
- `decathlon` / `customer` / `App Store`: 378 items, dominant sentiment positive. Main risks: general_reputation_risk, store_operations_issue, refund_friction. Main opportunities: promo_engagement. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `decathlon` / `customer` / `Trustpilot`: 365 items, dominant sentiment positive. Main risks: general_reputation_risk, store_operations_issue, refund_friction. Main opportunities: promo_engagement. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `decathlon` / `customer` / `Avis Vérifiés`: 356 items, dominant sentiment positive. Main risks: general_reputation_risk, store_operations_issue, refund_friction. Main opportunities: promo_engagement. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `decathlon` / `customer` / `Google Maps`: 343 items, dominant sentiment positive. Main risks: general_reputation_risk, store_operations_issue, refund_friction. Main opportunities: promo_engagement. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `intersport` / `customer` / `Intersport France`: 136 items, dominant sentiment positive. Main risks: store_operations_issue, general_reputation_risk, availability_risk. Main opportunities: promo_engagement, sport_category_interest, product_interest. Top themes: magasin_experience, general_brand_signal, prix_promo.
- `decathlon` / `customer` / `Decathlon France`: 131 items, dominant sentiment negative. Main risks: general_reputation_risk, customer_service_issue, store_operations_issue. Main opportunities: promo_engagement, sport_category_interest, product_interest. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `intersport` / `social` / `INTERSPORT France`: 98 items, dominant sentiment neutral. Main risks: general_reputation_risk. Main opportunities: sport_category_interest, promo_engagement, brand_visibility_opportunity. Top themes: general_brand_signal, football_teamwear, prix_promo.
- `decathlon` / `social` / `india_cycling`: 61 items, dominant sentiment neutral. Main risks: general_reputation_risk, customer_service_issue, product_quality_risk. Main opportunities: promo_engagement, product_interest, sport_category_interest. Top themes: general_brand_signal, prix_promo, velo_mobilite.
- `decathlon` / `social` / `Decathlon United - Communication For Teammates`: 41 items, dominant sentiment neutral. Main opportunities: sport_category_interest, brand_visibility_opportunity. Top themes: general_brand_signal, football_teamwear, sponsoring_partnership.
- `decathlon` / `promo` / `Decathlon France`: 30 items, dominant sentiment neutral. Main opportunities: product_interest, sport_category_interest. Top themes: general_brand_signal, velo_mobilite, football_teamwear.
- `intersport` / `promo` / `Intersport France`: 30 items, dominant sentiment neutral. Main opportunities: sport_category_interest, brand_visibility_opportunity, product_interest. Top themes: football_teamwear, general_brand_signal, running_fitness.
- `decathlon` / `employee` / `Decathlon`: 25 items, dominant sentiment positive. Main risks: general_reputation_risk. Main opportunities: brand_visibility_opportunity, sport_category_interest. Top themes: general_brand_signal, sponsoring_partnership, running_fitness.
- `intersport` / `social` / `Austria`: 25 items, dominant sentiment neutral. Main opportunities: promo_engagement. Top themes: general_brand_signal, magasin_experience, prix_promo.
- `intersport` / `employee` / `Intersport France`: 25 items, dominant sentiment negative. Main risks: general_reputation_risk, store_operations_issue. Main opportunities: product_interest. Top themes: general_brand_signal, magasin_experience, velo_mobilite.
- `decathlon` / `social` / `AskPH`: 21 items, dominant sentiment neutral. Main opportunities: sport_category_interest, promo_engagement. Top themes: general_brand_signal, service_client, magasin_experience.
- `decathlon` / `social` / `AtinAtinLang`: 21 items, dominant sentiment positive. Main risks: general_reputation_risk. Main opportunities: promo_engagement, sport_category_interest. Top themes: general_brand_signal, prix_promo, running_fitness.
- `decathlon` / `social` / `Frugal_Ind`: 21 items, dominant sentiment neutral. Main opportunities: promo_engagement. Top themes: general_brand_signal, prix_promo, magasin_experience.

## Global Summary Context

# Synthese globale Decathlon / Intersport - 20260312T171447444589Z_322ba7

## Perimetre execute

- Reddit: `data\reddit_runs\20260312T111945018828Z`
- News: `data\news_runs\20260312T112238682538Z`
- Review: `data\review_runs\20260312T112256626986Z`
- Store: `data\store_runs\20260312T110837370718Z`
- Youtube: `data\youtube_runs\20260312T171216027508Z_bfebae`
- Tiktok: `data\tiktok_runs\20260312T170748398608Z_887bb0`
- X: non disponible

## Volumes par source

- Reddit: `30` posts, `168` commentaires
- Google News: `43` articles
- Review sites: `213` lignes d'avis
- Google Maps / stores: `1475` avis, `40` magasins
- YouTube: `18` videos, `39` commentaires
- TikTok: `10` videos
- X: `0` posts normalises

## Lecture executive

- Review sites: brands `decathlon`=105, `intersport`=108
- Stores: brands `decathlon`=1475
- News: brands `both`=3, `decathlon`=21, `intersport`=19
- Reddit: brands `both`=1, `decathlon`=19, `intersport`=10
- YouTube: pillars `benchmark`=3, `cx`=5, `reputation`=10
- TikTok: pillars `reputation`=10
- X: brands `none`

## Detail par bloc

### Review sites

- Sources review: `custplace`=40, `dealabs`=60, `ebuyclub`=4, `glassdoor`=10, `trustpilot`=99
- Scopes review:
