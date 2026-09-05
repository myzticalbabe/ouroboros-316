# August 1, 2026 — Investigation Continuation ✅

**Status:** Continued the BCC (Berks Counseling Center, EIN 23-2043478) investigation.
Closed 3 gaps, advanced 2 more, and repaired the USASpending forensic script that had
been returning zero results since it was built in Session 10.

---

## Findings This Session

| Gap | Status | Finding |
|-----|--------|---------|
| **#19 SAMHSA Grant Reports** | 🟡 ADVANCED | USASpending API script FIXED (was returning 0 awards). Confirmed CCBHC grant **H79SM088878**: total obligation **$3,944,396**, outlay **$2,503,513** (63.5% drawn down), period **2023-09-30 → 2027-09-29**, CFDA 93.696. 51 federal awards enumerated totaling **$9,348,544.60**. |
| **#32 IRS Audit History** | ✅ RESOLVED | BCC: **ACTIVE** 501(c)(3), ruling **Feb 1979**, no revocation, no public IRS examination history. TEOS API is Akamai-blocked (403) from residential IP — manual lookup works. |
| **#6 Deborah Scull** | ✅ RESOLVED | **FOUND** — former **Lower Heidelberg Township Supervisor** (12+ yrs), **Central Tire Co.** family (Mogel family, Sinking Spring), Wernersville resident. Prior "completely invisible" finding overturned. |
| **#7 Jeffrey Ralph** | 🟡 ADVANCED | Candidate surfaced: **Dr. Jeffrey Ralph, GSK medicinal chemistry researcher** (PA). UNCONFIRMED as same person. Now listed as BCC **Treasurer** per 2025 filings. |
| **#2 Edward Jones** | ⏳ UNCHANGED | No public filing substantiates EJ managing BCC's portfolio. 990s don't name custodians; audit public summaries don't either. Board interlock confirmed; central question still open. |
| **#8 John Robinson** | ⏳ UNCONFIRMED | jrassociatesconsulting.com lead surfaced but identity match NOT verified. PA corporations search still needed. |

## USASpending Script Repair (usaspending_api.py)

Root causes of the 0-award failure (script built Session 10, never worked):
1. **Missing required filter** — USASpending v2 `spending_by_award` requires
   `filters.award_type_codes` (422 "Missing value").
2. **Mixed award-type groups** — `['A','B','C','D','02','03','04','05']` mixes contract
   codes (A/B/C/D) with grant codes (02-05); the API rejects mixed groups (422
   "'award_type_codes' must only contain types from one group"). Fixed with
   `GRANT_TYPE_CODES = ['02','03','04','05']` (BCC is a grantee).
3. **Invalid sort key** — `sort: '-Total Obligated'` → HTTP 400 (not in endpoint mappings).
   Removed.
4. **Wrong field name** — list view returns `Total Obligation` (assistance), not
   `Total Obligated` (contract). Fixed in `print_award()` + summation.
5. **api_post swallowed error bodies** — now captures HTTPError body for diagnosis.
6. **Dedup** — 3 duplicated fallback payloads consolidated into `name_search_awards()`.
7. **IndexError** — no-recipients path now returns early instead of `recipients[0]`.
8. **CCBHC grant missing from output** — added `keyword_search_awards()` FAIN merge
   (filters.keywords) so H79SM088878 appears; amount enrichment via per-award GET
   detail (`awards/{internal_id}/`), CCBHC prioritized, capped at 30 fetches.

Verified output: 51 awards, $9,348,544.60 total obligation, CCBHC grant present.

## Files Changed

| File | Change |
|------|--------|
| `Desktop/Libra/scrapers/usaspending_api.py` | Repaired USASpending v2 API payloads, added FAIN merge + amount enrichment (see above) |
| `INVESTIGATION_GAPS.html` | Added "Session 11 Findings" section; updated gaps #6, #7, #19, #32; corrected counts (5 critical / 11 high / 15 medium / 8 low = 39) |
| `SESSION_MILESTONE_2026-08-01.md` | This entry |

## Remaining Top Priorities

1. **ROUTE the COI Request Letter** through PA AG Charitable Trusts or SAMHSA — do NOT send directly to BCC (COI_REQUEST_LETTER.html ready, oversight routing only)
2. **Contact Herbein + Company** — does Edward Jones manage the portfolio?
3. **Send the Complaint Letter** to oversight bodies only — 7 city council + 3 county commissioners (BCC leadership EXCLUDED per SYSTEMIC_CORRUPTION_JUSTIFICATION.html)
4. **File PA Right-to-Know** with Berks County (BCC contracts, MOUs, payments)
5. **Verify John Robinson** via PA Dept of State corporations search
6. **Manual UJS Portal search** for ALL BCC court records
7. **Pull HigherGov performance narratives** for H79SM088878

### Post-Commit Audit — `53ed938` — 2026-09-05T10:08:45Z — ✅ PASS

| Field | Value |
|-------|-------|
| **Commit** | `53ed938` |
| **Branch** | `master` |
| **Time** | 2026-09-05T06:08:38-04:00 |
| **Message** | Add audit_links_refined.py dead-link checker |
| **Verification** | ✅ PASS (26 passed, 0 failed) |
| **Files Changed** | 1 file(s): audit_links_refined.py  |
| **Gap Counts** | 62 total, 53 open, 9 resolved |


### Post-Commit Audit — `e4c3373` — 2026-09-05T10:32:13Z — ✅ PASS

| Field | Value |
|-------|-------|
| **Commit** | `e4c3373` |
| **Branch** | `master` |
| **Time** | 2026-09-05T06:32:10-04:00 |
| **Message** | Add origin-aware CDP render harness |
| **Verification** | ✅ PASS (27 passed, 0 failed) |
| **Files Changed** | 3 file(s): SESSION_MILESTONE_2026-08-01.json SESSION_MILESTONE_2026-08-01.md verify_aoa_cdp.py  |
| **Gap Counts** | 62 total, 53 open, 9 resolved |

