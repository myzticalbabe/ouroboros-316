"""Integrity baseline: detect unrecorded modification of foundry scripts.

The INCIDENT file records external modification with an unidentified writer.
This tool makes recurrence DETECTABLE: `record` stores sha256 per script;
`check` fails loudly on any drift. Workflow: run `record` after every
reviewed commit; run `check` before consequential runs (sweeps, serves).

Usage:
  python scripts/integrity.py record   # (re)baseline tracked files
  python scripts/integrity.py check    # exit 0 clean, 1 drift (lists files)
  python scripts/integrity.py sources  # hash large source artifacts once
                                       # (models, refusal dirs) for provenance
"""
import hashlib
import json
import os
import sys

BASE = r"C:\Users\clint\edge0-intel"
STATE = os.path.join(BASE, "integrity.json")
SOURCES = os.path.join(BASE, "SOURCES.sha256")

TRACKED_EXTS = (".py", ".bat", ".md", ".json")
TRACKED_DIRS = ("scripts", "tests")
TRACKED_FILES = ("HANDOFF.md", "TECHNIQUES.md", "SVI_SPEC.md", "RAM_RUNBOOK.md",
                 "STRATUM_THESIS.md", "SESSION_2026-09-23.md", "SVI_SPEC.md",
                 "EMERGENT_GAP_AUDIT.md", "TOOL_GAP_AUDIT.md",
                 "PEBBLES_BAMBAM.md", "RUN_GEMMA_SURGERY.bat",
                 "RUN_LING_SWEEP.bat", "integrity.json")
SKIP_DIRS = {"__pycache__", "graft", ".graph", ".cache"}

SOURCE_ARTIFACTS = [
    os.path.join(BASE, "models", "Ling-3.0-tiny-abliterated-APEX-I-Compact.gguf"),
    os.path.join(BASE, "models", "edge0-8b-fp16", "refusal_dir.npy"),
    os.path.join(BASE, "models", "gemma-4-e4b-abliterated", "refusal_dir.npy"),
    r"C:\Users\clint\.lmstudio\models\lmstudio-community\gemma-4-E4B-it-GGUF\gemma-4-E4B-it-Q4_K_M.gguf",
    r"C:\Users\clint\llama-server\models\Spark-X2.5-4B\Spark-X2.5-4B-Q4_K_M.gguf",
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def collect():
    out = {}
    for d in TRACKED_DIRS:
        root = os.path.join(BASE, d)
        for dirpath, dirs, files in os.walk(root):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
            for fn in sorted(files):
                if fn.endswith(TRACKED_EXTS):
                    p = os.path.join(dirpath, fn)
                    out[os.path.relpath(p, BASE)] = sha256_file(p)
    for fn in TRACKED_FILES:
        p = os.path.join(BASE, fn)
        if os.path.exists(p):
            out[fn] = sha256_file(p)
    return out


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("record", "check", "sources"):
        print(__doc__)
        return 2
    if sys.argv[1] == "record":
        state = collect()
        json.dump(state, open(STATE, "w"), indent=1)
        print(f"baselined {len(state)} files -> {STATE}")
        return 0
    if sys.argv[1] == "check":
        if not os.path.exists(STATE):
            print("no baseline; run `record` first")
            return 2
        base = json.load(open(STATE))
        now = collect()
        drift = [k for k in base if base[k] != now.get(k, None)]
        new = [k for k in now if k not in base]
        gone = [k for k in base if k not in now]
        if drift or gone:
            print(f"DRIFT: {len(drift)} modified, {len(gone)} missing")
            for k in drift[:20] + gone[:10]:
                print(f"  {k}")
            return 1
        print(f"clean: {len(now)} files match ({len(new)} new untracked)")
        return 0
    lines = []
    for p in SOURCE_ARTIFACTS:
        if os.path.exists(p):
            lines.append(f"{sha256_file(p)}  {p}")
            print(f"hashed {os.path.basename(p)}")
        else:
            print(f"MISSING {p}")
    open(SOURCES, "w").write("\n".join(lines) + "\n")
    print(f"wrote {SOURCES}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
