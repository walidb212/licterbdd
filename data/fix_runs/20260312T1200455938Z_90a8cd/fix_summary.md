# Fix Summary - Intersport / Indeed / Poulpeo

## Correctifs appliques

- `Indeed` et `Poulpeo` passent maintenant en `crawl4ai` en priorite, plus en `Cloudflare-first`.
- Si une page Cloudflare ne produit aucun avis exploitable, `review_monitor` retente automatiquement en navigateur.
- Les pages de challenge (`Security Check`, `Just a moment`, `DataDome`, `captcha`) sont maintenant detectees explicitement.
- `Poulpeo` ne confond plus le nombre d avis avec une note agregée.
- `Intersport` dispose d un fallback de discovery via Google Maps quand le locator officiel renvoie `403` / `DataDome`.
- Les `run_id` ont ete rendus vraiment uniques avec suffixe aleatoire pour eviter les collisions en execution parallele.

## Runs verifies

### Indeed Decathlon
- Resultats: `20` avis employes
- Note agregée: `4.0 / 5`
- Volume agrégé: `7178`
- Fichier: `data/review_runs/20260312T113952155267Z/results.md`

### Poulpeo Decathlon
- Resultats: `50` avis clients
- Note agregée: `non exposee proprement`, garde a `null`
- Volume agrégé: `97`
- Fichier: `data/review_runs/20260312T113952004265Z/results.md`

### Indeed Intersport
- Resultats: `20` avis employes
- Note agregée: `3.4 / 5`
- Volume agrégé: `1349`
- Fichier: `data/review_runs/20260312T115927369096Z_21d241/results.md`

### Poulpeo Intersport
- Resultats: `50` avis clients
- Note agregée: `non exposee proprement`, garde a `null`
- Volume agrégé: `116`
- Fichier: `data/review_runs/20260312T115927366109Z_89800f/results.md`

### Intersport Discovery
- Locator officiel: bloque en `HTTP 403` + `DataDome`
- Fallback Google Maps: `67` candidats magasin detectes
- Fichier: `data/store_runs/20260312T113951483912Z/results.md`

### Intersport Google Maps Reviews
- Test court valide sur `1` magasin
- Avis recuperes: `5`
- Fichier: `data/store_runs/20260312T115333780610Z/results.md`

## Lecture rapide

- `Indeed` est maintenant stable pour `Decathlon` et `Intersport`.
- `Poulpeo` est maintenant exploitable sans faux score aggregé.
- `Intersport` n est pas reparable proprement via le store locator officiel tant que `DataDome` reste en place; le fallback Google Maps est le bon chemin pour ton hackathon.
- Les avis Google Maps `Intersport` marchent sur la base des magasins decouverts via ce fallback.

## Sites a ajouter en priorite

1. `eBuyClub`
   - fort signal e-commerce, cashback, livraison, SAV, retours
   - symetrique Decathlon / Intersport
2. `Dealabs`
   - tres bon pour la perception prix, promo, stock, frustration communautaire
   - utile pour le pilier benchmark et l angle rapport qualite/prix
3. `PagesJaunes`
   - utile en secours pour completer ou verifier l inventaire magasin local
   - a garder comme source `store` secondaire, pas comme source principale
4. `Pages produit officielles`
   - `Decathlon.fr` et `Intersport.fr`
   - tres utile pour les irritants produit, retours, qualite percue, tailles, montage, durabilite
5. `Google Maps Intersport` a echantillonner plus largement
   - c est deja la meilleure source locale tant que l officiel est bloque

## Recommandation de priorite

- `Must have`: Google Maps, Trustpilot, Custplace, Indeed, Poulpeo, eBuyClub, Reddit, Google News
- `Should have`: Dealabs, pages produit officielles
- `Fallback`: PagesJaunes

## Point de vigilance

- Ne melange pas dans un meme score les avis `employee`, `customer`, `store`, `promo` et `product`.
- Garde `Poulpeo` et `eBuyClub` comme signal e-commerce / parcours d achat.
- Garde `Google Maps` comme signal magasin local.
