# Tool Gap Audit (2026-09-23)
## Every tool we have, what's missing in how WE use it.

### Serve / inference
- **llama-server b10964: no activation steering API.** Runtime steering
  (priority experiment) is impossible through the server; only baked weights.
  Workaround exists (hot-layer ± doses as builds) but costs builds+evals.
- **Thinking toggle not honored** (Spark ignores enable_thinking=false).
  Reasoning tax is mandatory per call; verified by probe.
- **response_format/grammars never tried.** JSON discipline failure (Spark
  probe) has a server-side fix we haven't tested once.
- **No supervisor.** Manual serve/kill; crashes found by polling. status.bat
  observes, nothing recovers.
- **Port registry implicit** (handoff text). No ports file, no lock; two
  servers once fought over RAM silently (see M9).
- **llama-quantize: no imatrix-guided quants tried.** All Q4_K_M are
  default-importance; quality left on the table, unmeasured.

### Surgery / mutation
- **No provenance sidecar on builds.** Strength/dir/targets/layers live in
  filenames or not at all (duplicate-name incident proved it). collect_gemma2
  invented sidecars; never generalized. Genome = {} downstream of this.
- **Single direction only.** No multi-direction subspace, no per-expert
  GGUF targeting (whole-tensor edits on MoE!), no router-bias ops wired.
- **STRATUM reloads layers per prompt** (186 loads for 6 prompts; batch all
  prompts per layer = 31 loads, ~6x speedup unclaimed). No lm_head: hidden
  states only, no likelihood scoring.
- **No negative gate test.** svi gates verified ADMIT only; no corrupt build
  ever tested for REJECT (the transpose bug predates gates).

### Eval / fitness
- **Caps judge missing** (substring only); harness elicitation frozen at
  zero-shot; no MMLU/GSM8K adapter; caps set at ceiling risk (20/20 seen).
- **AZ ground truth weak** on triage/recall (proxy labels); route/config
  solid. Latency recorded, no SLOs.
- **svi --predict never executed** against a real combo (no combos exist).

### Memory / knowledge
- **Graft: MCP + init unwired; deep blocked** (provider speed). Structural
  adopted but unqueried for real work. No timeout knob exists upstream.
- **AEndrix-memory vs PAMS unresolved** (deferred decision, no criteria).
- **Ollama embeddings (nomic) never used** for doc retrieval; no RAG over
  the 108 azazael docs despite the sprawl audit.

### Ops / repo hygiene (serious)
- **Models NOT git-ignored** (check-ignore returns nothing for *.gguf).
  A 7GB accidental commit is one wildcard away. No LFS, no ignore rules.
- **Concurrent stager unidentified.** Foreign files (rainbow_queens,
  SESSION_MILESTONEs) appear in the index from another process. Provenance
  of our own commits is clean, but the repo is shared with an unknown writer.
- **No disk monitoring.** The 0-byte surprise had no early warning; fixed by
  driver-level deletion, but no alerting exists.
- **Docstring drift** (OUT filename, --keep) found twice by accident, not
  by process. No CLI doc generation.

### Dev loop
- **Two interpreters, one tested path.** Stock vs 3.14t package drift
  unexamined; gguf/transformers versions pinned nowhere (requirements file?
  none for edge0-intel).
- **LM Studio Hub reachable but unused** (one failed attempt). It bypasses
  the HF block — the OLMoE path may still be open through it.
- **Ollama client stale** (0.32, update downloaded, not installed).
- **Armada unbuilt** (net10 SDK gap). **cactus-needle/omniparse uninstalled**
  (researched only). **Needle 3 untried.**

### Top-3 closes (leverage order)
1. **`.gitignore` models + RMSE for repo hygiene** — one file, prevents the
   catastrophic accident class. Minutes.
2. **Build provenance sidecar** (strength/dir/targets/layers/timestamp/
   refusal-hash per GGUF) — unblocks genome schema (M5), Atlas Δ table,
   and every future "which build is this" mystery. Small.
3. **STRATUM batching + lm_head scoring** — 6x collect speedup and
   likelihood-based evals; multiplies every future direction campaign.
