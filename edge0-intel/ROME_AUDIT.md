# ROME-Style Fact Injection — Pre-Build Audit (2026-09-23)
## Verdict first: BUILDABLE with one structural downgrade (see A3).

### A. Requirements vs substrate
- **A1. White-box MLP access: PASS.** Ling fp16 dequant + per-layer shards
  proven; down_proj/gate_proj directly editable (apply_abliteration pattern).
- **A2. Covariance stats: FAIL at full ROME spec.** ROME needs second-moment
  stats over ~100k+ tokens of sample forwards. Native forward = 106 s each;
  full estimation = days. DOWNGRADE PATHS: (a) 50-sample micro-covariance
  (~90 min, noisy but workable for rank-one edits); (b) generic-text stats
  reused across edits (amortize once); (c) MEMIT-lite (fewer layers).
  Recommendation: (a)+(b) — one micro-covariance run, many edits.
- **A3. Writeback: PASS with conversion.** Edit in fp16 safetensors, then
  GGUF-convert for serving (llama-quantize path exists; converter must be
  verified for bailingmoe3 — untested, flagged).
- **A4. Eval: PASS.** AZ recall tasks ARE fact-recall probes; caps set guards
  fluency; neighbor-fact sets (to be built) guard specificity.

### B. Risks (ranked)
- **B1. Specificity bleed (known ROME failure mode).** Rank-one edits damage
  neighboring facts. Mitigation: neighbor eval set per injection batch;
  kill rule below.
- **B2. Covariance noise (from A2 downgrade).** Micro-stats mis-estimate;
  edits overshoot. Mitigation: small update norm cap + verify-then-keep
  (eval before ledgering, as always).
- **B3. Serving gap.** Edited fp16 needs GGUF conversion to serve; converter
  unverified for this arch. Mitigation: verify converter on roundtrip FIRST
  (s=0 equivalent: convert stock, serve, eval == baseline) before any edit.
- **B4. Irreversibility theater.** Keep pre-edit shard copies; every injection
  names its revert (file + hash). Disk cost acknowledged (runbook).

### C. Kill criteria (M8)
- Dead if: 3 injected facts fail efficacy (recall miss) after verified writes.
- Dead if: any batch drops caps >1 item (specificity breach) twice running.
- Downgrade to embedding-only tuning if MLP edits bleed but embed edits hold.

### D. Alternatives considered
- Prompt/context injection (graft sidecar): zero risk, zero permanence.
  Correct default for volatile facts; ROME is for stable mesh knowledge.
- Embedding-only tuning: cheaper, narrower (names/labels, not relations).
  Complementary, not competing — do both, different fact classes.
- Full SFT: blocked (no trainable loop at scale). Not an alternative today.

### E. Build order (on approval)
1. Converter roundtrip verify (stock fp16 -> GGUF -> serve -> eval == baseline).
2. Micro-covariance run (50 samples, generic text, amortized artifact).
3. Single-fact pilot (one worm-registry fact, efficacy + neighbors + caps).
4. Batch protocol only if pilot passes all three gates.
