#!/usr/bin/env python3
"""Validate the live ESP GRUB stub, but only when it has actually changed.

Why a hash gate: the ESP stub is rewritten by three different things -- the
Windows-side scripts, `grub-install` during an upgrade, and the zzz-p8-esp-stub
kernel hook. Re-validating identical bytes on every poll is noise that trains
you to ignore the output, so the check records the hash it last approved and
speaks up only when the file differs from that.

Exit codes are the contract:
  0  unchanged since last approval, or changed and valid
  1  changed and INVALID -- the ESP now holds a stub that will misboot
  2  could not check (no file, unreadable, validator missing)

2 is not a pass. A stub nobody could read is a stub nobody approved.

Usage:
  esp_validate.py /boot/efi/EFI/ubuntu/grub.cfg
  esp_validate.py U:/EFI/ubuntu/grub.cfg --state %LOCALAPPDATA%/esp_state.json
  esp_validate.py /boot/efi/EFI/ubuntu/grub.cfg --watch 60
  esp_validate.py /boot/efi/EFI/ubuntu/grub.cfg --force
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path


def load_validator():
    """Import validate_grub.py sitting next to this file."""
    here = Path(__file__).resolve().parent
    target = here / "validate_grub.py"
    if not target.is_file():
        raise SystemExit(f"ERROR: validator not found next to esp_validate.py: {target}")
    spec = importlib.util.spec_from_file_location("validate_grub_local", target)
    if spec is None or spec.loader is None:
        raise SystemExit(f"ERROR: cannot load {target}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def read_state(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def write_state(path: Path, payload: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"WARN: could not write state {path}: {exc}")


def validate_once(target: Path, state_path: Path, force: bool) -> int:
    if not target.is_file():
        print(f"ERROR: no stub at {target} - nothing approved")
        return 2
    try:
        digest = sha256(target)
    except OSError as exc:
        print(f"ERROR: cannot hash {target}: {exc}")
        return 2

    state = read_state(state_path)
    if not force and state.get("sha256") == digest and state.get("ok") is True:
        print(f"UNCHANGED {target} sha256={digest[:16]}... approved {state.get('validated_at', '?')}")
        return 0

    reason = "forced" if force else ("never checked" if not state else "content changed")
    print(f"CHANGED {target} sha256={digest[:16]}... ({reason})")

    mod = load_validator()
    try:
        errors = mod.check(target)
    except Exception as exc:  # a validator that cannot run is not an approval
        print(f"ERROR: validator raised {type(exc).__name__}: {exc}")
        write_state(state_path, {"path": str(target), "sha256": digest, "ok": False,
                                 "validated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                 "reason": f"validator error: {exc}"})
        return 2

    ok = not errors
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    if ok:
        print(f"VALID   {target} {target.stat().st_size} bytes")
    else:
        for err in errors:
            print(f"  FAIL {err}")
        print(f"INVALID {target} - {len(errors)} structural defect(s)")

    write_state(state_path, {"path": str(target), "sha256": digest, "ok": ok,
                             "validated_at": stamp, "reason": reason,
                             "errors": errors[:20]})
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate the ESP GRUB stub when it changes")
    ap.add_argument("stub", help="path to the ESP stub, e.g. /boot/efi/EFI/ubuntu/grub.cfg")
    ap.add_argument("--state", default=None, help="state file remembering the last approved hash")
    ap.add_argument("--force", action="store_true", help="validate even if unchanged")
    ap.add_argument("--watch", type=int, metavar="SECONDS", default=0,
                    help="poll forever and validate on every change")
    args = ap.parse_args()

    target = Path(args.stub)
    state_path = Path(args.state) if args.state else target.parent / ".esp_validate_state.json"

    if args.watch <= 0:
        return validate_once(target, state_path, args.force)

    print(f"watching {target} every {args.watch}s (Ctrl-C to stop)")
    last_verdict = 0
    first_pass = True
    try:
        while True:
            last_verdict = validate_once(target, state_path, args.force and first_pass)
            first_pass = False
            time.sleep(args.watch)
    except KeyboardInterrupt:
        print("stopped")
        return last_verdict


if __name__ == "__main__":
    sys.exit(main())
