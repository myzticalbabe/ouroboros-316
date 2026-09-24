"""Backfill build sidecars for pre-sidecar builds (known params only)."""
import hashlib
import json
import os
import time

BASE = r"C:\Users\clint\edge0-intel\models"
KNOWN = {
    "ling-abl-s05.gguf": {
        "src": os.path.join(BASE, "Ling-3.0-tiny-abliterated-APEX-I-Compact.gguf"),
        "refusal_dir": os.path.join(BASE, "edge0-8b-fp16", "refusal_dir.npy"),
        "strength": 0.5,
        "targets": ["attn_output.weight", "ffn_down_exps.weight",
                    "ffn_down_shexp.weight"],
        "layers": "all",
    },
}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


for fn, meta in KNOWN.items():
    dst = os.path.join(BASE, fn)
    if not os.path.exists(dst):
        print(f"SKIP missing {fn}")
        continue
    side = dst + ".build.json"
    if os.path.exists(side):
        print(f"exists {side}")
        continue
    rec = dict(meta)
    rec["dst"] = dst
    rdir = meta.get("refusal_dir", "")
    rec["refusal_sha256"] = sha(rdir) if rdir and os.path.exists(rdir) else None
    rec["edited"] = "unknown-pre-sidecar"
    rec["out_bytes"] = os.path.getsize(dst)
    rec["time"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    rec["backfilled"] = True
    json.dump(rec, open(side, "w"), indent=1)
    print(f"wrote {side}")
