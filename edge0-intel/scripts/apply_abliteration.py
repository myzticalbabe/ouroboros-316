"""1) Abliteration: orthogonalize refusal direction out of residual-writing
projections (o_proj attention out + expert down_proj), ZeroFuse-style.

Usage:
  a) collect direction (needs running forward):
       python scripts/collect_refusal_dir.py --out refusal_dir.npy
  b) apply:
       python scripts/apply_abliteration.py --dir refusal_dir.npy
         --targets o_proj,down_proj [--strength 1.0] [--out models/edge0-8b-abliterated]

Math: for each target weight W (out,in): W -= s * (r_hat @ (r_hat.T @ W))
i.e. remove the component that writes along refusal unit vector r_hat.
Direct edit, zero inference overhead, no retrain. Eval refusal rate before/after.
"""
import os, sys
import numpy as np

def abliterate_matrix(W: np.ndarray, r: np.ndarray, strength: float = 1.0) -> np.ndarray:
    """Remove refusal component from what W writes to the residual stream.

    r lives in residual space (dim == W.shape[0]); output-side projection:
    W' = W - s * outer(r_hat, W.T @ r_hat), so r_hat @ W' == 0.
    Raises ValueError on dim mismatch (caller skips those targets).
    """
    W = W.astype(np.float32)
    r = r.astype(np.float32)
    if W.shape[0] != r.shape[0]:
        raise ValueError(f"out dim {W.shape[0]} != refusal dim {r.shape[0]}")
    r_hat = r / (np.linalg.norm(r) + 1e-12)
    return (W - strength * np.outer(r_hat, (W.T @ r_hat))).astype(W.dtype)

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="refusal direction .npy (hidden dim)")
    ap.add_argument("--src", default=r"C:\Users\clint\edge0-intel\models\edge0-8b-fp16")
    ap.add_argument("--out", default=r"C:\Users\clint\edge0-intel\models\edge0-8b-abliterated")
    ap.add_argument("--targets", default="o_proj,down_proj")
    ap.add_argument("--strength", type=float, default=1.0)
    ap.add_argument("--layers", default="all")
    a = ap.parse_args()
    from safetensors.numpy import save_file, load_file
    r = np.load(a.dir)
    only = None if a.layers == "all" else {int(x) for x in a.layers.split(",")}
    tgts = set(a.targets.split(","))
    os.makedirs(a.out, exist_ok=True)
    import shutil
    for fn in sorted(os.listdir(a.src)):
        if not fn.endswith(".safetensors"):
            s, o = os.path.join(a.src, fn), os.path.join(a.out, fn)
            if os.path.isfile(s) and not os.path.exists(o):
                shutil.copy(s, o)
    print("configs/tokenizer/index copied", flush=True)
    n = 0
    for fn in sorted(os.listdir(a.src)):
        if not fn.endswith(".safetensors"):
            continue
        d = load_file(os.path.join(a.src, fn))
        out = {}
        for k, v in d.items():
            hit = any(t in k for t in tgts) and k.endswith(".weight")
            if hit:
                L = int(k.split(".layers.")[1].split(".")[0]) if ".layers." in k else -1
                if only is None or L in only:
                    try:
                        v = abliterate_matrix(np.asarray(v), r, a.strength)
                        n += 1
                    except ValueError as e:
                        print(f"skip {k}: {e}", flush=True)
            out[k] = v
        save_file(out, os.path.join(a.out, fn))
        print(f"{fn}: edited {n} so far", flush=True)
    print(f"done: {n} matrices abliterated -> {a.out}")

if __name__ == "__main__":
    main()
