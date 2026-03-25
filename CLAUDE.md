# BRIEFING COMPLET — Projet LICTER × Eugenia School BDD 2026
# Donne ce fichier en premier à Claude Code avant toute session de travail.
# Source officielle : https://licter-eugenia-bdd-2026.netlify.app

---

## 1. Contexte du hackathon

Organisé par **Licter × Eugenia School**, édition 2026.
Durée : 6 semaines. Jury : 4 professionnels de la data.

**Problématique centrale** : une marque génère chaque jour des centaines de signaux (avis, mentions, comparatifs). Comment les structurer, analyser et synthétiser pour en faire une arme stratégique pour ses décideurs ?

**Notre marque** : **Decathlon** — concurrent direct : **Intersport**
**Dataset** : `dataset_decathlon.xlsx` (fourni par les organisateurs)

**Intervenants jury** :
- Victor Phouangsavath — Consultant Social Data Analyst @ Licter
- Noah Segonds — Data Analyst Customer Growth @ Decathlon Digital

**Question jury à se poser en permanence** :
> "Si un membre du COMEX n'a que 2 minutes, est-ce que mon dashboard et mon magazine lui permettent de prendre une décision ?"

---

## 2. Critères d'évaluation

| Critère | Poids |
|---|---|
| Pertinence des insights (actionnables COMEX) | **30%** |
| Maîtrise technique du pipeline | **25%** |
| Qualité du dashboard | **20%** |
| Storytelling & recommandations | **15%** |
| Qualité du magazine PDF | **10%** |

---

## 3. Planning des rendus jour par jour

| Jour | Livrable |
|---|---|
| J1 | Roadmap du projet (Notion/Trello) + nomination chef de projet |
| J2 | Cartographie du pipeline (Miro/FigJam) — parcours de la donnée |
| J3 | V1 Dashboard fonctionnel (données triables/filtrables) |
| J4 | Automatisation complète — démonstration live bout en bout |
| J5 | Pitch & Présentation COMEX devant jury |

---

## 4. Livrables finaux obligatoires

1. **Vidéo Loom** — workflow N8N/Make de bout en bout (extraction → IA → BDD → dashboard)
2. **Dashboard interactif** — "Matrice de Bataille" connectée à Supabase
3. **Magazine exécutif PDF** — 5 pages max, niveau cabinet de conseil, pour la Direction
4. **Présentation PPT** — support de soutenance avec insights et recommandations

---

## 5. Stack technique

### Contrainte obligatoire
**N8N ou Make est le seul outil imposé.** On utilise N8N comme façade vitrine.

### Notre stack réelle (on n'utilise PAS leur recommandation)

| Couche | Recommandation officielle | Notre choix |
|---|---|---|
| Orchestration | Make | **N8N** (façade vitrine uniquement, 3 nœuds) |
| Scraping | Apify | **Stack Python custom** (voir modules repo) |
| IA | OpenAI API | **gpt-4o-mini** via `ai_batch` (20x moins cher) |
| BDD | Supabase | **PostgreSQL** local + Supabase comme interface jury |
| Dashboard | Antigravity | **Streamlit** custom (+ export Supabase pour conformité) |

---

## 6. Dataset Excel fourni — 3 onglets

### Onglet 1 — `Reputation_Crise`
- ~1 500 lignes de bad buzz "Accident vélo défectueux" Decathlon
- Période : 24 fév — 11 mars 2026 (crise encore active)
- Plateformes : TikTok, Twitter, Reddit, Facebook
- Sentiment : 100% Négatif
- **Pièges** : colonne `text` contient des cellules vides → drop NaN obligatoire
- Colonnes inutiles à dropper : `scrapingserverip`, `useragentstring`, `deprecatedfieldv2`, `processingtimems`

### Onglet 2 — `Benchmark_Marche`
- Mentions comparatives Decathlon vs Intersport sur 1 an
- Topics : prix, SAV, qualité, marques propres, service réparation
- **LIVRABLE OBLIGATOIRE** : colonne `sentiment_detected` est **intentionnellement vide** → à remplir via workflow IA OpenAI
- C'est le livrable technique n°2 que le jury vérifie

### Onglet 3 — `Experience_Client_CX` (nommé `VoixClient_CX` dans le code)
- Avis Trustpilot / Google Maps / App Store avec notes 1-5
- Catégories : conseils vendeur, choix rayon, rapport qualité/prix, SAV, retours

---

## 7. Pipeline complet de notre architecture

