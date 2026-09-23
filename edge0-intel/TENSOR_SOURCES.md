# TENSOR SOURCES DEEP DIVE — where swappable tensors come from (GET vs MAKE)

Box: 15.4GB RAM, Arc 140T 8GB, CPU-first. Our model: edge0-8b (BailingMoE,
hidden 1536, 24L, 16/16 heads, vocab 157184, 128 experts, top-8, silu).
RULE: donor dims must match exactly. Qwen/Mixtral/OLMoE tensors DO NOT fit.

## GET (download donors — same family only)

1. `inclusionAI/Ling-3.0-tiny` (MIT, 15.8GB BF16, 32 shards, `bailing_hybrid`).
   Config matches ours on all 9 fields (hidden/layers/heads/vocab/experts/topk).
   Full-precision donor for any layer/expert/attn swap. The base our 8B was built on.
2. `SC117/Ling-3.0-tiny-abliterated-APEX-GGUF` — abliterated Ling tiny
   (abliterix LoRA-steering, 130 configs Pareto-searched, 85% fewer refusals
   15/100 vs 98/100, KL 0.0677, caps spot-checks pass). GGUF tiers:
   Mini 3.41 / Compact 3.99 / Quality 5.77 / Balanced 5.96 / bf16 15.8 GB.
   Compact runs on our llama-server b10964 (bailingmoe3 support, b10470+) TODAY.
3. Edge0's own `lora_edge0_8b` + `prerouter_edge0_8b` (ship with checkpoint).
   Additive/swap-in files by design.
4. `d1sl1ke` oQ MLX quants — Apple-only, SKIP (no Intel value).
5. `inclusionAI/sglang_ling_v3/bailing_moe.py` — runnable torch reference
   (CUDA) for validating our CPU port math, not donor weights.

## MAKE (derive on this box, no training cluster)

1. **Abliteration (ZeroFuse/abliterix style)** — orthogonalize refusal direction
   out of `o_proj`/`down_proj`. Direct edit, zero inference cost, no retrain.
   Needs refusal direction: contrast-pair activations from a RUNNING forward
   (our CPU fallback path enables this), or transfer SC117's direction
   (same family — validate by refusal eval, expect approximate transfer).
   Tool: `scripts/apply_abliteration.py` (done).
2. **Expert surgery** — clone/swap/zero, same-count only (router+prerouter
   untouched). Tool: `scripts/expert_surgery.py` (done). NOTE (SafeMoE, ICLR
   2026): routing drift controls safety in MoE — prefer projection edits over
   routing changes when safety matters; eval refusal rate after every swap.
3. **Layer swap / Frankenmerge** — whole-layer replace, norm travels with
   layer. Tool: `scripts/layer_swap.py` (done).
4. **Mergekit (CPU, lazy tensors — fits this box)**: slerp/ties/dare/della
   blends of our fp16 + Ling-tiny BF16 donors; passthrough Frankenmerge;
   `mergekit-moe` builds MoE from dense (needs dense donors — skip);
   LoRA extraction (peft-compatible adapters FROM our edits).
5. **Prerouter heads** — tiny MLPs (hidden 512), cheap to retrain on routing
   traces once forward runs. Edge0 ships trained ones; keep as init.
6. **RFDT decision heads** (simple-jev style) — cheap, CPU-friendly, for the
   classifier layer, not the base model.
7. **LoRA fine-tune (peft)** — possible but backward-through-8B-MoE on CPU is
   days; gate on WSL-XPU torch. Defer unless measured gap demands it.
8. **Distillation / full retrain** — not on this box. Buy compute or skip.

## Recommended order
Compact GGUF live (done, MOE-OK) -> torch CPU forward (fallbacks in) ->
refusal direction -> abliterate fp16 -> mergekit blends with Ling-tiny ->
eval (refusal rate + caps spot-checks, SC117's protocol) -> prerouter/RFDT.
