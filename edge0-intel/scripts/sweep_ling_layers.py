"""Overnight per-layer ablation map for Ling (visible-console driver).

For each blk i: build layer-i-only ablation (s=1.0, 8B refusal dir),
serve :8091, eval_full N=100+20, kill server. Result: per-layer ΔSVI =
the importance map that directs expert-level hyper-mutation.
~12 min/layer. Logs everything to stdout (run under RUN_*.bat).

Usage: python scripts/sweep_ling_layers.py [--layers 0-5] [--force]
  --force rebuilds even if the layer GGUF already exists.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

BASE = r"C:\Users\clint\edge0-intel"
PY = r"C:\Users\clint\AppData\Local\Programs\Python\Python314\python3.14t.exe"
PY_STD = r"C:\Users\clint\AppData\Local\Programs\Python\Python314\python.exe"
SERVER = r"C:\Users\clint\llama-server\bin\llama-b10964-cpu\llama-server.exe"
SRC = os.path.join(BASE, "models", "Ling-3.0-tiny-abliterated-APEX-I-Compact.gguf")
RDIR = os.path.join(BASE, "models", "edge0-8b-fp16", "refusal_dir.npy")
PORT = 8091


def say(m):
    print(m, flush=True)


def run(cmd):
    return subprocess.run(cmd, capture_output=False).returncode


def wait_health(timeout=180):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            r = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=5)
            if r.status == 200:
                return True
        except Exception:
            pass
        time.sleep(5)
    return False


def kill_servers():
    subprocess.run(["taskkill", "/IM", "llama-server.exe", "/F"],
                   capture_output=True)
    time.sleep(4)


def layers_of_src():
    from gguf import GGUFReader
    import re
    r = GGUFReader(SRC)
    idx = set()
    for t in r.tensors:
        m = re.search(r"blk\.(\d+)\.", t.name)
        if m:
            idx.add(int(m.group(1)))
    return sorted(idx)


def parse_spec(spec, all_layers):
    if spec in ("all", ""):
        return all_layers
    out = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            out.update(range(int(lo), int(hi) + 1))
        elif part != "":
            out.add(int(part))
    return sorted(i for i in out if i in all_layers)


def main():
    args = sys.argv[1:]
    spec = "all"
    force = False
    for i, x in enumerate(args):
        if x == "--layers" and i + 1 < len(args):
            spec = args[i + 1]
        if x == "--force":
            force = True
    say(f"OBSERVE script=sweep_ling_layers spec={spec} force={force}")
    layers = parse_spec(spec, layers_of_src())
    say(f"layers to sweep: {layers}")
    t0 = time.time()
    for n, i in enumerate(layers):
        dst = os.path.join(BASE, "models", f"ling-layer-{i:02d}.gguf")
        tag = f"ling-L{i:02d}"
        say(f"\n=== [{n+1}/{len(layers)}] layer {i} -> {os.path.basename(dst)} ===")
        if not (os.path.exists(dst) and not force):
            rc = run([PY, os.path.join(BASE, "scripts", "gguf_abliterate.py"),
                      "--src", SRC, "--dst", dst, "--dir", RDIR,
                      "--strength", "1.0",
                      "--targets", "attn_output.weight,ffn_down_exps.weight,ffn_down_shexp.weight",
                      "--layers", str(i)])
            if rc != 0:
                say(f"BUILD FAILED layer {i} rc={rc}; continuing")
                continue
        else:
            say(f"reuse existing {os.path.basename(dst)}")
        kill_servers()
        srv = subprocess.Popen([SERVER, "-m", dst, "--host", "127.0.0.1",
                                "--port", str(PORT), "-c", "2048",
                                "-t", "8", "-ngl", "0"])
        if not wait_health():
            say(f"SERVE FAILED layer {i}; killing and continuing")
            kill_servers()
            continue
        say(f"serving :{PORT}, evaluating {tag}...")
        rc = run([PY_STD, os.path.join(BASE, "scripts", "eval_full.py"),
                  "--url", f"http://127.0.0.1:{PORT}",
                  "--model", tag, "--tag", tag, "--harm", "100"])
        say(f"eval {tag} rc={rc}")
        kill_servers()
    say(f"\nSWEEP DONE wall={(time.time()-t0)/3600:.1f}h")


if __name__ == "__main__":
    main()
