#!/usr/bin/env python3
"""Extract Part VII officer rows + Section B contractors from *_via_cdp.txt OCR.
Outputs: officers.csv, contractors.csv.
Layout-tolerant: rows keyed on (N) NAME pattern + nearby title (no Section-A proximity needed).
Heuristic for tesseract output — verify names against PDFs before citing.
"""
import csv
import glob
import os
import re

CACHE = os.path.dirname(os.path.abspath(__file__))
TITLES = ('PRESIDENT', 'VICE-PRESIDENT', 'SECRETARY', 'TREASURER', 'DIRECTOR',
          'TRUSTEE', 'CHAIRPERSON', 'CHAIRMAN', 'CHAIR', 'CFO', 'CEO', 'COO',
          'EXECUTIVE DIRECTOR', 'KEY EMPLOYEE')


def form_year(txt):
    m = re.search(r'For the (\d{4}) calendar year', txt)
    if m:
        return m.group(1)
    m = re.search(r'Form 990 \((\d{4})\)', txt)
    return m.group(1) if m else ''


def org_name(base, txt):
    m = re.search(r'C Name of organization\n(.+?)\n', txt)
    if m:
        return m.group(1).strip()
    return base.split('_')[0]  # BCC / COCA / TASC fallback


def extract_officers(txt):
    rows = []
    for m in re.finditer(r'\((\d+)\)\s+([A-Z][A-Z .\'\-&]+?)(?:\s+([\d.,]+))?\s*\n', txt):
        n, name, hours = m.group(1), m.group(2).strip(), m.group(3) or ''
        if len(name.split()) < 2 or len(re.sub(r'[^A-Za-z]', '', name)) < 6:
            continue
        seg = txt[m.end():m.end() + 400]
        nxt = re.search(r'\(\d+\)\s+[A-Z]', seg)
        seg = seg[:nxt.start()] if nxt else seg
        title = ''
        for t in sorted(TITLES, key=len, reverse=True):
            if re.search(r'\b' + t + r'\b', seg):
                title = t
                break
        if not title:
            continue
        tm = re.search(r'\b' + title + r'\b', seg)
        after = seg[tm.end():]
        comp_m = re.search(r'([\d,]+)\s+([\d,]+)(?:\s+([\d,]+))?', after)
        comp = tuple(re.sub(r'\s+', '', (g or '')) for g in comp_m.groups('')) if comp_m else ('', '', '')
        rows.append((n, name, hours, title) + comp)
    seen, out = set(), []
    for r in rows:
        if r[1] not in seen:
            seen.add(r[1])
            out.append(r)
    return out


def extract_contractors(txt):
    rows = []
    i = txt.find('highest compensated independent contractors')
    if i < 0:
        return rows
    j = txt.find('Part VIII', i)
    seg = txt[i:j if j > 0 else i + 4000]
    for m in re.finditer(
            r'\n([A-Z][A-Z0-9 &.,\'\-/]{4,60}?)\s+([A-Z][A-Z /&\-]{2,24}?)\s+(\d{3},\d{3})\b', seg):
        name, service, comp = (s.strip() for s in m.groups())
        if len(comp.replace(',', '')) >= 6 and 'TOTAL' not in name:
            rows.append((name, service, comp.replace(',', '')))
    return rows


def extract_totals(txt):
    m = re.search(r'd\s*Total.{0,80}?([\d,]{4,})\D{0,10}([\d,]+)\s+([\d,]+)', txt)
    if not m:
        return ('', '', '')
    return tuple(g.replace(',', '') for g in m.groups())


def main():
    opath = os.path.join(CACHE, 'officers.csv')
    cpath = os.path.join(CACHE, 'contractors.csv')
    with open(opath, 'w', newline='', encoding='utf-8') as fo, \
         open(cpath, 'w', newline='', encoding='utf-8') as fc:
        wo, wc = csv.writer(fo), csv.writer(fc)
        wo.writerow(['file', 'org', 'form_year', 'n', 'name', 'hours', 'title',
                     'comp_org', 'comp_related', 'other'])
        wc.writerow(['file', 'org', 'form_year', 'name', 'service', 'comp'])
        wt = csv.writer(open(os.path.join(CACHE, 'totals.csv'), 'w', newline='', encoding='utf-8'))
        wt.writerow(['file', 'org', 'form_year', 'total_org', 'total_related', 'total_other'])
        for path in sorted(glob.glob(os.path.join(CACHE, '*_via_cdp.txt'))):
            base = os.path.basename(path)
            txt = open(path, encoding='utf-8').read()
            org, fy = org_name(base, txt), form_year(txt)
            for r in extract_officers(txt):
                wo.writerow([base, org, fy] + list(r))
            for r in extract_contractors(txt):
                wc.writerow([base, org, fy] + list(r))
            wt.writerow([base, org, fy] + list(extract_totals(txt)))
    print('WROTE officers.csv + contractors.csv')


if __name__ == '__main__':
    main()
