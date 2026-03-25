# YouTube Monitor

## Fonctionnement

**Recherche YouTube** (`/results?search_query=...&sp=...`) — requêtes thématiques par marque (reputation, benchmark, CX) avec filtre date côté serveur (week, month, year)

**Filtre pertinence** — on garde uniquement les vidéos qui mentionnent "decathlon" ou "intersport" dans le titre ou la description

**Filtre date** (`--date-filter`) — YouTube filtre côté serveur via le paramètre `sp` (hour, today, week, month, year). Par défaut : `month`

**Chaînes officielles** (onglet `/videos`) — extraction yt-dlp des 20 dernières vidéos publiées par les chaînes Decathlon et Intersport

**Shorts officiels** (onglet `/shorts`) — extraction yt-dlp des 20 derniers Shorts publiés par les chaînes officielles

**Extraction commentaires** — pour chaque vidéo, yt-dlp récupère les top commentaires (100 max) avec replies (10 max par commentaire)

**Déduplication** — search + channels combinés et dédupliqués par (brand, video_id)

## Requêtes de recherche

| Marque | Requête | Pilier |
|---|---|---|
| decathlon | Decathlon velo defectueux | reputation |
| decathlon | Decathlon accident velo | reputation |
| decathlon | boycott Decathlon | reputation |
| decathlon | Decathlon scandale | reputation |
| decathlon | Decathlon vs Intersport | benchmark |
| decathlon | Decathlon Intersport comparatif | benchmark |
| decathlon | avis Decathlon 2025 | cx |
| decathlon | SAV Decathlon retour produit | cx |
| decathlon | test produit Decathlon qualite | cx |
| intersport | Intersport avis 2025 | reputation |
| intersport | Intersport probleme | reputation |
| intersport | Intersport vs Decathlon | benchmark |
| intersport | test produit Intersport qualite | cx |
| intersport | SAV Intersport retour | cx |

## Sortie

`data/youtube_runs/{run_id}/` :
- `videos.jsonl` — metadonnees video (id, titre, description, channel, vues, likes, comments, tags, date, pillar, brand)
- `comments.jsonl` — commentaires (id, auteur, texte, likes, date, is_reply, parent_id)
- `results.md` — resume du run avec stats par requete

## Usage

```bash
# Ce mois (defaut)
py -3.10 -m youtube_monitor --brand both --date-filter month

# Cette semaine
py -3.10 -m youtube_monitor --brand both --date-filter week

# Cette annee
py -3.10 -m youtube_monitor --brand both --date-filter year

# Sans filtre date
py -3.10 -m youtube_monitor --brand both --date-filter ""
```

## Volumes typiques

- ~60-160 videos par run (selon filtre date)
- ~50-1700 commentaires
- Duree : ~7-13 min
