# Resultats Reddit - Run 20260311T103856Z

## Perimetre

- Selection de marque: `both`
- Max posts par seed: `4`
- Max commentaires par post: `5`
- Mode: `headless=true`
- Sources: `r/Decathlon`, recherche Reddit generique, recherche comparative, recherches `quality`, `return`, `service`

## Metriques clefs

- Posts retenus: `24`
- Commentaires retenus: `97`
- Repartition des posts:
  - `Decathlon`: `16`
  - `Intersport`: `7`
  - `Both`: `1`
- Subreddit le plus present: `r/Decathlon` avec `4` posts retenus

## Signaux principaux

### 1. Decathlon produit aujourd'hui le signal Reddit le plus exploitable

Le pack de requetes actuel remonte nettement plus de contenu utile pour Decathlon que pour Intersport.

Ce qui ressort:
- les discussions autour de la politique de retour sont tres visibles
- les debats sur le rapport qualite / prix reviennent souvent
- Decathlon apparait dans des parcours d'achat tres concrets: chaussures, velos, randonnee, premier equipement

Interpretation:
Decathlon n'est pas seulement une marque citee. C'est une marque que les utilisateurs evaluent activement avant achat. Reddit est donc deja utile pour la veille produit et CX sur Decathlon.

### 2. La politique de retour est a la fois un levier de confiance et un point de friction

Deux threads a fort volume racontent des histoires opposees:
- Positif: [Decathlon Philippines is a top-tier, customer-centric sportswear store](https://www.reddit.com/r/AtinAtinLang/comments/1mrzn6w/) valorise un service tres client et une promesse de retour sur 365 jours.
- Friction: [Decathlon Return Policy changes?](https://www.reddit.com/r/singapore/comments/1pwnq70/) montre qu'une politique percue comme plus restrictive declenche vite un debat public.

Interpretation:
La politique de retour agit comme un amplificateur de reputation. Quand elle est simple et genereuse, elle cree de l'advocacy. Quand elle semble floue ou durcie, elle devient un sujet de mecontentement visible.

Angle COMEX possible:
"La politique de retour Decathlon est un accelerateur de perception. Claire et genereuse, elle nourrit la confiance. Ambigue, elle ouvre immediatement un sujet CX public."

### 3. Le benchmark Decathlon vs Intersport apparait deja de maniere lisible

Le thread comparatif le plus propre de ce run est:
- [Decathlon vs Intersport](https://www.reddit.com/r/skiing/comments/1fxnao0/)

Lecture recurrente des commentaires:
- Decathlon = moins cher, accessible, pertinent pour un acheteur budget
- Intersport = plus de choix, meilleure selection, meilleure qualite percue sur certaines categories

Interpretation:
Sur Reddit, la bataille ne se joue pas seulement sur le prix. Elle se joue surtout sur `value/accessibilite` pour Decathlon versus `choix/qualite` pour Intersport.

Angle COMEX possible:
"Le match Decathlon vs Intersport n'est pas percu comme une guerre de prix. Il est percu comme un arbitrage entre accessibilite et richesse d'offre."

### 4. La qualite Decathlon est jugee par categorie, pas comme un bloc uniforme

Threads utiles:
- [Is Decathlon quality actually good?](https://www.reddit.com/r/pune/comments/1ih9vix/)
- [What are your thoughts sa decathlon shoes?](https://www.reddit.com/r/PHikingAndBackpacking/comments/1qv7jv4/)
- [Decathlon vs bike brands for first road bike?](https://www.reddit.com/r/cycling/comments/1ng268j/)

Pattern observe:
- Decathlon est souvent accepte comme bon point d'entree ou bon achat budget
- la qualite est discutee par produit / categorie, pas comme jugement global de marque
- chaussures et velos sont des portes d'entree fortes pour la comparaison

Interpretation:
La perception Reddit de Decathlon est nuancee: `bon choix rationnel pour le budget`, mais avec un niveau de confiance qui varie selon la categorie produit.

## Threads a reutiliser

| Marque | Subreddit | Thread | Commentaires | Score | Relevance |
| --- | --- | --- | ---: | ---: | ---: |
| Decathlon | r/singapore | [Decathlon Return Policy changes?](https://www.reddit.com/r/singapore/comments/1pwnq70/) | 98 | 252 | 0.6 |
| Decathlon | r/AtinAtinLang | [Decathlon Philippines is a top-tier, customer-centric sportswear store](https://www.reddit.com/r/AtinAtinLang/comments/1mrzn6w/) | 91 | 1113 | 0.9 |
| Decathlon | r/PHikingAndBackpacking | [What are your thoughts sa decathlon shoes?](https://www.reddit.com/r/PHikingAndBackpacking/comments/1qv7jv4/) | 41 | 70 | 0.6 |
| Both | r/skiing | [Decathlon vs Intersport](https://www.reddit.com/r/skiing/comments/1fxnao0/) | 8 | 4 | 0.8 |
| Decathlon | r/cycling | [Decathlon vs bike brands for first road bike?](https://www.reddit.com/r/cycling/comments/1ng268j/) | 15 | 2 | 0.9 |
| Intersport | r/Austria | [Intersport nicht gut](https://www.reddit.com/r/Austria/comments/1jfnze2/) | 24 | 246 | 0.4 |

## Qualite de la data

### Points forts
- le crawl navigateur fonctionne de maniere fiable sur Reddit depuis cette machine
- la decouverte de permaliens marche meme quand les cartes Reddit ont un texte d'ancre vide
- l'extraction `shreddit-post` et `shreddit-comment` est stable

### Limites actuelles
- le signal Intersport reste plus faible et plus bruite que Decathlon
- certains resultats Intersport sont des mentions indirectes ou peu exploitables pour un vrai benchmark
- un seuil de confiance plus strict serait utile avant d'utiliser ce flux comme source finale d'insight concurrentiel

## Recommandations pour l'iteration suivante

1. Durcir les seeds Intersport avec des requetes plus explicites: `"intersport" return`, `"intersport" review`, `"intersport" customer service`, `"intersport" ski`, `"intersport" bike`.
2. Ajouter un seuil de confiance plus strict sur la couche benchmark et exclure les threads en dessous de `0.5`.
3. Classer les posts Reddit retenus dans 3 buckets pour la suite du pipeline hackathon:
   - `reputation`
   - `benchmark`
   - `cx`
4. Envoyer vers l'IA uniquement les posts retenus a forte confiance, pas l'ensemble brut des resultats de recherche.

## Fichiers du run

- Raw posts: `posts.jsonl`
- Raw comments: `comments.jsonl`
- Synthese: `results.md`
