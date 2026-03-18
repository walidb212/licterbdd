# AI batch enrichment - 20260314T153443594082Z_bd1c44

## Execution

- provider: `openrouter`
- model: `gpt-5-mini`
- social records: `265`
- review records: `25`
- news records: `43`
- entities summarized: `86`
- brand distribution: `both`=12, `decathlon`=211, `intersport`=110

## Input runs

- review: `data\review_runs\20260312T134308094240Z_6bfa32`
- store: `data\store_runs\20260312T135150148029Z_9f2499`
- product: `data\product_runs\20260312T140641173832Z_365232`
- news: `data\news_runs\20260312T112238682538Z`
- reddit: `data\reddit_runs\20260312T111945018828Z`
- youtube: `data\youtube_runs\20260312T171216027508Z_bfebae`
- tiktok: `data\tiktok_runs\20260312T170748398608Z_887bb0`
- x: non disponible
- global: `data\global_runs\20260312T171447444589Z_322ba7`

## Cross-source watchouts

- Top risks: `reputational_risk`=7, `competitor_preference`=5, `margin_pressure`=3, `product_failure`=2, `customer_dissatisfaction`=2, `quality_uncertainty`=2
- Top opportunities: `positive_engagement`=4, `price_competitiveness`=3, `promote_value_message`=3, `size_guidance`=3, `product_improvement`=3, `competitive_pricing`=3

## Highest-priority items

| Partition | Brand | Entity | Priority | Sentiment | Summary |
| --- | --- | --- | ---: | --- | --- |
| social | decathlon | Disclose | 95 | negative | enquête Disclose (avec Cash Investigation) affirme que Decathlon profite d'un système de travail forcé en Chine ciblant des personnes ouïghoures ; plusieurs mises à jour documentée |
| social | decathlon | Disclose | 95 | positive | l'auteur affirme qu'il n'y a aucun lien avec le Xinjiang ou la Corée du Nord, accuse le journaliste de vouloir induire en erreur et qualifie l'enquête de 'fake news', défend implic |
| social | intersport | greece | 90 | negative | customer reports order estimated for tuesday-thursday but by friday it had not left the warehouse; phone support unhelpful, store contact numbers not provided and staff were rude. |
| social | decathlon | PHikingAndBackpacking | 90 | mixed | chaussures decathlon achetées ~2200 ont duré 2021–2025 avant que la semelle se décolle; utilisateur juge l'achat rentable. |
| social | decathlon | deinfluencingPH | 90 | negative | reports fabric feels weak and might tear easily. |
| social | decathlon | DECATHLON | 90 | positive | decathlon tutorial video explains how to change a vtt inner tube, lists tools and links to products and atelier services. |
| social | decathlon | Athlé Expliqué | 90 | negative | podcast détaille trois controverses touchant Decathlon : exploitation systémique en Asie, exportations vers la Russie via des circuits opaques, et polémique sur des équipements nau |
| social | decathlon | Disclose | 90 | negative | renvoi vers une vidéo intitulée «Decathlon : révélations sur le travail forcé des Ouïghours en Chine». |

## Entity takeaways

