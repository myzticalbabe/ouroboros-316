"""2) Expert surgery (same-count only — no router/prerouter retrain):
  clone SRC expert over DST (strengthen), swap A<->B, zero an expert
  (effective prune with neutral router mass; router still routes, gets zeros).

Key layout: model.layers.{L}.mlp.experts.{gate,up,down}_proj.weight
  shaped [num_experts, out, in] (fused per-proj). num_experts stays 128.

Usage:
  python scripts/expert_surgery.py --op clone --layer 5 --src-exp 12 --dst-exp 77
  python scripts/expert_surgery.py --op swap --layer 5 --a 12 --b 77
  python scripts/expert_surgery.py --op zero --layer 5 --dst-exp 77
  [--src DIR] [--out DIR2] (default: in-place copy to models/edge0-8b-surgery)
"""
import os, shutil
import numpy as np

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--op", required=True, choices=["clone", "swap", "zero"])
    ap.add_argument("--layer", type=int, required=True)
    ap.add_argument("--src-exp", type=int, default=-1)
    ap.add_argument("--dst-exp", type=int, default=-1)
    ap.add_argument("--a", type=int, default=-1)
    ap.add_argument("--b", type=int, default=-1)
    ap.add_argument("--src", default=r"C:\Users\clint\edge0-intel\models\edge0-8b-fp16")
    ap.add_argument("--out", default=r"C:\Users\clint\edge0-intel\models\edge0-8b-surgery")
    a = ap.parse_args()
    from safetensors.numpy import save_file, load_file
    if os.path.abspath(a.src) != os.path.abspath(a.out):
        if os.path.exists(a.out):
            print(f"refusing: {a.out} exists (delete or pick another --out)")
            return
        shutil.copytree(a.src, a.out)
    tag = f"model.layers.{a.layer}.mlp.experts."
    touched = 0
    for fn in sorted(os.listdir(a.out)):
        if not fn.endswith(".safetensors"):
            continue
        p = os.path.join(a.out, fn)
        d = dict(load_file(p))
        changed = False
        for k in [k for k in d if k.startswith(tag) and k.endswith(".weight")]:
            W = np.asarray(d[k])
            if a.op == "clone":
                W[a.dst_exp] = W[a.src_exp]; changed = True
            elif a.op == "swap":
                W[a.a], W[a.b] = W[a.b].copy(), W[a.a].copy(); changed = True
            elif a.op == "zero":
                W[a.dst_exp] = 0; changed = True
            d[k] = W
            touched += 1
        if changed:
            save_file(d, p)
    print(f"{a.op} done, {touched} expert matrices touched in layer {a.layer} -> {a.out}")
    print("EVAL: perplexity + task suite before/after; router mass unchanged by design.")

if __name__ == "__main__":
    main()
