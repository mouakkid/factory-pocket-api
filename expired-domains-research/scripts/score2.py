#!/usr/bin/env python3
"""Quality gates + scoring for round-2 .net/.org/.ai candidates."""
import json, math, re, sys
INPUT = sys.argv[1] if len(sys.argv)>1 else 'rows2.jsonl'
OUT = sys.argv[2] if len(sys.argv)>2 else 'shortlist.json'
from collections import Counter, defaultdict

SPAM = re.compile(r'(v[i1]a[a-z]{0,3}gra|c[i1]a+l[i1]s|sildenafil|tadalafil|prednis|amoxicillin|'
    r'ampicillin|lasix|atarax|strattera|diflucan|tramadol|xanax|valium|levitra|clomid|zithromax|'
    r'propecia|accutane|nolvadex|lipitor|celebrex|neurontin|paxil|zoloft|prozac|kamagra|valtrex|'
    r'bactrim|vermox|cymbalta|motilium|zovirax|doxycycl|augmentin|priligy|proscar|avodart|flagyl|'
    r'keflex|arimidex|antabuse|dapoxetine|fluoxetine|lexapro|abilify|seroquel|lisinopril|metformin|'
    r'prednisone|ventolin|albuterol|synthroid|phentermine|adderall|oxycodone|'
    r'pills?|rxonline|onlinerx|pharmac|drugstore|'
    r'casino|poker|slots?|betting|bet88|gacor|togel|judi|bingo|jackpot|roulette|baccarat|sportsbook|'
    r'porn|sexcam|xxx|escort|milf|hentai|camgirl|'
    r'payday|quickloan|fastloan|loansonline|creditrepair|'
    r'essaywrit|homeworkhelp|coursework|paperwrit|'
    r'replica|oakley|louboutin|rayban|jerseys|uggboots|moncler|abercrombie|jordans|airmax|'
    r'vuitton|handbags|'
    r'freerobux|keygen|crackdll|torrent|warez|'
    r'weightloss|garcinia|ketodiet|cbdoil|vapeshop)', re.I)

GATES = {  # tld: (tf_min, rd_min) — bar set by how rich that TLD's inventory is
    'com': (28, 25),   # very rich pool -> highest bar
    'org': (25, 20),
    'net': (22, 18),
    'ai':  (15, 10),   # scarce
    'io':  (15, 10),   # scarce
}


def n(v):
    v = (v or '').replace(',', '').strip()
    return int(v) if v.lstrip('-').isdigit() and v != '-' else 0


def load():
    rows = {}
    for line in open(INPUT):
        r = json.loads(line)
        d = r['domain']
        if d in rows:
            rows[d]['src'] += ',' + r['src']
        else:
            rows[d] = r
    return rows


def name_quality(name):
    """Heuristic brandability / meaningfulness score."""
    s = 0.0
    if len(name) <= 6: s += 4
    elif len(name) <= 9: s += 2.5
    elif len(name) <= 12: s += 1
    v = sum(c in 'aeiouy' for c in name) / max(len(name), 1)
    if 0.25 <= v <= 0.55: s += 2                  # pronounceable
    if re.search(r'[bcdfghjklmnpqrstvwxz]{5,}', name): s -= 4   # consonant soup
    if re.fullmatch(r'[a-z]+', name): s += 1
    return s


def evaluate(r):
    """Return (passed, reasons_failed, metrics)."""
    d, tld = r['domain'], r['tld']
    name = d.rsplit('.', 1)[0]
    tf, cf, rd = n(r['tf']), n(r['cf']), n(r['rd'])
    rip, rsub, bl = n(r['rip']), n(r['rsub']), n(r['bl'])
    rdlive, rdhome = n(r['rdlive']), n(r['rdhome'])
    edu, gov, wiki = n(r['edu']), n(r['gov']), n(r['wiki'])
    aby, acr = n(r['aby']), n(r['acr'])
    dmoz = r['dmoz'] not in ('-', '')
    tldreg = n(r['tldreg'])
    tf_min, rd_min = GATES[tld]

    fails = []
    if SPAM.search(name):                      fails.append('spam-name')
    if tf < tf_min:                            fails.append(f'TF<{tf_min}')
    if rd < rd_min:                            fails.append(f'RD<{rd_min}')
    trust = tf / cf if cf else 0
    if trust < 0.35:                           fails.append('trust-ratio')      # spam signature
    if rd and rsub < 0.40 * rd:                fails.append('subnet-farm')      # links concentrated
    if rd and rip < 0.45 * rd:                 fails.append('ip-farm')
    if rd and bl / rd > 600:                   fails.append('sitewide-inflation')
    if rd and rdlive < 0.30 * rd:              fails.append('dead-links')
    if name_quality(name) < 0:                 fails.append('unpronounceable')

    score = 0.0
    score += 2.6 * tf                       # trust is king
    score += 22 * min(trust, 1.2)           # healthy trust/citation ratio
    score += 9 * math.log1p(rd)
    score += 7 * math.log1p(rsub)           # network diversity
    score += 12 * min(edu, 5)               # .edu referrers = strong
    score += 14 * min(gov, 4)               # .gov even stronger
    score += 9 * min(wiki, 4)
    score += 12 if dmoz else 0              # curated directory era
    if aby and aby < 2026:
        score += 1.6 * min(2026 - aby, 25)  # age
    score += 3 * math.log1p(acr)            # crawl depth = real site
    if rd:
        score += 14 * min(rdhome / rd, 0.5) # homepage links are editorial
        score += 10 * min(rdlive / rd, 1.0) # links still alive
    score += 2.5 * min(tldreg, 6)           # name defended in other TLDs
    score += 1.8 * name_quality(name)

    m = dict(tf=tf, cf=cf, trust=round(trust, 2), rd=rd, rip=rip, rsub=rsub,
             bl=bl, rdlive=rdlive, rdhome=rdhome, edu=edu, gov=gov, wiki=wiki,
             aby=aby, acr=acr, dmoz=dmoz, tldreg=tldreg,
             topics=r.get('ttf_topics', ''), score=round(score, 1))
    return (not fails), fails, m


if __name__ == "__main__":
    rows = load()
    kept, rejected = defaultdict(list), Counter()
    for d, r in rows.items():
        ok, fails, m = evaluate(r)
        r.update(m)
        if ok:
            kept[r['tld']].append(r)
        else:
            for f in fails:
                rejected[f] += 1
    print("gate failures:", dict(rejected.most_common()), file=sys.stderr)
    out = {}
    for tld, rs in kept.items():
        rs.sort(key=lambda x: -x['score'])
        out[tld] = rs[:40]           # keep 60, trim to 50 after live checks
        print(f"{tld}: {len(rs)} passed gates -> keeping {len(out[tld])}", file=sys.stderr)
    json.dump(out, open(OUT, 'w'), indent=1)
    for tld in sorted(out):
        print(f"\n===== .{tld} top 20 =====")
        print(f"{'DOMAIN':30} {'SC':>6} {'TF':>3} {'CF':>3} {'T/C':>4} {'RD':>4} {'SUB':>4} "
              f"{'EDU':>3} {'GOV':>3} {'WK':>3} {'ABY':>5} {'DMOZ':>4}")
        for r in out.get(tld, [])[:20]:
            print(f"{r['domain']:30} {r['score']:>6} {r['tf']:>3} {r['cf']:>3} {r['trust']:>4} "
                  f"{r['rd']:>4} {r['rsub']:>4} {r['edu']:>3} {r['gov']:>3} {r['wiki']:>3} "
                  f"{r['aby'] or '-':>5} {'yes' if r['dmoz'] else '-':>4}")
