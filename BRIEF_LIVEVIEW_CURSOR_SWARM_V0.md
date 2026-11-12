# Live-view cursor swarm v0 — mint brief (freebuff lane, sole execution authority)

> Brief status: NUMBERLESS until record id is minted (rule 1). Executor: read
> ONLY this file. All inputs are embedded; any chase read is a defect in this
> brief, report it before executing.

## 0. Authority, turf, pin, expiry

- **Sole authority.** This brief is the single execution authority for the
  live-view v0 work. All other briefs are foreign. One lane executes this
  brief; no two lanes share this worktree for it.
- **Turf allowlist (only these paths may be written):**
  `LIVEVIEW_CURSOR_SWARM_V0.html` (new, the view),
  `LIVEVIEW_CURSOR_SWARM_V0.jsonl` (new, the frame/ledger log).
  Everything else is read-only, especially `~/yggdrasil_forest/*.json`
  (atlases are NEVER edited), foreign lanes, tests, `.agents/mcp.json`,
  models, and `BRICK_MELLIFLUOUSML_AIO.md`.
- **Forbidden:** editing any atlas/manifest, `git add -A`, bulk commits,
  touching model dirs, network pulls, background daemons.
- **HEAD pin (advisory — executor re-derives first):**
  `288ba27cca5ba6e3556b99c226eac53c0120f4f9`, 2026-11-12 11:00 -0500,
  tree clean (`git status --porcelain` empty, verified same session).
  Valid only after executor's own `git log --oneline -5` +
  `git status --porcelain`. Orders survive the pin going stale.
- **Expiry:** numbers trusted until **2026-11-19**. After that, re-measure
  §§1–2 before executing.
- **Queue:** board all lanes 0 open at mint
  (`python C:/Users/clint/_board.py stats` — opencode/kilo/freebuff/crush/agy
  all `available: 0, open: 0`, retired 155/404/452/2/2).

## 1. Provenance (every number carries its command)

- Gate: `C:/Azazael/.venvs/py316t/Scripts/python.exe
  C:/Azazael/azazael/tools/mcp_startup_gate.py --fix` →
  `gate: PASS=9 WARN=1` (sole WARN: standing `supervisor-fresh`), exit 0,
  this session 2026-11-12.
- Disk: `38.84GB` free after brick steps 1–5
  (`powershell Get-PSDrive C`, +32.4GB from 6.44GB baseline same session).
- Substrate (read-only inputs, `ls -la ~/yggdrasil_forest/` same session,
  total 5.3MB):
  `domain_atlas_sentinel.json` 16414 B, `domain_atlas_hives.json` 153711 B,
  `forest_manifest.json` 5405 B (+ 9 further atlases: cain 21399, dev 1482,
  edge0 40330, eve_rani 17659, gosp 3200, ml 26135, oxman 3310, shards 4974,
  wraith 3316 — all bytes).
- Renderer gap (why v0 exists): `render_tree.py` and any dashboard are absent
  from this repo and `C:/Azazael/azazael/tools/` (glob + `ls|grep` + bounded
  `find`, same session). Only post-hoc forest MP4s exist. No live surface.
- Landed ancestry (nothing below is asserted without this check):
  `git merge-base --is-ancestor 288ba27 HEAD` (BRICK brief, landed),
  `git merge-base --is-ancestor cc0e5d0 HEAD` (housekeeping, landed).
  Re-run both before executing; a failure means the pin is stale — HALT.

## 2. What v0 builds (smallest version that meets the goal)

A single static HTML page + JSONL ledger that renders the sentinel and hives
atlases with **simulated** cursor glyphs (v0 moves scripted cursors; live
wiring is v1, explicitly out of scope):

- Each glyph: position = tree + node, color = verdict
  (green landed / amber held / red rolled back), label = claim text.
- Frame index with per-frame SHA-256 chain over
  `{frame, cursor_id, tree, node, verdict, claim, prev_hash}` appended to the
  JSONL log — replayable cursor-by-cursor.
- Unrendered cursor = not-happened: the page refuses glyph-less ledger rows
  (renders them in a quarantine strip, never on the tree).
- Scope is TWO atlases only (sentinel + hives). The other nine are v1.

## 3. Steps (bounded within the allowlist, in order)

1. Re-derive §1 (log, status, merge-base ×2, one atlas byte-count spot check).
   Any mismatch → HALT and report, do not proceed on memory.
2. Write `LIVEVIEW_CURSOR_SWARM_V0.html` (new file): reads the two atlases
   via file input / pasted JSON (no fetch server, no daemon), draws trees as
   nested lists + SVG edges, animates 5 scripted cursors with verdict colors,
   quarantine strip for glyph-less rows.
3. Write `LIVEVIEW_CURSOR_SWARM_V0.jsonl` (new file): ≥20 ledger rows with
   valid hash chain (`prev_hash` of row N = sha256 of row N−1 canonical JSON).
4. In-place proof: open the page (double-click; no server), screenshot the
   verdict colors, run the chain verifier (step 5) — paste outputs into DONE.
5. Chain verifier (one command, no new files — run inline):
   `C:/Azazael/.venvs/py316t/Scripts/python.exe -c
   "import json,hashlib;[verify each line's prev_hash]"` — must print
   `CHAIN OK N=20+` (adapt N to rows written).

## 4. Acceptance (commands, not assertions)

- DONE = `LIVEVIEW_CURSOR_SWARM_V0.html` + `.jsonl` landed in ONE commit
  (explicit pathspec, ≤2 files) with: screenshot showing green/amber/red
  glyphs + quarantine strip, `CHAIN OK` line, `git show --stat HEAD` read
  back, tree clean after, DONE recorded in PMB + Engram.
- Remainder (v1 live wiring to the worm swarm) is NOT done here — reported
  as the named next step, not attempted.

## 5. ERROR CAPTURE (mandatory, #714/#716)

Record every error, near-miss and falsification at ENCOUNTER TIME into
`bake_harvest_liveview_2026-11-12.jsonl` with schema
`{source, item_id, title, body, kind}`; body >= 40 chars; kinds: error_fix |
lesson | mandate | sop_rule | violation | anti_pattern. Do not defer to
session end — reconstruction loses detail and over-weights what is still
salient. Validate: `tools/merge_bake_lane.py --lane <file> --apply`
(substitute the repo's merge tool if the path differs; record the
substitution as the first harvest row — never silently swap tooling).

## 6. Evidence-via-tools (no harvest row or proof without invocation)

Every harvest row and acceptance proof cites the tool invocation
(command + outcome digest): in-place file run, page open + screenshot,
merge tool output, ancestry command, live git reads. Forbidden: memory,
assertion, stale artifacts, `/tmp` copies without project context,
single-invocation counts. A row without provenance is narrative, not evidence.
