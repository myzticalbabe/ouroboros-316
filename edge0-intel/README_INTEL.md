# edge0-intel — Intel backend for Edge0 (Arc GPU + CPU)

Stolen framework (Apache-2.0, upstream `Edge0-AI/Edge0` in `_upstream/`):
- `moe/spec.py`, `moe/routing.py` — router math
- `streaming/options.py`, `mmap.py`, `cache.py` — SSD mmap + shared LRU
- `prerouter/spec.py`, `heads.py`, `stager.py`, `state.py` — cross-token routing prediction
- `engine/base.py`, `sampling.py`, `server/`, `registry.py` — shared loop + HTTP

New here (`src/edge0/backends/intel/`):
- `device.py` — auto `xpu` (Arc via Level Zero/torch.xpu) else `cpu`
- `core.py` — numpy baseline + torch.xpu matmul dispatch (same names as mlx.core)
- `nn.py` — Module/Linear/RMSNorm/silu/gelu
- `io.py` — numpy mmap SafeTensorsStore + HF tokenizer
- `quant.py` — reference gather_qmm + swiglu (CPU now, MKL SYCL BLAS later)
- `backend.py` — BackendImpl assembly

Yes, GPU works: `EDGE0_INTEL_DEVICE=auto` uses Arc when `torch.xpu.is_available()`,
else CPU. Same code path, no fork.

## Use
```
python scripts/install_intel_backend.py   # copy overlay into _upstream + patch EDGE0_BACKEND
set EDGE0_BACKEND=intel
python tests/test_intel_backend.py
python scripts/check_intel_gpu.py
```
WSL: Windows Intel driver + `intel-basekit` + Level Zero, `ONEAPI_DEVICE_SELECTOR=level_zero:gpu`.
llama.cpp SYCL server stays for dense models; this backend is for streaming MoE.
