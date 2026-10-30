#!/bin/bash
# verify_gaps.sh — gap-count consistency gate for the BCC investigation corpus
#
# Canonical: 62 total, 10 resolved, 52 open (GAP_SWEEP 2026-09-11; supersedes the Aug-1 50-count)
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
#      a) The medium-gap header says "24 Items Listed / 20 Open"; the check still
#         demanded "14 Open". The document was right, the check was old.
#      b) The check demanded "125 awards" from FORENSIC_EXTRACTION_BLUEPRINT.html
#         and labelled it "(not 51)". The root document is 2026-09-04 and says 51;
#         the 2026-08-04 snapshot is the one that says 125. The check therefore
#         required the NEWER document to be regressed to the older figure. It is
#         now a WARN that prints both values: which award count is correct is an
#         investigative question and this gate has no business answering it.
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
check "INVESTIGATION_GAPS.html" "52 open" "Gaps file says 52 open"
check "INVESTIGATION_GAPS.html" "10 resolved" "Gaps file says 10 resolved"
check "INVESTIGATION_GAPS.html" "62 total" "Gaps file says 62 total"
check_not "INVESTIGATION_GAPS.html" "39 open" "No stale 39 open reference"
check_not "INVESTIGATION_GAPS.html" "42 open" "No stale 42 open reference"
# NOT `49 total`: the only surviving "49 total" is inside the dated Aug-2 changelog
# entry ("5 cross-referenced gaps added (49 total)"), which is a true statement about
# that date. The stale claim the old check was reaching for is present-tense and has
# two shapes, both measured present in HEAD and absent from the current ledger:
# the summary box `>49</div>` and the footer sentence `49 gaps identified`.
check_not "INVESTIGATION_GAPS.html" ">49</div>|49 gaps identified" "No present-tense 49-total claim (box or footer)"
echo ""

# --- medium-gap sub-count (measured 2026-10-30: "24 Items Listed / 20 Open") ----
echo "INVESTIGATION_GAPS.html (medium-gap sub-count):"
check "INVESTIGATION_GAPS.html" "20 Open" "Medium header says 20 Open"
check_not "INVESTIGATION_GAPS.html" "14 Open" "No stale 14 Open medium count"
check_not "INVESTIGATION_GAPS.html" "13 open.*medium" "No stale 13 open medium count"
echo ""

# --- documents that carry the canonical counts in their own words ---------------
echo "HIDDEN_NETWORK.html:"
check "HIDDEN_NETWORK.html" "52 open" "HIDDEN_NETWORK says 52 open"
check "HIDDEN_NETWORK.html" "10 resolved" "HIDDEN_NETWORK says 10 resolved"
echo ""

echo "STRATEGY_OVERVIEW.html:"
check "STRATEGY_OVERVIEW.html" "52 open" "STRATEGY_OVERVIEW says 52 open"
check "STRATEGY_OVERVIEW.html" "10 resolved" "STRATEGY_OVERVIEW says 10 resolved"
check_not "STRATEGY_OVERVIEW.html" "39 of 49" "No stale 39 of 49 reference"
echo ""

echo "COMPLAINT_LETTER.html:"
check "COMPLAINT_LETTER.html" "52 of 62 gaps remain open" "COMPLAINT_LETTER says 52 of 62"
check_not "COMPLAINT_LETTER.html" "39 of 49" "No stale 39 of 49 reference"
echo ""

echo "COMPLAINT_LETTER_REDACTED.html:"
check "COMPLAINT_LETTER_REDACTED.html" "52 of 62 gaps remain open" "REDACTED says 52 of 62"
check_not "COMPLAINT_LETTER_REDACTED.html" "39 of 49" "No stale 39 of 49 reference"
echo ""

echo "COMPLAINT_AGENCY_LETTER.txt:"
check "COMPLAINT_AGENCY_LETTER.txt" "52 of 62 gaps remain open" "AGENCY_LETTER says 52 of 62"
echo ""

echo "README.md:"
check "README.md" "52 of 62 gaps open" "README says 52 of 62"
check "README.md" "62 gaps" "README says 62 gaps"
check_not "README.md" "39 of 49" "No stale 39 of 49 reference"
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
echo "FORENSIC_EXTRACTION_BLUEPRINT.html (award count, measured 2026-10-30):"
check "FORENSIC_EXTRACTION_BLUEPRINT.html" "138</strong> award-level federal awards" \
      "Blueprint states 138 award-level awards (live USAspending re-query)"
check_not "FORENSIC_EXTRACTION_BLUEPRINT.html" "51 awards / |125 awards / " \
      "No stale 51- or 125-award claim left in the blueprint"
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
TOTAL=$((PASS + FAIL))
echo "=========================================="
echo "RESULTS: $PASS passed, $FAIL failed — $TOTAL checks executed"
echo "=========================================="

if [ "$FAIL" -gt 0 ]; then
  echo ""
  echo "⚠ GAP-COUNT DRIFT DETECTED — fix the stale references above before committing."
  exit 1
fi

echo ""
echo "✅ No stale gap counts; the declared corpus authority matches the disk."
exit 0
