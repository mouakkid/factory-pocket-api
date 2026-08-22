# Expired .com domain research

Pipeline de sélection de domaines .com expirés pour investissement, basé sur un compte
membre ExpiredDomains.net. Résultats du 22/08/2026 dans [RAPPORT.md](RAPPORT.md).

## Contenu

- `scripts/fetch_listings.sh` — requêtes filtrées vers l'espace membre (nécessite un
  cookie jar authentifié via `ED_JAR` ; la connexion demande un code 2FA envoyé par email,
  aucun identifiant n'est stocké ici).
- `scripts/parse_listing.py` — parse les pages HTML de listing en JSONL
  (`python3 parse_listing.py L1.html:tag1 L2.html:tag2 > rows.jsonl`).
- `scripts/score.py` — dédoublonnage, liste noire spam (pharma/casino/contrefaçon),
  détection de réseaux de domaines (motifs répétés + Domain Pop clonés), scoring.
  Produit `scored.json` + tableau des tops.
- `data/candidates_scored.csv` — les 860 candidats uniques scorés.
- `data/verdicts/*.txt` — verdict d'enquête par finaliste (disponibilité RDAP,
  chronologie Archive.org, qualité des backlinks, risque de marque, signaux de spam).

## Critères de filtre (phase serveur)

.com disponible (whois=22) · 0 tiret · 0 chiffre · ≤13 caractères · pas d'adulte ·
première capture Archive.org ≤2015/2016 · ≥30 captures · Domain Pop ≥10 ·
axes bonus : liens Wikipédia, TrustFlow ≥10, ≥2 autres TLDs enregistrés, noms ≤8 lettres.

## Reproduire

1. Se connecter sur expireddomains.net (login + code email), sauver les cookies dans un jar curl.
2. `ED_JAR=jar.txt ./scripts/fetch_listings.sh out/`
3. `python3 scripts/parse_listing.py out/L1.html:core1 ... > rows.jsonl`
4. `python3 scripts/score.py` puis enquête manuelle/agents sur le top.
