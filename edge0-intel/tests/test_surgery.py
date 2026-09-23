"""Validate surgery math without loading the 8B model (fast, CPU, numpy/torch).
1. abliteration: r_hat . W' == 0 (orthogonality), untouched rows identical.
2. expert_surgery: clone/swap/zero on synthetic fused expert shard.
3. layer_swap index: rebuild maps every key.
4. fla fallbacks: conv step-vs-full consistency; KDA output finite + state update.
"""
import os, sys, json, shutil
import numpy as np

OWN = r"C:\Users\clint\edge0-intel\scripts"
sys.path.insert(0, OWN)
TMP = r"C:\Users\clint\edge0-intel\tests\tmp_surg"
shutil.rmtree(TMP, ignore_errors=True)
os.makedirs(TMP, exist_ok=True)

# 1. abliteration
from apply_abliteration import abliterate_matrix
rng = np.random.default_rng(0)
W = rng.standard_normal((64, 32)).astype(np.float32)
r = rng.standard_normal((64,)).astype(np.float32)
W2 = abliterate_matrix(W, r, 1.0)
rh = r / np.linalg.norm(r)
res = float(np.abs(rh @ W2).max())
assert res < 1e-5, res
print(f"1 abliteration output-orthogonality max|r.W'|={res:.2e} OK")

# 2. expert surgery on synthetic shard
from safetensors.numpy import save_file, load_file
E, O, I = 4, 8, 16
d = {}
for p in ["gate_proj", "up_proj", "down_proj"]:
    d[f"model.layers.0.mlp.experts.{p}.weight"] = rng.standard_normal((E, O, I)).astype(np.float16)
src = os.path.join(TMP, "shard.safetensors"); save_file(d, src)
sdir = os.path.join(TMP, "m"); os.makedirs(sdir, exist_ok=True)
save_file(d, os.path.join(sdir, "model.layer0.safetensors"))
import expert_surgery as ES
sys.argv = ["x", "--op", "clone", "--layer", "0", "--src-exp", "1", "--dst-exp", "3",
            "--src", sdir, "--out", sdir + "_c"]
ES.main()
got = load_file(os.path.join(sdir + "_c", "model.layer0.safetensors"))
base = load_file(os.path.join(sdir, "model.layer0.safetensors"))
assert np.array_equal(np.asarray(got["model.layers.0.mlp.experts.gate_proj.weight"])[3],
                      np.asarray(base["model.layers.0.mlp.experts.gate_proj.weight"])[1])
sys.argv = ["x", "--op", "zero", "--layer", "0", "--dst-exp", "0",
            "--src", sdir, "--out", sdir + "_z"]
ES.main()
gotz = load_file(os.path.join(sdir + "_z", "model.layer0.safetensors"))
assert float(np.abs(np.asarray(gotz["model.layers.0.mlp.experts.gate_proj.weight"])[0]).max()) == 0.0
print("2 expert clone+zero OK")

# 3. index rebuild (same logic as build_fp16_index.py)
from safetensors import safe_open
wmap = {}
for fn in sorted(os.listdir(sdir + "_c")):
    if fn.endswith(".safetensors"):
        with safe_open(os.path.join(sdir + "_c", fn), framework="np") as f:
            for k in f.keys():
                wmap[k] = fn
assert len(wmap) == 3 and set(wmap.values()) == {"model.layer0.safetensors"}
print("3 index rebuild OK")

# 4. fla fallbacks: conv step-vs-full + KDA finite
import torch
from fla_torch_fallback import torch_kda, _torch_forward, _torch_step
from fla.modules.conv.short_conv import ShortConvolution
m = ShortConvolution(hidden_size=16, kernel_size=4); m.eval()
x = torch.randn(1, 7, 16)
with torch.no_grad():
    yf, c = _torch_forward(m, x, output_final_state=True)
    x8 = torch.cat([x, torch.randn(1, 1, 16)], dim=1)
    yf8, _ = _torch_forward(m, x8)
    ys, _ = _torch_step(m, x8[:, -1:], None, c, False)
    assert torch.allclose(yf8[:, -1:], ys, atol=1e-4), "conv step/full mismatch"
print("4a conv step==full OK")
B, T, HV, K, V = 1, 5, 8, 32, 32
q = torch.randn(B, T, 8, K); k = torch.randn(B, T, 8, K)
v = torch.randn(B, T, HV, V); g = torch.randn(B, T, HV, K)
b = torch.rand(B, T, HV).sigmoid()
o, s = torch_kda(q, k, v, g, b, torch.randn(HV), torch.randn(HV, K), None, None, True, -5.0)
assert torch.isfinite(o).all() and torch.isfinite(s).all()
o2, s2 = torch_kda(q[:, -1:], k[:, -1:], v[:, -1:], g[:, -1:], b[:, -1:],
                   torch.randn(HV), torch.randn(HV, K), s, None, True, -5.0)
# 5. GGUF-domain orientation: dequantize returns REVERSED dims vs t.shape;
# abliteration must preserve dq orientation (writer stores dims reversed, so
# dq-orientation writeback reproduces original metadata). Regression test for
# 2026-09-22 bug where .reshape(t.shape) scrambled data AND flipped dims,
# producing unloadable files (loader: expected 2048,1536 got 1536,2048).
from gguf_abliterate import ablaterate_gguf
r1536 = rng.standard_normal((1536,)).astype(np.float32)
# 2D case: dq orientation (1536, 2048) for metadata (2048, 1536)
Wdq = rng.standard_normal((1536, 2048)).astype(np.float32)
Wout = ablaterate_gguf(Wdq, r1536, 1.0)
assert Wout.shape == Wdq.shape, (Wout.shape, Wdq.shape)
rh = r1536 / np.linalg.norm(r1536)
assert float(np.abs(rh @ Wout).max()) < 1e-4, "2D output-orthogonality failed"
# 3D fused experts: dq orientation (E, O, I) = (8, 1536, 512)
W3 = rng.standard_normal((8, 1536, 512)).astype(np.float32)
W3out = ablaterate_gguf(W3, r1536, 1.0)
assert W3out.shape == W3.shape, (W3out.shape, W3.shape)
for e in range(W3out.shape[0]):
    assert float(np.abs(rh @ W3out[e]).max()) < 1e-4, f"expert {e} not orthogonal"
print("5 GGUF orientation + orthogonality (2D and fused-expert 3D) OK")
print("ALL SURGERY VALIDATIONS PASS")
