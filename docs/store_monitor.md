# Store Monitor (Google Maps)

## Fonctionnement

**Discovery magasins Decathlon** (`decathlon.fr/store-locator`) — scrape la liste des magasins depuis le store locator officiel, ou charge un inventaire JSON local (`decathlon_france.json`)

**Discovery magasins Intersport** (`intersport.fr/nos-magasins/`) — scrape via Playwright le locator officiel. Si bloque par DataDome (anti-bot), fallback automatique vers Google Maps Search ("Intersport Paris", "Intersport Lyon"...) par ville

**Enrichissement PagesJaunes** (optionnel) — pour les magasins sans adresse complete, recherche sur PagesJaunes via Cloudflare Browser Rendering pour recuperer adresse, code postal, ville

**Scraping avis Google Maps** (Playwright) — pour chaque magasin, ouvre la fiche Google Maps, clique sur l'onglet "Avis", trie par "Plus recent", scroll jusqu'a 40 avis max, parse chaque avis : auteur, note (1-5 etoiles), date, texte

**Mode incremental** (StateStore SQLite) — avant de scraper un magasin, probe les 5 premiers avis pour calculer un hash de signature. Si rien n'a change depuis le dernier run -> skip

**Anti-detection** — rotation de User-Agent, redemarrage du navigateur tous les 25 magasins, pauses aleatoires entre chaque magasin, suppression du flag `navigator.webdriver`

**Deduplication** — magasins dedupliques par (brand, store_name), avis dedupliques par (auteur, date, texte)

## Sortie

`data/store_runs/{run_id}/` :
- `stores.jsonl` — magasins (nom, adresse, code postal, ville, url Google Maps, status discovery)
- `reviews.jsonl` — avis (auteur, note, date, texte, note agregee du magasin, nombre total d'avis)
- `results.md` — resume avec stats par marque et exemples d'avis

## Usage

```bash
# Discovery + reviews
py -3.10 -m store_monitor --brand both --stage all

# Discovery seulement (pas de scraping avis)
py -3.10 -m store_monitor --brand both --stage discovery

# Limiter a 5 magasins pour test
py -3.10 -m store_monitor --brand decathlon --stage all --limit-stores 5
```

## Statut

**OK** — 1 475 avis, 40 magasins au dernier run. Scraping lent (Playwright ouvre chaque fiche une par une) mais fonctionnel.
