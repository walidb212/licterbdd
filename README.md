# LICTER — Brand Intelligence Platform

**Hackathon Eugenia School x Licter — Social Data Intelligence 2026**

Pipeline complet de veille, analyse et visualisation de la reputation de marque pour Decathlon vs Intersport.

---

## Architecture

```
COLLECTE (9 scrapers)          ENRICHISSEMENT IA           DASHBOARD COMEX
                                                          
store_monitor (Google Maps) --+                           +-- Reputation (crise velo)
review_monitor (Trustpilot)---+                           +-- Benchmark (Decathlon vs Intersport)
reddit_monitor ---------------+   ai_batch                +-- Experience Client (NPS, irritants)
youtube_monitor --------------+-> (OpenAI / Mistral) -->  +-- Recommandations (COMEX)
tiktok_monitor ---------------+   sentiment, topics,      +-- Synthese IA
news_monitor (Google News) ---+   priority, resume        +-- Personas synthetiques
x_monitor (Twitter/X) --------+                           +-- Assistant IA (RAG)
context_monitor (CGV/docs) ---+                           +-- Rapport PDF auto-genere
Dataset Excel (3 onglets) ----+                           
                                                          
Orchestration: prod_pipeline (.\run)                      
Cron: GitHub Actions (daily + weekly)                     
Alertes: Make webhook -> Slack                             
```

## Stack technique

| Couche | Technologie |
|---|---|
| **Scraping** | Python 3.10 -- yt-dlp, DrissionPage, Playwright, crawl4ai, urllib |
| **IA** | OpenAI gpt-4o-mini (impose jury), Mistral, OpenRouter (fallback) |
| **Backend** | Node.js -- Express, better-sqlite3 |
| **Frontend** | React 19, Tailwind CSS, Recharts, Tremor |
| **BDD** | SQLite (local), Supabase (jury) |
| **Orchestration** | N8N (facade), GitHub Actions (cron) |
| **Alertes** | Make webhook -> Slack |
| **PDF** | Puppeteer (HTML -> PDF A4) |

## Donnees collectees

### Sources scraper (donnees reelles)

| Source | Type | Volume | Partition |
|---|---|---|---|
| Google Maps | Avis magasins (40 magasins) | 1 475 avis | store |
| Trustpilot | Avis clients | 125 avis | customer |
| Custplace | Avis clients | 40 avis | customer |
| Glassdoor | Avis employes | 10 avis | employee |
| Indeed | Avis employes | 40 avis | employee |
| Poulpeo/eBuyClub | Avis cashback | 102 avis | customer |
| Dealabs | Promos/deals | 60 discussions | promo |
| Reddit | Posts + commentaires | 30 posts, 168 commentaires | community |
| YouTube | Videos + commentaires | 67 videos, 83 commentaires | social |
| TikTok | Videos (comptes + hashtags) | 68 videos | social |
| X/Twitter | Tweets | Variable (cookies requis) | social |
| Google News | Articles presse | 91 articles | news |
| CGV/retours | Documents officiels | 8 documents | context |

### Dataset Excel fourni (donnees hackathon)

| Onglet | Contenu | Volume |
|---|---|---|
| `Reputation_Crise` | Bad buzz velo defectueux (TikTok, Twitter, Reddit, Facebook) | 767 records |
| `Benchmark_Marche` | Mentions comparatives Decathlon vs Intersport (12 mois) | 2 600 records |
| `VoixClient_CX` | Avis Trustpilot, Google Maps, App Store (notes 1-5) | 1 442 records |

**Total : 6 249 records enrichis par IA**

## KPIs dashboard

### Pilier Reputation
- **Gravity Score** = spike volume x % negatif x priority moyen (0-10)
- Volume mentions / jour avec spike detection
- Top detracteurs (comptes a fort reach)
- Timeline crise 24 fev -> aujourd'hui

### Pilier Benchmark
- **Share of Voice** = mentions Decathlon / total mentions
- Sentiment comparatif Decathlon vs Intersport
- Radar forces/faiblesses par topic (Prix, SAV, Qualite, Marques propres)

### Pilier CX
- **NPS Proxy** = (5 etoiles - 1 etoile) / total x 100
- Top 5 irritants (avis 1-2 etoiles)
- Top 3 enchantements (avis 5 etoiles)
- Note moyenne toutes sources

## Features

### Pipeline
- `.\run` -- lance les 11 steps avec logs stylises (ASCII banner, progress bars, badges colores)
- `data/latest_run.json` -- fichier temps reel mis a jour apres chaque step
- Continue-on-error : si X ou product_monitor fail, le pipeline continue
- Retry automatique avec timeout par step

### Dashboard COMEX
- 3 piliers avec max 4 KPIs par page
- Code couleur = decision (rouge = agir, orange = surveiller, vert = OK)
- 1 recommandation actionnable par page
- Word Cloud des themes dominants
- Export PDF (rapport COMEX 5 pages)
- Export Excel (CSV compatible)

### Assistant IA (RAG)
- Chat en langage naturel sur les donnees collectees
- Multi-provider : OpenAI -> Mistral -> OpenRouter (fallback chain)
- System prompt hardened (8 regles absolues, anti-injection)
- Input sanitizer (regex injection, rate limiting, session scoring)
- Output validator (bloque les leaks techniques)
- Chat logs SQLite pour audit
- Cache reponses 15 min

### Personas synthetiques
- 3 personas auto-generes par IA
- Bases sur les donnees reelles (irritants, enchantements, sources)
- Satisfaction score, motivations, frustrations, canaux

