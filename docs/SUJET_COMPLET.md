# Sujet Complet — Eugenia School × Licter — Social Data Intelligence 2026

---

## Problématique

> "Une marque génère chaque jour des centaines de signaux : avis clients, mentions sociales, comparatifs concurrentiels. Comment les structurer, les analyser et les synthétiser pour qu'ils deviennent une arme stratégique pour ses décideurs ?"

Vous disposez de données sociales fictives (mentions, avis clients, comparatifs concurrentiels). Votre mission est de les transformer en **intelligence business actionnable pour un COMEX**.

---

## Marque attribuée

La marque est attribuée par **tirage au sort**. Chaque groupe travaille sur une marque différente issue du dataset fourni.

**Notre marque** : Decathlon (concurrent : Intersport)

---

## Dataset fourni

Fichier Excel sectoriel avec **3 onglets**. Les organisateurs insistent :

> "Partez de notre fichier Excel : ne perdez pas 2 jours à scraper 10 ans d'historique. Utilisez votre fichier Excel sectoriel (et ses 3 onglets), comprenez sa structure, et injectez-le dans votre environnement de travail pour avoir une base solide immédiatement."

---

## Stack technique imposée / recommandée

> "Make ou N8N sont les seuls outils imposés. Vous êtes libres sur tout le reste sauf pour l'orchestration."

| Couche | Outil recommandé | Description |
|---|---|---|
| **Orchestration** | **Make ou N8N** (obligatoire) | Seul outil imposé |
| Scraping | Apify | Extraction automatisée de données web |
| IA | OpenAI API | Moteur d'IA. Analyse sémantique, clustering thématique, scoring de sentiment, synthèse. Promptez efficacement, itérez sur la qualité des outputs |
| BDD | Supabase | Base de données PostgreSQL. Stockage centralisé. Interface entre vos automatisations Make et la visualisation Antigravity |
| Dashboard | Antigravity | Dashboards de KPIs, graphiques interactifs, pilotage en temps réel. Designez des vues claires, choisissez les bons KPIs, rendez la donnée lisible |

> "Ne scrapez pas tout depuis zéro : Apify ne sert qu'à automatiser le flux de nouvelles données."

---

## Planning jour par jour

> "Chaque jour a son objectif et son livrable intermédiaire. Le jury évaluera votre progression."

| Jour | Livrable |
|---|---|
| **J1** | Nomination du Chef de projet, garant des délais et de la communication. Création d'une feuille de route détaillant les grandes étapes, la répartition des tâches et les objectifs journaliers. |
| **J2** | Un schéma modélisant le parcours de la donnée : sources ciblées, outils d'extraction et d'automatisation envisagés, et comment la donnée est stockée avant d'être exploitée. |
| **J3** | Dashboard V1 fonctionnel (données triables/filtrables) |
| **J4** | Le flux est 100% opérationnel : le contenu est récupéré à la source, traité par le système d'automatisation, et mis à jour sur le Dashboard sans intervention manuelle. Démonstration finale du bon fonctionnement de la boucle sous forme de Loom et explication du processus. |
| **J5** | Défense du projet, présentation des insights stratégiques et démonstration. Présentation devant un jury de 4 professionnels. Vous devez convaincre que votre solution apporte de la valeur business. |

---

## 4 Livrables finaux

> "4 livrables finaux qui démontrent votre maîtrise du pipeline et votre capacité d'analyse."

1. **Vidéo Loom** — workflow N8N/Make de bout en bout (extraction → IA → BDD → dashboard)
2. **Dashboard interactif** — connecté à Supabase (Volumes, Sentiment, Alertes)
3. **Magazine exécutif PDF** — niveau cabinet de conseil, pour la Direction
4. **Présentation PPT** — support de soutenance avec insights et recommandations

---

## Critères d'évaluation

> "Voici comment votre travail sera évalué par le jury."

| Critère | Poids |
|---|---|
| Pertinence des insights (actionnables COMEX) | **30%** |
| Maîtrise technique du pipeline | **25%** |
| Qualité du dashboard | **20%** |
| Storytelling & recommandations | **15%** |
| Qualité du magazine PDF | **10%** |

---

## Vision des organisateurs — Ce qu'ils veulent que vous appreniez

### Analyse 360°
> "Une analyse 360° : Réputation, Concurrence et Expérience Client"

