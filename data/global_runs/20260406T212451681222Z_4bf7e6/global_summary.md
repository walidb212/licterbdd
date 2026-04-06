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

- Sources review: `custplace`=40, `dealabs`=60, `ebuyclub`=2, `glassdoor`=10, `indeed`=40, `poulpeo`=100, `trustpilot`=125
- Scopes review: `customer`=267, `employee`=50, `promo`=60
- Brands review: `decathlon`=186, `intersport`=191

### Google Maps / stores

- Store statuses: `none`
- Store review brands: `none`

### Google News

- News brands: `both`=39, `decathlon`=47, `intersport`=15
- News signaux: `benchmark`=1, `cx`=2, `general`=66, `product`=20, `reputation`=3, `store_network`=9

### Reddit

- Reddit brands: `both`=14, `decathlon`=60, `intersport`=6
- Reddit subreddits: `Budgetbikeriders`=1, `Decathlon`=19, `Denver`=1, `Fahrrad`=1, `Frandroid`=2, `IaCaca`=1, `Ingolstadt`=1, `Innsbruck`=1, `ManyBaggers`=1, `PHikingAndBackpacking`=1, `PHitness`=1, `Rosario`=1, `SoloTravel_India`=1, `StudyInTheNetherlands`=1, `SurveyCircle_fr`=1, `TechWear`=1, `Tools`=1, `UKhiking`=1, `Ultralight`=1, `XaviersMansion`=1, `askCroatians`=1, `askSingapore`=1, `bicycling`=1, `bikefit`=1, `climbingshoes`=1, `cycling`=2, `deinfluencingPH`=1, `france`=8, `india_cycling`=1, `indianrunners`=1, `italy`=1, `japanresidents`=1, `oldschoolcool80s`=1, `onebag`=3, `pcmasterraceFR`=1, `pedale`=11, `pelotonmemes`=1, `prsuk`=1, `santementale`=1, `surfing`=1, `wandern`=1

### YouTube

- YouTube brands: `decathlon`=21, `intersport`=51
- YouTube pillars: `benchmark`=9, `cx`=7, `reputation`=56
- YouTube source types: `channel`=37, `search`=35

### TikTok

- TikTok brands: `decathlon`=17, `intersport`=10
- TikTok pillars: `reputation`=27
- TikTok source types: `account`=20, `hashtag`=7

### X

- X brands: `decathlon`=12, `intersport`=23
- X search types: `latest`=21, `top`=14

## Ce que tu as vraiment aujourd'hui

1. Un aggregateur unifie qui integre maintenant YouTube et TikTok en plus des blocs reviews, stores, news, Reddit et X.
2. Des partitions de sources separees, ce qui permet de construire un dashboard propre sans melanger des semantiques incompatibles.
3. Une lecture rapide des derniers runs disponibles, utile pour un point de situation avant ingestion Sheets ou Supabase.

## Priorites recommandees

1. Conserver `source_partition`, `brand_focus`, `entity_level` et `pillar` dans la base cible.
2. Ne pas additionner les signaux sociaux YouTube/TikTok avec les notes clients sans un traitement IA explicite.
3. Traiter les sources sociales comme de l'awareness / benchmark / verbatim, pas comme de la satisfaction client brute.
