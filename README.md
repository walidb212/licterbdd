# LICTER — Brand Intelligence Platform

**Hackathon Eugenia School x Licter — Social Data Intelligence 2026**

Plateforme autonome de veille, analyse et visualisation de la reputation de marque pour Decathlon vs Intersport. 13 scrapers, enrichissement IA, dashboard COMEX avec RAG chatbot, MCP server, deploye sur Cloudflare.

---

## Architecture

```
COLLECTE (13 sources)              ENRICHISSEMENT                DASHBOARD COMEX (Cloudflare Pages)
                                                          
store_monitor (Google Maps)  --+                          +-- Reputation (Gravity Score, crise velo)
review_monitor (7 sites)     --+                          +-- Benchmark (SoV, radar forces/faiblesses)
reddit_monitor (JSON API)    --+   ai_batch               +-- Experience Client (NPS, irritants, marques)
youtube_monitor (yt-dlp)     --+-> (OpenAI gpt-4o-mini)   +-- Recommandations COMEX (5 recos priorisees)
tiktok_monitor (DrissionPage)--+   + topic detection      +-- SWOT Social Data
instagram_monitor (GraphQL)  --+   + crisis detection     +-- LLM Visibility (GPT, Gemini, Claude, Perplexity)
x_monitor (Playwright)       --+   + brand vs competitor  +-- Pipeline IA (Transcripts, Trending, Discovery)
news_monitor (Google News)   --+                          +-- Event Mode (monitoring temps reel)
facebook_ads_monitor (Meta)  --+                          +-- Comparateur IA (Content Compare)
app_store (iTunes RSS)       --+                          +-- Explorateur de donnees (Admin DB)
forums (DDG search)          --+                          +-- Assistant IA (RAG chatbot, 7223 vecteurs)
context_monitor (CGV)        --+                          +-- Rapport PDF COMEX (5 pages)
Dataset Excel (3 onglets)    --+                          +-- Export Excel
                                                          
Orchestration: prod_pipeline (.\run)                     API: Cloudflare Workers (D1 + Vectorize)
Parallelisation: 7 scrapers simultanes                   Alertes: Make webhook -> Slack
Cron: GitHub Actions (daily + weekly)                    MCP Server: 8 tools (Claude, ChatGPT, Cursor)
```

---

## Stack technique

| Couche | Technologie |
|---|---|
| **Scraping** | Python 3.10 — yt-dlp, DrissionPage, Playwright, crawl4ai, urllib |
| **IA enrichissement** | OpenAI gpt-4o-mini via OpenRouter, fallback heuristic |
| **IA chatbot** | RAG vectoriel (Cloudflare Vectorize, 7 223 vecteurs, OpenAI embeddings) |
| **Backend prod** | Cloudflare Workers (D1 SQLite, Vectorize, Pages) |
| **Backend local** | Node.js 22 — Express, better-sqlite3 |
| **Frontend** | React 19, Tailwind CSS 4, Recharts |
| **Orchestration** | N8N/Make (facade), GitHub Actions (cron daily+weekly) |
| **Alertes** | Make webhook -> Slack (gravity > 8 = critique, spike > 50% = haute) |
| **PDF** | Chrome headless (HTML -> PDF A4, 5 pages narratives) |
| **MCP** | Remote JSON-RPC sur Workers (8 tools) |

---

## Donnees en production (Cloudflare D1)

| Table | Volume | Description |
|---|---|---|
| `social_enriched` | 4 100+ | Reddit, YouTube, TikTok, X/Twitter, Instagram, Facebook, Excel |
| `review_enriched` | 1 913 | Trustpilot, Custplace, App Store, Excel CX |
| `news_enriched` | 101 | Google News articles |
| `store_reviews` | 1 400+ | Google Maps avis (59 magasins grandes villes FR) |
| `entity_summaries` | 217 | Syntheses par entite |
| `decathlon_products` | 4 541 | Catalogue produits (correlation avis/marques) |
| `excel_reputation` | 767 | Dataset crise velo |
| `excel_benchmark` | 2 600 | Dataset benchmark 12 mois |
| `excel_cx` | 1 442 | Dataset voix du client |

**Total : ~16 000+ records en base, 7 223 vecteurs indexes**

---

## Dashboard COMEX (9 onglets)

### GENERAL (4 onglets)
- **Reputation** — Gravity Score 10/10, timeline crise 14j, word cloud, smart playbook H+0 a J+7
- **Benchmark** — SoV 67%/33%, radar 6 topics, matrice forces/faiblesses, opportunite Decathlon
- **Experience Client** — NPS 16.7, irritants/enchantements contextuels, verbatims negatifs, analyse marques
- **Recommandations** — 5 recos priorisees (critique/haute/moyenne), badges colores, pilier tags

