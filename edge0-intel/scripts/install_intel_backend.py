"""Install Intel backend overlay into _upstream checkout + patch selector."""
from __future__ import annotations
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "edge0" / "backends" / "intel"
DST = ROOT / "_upstream" / "src" / "edge0" / "backends" / "intel"
INIT = ROOT / "_upstream" / "src" / "edge0" / "backends" / "__init__.py"

PATCH = '''elif _BACKEND == "intel":
    from edge0.backends.intel.backend import (  # noqa: F401
        BackendImpl,
        core,
        io,
        nn,
        quant,
    )
'''

def main() -> int:
    if not SRC.exists():
        print(f"missing {SRC}", file=sys.stderr)
        return 1
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST)
    print(f"copied {SRC} -> {DST}")
    text = INIT.read_text()
    if '"intel"' not in text:
        text = text.replace(
            'elif _BACKEND == "cuda":',
            PATCH + 'elif _BACKEND == "cuda":')
        text = text.replace(
            'f"unknown backend {_BACKEND!r}; available: mlx")',
            'f"unknown backend {_BACKEND!r}; available: mlx, intel")')
        INIT.write_text(text)
        print("patched backends/__init__.py for EDGE0_BACKEND=intel")
    else:
        print("already patched")
    print("done. test: set EDGE0_BACKEND=intel and run tests/test_intel_backend.py")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
