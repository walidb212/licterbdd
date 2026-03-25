# AI batch enrichment - 20260325T082536181904Z_dbbc41

## Execution

- provider: `mistral`
- model: `mistral-small-latest`
- social records: `4143`
- review records: `2019`
- news records: `96`
- entities summarized: `213`
- brand distribution: `both`=52, `decathlon`=4349, `intersport`=1857

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

- Top risks: `general_reputation_risk`=586, `brand_controversy`=275, `store_operations_issue`=167, `refund_friction`=106, `poor_customer_service`=45, `reputation_damage`=28
- Top opportunities: `promo_engagement`=963, `promo_visibility`=25, `product_visibility`=22, `staff_recognition`=20, `brand_visibility`=18, `product_availability`=18

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

- `decathlon` / `social` / `Decathlon`: 1469 items, dominant sentiment neutral. Main risks: general_reputation_risk, store_operations_issue, refund_friction. Main opportunities: promo_engagement, product_discussion, customer_satisfaction. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `intersport` / `social` / `Intersport`: 1159 items, dominant sentiment neutral. Main risks: general_reputation_risk, store_operations_issue, refund_friction. Main opportunities: promo_engagement, recommandation_positive, excellence_service. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `decathlon` / `social` / `reputation_crise`: 767 items, dominant sentiment negative. Main risks: brand_controversy, general_reputation_risk, reputation_damage. Main opportunities: promo_engagement. Top themes: general_brand_signal, brand_controversy, prix_promo.
- `decathlon` / `customer` / `App Store`: 378 items, dominant sentiment positive. Main risks: general_reputation_risk, store_operations_issue, refund_friction. Main opportunities: promo_engagement, satisfaction_client, maîtrise_rapport_qualité_prix. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `decathlon` / `customer` / `Trustpilot`: 365 items, dominant sentiment positive. Main risks: general_reputation_risk, store_operations_issue, refund_friction. Main opportunities: promo_engagement, satisfaction_client, fidélisation. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `decathlon` / `customer` / `Avis Vérifiés`: 356 items, dominant sentiment positive. Main risks: general_reputation_risk, store_operations_issue, refund_friction. Main opportunities: promo_engagement, fidélisation, fidélisation_client. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `decathlon` / `customer` / `Google Maps`: 343 items, dominant sentiment positive. Main risks: general_reputation_risk, store_operations_issue, refund_friction. Main opportunities: promo_engagement, satisfaction_client, fidélisation. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `intersport` / `customer` / `Intersport France`: 136 items, dominant sentiment positive. Main risks: poor_customer_service, service_failure, product_failure. Main opportunities: fast_delivery, delivery_speed_positive, competitive_pricing. Top themes: customer_service, product_quality, delivery_speed.
- `decathlon` / `customer` / `Decathlon France`: 131 items, dominant sentiment negative. Main risks: poor_customer_service, negative_word_of_mouth, product_defect. Main opportunities: customer_satisfaction, positive_customer_experience, cashback_engagement. Top themes: customer_service, product_quality, product_range.
- `intersport` / `social` / `INTERSPORT France`: 98 items, dominant sentiment positive. Main risks: price_perception_risk, customer_retention_risk, labor_practices. Main opportunities: brand_engagement, brand_awareness, community_building. Top themes: social_engagement, brand_engagement, zodiac_content.
- `decathlon` / `social` / `india_cycling`: 61 items, dominant sentiment neutral. Main risks: poor_customer_service, logistics_failure, component_downgrade. Main opportunities: price_competitiveness, educational_content, product_quality. Top themes: brand_mention, product_recommendation, product_mention.
- `decathlon` / `social` / `Decathlon United - Communication For Teammates`: 41 items, dominant sentiment positive. Main opportunities: positive_mentions, positive_engagement, brand_affinity. Top themes: general_brand_signal, brand_awareness, dare_program.
- `decathlon` / `promo` / `Decathlon France`: 30 items, dominant sentiment neutral. Main opportunities: promo_visibility, product_visibility, product_availability. Top themes: product_promo, product_mention, promo_listing.
- `intersport` / `promo` / `Intersport France`: 30 items, dominant sentiment neutral. Main opportunities: product_availability, promo_visibility, product_visibility. Top themes: product_promo, product_mention, brand_mention.
- `decathlon` / `employee` / `Decathlon`: 25 items, dominant sentiment positive. Main risks: low_compensation, management_issues, toxic_management. Main opportunities: positive_workplace, employee_satisfaction, positive_team_environment. Top themes: employee_experience, team_culture, employee_satisfaction.
- `intersport` / `social` / `Austria`: 25 items, dominant sentiment neutral. Main risks: negative_brand_perception, product_quality_concerns, shipping_restriction. Main opportunities: local_brand_mention, cross_border_shipping, local_food_positive_mention. Top themes: brand_mention, location_austria, shipping_service.
- `intersport` / `employee` / `Intersport France`: 25 items, dominant sentiment negative. Main risks: toxic_management, limited_benefits, turnover. Main opportunities: positive_employee_perception, strong_team_cohesion, training_quality. Top themes: management_issues, employee_experience, work_environment.
- `decathlon` / `social` / `AskPH`: 21 items, dominant sentiment neutral. Main risks: moderation_policy_change, moderation_automation, content_filtering. Main opportunities: employee_brand_image, employee_training_highlight, product_value_proposition. Top themes: community_moderation, karma_requirements, moderation_policy.
- `decathlon` / `social` / `AtinAtinLang`: 21 items, dominant sentiment positive. Main risks: trade_in_coordination_issue, application_rejection, staff_attitude. Main opportunities: employee_diversity, community_engagement, product_quality_positive. Top themes: employee_background, hiring_practices, customer_service.
- `decathlon` / `social` / `Frugal_Ind`: 21 items, dominant sentiment positive. Main risks: product_unused, product_bulky. Main opportunities: value_for_money_highlighted, product_quality_acknowledged, product_quality_highlight. Top themes: value_for_money, product_quality, product_usage_context.

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
