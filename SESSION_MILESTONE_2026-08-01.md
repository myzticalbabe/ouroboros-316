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


### Post-Commit Audit — `9745bc5` — 2026-09-05T10:38:02Z — ✅ PASS

| Field | Value |
|-------|-------|
| **Commit** | `9745bc5` |
| **Branch** | `master` |
| **Time** | 2026-09-05T06:38:01-04:00 |
| **Message** | Make CDP harness portable (cwd-relative scope, env chrome discovery) |
| **Verification** | ✅ PASS (27 passed, 0 failed) |
| **Files Changed** | 3 file(s): SESSION_MILESTONE_2026-08-01.json SESSION_MILESTONE_2026-08-01.md verify_aoa_cdp.py  |
| **Gap Counts** | 62 total, 53 open, 9 resolved |


### Post-Commit Audit — `48e1004` — 2026-09-23T04:24:04Z — ✅ PASS

| Field | Value |
|-------|-------|
| **Commit** | `48e1004` |
| **Branch** | `master` |
| **Time** | 2026-09-23T00:24:02-04:00 |
| **Message** | ShardFoundry 2026-09-23: STRATUM Gemma pipeline, dose-response, SVI spec, runbook principles |
| **Verification** | ✅ PASS (35 passed, 0 failed) |
| **Files Changed** | 11 file(s): .freebuff/handoff.md edge0-intel/HANDOFF.md edge0-intel/RAM_RUNBOOK.md edge0-intel/RUN_GEMMA_SURGERY.bat edge0-intel/SESSION_2026-09-23.md edge0-intel/STRATUM_THESIS.md edge0-intel/SVI_SPEC.md edge0-intel/scripts/collect_gemma_trunc.py edge0-intel/scripts/collect_stratum.py edge0-intel/scripts/gguf_abliterate.py edge0-intel/scripts/probe_stratum.py  |
| **Gap Counts** | 62 total, 53 open, 9 resolved |


### Post-Commit Audit — `533f824` — 2026-09-23T04:54:04Z — ✅ PASS

| Field | Value |
|-------|-------|
| **Commit** | `533f824` |
| **Branch** | `master` |
| **Time** | 2026-09-23T00:24:02-04:00 |
| **Message** | ShardFoundry 2026-09-23: STRATUM Gemma pipeline, dose-response, SVI spec, runbook principles |
| **Verification** | ✅ PASS (35 passed, 0 failed) |
| **Files Changed** | 14 file(s): .freebuff/handoff.md SESSION_MILESTONE_2026-08-01.json edge0-intel/HANDOFF.md edge0-intel/RAM_RUNBOOK.md edge0-intel/RUN_GEMMA_SURGERY.bat edge0-intel/SESSION_2026-09-23.md edge0-intel/STRATUM_THESIS.md edge0-intel/SVI_SPEC.md edge0-intel/evolve_log.jsonl edge0-intel/scripts/collect_gemma_trunc.py edge0-intel/scripts/collect_stratum.py edge0-intel/scripts/gguf_abliterate.py edge0-intel/scripts/probe_stratum.py edge0-intel/tests/test_surgery.py  |
| **Gap Counts** | 62 total, 53 open, 9 resolved |


### Post-Commit Audit — `9971ba7` — 2026-09-23T04:54:44Z — ✅ PASS

| Field | Value |
|-------|-------|
| **Commit** | `9971ba7` |
| **Branch** | `master` |
| **Time** | 2026-09-23T00:24:02-04:00 |
| **Message** | ShardFoundry 2026-09-23: STRATUM Gemma pipeline, dose-response, SVI spec, runbook principles |
| **Verification** | ✅ PASS (35 passed, 0 failed) |
| **Files Changed** | 15 file(s): .freebuff/handoff.md SESSION_MILESTONE_2026-08-01.json SESSION_MILESTONE_2026-08-01.md edge0-intel/HANDOFF.md edge0-intel/RAM_RUNBOOK.md edge0-intel/RUN_GEMMA_SURGERY.bat edge0-intel/SESSION_2026-09-23.md edge0-intel/STRATUM_THESIS.md edge0-intel/SVI_SPEC.md edge0-intel/evolve_log.jsonl edge0-intel/scripts/collect_gemma_trunc.py edge0-intel/scripts/collect_stratum.py edge0-intel/scripts/gguf_abliterate.py edge0-intel/scripts/probe_stratum.py edge0-intel/tests/test_surgery.py  |
| **Gap Counts** | 62 total, 53 open, 9 resolved |


### Post-Commit Audit — `f10ceee` — 2026-09-23T05:04:00Z — ✅ PASS

| Field | Value |
|-------|-------|
| **Commit** | `f10ceee` |
| **Branch** | `master` |
| **Time** | 2026-09-23T01:03:59-04:00 |
| **Message** | ShardFoundry: svi.py scoring+gates, sneg10 sign-flip result, dose-response ledger |
| **Verification** | ✅ PASS (35 passed, 0 failed) |
| **Files Changed** | 4 file(s): SESSION_MILESTONE_2026-08-01.json SESSION_MILESTONE_2026-08-01.md edge0-intel/SESSION_2026-09-23.md edge0-intel/scripts/svi.py  |
| **Gap Counts** | 62 total, 53 open, 9 resolved |


### Post-Commit Audit — `278705b` — 2026-09-23T05:32:06Z — ✅ PASS

| Field | Value |
|-------|-------|
| **Commit** | `278705b` |
| **Branch** | `master` |
| **Time** | 2026-09-23T01:32:02-04:00 |
| **Message** | ShardFoundry: stock retest variance row (16/100), readback verification noted |
| **Verification** | ✅ PASS (35 passed, 0 failed) |
| **Files Changed** | 3 file(s): SESSION_MILESTONE_2026-08-01.json SESSION_MILESTONE_2026-08-01.md edge0-intel/evolve_log.jsonl  |
| **Gap Counts** | 62 total, 53 open, 9 resolved |


