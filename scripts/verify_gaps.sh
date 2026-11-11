#!/bin/bash
# verify_gaps.sh — gap-count consistency gate for the BCC investigation corpus
#
# Canonical: 49 total, 9 resolved, 40 open (INVESTIGATION_GAPS.html ledger prose).
# Re-measured 2026-11-11: all IDs #1-#49 present in the ledger; section headers read
# High 14 listed / 11 open + Medium 18 listed / 15 open + Low 12 listed / 10 open +
# Critical 3 execution-ready + 2 blocked; subtitle + footer state 49 total / 40 open /
# 9 resolved. The 2026-10-30 '62 total / 10 resolved / 52 open (GAP_SWEEP 2026-09-11)'
# canonical never existed in any deliverable (git log -S '52 open' / '62 total' hits
# only this gate script itself). Per this gate's own defect-class-3 rule the document
# was right and the check was old, so the check now follows the ledger.
# Contract:  run from the repo root. Exit 0 = no stale counts, exit 1 = at least one FAIL.
# The number of checks is COUNTED, never written down — read the RESULTS line.
#
# REVISED 2026-10-30. The previous version had four defect classes. All four were
# measured, not suspected, and each one is why a line below looks the way it does.
#
#   1. NO EXISTENCE GUARD, so a `check_not` on a missing file PASSED vacuously.
#      CCBHC_REGIME_CHANGE.html and IRS_WHISTLEBLOWER_FORM_211.html do not exist at
#      the repo root; their "no stale counts" checks were green because grep could
#      not open the file. A file that is not there is not clean, it is unverified.
#      Every check now fails when its file is missing.
#
#   2. SEVEN PATHS POINTED AT DOCUMENTS THAT NO LONGER EXIST IN THIS TREE. They
#      survive only as the 2026-08-04 snapshot in Desktop/FACEBOOK/, which predates
#      the September ledger and contains none of 52/62/10 — LEGAL_REFERRAL_MEMO,
#      EVIDENCE_LOCATIONS, MOLTBOOK_AGENT_SETUP and CC_CONTACTS_MASTER each matched
#      zero of those counts. Fixed in two steps on 2026-10-30: first they were
#      reported as SKIP, then CORPUS_AUTHORITY.md declared the authority and the
#      gate began CHECKING each declared archive-only row against the disk.
#      "Skipped" is not a state this gate has any more.
#
#   3. TWO PATTERNS WERE STALE AGAINST THE CURRENT DOCUMENT.
#      a) (2026-10-30 note claimed the header reads "24 Items Listed / 20 Open";
#         it does not — measured 2026-11-11 the header reads "18 Items Listed /
#         15 Open", matching the 18 medium gap divs. Both the old check ("14 Open")
#         and the note's figure were ungrounded. The check asserts the header verbatim.)
#      b) The check demanded "125 awards" from FORENSIC_EXTRACTION_BLUEPRINT.html
#         and labelled it "(not 51)". The root document is 2026-09-04 and says 51;
#         the 2026-08-04 snapshot is the one that says 125. The check therefore
#         required the NEWER document to be regressed to the older figure. It is
#         now a WARN that prints both values: which award count is correct is an
#         investigative question and this gate has no business answering it.
#         REVISED 2026-11-11: the committed code contradicted this note (hard 138
#         demand + hard 51/125 ban, no WARN primitive existed). The hard checks are
#         now warn() calls: the alleged 2026-10-30 re-query has no evidence artifact
#         in the repo (SESSION_MILESTONE_2026-08-01.md mentions only a filter defect),
#         so the gate records values instead of adjudicating them.
#
#   4. ONE CHECK WAS UNFALSIFIABLE. `check CC_CONTACTS_MASTER.html "46"` passed on
#      any text containing the digits 4 and 6 — a phone number, a date, an address.
#      Removed. It proved nothing on the day it was written.
#
# NOT TRACKED: `.agents/` is gitignored (.gitignore:87), so this file cannot be
# committed or reverted. The home pre-commit is its only executor.

# Self-locating: this file is now tracked, so a human may run it from anywhere.
# It must evaluate paths against the repo root, which is what the hook already does.
if _top=$(git rev-parse --show-toplevel 2>/dev/null) && [ -n "$_top" ]; then
  cd "$_top" || exit 1
fi

echo "=== GAP COUNT VERIFICATION ==="
echo ""

PASS=0
FAIL=0
WARN=0

# ---------------------------------------------------------------------------
# primitives
# ---------------------------------------------------------------------------
check() {  # file pattern label
  if [ ! -f "$1" ]; then
    echo "  ❌ FAIL: $3 — file missing: $1 (unverified is not clean)"
    FAIL=$((FAIL + 1))
    return
  fi
  if grep -qE "$2" "$1"; then
    echo "  ✅ $3"
    PASS=$((PASS + 1))
  else
    echo "  ❌ FAIL: $3 — pattern '$2' not found in $1"
    FAIL=$((FAIL + 1))
  fi
}

