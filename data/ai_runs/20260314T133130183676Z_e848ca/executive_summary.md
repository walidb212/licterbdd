# AI batch enrichment - 20260314T133130183676Z_e848ca

## Execution

- provider: `heuristic`
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

- Top risks: `general_reputation_risk`=9, `store_operations_issue`=7, `product_safety_risk`=3, `product_quality_risk`=2, `customer_service_issue`=2, `refund_friction`=2
- Top opportunities: `promo_engagement`=70, `sport_category_interest`=36, `product_interest`=21, `brand_visibility_opportunity`=9, `community_momentum`=1

## Highest-priority items

| Partition | Brand | Entity | Priority | Sentiment | Summary |
| --- | --- | --- | ---: | --- | --- |
| employee | decathlon | Decathlon | 100 | negative | A fuir... A fuir... Ayant tAvis : Data Engineer – Équipe Data Observability (Decathlon Digital) Je ne recommande pas de rejoindre cette équipe dans son état actuel. Le principal pr |
| employee | decathlon | Decathlon | 100 | negative | C'est inférieur C'est inférieur Quel est laspect le plus agréable dans le fait de travailler dans cette entreprise ? Le sal travaille ils sont pas corrects dans ce travail Quel est |
| employee | decathlon | Decathlon | 100 | negative | Ma pire expérience professionnelle Ma pire expérience professionnelle Jai travaill la bas pendant un mois, lt en 2022. Cela fut le pire mois de ma vie. Vous faites des tches rptiti |
| social | decathlon | Athlé Expliqué | 99 | negative | Boycott Decathlon 2025 : Les 3 raisons de la controverse Boycott Decathlon 2025 : Les 3 raisons de la controverse 🎙️ Boycott Decathlon 2025 : Les dessous d'un scandale qui secoue l |
| store | intersport | INTERSPORT - DAMMARIE LES LYS | 90 | negative | Je suis allé à intersport en région parisienne à dammarie, en me disant qu il serait bien mieux achalandé que ceux par chez moi j habite dans l aisne ,et bien non!!!!je suis venu a |
| store | intersport | INTERSPORT - DAMMARIE LES LYS | 90 | negative | Aujourd'hui intersport Dammarie les Lys. Je souhaite retourner un tuba acheté la semaine dernière et on refuse de me le reprendre pour cause d'hygiène. Mais j’ai bien dû l'essayer  |
| store | intersport | INTERSPORT - DAMMARIE LES LYS | 90 | negative | Des réflexions sur le sens des caisses!!! C'est inadmissible! Ce Monsieur a qui cela ne plaît pas, devrait plutôt revoir l'aménagement de son magasin, puisqu'apparemment je ne suis |
| store | intersport | INTERSPORT - DAMMARIE LES LYS | 90 | negative | Basket achetée en novembre 2023, en avril l’état est catastrophique, décoller le service client en ligne me demande de contacter le magasin pour un échange ou remboursement mais le |

## Entity takeaways

- `decathlon` / `employee` / `Decathlon`: 20 items, dominant sentiment positive. Main risks: general_reputation_risk. Main opportunities: sport_category_interest, brand_visibility_opportunity. Top themes: general_brand_signal, running_fitness, magasin_experience.
- `decathlon` / `social` / `india_cycling`: 15 items, dominant sentiment neutral. Main risks: product_safety_risk, general_reputation_risk. Main opportunities: promo_engagement, product_interest, sport_category_interest. Top themes: prix_promo, general_brand_signal, velo_mobilite.
- `decathlon` / `social` / `Decathlon`: 13 items, dominant sentiment neutral. Main risks: store_operations_issue, product_safety_risk. Main opportunities: promo_engagement. Top themes: general_brand_signal, magasin_experience, service_client.
- `both` / `social` / `skiing`: 9 items, dominant sentiment neutral. Main opportunities: promo_engagement. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `decathlon` / `social` / `AtinAtinLang`: 9 items, dominant sentiment positive. Main opportunities: promo_engagement, sport_category_interest. Top themes: prix_promo, running_fitness, general_brand_signal.
- `decathlon` / `social` / `PHikingAndBackpacking`: 9 items, dominant sentiment positive. Main opportunities: promo_engagement. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `decathlon` / `social` / `cycling`: 9 items, dominant sentiment neutral. Main opportunities: promo_engagement, product_interest, brand_visibility_opportunity. Top themes: prix_promo, general_brand_signal, velo_mobilite.
- `decathlon` / `social` / `deinfluencingPH`: 9 items, dominant sentiment neutral. Main opportunities: promo_engagement, sport_category_interest. Top themes: prix_promo, magasin_experience, general_brand_signal.
- `decathlon` / `social` / `hiking`: 9 items, dominant sentiment positive. Main opportunities: promo_engagement, sport_category_interest. Top themes: prix_promo, general_brand_signal, qualite_produit.
- `decathlon` / `social` / `outdoorgear`: 9 items, dominant sentiment neutral. Main opportunities: promo_engagement. Top themes: prix_promo, general_brand_signal, magasin_experience.
- `decathlon` / `social` / `pune`: 9 items, dominant sentiment positive. Main opportunities: promo_engagement. Top themes: general_brand_signal, qualite_produit, prix_promo.
- `decathlon` / `social` / `singapore`: 9 items, dominant sentiment neutral. Main risks: general_reputation_risk. Top themes: general_brand_signal, retour_remboursement, brand_controversy.
- `intersport` / `social` / `Austria`: 9 items, dominant sentiment neutral. Main opportunities: promo_engagement. Top themes: general_brand_signal, prix_promo.
- `intersport` / `social` / `frankfurt`: 9 items, dominant sentiment neutral. Main opportunities: promo_engagement, sport_category_interest. Top themes: magasin_experience, prix_promo, running_fitness.
- `intersport` / `social` / `laufen`: 9 items, dominant sentiment neutral. Main opportunities: sport_category_interest. Top themes: running_fitness, magasin_experience, general_brand_signal.
- `intersport` / `social` / `luftablassen`: 9 items, dominant sentiment neutral. Main risks: store_operations_issue. Main opportunities: promo_engagement, sport_category_interest. Top themes: general_brand_signal, prix_promo, magasin_experience.
- `decathlon` / `social` / `kettlebell`: 8 items, dominant sentiment neutral. Top themes: general_brand_signal, magasin_experience.
- `intersport` / `social` / `wien`: 8 items, dominant sentiment neutral. Main opportunities: promo_engagement, product_interest. Top themes: general_brand_signal, prix_promo, velo_mobilite.
- `decathlon` / `social` / `Budgetbikeriders`: 6 items, dominant sentiment neutral. Main risks: store_operations_issue, product_safety_risk. Main opportunities: promo_engagement, product_interest. Top themes: prix_promo, magasin_experience, velo_mobilite.
- `decathlon` / `social` / `Cleanrider`: 6 items, dominant sentiment positive. Main opportunities: product_interest, promo_engagement. Top themes: velo_mobilite, prix_promo, general_brand_signal.

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