```
ÉTAPE 1 : INGEST
├── Dataset Excel fourni (base historique)
└── Scraping live via stack Python custom

ÉTAPE 2 : NETTOYAGE & DÉDUPLICATION
├── Drop NaN, lignes vides
├── Déduplication par review_id
├── Normalisation dates, langues
├── Détection langue (langdetect)
└── Filtre qualité (texte < 5 mots → drop)

ÉTAPE 3 : ENRICHISSEMENT IA (multi-passes via ai_batch)
├── Pass 1 — Sentiment (Positif/Négatif/Neutre)
├── Pass 2 — Topic extraction (Prix, SAV, Qualité, Livraison...)
├── Pass 3 — Crisis detection (is_crisis + gravity_score)
└── Pass 4 — Résumé automatique (1 phrase par cluster)

ÉTAPE 4 : SCORING & CALCUL KPIs
├── Reach Score     = likes + (shares × 3) + (followers × 0.01)
├── Gravity Score   = volume_spike × sentiment_negatif × reach
├── Share of Voice  = mentions_decathlon / total_mentions
└── NPS proxy       = (5★ - 1★) / total_avis × 100

ÉTAPE 5 : ALERTING
├── Si gravity_score > seuil → webhook Slack/email
├── Si volume/jour > moyenne × 2 → flag "crise détectée"
└── Si sentiment négatif > 70% → alerte rouge dashboard

ÉTAPE 6 : STOCKAGE
├── PostgreSQL (données brutes + enrichies)
└── Vue matérialisée (KPIs précalculés pour dashboard rapide)

ÉTAPE 7 : VISUALISATION
├── Streamlit Dashboard (3 piliers : Réputation / Benchmark / CX)
├── Export PDF automatique (magazine COMEX 5 pages)
└── N8N trigger (façade obligatoire → appelle notre FastAPI)
```

---

## 8. Repo Python — état au 18 mars 2026

### Modules présents

```
LICTER/
├── monitor_core/       # état SQLite partagé, Cloudflare helpers, .env loader
├── reddit_monitor/     # posts + commentaires via crawl4ai
├── youtube_monitor/    # vidéos + commentaires via yt-dlp (search + chaînes officielles)
├── tiktok_monitor/     # vidéos + commentaires via yt-dlp + DrissionPage (comptes + hashtags + search)
├── x_monitor/          # tweets via clix local (Python 3.13 dans .venv-x)
├── news_monitor/       # Google News RSS + enrichissement Cloudflare
├── review_monitor/     # Trustpilot, Custplace, Glassdoor, Indeed, Dealabs, Poulpeo, eBuyClub
├── store_monitor/      # discovery magasins + Google Maps reviews (Playwright)
├── product_monitor/    # pages produit (fragile anti-bot, résultats 0 actuellement)
├── context_monitor/    # CGV, retours, livraison officiels Decathlon + Intersport
├── global_summary/     # snapshot Markdown consolidé multi-sources
├── ai_batch/           # enrichissement OpenAI/OpenRouter sur outputs monitors
├── db/                 # schema.sql PostgreSQL/Supabase + loader.py (JSONL+Excel → DB)
├── prod_pipeline/      # runner cron avec retries, timeouts, logs
└── data/               # tous les outputs JSONL par monitor et par run
```

### Détail scrapers sociaux

#### youtube_monitor

1. **Recherche YouTube** (`ytsearch{N}:query`) — filtre date côté serveur (`week`, `month`…)
2. **Filtre brand** — on garde uniquement les vidéos qui mentionnent "decathlon" ou "intersport" dans le titre ou la description
3. **Chaînes officielles** — vidéos `/videos` + Shorts `/shorts` (via yt-dlp `channel_url/videos`, `channel_url/shorts`)
4. **Commentaires** — extraction yt-dlp `getcomments` pour chaque vidéo (max 100 comments, 10 replies)
5. **9 search queries** Decathlon (crise vélo, boycott, SAV, benchmark…) + **5 queries** Intersport
6. **2 chaînes officielles** : `@decathlon` (global) + `@intersportfr`

#### tiktok_monitor

1. **Page hashtag** (`/tag/keyword`) — DrissionPage avec interception API XHR, ~150-200 vidéos par hashtag avec métriques complètes
2. **Comptes officiels** (`@decathlon`, `@intersportfr`) — extraction yt-dlp des dernières vidéos publiées
3. **Filtre pertinence** — on garde uniquement les vidéos qui mentionnent le keyword dans la description ou les hashtags
4. **Filtre date** — uniquement les vidéos des 30 derniers jours (`--max-age-days 30`)
5. **Déduplication** — hashtag + account combinés et dédupliqués par `video_id`
6. **Commentaires** — yt-dlp `getcomments` sur les top 3 vidéos par hashtag (DrissionPage trouve les URLs, yt-dlp extrait les commentaires)
7. **10 hashtags** : decathlon, decathlonfrance, decathlonsport, decathlonfr, intersport, intersportfrance, intersportfr, rockrider, nakamura, sportpascher
8. **Anti-détection** — Chrome headless via DrissionPage (pas Playwright), pause aléatoire 4-8s entre hashtags

