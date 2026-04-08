# LICTER : Brand Intelligence Platform

> **Hackathon Eugenia School x Licter 2026**
> Plateforme autonome de veille, analyse et visualisation de la reputation de marque.
> Decathlon vs Intersport. 13 scrapers. 16 000+ records. 7 223 vecteurs. Dashboard COMEX temps reel.

**[Dashboard en production](https://licter-dashboard.pages.dev)** | **[API Workers](https://licter-api.sales-bwcapital.workers.dev/api/health)** | **[Rapport PDF COMEX](https://licter-dashboard.pages.dev/rapport-comex.pdf)**

---

## Le projet en 30 secondes

Un membre du COMEX Decathlon n'a que 2 minutes. Notre plateforme lui permet de :

1. **Voir** que la crise velo est a Gravity Score 10/10 et que 1 500+ mentions negatives circulent depuis 15 jours
2. **Comprendre** que le SAV represente 40% des avis negatifs (Trustpilot 1.7/5 vs Intersport 4.2/5)
3. **Agir** avec 5 recommandations priorisees : communique de crise 48h, chatbot SAV, campagne marques propres
4. **Comparer** : Decathlon domine sur le prix (73%) et les marques propres (81%), Intersport gagne sur la qualite percue (60%) et le maillage (935 magasins)

Tout ca est alimente en continu par 13 scrapers automatises, enrichi par IA (GPT-4o-mini), indexe dans une base vectorielle (7 223 vecteurs), et deploye sur Cloudflare.

---

## Architecture

```
                    13 SCRAPERS PYTHON                            CLOUDFLARE STACK
                                                          
  reddit_monitor    (JSON API, 10s)        ──┐        ┌── Workers (API REST, 20+ endpoints)
  youtube_monitor   (yt-dlp + comments)    ──┤        ├── D1 (SQLite, 16 000+ records)
  tiktok_monitor    (DrissionPage + yt-dlp)──┤        ├── Vectorize (7 223 embeddings)
  x_monitor         (Playwright + cookies) ──┤        ├── Pages (React dashboard)
  instagram_monitor (GraphQL, no login)    ──┤        └── MCP Server (8 tools, JSON-RPC)
  news_monitor      (Google News RSS)      ──┤                     
  store_monitor     (Google Maps, Playwright)┤   ai_batch          DASHBOARD COMEX
  review_monitor    (7 sites d'avis)       ──┤   (gpt-4o-mini)    
  facebook_ads      (Meta Ad Library)      ──┼──────────────┐  ┌── Reputation (crise, gravity)
  facebook_groups   (DrissionPage)         ──┤              │  ├── Benchmark (SoV, radar 6 axes)
  app_store         (iTunes RSS)           ──┤   4 passes:  ├──├── Experience Client (NPS, marques)
  forums_monitor    (DDG search)           ──┤   sentiment  │  ├── Recommandations (5 recos)
  context_monitor   (CGV officiels)        ──┘   topic      │  ├── SWOT Social Data
                                                 crisis     │  ├── LLM Visibility (4 modeles)
  Dataset Excel fourni (3 onglets)         ──────brand ─────┘  ├── Pipeline IA (Transcripts, Trending)
                                                               ├── Event Mode (temps reel)
  Orchestration: prod_pipeline (parallelise)                   ├── Comparateur IA
  77 min sequentiel → 15 min parallelise                       ├── Explorateur de donnees
  GitHub Actions: cron daily + weekly                          └── Chatbot RAG (Vectorize)
```

---

## Stack technique

| Couche | Technologie | Pourquoi ce choix |
|---|---|---|
| **Scraping** | Python 3.10, yt-dlp, DrissionPage, Playwright | Chaque plateforme a son anti-bot, chaque scraper est adapte |
| **IA** | OpenAI gpt-4o-mini via OpenRouter | Impose par le jury, ~$0.02 pour 8 000 records |
| **RAG** | Cloudflare Vectorize + OpenAI embeddings | 7 223 vecteurs, recherche semantique cosine similarity |
| **Backend** | Cloudflare Workers + D1 | Edge computing, latence <50ms, cout zero |
| **Frontend** | React 19 + Tailwind CSS 4 + Recharts | Dashboard responsive, 9 onglets, chat flottant |
| **Alertes** | Make webhook → Slack | Gravity > 8 = alerte critique immediate |
| **MCP** | JSON-RPC sur Workers | 8 tools accessibles depuis Claude, ChatGPT, Cursor |
| **PDF** | Chrome headless → HTML → PDF | Magazine COMEX 5 pages narratif |

---

## Donnees collectees

### En production (Cloudflare D1)

| Table | Volume | Description |
|---|---|---|
| `social_enriched` | **4 063** | Reddit 389, YouTube 165, TikTok 27, X/Twitter 74, Instagram 24, Facebook 12, Excel 3 367 |
| `review_enriched` | **1 913** | Trustpilot, Custplace, App Store, Glassdoor, Indeed, Poulpeo, eBuyClub, Excel CX |
| `store_reviews` | **1 403** | Google Maps (59 magasins grandes villes FR, Decathlon + Intersport) |
| `news_enriched` | **101** | Google News articles presse |
| `decathlon_products` | **4 541** | Catalogue produits scrape (correlation avis/marques) |
| `entity_summaries` | **217** | Syntheses IA par entite |
| `excel_*` | **4 809** | 3 datasets fournis (Reputation 767, Benchmark 2 600, CX 1 442) |

**Total : 17 047 records en base, 7 223 vecteurs indexes**

### Donnees brutes (dans ce repo)

```
data/
├── reddit_runs/      389 posts + commentaires (JSON API, pagination cursor)
├── youtube_runs/     174 videos + commentaires (yt-dlp, transcripts Whisper)
├── tiktok_runs/       43 videos (DrissionPage hashtags + comptes officiels)
├── x_runs/           212 tweets (Playwright login, cookies auth_token + ct0)
├── instagram_runs/    26 posts (GraphQL API, no login required)
├── facebook_runs/      7 posts groupes (Running Club France, Groupe DECATHLON)
├── facebook_ads_runs/  pubs Meta Ad Library (50k Dec vs 46k Intersport)
├── news_runs/        111 articles Google News
├── store_runs/       934 avis Google Maps (Playwright scroll + reviews extraction)
├── product_runs/     114 fiches produit
├── context_runs/       4 documents CGV/retours/livraison
├── ai_runs/       17 859 records enrichis IA (sentiment, topic, crisis, brand)
├── pipeline_runs/     logs d'execution parallelises
└── dataset_decathlon.xlsx  (fourni par les organisateurs)
```

---

## Dashboard COMEX : 9 onglets

### GENERAL

| Onglet | Ce qu'il montre | KPIs cles |
|---|---|---|
| **Reputation** | Crise velo, timeline 14j, word cloud, smart playbook H+0 a J+7 | Gravity 10/10, Volume 4 750, Negatif 32% |
| **Benchmark** | Decathlon vs Intersport, radar 6 axes, opportunite strategique | SoV 67/33%, Prix 73%, Marques propres 81% |
| **Experience Client** | Irritants/enchantements, verbatims negatifs, analyse marques | NPS +16.7, SAV 40% des negatifs |
| **Recommandations** | 5 actions priorisees avec impact et KPI cible | Critique → Haute → Moyenne |

### OUTILS AVANCES

| Onglet | Ce qu'il montre |
|---|---|
| **SWOT** | Forces/Faiblesses/Opportunites/Menaces genere depuis les donnees sociales |
| **LLM Visibility** | 4 LLMs testes (GPT-4o, Gemini 2.0, Claude 3.5, Perplexity), reponses completes |
| **Pipeline IA** | Transcripts video (Groq Whisper), Trending Opportunities, Auto-Discovery sources |
| **Event Mode** | Monitoring haute frequence, 6 scrapers toutes les N minutes, logs temps reel |
| **Explorateur** | Navigation dans toutes les tables, filtres source/marque/sentiment, liens vers sources |

---

## 5 insights cles pour le jury

### 1. Crise structurelle (Gravity 10/10)
> 1 500+ mentions negatives en 15 jours sur l'accident velo defectueux. Pic viral 7-10 mars. Appels au boycott relayes par des comptes verifies sur TikTok, X et Reddit. L'absence de reponse officielle apres 6 semaines aggrave la situation.
>
> **Recommandation** : Communique transparent + hotline dans les 48h. Impact estime : -60% volume negatif en 7 jours.

### 2. SAV = levier #1 d'amelioration
> 40% de TOUS les avis negatifs portent sur le service apres-vente. Trustpilot : Decathlon 1.7/5 vs Intersport 4.2/5. C'est un ecart de 2.5 points qui ne s'explique pas par la taille.
>
> **Recommandation** : Chatbot SAV premiere reponse (60% des tickets niveau 1). Objectif : NPS +15 pts Q3.

### 3. Avantage concurrentiel a proteger
> Decathlon domine sur le prix (73% vs 45%) et les marques propres (81% vs 35%). Mais Intersport gagne sur la qualite percue (60% vs 20%) et le maillage territorial (935 vs 335 magasins).
>
> **Recommandation** : Amplifier "Sport accessible a tous". Ne PAS attaquer Intersport sur les grandes marques.

### 4. Visibilite IA : avantage strategique
> Decathlon cite en 1er par 85% des LLMs (GPT-4o, Gemini, Claude, Perplexity). Intersport a 40%. C'est un avantage competitif nouveau que peu d'entreprises mesurent.

### 5. Analyse marques propres
> Quechua est la marque la plus appreciee (18 mentions positives). Riverside/Elops concentre le plus de critiques (8 avis negatifs, principalement velos electriques). Van Rysel et Domyos sont bien percues.

---

## Features differenciantes

### RAG Vectoriel (7 223 vecteurs)
On n'a pas juste un chatbot qui repond au pif. Chaque texte (avis, tweet, article) est converti en vecteur 1024 dimensions via OpenAI text-embedding-3-small, indexe dans Cloudflare Vectorize. Quand un utilisateur pose une question, on cherche les textes semantiquement proches (cosine similarity), on les injecte comme contexte dans le prompt, et le LLM repond avec des sources verifiables. 7 223 vecteurs indexes, latence <200ms.

### LLM Visibility Multi-modeles
On pose 5 questions a 4 LLMs differents (GPT-4o, Gemini 2.0, Claude 3.5, Perplexity) via OpenRouter en parallele. On analyse : est-ce que Decathlon est mentionne ? Cite en premier ? Avec quel sentiment ? Les reponses completes sont consultables au clic. Resultat cache en D1 (24h). Decathlon mentionne dans 90% des reponses.

### Pipeline parallelise (77 min → 15 min)
13 scrapers dont 7 en parallele. Reddit passe de 12 min (crawl4ai) a 10 secondes (JSON API). ai_batch skip les records deja enrichis (48% d'economie). Continue-on-error : si X/Twitter fail (cookies expires), le pipeline continue.

### Event Mode
Pendant une crise ou un lancement, on active le monitoring haute frequence : 6 scrapers toutes les 5 minutes, re-ingest automatique, calcul KPIs en temps reel, alertes si les seuils sont depasses. Auto-stop configurable (max 24h).

### Correlation avis/produits
4 541 produits Decathlon scraped (URL, titre, image, marque, categorie). On cherche les noms de marques propres (Kiprun, Quechua, Domyos, Rockrider...) dans les vrais avis clients pour identifier quelles gammes concentrent les critiques et les eloges.

### MCP Server (Model Context Protocol)
8 tools accessibles depuis Claude Desktop, ChatGPT, Cursor : `get_brand_kpis`, `search_mentions`, `get_top_irritants`, `get_trending_topics`, `compare_brands`, `get_crisis_alerts`, `get_content_strategy`, `get_influencers`. JSON-RPC sur Cloudflare Workers.

---

## Optimisations pipeline

| Composant | Avant | Apres | Gain |
|---|---|---|---|
| Reddit | crawl4ai (12 min) | JSON API + pagination (10s) | **400x** |
| YouTube | 14 queries + all comments (10 min) | 8 queries + top 10 comments (3 min) | **3x** |
| ai_batch | 6 249 records (15 min) | Skip rated 48% + chunk 20 (5 min) | **3x** |
| Pipeline total | Sequentiel (77 min) | Parallelise 7 scrapers (15 min) | **5x** |
| LLM Visibility | 20 appels sequentiels (timeout) | 20 appels paralleles (8s) | **10x** |

---

## Commandes

```bash
# Pipeline complet (13 steps, parallelise, ~15 min)
.\run

# Scrapers individuels
py -3.10 -m reddit_monitor --brand both
py -3.10 -m youtube_monitor --brand both --date-filter week
py -3.10 -m x_monitor --brand decathlon --latest-count 10
py -3.10 -m tiktok_monitor --brand both
py -3.10 -m instagram_monitor --brand both
py -3.10 -m store_monitor --brand decathlon --limit-stores 10

# Enrichissement IA
py -3.10 -m ai_batch --brand both --provider auto --input-run latest

# Tests (55 tests)
py -3.10 -m unittest discover -s tests

# Deploy
cd worker && npx wrangler deploy
cd dashboard && npx vite build && npx wrangler pages deploy dist
```

---

## Structure du repo

```
LICTER/
├── monitor_core/           # Etat SQLite, helpers Cloudflare, .env loader
├── reddit_monitor/         # JSON API old.reddit.com (pagination cursor)
├── youtube_monitor/        # yt-dlp (8 queries, comments, transcripts Whisper)
├── tiktok_monitor/         # DrissionPage + yt-dlp (hashtags + comptes)
├── instagram_monitor/      # GraphQL API (no login, comptes officiels)
├── x_monitor/              # Playwright + cookies auth_token/ct0
├── news_monitor/           # Google News RSS + Cloudflare enrichment
├── store_monitor/          # Google Maps avis (Playwright, discovery + reviews)
├── review_monitor/         # 7 sites: Trustpilot, Glassdoor, Indeed, Custplace...
├── facebook_ads_monitor/   # Meta Ad Library (DrissionPage)
├── context_monitor/        # CGV, retours, livraison officiels
├── ai_batch/               # Enrichissement IA multi-provider (4 passes)
├── prod_pipeline/          # Orchestrateur parallelise avec logs
├── db/                     # Schema SQL + loader
├── worker/                 # Cloudflare Worker (D1 + Vectorize + 20 endpoints)
├── dashboard/              # React 19 + Tailwind 4 + Recharts (9 onglets)
├── server/                 # Express local (SQLite + RAG + PDF + Event Mode)
├── licter-mcp/             # MCP server local (8 tools)
├── scripts/                # Helpers d'indexation vectorielle
├── data/                   # Toutes les donnees brutes (JSONL par monitor)
├── docs/                   # Documentation par monitor
└── decathlon_products.csv  # 4 541 produits scraped
```

---

## API Endpoints (20+)

| Endpoint | Description |
|---|---|
| `GET /api/reputation` | KPIs reputation + volume/jour + gravity score |
| `GET /api/benchmark` | SoV + radar 6 axes + brand scores |
| `GET /api/cx` | NPS + irritants + enchantements |
| `GET /api/cx/top-products` | Marques les plus citees dans les avis (cache D1) |
| `GET /api/crisis` | Severity + timeline + early warnings |
| `GET /api/recommendations` | 5 recos priorisees |
| `GET /api/llm-visibility` | 4 LLMs testes (cache D1 24h) |
| `GET /api/wordcloud` | Mots et themes frequents |
| `POST /api/chat` | RAG chatbot (Vectorize + OpenAI) |
| `GET /api/admindb` | Explorateur DB avec filtres |
| `GET /api/swot` | SWOT genere depuis les donnees |
| `POST /mcp` | MCP JSON-RPC (8 tools) |

---

## Comparaison avec les outils pro

| Fonctionnalite | Licter (40k€/an) | Notre plateforme (0€) |
|---|---|---|
| Sources monitorees | ~5 (Twitter, Insta, TikTok) | **13** (+ Reddit, YouTube, Google Maps, Facebook Ads, Forums) |
| Enrichissement IA | Proprietary | **gpt-4o-mini** (transparent, reproductible) |
| RAG chatbot | Non | **7 223 vecteurs** avec sources verifiables |
| LLM Visibility | Non | **4 modeles** testes en parallele |
| Event Mode | Non | **Monitoring toutes les 5 min** |
| Catalogue produits | Non | **4 541 produits** correles aux avis |
| MCP Server | Non | **8 tools** pour Claude/ChatGPT/Cursor |
| Cout | 40 000€/an | **~5€** (API OpenAI + OpenRouter) |

---

*LICTER x Eugenia School BDD 2026*
*13 sources | 17 047 records | 7 223 vecteurs | 20+ endpoints | 4 541 produits | Cloudflare edge*
