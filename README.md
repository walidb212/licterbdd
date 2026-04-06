# LICTER — Brand Intelligence Platform

**Hackathon Eugenia School x Licter — Social Data Intelligence 2026**

Agent autonome de veille, analyse et visualisation de la reputation de marque pour Decathlon vs Intersport. 12 scrapers, 3 features d'intelligence autonome, dashboard COMEX avec RAG chatbot.

---

## Architecture

```
COLLECTE (12 sources)              ENRICHISSEMENT                DASHBOARD COMEX
                                                          
store_monitor (Google Maps)  --+                          +-- Reputation (Gravity Score, crise velo)
review_monitor (7 sites)     --+                          +-- Benchmark (SoV, radar forces/faiblesses)
reddit_monitor (JSON API)    --+   ai_batch               +-- Experience Client (NPS, irritants)
youtube_monitor (yt-dlp)     --+-> (OpenAI gpt-4o-mini)   +-- Recommandations COMEX
tiktok_monitor (DrissionPage)--+   + topic detection      +-- Synthese IA (entites cles)
instagram_monitor (GraphQL)  --+   + crisis detection     +-- Personas synthetiques
x_monitor (Playwright)       --+   + brand vs competitor  +-- Assistant IA (RAG chatbot)
news_monitor (Google News)   --+                          +-- Rapport PDF auto-genere
facebook_ads_monitor (Meta)  --+                          +-- Word Cloud
app_store (iTunes RSS)       --+                          +-- Export Excel
forums (DDG search)          --+                          +-- Trending Opportunity
Dataset Excel (3 onglets)    --+                          +-- Auto-Discovery
                                                          +-- Event Mode (temps reel)
Orchestration: prod_pipeline (.\run)                     
Parallelisation: 7 scrapers simultanes                    Alertes: Make webhook -> Slack
Cron: GitHub Actions (daily + weekly)                     16+ endpoints API REST
```

---

## Stack technique

| Couche | Technologie |
|---|---|
| **Scraping** | Python 3.10 — yt-dlp, DrissionPage, Playwright, crawl4ai, urllib |
| **IA enrichissement** | OpenAI gpt-4o-mini (impose jury), Mistral, OpenRouter (fallback chain) |
| **IA chatbot** | RAG multi-provider avec system prompt hardened + input sanitizer |
| **Backend** | Node.js 22 — Express, better-sqlite3 |
| **Frontend** | React 19, Tailwind CSS 4, Recharts, Tremor, react-markdown |
| **BDD** | SQLite (local temps reel), Supabase (jury) |
| **Orchestration** | N8N/Make (facade), GitHub Actions (cron daily+weekly) |
| **Alertes** | Make webhook -> Slack (gravity > 8 = critique, spike > 50% = haute) |
| **PDF** | Puppeteer (HTML -> PDF A4, 5 pages COMEX) |
| **Securite** | Input sanitizer (injection regex, rate limiting), output validator |

---

## Donnees collectees

### 12 sources actives (donnees reelles)

| Source | Type | Volume dernier run | Partition |
|---|---|---|---|
| Google Maps | Avis magasins (40 magasins) | 1 475 avis | store |
| Trustpilot | Avis clients (pagination __NEXT_DATA__) | 125 avis | customer |
| Custplace | Avis clients | 40 avis | customer |
| Glassdoor | Avis employes | 10 avis | employee |
| Indeed | Avis employes | 40 avis | employee |
| Poulpeo/eBuyClub | Avis cashback | 102 avis | customer |
| Dealabs | Promos/deals | 60 discussions | promo |
| Reddit | Posts + commentaires (JSON API, pagination cursor) | 1 006 records | community |
| YouTube | Videos + commentaires (yt-dlp, top 10 comments) | 175 records | social |
| TikTok | Videos comptes + hashtags (DrissionPage + yt-dlp) | 76 videos | social |
| Instagram | Posts comptes officiels (GraphQL API, no login) | 26 posts | social |
| X/Twitter | Tweets (Playwright + cookies) | 112 tweets | social |
| Google News | Articles presse (RSS + Cloudflare enrichment) | 112 articles | news |
| Facebook Ads | Pubs Meta Ad Library (DrissionPage, relay store) | 60 pubs | social |
| App Store | Avis iOS (iTunes RSS API) | 50 avis | customer |
| Forums | Posts forums sport FR (DDG search) | 29 posts | community |
| CGV/retours | Documents officiels Decathlon + Intersport | 8 documents | context |

### Dataset Excel fourni (donnees hackathon)

