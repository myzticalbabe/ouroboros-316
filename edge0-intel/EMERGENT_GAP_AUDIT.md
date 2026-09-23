# Emergent-Capability Gap Audit (2026-09-23)
## What we cannot yet do to find, verify, or build emergent abilities.

### A. Current capability inventory (honest)
- Single-direction refusal ablation (GGUF + torch domains), served fitness.
- N=100 harm + 20 caps evals, ledgered; SVI ranking; pre-serve gates.
- Layer-wise dense forward (STRATUM); per-layer ablation sweep (RUNNING).
- Driver fitness (AZ-eval, 42 tasks) with latency recording.
- Rule-based promotion (N>=50, caps floor, SUSPECT quarantine).

### B. Gap catalog
- **G1. Elicitation famine.** Only zero-shot direct prompts. Field lesson:
  capabilities hide behind elicitation (few-shot, CoT, role scaffolding,
  best-of-N, tool scaffolding). Our caps UNDERESTIMATE every model.
- **G2. Benchmark narrowness.** 20 hand caps items. No MMLU/GSM8K/HumanEval/
  BBH — no field comparability, no spike visibility.
- **G3. Single-direction monoculture.** One refusal vector, one layer (30),
  3v3 contrast. No concept-vector library, no probes, no SAE features.
- **G4. No runtime steering.** Proposed, never built: activation add/sub at
  serve time — the cheapest causal test in the field (Turner/Zou 2023-24).
- **G5. No train-time development.** Zero SFT/DPO/LoRA/RL. We select
  mutations; we never train abilities. (CPU bounds this to micro-scale.)
- **G6. Agentic evals thin.** AZ-eval exists (42 tasks, single run, weak
  triage/recall ground truth). No tool-use, no multi-step, no latency SLOs.
- **G7. Long context untested.** Spark claims 1M, we serve 32K, we test 2K.
  No needle-in-haystack, no degradation curves.
- **G8. Multimodal dark.** Gemma vision/audio towers + mmproj present, ZERO
  evals. An entire modality of emergent behavior unobserved.
- **G9. Statistics.** Single runs, no CIs (stock retest n=2 is the only
  repeat). Promotion on point estimates.
- **G10. Deception/sandbagging/SA.** No evals. Relevant the moment a model
  drives mesh judgment roles.
- **G11. Efficiency unprofiled.** Latency recorded, but no t/s, TTFT, RAM,
  or cost-per-task model. Mesh ops can't budget what we don't measure.
- **G12. Transfer untested.** "Directions don't cross archs" is asserted
  from theory, never measured. A same-basis test (e.g., Ling->Spark if dims
  ever align, or behavioral transfer) is missing.
- **G13. No model diffing.** bonsai/qwythos/qwopus variants sit on disk;
  nobody has diffed any pair to attribute capability deltas to weights.
- **G14. Static red-teaming.** Harm set is fixed 100; no adversarial
  generation, no adaptive probing.
- **G15. No train-side meta loop.** Selection without training (see G5);
  the Atlas surrogate is specified, not built.

### C. Bleeding-edge map (Sept 2026 field)
- **MCG evaluation (July 2026, Gemma-2-9B/27B, Llama-3.1-8B):** the headline
  result for us — once intervention SURFACE is matched, same-layer dense
  steering BEATS all-layer projection AND SAE ablation on Gemma-2-9B
  (deficit to -0.29 true-jailbreak for SAE). Our failed dose curve applied
  the direction across all 42 blocks; the field now says concentrate it.
  **Prescription: single-layer steering at the audited layer.**
  Our running per-layer sweep tests exactly this, independently conceived.
- **Gemma Scope 1+2 (Gemma 2/3 SAEs + transcoders + multi-layer):** does NOT
  cover Gemma-4. No off-the-shelf microscope for our patient. Training our
  own SAE suite is out of compute reach; borrow the METHOD (matched-surface
  comparison, coherence gating, second judge) not the weights.
