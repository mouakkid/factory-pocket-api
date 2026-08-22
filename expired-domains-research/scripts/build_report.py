#!/usr/bin/env python3
"""Merge verified metrics + agent verdicts into the final deliverable."""
import re, glob, json

def parse_verdicts():
    recs = {}
    for p in glob.glob('verdicts2/*.txt'):
        txt = open(p, encoding='utf-8', errors='replace').read()
        for b in re.split(r'(?=^DOMAIN:\s)', txt, flags=re.M):
            m = re.match(r'^DOMAIN:\s*(\S+)', b)
            if not m:
                continue
            d = m.group(1).strip().lower().strip('`*')
            def f(k):
                mm = re.search(rf'^{k}:\s*(.+?)(?=\n[A-Z_]+:|\Z)', b, re.M | re.S)
                return re.sub(r'\s+', ' ', mm.group(1)).strip() if mm else ''
            v = f('VERDICT').split()[0] if f('VERDICT') else ''
            if not v:
                continue
            recs[d] = {'verdict': v, 'just': f('JUSTIFICATION'), 'angle': f('ANGLE'),
                       'tm': f('TRADEMARK_RISK'), 'ident': f('IDENTITY') or f('PRODUCT'),
                       'spam': f('SPAM_HISTORY'), 'links': f('LINK_SOURCES') or f('LINK_QUALITY'),
                       'status': f('ORG_STATUS') or f('BUSINESS_STATUS') or f('OWNER_STATUS')}
    return recs

RANK = {'PERLE': 0, 'BON': 1, 'MOYEN': 2, 'REJET': 3, '': 4}

if __name__ == '__main__':
    recs = parse_verdicts()
    top = json.load(open('top10.json'))
    json.dump(recs, open('verdict_map.json', 'w'), indent=1)
    out = {}
    for tld in ('com', 'net', 'org', 'io', 'ai'):
        rows = []
        for i, r in enumerate(top[tld], 1):
            v = recs.get(r['domain'], {})
            rows.append({**r, 'rank': i, **v})
        out[tld] = rows
    json.dump(out, open('final_report.json', 'w'), indent=1)
    tot = {}
    for tld, rows in out.items():
        for r in rows:
            tot[r.get('verdict', 'pending')] = tot.get(r.get('verdict', 'pending'), 0) + 1
    print('verdicts parsed:', len(recs))
    print('top-50 coverage:', tot)
    for tld in ('com', 'net', 'org', 'io', 'ai'):
        keep = [r for r in out[tld] if r.get('verdict') in ('PERLE', 'BON', 'MOYEN')]
        print(f"  .{tld}: {len(keep)} worth considering / 10")