| Onglet | Contenu | Volume |
|---|---|---|
| `Reputation_Crise` | Bad buzz velo defectueux (TikTok, Twitter, Reddit, Facebook) | 767 records |
| `Benchmark_Marche` | Mentions comparatives Decathlon vs Intersport (12 mois) | 2 600 records |
| `VoixClient_CX` | Avis Trustpilot, Google Maps, App Store (notes 1-5) | 1 442 records |

**Total pipeline : ~8 300+ records dont 6 471 enrichis par IA**

---

## KPIs dashboard

### Pilier Reputation — "On est en crise ?"
- **Gravity Score** = spike volume x % negatif x priority moyen (0-10)
- Volume mentions / jour avec spike detection
- 852 posts auto-detectes `crisis_alert`
- Top detracteurs (comptes a fort reach)
- Timeline crise 24 fev -> aujourd'hui

### Pilier Benchmark — "On gagne vs la concurrence ?"
- **Share of Voice** = mentions Decathlon / total (65% Decathlon vs 35% Intersport)
- Sentiment comparatif par marque
- Radar forces/faiblesses par topic (Prix, SAV, Qualite, Marques propres)
- Facebook Ads : 50 001 pubs Decathlon vs 46 387 Intersport

### Pilier CX — "Les clients sont contents ?"
- **NPS Proxy** = (5 etoiles - 1 etoile) / total x 100 = **16.7**
- Note moyenne : **3.27/5** (3 411 avis)
- Top 5 irritants (SAV injoignable 7%, Retours complexes 5%)
- Top 3 enchantements

---

## Features avancees

### Pipeline parallelise (`.\run`)
- 12 steps dont 7 en parallele (news, reddit, youtube, tiktok, instagram, x, context)
- Logs stylises ASCII (banner, progress bars, badges colores)
- `data/latest_run.json` mis a jour en temps reel apres chaque step
- Continue-on-error : si X ou product_monitor fail, le pipeline continue
- **77 min sequentiel -> 15 min parallelise (5x plus rapide)**

### Enrichissement post-ingest
- **14 topics business** : velo_mobilite, rapport_qualite_prix, sav_service_client, experience_magasin, marques_propres, livraison, retour_remboursement, prix_promotion, outdoor_randonnee, running_fitness, sports_equipe, choix_en_rayon, service_reparation, application_digitale
- **Post type detection** : crisis_alert (852), complaint (431), endorsement (911), question (73), comparison (18), review, mention
- **Brand vs Competitor tagging** : brand_only (4114), competitor_mentioned (20), comparison (7)

### Assistant IA (RAG chatbot)
- Multi-provider fallback : OpenAI -> Mistral -> OpenRouter
- System prompt hardened (8 regles absolues, anti-injection)
- Input sanitizer : regex injection (20 patterns FR/EN), rate limiting (10 msg/min), block immediat sur injection
- Output validator : bloque les leaks techniques ("system prompt", "GPT", "Mistral")
- Chat logs SQLite pour audit trail
- Cache reponses 15 min
- Markdown rendering (gras, listes, titres)

### Rapport PDF COMEX (5 pages)
- Page 1 : Couverture avec 4 KPIs cles
- Page 2 : Reputation (alerte crise, sentiment, sparkline volume)
- Page 3 : Benchmark (SoV, radar forces/faiblesses, insights)
- Page 4 : CX (NPS, irritants, enchantements, distribution etoiles)
- Page 5 : Recommandations strategiques (critique/haute/moyenne) + entites cles
- Genere automatiquement depuis les donnees live

### Facebook Ads Intelligence
- Scrape Meta Ad Library via DrissionPage (relay store JSON)
- Comparatif Decathlon (50k pubs, 1.07M fans) vs Intersport (46k pubs, 1.76M fans)
- Analyse : formats (carousel vs video), CTA ("Acheter" vs "En savoir plus"), plateformes
- Insight : Intersport a 65% plus de fans Facebook, mise plus sur la video

### Trending Opportunity (GET /api/trending)
- Detecte les trends sport/fitness depuis les donnees collectees
- Filtre par 50+ categories produit Decathlon (running, velo, randonnee, fitness...)
- Score : spike_pct x relevance
- 0 faux positifs (filtre pertinence strict)

