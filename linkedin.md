# Licteur - LinkedIn #Decathlon Scraper

Script Python qui recherche et collecte les posts LinkedIn publics mentionnant **#Decathlon**, postÃ©s par des personnes **externes** Ã  l'entreprise Decathlon.

## Ce que fait le script

1. Recherche des posts via DuckDuckGo (pas besoin de compte LinkedIn) â€” 33 requÃªtes au total
2. Scrape le contenu public de chaque post trouvÃ© (meta tags, JSON-LD, HTML)
3. Filtre automatiquement les posts de Decathlon et de ses employÃ©s
4. Ne garde que les posts des **21 derniers jours**
5. TÃ©lÃ©charge les images dans un dossier `images/`
6. GÃ©nÃ¨re un rÃ©sumÃ© de chaque post via **Claude Haiku** (AI)
7. Exporte tout dans `resultats_decathlon.json`

> Les URLs bloquÃ©es par LinkedIn (code 999) sont quand mÃªme conservÃ©es dans le JSON avec le statut `non_scraped_linkedin_bloque`.

## Installation

```bash
# 1. Installer les dÃ©pendances
pip install -r requirements.txt

# 2. Configurer la clÃ© API Claude (pour les rÃ©sumÃ©s)
cp .env.example .env
# Puis Ã©dite .env et mets ta clÃ© ANTHROPIC_API_KEY
```

### Obtenir une clÃ© API Anthropic

1. Va sur https://console.anthropic.com/
2. CrÃ©e un compte (gratuit)
3. Va dans **API Keys > Create Key**
4. Copie la clÃ© dans ton fichier `.env`

> Sans clÃ© API, le script fonctionne quand mÃªme mais les rÃ©sumÃ©s seront juste le texte tronquÃ© (200 caractÃ¨res).

## Utilisation

```bash
python scraper.py
```

Le script va :
- Chercher sur tous les hashtags Decathlon (France, UK, India, etc.)
- Afficher sa progression en temps rÃ©el (5 Ã©tapes numÃ©rotÃ©es)
- CrÃ©er `resultats_decathlon.json` et le dossier `images/`

## Structure du JSON de sortie

```json
{
  "metadata": {
    "date_extraction": "2026-03-18T10:00:00",
    "periode": "derniers 21 jours",
    "hashtags_recherches": ["#decathlon", "#DecathlonFrance", "..."],
    "nombre_recherches": 33,
    "nombre_urls_trouvees": 120,
    "nombre_posts_scrapes": 75,
    "nombre_posts_non_scrapes": 45,
    "nombre_posts_total": 120
  },
  "posts": [
    {
      "url": "https://linkedin.com/posts/...",
      "auteur": "Jean Dupont",
      "titre_auteur": "Coach sportif indÃ©pendant",
      "date": "2026-03-15",
      "texte": "Contenu complet du post...",
      "resume": "RÃ©sumÃ© gÃ©nÃ©rÃ© par Claude AI...",
      "statut": "scraped",
      "mentions": ["@Nike", "@Adidas"],
      "images": ["https://...original_url"],
      "images_locales": ["images/jean-dupont_a1b2c3.jpg"],
      "nb_likes": 150,
      "nb_commentaires": 12,
      "commentaires": []
    }
  ]
}
```

**Valeurs possibles pour `statut`** :
- `scraped` â€” post rÃ©cupÃ©rÃ© avec succÃ¨s
- `non_scraped_linkedin_bloque` â€” URL trouvÃ©e mais LinkedIn a bloquÃ© le scraping

## Limitations

- **Posts publics uniquement** : seuls les posts visibles sans connexion LinkedIn sont accessibles
- **Couverture partielle** : dÃ©pend de ce que DuckDuckGo a indexÃ©
- **Pas de commentaires** : LinkedIn ne rend pas les commentaires accessibles sans authentification
- **Rate limiting** : des dÃ©lais alÃ©atoires (2-5 s) sont ajoutÃ©s entre les requÃªtes
- **LinkedIn peut bloquer** : si trop de requÃªtes, LinkedIn renvoie un code 999 â€” les URLs sont quand mÃªme conservÃ©es

## Hashtags recherchÃ©s

Le script cherche automatiquement ces variantes :
- `#decathlon`, `#DecathlonFrance`, `#DecathlonSport`
- `#DecathlonIndia`, `#DecathlonItalia`, `#DecathlonBelgium`
- `#DecathlonPolska`, `#DecathlonDeutschland`
- `#DecathlonUK`, `#DecathlonBrasil`, `#DecathlonCanada`

Plus des recherches thÃ©matiques : avis client, partenariat, innovation, marques propres (Quechua, Kipsta, Domyos, B'Twin, Forclaz, Kalenji, Tribord, Nabaiji, Rockriderâ€¦).

Tu peux modifier la liste `HASHTAGS` et `SEARCH_QUERIES` dans `scraper.py` pour ajouter d'autres variantes.

## DÃ©pendances

| Package | RÃ´le |
|---|---|
| `requests` | RequÃªtes HTTP |
| `beautifulsoup4` | Parsing HTML |
| `ddgs` | Recherche DuckDuckGo |
| `anthropic` | RÃ©sumÃ©s via Claude Haiku |
| `python-dotenv` | Chargement du `.env` |