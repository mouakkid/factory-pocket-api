#!/usr/bin/env python3
"""Live verification of shortlisted domains.

For every candidate:
  * RDAP  -> is it REALLY still unregistered (listings go stale fast)
  * Wikipedia exturlusage across 8 wikis -> live citations, split by namespace
    (ns0 = real article = valuable; Talk/User = worthless noise)
  * Archive.org -> first capture, recent capture, continuity probes
  * Live HTTP -> is something already parked / rebuilt on it
"""
import json, re, sys, time
IN  = sys.argv[1] if len(sys.argv)>1 else 'shortlist.json'
OUT = sys.argv[2] if len(sys.argv)>2 else 'enriched.json'
TLDS= (sys.argv[3].split(',') if len(sys.argv)>3 else ['net','org','ai'])
import requests
from concurrent.futures import ThreadPoolExecutor

S = requests.Session()
S.headers['User-Agent'] = 'domain-research/1.0'
TIMEOUT = 25

RDAP = {
    'net': 'https://rdap.verisign.com/net/v1/domain/{}',
    'org': 'https://rdap.publicinterestregistry.org/rdap/domain/{}',
    'ai':  'https://rdap.identitydigital.services/rdap/domain/{}',
    'com': 'https://rdap.verisign.com/com/v1/domain/{}',
    'io':  'https://rdap.identitydigital.services/rdap/domain/{}',
}
WIKIS = ['en', 'fr', 'de', 'es', 'it', 'nl', 'pt', 'ru']
PROBE_YEARS = ['20050601', '20100601', '20150601', '20200601', '20240601', '20260101']


def rdap(domain, tld):
    try:
        r = S.get(RDAP[tld].format(domain), timeout=TIMEOUT)
        if r.status_code == 404:
            return {'available': True, 'rdap': 404}
        if r.status_code == 200:
            j = r.json()
            st = j.get('status', [])
            reg = ''
            for e in j.get('entities', []):
                if 'registrar' in e.get('roles', []):
                    for v in e.get('vcardArray', [[], []])[1]:
                        if v[0] == 'fn':
                            reg = v[3]
            ev = {e.get('eventAction'): e.get('eventDate', '')[:10]
                  for e in j.get('events', [])}
            return {'available': False, 'rdap': 200, 'status': st,
                    'registrar': reg, 'registered': ev.get('registration', ''),
                    'expires': ev.get('expiration', '')}
        return {'available': None, 'rdap': r.status_code}
    except Exception as e:
        return {'available': None, 'rdap': f'err:{type(e).__name__}'}


def wiki_links(domain):
    """Live Wikipedia citations, separated by namespace."""
    arts, talk, wikis_hit = [], 0, []
    for lang in WIKIS:
        try:
            r = S.get(f'https://{lang}.wikipedia.org/w/api.php',
                      params={'action': 'query', 'list': 'exturlusage',
                              'euquery': domain, 'eulimit': 100,
                              'euprop': 'title|url', 'format': 'json'},
                      timeout=TIMEOUT)
            items = r.json().get('query', {}).get('exturlusage', [])
        except Exception:
            continue
        got = False
        for it in items:
            if it.get('ns') == 0:
                arts.append(f"{lang}:{it['title']}")
                got = True
            else:
                talk += 1
        if got:
            wikis_hit.append(lang)
        time.sleep(0.05)
    uniq = sorted(set(arts))
    return {'wiki_articles': uniq[:12], 'wiki_article_count': len(uniq),
            'wiki_nonarticle': talk, 'wiki_langs': wikis_hit}


def wayback(domain):
    out = {}
    hits = []
    for ts in PROBE_YEARS:
        try:
            r = S.get('https://archive.org/wayback/available',
                      params={'url': domain, 'timestamp': ts}, timeout=TIMEOUT)
            snap = r.json().get('archived_snapshots', {}).get('closest', {})
            if snap.get('available'):
                hits.append((ts[:4], snap.get('timestamp', '')[:6],
                             snap.get('status', '')))
        except Exception:
            pass
        time.sleep(0.05)
    out['wayback_probes'] = [f"{a}->{b}({c})" for a, b, c in hits]
    if hits:
        stamps = sorted(b for _, b, _ in hits if b)
        out['wb_first'] = stamps[0] if stamps else ''
        out['wb_last'] = stamps[-1] if stamps else ''
    return out


def live(domain):
    for scheme in ('https://', 'http://'):
        try:
            r = S.get(scheme + domain, timeout=12, allow_redirects=True)
            body = r.text[:6000].lower()
            flags = []
            for kw, lab in [('togel', 'gambling-id'), ('slot gacor', 'gambling-id'),
                            ('casino', 'casino'), ('bandar', 'gambling-id'),
                            ('taruhan', 'gambling-id'), ('đá gà', 'gambling-vn'),
                            ('domain is for sale', 'for-sale'),
                            ('buy this domain', 'for-sale'),
                            ('parked', 'parked'), ('godaddy', 'parking-gd'),
                            ('sedo', 'parking-sedo'), ('afternic', 'parking')]:
                if kw in body:
                    flags.append(lab)
            title = re.search(r'<title[^>]*>(.*?)</title>', body, re.S)
            return {'http': r.status_code, 'final_url': r.url[:120],
                    'title': (title.group(1).strip()[:90] if title else ''),
                    'flags': sorted(set(flags))}
        except Exception:
            continue
    return {'http': 0, 'flags': []}


def enrich(r):
    d = r['domain']
    out = dict(r)
    out.update(rdap(d, r['tld']))
    out.update(wiki_links(d))
    out.update(live(d))
    return out


if __name__ == '__main__':
    shortlist = json.load(open(IN))
    todo = [r for tld in TLDS for r in shortlist.get(tld, [])]
    print(f'enriching {len(todo)} domains...', file=sys.stderr)
    done = []
    with ThreadPoolExecutor(max_workers=5) as ex:
        for i, res in enumerate(ex.map(enrich, todo), 1):
            done.append(res)
            if i % 20 == 0:
                print(f'  {i}/{len(todo)}', file=sys.stderr)
    json.dump(done, open(OUT, 'w'), indent=1)
    avail = sum(1 for r in done if r.get('available') is True)
    gone = sum(1 for r in done if r.get('available') is False)
    print(f'done. available={avail} taken={gone} unknown={len(done)-avail-gone}',
          file=sys.stderr)