### Post-Commit Audit — `fc864a8` — 2026-09-23T05:47:30Z — ✅ PASS

| Field | Value |
|-------|-------|
| **Commit** | `fc864a8` |
| **Branch** | `master` |
| **Time** | 2026-09-23T01:47:26-04:00 |
| **Message** | ShardFoundry: spark-x25 stock baseline (0/100, caps 17/20) |
| **Verification** | ✅ PASS (35 passed, 0 failed) |
| **Files Changed** | 3 file(s): SESSION_MILESTONE_2026-08-01.json SESSION_MILESTONE_2026-08-01.md edge0-intel/evolve_log.jsonl  |
| **Gap Counts** | 62 total, 53 open, 9 resolved |


### Post-Commit Audit — `9ffb7a8` — 2026-09-23T06:06:43Z — ✅ PASS

| Field | Value |
|-------|-------|
| **Commit** | `9ffb7a8` |
| **Branch** | `master` |
| **Time** | 2026-09-23T02:06:42-04:00 |
| **Message** | ShardFoundry: dim-mismatch skip + test 6, Spark bench, session record |
| **Verification** | ✅ PASS (35 passed, 0 failed) |
| **Files Changed** | 5 file(s): SESSION_MILESTONE_2026-08-01.json SESSION_MILESTONE_2026-08-01.md edge0-intel/SESSION_2026-09-23.md edge0-intel/scripts/gguf_abliterate.py edge0-intel/tests/test_surgery.py  |
| **Gap Counts** | 62 total, 53 open, 9 resolved |


### Post-Commit Audit — `eaf6f16` — 2026-09-23T06:18:47Z — ✅ PASS

| Field | Value |
|-------|-------|
| **Commit** | `eaf6f16` |
| **Branch** | `master` |
| **Time** | 2026-09-23T02:18:45-04:00 |
| **Message** | ShardFoundry: Spark mesh-driver probe (routing pass, JSON needs grammar) |
| **Verification** | ✅ PASS (35 passed, 0 failed) |
| **Files Changed** | 3 file(s): SESSION_MILESTONE_2026-08-01.json SESSION_MILESTONE_2026-08-01.md edge0-intel/scripts/probe_spark_mesh.py  |
| **Gap Counts** | 62 total, 53 open, 9 resolved |


### Post-Commit Audit — `d6952b7` — 2026-09-23T15:16:43Z — ✅ PASS

| Field | Value |
|-------|-------|
| **Commit** | `d6952b7` |
| **Branch** | `master` |
| **Time** | 2026-09-23T11:16:41-04:00 |
| **Message** | ShardFoundry docs: reasoning-harness fix, Spark/Graft/Armada findings, handoff sync |
| **Verification** | ✅ PASS (35 passed, 0 failed) |
| **Files Changed** | 5 file(s): .freebuff/handoff.md edge0-intel/HANDOFF.md edge0-intel/SESSION_2026-09-23.md edge0-intel/scripts/eval_full.py edge0-intel/scripts/probe_thinkflag.py  |
| **Gap Counts** | 62 total, 53 open, 9 resolved |


### Post-Commit Audit — `aa8781f` — 2026-09-23T17:23:05Z — ✅ PASS

| Field | Value |
|-------|-------|
| **Commit** | `aa8781f` |
| **Branch** | `master` |
| **Time** | 2026-09-23T13:23:03-04:00 |
| **Message** | ShardFoundry: per-layer sweep driver + layers filter + visible bat |
| **Verification** | ✅ PASS (35 passed, 0 failed) |
| **Files Changed** | 5 file(s): SESSION_MILESTONE_2026-08-01.json SESSION_MILESTONE_2026-08-01.md edge0-intel/RUN_LING_SWEEP.bat edge0-intel/scripts/gguf_abliterate.py edge0-intel/scripts/sweep_ling_layers.py  |
| **Gap Counts** | 62 total, 53 open, 9 resolved |


### Post-Commit Audit — `0cf33b1` — 2026-09-23T17:56:00Z — ✅ PASS

| Field | Value |
|-------|-------|
| **Commit** | `0cf33b1` |
| **Branch** | `master` |
| **Time** | 2026-09-23T13:55:54-04:00 |
| **Message** | ShardFoundry: disk-steady sweep, G-drive findings, disk rules |
| **Verification** | ✅ PASS (35 passed, 0 failed) |
| **Files Changed** | 5 file(s): SESSION_MILESTONE_2026-08-01.json SESSION_MILESTONE_2026-08-01.md edge0-intel/RAM_RUNBOOK.md edge0-intel/RUN_LING_SWEEP.bat edge0-intel/scripts/sweep_ling_layers.py  |
| **Gap Counts** | 62 total, 53 open, 9 resolved |


### Post-Commit Audit — `1319c28` — 2026-09-23T18:25:38Z — ✅ PASS

| Field | Value |
|-------|-------|
| **Commit** | `1319c28` |
| **Branch** | `master` |
| **Time** | 2026-09-23T14:25:35-04:00 |
| **Message** | ShardFoundry: emergent-capability gap audit G1-G15 + MCG same-layer prescription |
| **Verification** | ✅ PASS (35 passed, 0 failed) |
| **Files Changed** | 3 file(s): SESSION_MILESTONE_2026-08-01.json SESSION_MILESTONE_2026-08-01.md edge0-intel/EMERGENT_GAP_AUDIT.md  |
| **Gap Counts** | 62 total, 53 open, 9 resolved |

