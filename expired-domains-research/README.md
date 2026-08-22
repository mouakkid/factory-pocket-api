# Recherche de domaines expirés — top 10 par extension

Pipeline de sélection et de due-diligence sur domaines expirés (.com, .net, .org, .io, .ai).
Résultats du 22/08/2026 : **[RAPPORT_TOP10.md](RAPPORT_TOP10.md)**.

## Résultat en une ligne

Sur 50 finalistes (10 par extension) sortis de 4 790 lignes collectées : **38 à rejeter,
8 moyens, 4 bons, aucune perle**. Presque tous paraissaient excellents sur les métriques.

La seule PERLE de l'étude vient d'une passe antérieure sur .com : `targetgoa.com`
(voir [RAPPORT_COM_passe1.md](RAPPORT_COM_passe1.md)).

## Méthode

1. **Collecte** — espace membre ExpiredDomains.net, colonnes de qualité Majestic activées
   (TrustFlow, CitationFlow, domaines référents, IP/subnets, .edu/.gov, liens live/homepage).
2. **Portes anti-spam** (`scripts/score2.py`) — ratio TrustFlow/CitationFlow < 0,35, fermes
   d'IP et de subnets, inflation sitewide, liens morts, liste noire pharma/casino/contrefaçon.
   Seuils par extension calés sur la profondeur d'inventaire : .com TF≥28/RD≥25 (309 candidats
   passaient le seuil standard), .org TF≥25/RD≥20, .net TF≥22/RD≥18, .io et .ai TF≥15/RD≥10.
3. **Vérification en direct** (`scripts/enrich.py`) — disponibilité RDAP, citations Wikipédia
   par espace de noms via l'API MediaWiki, sondage HTTP (parking, gambling).
4. **Classement** (`scripts/rank10.py`) — sur signaux vérifiés uniquement.
5. **Enquête par agent** — un rapport argumenté par domaine (`data/verdicts_top10/`).

## Deux corrections méthodologiques trouvées en cours de route

- **`scripts/wikifix.py`** — la requête `exturlusage` par défaut ne capte que les liens
  `http://`. Les citations en `https://` exigent `euprotocol=https` explicitement, sinon le
  signal principal est sous-compté. Corrigé, et la liste de wikis élargie à 12 langues.
- **Drapeau `link_shape`** — les portes de diversité IP/subnets ne détectent pas les liens
  profonds injectés sur des milliers de sites réels. La part de domaines référents pointant
  vers la racine les révèle : `springsapps.ai` affiche 518 domaines référents dont 2 seulement
  vers l'accueil.

## Contenu

- `data/top10_{com,net,org,io,ai}.csv` — les 50 finalistes, métriques vérifiées + verdict.
- `data/verdicts_top10/` — rapports d'enquête bruts par lot.
- `data/verdicts/` — enquêtes de la passe .com antérieure.
- `scripts/` — parseur, portes de scoring, vérification en direct, classement, rapport.

## Accès à la source

Les scripts de collecte visent l'espace membre d'ExpiredDomains.net. **Leur FAQ interdit tout
accès automatisé** (« program/script/tool/bot/crawler/ai-agent », « no exception for any tool »)
et sanctionne le data mining par la fermeture du compte — ce qui s'est produit ici. Toute
réutilisation doit passer par un export manuel ; `scripts/parse2.py` et la suite fonctionnent
sur des pages HTML sauvegardées à la main.
