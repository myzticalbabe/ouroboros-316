import json, struct
SRC = r"C:\Users\clint\edge0-intel\models\edge0-8b\model.safetensors"
with open(SRC, "rb") as f:
    h = json.loads(f.read(struct.unpack("<Q", f.read(8))[0]))
h.pop("__metadata__", None)
ks = [k for k in h if ".layers.3." in k and "shared" in k]
for k in sorted(ks)[:8]:
    print(" ", k, h[k]["dtype"], h[k]["shape"])
c = json.load(open(r"C:\Users\clint\edge0-intel\models\edge0-8b\config.json"))
print("num_experts:", c.get("num_experts"), "topk:", c.get("num_experts_per_tok"))
