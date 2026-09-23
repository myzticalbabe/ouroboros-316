import sys
from gguf import GGUFReader
r = GGUFReader(r"C:\Users\clint\edge0-intel\models\Ling-3.0-tiny-abliterated-APEX-I-Compact.gguf")
out = open(r"C:\Users\clint\edge0-intel\parts2.txt", "w")
for k, v in r.fields.items():
    if k in ("tokenizer.ggml.tokens", "bailingmoe3.attention.head_count_kv",
             "tokenizer.ggml.merges", "tokenizer.ggml.token_type"):
        out.write(k + " " + str([(p.shape, str(p.dtype)) for p in v.parts]) + "\n")
out.close()
print("wrote")