### OUTILS AVANCES (5 onglets)
- **SWOT** — Forces/Faiblesses/Opportunites/Menaces genere depuis les donnees
- **LLM Visibility** — 4 modeles testes (GPT-4o, Gemini 2.0, Claude 3.5, Perplexity), reponses completes expandables
- **Pipeline IA** — Transcripts video (Groq Whisper), Trending Opportunities, Auto-Discovery sources
- **Event Mode** — Monitoring haute frequence, 6 scrapers, logs temps reel, historique events
- **Explorateur** — Navigation dans toutes les tables, filtres par source/marque/sentiment, liens vers sources

---

## Features differenciantes

### RAG Vectoriel (7 223 vecteurs)
- Indexation de tous les textes (social, avis, news) via OpenAI text-embedding-3-small
- Recherche semantique cosine similarity via Cloudflare Vectorize
- Chatbot avec context RAG + system prompt hardened + input sanitizer anti-injection
- Correlation avis/marques via recherche semantique dans le catalogue produit

### LLM Visibility Multi-modeles
- 5 questions posees a 4 LLMs en parallele via OpenRouter
- Decathlon mentionne dans 90% des reponses, cite en 1er dans 85%
- Reponses completes stockees en cache D1 (24h), expandables au clic
- Markdown rendering (gras, listes)

### Pipeline parallelise (77 min -> 15 min)
- 13 steps dont 7 en parallele
- Continue-on-error : si un scraper fail, le pipeline continue
- ai_batch : skip rated (48% savings), chunk size 20
- Reddit JSON API : 400x plus rapide que crawl4ai

### Event Mode
- Monitoring haute frequence (scrape toutes les N minutes)
- 6 scrapers : news, reddit, instagram, tiktok, youtube, x
- Auto-ingest + calcul KPIs + alertes automatiques
- Auto-stop configurable (max 24h)

---

## API Endpoints (20+)

| Endpoint | Description |
|---|---|
| `/api/reputation` | KPIs reputation + volume/jour |
| `/api/benchmark` | SoV + radar forces/faiblesses |
| `/api/cx` | NPS + irritants + enchantements |
| `/api/cx/top-products` | Marques les plus citees (cache D1) |
| `/api/crisis` | Severity + timeline + warnings |
| `/api/recommendations` | 5 recos priorisees |
| `/api/llm-visibility` | 4 LLMs testes, reponses completes |
| `/api/wordcloud` | Mots/themes frequents |
| `/api/chat` | RAG chatbot (Vectorize + OpenAI) |
| `/api/admindb` | Explorateur DB avec filtres |
| `/api/influencers` | Top auteurs par engagement |
| `/api/heatmap` | Carte sentiment par magasin |
| `/mcp` | MCP JSON-RPC (8 tools) |

---

## Commandes

```bash
# Pipeline complet (13 steps, parallelise, ~15 min)
.\run

# Scraper individuel
py -3.10 -m reddit_monitor --brand both
py -3.10 -m youtube_monitor --brand both --date-filter week
py -3.10 -m x_monitor --brand decathlon --latest-count 10
py -3.10 -m tiktok_monitor --brand both
py -3.10 -m instagram_monitor --brand both

# ai_batch enrichissement
py -3.10 -m ai_batch --brand both --provider auto --input-run latest

# Tests (55 tests)
py -3.10 -m unittest discover -s tests

# Deploy
cd worker && npx wrangler deploy
cd dashboard && npx vite build && npx wrangler pages deploy dist
```

---

## Insights cles (pitch jury)

**Insight 1 — Crise structurelle** : 1 500+ mentions negatives en 15 jours sur l'accident velo. Gravity Score 10/10. Recommandation : communique transparent + hotline dans les 48h. Impact : -60% negatif en 7j.

**Insight 2 — Avantage concurrentiel** : Decathlon domine sur le prix (73% vs 45%) et les marques propres (81% vs 35%). Intersport gagne sur le maillage (935 vs 335 magasins) et la qualite percue (60% vs 20%). Ne pas attaquer Intersport sur son terrain.

**Insight 3 — SAV = levier #1** : 40% des avis negatifs portent sur le SAV. Trustpilot : Decathlon 1.7/5 vs Intersport 4.2/5. Un chatbot premiere reponse reduirait 60% des tickets. Objectif : NPS +15 pts Q3.

**Insight 4 — Visibilite IA** : Decathlon cite en 1er par 85% des LLMs (GPT, Gemini, Claude, Perplexity). Intersport a 40%. Avantage strategique a proteger.

**Insight 5 — Marques propres** : Quechua et Riverside concentrent les critiques (qualite percue). Van Rysel et Domyos sont les marques les plus appreciees. B'Twin en tete des mentions positives cyclisme.

---

*LICTER x Eugenia School — BDD 2026*
*13 sources | 16 000+ records | 7 223 vecteurs | 20+ endpoints | Cloudflare Workers + D1 + Vectorize + Pages*
