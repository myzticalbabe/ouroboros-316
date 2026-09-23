# META-EVOLUTION NETWORK over tensor shards — potential + roadmap

Thesis: treat every shard group (layer attentions, expert blocks, norms, head,
adapters) as genes; mutate with our surgery operators; score functional fitness
(refusal rate + caps + KL vs parent); evolve. Shard granularity + MoE-aware
operators + functional fitness = new combination.

## Why it's new (vs prior art)
- mergekit `evolve` (Akiba et al. 2024): evolves MERGE RATIOS of whole models.
  Ours evolves WHICH tensors live where (expert/layer/adapter level).
- NSGA-II / EvolutionEngine: generic Pareto optimizers. Ours contributes the
  genome encoding (shard groups) + MoE operators (expert clone/swap/zero,
  prerouter heads, abliteration strength per projection).
- SafeMoE (ICLR'26): routing drift = safety axis. Our fitness INCLUDES refusal
  rate, so evolution cannot silently drift into refusal collapse OR uncensor
  bypass without it being measured — drift becomes a selected trait, not an accident.
- Abliterix: Bayesian search over abliteration configs (single technique).
  Ours is multi-operator, multi-objective, across the whole tensor set.

## Genome encoding
- Gene = shard file (24 layers + shared + adapters) or finer (expert block).
- Alleles per gene: source (stock/donor/abliterated/merged/slerp-t), operator
  params (abliteration strength 0..1.5, merge ratio, expert clone map).
- Individual = full model = 26-gene vector + global params.

## Operators (all already built except E)
- T1 abliteration strength per projection group (continuous gene).
- T2 expert clone/swap/zero maps (combinatorial gene).
- T3 layer source select (donor A/B/stock per layer).
- T4 mergekit blends (ratio gene per tensor group).
- E (new): crossover = take layers 0-11 from parent A, 12-23 from parent B
  (layer_swap already supports it); mutation = perturb one gene.

## Fitness (all measurable today)
- f_refusal = 1 - refusals/6 (eval_harness harmful set).
- f_caps = caps/5 (math/logic/code/translation/knowledge).
- f_kl = capability drift proxy (spot-check pass rate; full KL later).
- Multi-objective: Pareto front (refusal target, caps keep) — NSGA-II style.
- Cost control: fitness on Compact-GGUF-equivalent quants via :8089/:8090
  servers (seconds/token), promote winners to fp16 full eval rarely.

## Roadmap
- P0 (now): fitness infra = eval_harness (done) + runner logging gene->score
  to JSONL ledger (`evolve_log.jsonl`).
- P1: single-gene sweeps (abliteration strength per layer-group; expert-zero
  sensitivity map) — finds which tensors MATTER. Cheap, no evolution yet.
- P2: random search over 2-gene combos, Pareto-track.
- P3: full loop — tournament selection + crossover + mutation, population 8-16,
  generations gated by wall-clock (CPU eval is the bottleneck; distill fitness
  to fewer prompts as proxy).
- P4: close the loop into serving — champion genes become the served build;
  prerouter/RFDT heads evolve as separate gene groups.

## Risks
- Eval overfitting (6+5 set too small) -> grow prompt sets before trusting champions.
- Combos that break fluency silently -> keep caps + a fluency judge in fitness.
- CPU eval throughput bounds population size -> proxy fitness, promote rarely.