### Synthèse COMEX
> "La donnée croule partout. La compétence rare, ce n'est pas d'avoir accès aux données, c'est de les synthétiser. Vous apprenez à réduire 1 500 lignes de verbatims en 3 insights actionnables que le COMEX peut lire en 2 minutes."

### Pipelines autonomes
> "Vous ne serez jamais un analyste qui passe des nuits à copier-coller des données. Vous construisez des pipelines autonomes qui alimentent en continu votre base de connaissance. Un réflexe recherché dans tous les pôles Data, Marketing, et Stratégie."

### Storytelling data
> "La donnée sans narration ne vaut rien. La compétence la plus rare chez les analystes juniors, c'est de savoir transformer un chiffre complexe en un récit convaincant pour des décideurs non-techniques. Votre magazine COMEX vous y entraîne."

### Exemple d'insight attendu
> "Le NPS de notre SAV chute de 40% les lundis matins sur Trustpilot"

---

## Do's & Don'ts (extraits du site)

**Do's** :
- Chaque graphique doit répondre à une question
- Penser COMEX en permanence

**Don'ts** :
- Ne négligez pas le magazine : c'est le livrable évalué
- N'oubliez pas la vidéo Loom : indispensable pour la validation technique

---

## Intervenants jury

- Victor Phouangsavath — Consultant Social Data Analyst @ Licter
- Noah Segonds — Data Analyst Customer Growth @ Decathlon Digital

---

# Notre approche vs le sujet — Bilan

## Ce qu'on fait bien ✓

| Exigence sujet | Notre réponse |
|---|---|
| Dataset Excel 3 onglets ingéré | ✓ `data/excel_runs/` — 4 809 records chargés |
| Scraping automatisé | ✓ 9 scrapers (Google Maps, Trustpilot, Reddit, YouTube, TikTok, X, News, Context, Products) |
| Enrichissement IA (sentiment, topics) | ✓ `ai_batch` avec Mistral — 6 249 records enrichis |
| Dashboard interactif | ✓ React + Express + SQLite — 8 onglets (Réputation, Benchmark, CX, Recommandations, Synthèse, Personas, Assistant IA, Crise) |
| Pipeline autonome | ✓ `prod_pipeline` avec `.\run` — 11 steps, cron GitHub Actions prêt |
| Rapport PDF COMEX | ✓ `GET /api/report/pdf` — 5 pages auto-générées |
| 3 piliers (Réputation, Benchmark, CX) | ✓ Exactement ce qui est demandé |
| Insights actionnables | ✓ Gravity Score, SoV, NPS proxy, top irritants, recommandations priorisées |
| Assistant IA (RAG) | ✓ Chat Mistral avec contexte KPIs — **bonus non demandé** |
| Synthetic Personas | ✓ 3 personas auto-générés — **bonus non demandé** |
| Détection de crise | ✓ Severity, timeline, early warnings — **bonus non demandé** |

## Points d'attention ⚠

| Exigence | Statut | Action |
|---|---|---|
| **N8N/Make obligatoire** | ⚠ N8N en façade seulement (3 nœuds) | Créer un workflow N8N visible qui trigger le pipeline Python via webhook |
| **Vidéo Loom** | ⚠ Pas encore filmée | Filmer maintenant avec le script préparé |
| **Supabase** | ⚠ Pas connecté | Pousser les données vers Supabase pour que le jury puisse voir la BDD |
| **Antigravity** | ⚠ Non utilisé (React custom) | Peut-être mentionner en backup, dashboard React est plus impressionnant |
| **Magazine PDF** | ✓ Mais à peaufiner | Le PDF existe mais peut être amélioré visuellement |
| **PPT** | ❌ Pas encore créé | Créer les slides de soutenance J5 |

## Tu es sur la bonne voie ?

**OUI — largement.** Tu dépasses les attentes sur :
- Volume de données (6 249 records vs le dataset Excel seul)
- Nombre de sources (9 scrapers vs "utilisez Apify")
- Features avancées (RAG, Personas, Crise, PDF auto)
- Pipeline technique (Express + SQLite + React vs Make + Supabase + Antigravity basique)

**Les 3 risques** :
1. **N8N** — Le jury va vérifier que N8N/Make est bien utilisé. Un workflow visible est obligatoire.
2. **Loom** — C'est un livrable. Pas de Loom = pénalité.
3. **PPT** — Support de soutenance pas encore fait.
