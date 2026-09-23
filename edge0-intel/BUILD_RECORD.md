# BUILD RECORD — edge0-intel (new thing from several project packages)

Date: 2026-09-21. Box: Win11 + Arc 140T 8GB + WSL Ubuntu-26.04 + Python 3.14.

## What was built
`C:\Users\clint\edge0-intel\` — Intel backend overlay for Edge0 streaming-MoE,
CPU now + Arc GPU (torch.xpu/Level Zero) when available. Test passes:
`OK device=cpu ... matmul/softmax/linear/swiglu pass`.

## Pieces stolen (and from where)
1. Edge0-AI/Edge0 (Apache-2.0, `_upstream/`, 2026-09-17 paper 2609.18063):
   framework only — `moe/spec+routing`, `streaming/options+mmap+cache
   (SharedExpertCache LRU, PrefetchBuffer)`, `prerouter/spec+heads+stager+state
   (fc1->erf gelu->fc2 + linear_init)`, `engine/base` loop, `sampling`,
   `server/app`, `registry`, `config`. Left MLX `_impl` + qwen/ling glue.
2. Edge0 backend contract (`backends/__init__.py` + `base.py` TensorStore):
   kept verbatim, added `elif _BACKEND=="intel"` branch. core/nn/io/quant
   surface identical so engine/streaming/prerouter run unchanged.
3. Intel oneAPI docs + community Arc guides (llama.cpp SYCL `-DGGML_SYCL=ON`,
   `ONEAPI_DEVICE_SELECTOR=level_zero:gpu`, Vulkan fallback, `--split-mode layer`):
   used as device-selection model for `device.py` (auto xpu/cpu).
4. simple-jev idea (logit-score, no generation, prefix KV reuse): noted as next
   scorer on same backend; not copied yet, contract reserved in quant/core.
5. WSL GPU setup (Intel compute-runtime WSL.md, oneAPI basekit): verified
   `/dev/dri/renderD128` + Intel OpenCL Ultra 9 285H present; sycl-ls absent =
   basekit still to install in WSL.

## New code (ours)
`src/edge0/backends/intel/`: `device.py`, `core.py` (numpy + torch.xpu matmul
dispatch), `nn.py`, `io.py` (numpy mmap SafeTensorsStore), `quant.py`
(reference gather_qmm + swiglu), `backend.py`, plus `scripts/install_*.py`,
`scripts/check_intel_gpu.py`, `tests/test_intel_backend.py`.

## How verified
- `install_intel_backend.py`: overlay copied, selector patched (mlx,intel).
- `EDGE0_BACKEND=intel test_intel_backend.py`: pass on Windows CPU path.
- `check_intel_gpu.py`: Arc 140T reported, WSL DRI+OpenCL OK,
  torch.xpu=False on Win Python (expected; XPU torch lives in WSL).

## Trials (2026-09-21)
- Edge0-35B streaming: framework proof PASS on intel backend
  (`EDGE0-FUNC (1, 8) bundle intel` — PrerouterHead math + SharedExpertCache
  via importlib bypass). Full 35B weights NOT loaded (too big for 95GB free
  alongside rest; needs safetensors set, not GGUF).
  Deficiency found: `prerouter/__init__.py -> install.py` hard-imports
  `backends.mlx._impl.qwen3_next`, bypassing the backend selector. Intel port
  must rewrite install.py to load heads via intel io (safetensors) instead.
- edge0-8b full tier downloaded (2026-09-21): model.safetensors 4.20GB +
  lora_edge0_8b + prerouter_edge0_8b + tokenizer + modeling_bailing_moe_v3.py.
  Transformers-direct load FAILS twice: (1) custom quant config without
  quant_method (fixed by stripping quantization_config); (2) quant tensors
  (.weight int-packed + .scales/.biases for experts/shared/attn) are
  UNEXPECTED to the torch modeling class — the release relies on the mlx
  engine (load_installed) to interpret them. Full generation needs either
  the engine/install MLX-decoupling port or a custom torch loader mapping
  quant->dequant (our intel quant.gather_qmm is the math reference).
- FIX (2026-09-21): custom streamed dequantizer `scripts/dequant_8b.py`
  (U32 packed + BF16 scales/biases, affine group-64 -> fp16 per-layer shards).
  Layer-1 proof: 26 tensors 652MB fp16 + shared 966MB (embed+head).
  Full 24-layer run (~16GB) launched as scheduled task `edge8b-dequant`.
  Retrain verdict: base needs NO retrain (weights are the product; LoRA +
  prerouter ship paired). Cheap retrain later = prerouter heads (tiny MLPs,
  need routing traces from a running model) or RFDT decision heads.
  LoRA retrain = heavy (GPU+triton, days) — not needed unless quality gap
  measured after the fix runs.
- Qwen3.8-27B uncensored: `ollama pull qwen3.8:27b` started in background
  (ollama PIDs live); not in `ollama list` yet (16GB-class download).
  Dense 27B VL — runs via Ollama/llama-server SYCL GGUF path, NOT Edge0
  streaming (no experts). Needs Q4/Q3 quant to fit 15.4GB RAM + Arc 8GB.
