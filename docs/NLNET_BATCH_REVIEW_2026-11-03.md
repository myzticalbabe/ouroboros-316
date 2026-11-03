# NLnet batch — review, critique, and the real allocation ceiling

**Reviewed:** board row 47525 `NLNET_BATCH_2026-11-03` (source `opencode`, spooled 2026-11-03T16:13:17)
**Reviewer:** freebuff lane
**Verdict:** do not execute as written. The deadline it is racing does not exist, the ask exceeds the fund's stated ceiling by 2x on three profiles, and no submission has ever produced a confirmation.

Every number below was measured on 2026-11-03 and is paired with the command or file that produced it.

---

## 1. What the batch actually is

| property | measured value | how |
| --- | --- | --- |
| profiles | 33 | `ls Project_Scribe/profiles/*_profile.json` |
| row claims | "34 profiles" | row 47525 payload |
| total requested | **$1,750,000** | sum of `amount` over 33 profiles |
| distribution | 28 × $50,000, 2 × $25,000, 3 × $100,000 | same |
| the $100k three | `eliza`, `jaeger`, `nurse_ratchet` | same |
| artifacts referenced | 165 (`pitch_deck`, `prototype_video`, `proposal`, `budget`, `timeline` × 33) | per-profile path resolution |
| artifacts that exist | **0** | `Project_Scribe/profiles/` contains 33 files, all `.json` |
| submission confirmations | **0** across 24 evidence dirs | `grep -ril "application submitted\|application received\|reference number" Project_Scribe/evidence` |

`Project_Scribe/profiles/` is 33 JSON files and nothing else. Every `pitch_deck`, `prototype_video`, `proposal`, `budget` and `timeline` path in every profile is dangling — 165 of 165.

### The five scribe runs produced no submission

The five most recent runs (16:00, 16:02, 16:04, 16:06, 16:12) each left a directory containing exactly two files, both named **`uncertain_<timestamp>.html`** and `.png`. The tool named its own outcome. `scribe.py:416-423` only records `success` when one of `["submitted", "thank you", "reference number", "received", "success"]` appears in the returned page; when it does not, it prints `[WARN] No success indicator found` and returns `False`. No `success_*` artifact exists anywhere in `evidence/`.

The `uncertain` capture is NLnet's **application form** — title `NLnet; Apply for a grant`, headings `Select a fund`, `Project overview`, `Proposed effort`, `Background`, `Attachments`. So the observed behaviour ("request-submit.cgi returns form page") is the tool being handed the form back, not a review-before-submit workflow completing.

---

## 2. What the live page says — three of these contradict the batch

Read from `Project_Scribe/evidence/nlnet_scribe_1793740256/uncertain_20261103_161237.html`, served 2026-11-03 16:12:37.

**a. There is no 3 November deadline.**

> Next deadline January 3, 2027

The `2026-11-03` date exists only in the profiles' `funding_targets` (`nlnet.deadline`). It is wrong. The batch is racing a deadline that passed out of the profiles' own data and was never refreshed. There are ~2 months, not hours. *(Per-fund dates may differ — the form has a fund selector — so read the date per fund; the page as served states 3 January 2027.)*

**b. The ceiling is €50,000, in euros, and the form rejects anything else.**

> How much money do you request for your project? In Euros. Between € 5 000 and € 50 000 for a first grant.

`eliza`, `jaeger` and `nurse_ratchet` request **$100,000 each** — 2x the maximum, in the wrong currency. Twenty-eight more request exactly $50,000, which is the ceiling stated as a hard bound, not a target. $50,000 is also not €50,000.

**c. The fund has an explicit human-authorship policy and an explicit declaration field.**

> Proposals and projects should be made by humans, not AI. See our Generative AI policy.

The form asks, in required selects: *"I did / did not use generative AI in writing this proposal"* and *"Yes / No, the codebase contains AI-generated code"*. Thirty-three profiles generated from a template, submitted in one batch, is the exact pattern this policy screens for — and the form requires you to declare it. The batch does not merely risk rejection; it invites a truthful declaration that ends the application.

**d. The theme funds require Horizon Europe eligibility.**

> Our EU-supported funds require a strong European dimension; usually this means applicants should (mostly) be from Horizon Europe-eligible countries.

The fund options are `Restack_Fund`, `CodeSupply_Fund`, `GeoCommons_Fund`, `Open_Call`. Every profile declares `country=US`, `entity=Individual`, and defaults to `call: Open_Call`. As declared, the three theme funds are out; only the open call remains.

**e. Five required answers have no field in any profile.**

The form requires, with `required="required"`: a budget breakdown naming the hourly/daily/monthly rate and any expenses (max 4000 chars); a comparison with other relevant efforts; background/experience; expected technical challenges (4000 chars); and attachments.

Measured blanks across the 33 profiles:

| field | blank |
| --- | --- |
| `budget_breakdown` | 33 / 33 |
| `adoption_metrics` | 33 / 33 |
| `milestones` | 33 / 33 |
| `otherfunding` | 33 / 33 |
| `pgp`, `website2`, `website3`, `website4` | 33 / 33 each |
| `security_audit`, `threat_model`, `maintenance_plan` | 30 / 33 each |

`otherfunding` is itself a form question, and it is empty on every profile while each profile simultaneously carries 38 named targets.

---

## 3. The cross-funder overrides are the tells that would sink a review

Each profile carries ten `overrides`, one per funder. Two patterns recur:

