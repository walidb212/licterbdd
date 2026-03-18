# Synthese globale Decathlon / Intersport - 20260312T170239896061Z_166b0f

## Perimetre execute

- Reddit: `data\reddit_runs\20260312T111945018828Z`
- News: `data\news_runs\20260312T112238682538Z`
- Review: `data\review_runs\20260312T134446071711Z_329efe`
- Store: `data\store_runs\20260312T135150148029Z_9f2499`
- Youtube: `data\youtube_runs\20260312T165258911440Z_48d46a`
- Tiktok: non disponible
- X: non disponible

## Volumes par source

- Reddit: `30` posts, `168` commentaires
- Google News: `43` articles
- Review sites: `0` lignes d'avis
- Google Maps / stores: `5` avis, `1` magasins
- YouTube: `6` videos, `5` commentaires
- TikTok: `0` videos
- X: `0` posts normalises

## Lecture executive

- Review sites: brands `none`
- Stores: brands `intersport`=5
- News: brands `both`=3, `decathlon`=21, `intersport`=19
- Reddit: brands `both`=1, `decathlon`=19, `intersport`=10
- YouTube: pillars `benchmark`=1, `cx`=2, `reputation`=3
- TikTok: pillars `none`
- X: brands `none`

## Detail par bloc

### Review sites

- Sources review: `none`
- Scopes review: `none`
- Brands review: `none`

### Google Maps / stores

- Store statuses: `review_scraped`=1
- Store review brands: `intersport`=5

### Google News

- News brands: `both`=3, `decathlon`=21, `intersport`=19
- News signaux: `cx`=1, `general`=21, `product`=12, `sports_team`=3, `store_network`=6

### Reddit

- Reddit brands: `both`=1, `decathlon`=19, `intersport`=10
- Reddit subreddits: `AskIndia`=1, `AtinAtinLang`=1, `Austria`=1, `Budgetbikeriders`=1, `Decathlon`=3, `PHikingAndBackpacking`=1, `RepzHunter`=1, `asda`=1, `bangalore`=1, `cycling`=1, `deinfluencingPH`=1, `frankfurt`=1, `gravelcycling`=1, `graz`=1, `greece`=1, `hiking`=1, `india_cycling`=2, `indianrunners`=1, `kettlebell`=1, `laufen`=1, `luftablassen`=1, `outdoorgear`=1, `pune`=1, `singapore`=1, `skiing`=1, `verbraucherschutz`=1, `wien`=1

### YouTube

- YouTube brands: `intersport`=6
- YouTube pillars: `benchmark`=1, `cx`=2, `reputation`=3
- YouTube source types: `channel`=1, `search`=5

### TikTok

- TikTok brands: `none`
- TikTok pillars: `none`
- TikTok source types: `none`

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
