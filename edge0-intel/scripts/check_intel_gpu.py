"""Check Intel GPU stack on Windows + WSL (Arc 140T path)."""
from __future__ import annotations
import subprocess, glob, os, platform

def run(cmd, **kw):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=8, **kw)
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return f"<unavailable: {e}>"

def main():
    print(f"os={platform.system()} {platform.release()}")
    print("--- Windows GPU ---")
    try:
        import subprocess as sp
        r = sp.run(["powershell", "-NoProfile", "-Command",
            "Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM | Format-Table -AutoSize"],
            capture_output=True, text=True, timeout=10)
        print(r.stdout.strip() or "(no output)")
    except Exception as e:
        print(f"(skip: {e})")
    print("--- WSL probe ---")
    print(run(["wsl", "-d", "Ubuntu-26.04", "--", "bash", "-lc",
        "echo kernel:$(uname -r); echo dri:$(ls /dev/dri 2>&1); "
        "clinfo -l 2>&1 | head -5; python3 -c 'import torch; print(torch.__version__, hasattr(torch,\"xpu\"))' 2>&1 | head -3"]))
    print("--- local python torch ---")
    try:
        import torch
        print(f"torch={torch.__version__} xpu={torch.xpu.is_available() if hasattr(torch,'xpu') else False}")
    except Exception as e:
        print(f"torch missing ({e}) -> numpy CPU path still works")
    print(f"ONEAPI_DEVICE_SELECTOR={os.environ.get('ONEAPI_DEVICE_SELECTOR','(unset)')}")

if __name__ == "__main__":
    main()