- `decathlon` / `employee` / `Decathlon`: 20 items, dominant sentiment positive. Main risks: unfulfilled_promises, toxic_management, recruiting_risk. Main opportunities: programmes_de_formation, positive_ambiance, talent_attraction. Top themes: formation, ambiance, workplace_culture.
- `decathlon` / `social` / `india_cycling`: 15 items, dominant sentiment positive. Main risks: competitor_comparison, product_feature_confusion, potential_bias_disclosed. Main opportunities: positive_brand_mention, educate_on_value_proposition, clarify_product_differences. Top themes: product_recommendation, price_value, brand_comparison.
- `decathlon` / `social` / `Decathlon`: 13 items, dominant sentiment neutral. Main risks: service_disruption, product_malfunction, negative_brand_experience. Main opportunities: provide_service_options, communicate_support_channels, assist_with_product_lookup. Top themes: product_identification, product_availability, competitor_mention.
- `both` / `social` / `skiing`: 9 items, dominant sentiment neutral. Main risks: negative_mention_decathlon_quality, intersport_price_premium, decathlon_mixed_quality. Main opportunities: local_store_guidance, targeted_recommendations, decathlon_budget_price_point. Top themes: product_quality, pricing, product_selection.
- `decathlon` / `social` / `AtinAtinLang`: 9 items, dominant sentiment positive. Main risks: payment_issue, missing_contact_details, staff_tone_perception. Main opportunities: highlight_customer_experience, promote_returns_policy, positive_pricing_perception. Top themes: customer_service, pricing, product_quality.
- `decathlon` / `social` / `PHikingAndBackpacking`: 9 items, dominant sentiment positive. Main risks: product_delamination, competitor_switch. Main opportunities: promote_value_message, size_guidance, provide_sizing_guidance. Top themes: price_value, use_case_hiking, product_durability.
- `decathlon` / `social` / `cycling`: 9 items, dominant sentiment neutral. Main risks: model_discontinuation, pricing_discontent, product_feature_gap. Main opportunities: emphasize_in_store_services, offer_specialist_adjustments, promote_value_offerings. Top themes: component_performance, component_preference, brand_marketing_cost.
- `decathlon` / `social` / `deinfluencingPH`: 9 items, dominant sentiment negative. Main risks: competition_from_unbranded, durability_concern, fit_concern. Main opportunities: encourage_try_in_store, encourage_user_reviews, share_product_experiences. Top themes: price_value, in_store_trial, alternative_purchase.
- `decathlon` / `social` / `hiking`: 9 items, dominant sentiment positive. Main risks: sizing_issues, quality_uncertainty, company_opacity. Main opportunities: provide_product_recommendations, highlight_specific_brands, regional_popularity. Top themes: product_quality, product_durability, competitor_mention.
- `decathlon` / `social` / `outdoorgear`: 9 items, dominant sentiment neutral. Main risks: product_quality_concern, sizing_inconsistency, premium_switch. Main opportunities: value_pricing_strength, share_product_reviews, highlight_homebrand_value. Top themes: value_for_money, product_quality, sizing_issues.
- `decathlon` / `social` / `pune`: 9 items, dominant sentiment mixed. Main risks: quality_uncertainty, quality_inconsistency, staining_discoloration. Main opportunities: provide_quality_information, share_lifespan_details, warranty_as_strength. Top themes: product_quality, product_durability, product_range.
- `decathlon` / `social` / `singapore`: 9 items, dominant sentiment negative. Main risks: return_policy_abuse, reputational_risk, negative_returns_policy_perception. Main opportunities: clarify_returns_policy, improve_policy_communication, policy_support. Top themes: return_policy_abuse, returns_policy, policy_change.
- `intersport` / `social` / `Austria`: 9 items, dominant sentiment negative. Main risks: reputational_risk, assortments_mismatch, customer_dissatisfaction. Main opportunities: diversify_product_colors, adjust_inventory, monitor_trend. Top themes: limited_color_variety, product_assortment_issue, surprise.
- `intersport` / `social` / `frankfurt`: 9 items, dominant sentiment neutral. Main risks: competitor_preference, negative_service_comment, negative_instore_experience. Main opportunities: consider_city_store_presence, showcase_flagship_store, service_improvement. Top themes: service_quality, competitor_recommendation, competitor_mention.
- `intersport` / `social` / `laufen`: 9 items, dominant sentiment neutral. Main risks: inconsistent_customer_experience, low_awareness_of_local_offers, variable_staff_expertise. Main opportunities: promote_in_store_expertise, address_rural_customer_needs, train_staff_specialization. Top themes: retail_advice_quality, purchase_decision, geographic_accessibility.
- `intersport` / `social` / `luftablassen`: 9 items, dominant sentiment negative. Main risks: staff_frustration, discount_pressure, service_devaluation. Main opportunities: highlight_expert_advice, loyalty_incentives, interest_in_discounts. Top themes: customer_behavior, retail_customer_advice, compensation_expectations.
- `decathlon` / `social` / `kettlebell`: 8 items, dominant sentiment positive. Main risks: competitor_mention, product_size_issue, fit_complaint. Main opportunities: product_improvement, promote_new_product, provide_usage_guidance. Top themes: product_quality, product_design_issue, alternative_brands.
- `intersport` / `social` / `wien`: 8 items, dominant sentiment neutral. Main risks: service_quality_concern, competitor_price_pressure. Main opportunities: promote_service_offerings, provide_local_store_info, brand_visibility. Top themes: snowboard_service, service_locations, service_pricing.
- `decathlon` / `social` / `Budgetbikeriders`: 6 items, dominant sentiment neutral. Main risks: product_degradation, customer_dissatisfaction, design_tradeoffs. Main opportunities: highlight_warranty_and_service, promote_entry_level_models, price_competitiveness. Top themes: product_comparison, value_assessment, beginner_purchase_advice.
- `decathlon` / `social` / `Cleanrider`: 6 items, dominant sentiment neutral. Main risks: competitive_pricing_pressure, product_competition, negative_experience. Main opportunities: product_marketing_visibility, pricing_response, product_visibility. Top themes: product_news, competitive_product_launch, bike_pricing.

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
