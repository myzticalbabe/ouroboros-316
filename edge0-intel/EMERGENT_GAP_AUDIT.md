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
