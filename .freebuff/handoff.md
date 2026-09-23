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
  edge0-intel/STRATUM_THESIS.md): probe PASS, collect PASS 1.3min ->
  models/gemma-4-e4b-abliterated/refusal_dir.npy (norm 29.78, dim 2560).
- GGUF surgery: 3 bugs fixed (orientation+test5, KV library parse, GGUF.*
  skip); 16-worker 3.14t pool (84 targets / 3 s).
- Dose-response N=100 (`:8092`, all ledgered): stock 14/19, s05 12/19,
  s10 20/19, s15 15/18, s20 22/18, sneg10 14/19. Direction BACKWARDS/FLAT;
  sneg10 = stock rules out sign flip. Do NOT escalate strength.
- Baselines: stock N=100 (14%) SUPERSEDES N=6 subset (50%). N>=50 rule now
  in SVI_SPEC.md promotion policy.
- Next: direction audit (layers 20-35, wider contrast); scripts/svi.py;
  P1 zero map via STRATUM loader. :8089/:8090 down by design until then.
- New docs: SVI_SPEC.md, RAM_RUNBOOK.md (8 principles), SESSION_2026-09-23.md.

## Live servers
- :8089 SC117 Compact GGUF (fitness backend, exp-k4 override active — restart
  WITHOUT --override-kv to restore k8 baseline).
- :8090 Gemma E4B stock Q4_K_M (baseline 3/6+4/5).
- :8091 was roundtrip validation (killed after proof).

## RUNNING now
- ~~edge-gemmacollect~~ SUPERSEDED by edge-collectclean (canonical, OBSERVE-first).
- Gemma direction: load PROVEN (2076 tensors), embed-pin fix PROVEN (loads 42
  layers), forward BLOCKED by RAM (2.4GB free vs ~8GB need -> OOM kill, no
  traceback). REBOOT authorized (option 2) to clear compression/standby.
- Post-reboot order: verify free RAM -> run edge-collectclean ->
  refusal_dir.npy -> abliterate Gemma (skip towers) -> llama-quantize Q4_K_M ->
  serve :8092 -> eval_full --tag gemma-abl-s10.
- :8089/:8090 DOWN (paused for RAM); restart fitness backends post-reboot.

## Next pours (in order)
1. Gemma direction -> apply_abliteration (skip vision/audio towers+mmproj) ->
   llama-quantize.exe (in llama-b10964-cpu dir) Q4_K_M -> serve :8092 ->
   eval_full --tag gemma-abl-s10. Target 0/6+, caps 4/5+.
2. abl-s1.0 native proxy eval (needs ~32GB offload space — disk only 21GB free;
   free space first or GGUF-convert the abl dir).
3. P1 strength sweep (0.5/1.5) + per-layer zero map (GGUF domain now proven).
4. P2 combos -> P3 loop per META_EVOLUTION_DEEPDIVE.md.

## Watchouts
- Disk: 21GB free. Candidate builds are 16-19GB each; clean offload_* scratch
  and superseded models aggressively (see memory: disk crisis 2026-09-21).
- N=6 evals are +/-20% noise; promote only on N>=50 (sets grown in eval_sets/).
- Qwen/Mixtral tensors NEVER fit (arch rule); donors: Ling family only.
- Ollama qwen3.8:27b + duplicate bonsai were removed (superseded). Remaining
  Ollama models untouched.
