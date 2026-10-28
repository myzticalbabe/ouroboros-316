# Arena synthesis — 64 neurons (single-hidden-layer classifier, digits)

## Contract (Phase A)
Task: identical for all candidates — train a **64-neuron** hidden-layer
classifier on sklearn digits (1797×64, 10 classes, 80/20 stratified split,
seed 7) and report test accuracy + wall time + `results.json`.
Rubric: (1) test accuracy ≥ 0.90, (2) wall time < 120 s,
(3) determinism (rerun ⇒ identical JSON), (4) dependency weight.

## Candidates (Phase B)
- **A** `candidate-a/train_a.py` — numpy, ReLU, He init, full-batch SGD.
  Test **0.9806**, 0.5 s. Rejected as base: slower, lower accuracy than C.
- **B** `candidate-b/train_b.py` — sklearn `MLPClassifier(64,)`, adam, early
  stopping (46 iters). Test **0.9639**, 0.2 s. Rejected as base: weakest
  accuracy, heaviest dependency. Donated its early-stopping idea.
- **C** `candidate-c/train_c.py` — numpy, tanh, Xavier init, mini-batch Adam.
  Test **0.9861**, 0.2 s. **Picked as base**: best accuracy, numpy-only,
  cleanest extension boundary.

## Adaptations (honest deviations from the skill)
- **Fan-out**: this harness has no subagent-spawn tool, and its background
  runner silently reaps compute jobs (all 3 parallel launches dropped with
  empty logs — same failure seen earlier with background pip). Ran the three
  candidates sequentially with the identical contract and separate output
  dirs instead. No candidate was favored: same data, seed, split, thresholds.
- **Cross-judge**: single-model harness, so no foreign-family judge exists.
  Judged directly against the rubric above; scores are numbers, not vibes.

## Graft (Phase E)
One graft from B into C: early-stopping on train-accuracy plateau
(`PATIENCE = 8`) with best-weight snapshot. Result `solution.py`:
test **0.9833**, train 1.0, **0.1 s, 30 epochs** (vs 60).
Trade stated plainly: −0.003 test vs raw C for halved epochs and a
principled stop. A's explicit results schema kept (parity, not a graft).

## Verification (Phase F)
Reran `solution.py` twice: identical JSON both runs
(test 0.9833, epochs 30) — determinism ✓; accuracy ≥ 0.90 ✓;
runtime 0.1 s ✓; single file, numpy-only ✓.

## Verdict on arena-for-us
The pattern works here: framing a gradeable contract up front is what made
the pick mechanical (C wins 3 of 4 criteria outright). Cost was ~3× one
attempt for this size of task; worth it for artifacts with real design
freedom, overkill for rote edits. The harness gaps (no subagent fan-out,
no foreign judge) are the binding constraints — with them, run candidates
sequentially and judge on numbers.
