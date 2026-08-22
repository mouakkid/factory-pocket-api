#!/usr/bin/env python3
"""Parse ExpiredDomains listings with Majestic quality columns -> JSONL."""
import re, sys, json, html as ihtml, glob, os

FIELDS = ["length", "bl", "domainpop", "creationdate", "abirth", "aentries",
          "dmoz", "statustld_registered", "wikipedia_links", "related_cnobi",
          "majesticseo_tf", "majesticseo_cf", "majesticseo_domainpop",
          "majesticseo_ippop", "majesticseo_classcpop",
          "majesticseo_topicaltrustflow", "majesticseo_edudomainpop",
          "majesticseo_govdomainpop", "majesticseo_refdomaintypelive",
          "majesticseo_refdomaintypehomepagelink", "whois"]

SHORT = {"majesticseo_tf": "tf", "majesticseo_cf": "cf",
         "majesticseo_domainpop": "rd", "majesticseo_ippop": "rip",
         "majesticseo_classcpop": "rsub", "majesticseo_edudomainpop": "edu",
         "majesticseo_govdomainpop": "gov",
         "majesticseo_refdomaintypelive": "rdlive",
         "majesticseo_refdomaintypehomepagelink": "rdhome",
         "wikipedia_links": "wiki", "statustld_registered": "tldreg",
         "aentries": "acr", "abirth": "aby", "creationdate": "wby",
         "domainpop": "skdp", "related_cnobi": "rel"}


def clean(td):
    td = re.sub(r'<ul.*?</ul>', '', td, flags=re.S)
    return ihtml.unescape(re.sub(r'<[^>]+>', '', td)).strip()


def parse(path, tag, tld):
    doc = open(path, encoding='utf-8', errors='replace').read()
    out = []
    for tr in re.findall(r'<tr>(.*?)</tr>', doc, re.S):
        if 'field_domain' not in tr:
            continue
        m = re.search(r'<td class="field_domain"><a[^>]*title="([^"]+)"', tr)
        if not m:
            continue
        row = {"domain": m.group(1).lower(), "tld": tld, "src": tag}
        for f in FIELDS:
            mm = re.search(r'<td class="field_%s"[^>]*>(.*?)</td>' % f, tr, re.S)
            row[SHORT.get(f, f)] = clean(mm.group(1)) if mm else ""
        mbl = re.search(r'class="bllinks"[^>]*title="([0-9,]+)"', tr)
        if mbl:
            row["bl"] = mbl.group(1).replace(",", "")
        # topical trust flow topics live in title attributes
        ttf = re.search(r'<td class="field_majesticseo_topicaltrustflow"[^>]*>(.*?)</td>', tr, re.S)
        if ttf:
            topics = re.findall(r'title="([^"]+)"', ttf.group(1))
            row["ttf_topics"] = "|".join(topics[:3])
        out.append(row)
    return out


if __name__ == "__main__":
    allrows = []
    for path in sorted(glob.glob("R2_*.html")):
        tag = os.path.basename(path)[3:-5]      # R2_net_tf1.html -> net_tf1
        tld = tag.split("_")[0]
        rows = parse(path, tag, tld)
        print(f"{tag}: {len(rows)}", file=sys.stderr)
        allrows.extend(rows)
    with open("rows2.jsonl", "w") as f:
        for r in allrows:
            f.write(json.dumps(r) + "\n")
    print(f"total {len(allrows)}", file=sys.stderr)
