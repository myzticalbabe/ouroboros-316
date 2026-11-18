"""Version discovery and interpreter resolution."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional

# Canonical version tags used throughout the runtime.
VERSIONS: List[str] = [
    "3.8", "3.9", "3.10", "3.11", "3.12", "3.13", "3.14", "3.14t",
    "3.15", "3.15t", "3.16", "3.16t",
]


@dataclass
class Interpreter:
    version: str
    path: str
    free_threaded: bool = False

    def run(self, args, **kw):
        return subprocess.run([self.path, *args], **kw)


def _is_free_threaded(path: str) -> bool:
    try:
        out = subprocess.run(
            [path, "-c", "import sys; print(getattr(sys, '_is_gil_enabled', lambda: True)())"],
            capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip().lower() == "false"
    except Exception:
        return False


def discover() -> Dict[str, Interpreter]:
    """Discover available Python interpreters via the py launcher and direct paths."""
    found: Dict[str, Interpreter] = {}

    # 1. py launcher
    if shutil.which("py"):
        try:
            out = subprocess.run(["py", "-0p"], capture_output=True, text=True, timeout=15)
            for line in out.stdout.splitlines():
                line = line.strip()
                if not line or ":" not in line:
                    continue
                # format: " -V:3.14          C:\...\python.exe"
                import re
                m = re.match(r"^-V:(\S+)\s+\*?\s*(.+)$", line.strip())
                if not m:
                    continue
                tag = m.group(1).strip()
                path = m.group(2).strip()
                if not path.lower().endswith(".exe"):
                    continue
                # normalize tag -> version
                ver = _normalize_tag(tag)
                if ver is None:
                    continue
                ft = _is_free_threaded(path)
                # prefer free-threaded for t tags
                if ver not in found or (ver.endswith("t") and ft):
                    found[ver] = Interpreter(version=ver, path=path, free_threaded=ft)
        except Exception:
            pass

    # 2. direct well-known paths
    direct = [
        r"C:\Program Files\Python36\python.exe",
        r"C:\Program Files\Python37\python.exe",
        r"C:\Users\clint\AppData\Local\Programs\Python\Python314\python.exe",
        r"C:\Users\clint\AppData\Local\Programs\Python\Python315\python.exe",
        r"C:\Azazael\.venvs\py316t\Scripts\python.exe",
        r"C:\Azazael\.venvs\py315t\Scripts\python.exe",
    ]
    for p in direct:
        if not _exists(p):
            continue
        # determine version
        try:
            out = subprocess.run([p, "--version"], capture_output=True, text=True, timeout=10)
            verstr = (out.stdout or out.stderr).strip()  # Python 3.x.y
            parts = verstr.split()
            if len(parts) < 2:
                continue
            v = parts[1]  # 3.14.7
            major_minor = ".".join(v.split(".")[:2])
            ft = _is_free_threaded(p)
            tag = major_minor + ("t" if ft else "")
            if tag not in found:
                found[tag] = Interpreter(version=tag, path=p, free_threaded=ft)
        except Exception:
            pass

    return found


def _exists(p: str) -> bool:
    import os
    return os.path.isfile(p)


def _normalize_tag(tag: str) -> Optional[str]:
    # tag like "3.14", "3.14t", "Astral/CPython3.14.3", "3.15t"
    t = tag.strip()
    if t.startswith("Astral/"):
        # CPython3.14.3 -> 3.14 (or .3 -> minor)
        import re
        m = re.search(r"CPython(\d+)\.(\d+)", t)
        if not m:
            return None
        return f"{m.group(1)}.{m.group(2)}"
    # 3.14 or 3.14t
    if t and t[0].isdigit():
        return t
    return None


def resolve(version: str) -> Optional[Interpreter]:
    d = discover()
    if version in d:
        return d[version]
    # try without t
    if version.endswith("t") and version[:-1] in d:
        return d[version[:-1]]
    return None


def available_versions() -> List[str]:
    return sorted(discover().keys())


if __name__ == "__main__":
    d = discover()
    for v, it in sorted(d.items()):
        print(f"{v}: {it.path}  free_threaded={it.free_threaded}")
    print("json:", json.dumps({v: it.path for v, it in d.items()}, indent=2))