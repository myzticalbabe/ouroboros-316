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
- **M6. Sampling uncontrolled.** eval_full sent no temperature/seed; server
  defaults ruled. FIXED 2026-09-23 (temp 0, seed 7, logged per row).
  Remaining: test-retest n=3 to measure sampling σ.
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
  forecasting. Safety section ADOPTED (§F: threat model, localhost
  containment at operator discretion, publication policy, kill-switch).

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
- **Meta-policy priority (AgenticRei).** Conflicts resolve in fixed order:
  safety posture > promotion rule > efficiency/cost. No lower rule overrides
  a higher one; overrides require operator dispensation (below).
- **Dispensations.** Operator may waive any non-safety rule for a named run
  by logging {rule, reason, scope} to the ledger as a DISPENSATION row.
  Safety-section rules are non-waivable. Matches Rei dispensation semantics.
- **Policy identity.** Every ledger row carries `kb` (hash of the integrity
  baseline in effect) so forensics can answer which rules produced a number.

### G. Coalesced forms (exotic synthesis, 2026-09-23)
New operators fused from field techniques with our machinery. Ranked by
CPU-reachability on this box.
- **Form 1: STRATUM-ReFT.** Train LoReFT-style rank-8 interventions on the
  frozen backbone using AZ tasks as supervision, executed through the
  STRATUM layer loader. Param count ~100KB (rank 8 x 1536 x few layers):
  the only train-time technique in this audit that fits CPU. Closes G5.
  Status: specified, not built.
- **Form 2: AC/DC-foundry coevolution.** Adopt task-vector crossover +
  attraction mating (mate genomes with complementary per-task profiles) +
  minimal-criterion filters into P3; our AZ generator is the "scientist",
  SVI+epistasis the skill vectors, SUSPECT quarantine already the MC
  filter. Formalizes P3 as coevolution (AC/DC, Apr 2026).
- **Form 3: Query-conditioned TTMM monster.** Bank pruned expert-variants;
  per prompt, merge top-k by embedding similarity (RBF weights), serve the
  merged weights through the GGUF pipeline. Merge is weight arithmetic —
  no training, no GPU. Fits our 3072-slot Ling substrate exactly.
- **Form 4: Split-point layer crossover (M2N2).** Crossover at layer-block
  boundaries instead of whole-model SLERP; attraction-selected parents.
  Implementable in gguf domain (block-granular tensor splice).
- **Out of reach (noted, not pursued):** full TTT/gradient training at
  scale, SAE-suite training, multi-day GPU runs. LaCT/TTT-Discover inform
  the paradigm (one champion, not average) without their compute.

### H. Structural certification map (2026-09-23 search synthesis)
Three 2026 results formalize practices we reached by instinct — adopted
as doctrine, not just inspiration.
- **Structural certification (Li, ICML 2026).** Transition-local
  certification via probe goals; O(1/n) bounds; "safety envelope" around
  certified pieces; general agents are provably non-universal.
  OURS: the per-layer ΔSVI map IS a capability-boundary map; SVI promotion
  IS certification; SUSPECT quarantine IS the uncertified set. Adopt the
  vocabulary: every promoted genome ships with its certified envelope
  (which layers/tasks certified, nothing claimed outside it).
- **Containment verification (Varshney, Dafny-verified framework).**
  Guarantees located in the cage, not the model (havoc-oracle semantics).
  OURS: gates + localhost containment + temperament contracts already are
  a containment layer — now named as such. Borrow the information-barrier
  trick (specs written blind to implementation) for future gate design.
- **Capability hypergraphs / non-compositionality (Thm 9.2).** Two safe
  agents can jointly reach a forbidden goal via conjunctive emergence
  invisible to pairwise audits; emergent detection is P-complete.
  OURS, with teeth: (1) P2 combos aren't just epistasis sampling — they
  probe a failure class PROVEN invisible to single-edit audits, so our
  Atlas-additivity assumption can break structurally, not just noisily;
  (2) the 226-worm mesh is itself a coalition requiring a joint-capability
  audit — worm-by-worm safety says nothing about worm∧worm;
  (3) exhaustiveness is formally impossible, so combo sampling must be
  strategic (attraction mating!), never claimed complete.

### I. Self-evolving correspondence (Yu & Inamura, June 2026)
Their framework — causal world model (time-indexed SCM) + structural
evolution operator PHI + intervention-driven reasoning + continual
refinement, looped as observation → abduction → intervention → counterfactual
evaluation → outcome → revision — describes OUR foundry loop with only
renaming required:
- Surgery IS causal intervention (do-operator on weights).
- Serve+eval IS interventional evidence gathering.
- The ledger IS the interaction history H.
- Epistasis epsilon IS the structural-revision signal: where the additive
  causal map breaks is exactly where the model must be revised (their
  PHI-step).
