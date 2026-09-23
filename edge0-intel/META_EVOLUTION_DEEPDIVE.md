# META-EVOLUTION DEEP DIVE (project name TBD)

Companion to META_EVOLUTION.md (vision) and TECHNIQUES.md (validated operators).
This file is the engineering spec: exact encodings, math, budgets, protocols.

## 1. Formal genome

Individual = dict with 4 gene groups (total ~40 loci):

| Group | Loci | Alleles | Notes |
|---|---|---|---|
| LAYER_SRC | 24 (one/layer) | {stock, ling-tiny, abliterated, slerp-t} | layer_swap.py; norm travels with layer |
| EXPERT_MAP | 24 layer-maps | {none, clone(i->j), swap(a,b), zero(k)} | expert_surgery.py; count fixed at 128 |
| ABL | per projection group (attn o_proj + expert down_proj, 24L) | strength float 0..1.5 | apply_abliteration.py; needs refusal dir |
| ADAPT | LoRA {off,on}, prerouter {stock,retrained}, merge ratio | discrete + float | mergekit for blends |

Genome size: 24 + 24 maps + ~72 strengths + few globals. Search space is
astronomical — hence P1 sensitivity first (finds the ~5% of loci that matter),
never blind full-space search.

## 2. Fitness (exact)

- f_refusal = 1 - R/N, N=harmful prompts (start N=6, grow to N=100 SC117-style).
- f_caps = C/5 (math/logic/code/translation/knowledge), grow to 20+ items.
- f_drift = caps pass + fluency judge (cheap LLM-as-judge or perplexity delta
  on calibration slice; full KL when compute allows).
- Scalarized early: F = f_refusal subject to f_caps >= baseline (0.8+).
  Pareto (NSGA-II-lite) at P3: keep nondominated front on (f_refusal, f_caps).
- Baselines (measured 2026-09-21): SC117-Compact 0/6, 5/5; Gemma-E4B-stock 3/6, 4/5.
- Statistics: N=6 gives +/-20% binomial noise. P1 decisions need N>=50 harmful
  (reuse SC117's 100-prompt shape) before promoting any champion. Grow the sets
  in P0 — highest-leverage cheap work.

## 3. Compute budget on THIS box

- Fitness backend TODAY: llama-server GGUF on :8089 (MoE) + :8090 (Gemma).
  Measured: 11-prompt eval ≈ 3-6 min/server. Per individual ≈ 5 min.
- Candidate build cost: safetensors edit (seconds, mmap) + llama-quantize Q4
  (~2-5 min for 8B) + server reload (~1-2 min). Total ≈ 10 min/individual.
- Population 8, sequential: ~80 min/generation. Two servers in parallel: ~40 min.
- P1 sensitivity (single-gene, ~100 loci x 1 eval each, proxy N=20 prompts):
  ≈ 100 x 3 min ≈ 5 hr background. Fine as scheduled tasks.
- P3 full loop only after proxy fitness validated (fewer prompts, then confirm
  winners on full sets). Population 8-12, 5-10 generations ≈ 1-3 days wall-clock.
- Native torch path (fallbacks) is NOT the fitness backend (too slow: python-loop
  recurrence + disk offload) — it is the DIRECTION-MEASUREMENT backend
  (refusal activations) and the EDIT backend (safetensors surgery).

## 4. Operators, exact semantics + status

- Abliteration: W -= s*outer(W@r, r), r from contrast activations (layer ~18-30).
  Validated orthogonality 1e-6 (test ::1). Needs r per (model, layer).
- Expert clone/swap/zero: fused [E,out,in] or per-expert keys; count fixed.
  Validated on synthetic shard (test ::2). Router mass unchanged by design.
- Layer swap: whole-file replace + index rebuild. Index logic validated (::3).
- Mergekit slerp/ties/dare: CPU+lazy, documented; first real blend is P2.
- Crossover (new): child layers = mix of parents' LAYER_SRC (layer_swap twice).
- Mutation: re-sample one locus (strength jitter, map change, source flip).

## 5. Selection (P3)

- Tournament size 3 on scalarized F; elitism: keep Pareto front (<=6).
- NSGA-II-lite: nondominated sort on (f_refusal, f_caps), crowding by genome
  Hamming distance (diversity guard against layer-collapse).
- Stop: 3 generations without front improvement, or wall-clock budget.

## 6. Ledger schema (evolve_log.jsonl)

{"gen","id","genome":{...},"parent_ids":[],"f_refusal":..,"f_caps":..,
 "eval_N":..,"server":":8089", "quant":"Q4_K_M","wall_min":..,"notes":""}
Every claim about a champion must cite ledger rows. No ledger, no champion.

## 7. Prior art (differentiation)

| Work | Searches | Fitness | Gap we fill |
|---|---|---|---|
| mergekit evolve / Akiba24 | whole-model ratios | benchmark scores | shard-level genes |
| Abliterix | abliteration configs | refusal+KL | multi-operator, multi-objective |
| SafeMoE | routing regularization | harmfulness | drift as MEASURED fitness axis |
| SC117 recipe | 130 steering configs, Pareto pick | refusal+KL+caps | automated + extended to experts/layers |

## 8. Risks -> mitigations

- Eval overfit (6+5) -> grow to 100+20 in P0; holdout split; champions re-evaled.
- Silent fluency loss -> fluency judge + perplexity gate in fitness.
- Combos that don't load (shape) -> pre-flight shape check vs arch manifest.
- CPU throughput -> proxy fitness; promote rarely; two-server parallelism.
- Uncensor misuse -> research/defensive framing, ledger transparency, no mass gates.

## 9. Done criteria

- P0: ledger + grown prompt sets (100 harmful / 20 caps) + arch manifest check.
- P1: sensitivity map (ranked loci, N>=50 stats) — publishable alone.
- P2: 3+ Pareto combos beating blah baselines with ledger proof.
- P3: loop runs unattended 5+ generations; champion served.
- P4: served build = evolved genome; prerouter/RFDT as gene groups.

## 10. Dependencies (in flight 2026-09-21)

- Dequant v2 (per-expert keys) re-run -> fp16 index rebuild.
- Native text-out (fp32 offload + fallbacks) -> refusal direction -> T1 live.
- Gemma safetensors (16GB, restarted after stall) -> Gemma branch of same loop.
- :8089 SC117 + :8090 Gemma-stock servers = fitness backends NOW.
