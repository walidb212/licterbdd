# TikTok Monitor

## Fonctionnement

**Recherche TikTok** (`/search/video?q=keyword`) — capte les videos qui mentionnent le mot-cle sans forcement avoir le hashtag (via DrissionPage, experimental)

**Page hashtag** (`/tag/keyword`, onglet "Videos") — donne le volume, trie par date recente, ~150 videos par hashtag (via DrissionPage)

**Comptes officiels** (`@decathlon`, `@intersportfr`) — extraction yt-dlp des dernieres videos publiees

**Filtre pertinence** — on garde uniquement les videos qui mentionnent le keyword dans le titre ou la description

**Filtre date** — uniquement les videos des 30 derniers jours (`--max-age-days 30`)

**Deduplication** — search + tag combines et dedupliques par video_id

## Sortie

`data/tiktok_runs/{run_id}/` :
- `videos.jsonl` — metadonnees video (id, titre, description, auteur, vues, likes, comments, date)
- `comments.jsonl` — commentaires (id, auteur, texte, likes, date)
- `sources.jsonl` — detail des sources scrapees
- `results.md` — resume du run

## Usage

```bash
# Comptes officiels seulement (stable)
py -3.10 -m tiktok_monitor --brand both

# Avec hashtags experimentaux
py -3.10 -m tiktok_monitor --brand both --include-experimental

# Filtre date 7 jours
py -3.10 -m tiktok_monitor --brand both --max-age-days 7
```

## Statut

**OK** (comptes officiels) — 10 videos au dernier run. Hashtags = experimental (DrissionPage, peut etre instable).
