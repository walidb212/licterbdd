# Google News Monitor

## Fonctionnement

**Flux RSS Google News** (`news.google.com/rss/search?q=...`) — requetes avec filtre `when:7d` (7 derniers jours) integre dans l'URL

**5 requetes** :
- `"Decathlon"` — actualites generales
- `"Decathlon" (SAV OR "service client" OR retour OR remboursement OR magasin)` — actualites CX
- `"Intersport"` — actualites generales
- `"Intersport" (SAV OR "service client" OR retour OR remboursement OR magasin)` — actualites CX
- `"Decathlon" AND "Intersport"` — benchmark comparatif

**Classification automatique** — chaque article est classe par signal via mots-cles dans titre+description :
- `reputation` : boycott, greve, plainte, rappel, controverse, crise, accident
- `cx` : SAV, service client, retour, remboursement, livraison
- `benchmark` : vs, comparatif, face a
- `product` : velo, rockrider, quechua, produit
- `store_network` : ouverture, fermeture, magasin
- `sports_team` : cyclisme, tour, peloton (filtre — vire si pas de mention Intersport)
- `general` : tout le reste

**Filtre pertinence** — les articles type `sports_team` qui ne mentionnent pas Intersport sont vires (car "Decathlon" est aussi un nom d'equipe cycliste)

**Enrichissement Cloudflare** (optionnel) — recupere le contenu Markdown complet de l'article via Cloudflare Browser Rendering API

**Deduplication** — meme article trouve par plusieurs requetes -> merge (query_names, brand_detected)

## Sortie

`data/news_runs/{run_id}/` :
- `articles.jsonl` — articles (titre, date, source, description, signal_type, brand_detected, markdown si enrichi)
- `queries.jsonl` — detail de chaque requete (fetched, retained, added)
- `results.md` — resume avec top articles et distribution par signal/source

## Usage

```bash
py -3.10 -m news_monitor --brand both
py -3.10 -m news_monitor --brand decathlon --days-back 14
py -3.10 -m news_monitor --brand both --enrich-mode cloudflare
```

## Statut

**OK** — 43 articles au dernier run. Enrichissement Cloudflare desactive (CLOUDFLARE_API_TOKEN manquant).
