#!/usr/bin/env python3
"""Re-verify Wikipedia citations querying BOTH protocols.

The earlier pass used the API default, which only matches http:// links;
https:// citations were silently missed.
"""
import json, sys, time, requests
S = requests.Session(); S.headers['User-Agent'] = 'domain-research/1.0'
WIKIS = ['en','fr','de','es','it','nl','pt','ru','pl','sv','ja','ar']

def q(lang, domain, proto):
    p = {'action':'query','list':'exturlusage','euquery':domain,'eulimit':100,
         'euprop':'title|url','format':'json','maxlag':5}
    if proto: p['euprotocol'] = proto
    for attempt in range(4):
        try:
            r = S.get(f'https://{lang}.wikipedia.org/w/api.php', params=p, timeout=30)
            if r.status_code == 200:
                return r.json().get('query',{}).get('exturlusage',[])
        except Exception:
            pass
        time.sleep(1.5*(attempt+1))
    return None

def check(domain):
    arts, other, langs, errs = [], 0, [], 0
    for lang in WIKIS:
        hit = False
        for proto in ('http','https'):
            items = q(lang, domain, proto)
            if items is None:
                errs += 1; continue
            for it in items:
                if it.get('ns') == 0:
                    arts.append(f"{lang}:{it['title']}"); hit = True
                else:
                    other += 1
            time.sleep(0.15)
        if hit: langs.append(lang)
    u = sorted(set(arts))
    return {'wiki_articles': u, 'wiki_article_count': len(u),
            'wiki_nonarticle': other, 'wiki_langs': langs, 'wiki_errors': errs}

if __name__ == '__main__':
    top = json.load(open('top10.json'))
    changed = []
    for tld in ('com','net','org','io','ai'):
        for r in top[tld]:
            before = r['wiki_article_count']
            res = check(r['domain'])
            r.update(res)
            if res['wiki_article_count'] != before:
                changed.append((r['domain'], before, res['wiki_article_count'], res['wiki_articles'][:6]))
                print(f"  CHANGED {r['domain']}: {before} -> {res['wiki_article_count']}  {res['wiki_articles'][:6]}", flush=True)
    json.dump(top, open('top10.json','w'), indent=1)
    print(f"\nre-verified 50 domains; {len(changed)} corrected")
