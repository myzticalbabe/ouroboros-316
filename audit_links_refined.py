#!/usr/bin/env python3
"""
audit_links_refined.py -- dead-link + absolute-path audit for the corpus.

Scans every *.html file in the corpus root for internal relative href/src
references and verifies the target exists. Flags:

  - dead links      : href/src pointing at a relative *.html that is not present
  - absolute paths  : href/src using file:///C:/... that should be relative
  - external links  : http(s) links are reported as informational (not dead —
                      they are not fetched; offline audit only)

Output is machine-parseable for the pre-commit gate:

  Dead links: N
  Internal links (OK): N
  ZERO dead links            <- summary line the gate greps for

Exit codes:
  0 = no dead links
  1 = dead links found
  2 = usage/scan error

Run:  python3 audit_links_refined.py [corpus_dir]
      (default corpus dir: current working directory)
"""

import os
import re
import sys

# Only count href/src inside real tags that fetch resources: <a href>, <link href>,
# <script src>, <img src>, <iframe src>, <source src>, <video src>, <audio src>.
# Documentation examples inside <span class="mono"> or <code> are NOT links and
# must not be counted (real incident: AUDIT_REPORT.html shows the fix as
# href="worm_analysis_dashboard.html" inside a span and was falsely flagged).
TAG_HREF_RE = re.compile(
    r'<(?:a|link)\s[^>]*?(?:href)\s*=\s*["\']([^"\'#]+)["\']', re.I
)
TAG_SRC_RE = re.compile(
    r'<(?:script|img|iframe|source|video|audio)\s[^>]*?(?:src)\s*=\s*["\']([^"\'#]+)["\']', re.I
)
FILE_ABS_RE = re.compile(r'^file:///[A-Za-z]:', re.I)
REL_HTML_RE = re.compile(r'^[^:/?#]+\.html?$', re.I)


def scan(corpus_dir: str):
    html_files = sorted(
        f for f in os.listdir(corpus_dir)
        if f.lower().endswith(".html")
    )
    dead = []
    internal_ok = 0
    external = 0
    abs_paths = []

    for fname in html_files:
        path = os.path.join(corpus_dir, fname)
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                content = fh.read()
        except OSError as e:
            print(f"  ERROR reading {fname}: {e}")
            continue

        matches = list(TAG_HREF_RE.finditer(content)) + list(TAG_SRC_RE.finditer(content))
        for m in matches:
            target = m.group(1).strip()
            if not target or target.startswith("#"):
                continue
            if FILE_ABS_RE.match(target):
                abs_paths.append((fname, target))
                continue
            if target.startswith(("http://", "https://", "//")):
                external += 1
                continue
            if REL_HTML_RE.match(target):
                target_path = os.path.join(corpus_dir, target.split("#")[0])
                if os.path.exists(target_path):
                    internal_ok += 1
                else:
                    dead.append((fname, target))

    # ---- report ----
    print(f"Audited {len(html_files)} HTML files in {corpus_dir}")
    print(f"Dead links: {len(dead)}")
    print(f"Internal links (OK): {internal_ok}")
    print(f"External links (informational): {external}")
    if abs_paths:
        print(f"Absolute file:// paths (should be relative): {len(abs_paths)}")
        for src, tgt in abs_paths[:15]:
            print(f"  {src} -> {tgt}")
    if dead:
        print("\nDEAD LINKS:")
        for src, tgt in dead[:50]:
            print(f"  {src} -> {tgt}")
    if not dead and not abs_paths:
        print("\nZERO dead links")
    return 1 if dead else (2 if abs_paths else 0)


if __name__ == "__main__":
    corpus_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    sys.exit(scan(corpus_dir))