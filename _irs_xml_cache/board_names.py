#!/usr/bin/env python3
"""Extract United Way board names from beam10 HTML -> uwberks_board.csv (WSL paths)."""
import csv
import re

SRC = "/root/BCC-REINVESTIGATION/00_raw/beam10_uwberks_board_20250322_20261026-0859.html"
OUT = "/mnt/c/Users/clint/_irs_xml_cache/uwberks_board.csv"

h = open(SRC, encoding="utf-8", errors="ignore").read()
text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S)
text = re.sub(r"<[^>]+>", " ", text)
text = re.sub(r"\s+", " ", text)
i = text.find("United Way Board of Directors")
j = text.find("Tocqueville", i)
seg = text[i:j if j > 0 else i + 6000]
# Board entries run Name / role / company in sequence; capture capitalized name chunks
names = re.findall(
    r"\b((?:Dr\. |Judge )?([A-Z][a-z]+) ([A-Z][a-z'’\-]+(?: [A-Z][a-z'’\-]+)?))\b", seg)
seen, rows = set(), []
for full, first, last in names:
    key = (first.lower(), last.lower())
    if key not in seen and len(first) > 1:
        seen.add(key)
        rows.append((full.strip(), first, last))
with open(OUT, "w", newline="") as out:
    w = csv.writer(out)
    w.writerow(["name", "first", "last"])
    w.writerows(rows)
print(len(rows), flush=True)
for r in rows:
    print(" ", r[0], flush=True)