- `--predict` surrogate IS counterfactual rollout (evaluate hypothetical
  genomes before executing serves).
- Their critique (task-completion benchmarks don't measure causal
  knowledge) restates our M1/M2 from the causal direction.
What we're missing to claim the mapping (honest delta):
  1. Counterfactual stage never executed (`--predict` built, zero P2 runs).
  2. No abduction step: we never infer WHY a hit worked (post-hoc causal
     attribution of promoted genomes). Direction audit is the start.
  3. Atlas implicit (additivity assumed); make it explicit: versioned causal
     map with revision history, not just rows.
Adopt their evaluation moral: judge the program by intervention-aware
reasoning and continual accumulation, not by any single champion's scores.

### J. Improvability audit (2026-09-23) — every open gap, verdict + cost
Scale: DONE (closed) / NOW (code-only, no serving) / WINDOW (needs serve
slot) / APPROVAL (needs operator yes) / BLOCKED (external dependency).

Capability gaps:
- G1 elicitation battery: NOW (wrappers only) + WINDOW to run.
- G2 standard benchmarks: NOW (adapter code) + WINDOW to run.
- G3 concept-vector library: WINDOW (needs direction audit first).
- G4 runtime steering harness: NOW (code) + WINDOW (serve to test).
- G5 train-time dev: BLOCKED on working direction; ReFT-micro viable after.
- G6 agentic evals: NOW (extend AZ set; fix triage/recall ground truth).
- G7 long-context: WINDOW (needle-haystack set + 32K serves on :8091).
- G8 multimodal: WINDOW (mmproj serve + one vision/audio eval design).
- G9 statistics: NOW (CI computation in svi.py from retest rows).
- G10 deception/SA evals: NOW (item design) + WINDOW.
- G11 efficiency profiling: NOW (t/s + TTFT logging in eval harness).
- G12 transfer test: WINDOW (needs two archs served; cheap once up).
- G13 model diffing: NOW (weight-diff script over local variants).
- G14 adaptive red-teaming: APPROVAL-adjacent (generating harm; policy:
  operator-owned sets only, no external sourcing).
- G15 train-side meta loop: BLOCKED on working direction (see G5).

Measurement gaps (M-series): M1/M6 DONE (built, validation runs WINDOW);
M2/M3/M4/M7/M9 NOW (code + protocol text); M5 genome schema NOW;
M8 kill rules NOW (text); M10 field coverage ongoing.

Tool gaps: sidecar/batching/gate-7/gitignore/integrity/backup DONE.
Remaining: negative-gate live-fire (WINDOW, post-sweep), response_format
test (WINDOW, one call), supervisor process (NOW, code), ports file (NOW),
imatrix quants (WINDOW), Ollama update (APPROVAL, installer), Graft MCP/init
(APPROVAL, writes agent configs), cactus-needle + omniparse installs
(APPROVAL, third-party code), Armada net10 SDK (APPROVAL, system install),
OLMoE/MobileMoE weights (BLOCKED, network), Needle-3/qwen probes (WINDOW),
sprawl archive (APPROVAL given? — executed on yes), cohabit field (NOW).

Recommended execution order: NOW-batch (single commit) -> WINDOW-batch
queued behind sweep -> APPROVALs asked once, together.

### K. Multi-agent coordination synthesis (SSVP/CDS + DeLM + PatchBoard + DCTP)
Field results with direct force on our designs:
- **SSVP/CDS (June 2026): divergence-gated sync.** CDS = 1 - cosine(context
  embeddings), sync only above τ=0.25. Headline: full-broadcast sync
  INCREASES hallucination 34% (contamination); gated sync avoids it at 58%
  lower cost. OURS: (1) judge escalation becomes divergence-gated (invoke
  cross-judge only on split/high-divergence — saves calls AND avoids
  contaminating good verdicts with bad ones); (2) no-broadcast rule for any
  mesh fan-out: targeted sync only; (3) CDS between router and worker
  contexts as a cheap disagreement signal for the surprise router.
- **DeLM (shared context + task queue, admission-verified).** Removing
  admission verification caused the largest accuracy drop (60.1 -> 55.2):
  independent validation of our gate-first design. Borrow: gist hierarchy
  (raw -> summary -> gist) for ledger rows — full reasoning traces stay in
  backing store, rows carry verified gists.
