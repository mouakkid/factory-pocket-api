#!/usr/bin/env bash
# Fetch filtered listings from ExpiredDomains.net member area.
# Requires an authenticated cookie jar (log in first; 2FA code arrives by email).
# Usage: ED_JAR=/path/to/jar.txt ./fetch_listings.sh /output/dir
set -euo pipefail
OUT="${1:-.}"
JAR="${ED_JAR:?set ED_JAR to an authenticated cookie jar file}"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
BASE="https://member.expireddomains.net/domains/expiredcom/"
# Shared criteria: available only, no adult, no hyphens/digits, <=13 chars, 200/page
COMMON="fwhois=22&fadult=1&fmaxhyphen=0&fmaxnumbercount=0&fmaxcharcount=13&flimit=200"

get() { curl -sS -c "$JAR" -b "$JAR" -A "$UA" -m 90 "$BASE?$1" -o "$OUT/$2"; sleep 2; }

# Core: DP>=10, BL>=10, first archived <=2015, >=30 captures (2 pages)
get "$COMMON&fdomainpop=10&fbl=10&fabirth_year=2015&facr=30&o=domainpop&r=d"            L1.html
get "$COMMON&fdomainpop=10&fbl=10&fabirth_year=2015&facr=30&o=domainpop&r=d&start=200"  L2.html
# Wikipedia-linked
get "$COMMON&fwikilinks=1&fdomainpop=5&fabirth_year=2018&o=domainpop&r=d"               L3.html
# Registered in >=2 other TLDs
get "$COMMON&fminstatustldreg=2&fdomainpop=10&fbl=5&fabirth_year=2016&o=domainpop&r=d"  L4.html
# Short premium (<=8 chars)
get "fwhois=22&fadult=1&fmaxhyphen=0&fmaxnumbercount=0&fmaxcharcount=8&flimit=200&fdomainpop=15&fabirth_year=2016&facr=30&o=domainpop&r=d" L5.html
# Majestic TrustFlow >= 10
get "$COMMON&fmseotf=10&fdomainpop=10&fabirth_year=2016&o=domainpop&r=d"                L6.html
echo "done -> $OUT/L1..L6.html"
