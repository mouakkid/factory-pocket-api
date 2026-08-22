#!/usr/bin/env python3
"""Parse ExpiredDomains.net member listing HTML into JSONL rows."""
import re, sys, json, html as ihtml

FIELDS = ["length", "bl", "domainpop", "creationdate", "abirth",
          "aentries", "majestic_globalrank", "statustld_registered",
          "wikipedia_links", "whois"]

def cell_text(td_html):
    td_html = re.sub(r'<ul.*?</ul>', '', td_html, flags=re.S)  # drop hidden menus
    txt = re.sub(r'<[^>]+>', '', td_html)
    return ihtml.unescape(txt).strip()

def parse(path, tag):
    doc = open(path, encoding='utf-8', errors='replace').read()
    out = []
    for tr in re.findall(r'<tr>(.*?)</tr>', doc, re.S):
        if 'field_domain' not in tr:
            continue
        m = re.search(r'<td class="field_domain"><a[^>]*title="([^"]+)"', tr)
        if not m:
            continue
        row = {"src": tag, "domain": m.group(1).lower()}
        for f in FIELDS:
            mm = re.search(r'<td class="field_%s"[^>]*>(.*?)</td>' % f, tr, re.S)
            row[f] = cell_text(mm.group(1)) if mm else ""
        mbl = re.search(r'class="bllinks"[^>]*title="([0-9,]+)"', tr)
        if mbl:
            row["bl"] = mbl.group(1).replace(",", "")
        out.append(row)
    return out

if __name__ == "__main__":
    allrows = []
    for arg in sys.argv[1:]:
        path, tag = arg.split(":", 1)
        rows = parse(path, tag)
        print(f"{path} [{tag}]: {len(rows)} rows", file=sys.stderr)
        allrows.extend(rows)
    for r in allrows:
        print(json.dumps(r))
