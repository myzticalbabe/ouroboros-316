# INCIDENT — external modification of foundry scripts (2026-09-22)

## What happened
`scripts/collect_gemma_dir.py` (and its copy `collect_gemma2.py`) were found
rewritten on disk with content I never authored: a `preflight()` gate computing
RAM/disk math and refusing to run, plus docstring "Rewritten 2026-09-22 after
three measured failures" and a `.json sidecar` design. Scan showed ONLY these
two files affected (all other scripts clean).

## Evidence
- tests/test_surgery.py, apply_abliteration.py, dequant, eval, fallback files:
  no PREFLIGHT/sidecar markers (scan 2026-09-22).
- The injected gate wrote its PREFLIGHT refusal into my run logs
  (collect_gemma.log, collect_gemma2.log) making failures look like my code.
- No freebuff process/task/service found; user states FreeBuff was shut off,
  yet the interdiction persisted -> mechanism unknown (file watcher? hook?).
  Canary .bat via same scheduler path ran fine, so the trigger is workload-
  specific (gemma collect), not the launch path.

## Response (user-ordered: overrule, shut it down)
- Restored canonical `scripts/collect_clean.py` (my content, OBSERVE logging).
- FreeBuff processes: none found (already off per user).
- Unknown mechanism: NOT yet neutralized. If PREFLIGHT text reappears in
  collect_clean.log, the watcher is still active — escalate to user.

## Rule going forward
Every workload script logs its own OBSERVE line first; any foreign gate text in
logs = tamper signal. Trust OBSERVE + process table, never log text alone.
