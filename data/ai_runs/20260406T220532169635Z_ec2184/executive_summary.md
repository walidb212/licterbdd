# AI batch enrichment - 20260406T220532169635Z_ec2184

## Execution

- provider: `heuristic`
- model: `gpt-4o-mini`
- social records: `3988`
- review records: `1913`
- news records: `101`
- entities summarized: `217`
- brand distribution: `both`=159, `decathlon`=4361, `intersport`=1482

## Input runs

- review: `data\review_runs\20260318T083831998034Z_45415a`
- store: `data\store_runs\20260406T204158629035Z_d083c3`
- product: `data\product_runs\20260406T211343302229Z_528915`
- news: `data\news_runs\20260406T211521325913Z_60ab24`
- reddit: `data\reddit_runs\20260406T211521896971Z_7f2def`
- youtube: `data\youtube_runs\20260406T211521192534Z_6de472`
- tiktok: `data\tiktok_runs\20260406T211521225575Z_0a7dab`
- x: `data\x_runs\20260406T211522247733Z_7e0528`
- global: `data\global_runs\20260406T212451681222Z_4bf7e6`

## Cross-source watchouts

- Top risks: `general_reputation_risk`=727, `brand_controversy`=305, `store_operations_issue`=216, `refund_friction`=130, `customer_service_issue`=32, `availability_risk`=23
- Top opportunities: `promo_engagement`=1157, `product_interest`=126, `sport_category_interest`=116, `brand_visibility_opportunity`=19, `community_momentum`=5

## Highest-priority items

| Partition | Brand | Entity | Priority | Sentiment | Summary |
| --- | --- | --- | ---: | --- | --- |
| social | decathlon | reputation_crise | 100 | negative | Scandaleux, Decathlon qui tente de cacher 'Accident vélo défectueux'. Plus jamais je n'achète. #alerte |
| social | decathlon | reputation_crise | 100 | negative | Boycott total : Decathlon responsable de 'Accident vélo défectueux'. Je supprime mon compte. #crise |
| social | decathlon | reputation_crise | 100 | negative | Boycott total : Decathlon démasqué concernant 'Accident vélo défectueux'. N'y allez plus. #omg |
| social | decathlon | reputation_crise | 100 | negative | Scandale ! Decathlon démasqué concernant 'Accident vélo défectueux'. Partagez svp. #boycott |
| social | decathlon | reputation_crise | 100 | negative | Scandale ! Decathlon démasqué concernant 'Accident vélo défectueux'. Plus jamais je n'achète. #badbuzz |
| social | decathlon | reputation_crise | 100 | negative | Scandale ! Decathlon pris en flagrant délit de 'Accident vélo défectueux'. Retweetez en masse. #fail |
| social | decathlon | reputation_crise | 100 | negative | Urgent : Decathlon qui ne dit rien sur 'Accident vélo défectueux'. Faites passer le message. #boycott |
| social | decathlon | reputation_crise | 100 | negative | Scandaleux, Decathlon qui fait face à 'Accident vélo défectueux'. Faites passer le message. #boycott |

## Entity takeaways

