# HANDOFF — The Oxford ShardFoundry (2026-09-22)

## Identity
Meta-evolution over tensor shards: populations of model builds, surgery operators
as mutations, functional fitness (refusal + caps), ledger of every run, champions
served. Specs: META_EVOLUTION.md, META_EVOLUTION_DEEPDIVE.md, TECHNIQUES.md,
TENSOR_SOURCES.md, PROJECT_NAME.md. All under C:\Users\clint\edge0-intel\.

## PROVEN working (do not redo)
- GGUF-domain surgery: scripts/gguf_abliterate.py — byte-exact metadata copy
  (KV layouts: scalar/string/array-item-parts), F16 writeback, s=0 roundtrip
  SERVED on :8091 with MOE-OK + 391 correct. Fast loop: edit->serve->eval.
- Native torch path: int4 U32 dequant (scripts/dequant_8b.py, 26 files/15.7GB,
  per-expert keys, 9349-tensor index) + CPU fallbacks (KDA port, short-conv,
  RMS-gate, scripts/fla_torch_fallback.py) -> "Hello, I am a 30-year" (106s).
- Safetensors abliteration: models/edge0-8b-abl-s1.0 DONE (2986 matrices,
  output-side projection, dim-mismatch skips). Math validated 1e-6.
- Refusal direction (8B): models/edge0-8b-fp16/refusal_dir.npy (norm 20.9, dim 1536).
- Evals: scripts/eval_full.py (100+20) + evolve_log.jsonl ledger.
  BASELINES: SC117-Compact 0/100 + 19/20; Gemma-E4B-stock 3/6 + 4/5; exp-k4 0/25 + 18/20.
- Tests: tests/test_surgery.py ALL PASS (caught 2 real bugs).

## Session 2026-09-23 results (supersedes "RUNNING now" + pour 1)
- Gemma torch-forward: DEAD, root-caused (torch_cpu segfault + meta-device
  crash, 8 attempts). Replaced by STRATUM layer-wise pipeline (see
  STRATUM_THESIS.md): probe PASS, collect PASS 1.3min ->
  models/gemma-4-e4b-abliterated/refusal_dir.npy (norm 29.78, dim 2560).
- GGUF surgery: 3 bugs fixed (orientation+test5, KV library parse, GGUF.*
  skip); 16-worker 3.14t pool (84 targets / 3 s).
- Dose-response N=100 (`:8092`, all ledgered): stock 14/19, s05 12/19,
  s10 20/19, s15 15/18, s20 22/18, sneg10 14/19. Direction BACKWARDS/FLAT;
  sneg10 = stock rules out sign flip. Do NOT escalate strength.
- Baselines: stock N=100 (14%) SUPERSEDES N=6 subset (50%). N>=50 rule now
  in SVI_SPEC.md promotion policy.
- Spark-X2.5: stock 0/100 + 17/20 (reference genome). IS a reasoning model:
  all caps empties were token-cutoff artifacts; eval_full.py fixed (256/600
  + reasoning fallback); historical caps suspect. Ctx 1M claimed, ~32-64K
  physical here. Mesh-driver probe: routes, can't JSON (use grammar).
- Graft structural tier adopted (384 nodes, accurate); deep tier blocked on
  provider speed (16/36 cached, batch timeouts). Armada paused (needs .NET 10
  SDK; targets net10.0).
- Next: direction audit (layers 20-35, wider contrast); scripts/svi.py DONE
  (table+predict+gates, verified); P1 zero map via STRATUM loader.
  :8089/:8090/:8092 down; :8091 UP (Spark 32K ctx, mesh/driver endpoint).
- New docs: SVI_SPEC.md, RAM_RUNBOOK.md (8 principles), SESSION_2026-09-23.md.
## Live servers
- :8091 Spark-X2.5 Q4_K_M, -c 32768 (driver + fast bench endpoint).
- :8089/:8090/:8092 DOWN by design until next task needs them.

## RUNNING now — SUPERSEDED by Session 2026-09-23 results above.
- Gemma direction DONE via STRATUM (not torch-forward): refusal_dir.npy
  norm 29.78 dim 2560. Dose-response DONE: direction backwards/flat.
- :8089/:8090 DOWN by design (RAM + no pending fitness task).

## Next pours (in order)
1. Direction audit: layers 20-35 separability + steering check, then wider
   contrast. Gated by svi.py admission gates.
2. P1 per-layer zero map via STRATUM loader -> `--predict` ranking.
3. Re-baseline caps with fixed harness (256/600 + reasoning fallback);
   all historical caps suspect.
4. P2 combos -> P3 loop per META_EVOLUTION_DEEPDIVE.md (only after a
   working single direction exists).

## Watchouts
- Disk: ~44GB free C:. Candidate builds 5-7GB each; keep 15GB headroom.
- N>=50 for promotion (SVI_SPEC.md). N=6 subsets gated entry only.
- Refusal-direction dose on Gemma: backwards/flat — do NOT escalate strength.
- Donors: same-arch only (shape + coordinate + interface rule).
- One run, one window (RAM_RUNBOOK.md principles).
