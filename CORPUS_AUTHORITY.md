# CORPUS AUTHORITY — one authoritative tree, and where the other one lives

**Declared 2026-10-30.** The BCC investigation corpus exists in two generations and
they disagree. This file is the single statement of which one is current. The gap
gate (`~/.agents/skills/verify_gaps.sh`) parses the table at the bottom of this file,
so the declaration and its enforcement cannot drift apart.

## The two trees

| tree | path | generation | documents | status |
|---|---|---|---|---|
| **current** | `C:/Users/clint/` (top level) | September 2026 — the ledger `INVESTIGATION_GAPS.html` is dated 2026-09-04 and carries 62 total / 52 open / 10 resolved | 206 | **AUTHORITATIVE** |
| archive | `C:/Users/clint/Desktop/FACEBOOK/` | 2026-08-04 — pre-dates the September ledger; contains none of 52/62/10 | 261 | HISTORICAL — never cite as current, never edit |

## Precedence rule

- **64 document names exist in both trees. The current copy wins, unconditionally.**
- **197 names exist only in the archive** (67 html, 128 txt, 2 md). They are historical artefacts, not current findings.
- **142 names exist only at the top level** — the September generation, with no August predecessor.
- The archive is kept because it is the source the 2026-08-04 video renders were made from. It is a museum, not a workspace.

## Verified archive-only documents (gate-parsed)

These are the documents the gap gate previously asserted September counts against, which
is why it could never pass. Each row is checked by the gate: the name must be **absent from
the current tree** and **present in the archive**. If one is ever promoted forward without
this table being updated, the gate fails.

| document | status | note |
|---|---|---|
| LEGAL_REFERRAL_MEMO.html | archive-only | Aug-4 referral memo; no September rewrite exists — in archive, 55417 bytes |
| EVIDENCE_LOCATIONS.html | archive-only | Aug-4 map of where evidence sits; superseded in practice by the September ledger's own annexes — in archive, 40428 bytes |
| MOLTBOOK_AGENT_SETUP.html | archive-only | Aug-4 agent-setup doc; also the only copy carrying '125 awards' — in archive, 43340 bytes |
| CC_CONTACTS_MASTER.html | archive-only | Aug-4 contact sheet; the old '46' assertion matched any digits and proved nothing — in archive, 31668 bytes |
| CCBHC_REGIME_CHANGE.html | archive-only | Aug-4 regime-change analysis; was a vacuous PASS because the file did not exist at root — in archive, 44601 bytes |
| IRS_WHISTLEBLOWER_FORM_211.html | archive-only | Aug-4 Form 211 draft; was a vacuous PASS for the same reason — in archive, 52076 bytes |

## Not in either tree

`investigation-document-construction.md` (the `.md` variant the gate used to assert on) is
in neither tree and not under `.agents/skills/`. It is treated as retired: the gate no
longer asserts anything about it.

## What this declaration does NOT decide

Whether any archive-only document should be **promoted** into the current tree, and if so
with which figures. Promotion is an editorial act: copy the document forward, update its
counts against the September ledger, then add its row here as `current` and the gate will
require it at the top level instead of in the archive.

_Counts measured 2026-10-30 by directory listing; re-derive rather than quote._