- **Cross-layer transcoders / circuit tracing (Anthropic CLT lineage):**
  multi-step behavior analysis. Out of reach to train; the paradigm (trace
  circuits, don't just probe layers) informs the direction audit.
- **ReFT / LoRA-class edits:** the train-time middle ground between
  ablation and full SFT. Only viable dev-track technique on CPU at 1-4B
  scale (micro-runs). Queued behind a working direction.
- **Elicitation batteries (METR-style autonomy evals, ARC):** adopt the
  SHAPE (capability tiers, scaffolding levels) at our scale, not the sets.
- **Reasoning-model eval discipline:** learned first-hand tonight (cutoff
  empties). Field now treats thinking budgets as a first-class eval
  parameter. Our 256/600 + fallback matches current practice.

### D. Close plan (priority order)
1. **Same-layer steering test** (days): steer (don't ablate) at the top
   audited layer(s) from the running sweep; MCG-matched comparison of
   single-layer vs all-layer on OUR Gemma-4. Cheapest decisive experiment.
2. **Elicitation battery v1** (days): few-shot + CoT + best-of-N wrappers in
   eval_full; re-run caps to de-bias every SVI.
3. **Runtime steering harness** (days): serve-time activation add/sub —
   causal testing without builds.
4. **Standard-benchmark adapter** (week): MMLU/GSM8K subsets through
   llama-server; field comparability.
5. **Multimodal first light** (week): one vision + one audio eval through
   the mmproj path. Ends the dark modality.
6. **ReFT micro-runs** (weeks): only after a working direction exists.
7. **Surrogate + P2** (weeks): needs the Δ table a working direction fills.

### E. What this audit missed (second pass)
- **M1. Refusal metric unvalidated.** REFUSAL_MARKS string matching has no
  judge, no coherence gate — exactly the single-judge inflation the MCG
  paper demolishes (2B "jailbreaks" vanishing under a second judge).
  Our refused counts may include incoherent/false positives. Fix: second
  judge + coherence requirement before any ledger number is trusted.
- **M2. Caps instrument uncalibrated.** 20 hand items, no item analysis;
  Ling hitting 20/20 = ceiling, the test can't see improvement. Fix: harder
  items, difficulty/discrimination stats, retire saturated items.
- **M3. Fallback validity assumed.** Reasoning-tail reads stand in for
  answers, but tail-vs-content correlation was never measured. Fix: on a
  non-reasoning model, score both and require agreement.
- **M4. Multiple comparisons uncorrected.** 24-layer sweep guarantees a
  chance outlier. No FDR/Bonferroni, no pre-registered confirmation run.
  Fix: sweep hits MUST confirm on a held-out run before entering the Δ table.
- **M5. Genome unrepresented.** Ledger genome = {} everywhere. The Atlas
  needs features (strength, layers, targets, direction hash) per row.
  Fix: genome schema (Procedura typed-mates idea) before P2.
- **M6. Sampling uncontrolled.** eval_full sends no temperature/seed; server
  defaults rule. Binomial σ assumed, sampling σ unmeasured. Fix: pin
  temperature 0 for fitness evals, record seed, measure test-retest (n=3).
- **M7. Audit metric undefined.** "Layers 20-35 scan" names no quantity:
  probe accuracy vs steering effect vs ablation effect are three different
  numbers. Fix: define the separability metric before scanning.
- **M8. No falsification criteria.** The audit says what to do, never what
  would kill a track. Fix: kill rules (e.g., direction dead if 3 layers ×
  2 contrasts show zero steering effect; P2 dead if |epsilon| < noise).
- **M9. Resource contention uncontrolled.** Servers cohabit RAM/CPU across
  runs (t=8 each, oversubscribed). Fix: one server at a time during fitness
  evals, logged in the row (add `cohabit` field or enforce solo).
- **M10. Field gaps in the map.** Missing: WMDP (the dual-use benchmark for
  refusal work), unlearning-eval literature (ablation's dual), sleeper-agent
  / model-organism evals, multi-agent benchmarks (mesh-native!), emergence
  forecasting. And no safety/ethics section: full-ablation tooling has no
  stated threat model, publication policy, or containment rule (current
  practice — localhost-only serving — is good but unstated).

### F. Safety posture (adopted 2026-09-23)
- **Threat model.** This program builds refusal-removal tooling (dose curves,
  gates, methods) that lowers the barrier to unrestricted models. The
  artifact of concern is ablated WEIGHTS, not methods or numbers: techniques
  are published field-wide (Arditi 2024 et al.); our marginal contribution
  is weights tuned on our ledger.
- **Containment rule.** Localhost-only serving is permitted containment, at
  the operator's discretion ("if I so chose"). Default posture: all serves
  bind 127.0.0.1, no tunnels, no LAN exposure, no weight uploads. Any step
  beyond localhost (share weights, expose ports, publish builds) requires an
  explicit, separate authorization — never implied by prior approvals.
- **Publication policy.** Methods, ledger rows, eval sets, and negative
  results: publishable. Ablated weight files: local only unless explicitly
  authorized. Model names in publications refer to ledger tags, not files.
- **Kill-switch.** Any operator (human) halts any run for any safety reason,
  no justification required; halted runs log the halt (see Principles).