### Auto-Discovery (GET /api/autodiscover)
- Scanne 11 000+ textes pour trouver des sources non monitorees
- Regex extraction : subreddits, hashtags, comptes Instagram/TikTok
- Filtre generique (exclut #shopping, #client, #avis...)
- Suggestions actionnables : #boycott (167), #badbuzz (163), #crise (160)

### Event Mode (POST /api/event/start)
- Monitoring haute frequence pendant evenements (crise, lancement, JO)
- Scrapers rapides toutes les N minutes (news 10s + reddit 10s + instagram 35s)
- Auto-ingest + check alertes apres chaque cycle
- Auto-stop apres 24h max
- Logs des 10 derniers cycles

### Alertes Slack/Make
- Webhook Make configure et teste
- Gravity Score > 8 -> alerte critique immediate
- Volume spike > 50% -> alerte haute
- NPS < 0 -> alerte moyenne
- Cooldown 5 min anti-spam

---

## API Endpoints (16+)

| Endpoint | Methode | Description |
|---|---|---|
| `/api/health` | GET | Status serveur |
| `/api/reputation` | GET | KPIs reputation + volume/jour + plateformes |
| `/api/benchmark` | GET | SoV + radar + brand scores |
| `/api/cx` | GET | NPS + irritants + enchantements |
| `/api/crisis` | GET | Severity + timeline + early warnings |
| `/api/recommendations` | GET | 4 recos priorisees |
| `/api/summary` | GET | Entites + risks + opportunities |
| `/api/chat` | POST | RAG chatbot (message -> reponse) |
| `/api/chat/stats` | GET | Stats sanitizer + logs |
| `/api/trending` | GET | Trends sport detectees |
| `/api/autodiscover` | GET | Suggestions nouvelles sources |
| `/api/event/start` | POST | Demarrer Event Mode |
| `/api/event/stop` | POST | Arreter Event Mode |
| `/api/event/status` | GET | Status Event Mode |
| `/api/wordcloud` | GET | Mots/themes frequents |
| `/api/report/html` | GET | Rapport COMEX HTML |
| `/api/report/pdf` | GET | Rapport COMEX PDF (A4) |
| `/api/export/excel` | GET | Export CSV (6 248 rows) |
| `/api/personas` | GET | 3 personas synthetiques |
| `/api/alert/test` | POST | Test webhook Make |
| `/api/ingest` | POST | Re-ingest manuel |

---

## Commandes

```bash
# Pipeline complet (12 steps, parallelise, ~15 min)
.\run

# Scrapers rapides seulement (~5 min)
.\run --steps news_monitor,reddit_monitor,youtube_monitor,instagram_monitor

# Dashboard (frontend + backend)
cd dashboard && npm start

# Scraper individuel
py -3.10 -m instagram_monitor --brand both
py -3.10 -m facebook_ads_monitor --brand both --max-ads 30
py -3.10 -m reddit_monitor --brand decathlon
py -3.10 -m youtube_monitor --brand both --date-filter week

# ai_batch
py -3.10 -m ai_batch --brand both --provider auto --input-run latest --chunk-size 20

# Tests
py -3.10 -m unittest discover -s tests
```

---

## Structure du repo

```
LICTER/
+-- monitor_core/           # Etat SQLite, helpers, .env loader
+-- store_monitor/          # Google Maps avis (Playwright, 40 magasins)
+-- review_monitor/         # 7 sites: Trustpilot, Glassdoor, Indeed, Custplace, Poulpeo, eBuyClub, Dealabs
|   +-- appstore.py         # App Store iOS (iTunes RSS API)
|   +-- avis_verifies.py    # Avis Verifies (HTML scrape)
|   +-- forums.py           # Forums sport FR (DDG search)
+-- reddit_monitor/         # JSON API old.reddit.com (pagination cursor, filtre FR)
+-- youtube_monitor/        # yt-dlp (8 queries, comments top 10 seulement)
+-- tiktok_monitor/         # DrissionPage + yt-dlp (hashtags + comptes)
+-- instagram_monitor/      # GraphQL API (no login, comptes officiels)
+-- x_monitor/              # Playwright + cookies
+-- news_monitor/           # Google News RSS + Cloudflare enrichment
+-- facebook_ads_monitor/   # Meta Ad Library (DrissionPage, relay store JSON)
+-- context_monitor/        # CGV, retours, livraison officiels
+-- ai_batch/               # Enrichissement IA multi-provider (skip rated, chunk 20)
+-- prod_pipeline/          # Orchestrateur parallelise avec logs stylises
+-- db/                     # Schema SQL + loader PostgreSQL/Supabase
+-- server/                 # Express + SQLite + RAG + 16 endpoints
|   +-- index.mjs           # Serveur principal (port 8000)
|   +-- db.mjs              # SQLite init + helpers + enrichment columns
|   +-- ingest.mjs          # JSONL -> SQLite au boot + topic/crisis/brand enrichment
|   +-- kpis.mjs            # Calcul KPIs (gravity, SoV, NPS, radar, irritants...)
|   +-- rag.mjs             # RAG multi-provider + hardened prompt + cache
|   +-- pdf.mjs             # Rapport PDF COMEX 5 pages
|   +-- crisis.mjs          # Detection de crise (severity, spike, timeline)
|   +-- alerts.mjs          # Webhooks Make/Slack
|   +-- trending.mjs        # Trending Opportunity (filtre par categorie produit)
|   +-- autodiscover.mjs    # Auto-Discovery nouvelles sources
|   +-- eventmode.mjs       # Event Mode haute frequence
|   +-- enrich.mjs          # Topic + post_type + brand_target detection
|   +-- middleware/
|   |   +-- sanitizer.mjs   # Anti-injection (20 patterns) + rate limiting
|   +-- routes/             # reputation, benchmark, cx, recommendations, summary, chat, report, personas
+-- dashboard/              # React 19 + Tailwind 4 + Recharts
|   +-- src/
|       +-- App.tsx          # Layout sidebar + main + chat flottant
|       +-- api/client.ts    # React Query hooks (16 endpoints)
|       +-- charts/          # CrisisLineChart, PlatformPieChart, SentimentRadar, SovBarChart, RatingDistBar, RatingLineChart, WordCloud
|       +-- components/      # KpiCard, AlertBanner, TabBar, panels/ (8 panels)
+-- data/                   # Tous les outputs JSONL par monitor et par run
+-- docs/                   # Documentation par monitor + SUJET_COMPLET.md
+-- .github/workflows/      # daily.yml + weekly.yml (cron GitHub Actions)
+-- run.bat                 # Raccourci pipeline Windows
```

---

## Optimisations pipeline

| Composant | Avant | Apres | Gain |
|---|---|---|---|
| Reddit | crawl4ai (12 min) | JSON API + pagination (10s) | **400x** |
| YouTube | 14 queries + comments all (10 min) | 8 queries + comments top 10 (3 min) | **3x** |
| ai_batch | 6249 records x API (15 min) | Skip rated 48% + chunk 20 (5 min) | **3x** |
| store_monitor | 40 magasins (30 min) | Limite 10 magasins (8 min) | **4x** |
| Pipeline total | Sequentiel (77 min) | Parallelise 7 scrapers (15 min) | **5x** |

---

## Insights cles (pitch jury)

### Reputation
- **Gravity Score 10/10** — crise velo active, 1 500+ mentions negatives
- 852 posts auto-detectes comme `crisis_alert`
- Recommandation : communique transparent + hotline dans les 48h

### Benchmark
- **SoV Decathlon 65%** vs Intersport 35%
- Intersport gagne sur les grandes marques et le maillage (935 vs 335 magasins)
- Facebook Ads : Intersport a **65% plus de fans** (1.76M vs 1.07M) et mise plus sur la video
- Decathlon domine en rapport qualite/prix (+45% SoV)

### CX
- **NPS Proxy 16.7** — positif mais fragile
- Trustpilot : Decathlon **1.70/5** vs Intersport **4.20/5**
- Top irritant : SAV injoignable (7%) — chatbot de triage recommande

### Competitif
- "On scrape les 3 memes sources que Licter (X, Instagram, TikTok) pour 0 euros au lieu de 40k euros/mois"
- Facebook Ads intelligence : insight sur les strategies pub de chaque marque
- Auto-Discovery : decouverte autonome de nouvelles sources a monitorer

---

## Comparaison avec le dataset Excel

| Source | Nos scrapers | Dataset Excel |
|---|---|---|
| Google Maps | **1 475** avis | 343 avis |
| Trustpilot | 125 avis | 365 avis |
| Reddit | **1 006** records | 846 records |
| YouTube | **175** records | -- |
| TikTok | 76 videos | 203 records |
| X/Twitter | 112 tweets | 841 records |
| Instagram | **26** posts | -- |
| Facebook Ads | **60** pubs | -- |
| App Store | **50** avis | 378 records |
| Google News | **112** articles | -- |
| Forums | 29 posts | 664 records |
| Avis Verifies | 2 records | 356 records |
| Facebook | -- | 178 records |
| LinkedIn | -- | 635 records |

**Nos scrapers apportent** : donnees fraiches, URLs verifiables, metriques engagement, YouTube + Instagram + Facebook Ads + Google News (absents du dataset), pipeline automatise continu.

**Le dataset apporte** : base historique, topics pre-categorises, labels crise, 4 plateformes non scrapees (Facebook, LinkedIn, Avis Verifies, News Forums).

**Les deux sont complementaires.** Le dataset = photo figee. Nos scrapers = camera de surveillance 24/7 avec analyste IA integre.

---

*LICTER x Eugenia School — BDD 2026*
*12 sources | 8 300+ records | 16 endpoints | 3 features autonomes | Pipeline 15 min*
