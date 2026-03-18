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
- Scopes review: `customer`=143, `employee`=10, `promo`=60
- Brands review: `decathlon`=105, `intersport`=108

### Google Maps / stores

- Store statuses: `legacy_review_loaded`=39, `review_scraped`=1
- Store review brands: `decathlon`=1475

### Google News

- News brands: `both`=3, `decathlon`=21, `intersport`=19
- News signaux: `cx`=1, `general`=21, `product`=12, `sports_team`=3, `store_network`=6

### Reddit

- Reddit brands: `both`=1, `decathlon`=19, `intersport`=10
- Reddit subreddits: `AskIndia`=1, `AtinAtinLang`=1, `Austria`=1, `Budgetbikeriders`=1, `Decathlon`=3, `PHikingAndBackpacking`=1, `RepzHunter`=1, `asda`=1, `bangalore`=1, `cycling`=1, `deinfluencingPH`=1, `frankfurt`=1, `gravelcycling`=1, `graz`=1, `greece`=1, `hiking`=1, `india_cycling`=2, `indianrunners`=1, `kettlebell`=1, `laufen`=1, `luftablassen`=1, `outdoorgear`=1, `pune`=1, `singapore`=1, `skiing`=1, `verbraucherschutz`=1, `wien`=1

### YouTube

- YouTube brands: `decathlon`=11, `intersport`=7
- YouTube pillars: `benchmark`=3, `cx`=5, `reputation`=10
- YouTube source types: `channel`=4, `search`=14

### TikTok

- TikTok brands: `decathlon`=5, `intersport`=5
- TikTok pillars: `reputation`=10
- TikTok source types: `account`=10

### X

- X brands: `none`
- X search types: `none`

## Ce que tu as vraiment aujourd'hui

1. Un aggregateur unifie qui integre maintenant YouTube et TikTok en plus des blocs reviews, stores, news, Reddit et X.
2. Des partitions de sources separees, ce qui permet de construire un dashboard propre sans melanger des semantiques incompatibles.
3. Une lecture rapide des derniers runs disponibles, utile pour un point de situation avant ingestion Sheets ou Supabase.

## Priorites recommandees

1. Conserver `source_partition`, `brand_focus`, `entity_level` et `pillar` dans la base cible.
2. Ne pas additionner les signaux sociaux YouTube/TikTok avec les notes clients sans un traitement IA explicite.
3. Traiter les sources sociales comme de l'awareness / benchmark / verbatim, pas comme de la satisfaction client brute.
