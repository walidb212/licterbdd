# Commerce Signal Summary - eBuyClub / Dealabs / Next Data

## Runs validates

### eBuyClub
- Run: `20260312T124225899669Z_4c5c55`
- Resultat: `2` vrais avis retenus apres filtrage promo parasite
- Decathlon: `1` avis, note agregée `5.0`, volume `5184`
- Intersport: `1` avis, note agregée `5.0`, volume `44`
- Fichier: `data/review_runs/20260312T124225899669Z_4c5c55/results.md`

### Dealabs
- Run: `20260312T124225905152Z_d9f8fd`
- Resultat: `60` signaux promo
- Decathlon: `30`
- Intersport: `30`
- Fichier: `data/review_runs/20260312T124225905152Z_d9f8fd/results.md`

## Ce que ca apporte

- `eBuyClub` donne un signal achat / cashback / parcours e-commerce tres qualifie mais faible en volume.
- `Dealabs` donne un signal prix / promo / stock / desirabilite bien plus volumique.
- Les deux sources ne doivent pas etre fusionnees avec `Trustpilot` ou `Google Maps` dans un meme score de satisfaction.

## Recommandations source suivantes

1. `Pages produit Decathlon`
   - forte valeur produit
   - avis natifs et pages d avis publieses par Decathlon
2. `Pages produit Intersport`
   - forte valeur produit
   - Intersport indique que les avis sont collectes via Bazaarvoice depuis juin 2024
3. `PagesJaunes`
   - bon filet de secours local pour completer certains magasins avec peu de signal Google Maps
4. `Support / reparation Decathlon`
   - riche pour les themes SAV, atelier, montage, pieces detachees, retours et maintenance

## Optimisations techniques recommandees

1. `Sitemap-first discovery`
   - crawler les sitemaps / listes categories au lieu de partir de recherches larges
2. `Source partitioning`
   - stocker separement `customer`, `employee`, `store`, `promo`, `product`
3. `Review freshness`
   - pour les runs incrementaux, ne garder que les nouveaux contenus avec hash dedupe + date max par source
4. `Query seeding`
   - pour Google Maps Intersport, lancer des seeds par grandes villes puis merger/deduper
5. `Materialized views`
   - precalculer des vues `top irritants`, `top promos`, `top zones magasin`, `delta Decathlon vs Intersport`
