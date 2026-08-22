#!/usr/bin/env python3
"""Render the final French markdown report from merged data."""
import json

TLD_NOTE = {
 'com': "Inventaire le plus riche : 309 candidats franchissaient le seuil standard, j'ai donc relevé la barre à TrustFlow ≥ 28 et 25 domaines référents.",
 'net': "Seuil TrustFlow ≥ 22, 18 domaines référents.",
 'org': "Seuil TrustFlow ≥ 25, 20 domaines référents. Extension dominée par des associations encore vivantes.",
 'io':  "Inventaire rare (46 candidats au seuil), seuil abaissé à TrustFlow ≥ 15. Coût de portage ~35-70 $/an.",
 'ai':  "Inventaire rare (120 candidats), seuil TrustFlow ≥ 15. Coût de portage ~70-200 $ par période de 2 ans obligatoire.",
}
SYM = {'PERLE':'🏆 PERLE','BON':'✅ BON','MOYEN':'🟡 MOYEN','REJET':'❌ REJET','':'⏳ en cours'}

f = json.load(open('final_report.json'))
L = []
L.append("# Domaines expirés — top 10 par extension\n")
L.append("**22 août 2026** · Source : compte membre ExpiredDomains.net · "
         "Vérifications indépendantes : RDAP (disponibilité en direct), API MediaWiki "
         "(citations Wikipédia par espace de noms), archive.org, sondage HTTP, "
         "puis une enquête par agent dédié sur chaque finaliste.\n")

tot = {}
for tld in ('com','net','org','io','ai'):
    for r in f[tld]:
        v = r.get('verdict','')
        tot[v] = tot.get(v,0)+1
keep = tot.get('PERLE',0)+tot.get('BON',0)+tot.get('MOYEN',0)
L.append(f"## Verdict d'ensemble\n")
L.append(f"Sur les **50 finalistes** (10 par extension) issus de 4 790 lignes collectées : "
         f"**{tot.get('REJET',0)} à rejeter**, **{tot.get('MOYEN',0)} moyens**, "
         f"**{tot.get('BON',0)} bons**, **{tot.get('PERLE',0)} perle**. "
         f"Soit {keep} domaines sur 50 méritant considération.\n")
L.append("Presque tous paraissaient excellents sur les métriques. C'est le résultat "
         "central de l'étude : **les métriques de liens ne survivent pas à la vérification**.\n")

for tld in ('com','net','org','io','ai'):
    L.append(f"\n---\n\n## .{tld.upper()}\n")
    L.append(f"*{TLD_NOTE[tld]}*\n")
    for r in f[tld]:
        v = r.get('verdict','')
        L.append(f"\n### {r['rank']}. `{r['domain']}` — {SYM[v]}\n")
        m = (f"TrustFlow {r['tf']}/CitationFlow {r['cf']} (ratio {r['trust']}) · "
             f"{r['rd']} domaines référents sur {r['rsub']} subnets · ")
        if r['wiki_article_count']: m += f"**{r['wiki_article_count']} citations Wikipédia vivantes** · "
        if r['edu']: m += f"{r['edu']} liens .edu · "
        if r['gov']: m += f"{r['gov']} liens .gov · "
        if r['dmoz']: m += "référencé DMOZ · "
        if r['aby']: m += f"1ʳᵉ archive {r['aby']} · "
        m += f"{r['acr']} captures"
        if r.get('link_shape') == 'deep-link-spam':
            m += f" · ⚠️ **profil de liens profonds suspect** ({r['rdhome']}/{r['rd']} vers l'accueil)"
        L.append(m + "\n")
        if r.get('ident'): L.append(f"\n**Identité** — {r['ident'][:600]}\n")
        if r.get('status'): L.append(f"\n**Statut du propriétaire** — {r['status'][:300]}\n")
        if r.get('spam') and r['spam'].lower() not in ('none','none found','aucun'):
            L.append(f"\n**Historique de spam** — {r['spam'][:500]}\n")
        if r.get('just'): L.append(f"\n**Justification** — {r['just'][:800]}\n")
        if r.get('angle'): L.append(f"\n**Angle** — {r['angle'][:400]}\n")
        if r.get('tm'): L.append(f"\n**Risque de marque** — {r['tm'][:300]}\n")

open('/home/user/factory-pocket-api/expired-domains-research/RAPPORT_TOP10.md','w').write('\n'.join(L))
print("written:", len('\n'.join(L)), "chars")
print("tally:", tot)