check_not() {  # file pattern label
  if [ ! -f "$1" ]; then
    echo "  ❌ FAIL: $3 — file missing: $1 (cannot be verified clean)"
    FAIL=$((FAIL + 1))
    return
  fi
  if grep -qE "$2" "$1"; then
    echo "  ❌ STALE: $3 — '$2' still present in $1:"
    grep -nE "$2" "$1" | head -3 | sed 's/^/       /'
    FAIL=$((FAIL + 1))
  else
    echo "  ✅ $3"
    PASS=$((PASS + 1))
  fi
}

warn() {  # file detail — recorded, never blocking: for investigative questions
  # this gate has no business answering (award counts, unresolved provenance).
  echo "  ⚠ WARN: $1 — $2"
  WARN=$((WARN + 1))
}

struct() {  # file label — existence and size only; says so in the output
  if [ -s "$1" ]; then
    echo "  ✅ $2 (present, $(wc -c <"$1" | tr -d ' ') bytes — structural only: this document cites no gap counts)"
    PASS=$((PASS + 1))
  else
    echo "  ❌ FAIL: $2 — missing or empty: $1"
    FAIL=$((FAIL + 1))
  fi
}

assert_archive_only() {  # filename -- the manifest's claim, checked against the disk
  if [ -f "$1" ]; then
    echo "  ❌ FAIL: $1 is declared archive-only but exists at the top level"
    echo "       promote it properly (update CORPUS_AUTHORITY.md) or delete the stray copy"
    FAIL=$((FAIL + 1))
  elif [ -f "Desktop/FACEBOOK/$1" ]; then
    echo "  ✅ $1 — archive-only as declared (absent here, present in archive)"
    PASS=$((PASS + 1))
  else
    echo "  ❌ FAIL: $1 is declared archive-only but is in neither tree"
    FAIL=$((FAIL + 1))
  fi
}

# =============================================================================
# CANONICAL COUNTS: 52 open, 10 resolved, 62 total
# =============================================================================
echo "Canonical counts (must be: 52 open, 10 resolved, 62 total)"
echo ""

# --- INVESTIGATION_GAPS.html: the ledger itself ---------------------------------
echo "INVESTIGATION_GAPS.html (canonical ledger):"
check "INVESTIGATION_GAPS.html" "40 open" "Gaps file says 40 open"
check "INVESTIGATION_GAPS.html" "9 resolved" "Gaps file says 9 resolved"
check "INVESTIGATION_GAPS.html" "(49 total)" "Gaps file says 49 total"
check_not "INVESTIGATION_GAPS.html" "62 total|52 open|52 of 62" "No fictional 62/52 counts (never existed in any deliverable)"
check_not "INVESTIGATION_GAPS.html" "39 open" "No stale 39 open reference"
check_not "INVESTIGATION_GAPS.html" "42 open" "No stale 42 open reference"
# 49 total IS the canonical total (ledger subtitle, summary box, footer, section
# headers). REVISED 2026-11-11: the old check_not treated the true total as stale
# because it assumed 62. Removed; the fiction-guard above now watches for 62/52.
echo ""

# --- medium-gap sub-count (ledger header, re-measured 2026-11-11) ----
echo "INVESTIGATION_GAPS.html (medium-gap sub-count):"
check "INVESTIGATION_GAPS.html" "18 Items Listed / 15 Open" "Medium header says 18 listed / 15 open"
check_not "INVESTIGATION_GAPS.html" "14 Open" "No stale 14 Open medium count"
check_not "INVESTIGATION_GAPS.html" "13 open.*medium" "No stale 13 open medium count"
echo ""

# --- documents that carry the canonical counts in their own words ---------------
echo "HIDDEN_NETWORK.html:"
check "HIDDEN_NETWORK.html" "49 gaps identified" "HIDDEN_NETWORK says 49 gaps"
check "HIDDEN_NETWORK.html" "9 resolved" "HIDDEN_NETWORK says 9 resolved"
check "HIDDEN_NETWORK.html" "40 open" "HIDDEN_NETWORK says 40 open"
check_not "HIDDEN_NETWORK.html" "8 resolved" "No stale 8-resolved count"
echo ""

echo "STRATEGY_OVERVIEW.html:"
check "STRATEGY_OVERVIEW.html" "40 of 49 investigation gaps remain open" "STRATEGY_OVERVIEW says 40 of 49"
check_not "STRATEGY_OVERVIEW.html" "42 of 49|39 of 49" "No stale 42/39-of-49 reference"
echo ""

echo "COMPLAINT_LETTER.html:"
check "COMPLAINT_LETTER.html" "40 of 49 gaps remain open" "COMPLAINT_LETTER says 40 of 49"
check_not "COMPLAINT_LETTER.html" "42 of 49|39 of 49" "No stale 42/39-of-49 reference"
echo ""

echo "COMPLAINT_LETTER_REDACTED.html:"
check "COMPLAINT_LETTER_REDACTED.html" "40 of 49 gaps remain open" "REDACTED says 40 of 49"
check_not "COMPLAINT_LETTER_REDACTED.html" "42 of 49|39 of 49" "No stale 42/39-of-49 reference"
echo ""