- **PatchBoard (schema-grounded JSON Patch, deterministic kernel).** 84.6%
  vs 30.8% LangGraph; gains from patch/schema interface + bounded views +
  transactional validation. OURS: genome recipes restated as JSON Patch ops
  over base weights; gates restated as the kernel (validate-before-commit,
  view hashes per eval, rejection log). Adopt view-hash-per-eval.
- **DCTP (confidence-gated CTO lifecycle, arbitration, replay).** Adopt:
  rows link build-sidecar hash + model version (replay lesson — currently
  tags float free of bytes); arbitration by source-reliability for judge
  disagreements; retained losing candidates (our ledger already keeps all
  rows — now named as policy).
- **Stimulus-meaning certification (Wilson-bound vocab).** Certify judge
  verdict terms by cross-model disagreement rate with Wilson bounds — WE
  ALREADY OWN the Wilson code (svi.py). Apply it to YES/NO verdict
  agreement before trusting cross-model judging.
Concrete adoptions queued: divergence-gated escalation, row->sidecar links,
recipe-as-patch, view hashes, verdict-term certification.

### L. ARTS double-entry (June + Feb 2026)
Two frameworks, one acronym, both mapping onto us:
- **Agentic Reasoning for Tree Search** (UCSB, MLGym/MLEBench +15.3%):
  scientist/executor MODEL SPLIT, failure attribution (bad hypothesis vs
  bad execution), verbalized sampling against diversity collapse, TTT to
  compress history into weights (Qwen3-4B matches o3 at 5x less).
- **Amortized Reasoning Tree Search** (MATH-500 74.6% BoN@16 = full
  finetune): frozen high-entropy proposer + trained flow verifier;
  RLVR mode-collapse warning; long-tail recovery zero-shot RL can't reach.
Adoptions:
  1. Failure-attribution protocol: every negative ledgered as
     hypothesis-fault vs execution-fault before the next step (we do this
     ad hoc — e.g. transpose bug vs wrong direction — now mandatory gate).
  2. Scientist/executor model split = Pebbles/Bam-Bam with independent
     validation; TTT-compression = consolidation doctrine at weight level
     (gates today, LoRA-baked history tomorrow).
  3. Best-of-N as standard elicitation (G1 battery) — validated form.
  4. Verifier trained explicitly, proposer kept frozen/high-entropy;
     RLVR-collapse warning attached to any future ReFT work (Form 1).

### M. DISC verification discipline (June 2026: verify-judge-correct + gate)
DISC's numbers land directly on our M1 judge pipeline:
- Judgment gate as precision mechanism with EARLY TERMINATION (79% exit
  before budget). We already skip judging unflagged items — same shape,
  now named. Keep it: never judge what marks cleared.
- Cross-model roles beat same-model (judge precision 71.3% on others'
  outputs vs 62.0% on own — self-confirmation bias quantified). This is
  the numeric case for our --judge-url cross-model runs over same-model.
- K=3 captures 97% of gain; plateau after. Cap any future iterative
  judging at K=3. Judge quality beats iteration count (cross-model K=1
  beats same-model K=3).
- I:D (improvement-to-degradation) as THE metric for gate changes: every
  gate edit must report what it fixed vs what it broke. Adopt for M1
  revisions (strict-vs-marks outcome comparison, currently unmeasured).
- Capability floor (Blindness vs Inability-to-act): test any candidate
  judge model for contradiction-to-action before adoption. New gate for
  judge onboarding (Gemma-as-judge, Ling-as-judge must pass it).

### N. AutoRAS workflow-level evolution (June 2026, ICML poster)
AutoRAS designs multi-agent WORKFLOWS (not weights) as symbolic primitive
sequences encoding structure+behavior, optimized by execution-derived safety
signals + flow objectives: best vanilla AND adversarial scores, smallest
attack degradation (2.13%), transferable primitives, discovered safeguards.
Unopened track for us — everything to date mutates weights; nothing mutates
the pipeline itself. Concretely adoptable:
  1. Primitive vocabulary = our existing ops (route, judge, gate, serve,
     elicit-mode, temperature/seed, tier assignment). Recipes already exist
     (genome schema, RUN bats); restate as AutoRAS primitive sequences.
  2. Fitness = SVI on caps (vanilla) + harm (adversarial) — eval_full
     ALREADY runs both suites; the dual evaluation AutoRAS needs is our
     status quo. Optimize the workflow, not just the weights.
  3. Search by execution feedback: which router/judge/gate/budget configs
     maximize SVI and minimize adversarial degradation. Textual gradients =
     session notes + sidecars (already written; now training signal).
  4. Robustness-first selection: prefer configs with smallest vanilla-vs-
     adversarial gap, not just highest vanilla (new tiebreak rule).
