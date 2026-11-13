"""Run the real hook body, extracted from the installer, against a sandbox.

The hook only ever runs on Ubuntu inside a kernel postinst, which is the worst
possible place to discover it is broken. This extracts the exact heredoc the
installer writes, points its ESP/template/log at a temp dir, and drives the
three paths that matter:

  success  -> stub rendered, carries the live UUID, no placeholder left
  skip     -> template absent: exit 0, stub untouched, SKIP logged
  error    -> template broken: exit 0, stub untouched, ERROR logged

Exit 0 only if every case behaved. A hook that fails a kernel install wedges
apt, so "exit 0 in every case" is asserted as hard as the render itself.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
INSTALLER = HERE / "00_install_hook.sh"
TEMPLATE = HERE / "grub.cfg.tmpl"
UUID = "58e46179-d777-4203-a807-8794a3fb2351"

results: list[tuple[bool, str]] = []


def check(cond: bool, msg: str) -> None:
    results.append((cond, msg))
    print(("PASS  " if cond else "FAIL  ") + msg)


def posix(p: Path) -> str:
    """sh needs /c/Users/... not C:\\Users\\...  On POSIX this is a no-op."""
    s = p.as_posix()
    if re.match(r"^[A-Za-z]:", s):
        s = "/" + s[0].lower() + s[2:]
    return s


def extract_hook() -> str:
    text = INSTALLER.read_text(encoding="utf-8")
    m = re.search(r"<<'HOOK'\n(.*?)\nHOOK\n", text, re.S)
    if not m:
        raise SystemExit("ERROR: could not find the <<'HOOK' heredoc in the installer")
    return m.group(1) + "\n"


def build_sandbox(root: Path, hook_src: str) -> tuple[Path, Path, Path, Path]:
    esp = root / "esp"
    (esp / "EFI" / "ubuntu").mkdir(parents=True)
    tmpl_dir = root / "etc"
    tmpl_dir.mkdir()
    log = root / "hook.log"

    # a fake findmnt so the hook can read a UUID on any platform
    binp = root / "bin"
    binp.mkdir()
    fake = binp / "findmnt"
    fake.write_text(f"#!/bin/sh\necho {UUID}\n", encoding="utf-8")
    fake.chmod(0o755)

    # point the hook at the sandbox instead of /boot/efi and /etc
    patched = hook_src
    patched = patched.replace("ESP=/boot/efi", f"ESP={posix(esp)}")
    patched = patched.replace("TMPL=/etc/p8-esp-stub/grub.cfg.tmpl",
                              f"TMPL={posix(tmpl_dir / 'grub.cfg.tmpl')}")
    patched = patched.replace("LOG=/var/log/p8-esp-stub.log", f"LOG={posix(log)}")
    patched = patched.replace("VALIDATOR=/etc/p8-esp-stub/esp_validate.py",
                              f"VALIDATOR={posix(tmpl_dir / 'esp_validate.py')}")
    patched = patched.replace("VSTATE=/var/lib/p8-esp-stub/validate-state.json",
                              f"VSTATE={posix(root / 'validate-state.json')}")

    # the validator the hook will call, copied from the project root
    repo = HERE.parent
    for name in ("esp_validate.py", "validate_grub.py"):
        src = repo / name
        if not src.is_file():
            raise SystemExit(f"ERROR: {src} missing - cannot test the validator path")
        shutil.copy(src, tmpl_dir / name)
    hook = root / "hook.sh"
    hook.write_text(patched, encoding="utf-8")
    hook.chmod(0o755)
    return hook, esp, tmpl_dir, log


def run(hook: Path, env_extra: dict[str, str]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.update(env_extra)
    return subprocess.run(["sh", str(hook)], capture_output=True, text=True, env=env)


def main() -> int:
    if shutil.which("sh") is None:
        print("ERROR: no sh on PATH")
        return 2

    hook_src = extract_hook()
    print(f"extracted hook body: {len(hook_src)} chars, "
          f"{hook_src.count(chr(10))} lines")

    # ---------- case 1: success ----------
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        hook, esp, tmpl_dir, log = build_sandbox(root, hook_src)
        shutil.copy(TEMPLATE, tmpl_dir / "grub.cfg.tmpl")

        path_env = f"{posix(root / 'bin')}:{os.environ['PATH']}"
        r = run(hook, {"PATH": path_env})
        if r.stderr.strip():
            print(f"      hook stderr: {r.stderr.strip()[:200]}")
        check(r.returncode == 0, f"success path exits 0 (got {r.returncode})")
        stub = esp / "EFI" / "ubuntu" / "grub.cfg"
        check(stub.is_file(), "success path wrote the stub")
        body = stub.read_text(encoding="utf-8") if stub.is_file() else ""
        check(UUID in body, "stub carries the live UUID")
        check("@P8UUID@" not in body, "no @P8UUID@ placeholder left behind")
        check(body.count("menuentry") == 6, f"stub has 6 menuentries (got {body.count('menuentry')})")
        check(not any(ln.startswith("configfile") for ln in body.splitlines()),
              "no top-level configfile: the statement that hid every entry below it")
        check("bootmgfw.efi" in body, "stub keeps the Windows chainload")
        logtxt = log.read_text(encoding="utf-8") if log.is_file() else ""
        check("OK: stub re-rendered" in logtxt, f"success logged (log={logtxt.strip()[:80]!r})")

        # ---------- case 2: template absent -> skip, untouched, exit 0 ----------
        before = stub.read_bytes() if stub.is_file() else b""
        (tmpl_dir / "grub.cfg.tmpl").unlink()
        r = run(hook, {"PATH": path_env})
        check(r.returncode == 0, f"missing-template path exits 0 (got {r.returncode})")
        check(stub.read_bytes() == before, "missing template leaves the stub untouched")
        logtxt = log.read_text(encoding="utf-8")
        check("SKIP: template" in logtxt, "missing template is logged as SKIP")

        # ---------- case 3: broken template -> error, untouched, exit 0 ----------
        (tmpl_dir / "grub.cfg.tmpl").write_text("menuentry 'x' {\n  linux /nope\n}\n",
                                                encoding="utf-8")
        r = run(hook, {"PATH": path_env})
        check(r.returncode == 0, f"uuid-less template exits 0 (got {r.returncode})")
        check(stub.read_bytes() == before, "uuid-less template leaves the stub untouched")
        logtxt = log.read_text(encoding="utf-8")
        check("ERROR: rendered stub does not contain root UUID" in logtxt,
              "uuid-less template is logged as ERROR")

        # ---------- case 4: no root UUID readable -> error, untouched, exit 0 ----------
        shutil.copy(TEMPLATE, tmpl_dir / "grub.cfg.tmpl")
        fake = root / "bin" / "findmnt"
        fake.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        r = run(hook, {"PATH": path_env})
        check(r.returncode == 0, f"unreadable UUID exits 0 (got {r.returncode})")
        check(stub.read_bytes() == before, "unreadable UUID leaves the stub untouched")
        logtxt = log.read_text(encoding="utf-8")
        check("ERROR: cannot read root UUID" in logtxt, "unreadable UUID is logged as ERROR")

        # ---------- case 5: structurally broken render -> rejected + rolled back ----------
        # findmnt must work again here: case 4 left it failing, and a render that
        # never happens would pass the "untouched" assertion for the wrong reason.
        fake.write_text(f"#!/bin/sh\necho {UUID}\n", encoding="utf-8")
        (tmpl_dir / "grub.cfg.tmpl").write_text(
            "menuentry 'broken' {\n  linux /boot/vmlinuz root=UUID=@P8UUID@\n",
            encoding="utf-8",
        )
        r = run(hook, {"PATH": path_env})
        check(r.returncode == 0, f"broken render exits 0 (got {r.returncode})")
        check(stub.read_bytes() == before,
              "broken render is rolled back - ESP keeps the last valid stub")
        logtxt = log.read_text(encoding="utf-8")
        check("CRITICAL: validator rejected stub" in logtxt,
              "broken render is logged as CRITICAL")
        check("OK: rolled back to previous stub" in logtxt,
              "rollback is logged as OK")

        # ---------- case 6: no ESP -> skip quietly ----------
        shutil.copy(TEMPLATE, tmpl_dir / "grub.cfg.tmpl")
        shutil.rmtree(esp / "EFI" / "ubuntu")
        r = run(hook, {"PATH": path_env})
        check(r.returncode == 0, f"absent ESP exits 0 (got {r.returncode})")
        logtxt = log.read_text(encoding="utf-8")
        check("SKIP: " in logtxt and "absent" in logtxt, "absent ESP is logged as SKIP")

    failed = [m for ok, m in results if not ok]
    print(f"\n{len(results) - len(failed)} passed, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
