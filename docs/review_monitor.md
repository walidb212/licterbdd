# Review Monitor

## Fonctionnement

**14 sources scrapees** (7 sites x 2 marques), reparties en 3 scopes :

| Scope | Sites | Partition |
|---|---|---|
| **customer** | Trustpilot, Custplace, Poulpeo, eBuyClub | customer |
| **employee** | Glassdoor, Indeed | employee |
| **promo** | Dealabs | promo |

**Fetch en 2 passes** — d'abord Cloudflare Browser Rendering (si token dispo), sinon fallback crawl4ai (navigateur headless). Si Cloudflare retourne 0 avis -> retry automatique avec crawl4ai

**Parsing HTML par site** — chaque site a son parser dedie :
- Trustpilot : DOM `<article>` + selectors specifiques
- Glassdoor / Indeed : JSON-LD `<script type="application/ld+json">` + fallback DOM cards
- Custplace : CSS cards `article.topic-sample`
- Poulpeo / eBuyClub : JSON-LD + fallback DOM cards generiques
- Dealabs : DOM cards `article` / `div[class*='thread']`

**Extraction par avis** — auteur, date, note (1-5 etoiles), titre, texte du verbatim, note agregee de la source, nombre total d'avis

**Filtre qualite** — detection des captchas/challenges (Indeed, Poulpeo), filtrage des faux avis type coupon/code promo (eBuyClub), deduplication par (auteur, date, titre, texte)

**Mode incremental** (StateStore SQLite) — chaque avis est hashe, les avis deja vus dans un run precedent sont skippes

**Deduplication** — meme avis trouve sur plusieurs pages -> merge

## Sortie

`data/review_runs/{run_id}/` :
- `reviews.jsonl` — avis (site, marque, scope, auteur, date, note, titre, texte, note agregee)
- `sources.jsonl` — resume par source (note agregee, volume, reviews extraites, fetch mode)
- `results.md` — resume avec stats et exemples de verbatims

## Usage

```bash
# Toutes les sources
py -3.10 -m review_monitor --brand both

# Trustpilot seulement
py -3.10 -m review_monitor --brand both --site trustpilot

# Scope employee seulement
py -3.10 -m review_monitor --brand both --scope employee

# Decathlon seulement
py -3.10 -m review_monitor --brand decathlon
```

## Volumes typiques (dernier run)

| Source | Decathlon | Intersport |
|---|---:|---:|
| Trustpilot | 60 | 65 |
| Custplace | 20 | 20 |
| Poulpeo | 50 | 50 |
| eBuyClub | 1 | 1 |
| Glassdoor | 5 | 5 |
| Indeed | 20 | 20 |
| Dealabs | 30 | 30 |
| **Total** | **186** | **191** |

## Insight cle

Trustpilot Decathlon : **1.70/5** (2 919 avis) vs Intersport : **4.20/5** (7 438 avis)