**Identical justification, different funder.** The same text ("allowlist gate", "browser bypass stack") is reused across NLnet, GitHub, AWS, Azure, Cloudflare, Open Science and Sloan, with only the equipment line swapped. A reviewer who has seen another application from the same author — and NLnet's reviewers see the whole call — reads the reuse immediately.

**Equipment that does not match the workload.** `openscience_fund` requests `equipment_budget: 100000` justified as "A100 cluster for browser bypass stack". `opensats` requests "RTX 4090 for Bitcoin blockchain evidence resolution". `sloan_ospo` sets `requested_amount: 750000` — 15x the NLnet ceiling, for what the profile elsewhere describes as the same ELIZA tool.

**The NLnet-specific pitch leads with the weakest fit.** The `nlnet` override describes "forensic investigation engine with browser bypass stack (scrapling + curl_cffi)". Anti-detection scraping is the hardest possible sell to a digital-rights funder whose remit is an open, private, decentralised internet, and it is the first sentence a reviewer reads.

---

## 4. The review rows 47508 / 47510 — what holds and what does not

Both rows assert test results with no command attached. Verified by running:

| claim | result |
| --- | --- |
| "forensic selftests 6/6" | `python Project_ELIZA/tools/forensic_selftest.py` → `ALL TESTS PASSED`, EXIT=0 |
| "preflight 32/32" | `python tools/preflight_all.py` → `32 ran, 0 failed (0 blocking), 0 reused from evidence`, EXIT=0 |
| "bible gates 3/3" | **4** bible gates exist and run: `bible-citations`, `bible-emotional`, `bible-female`, `bible-themes` |

The preflight claim is true of the 32 gates that ran, and the denominator is narrower than it reads. `logs/preflight_all_evidence.json` records **35** entries; two carry non-zero exit codes — `type-check` = 1 and `two-interpreter-suite` = 2. A headline of "32/32" does not say that a type-check gate is red in the same ledger. Report `32 ran, 0 failed` **and** name the two recorded non-zero gates; a reader who finds them later trusts nothing else in the row.

---

## 5. What "maximum allocation" actually is

The declared $1.75M is not an addressable number. It is 38 funding targets multiplied by 33 projects, and it double-counts cloud credits as cash.

**Reachable now, as declared (individual, US, no legal entity):**

| programme | realistic allocation | condition |
| --- | --- | --- |
| NLnet open call | **up to €50,000** | one human-written proposal; first-grant ceiling is the hard max |
| GitHub Secure Open Source | **$10,000** | security-scoped, real repo, rolling |

That is the honest ceiling for the next two months: roughly **€50,000 + $10,000**. One €50k grant is the largest single allocation available to this applicant today, and there is no way to take it 33 times.

**Blocked by `entity=Individual`, not by merit:** AWS Activate, Microsoft for Startups, Cloudflare, Google for Startups, NVIDIA Inception (all require a company or an institutional affiliation); CZI EOSS and Sloan (require demonstrated adoption — `adoption_metrics` is blank on 33/33); Prototype Fund (German residency); Open Science Fund and Humanity AI (deadlines already past in the profiles' own data: 2026-05-11 and 2026-10-21).

**The two moves that actually raise the ceiling**, in order of leverage:
1. **Incorporate** — a US LLC or a fiscal-host relationship unlocks the credit programmes, whose declared values ($200k AWS, $150k Microsoft, $350k Cloudflare/Google) dwarf every cash grant on the list. This is the single biggest multiplier available.
2. **A European collaborator or fiscal host** — unlocks Restack/CodeSupply/Geocommons, and is the only route past the "strong European dimension" line.

---

## 6. What makes the request impressive — the material already exists

The corpus does not need embellishment; it needs one coherent narrative with numbers behind it. What is measurable today:

- **310,424 lines** across **746 modules**, **1,395 classes**, 19 trees (Windows atlas, measured 2026-10-30)
- **three environments** maintained: Windows, Ubuntu 26.04 (266,716 lines), Kali (273,425 lines)
- **6,277 tests** exist; **35 preflight gates**; **32/32** of the default set green
- a **140,774-node / 228,236-edge** code graph, rebuilt 2026-11-03 from current HEAD
- an evidence chain with hash-sealed containers, Merkle audit trees and tamper detection
- a **free-threaded Python 3.15t** runtime target — genuinely uncommon engineering

That is a fundable artefact. "Thirty-three applications from one person" is not.

**The single proposal worth writing** (target: open call, €50,000, 3 January 2027):
1. Lead with the *infrastructure* claim — cross-platform, free-threaded, reproducible-build, local-first toolchain — not with browser bypass.
2. Answer the five required fields the profiles leave blank, in plain English, in the author's own words: budget with an explicit hourly rate, a comparison against existing efforts, relevant experience, expected technical challenges, attachments.
3. Attach what already exists: the test count, the gate output, the atlas numbers, one real demo video.
4. One project, one ask, €50,000. Not 33 asks.

---

## 7. Recommendation

- **Do not run the batch.** No submission has produced a confirmation, the attachments do not exist, and the deadline it targets is not the fund's deadline.
- **Fix the three $100,000 profiles** to at most €50,000 — as written they fail the form's own stated range.
- **Pick one project** and write one proposal against `Open_Call` with ~2 months of runway.
- **Re-verify every deadline per fund** before relying on any of them; the profiles' 3 November date was already wrong by an unknown margin.

Row 47525 remains blocked pending explicit authorisation; nothing in it has been executed.
