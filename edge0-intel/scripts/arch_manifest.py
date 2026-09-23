"""P0 arch manifest: assert identical dims across all donor/stock dirs.
Fails LOUD before any swap/merge runs. Usage:
  python scripts/arch_manifest.py --dirs models/edge0-8b-fp16 [donor...]
"""
import json, os, struct
import numpy as np

KEYS = ["hidden_size", "num_hidden_layers", "num_attention_heads",
        "num_key_value_heads", "vocab_size", "num_experts",
        "num_experts_per_tok", "intermediate_size"]


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="+", required=True)
    a = ap.parse_args()
    cfgs = {}
    for d in a.dirs:
        with open(os.path.join(d, "config.json")) as fh:
            c = json.load(fh)
        cfgs[d] = {k: c.get(k) for k in KEYS}
    base = cfgs[a.dirs[0]]
    ok = True
    for d, c in cfgs.items():
        for k in KEYS:
            if c[k] != base[k]:
                print(f"MISMATCH {d} {k}: {c[k]} != {base[k]}")
                ok = False
    print("config manifest:", "MATCH" if ok else "FAIL")
    # expert tensor shape parity on a MoE layer (early layers may be dense-first)
    for d in a.dirs:
        idx = json.load(open(os.path.join(d, "model.safetensors.index.json")))["weight_map"]
        per_layer = {}
        for k in idx:
            if ".mlp.experts." in k and k.endswith(".weight"):
                try:
                    L = int(k.split(".layers.")[1].split(".")[0])
                except ValueError:
                    continue
                per_layer[L] = per_layer.get(L, 0) + 1
        moe_layers = sorted(per_layer)
        eg = next((k for k in sorted(idx) if ".mlp.experts." in k and k.endswith(".weight")), None)
        print(f"{d}: moe_layers={len(moe_layers)} (eg {moe_layers[:3]}), "
              f"keys/layer={per_layer.get(moe_layers[0]) if moe_layers else 0}, eg_key={eg}")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
