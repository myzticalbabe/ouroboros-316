#!/usr/bin/env python3
"""Cross-board intersections: 990 rosters (OCR + XML) x UWBerks board.
Also repairs contractor name/service splits. Outputs: crossboard.csv."""
import csv
import os
import re

CACHE = os.path.dirname(os.path.abspath(__file__))


def norm(name):
    name = re.sub(r"AS OF.*|UNTIL.*|BEGAN.*|ENDED.*", "", name).strip()
    return re.sub(r"\s+", " ", name).upper()


def load_names(path, namecol="name"):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    return [(r.get("org", "?"), r.get("file", "?"), norm(r[namecol])) for r in rows]


pools = {}
pools["990-OCR"] = load_names(os.path.join(CACHE, "officers.csv"))
pools["990-XML"] = load_names(os.path.join(CACHE, "roster_xml.csv"))
uwb = list(csv.DictReader(open(os.path.join(CACHE, "uwberks_board.csv"), encoding="utf-8")))
pools["UWBERKS"] = [("UWBERKS", r["source"], norm(r["name"])) for r in uwb]

# last-name index over 990 pools
by_last = {}
for pool, rows in pools.items():
    if pool == "UWBERKS":
        continue
    for org, src, nm in rows:
        parts = nm.split()
        if parts:
            by_last.setdefault(parts[-1], []).append((pool, org, src, nm))

hits = []
for r in uwb:
    last = r["last"].upper()
    first = r["first"].upper()
    for pool, org, src, nm in by_last.get(last, []):
        if first in nm:  # first-name confirms (avoids Tonya/Wynton Butler)
            hits.append((r["name"], nm, pool, org, src))

with open(os.path.join(CACHE, "crossboard.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["uwberks_name", "roster_name", "pool", "org", "source"])
    w.writerows(hits)
print("HITS:", len(hits))
for h in hits:
    print(" ", h)


def fix_contractors():
    p = os.path.join(CACHE, "contractors.csv")
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    fixed = []
    for r in rows:
        combo = (r["name"] + " " + r["service"]).strip()
        if combo.endswith("DOCTOR"):
            service, company = "DOCTOR", combo[:-len("DOCTOR")].strip()
        elif combo.endswith("HEALTHCARE SERVICES"):
            service, company = "HEALTHCARE SERVICES", combo[:-len("HEALTHCARE SERVICES")].strip()
        else:
            service, company = r["service"], r["name"]
        fixed.append([r["file"], r["org"], r["form_year"], company, service, r["comp"]])
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["file", "org", "form_year", "name", "service", "comp"])
        w.writerows(fixed)
    print("contractors fixed:", len(fixed))


fix_contractors()
