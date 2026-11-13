"""Regression test for the exact defect that survived twelve sessions.

The v4 stub (and the 840-byte stub in Redo-GrubRecovery.ps1) ran

    configfile ($root)/boot/grub/grub.cfg

at top level, before it defined any menuentry. GRUB's `configfile` REPLACES the
running configuration, so the Ubuntu entries written below it were never
displayed and the visible menu was the distro's own grub.cfg. Static brace
balance passed every time; nothing checked the ORDER of statements.

This test fails if any `configfile` is executed at top level, or before the
first menuentry. It also fails if the default entry (index 0) is not a direct
kernel boot -- the default must not depend on another file being correct.
"""
import re
import sys
from pathlib import Path

STUB = Path(__file__).with_name("grub_menu_v5.cfg")


def top_level_configfile(text: str) -> list[int]:
    """Line numbers of configfile calls that run outside a menuentry body."""
    hits = []
    depth = 0
    in_entry = False
    for n, line in enumerate(text.splitlines(), 1):
        code = line.split("#", 1)[0]
        if re.match(r"\s*menuentry\b", code):
            in_entry = True
        if not in_entry and re.search(r"(^|\s)configfile(\s|$)", code):
            hits.append(n)
        depth += code.count("{") - code.count("}")
        if in_entry and depth <= 0:
            in_entry = False
            depth = 0
    return hits


def entries(text: str) -> list[tuple[str, str]]:
    out = []
    for m in re.finditer(r"^\s*menuentry\s+'([^']*)'\s*\{(.*?)^\s*\}", text, re.M | re.S):
        out.append((m.group(1), m.group(2)))
    return out


def functions(text: str) -> dict[str, str]:
    out = {}
    for m in re.finditer(r"^\s*function\s+(\w+)\s*\{(.*?)^\s*\}", text, re.M | re.S):
        out[m.group(1)] = m.group(2)
    return out


def main() -> int:
    if not STUB.exists():
        print(f"FAIL: {STUB} does not exist")
        return 2
    text = STUB.read_text(encoding="utf-8")
    errs = []

    bad = top_level_configfile(text)
    if bad:
        errs.append(f"top-level configfile at line(s) {bad}: this replaces the menu "
                    f"and hides every entry below it (the twelve-session defect)")

    found = entries(text)
    if len(found) < 4:
        errs.append(f"only {len(found)} menuentries - a menu this short cannot carry "
                    f"Ubuntu + fallback + diagnostics + Windows")

    # Comments explain the defect and therefore name it; strip them first or the
    # word 'configfile' in a comment reads as a statement.
    code_only = "\n".join(line.split("#", 1)[0] for line in text.splitlines())
    first = code_only.find("menuentry")
    cf = code_only.find("configfile")
    if cf != -1 and (first == -1 or cf < first):
        errs.append("configfile appears before the first menuentry")

    if not found:
        errs.append("no menuentry at all")
    else:
        title, body = found[0]
        helpers = functions(text)
        resolves = body
        for name, fbody in helpers.items():
            if re.search(rf"\b{name}\b", body):
                resolves += "\n" + fbody
        if not re.search(r"\b(linux|chainloader|fwsetup)\b", resolves):
            errs.append(f"default entry {title!r} does not reach a direct boot - it depends "
                        f"on another file")
        if "linux" in resolves and "initrd" not in resolves:
            errs.append(f"default entry {title!r} reaches linux but never an initrd")

    uuid = "58e46179-d777-4203-a807-8794a3fb2351"
    if uuid not in text:
        errs.append("root UUID missing - a stale UUID is the failure that produced the "
                    "Windows-only menu")

    print(f"  menuentry={len(found)} top_level_configfile={bad}")
    for t, _ in found:
        print(f"    - {t}")

    if errs:
        for e in errs:
            print(f"  FAIL {e}")
        return 1
    print("  PASS no top-level configfile, default entry boots a kernel directly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
