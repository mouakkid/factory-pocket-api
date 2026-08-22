#!/usr/bin/env python3
"""Final ranking on VERIFIED signals -> top 10 per TLD, across 5 extensions."""
import json, math, re
from collections import defaultdict

E = json.load(open('enriched.json')) + json.load(open('enriched_comio.json'))

def brand(name):
    s, L = 0.0, len(name)
    if L <= 5: s += 6
    elif L <= 7: s += 4.5
    elif L <= 9: s += 3
    elif L <= 12: s += 1.5
    v = sum(c in 'aeiouy' for c in name) / max(L, 1)
    if 0.28 <= v <= 0.52: s += 2.5
    if re.search(r'[bcdfghjklmnpqrstvwxz]{5,}', name): s -= 5
    words = ('eco','italy','tour','data','smart','media','green','health','cloud','labs','works',
             'group','soft','tech','web','news','shop','home','life','world','art','music','sport',
             'city','club','book','learn','study','school','fund','care','design','studio','farm',
             'food','water','solar','energy','mind','brain','flow','craft','forge','pixel','morph',
             'novel','read','slide','sun','moon','star','libr','radio','front','scan','house')
    if any(w in name for w in words): s += 2
    return s

scored = defaultdict(list)
for r in E:
    if r.get('available') is not True:
        continue
    if set(r.get('flags', [])) & {'gambling-id', 'gambling-vn', 'casino'}:
        continue
    name = r['domain'].rsplit('.', 1)[0]
    art = r['wiki_article_count']
    s  = 30 * min(art, 5)                       # VERIFIED live Wikipedia article citations
    s += 2.4 * r['tf']
    s += 18 * min(r['trust'], 1.5)
    s += 8 * math.log1p(r['rd'])
    s += 6 * math.log1p(r['rsub'])
    s += 13 * min(r['edu'], 5)
    s += 16 * min(r['gov'], 4)
    s += 14 if r['dmoz'] else 0
    if r['aby']: s += 1.3 * min(2026 - r['aby'], 26)
    s += 4.0 * math.log1p(r['acr'])
    if r['rd']:
        s += 13 * min(r['rdhome'] / r['rd'], 0.5)
        s += 9 * min(r['rdlive'] / r['rd'], 1.0)
    s += 2.2 * min(r['tldreg'], 6)
    s += 2.2 * brand(name)
    if set(r.get('flags', [])) & {'for-sale', 'parked', 'parking-gd', 'parking-sedo', 'parking'}:
        s -= 15
    r['final'] = round(s, 1)
    scored[r['tld']].append(r)

top = {}
for tld, rs in scored.items():
    rs.sort(key=lambda x: -x['final'])
    top[tld] = rs[:10]
json.dump(top, open('top10.json', 'w'), indent=1)

for tld in ('com', 'net', 'org', 'io', 'ai'):
    rs = top.get(tld, [])
    print(f"\n{'='*104}\n.{tld.upper()}  —  top {len(rs)}  (of {len(scored[tld])} passing gates & verified available)\n{'='*104}")
    print(f"{'#':>2} {'DOMAIN':30} {'SC':>6} {'TF':>3} {'T/C':>5} {'RD':>4} {'SUB':>4} {'IP':>4} "
          f"{'EDU':>3} {'GOV':>3} {'WIKI':>4} {'DMOZ':>4} {'ABY':>5} {'CAPT':>5} {'TLD':>3}")
    for i, r in enumerate(rs, 1):
        print(f"{i:>2} {r['domain']:30} {r['final']:>6} {r['tf']:>3} {r['trust']:>5} {r['rd']:>4} "
              f"{r['rsub']:>4} {r['rip']:>4} {r['edu']:>3} {r['gov']:>3} {r['wiki_article_count']:>4} "
              f"{'Y' if r['dmoz'] else '-':>4} {r['aby'] or '-':>5} {r['acr']:>5} {r['tldreg']:>3}")
