import sys
from gguf import GGUFReader
p = r"C:\Users\clint\edge0-intel\models\Ling-3.0-tiny-abliterated-APEX-I-Compact.gguf"
r = GGUFReader(p)
names = [t.name for t in r.tensors]
exp = sorted(t for t in names if "expert" in t.lower())
print("tensors:", len(names), "expert tensors:", len(exp))
for t in exp[:6]:
    print(" ", t)
lyrs = sorted({t.split(".")[2] for t in exp if t.startswith("blk.")})
print("moe blks:", lyrs[:6], "... total", len(lyrs))
