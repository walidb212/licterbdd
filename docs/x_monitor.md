# X (Twitter) Monitor

## Fonctionnement

**Authentification cookies** (`X_AUTH_TOKEN` + `X_CT0`) — Playwright ouvre un Chrome headless connecte a x.com avec les cookies de session

**Recherche mentions latest** (`/search?q="Decathlon"&f=live`) — recupere les tweets les plus recents mentionnant la marque, scroll 3x la page

**Recherche mentions top** (`/search?q="Decathlon"&f=top`) — recupere les tweets les plus populaires mentionnant la marque, scroll 3x la page

**Extraction DOM** — parse chaque tweet depuis le HTML : texte, auteur, date, likes, retweets, replies, quotes, views

**Inference brand** — detecte si le tweet parle de "decathlon", "intersport" ou les deux depuis le contenu texte

**Deduplication** — latest + top combines et dedupliques par tweet_id (meme tweet trouve par plusieurs requetes -> merge des metriques)

## Requetes

| Requete | Marque | Type |
|---|---|---|
| "Decathlon" OR @Decathlon OR #Decathlon -is:retweet | decathlon | latest + top |
| "Intersport" OR @Intersport OR #Intersport -is:retweet | intersport | latest + top |

## Sortie

`data/x_runs/{run_id}/` :
- `queries.jsonl` — detail de chaque requete (raw count, retained, added)
- `tweets_raw.jsonl` — tweets bruts tel que parses du DOM
- `tweets_normalized.jsonl` — tweets nettoyes avec metriques (likes, retweets, replies, quotes, views, engagement_score)
- `results.md` — resume avec top tweets par engagement

## Usage

```bash
py -3.10 -m x_monitor --brand both
py -3.10 -m x_monitor --brand decathlon --latest-count 100 --top-count 50
```

## Statut

**BLOQUE** — 0 tweets. Les cookies X ont expire. Pour debloquer :
1. Se connecter a x.com dans un navigateur
2. DevTools > Application > Cookies > copier `auth_token` et `ct0`
3. Mettre dans `.env` : `X_AUTH_TOKEN=...` et `X_CT0=...`
