import sys
sys.path.insert(0, r"C:\Users\clint\edge0-intel\scripts")
from gguf_abliterate import parse_kv
from gguf import GGUFReader
for path in [r"C:\Users\clint\edge0-intel\models\Ling-3.0-tiny-abliterated-APEX-I-Compact.gguf",
             r"C:\Users\clint\edge0-intel\models\ling-roundtrip.gguf"]:
    r = GGUFReader(path)
    print("==", path.split("\\")[-1])
    for k in ["tokenizer.ggml.tokens", "tokenizer.ggml.token_type", "tokenizer.ggml.merges"]:
        f = r.fields.get(k)
        if f is None:
            print(" ", k, "MISSING"); continue
        p = parse_kv(f.parts)
        v = p[2][1]
        print(" ", k, len(v), "first_len", len(v[0]) if isinstance(v[0], bytes) else v[0])
