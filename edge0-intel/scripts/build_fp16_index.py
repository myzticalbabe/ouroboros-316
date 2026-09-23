"""Assemble models/edge0-8b-fp16/ into a loadable checkpoint:
copy config (quantization_config stripped) + tokenizer files from the
int4 parent, write model.safetensors.index.json over per-layer shards.
"""
import json, os, shutil

PARENT = r"C:\Users\clint\edge0-intel\models\edge0-8b"
FP16 = r"C:\Users\clint\edge0-intel\models\edge0-8b-fp16"

for f in ["config.json", "tokenizer.json", "tokenizer_config.json",
          "special_tokens_map.json", "generation_config.json", "chat_template.jinja"]:
    s = os.path.join(PARENT, f)
    if os.path.exists(s):
        shutil.copy(s, os.path.join(FP16, f))

with open(os.path.join(FP16, "config.json")) as fh:
    cfg = json.load(fh)
cfg.pop("quantization_config", None)
cfg["torch_dtype"] = "float16"
with open(os.path.join(FP16, "config.json"), "w") as fh:
    json.dump(cfg, fh, indent=2)

from safetensors import safe_open
weight_map, total = {}, 0
for fn in sorted(os.listdir(FP16)):
    if not fn.endswith(".safetensors"):
        continue
    with safe_open(os.path.join(FP16, fn), framework="np") as f:
        for k in f.keys():
            weight_map[k] = fn
            total += 1
with open(os.path.join(FP16, "model.safetensors.index.json"), "w") as fh:
    json.dump({"metadata": {"total_size": total}, "weight_map": weight_map}, fh)
print(f"indexed {total} tensors over fp16 dir")