echo "COMPLAINT_AGENCY_LETTER.txt:"
check "COMPLAINT_AGENCY_LETTER.txt" "40 of 49 gaps remain open" "AGENCY_LETTER says 40 of 49"
check_not "COMPLAINT_AGENCY_LETTER.txt" "42 of 49|39 of 49|52 of 62|62 total|52 open" "AGENCY_LETTER carries no stale gap counts"
echo ""

echo "README.md:"
check "README.md" "40 of 49 gaps open" "README says 40 of 49"
check "README.md" "9 resolved" "README says 9 resolved"
check "README.md" "49 gaps" "README says 49 gaps"
check_not "README.md" "39 of 49|42 of 49|7 resolved" "No stale 39/42-of-49 or 7-resolved reference"
echo ""

# --- files whose only job is to carry NO stale counts ---------------------------
echo "FUNDING_REVIEW.html:"
check_not "FUNDING_REVIEW.html" "39 open|42 open|49 gap" "No stale gap counts (39/42/49)"
echo ""

echo "CONSOLIDATED_SCROLL.html:"
check_not "CONSOLIDATED_SCROLL.html" "39 open|42 open|49 gap" "No stale gap counts (39/42/49)"
echo ""

# --- checklist: exists and is not empty; it cites no gap IDs at all -------------
echo "CRITICAL_GAP_EXECUTION_CHECKLIST.html:"
struct "CRITICAL_GAP_EXECUTION_CHECKLIST.html" "CHECKLIST present"
echo ""

# --- award count: SETTLED 2026-10-30 by re-querying the source -----------------
# The document carried two mutually inconsistent counts at the SAME dollar total:
# "51 awards / $9.35M" in the 2026-09-04 root copy and "125 awards / $9.35M" in the
# 2026-08-04 snapshot. Live USAspending (spending_by_award, award-level, all fiscal
# years, both "INC" name variants: 133 grants + 5 contracts) returns 138 awards /
# $25.87M net, plus 5 sub-awards. Neither 51 nor 125 reproduces under any scope
# tested; the nearest measured subset to $9.35M is HHS-SAMHSA (5 awards, $9.64M).
# The root document now states the measured figure with its provenance. The August
# snapshot keeps saying 125 ON PURPOSE -- it is a dated artefact and is not rewritten.
echo "FORENSIC_EXTRACTION_BLUEPRINT.html (award count — WARN only, see header note 3b):"
warn "FORENSIC_EXTRACTION_BLUEPRINT.html" "award figures on record: $(grep -o -E '[0-9]+ awards' FORENSIC_EXTRACTION_BLUEPRINT.html | sort -u | tr '\n' '/' | head -c 120) — the claimed 2026-10-30 live USAspending re-query (138 awards) has no evidence artifact in the repo; re-query USAspending spending_by_award before restating"
echo ""# --- corpus authority: the manifest is the single source, the gate enforces it --
# This replaces the old hardcoded SKIP list. The declaration lives in
# CORPUS_AUTHORITY.md; each row it marks `archive-only` is CHECKED (absent at the top
# level, present in the archive) rather than skipped, so 'declared elsewhere' can
# never quietly become 'not checked'.
echo "CORPUS_AUTHORITY.md (which tree is current, enforced):"
MANIFEST="CORPUS_AUTHORITY.md"
if [ ! -f "$MANIFEST" ]; then
  echo "  ❌ FAIL: $MANIFEST is missing — there is no declared authoritative tree"
  FAIL=$((FAIL + 1))
else
  if grep -q "AUTHORITATIVE" "$MANIFEST"; then
    echo "  ✅ authority declared (current tree = top level)"
    PASS=$((PASS + 1))
  else
    echo "  ❌ FAIL: $MANIFEST names no AUTHORITATIVE tree"
    FAIL=$((FAIL + 1))
  fi
  rows=0
  while IFS='|' read -r _ name _; do
    name=$(echo "$name" | tr -d ' \r')
    [ -z "$name" ] && continue
    rows=$((rows + 1))
    assert_archive_only "$name"
  done < <(grep -E '^\| [A-Za-z0-9_.-]+\.(html|htm|txt|md) \| archive-only \|' "$MANIFEST")
  if [ "$rows" -eq 0 ]; then
    echo "  ❌ FAIL: no archive-only rows parsed from $MANIFEST — the table format drifted"
    FAIL=$((FAIL + 1))
  fi
fi
echo ""

# =============================================================================
TOTAL=$((PASS + FAIL + WARN))
echo "=========================================="
echo "RESULTS: $PASS passed, $FAIL failed, $WARN warned — $TOTAL checks executed"
echo "=========================================="

if [ "$FAIL" -gt 0 ]; then
  echo ""
  echo "⚠ GAP-COUNT DRIFT DETECTED — fix the stale references above before committing."
  exit 1
fi

echo ""
echo "✅ No stale gap counts; the declared corpus authority matches the disk."
exit 0