### Données réelles disponibles (snapshot 18 mars 2026)

| Source | Volume réel |
|---|---|
| `store_monitor` (Google Maps) | **1 475 avis**, 40 magasins |
| `review_monitor` (Trustpilot, Glassdoor...) | **213 avis** |
| `reddit_monitor` | **30 posts**, 168 commentaires |
| `youtube_monitor` | **18 vidéos**, 39 commentaires |
| `tiktok_monitor` | **68 vidéos** (comptes + hashtags DrissionPage) |
| `news_monitor` | **43 articles** |
| `context_monitor` | **8 documents** CGV/retours/livraison |
| `x_monitor` | ⚠️ **0 posts** — cookies expirés |
| `product_monitor` | ⚠️ **0 résultats** — anti-bot bloquant |
| `ai_batch` | ✅ **validé** via OpenRouter (social=265, review=25, news=43, entities=86) |

### Tests

```powershell
py -3.10 -m unittest discover -s tests   # 55 tests OK
py -3.10 -m compileall monitor_core review_monitor store_monitor product_monitor context_monitor news_monitor reddit_monitor youtube_monitor tiktok_monitor global_summary x_monitor ai_batch prod_pipeline   # OK
```

---

## 9. Règle fondamentale — Source partitions

**Ne jamais fusionner** ces partitions dans un score brut unique :

| Partition | Sources |
|---|---|
| `customer` | Trustpilot, Custplace, Poulpeo, eBuyClub |
| `employee` | Glassdoor, Indeed |
| `store` | Google Maps magasins |
| `promo` | Dealabs |
| `product` | pages produit officielles |
| `context` | CGV, docs retours/livraison |
| `news` | presse Google News |
| `community` | Reddit |
| `social` | Twitter/X, YouTube, TikTok |

---

## 10. Variables d'environnement

```
# Copier .env.example → .env

CLOUDFLARE_API_TOKEN=...
CLOUDFLARE_ACCOUNT_ID=...

X_AUTH_TOKEN=...
X_CT0=...

# Fourni par les organisateurs — utiliser OBLIGATOIREMENT gpt-4o-mini
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
```

---

## 11. Commandes prioritaires

```powershell
# PRIORITÉ 1 — Lancer ai_batch (jamais tourné en live)
python -m ai_batch --brand both --input-run latest --output-dir data/ai_runs

# Test sans clé OpenAI
python -m ai_batch --brand both --provider heuristic --input-run latest

# Run prod complet stable
python -m prod_pipeline --brand both --steps store_monitor,review_monitor,news_monitor,reddit_monitor,youtube_monitor,tiktok_monitor,context_monitor,global_summary,ai_batch

# Snapshot global consolidé
python -m global_summary
```

---

## 12. KPIs dashboard à produire

### Pilier Réputation
- Volume mentions / jour → spike detection crise vélo
- Gravity Score = `volume_spike × sentiment_négatif × reach`
- Top influenceurs détracteurs (`is_verified=1`, `user_followers` desc)
- Timeline crise 24 fév → aujourd'hui

### Pilier Benchmark
- Share of Voice = `mentions_decathlon / total_mentions`
- Sentiment Score comparatif Decathlon vs Intersport
- Radar forces/faiblesses par topic (Prix, SAV, Qualité, Marques propres)

### Pilier CX
- Évolution note moyenne sur 12 mois
- Top 5 irritants (avis 1-2★)
- Top 3 enchantements (avis 5★)
- NPS proxy = `(5★ - 1★) / total × 100`

---

## 13. Insights clés à défendre devant le jury

**Insight 1 — Crise structurelle** : 1 500+ mentions négatives en 15 jours sur l'accident vélo. Pic 7-10 mars. Recommandation : communiqué transparent + hotline dédiée dans les 48h.

**Insight 2 — Remontada Intersport** : 935 magasins vs 335. Intersport gagne sur les grandes marques. Decathlon conserve +45% sur le rapport qualité/prix. Ne pas essayer de battre Intersport sur son terrain.

**Insight 3 — SAV comme levier CX** : 40% des avis négatifs portent sur le SAV. Réparable en 3 mois. Un chatbot de première réponse pourrait réduire 60% des avis négatifs.

---

## 14. Do's et Don'ts

**Do's** : penser COMEX, automatiser d'abord, tester les prompts sur 20-50 lignes, documenter les choix de KPIs, utiliser gpt-4o-mini uniquement.

**Don'ts** : dashboard "sapin de Noël", négliger le magazine, oublier la vidéo Loom, fusionner les source_partitions, inventer des chiffres.

---

*Briefing généré le 14 mars 2026 — LICTER × Eugenia School BDD 2026*
