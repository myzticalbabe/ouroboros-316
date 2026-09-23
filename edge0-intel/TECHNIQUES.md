# TECHNIQUES — perfected tensor-swap procedures (validation status each)

Box: Win11, 15.4GB RAM, Arc 140T 8GB, CPU-first, WSL Ubuntu-26.04.
Model: edge0-8b / Ling-3.0-tiny family (hidden 1536, 24L, 128 experts, top-8).
RULE 0: donor dims must match exactly. Qwen/Mixtral/OLMoE never fit.

## T1 Abliteration (uncensor by projection) — MATH PROVEN, live pending
- `scripts/apply_abliteration.py`: `W -= s*outer(W@r_hat, r_hat)` on
  `o_proj`/`down_proj`. Test `tests/test_surgery.py::1` proves row-orthogonality
  (`max|W'.r| ~1e-6`); the run caught + fixed a real projection-order bug.
- Refusal direction: `scripts/collect_refusal_dir.py` (contrast pairs) — needs
  running forward; fallback = transfer SC117's direction (same family, validate).
- Baseline measured on SC117-Compact (`:8089`): **refusals 0/6, caps 5/5**
  (`scripts/eval_harness.py --tag sc117-compact`). Our abliterated fp16 gets
  measured against this exact bar after text-out works.

## T2 Expert surgery (clone/swap/zero, same-count) — PROVEN on synthetic shard
- `scripts/expert_surgery.py`. Test ::2 proves clone copies src->dst exactly
  and zero neutralizes (fused `[E,out,in]` layout, 128 experts kept).
- No router/prerouter retrain by construction. SafeMoE (ICLR'26) caveat: routing
  drift governs safety — prefer T1 projection edits for safety-relevant changes;
  eval refusal rate after every op.

## T3 Layer swap / Frankenmerge — TOOL DONE, index logic PROVEN
- `scripts/layer_swap.py` (donor layers + index rebuild). Test ::3 proves index
  maps every key. Live donor swap awaits text-out (needs before/after eval).

## T4 Mergekit blends (slerp/ties/dare) — DOCUMENTED, not yet run
- CPU + lazy tensors fit this box. Candidates: our fp16 x Ling-3.0-tiny BF16.
- `mergekit-moe` (dense->MoE) skipped: no dense donors in-family.

## T5 Dequant int4->fp16 streaming — PROVEN (production artifact)
- `scripts/dequant_8b.py`: U32+BF16-scales affine group-64 -> fp16 per-layer
  shards + per-expert key explode (modeling class layout). Full 8B: 26 files,
  15.7GB. Two bugs caught by tests, not by luck (projection order, key layout).

## T6 Torch CPU fallbacks for fla kernels — SHAPE/CONSISTENCY PROVEN
- `scripts/fla_torch_fallback.py`: KDA recurrence ported from triton kernel math
  (l2norm, `-5*sigmoid(exp(A)*(g+bias))` decay, beta gate, delta update);
  ShortConvolution depthwise torch port (step==full proven ::4a);
  FusedRMSNormGated torch port; KDA finite + state threading proven ::4b.
- Forces fp32 on CPU (CPU has no fp16 matmul) -> disk-offload load works
  (141s, 4.8GB resident of 15.7GB). Remaining: full generation proof.

## T7 Eval harness — LIVE, baselined
- `scripts/eval_harness.py`: 6 harmful (refusal marks) + 5 caps (math/logic/
  code/translation/knowledge). SC117-Compact: 0/6 refusals, 5/5 caps.
- 2026-09-23: reasoning-aware (reads via eval_full.read_response, 400 tok).
  Pre-fix version scored 0 on thinking models. Ledger fitness lives in
  eval_full.py (N>=50); harness is smoke only.

## T8 GGUF-domain surgery — PROVEN (Ling + Gemma)
- `scripts/gguf_abliterate.py`: dequantize target tensors (dq orientation =
  REVERSED vs GGUF meta — never `.reshape(t.shape)`), output-side projection
  along whichever axis carries the residual dim, write back F16, everything
  else byte-identical, KV via library `field.types`/`contents()` (hand
  parse_kv died on Gemma string-arrays), skip GGUF.* pseudo-fields.
- Dim-mismatch skip (ValueError -> pass through): wrong-arch tensors can't
  abort a run (proven on Spark: edited=0 honest roundtrip).
- `--layers all|list|range` for per-layer maps; 16-worker 3.14t pool, order
  preserved (84 targets / 3 s). GPU correctly rejected (streaming job).
- Readback verification: `r̂·W′ ~1e-5` on written bytes before serving.
- Status (2026-09-23): Ling s05 0/100+19/20; Gemma dose backwards/flat
  (stock 14 -> s20 22) — faithful surgery, wrong vector. Do NOT escalate.

## T9 Layer-wise dense forward (STRATUM) — PROVEN
- `collect_stratum.py`: dual config (full-42 for structure, truncated-31
  twin for PLE dims), per-layer table sliced to 31 blocks, vestigial k/v
  drop mirroring `_keys_to_ignore_on_load_unexpected`, backbone-only
  forward (lm_head never materializes), lazy safe_open streaming.
  6 prompts x 31 layers, wall 1.3 min. Refusal dir norm 29.78 dim 2560.
- `probe_stratum.py` proved mechanics first (layer-0: shape + finite + norm).

## T10 Fitness, SVI, gates — LIVE
- `eval_full.py`: reasoning-aware reads (256/600 budgets), temp 0 seed 7
  logged, dual counts (marks continuity + `_j` coherence+second-judge).
- `svi.py`: SVI = .5*refusal + .5*caps - .02*wall; promotion N>=50, caps
  floor .80, SUSPECT quarantine (caps==0); `--predict` additive +
  epistasis epsilon; pre-serve gates (compile / mate-dims / mate-finite).
- `az_eval.py`: mesh-native driver fitness (42 tasks from worm registry +
  traces) + median latency. Spark baseline 20/42, 25 s/task.

## T11 Ops patterns (all adopted, all earned)
- OBSERVE-first logging (ram/disk) + dual stdout/file + traceback-to-log.
- RUN_*.bat: visible console, title, EXIT + pause. One run, one window.
- Disk-steady sweeps: ledger rows are the artifacts, builds deleted after
  (`--keep` overrides). G: is cold-archive only (~11 MB/s, never serve).
- status.bat: RAM holders, :8089-8092 health, sweep JSON, canary, logs, ledger.
- Staged prints + faulthandler trip on long jobs; silence is a bug.

## Suite
- `tests/test_surgery.py`: ALL SURGERY VALIDATIONS PASS (1,2,3,4a,4b,5,6).
- Live MoE: SC117 Compact GGUF on llama-server b10964 `:8089` (MOE-OK + eval).
