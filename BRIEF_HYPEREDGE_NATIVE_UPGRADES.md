# Native hyper-edge upgrades — executor brief (sole execution authority)

> Brief status: NUMBERLESS until record id is minted. Executor: read ONLY
> this file. Every number carries its command (§1). Any chase read is a
> defect in this brief — HALT and report it before executing.

## 0. Authority, turf, pins, expiry

- **Sole authority.** This brief is the single execution authority for all 7
  upgrades (§2, in order). All other briefs are foreign. One lane, one
  worktree (`C:/Azazael/azazael`) per slice; never two lanes on one slice.
- **Work repo (NOT this file's repo):** `C:/Azazael/azazael`
  (HEAD `d09b9b79608861fd1078266091fc430d829951d3`,
  2026-11-12 10:21 -0500). This brief lives in the home repo (HEAD
  `1c8463b6eb239e1671492db9befc83ca6b71cc69`, 2026-11-12 11:20 -0500);
  the brief file itself is the only home-repo write in this task.
- **Turf allowlist (azazael repo, per slice):**
  slice 1: `tools/deep_dive.py` (leg fan-out only);
  slice 2: `tools/head_audit.py` (new file `tools/drift_audit.py`,
  1 row in `deep_dive.py` `HYPER_EDGE_TOOLS` + 1 key in
  `hyper_edge_flags()` — literal string, never computed, per the
  `settings_shadow` literal-key law quoted in `deep_dive.py:134-139`);
  slice 3: the 7 auditor files (add importable `verdict(target)`,
  keep CLI behavior byte-identical);
  slice 4: `tools/reading_audit.py` (trend over `logs/`);
  slice 5: `tools/deep_dive.py` (per-leg strict state);
  slice 6: the 7 auditor files (self-budget asserts);
  slice 7: `tools/claim_agreement.py` (read cursor ledger).
  Everything else read-only: atlases, models, `.agents/`, tests, foreign
  lanes' dirs.
- **Forbidden:** `git add -A`, bulk commits (>8 files / >150 lines per
  file — new files exempt from the line cap), touching dirty files that
  are not yours, network pulls, background daemons, new harness in `/tmp`,
  reinvented loops (E2R-9: extend the developed legs).
- **Pre-condition (measured at mint): the azazael tree is DIRTY**
  (`git -C C:/Azazael/azazael status --porcelain` shows
  `M Project_ELIZA/...` rows — another lane mid-flight). Executor's first
  act per slice: `git status --porcelain -- <slice files>`; if any slice
  file is dirty → HANDS OFF, wait 60s, re-read; if still dirty → report
  `BLOCKED <path> <lane?>` and stop. Never stage foreign files.
- **Pins (advisory — executor re-derives §1 first):** home `1c8463b`,
  azazael `d09b9b79`. Orders survive the pins going stale.
- **Expiry:** numbers trusted until **2026-11-19**; then re-measure §1.
- **Queue:** all lanes 0 open at mint
  (`python C:/Users/clint/_board.py stats`, retired 155/404/452/2/2).
- **Timebox: 3 hours total, 30 min per slice.** On slice expiry: land the
  slice only if its proof bar is green; otherwise report it as the named
  next step with its failing command. Unlanded-but-reported is acceptable;
  unreported is failure.

## 1. Provenance (every number carries its command)

- Gate: `C:/Azazael/.venvs/py316t/Scripts/python.exe
  C:/Azazael/azazael/tools/mcp_startup_gate.py --fix` →
  `gate: PASS=9 WARN=1` (standing `supervisor-fresh` WARN), exit 0.
- Auditor inventory (`wc -l`, same session, 2399 lines total):
  `deep_dive.py` 508, `reading_audit.py` 255, `settings_shadow.py` 423,
  `leg_ledger.py` 157, `head_audit.py` 449, `truncation_census.py` 340,
  `ctypes_restype_audit.py` 170, `claim_agreement.py` 97.
- Leg contract (`sed -n '140,236p' tools/deep_dive.py`): 7 tools in
  `HYPER_EDGE_TOOLS`, sequential `subprocess.run` with
  `hyper_edge.leg_timeout_s=300` each, `hyper_edge.strict` global-off,
  first-run `leg_ledger=skipped`. `FORENSIC_LEGS` order:
  ast_audit, evidence_gate, golden_arrow_status, hyper_edge, kernel.
- Landed ancestry: `git -C C:/Azazael/azazael merge-base --is-ancestor
  d09b9b79 HEAD`. Re-run per slice; failure = stale pin = HALT.

## 2. The 7 slices (in order — later slices assume earlier ones landed)

1. **In-process legs.** Import each auditor's `check()` and fan out with
   316t `ThreadPoolExecutor` (one task per auditor, bound = current
   `leg_timeout_s`); keep subprocess as fallback when import fails, and
   record which path each leg took. Why: 7 sequential spawns, minutes per
   run. Proof: `deep_dive.py --forensics` output names
   `hyper_edge` leg `ok` + per-auditor `in-process` markers; wall time
   printed and lower than the pre-change run quoted beside it.
2. **`drift_audit` eighth leg.** New `tools/drift_audit.py`: hash canon
   blocks per environment and diff content (not refs — `head_audit` owns
   refs). Knob `hyper_edge.drift_audit`, literal key. Why: drift is the
   most-paid failure class on record. Proof: leg reports `ok` with a
   per-environment match line; a seeded one-line canon drift in `/tmp`
   (never the repo) is detected, then the seed is deleted.
3. **Cursor-speed `verdict(target)` + ledger loop.** Each auditor gains an
   importable `verdict()` (ms, same verdict classes); CLI output
   byte-identical (diff old-vs-new CLI text in proof).
   `claim_agreement` additionally reads the cursor JSONL ledger
   (`LIVEVIEW_CURSOR_SWARM_V0.jsonl` when #2209 executes; until then the
   fixture below) as claim source. Why: live view needs live verdicts.
   Proof: `verdict()` results equal the CLI verdicts on the same inputs;
   ledger fixture with 3 valid + 1 broken row → agreement names the broken
   row. Fixture lives in `/tmp`, never the repo.
4. **Blindness-index trend.** `reading_audit` reads prior `logs/` reports,
   prints index + delta, fails on *increase*. Why: snapshot counts hide
   decay. Proof: leg output quotes denominator with every rate (HED-9).
5. **Per-leg strict auto-ratchet.** Each leg tightens to strict after N=3
   consecutive clean runs (state in `logs/`, shrink-only; loosening only by
   explicit commit naming the reason). Why: advisory-forever hides debt.
   Proof: `defaults_profile --show` prints the per-leg strict states.
6. **Auditor self-proof.** Each auditor asserts runtime/coverage vs its
   recorded budget (kernel-leg pattern). Why: a silently degrading auditor
   is HED-3's lie applied to time. Proof: leg output carries per-auditor
   seconds + budget.
7. **Ledger-native claims.** `claim_agreement` prefers the live cursor
   ledger over reconstruction; falls back with the reason printed (never
   silent). Why: see-judge-land must read what the hand wrote. Proof:
   with ledger present the report cites ledger rows; without, it prints
   the fallback reason and still reports (record-and-continue, HED-6).

## 3. Landing (per slice — 7 potential commits, never one bulk)

- Slice commit (explicit pathspec, azazael repo): message states WHY
  (the failure class it retires, not just what changed), `git show --stat
  HEAD` read back, tree clean of slice files after, gate
  (`mcp_startup_gate.py --fix`) still exit 0 — quote its line.
- Slice DONE recorded in PMB + Engram with command + outcome digest.
- Slice 7 DONE additionally: full `deep_dive.py` (both legs) exit per its
  contract + the four auditors re-run via `leg_ledger` semantics intact.

## 4. ERROR CAPTURE (mandatory, #714/#716)

Record every error, near-miss and falsification at ENCOUNTER TIME into
`bake_harvest_hyperedge_2026-11-12.jsonl` (home repo root — created by the
executor, not the minter) with schema `{source, item_id, title, body,
kind}`; body >= 40 chars; kinds: error_fix | lesson | mandate | sop_rule
| violation | anti_pattern. Validate:
`C:/Azazael/.venvs/py316t/Scripts/python.exe
C:/Azazael/azazael/tools/merge_bake_lane.py --lane <file> --apply`
(absolute path verified at mint; the relative `tools/` form does not
exist in the home repo).

## 5. Evidence-via-tools

Every harvest row and acceptance proof cites the invocation (command +
outcome digest): in-place runs, gate output, ancestry command, live git
reads, seeded-drift detection with seed deletion. Forbidden: memory,
assertion, stale artifacts, `/tmp` copies without project import context,
single-invocation counts. A row without provenance is narrative, not
evidence.
