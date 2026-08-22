#!/usr/bin/env python3
"""Dedupe, blacklist-filter, network-detect and score ExpiredDomains candidates."""
import json, math, re, sys
from collections import Counter

SPAM = re.compile(r'(v[i1]a[a-z]{0,3}gra|c[i1]a+l[i1]s|sildenafil|tadalafil|prednis|amoxicillin|'
    r'ampicillin|lasix|atarax|strattera|diflucan|tramadol|xanax|valium|levitra|clomid|'
    r'zithromax|propecia|accutane|nolvadex|lipitor|celebrex|neurontin|paxil|zoloft|prozac|'
    r'kamagra|valtrex|bactrim|vermox|cymbalta|motilium|zovirax|doxycycl|augmentin|prilig|'
    r'proscar|avodart|flagyl|cipro\b|keflex|arimidex|antabuse|dapoxetine|fluoxetine|lexapro|'
    r'abilify|seroquel|zestril|lisinopril|metformin|prednisone|ventolin|albuterol|synthroid|'
    r'pills?|rxonline|onlinerx|pharm|meds$|'
    r'casino|poker|slots?|betting|gacor|togel|judi|bingo|jackpot|roulette|'
    r'porn|sexy?|xxx|escort|milf|'
    r'payday|quickloan|fastloan|loansonline|'
    r'essay|homework|coursework|'
    r'replica|oakley|louboutin|raybans?|jerseys|uggs?|moncler|abercrombie|'
    r'jordans|airmax|nikeair|gucci|vuitton|'
    r'gcash|hoki|maxwin|bet(?:88|365|way)|'
    r'cbdoil|freerobux|keygen)', re.I)

def num(s):
    s = (s or '').replace(',', '').strip()
    return int(s) if s.isdigit() else 0

rows = {}
for line in open('rows.jsonl'):
    r = json.loads(line)
    d = r['domain']
    if d in rows:
        rows[d]['src'] += ',' + r['src']
    else:
        rows[d] = r

# network detection: token shared by many candidates
def tokens(name):
    toks = set()
    for t in ('rent', 'sale', 'homes', 'house', 'city', 'apartments', 'flats', 'jobs',
              'hotels', 'cars', 'shop', 'store', 'online', 'cheap', 'buy', 'best'):
        if t in name:
            toks.add(t)
    return toks

names = [d.replace('.com', '') for d in rows]
tokcount = Counter(t for n in names for t in tokens(n))
dpcount = Counter(num(r['domainpop']) for r in rows.values())

out, dropped = [], Counter()
for d, r in rows.items():
    name = d.replace('.com', '')
    bl = num(r['bl']); dp = num(r['domainpop']); wiki = num(r['wikipedia_links'])
    acr = num(r['aentries']); tldreg = num(r['statustld_registered'])
    aby = num(r['abirth']) or 2026
    mgr = num(r['majestic_globalrank'])
    age = 2026 - aby
    if SPAM.search(name):
        dropped['spam'] += 1; continue
    if not re.search(r'[aeiouy]', name):
        dropped['unpronounceable'] += 1; continue
    # network fingerprint: common commercial token shared by >=6 candidates AND cloned DP value
    net = any(tokcount[t] >= 6 for t in tokens(name))
    cloned_dp = dpcount[dp] >= 4 and dp > 50
    if net and cloned_dp:
        dropped['network'] += 1; continue
    if dp >= 250 and aby >= 2019 and wiki == 0:
        dropped['young_bigdp'] += 1; continue
    score = (2.2 * math.log1p(dp) + 1.6 * math.log1p(bl) + 1.1 * age
             + 7.0 * min(wiki, 3) + 1.0 * math.log1p(acr) + 1.8 * min(tldreg, 5))
    if mgr:
        score += 4
    if net or cloned_dp:
        score -= 8
    if len(name) <= 8:
        score += 3
    if re.fullmatch(r'[a-z]+', name) and len(name) <= 10:
        score += 2
    if aby <= 2008:
        score += 4
    r.update(dict(name=name, blv=bl, dpv=dp, wikiv=wiki, acrv=acr, tldregv=tldreg,
                  abyv=aby, age=age, mgrv=mgr, score=round(score, 1),
                  cre=r['creationdate'].strip()))
    out.append(r)

out.sort(key=lambda r: -r['score'])
json.dump(out, open('scored.json', 'w'), indent=1)
print(f"unique: {len(rows)}, dropped: {dict(dropped)}, kept: {len(out)}", file=sys.stderr)
print(f"{'DOMAIN':26} {'SCORE':>6} {'DP':>5} {'BL':>7} {'WIKI':>4} {'ABY':>5} {'ACR':>5} {'TLDr':>4} {'MGR':>9} {'CREATED':>10}  SRC")
for r in out[:85]:
    print(f"{r['domain']:26} {r['score']:>6} {r['dpv']:>5} {r['blv']:>7} {r['wikiv']:>4} {r['abyv']:>5} {r['acrv']:>5} {r['tldregv']:>4} {r['mgrv']:>9} {r['cre']:>10}  {r['src'][:24]}")
