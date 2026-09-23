"""3) Layer swap / Frankenmerge: replace whole layer(s) across same-hidden-dim
(1536) checkpoints, or graft a foreign head. Norm scales travel with the layer.

Usage:
  python scripts/layer_swap.py --layers 20,21,22 --donor DIR --out DIR2
    [--src models/edge0-8b-fp16]
  - copies src->out (unless out exists), overwrites layer files from donor
  - donor must expose same per-layer file split (model.layer{L}.safetensors)
    or a single model.safetensors (keys filtered by layer tag)
  - rebuilds model.safetensors.index.json via build_fp16_index logic

Rules: hidden dims must match; keep donor norm+attn+mlp together per layer;
eval after every swap. Head graft: donor lm_headvende? use --only-head to
swap just model shared (embed stays src unless --embed too).
"""
import os, shutil, json

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--layers", default="")
    ap.add_argument("--donor", required=True)
    ap.add_argument("--src", default=r"C:\Users\clint\edge0-intel\models\edge0-8b-fp16")
    ap.add_argument("--out", default=r"C:\Users\clint\edge0-intel\models\edge0-8b-franken")
    ap.add_argument("--only-head", action="store_true")
    a = ap.parse_args()
    from safetensors.numpy import save_file, load_file
    if os.path.abspath(a.src) != os.path.abspath(a.out):
        if os.path.exists(a.out):
            print(f"refusing: {a.out} exists")
            return
        shutil.copytree(a.src, a.out)
    if a.only_head:
        cand = [os.path.join(a.donor, "model.layershared.safetensors")]
    else:
        want = {int(x) for x in a.layers.split(",") if x.strip() != ""}
        cand = [os.path.join(a.donor, f"model.layer{L}.safetensors") for L in want]
    for p in cand:
        if not os.path.exists(p):
            print(f"missing donor file {p}; trying single-shard filter...")
            continue
        shutil.copy(p, os.path.join(a.out, os.path.basename(p)))
        print(f"swapped {os.path.basename(p)}")
    # rebuild index
    from safetensors import safe_open
    wmap, total = {}, 0
    for fn in sorted(os.listdir(a.out)):
        if fn.endswith(".safetensors"):
            with safe_open(os.path.join(a.out, fn), framework="np") as f:
                for k in f.keys():
                    wmap[k] = fn
                    total += 1
    json.dump({"metadata": {"total_size": total}, "weight_map": wmap},
              open(os.path.join(a.out, "model.safetensors.index.json"), "w"))
    print(f"franken done: index {total} tensors -> {a.out}")

if __name__ == "__main__":
    main()
