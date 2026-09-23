# STRATUM — Layer-Wise Surgery for Dense (non-MoE) Models
## Postulate, Hypothesis, and Thesis (2026-09-22)

## 1. Postulate

To modify dense non-MoE models under hard RAM ceilings, we need a program
analogous to edge0's per-shard pipeline: one that loads, executes, and edits
individual layers without ever materializing the full model — thereby
overcoming the technological constraints (RAM ceiling, accelerate
meta-device failures, torch native segfaults) that block all full-model
tooling on this machine.

## 2. Hypothesis

A layer-wise forward pipeline — load one layer's weights from safetensors,
execute it, cache the activation, evict the weights — reproduces full-model
hidden states within floating-point tolerance while bounding peak RAM to
one layer plus embeddings. This removes both blockers simultaneously:

- the RAM ceiling (peak ~6–7 GB vs ~12 GB for full-model forward), and
- the accelerate failure modes (no device_map, no disk-offload hooks, no
  meta tensors — everything explicitly materialized — so neither the
  torch_cpu.dll segfault nor the `torch.where` meta-device crash can occur).

Consequence: refusal-direction collection and abliteration become possible
on dense models (Gemma-4 E4B) on this 16 GB machine, exactly as edge0's
per-shard pipeline made them possible on the 8B MoE.

## 3. Thesis

### 3.1 Problem
Dense-model surgery is currently impossible here. Measured, not theorized:
- Full torch forward of Gemma-4 E4B (14.89 GB bf16, single safetensors)
  dies on every attempt: 4 canonical runs (2.4/7.4/10.7/10.9 GB free) plus
  4 truncated-31-layer runs, all killed at first forward.
- Root cause is NOT RAM alone: Windows Event Log shows
  `torch_cpu.dll, exception 0xc0000005` (native segfault) on repeat runs,
  and faulthandler traces the latest failure to
  `modeling_gemma4.py:2314 — torch.where(multimodal_mask, pad_embedding,
  inputs_embeds)` with a meta-device tensor. The accelerate disk-offload
  machinery leaves tensors meta on exactly the path the multimodal merge
  touches. Patching around it (truncation to 31 layers, per-layer table
  slicing 10752→7936, 4.5–8 GB resident caps, lm_head skipping) moved the
  failure point but never past it: the tooling stack itself is the wall.

### 3.2 Precedent (why we believe this works)
edge0-8b, same machine, same ceiling — SOLVED by refusing full-model
tooling: int4 U32 dequant (`scripts/dequant_8b.py`, 26 files / 15.7 GB,
per-expert keys, 9349-tensor index) plus hand-ported CPU fallbacks (KDA
port, short-conv, RMS-gate, `scripts/fla_torch_fallback.py`) produced a
real forward ("Hello, I am a 30-year", 106 s) and then a real artifact
(`models/edge0-8b-fp16/refusal_dir.npy`, norm 20.9, dim 1536), which now
drives the PROVEN GGUF surgery loop. The doctrine is established:
**when the framework cannot load the model, load the tensors yourself.**

### 3.3 Why dense is easier than the solved MoE case
- No experts, no routing, no per-expert keys: each decoder layer is a
  closed function (attn + MLP + norms) over the residual stream.
- No file surgery needed: safetensors supports lazy per-tensor reads
  (`safe_open`), so one 14.89 GB file serves as its own shard store.
- Only 31 layers are needed (hidden_states[30]); layers 31–41 are never
  touched — already proven loadable-in-principle by the truncation runs.

### 3.4 Method (program: STRATUM, `scripts/layerwise_dense.py`)
1. `safe_open` the single safetensors; mmap embeddings once and pin to CPU
   (embed_tokens 1.34 GB + per-layer table sliced to 31 blocks 4.16 GB —
   both PROVEN pinnable).
2. For each prompt: embed → for i in 0..30: load layer-i tensors, execute
   the layer's exact math (reuse transformers' layer class with injected
   weights, or a ported minimal forward), append activation, evict.
3. Replicate the multimodal merge prefix on CPU with materialized tensors
   (the `torch.where` at :2314 works fine once nothing is meta).
4. Contrast harmful vs benign at layer 30 → `refusal_dir.npy`.
5. Same pipeline in reverse supplies torch-domain abliteration AND the
   P1 per-layer zero map (edit layer files individually — the exact
   operation the handoff lists as next).
- Peak RAM: 5.5 GB embeddings + ~0.5 GB active layer + activations ≈
  6–7 GB. Fits in the measured 10–11 GB window with margin.
- Cost: I/O-bound, ~15 GB streamed per prompt × 6 prompts ≈ minutes,
  same order as the 8B MoE's 106 s forward. Acceptable.

### 3.5 Validation criteria (functional fitness is ground truth)
1. Algebraic: layer-wise activations equal full-model activations up to fp
   associativity (verifiable on any layer against a small reference where
   full load fits; the foundry's `tests/test_surgery.py` pattern).
2. Artifact sanity: refusal_dir norm/dim in family with the 8B precedent
   (norm ~O(20), dim 2560 for Gemma vs 1536 for Ling).
3. Fitness: abliterate → quantize → serve :8092 → `eval_full`
   (target 0/6+ refusal collapse, caps 4/5+ held — same bar as handoff §1).
   A direction that moves fitness is correct; all else is commentary.

### 3.6 Risks and answers
- Gemma-4 merge-path fidelity (audio/vision towers, per-layer inputs):
  text-only prompts exercise the language path; towers load but idle.
  Residual risk is bounded by criterion 3 (fitness decides).
- Speed: streaming 90 GB/prompt-set from SSD at ~500 MB/s ≈ 3 min/set.
  Fine.
- Scope creep into a framework rewrite: FORBIDDEN. STRATUM executes
  layers; it does not reimplement training, quantization, or serving.
  llama-quantize + llama-server stay as-is (both PROVEN).

### 3.7 Milestones
1. `probe_stratum.py`: load ONE layer, forward ONE prompt, print shape.
2. Full 31-layer × 6-prompt collection → Gemma `refusal_dir.npy`.
3. Torch-domain abliteration (skip towers) → quantize Q4_K_M → :8092 →
   `eval_full --tag gemma-abl-s10`.
4. P1 per-layer zero map rides the same loader for free.

## 4. Status line
Gemma torch-forward via transformers+accelerate: DEAD (segfault + meta
crash, 8 attempts, root-caused 2026-09-22). STRATUM is the replacement
path, not another patch on the dead one.
