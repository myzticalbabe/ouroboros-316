from gguf import GGUFReader
import sys
sys.path.insert(0, r"C:\Users\clint\edge0-intel\scripts")
from gguf_abliterate import parse_kv
for path in [r"C:\Users\clint\edge0-intel\models\Ling-3.0-tiny-abliterated-APEX-I-Compact.gguf",
             r"C:\Users\clint\edge0-intel\models\ling-roundtrip.gguf"]:
    r = GGUFReader(path)
    print("==", path.split("\\")[-1])
    for k in ["tokenizer.ggml.tokens", "tokenizer.ggml.scores",
              "tokenizer.ggml.token_type", "tokenizer.ggml.merges"]:
        if k in r.fields:
            p = parse_kv(r.fields[k].parts)
            v = p[2][1] if p[1] == 9 else p[2]
            print(" ", k, len(v))
        else:
            print(" ", k, "MISSING")
