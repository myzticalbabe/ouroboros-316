"""Dequantize edge0-8b int4 (U32 packed + BF16 scales/biases, group 64, affine)
to BF16 safetensors, streamed per-tensor (never holds full model in RAM).

Out: models/edge0-8b-fp16/model.layer{L}.safetensors per layer + shared head.
Run: python scripts/dequant_8b.py [--layers 0,1] (default: all 24)
"""
import os, sys, json
import numpy as np

SRC = r"C:\Users\clint\edge0-intel\models\edge0-8b\model.safetensors"
DST = r"C:\Users\clint\edge0-intel\models\edge0-8b-fp16"
BITS, GROUP = 4, 64

def unpack_affine(w_u32, scales, biases):
    vals_per = 32 // BITS
    mask = (1 << BITS) - 1
    E = w_u32.shape[:-1]
    packed = w_u32.shape[-1]
    inn = packed * vals_per
    w = np.empty(E + (inn,), dtype=np.float32)
    for v in range(vals_per):
        w[..., v::vals_per] = ((w_u32 >> (v * BITS)) & mask).astype(np.float32)
    rep = inn // scales.shape[-1]
    s = np.repeat(scales.astype(np.float32), rep, axis=-1)
    b = np.repeat(biases.astype(np.float32), rep, axis=-1)
    return w * s + b

def main():
    from safetensors.numpy import save_file
    sel = sys.argv[sys.argv.index("--layers") + 1] if "--layers" in sys.argv else "all"
    only = None if sel == "all" else {int(x) for x in sel.split(",")}
    os.makedirs(DST, exist_ok=True)
    names = None  # header read below via safe_open (lazy, per-tensor)
    from safetensors import safe_open
    import torch
    def tonp(t):
        if isinstance(t, torch.Tensor):
            if t.dtype == torch.bfloat16:
                t = t.to(torch.float32)
            return t.numpy()
        return np.asarray(t)
    with safe_open(SRC, framework="pt") as f:
        keys = list(f.keys())
    layers = {}
    for k in keys:
        if ".layers." in k:
            try:
                L = int(k.split(".layers.")[1].split(".")[0])
            except ValueError:
                continue
            if only is not None and L not in only:
                continue
            layers.setdefault(L, []).append(k)
        else:
            layers.setdefault("shared", []).append(k)
    print(f"layers: {sorted(x for x in layers if x!='shared')} + shared({len(layers.get('shared',[]))})", flush=True)
    import re
    with safe_open(SRC, framework="pt") as f:
        for L, ks in sorted(layers.items(), key=lambda kv: (kv[0] == "shared", kv[0])):
            out = {}
            for k in ks:
                a = tonp(f.get_tensor(k))
                if a.dtype == np.uint32 and (k.endswith(".weight")):
                    base = k[: -len(".weight")]
                    s = tonp(f.get_tensor(base + ".scales"))
                    b = tonp(f.get_tensor(base + ".biases"))
                    W = unpack_affine(a, s, b).astype(np.float16)
                    m = re.search(r"mlp\.experts\.(gate_proj|up_proj|down_proj)\.weight$", k)
                    if m is not None and W.ndim == 3 and W.shape[0] == 128:
                        # modeling class wants per-expert keys experts.{i}.{proj}.weight
                        for i in range(W.shape[0]):
                            out[k.replace("mlp.experts.", f"mlp.experts.{i}.")] = W[i]
                    else:
                        out[k] = W
                elif k.endswith((".scales", ".biases")):
                    continue  # folded into weight
                else:
                    out[k] = np.asarray(a)
            save_file(out, os.path.join(DST, f"model.layer{L}.safetensors"))
            n_mb = sum(v.nbytes for v in out.values()) / 1e6
            print(f"wrote layer {L}: {len(out)} tensors {n_mb:.0f} MB", flush=True)

if __name__ == "__main__":
    main()