### Detection de crise
- Severity scoring (critical/high/medium/low)
- Spike detection (volume > moyenne x 2)
- Early warnings (tendance 3 derniers jours)
- Timeline de crise avec zone negative

### Alertes
- Make webhook -> Slack
- Gravity Score > 8 -> alerte critique
- Volume spike > 50% -> alerte haute
- NPS < 0 -> alerte moyenne
- Cooldown 5 min anti-spam

## Commandes

```bash
# Pipeline complet (11 steps)
.\run

# Pipeline partiel
.\run --steps news_monitor,reddit_monitor,youtube_monitor

# Dashboard (frontend + backend)
cd dashboard && npm start

# Backend seul
cd server && node index.mjs

# Tests Python
py -3.10 -m unittest discover -s tests

# ai_batch
py -3.10 -m ai_batch --brand both --provider auto --input-run latest
```

## Structure du repo

```
LICTER/
+-- monitor_core/           # Etat SQLite, helpers, .env loader
+-- store_monitor/          # Google Maps (Playwright)
+-- review_monitor/         # Trustpilot, Glassdoor, Indeed, Custplace...
+-- reddit_monitor/         # Posts + commentaires (crawl4ai)
+-- youtube_monitor/        # Videos + commentaires (yt-dlp)
+-- tiktok_monitor/         # Videos (yt-dlp + DrissionPage)
+-- x_monitor/              # Tweets (Playwright + cookies)
+-- news_monitor/           # Google News RSS + Cloudflare
+-- context_monitor/        # CGV, retours, livraison
+-- ai_batch/               # Enrichissement IA multi-provider
+-- prod_pipeline/          # Orchestrateur avec logs stylises
+-- db/                     # Schema SQL + loader PostgreSQL
+-- server/                 # Express + SQLite + RAG
|   +-- index.mjs           # Serveur principal (port 8000)
|   +-- db.mjs              # SQLite init + helpers
|   +-- ingest.mjs          # JSONL -> SQLite au boot
|   +-- kpis.mjs            # Calcul KPIs (gravity, SoV, NPS...)
|   +-- rag.mjs             # RAG multi-provider + hardened prompt
|   +-- pdf.mjs             # Generation rapport PDF
|   +-- crisis.mjs          # Detection de crise
|   +-- alerts.mjs          # Webhooks Make/Slack
|   +-- middleware/
|   |   +-- sanitizer.mjs   # Anti-injection + rate limiting
|   +-- routes/             # 8 endpoints API
+-- dashboard/              # React + Tailwind + Recharts
|   +-- src/
|       +-- App.tsx          # Layout 3 colonnes + chat flottant
|       +-- api/client.ts    # React Query hooks
|       +-- charts/          # 7 composants graphiques
|       +-- components/      # Panels, KpiCard, AlertBanner
+-- data/                   # Tous les outputs JSONL
+-- docs/                   # Documentation par monitor
+-- .github/workflows/      # Cron GitHub Actions (daily + weekly)
+-- run.bat                 # Raccourci pipeline
```

## Ce qui manque

| Element | Statut | Priorite |
|---|---|---|
| **Video Loom** | Non filmee | CRITIQUE -- livrable J4 obligatoire |
| **PPT soutenance** | Non cree | CRITIQUE -- livrable J5 |
| **N8N workflow visible** | Facade seulement | HAUTE -- le jury verifie |
| **Supabase** | db/loader.py existe mais non connecte | HAUTE -- le jury veut voir la BDD |
| **App Store scraper** | Non implemente | MOYENNE -- l'Excel en a 378 records |
| **Avis Verifies scraper** | Non implemente | MOYENNE -- l'Excel en a 356 records |
| **Facebook scraper** | Non implemente | BASSE -- anti-bot tres fort |
| **LinkedIn scraper** | Teste, 0 resultat via DDG | BASSE -- abandonne |

## Scrapers vs Excel : aurait-on pu se passer du dataset ?

**Non -- le dataset Excel couvre des sources qu'on ne scrape pas :**

| Source | Dans nos scrapers | Dans le dataset Excel |
|---|---|---|
| Google Maps | 1 475 avis | 343 avis |
| Trustpilot | 125 avis | 365 avis |
| Reddit | 198 records | 846 records |
| YouTube | 150 records | -- |
| TikTok | 68 videos | 203 records |
| Twitter/X | Variable | 841 records |
| App Store | -- | 378 records |
| Avis Verifies | -- | 356 records |
| Facebook | -- | 178 records |
| LinkedIn | -- | 635 records |
| News Forums | -- | 664 records |

**Ce que le dataset apporte en plus :**
- Topics pre-categorises (SAV, qualite, prix, marques propres)
- Labels de crise ("Crisis Alert", "Accident velo defectueux")
- Comparaison explicite Decathlon vs Intersport
- 4 plateformes qu'on ne scrape pas (App Store, Avis Verifies, Facebook, LinkedIn)

**Ce que nos scrapers apportent en plus :**
- Donnees fraiches (vs dataset fige)
- URLs sources verifiables
- Metriques d'engagement reelles (scores, likes, vues)
- Google Maps avec geolocalisation magasins
- Articles presse complete (Google News)
- Automatisation continue (cron)

**Conclusion** : les deux sont complementaires. Le dataset donne la base historique, les scrapers donnent le flux temps reel.

---

*LICTER x Eugenia School -- BDD 2026*