- `decathlon` / `social` / `Decathlon`: 1470 items, dominant sentiment neutral. Main risks: general_reputation_risk, store_operations_issue, refund_friction. Main opportunities: promo_engagement, product_interest, sport_category_interest. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `intersport` / `social` / `Intersport`: 1159 items, dominant sentiment neutral. Main risks: general_reputation_risk, store_operations_issue, refund_friction. Main opportunities: promo_engagement. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `decathlon` / `social` / `reputation_crise`: 767 items, dominant sentiment negative. Main risks: brand_controversy, general_reputation_risk. Main opportunities: promo_engagement. Top themes: general_brand_signal, brand_controversy, prix_promo.
- `decathlon` / `customer` / `App Store`: 378 items, dominant sentiment positive. Main risks: general_reputation_risk, store_operations_issue, refund_friction. Main opportunities: promo_engagement. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `decathlon` / `customer` / `Trustpilot`: 365 items, dominant sentiment positive. Main risks: general_reputation_risk, store_operations_issue, refund_friction. Main opportunities: promo_engagement. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `decathlon` / `customer` / `Avis Vérifiés`: 356 items, dominant sentiment positive. Main risks: general_reputation_risk, store_operations_issue, refund_friction. Main opportunities: promo_engagement. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `decathlon` / `customer` / `Google Maps`: 343 items, dominant sentiment positive. Main risks: general_reputation_risk, store_operations_issue, refund_friction. Main opportunities: promo_engagement. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `intersport` / `customer` / `Intersport France`: 136 items, dominant sentiment positive. Main risks: store_operations_issue, general_reputation_risk, availability_risk. Main opportunities: promo_engagement, sport_category_interest, product_interest. Top themes: magasin_experience, general_brand_signal, prix_promo.
- `decathlon` / `customer` / `Decathlon France`: 131 items, dominant sentiment negative. Main risks: general_reputation_risk, customer_service_issue, store_operations_issue. Main opportunities: promo_engagement, sport_category_interest, product_interest. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `decathlon` / `social` / `Transition Vélo`: 59 items, dominant sentiment neutral. Main risks: product_safety_risk. Main opportunities: product_interest, promo_engagement, brand_visibility_opportunity. Top themes: velo_mobilite, prix_promo, magasin_experience.
- `intersport` / `social` / `INTERSPORT France`: 41 items, dominant sentiment neutral. Main risks: product_quality_risk, store_operations_issue. Main opportunities: sport_category_interest, promo_engagement, brand_visibility_opportunity. Top themes: general_brand_signal, football_teamwear, running_fitness.
- `decathlon` / `promo` / `Decathlon France`: 30 items, dominant sentiment neutral. Main opportunities: product_interest, sport_category_interest. Top themes: general_brand_signal, velo_mobilite, football_teamwear.
- `decathlon` / `social` / `pedale`: 30 items, dominant sentiment neutral. Main risks: customer_service_issue, refund_friction. Main opportunities: promo_engagement, product_interest, sport_category_interest. Top themes: service_client, prix_promo, magasin_experience.
- `intersport` / `promo` / `Intersport France`: 30 items, dominant sentiment neutral. Main opportunities: sport_category_interest, brand_visibility_opportunity, product_interest. Top themes: football_teamwear, general_brand_signal, running_fitness.
- `decathlon` / `employee` / `Decathlon`: 25 items, dominant sentiment positive. Main risks: general_reputation_risk. Main opportunities: brand_visibility_opportunity, sport_category_interest. Top themes: general_brand_signal, sponsoring_partnership, running_fitness.
- `intersport` / `employee` / `Intersport France`: 25 items, dominant sentiment negative. Main risks: general_reputation_risk, store_operations_issue. Main opportunities: product_interest. Top themes: general_brand_signal, magasin_experience, velo_mobilite.
- `decathlon` / `social` / `onebag`: 20 items, dominant sentiment neutral. Main risks: product_quality_risk, store_operations_issue. Main opportunities: sport_category_interest, brand_visibility_opportunity. Top themes: general_brand_signal, magasin_experience, qualite_produit.
- `intersport` / `social` / `Les Echos`: 20 items, dominant sentiment neutral. Main opportunities: promo_engagement. Top themes: general_brand_signal, magasin_experience, retour_remboursement.
- `decathlon` / `social` / `france`: 19 items, dominant sentiment neutral. Main risks: refund_friction, availability_risk, brand_controversy. Main opportunities: promo_engagement, sport_category_interest, community_momentum. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `both` / `social` / `surfing`: 18 items, dominant sentiment neutral. Main risks: product_quality_risk. Main opportunities: promo_engagement, sport_category_interest. Top themes: general_brand_signal, prix_promo, qualite_produit.

## Global Summary Context

# Synthese globale Decathlon / Intersport - 20260406T212451681222Z_4bf7e6

## Perimetre execute

- Reddit: `data\reddit_runs\20260406T211521896971Z_7f2def`
- News: `data\news_runs\20260406T211521325913Z_60ab24`
- Review: `data\review_runs\20260318T083831998034Z_45415a`
- Store: `data\store_runs\20260406T204158629035Z_d083c3`
- Youtube: `data\youtube_runs\20260406T211521192534Z_6de472`
- Tiktok: `data\tiktok_runs\20260406T211521225575Z_0a7dab`
- X: `data\x_runs\20260406T211522247733Z_7e0528`

## Volumes par source

- Reddit: `80` posts, `309` commentaires
- Google News: `101` articles
- Review sites: `377` lignes d'avis
- Google Maps / stores: `0` avis, `0` magasins
- YouTube: `72` videos, `98` commentaires
- TikTok: `27` videos
- X: `35` posts normalises

## Lecture executive

- Review sites: brands `decathlon`=186, `intersport`=191
- Stores: brands `none`
- News: brands `both`=39, `decathlon`=47, `intersport`=15
- Reddit: brands `both`=14, `decathlon`=60, `intersport`=6
- YouTube: pillars `benchmark`=9, `cx`=7, `reputation`=56
- TikTok: pillars `reputation`=27
- X: brands `decathlon`=12, `intersport`=23

## Detail par bloc

### Review sites

- Sources review: `custplace`=40, `deal
