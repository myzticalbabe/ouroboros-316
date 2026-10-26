#!/usr/bin/env python3
"""Extract Form990 Part VII rosters from beam1 IRS XMLs -> roster_xml.csv (WSL paths)."""
import csv
import xml.etree.ElementTree as ET

FILES = [
    ("/root/BCC-REINVESTIGATION/00_raw/beam1_irs990_bcc_FY2025_public.xml", "BCC"),
    ("/root/BCC-REINVESTIGATION/00_raw/beam1_irs990_coca_TY2024.xml", "COCA"),
    ("/root/BCC-REINVESTIGATION/00_raw/beam1_irs990_tasc_TY2024.xml", "TASC"),
]
OUT = "/mnt/c/Users/clint/_irs_xml_cache/roster_xml.csv"


def g(e, tag, N):
    n = e.find("x:" + tag, N)
    return n.text.strip() if n is not None and n.text else ""


with open(OUT, "w", newline="") as out:
    w = csv.writer(out)
    w.writerow(["file", "org", "taxyr", "name", "title", "hours", "comp_org"])
    for f, org in FILES:
        r = ET.parse(f).getroot()
        N = {"x": r.tag.split("}")[0].strip("{")}
        taxyr = g(r, "TaxYr", N)
        n = 0
        for o in r.findall(".//x:Form990PartVIISectionAGrp", N):
            w.writerow([f.split("/")[-1], org, taxyr,
                        g(o, "PersonNm", N), g(o, "TitleTxt", N),
                        g(o, "AverageHoursPerWeekRt", N),
                        g(o, "ReportableCompFromOrgAmt", N)])
            n += 1
        print(f.split("/")[-1], n, flush=True)
print("WROTE " + OUT, flush=True)
