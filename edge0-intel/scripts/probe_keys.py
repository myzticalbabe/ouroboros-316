import json, struct
SRC = r"C:\Users\clint\edge0-intel\models\edge0-8b\model.safetensors"
with open(SRC, "rb") as f:
    h = json.loads(f.read(struct.unpack("<Q", f.read(8))[0]))
h.pop("__metadata__", None)
ks = [k for k in h if ".layers.3." in k and "expert" in k.lower()]
print("layer3 expert-ish keys:", len(ks))
for k in sorted(ks)[:10]:
    print(" ", k, h[k]["dtype"], h[k]["shape"])
