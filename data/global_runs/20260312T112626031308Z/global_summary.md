# Synthese globale Decathlon / Intersport - 20260312T112626031308Z

## Perimetre execute

- Reddit: `c:\Users\walid\Cursor - Projects\EugeniaSchool\LICTER\data\reddit_runs\20260312T111945018828Z`
- Google News: `c:\Users\walid\Cursor - Projects\EugeniaSchool\LICTER\data\news_runs\20260312T112238682538Z`
- Review sites: `c:\Users\walid\Cursor - Projects\EugeniaSchool\LICTER\data\review_runs\20260312T112256626986Z`
- Google Maps / stores Decathlon: `c:\Users\walid\Cursor - Projects\EugeniaSchool\LICTER\data\store_runs\20260312T110837370718Z`
- Diagnostic stores Intersport: `c:\Users\walid\Cursor - Projects\EugeniaSchool\LICTER\data\store_runs\20260312T111316635388Z`
- X non lance: credentials `X_AUTH_TOKEN` / `X_CT0` absents

## Inventaire existant

- Inventaire Decathlon France disponible: `335` magasins
- Base Google Maps legacy disponible: `39` magasins Decathlon avec avis deja scrap?s
- Dernier run Google Maps consolide: `40` magasins charges, `1475` avis totalises

## Volumes par source

- Reddit: `30` posts, `168` commentaires
- News: `43` articles retenus sur `5` requetes
- Review sites: `213` lignes d'avis exploitees
- Google Maps Decathlon: `1475` avis magasins

## Lecture executive

- Trustpilot: Decathlon est a `1.7` / 5 sur `2913` avis, Intersport a `4.2` / 5 sur `7358` avis.
- Custplace: les deux marques sont faibles, avec Decathlon a `1.6` et Intersport a `1.3`.
- Glassdoor: Decathlon est mieux percu cote employe (`4.0` / 5) qu'Intersport (`3.3` / 5).
- Google Maps Decathlon est deja la base la plus dense du projet: `1475` avis magasins sur `40` magasins couverts.
- Reddit remonte surtout un signal Decathlon (`19` posts) plus riche que le signal Intersport (`10` posts).
- News: repartition `both=4, decathlon=20, intersport=19` avec un mix surtout `general`, `product` et `cx`.

## Detail par bloc

### Review sites

| Site | Brand | Scope | Note agg. | Volume agg. | Lignes extraites |
| --- | --- | --- | ---: | ---: | ---: |
| custplace | decathlon | customer | 1.60 | 117 | 20 |
| custplace | intersport | customer | 1.30 | 135 | 20 |
| dealabs | decathlon | promo | - | - | 30 |
| dealabs | intersport | promo | - | - | 30 |
| ebuyclub | decathlon | customer | 5.00 | 5184 | 1 |
| ebuyclub | intersport | customer | 5.00 | 44 | 3 |
| glassdoor | decathlon | employee | 4.00 | 10919 | 5 |
| glassdoor | intersport | employee | 3.30 | 107 | 5 |
| trustpilot | decathlon | customer | 1.70 | 2913 | 49 |
| trustpilot | intersport | customer | 4.20 | 7358 | 50 |

- Repartition review sites: `custplace`=40, `dealabs`=60, `ebuyclub`=4, `glassdoor`=10, `trustpilot`=99
- Repartition review brands: `decathlon`=105, `intersport`=108
- Repartition review scopes: `customer`=143, `employee`=10, `promo`=60
- Indeed n'a pas fourni de verbatims exploitables dans le run global final; les pages sont instables selon le mode de rendu.
- Poulpeo n'a pas encore fourni de lignes utiles dans ce run global.

### Google Maps / stores

- Stores charges: `40`
- Status stores: `legacy_review_loaded`=39, `review_scraped`=1

| Stores Decathlon les plus fragiles | Note agg. | Volume agg. | Localisation |
| --- | ---: | ---: | --- |
| Decathlon Saint André de Cubzac | 3.6 | - | 240 avenue Boucicaut, 33240, Saint-André de Cubzac |
| Decathlon Essentiel Givet | 3.7 | - | Route de Beauraing, 08600, GIVET |
| Decathlon Arles | 3.8 | - | Zone Commerciale Fourchon, 13200, Arles |
| Decathlon Saint Gaudens | 3.8 | - | ZAC des Landes, 10AvenueduCagire, 31800 |
| Decathlon Soissons | 3.8 | - | PARC DES MOULINS - 79 route de Chevreux, 02200, SOISSONS |

- Irritants frequents dans les avis <=2 etoiles: `attente_caisse`=73, `livraison_commande`=48, `retour_remboursement`=35, `sav`=34, `atelier_velo`=31, `stock_disponibilite`=29
- Motifs positifs dans les avis 5 etoiles: `accueil_conseil`=590, `choix_variete`=102, `prix`=80, `atelier`=78
- Intersport magasins: aucun inventaire officiel extrait dans ce run, store locator bloque par DataDome/HTTP 403.

### Google News

- Repartition brands: `both`=4, `decathlon`=20, `intersport`=19
- Repartition signaux: `cx`=1, `general`=21, `product`=12, `sports_team`=3, `store_network`=6
- Top sources presse: `Frandroid`=4, `Cleanrider`=3, `Marie France, magazine féminin`=3, `La Gazette France`=2, `L'Est Républicain`=2, `Transition Vélo`=2, `letribunaldunet`=2, `Tribuna.com`=2
- Les signaux qui remontent le plus sont la transformation omnicanale, les lancements produit, les activations magasin et les collaborations retail.

### Reddit

- Repartition brands: `both`=1, `decathlon`=19, `intersport`=10
- Top subreddits: `Decathlon`=3, `india_cycling`=2, `PHikingAndBackpacking`=1, `deinfluencingPH`=1, `indianrunners`=1, `outdoorgear`=1, `laufen`=1, `greece`=1
- Signal observe: Decathlon ressort surtout sur la qualite produit, les retours, le service atelier velo et la comparaison rapport qualite/prix; Intersport ressort plus faiblement et davantage sur l'experience magasin ou le pricing.

## Ce que tu as vraiment aujourd'hui

1. Une base locale dense et deja exploitable sur Decathlon magasins via Google Maps.
2. Un bloc review sites bilateral solide pour la perception client publique avec Trustpilot, Custplace et eBuyClub, plus Glassdoor cote employe.
3. Un bloc media/news pour le contexte marche et les signaux externes recents.
4. Un bloc Reddit pour enrichir les comparatifs et les irritants CX moins visibles sur les plateformes d'avis classiques.
5. Deux angles encore incomplets: X non authentifie et Intersport magasins bloque par DataDome.

## Priorites recommandees

1. Normaliser tout ca vers un schema unique dans Sheets/Supabase avec un champ `source_family` (`store`, `review_site`, `news`, `community`).
2. Lancer l'IA d'abord sur les avis Google Maps Decathlon et les avis Trustpilot/Custplace, car c'est la masse de signal la plus exploitable pour le COMEX.
3. Traiter Intersport magasins comme un chantier de sourcing distinct tant qu'un inventaire n'est pas obtenu.
4. Ne pas melanger les notes d'agregat entre plateformes: Trustpilot, Custplace, Glassdoor, Google Maps et Dealabs n'ont pas la meme semantique.

