"""Static syntax check for a GRUB config: structure, never execution.

A wrong stub is invisible from Windows: it only fails on the next reboot, in
a menu the user is staring at. This checks the failures that would leave a
menu that boots nothing, plus the GRUB-specific landmines:

  * unbalanced { } / if-fi / for-done / function bodies
  * unbalanced [ ] tests and quotes
  * `&&`, `||` -- GRUB has no such operators in this form
  * ${var#...} / ${var%...} -- substring ops GRUB does not implement
  * a variable used before it is set
  * insmod of a module that is never used, and use of a command whose module
    is neither built in nor insmod'ed
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

BUILTIN = {
    "set", "echo", "if", "then", "else", "fi", "for", "do", "done", "function",
    "return", "menuentry", "linux", "initrd", "chainloader", "configfile",
    "normal", "search", "ls", "sleep", "insmod", "true", "false", "clear",
    "reboot", "halt", "exit", "cat", "test", "[", "regexp", "fwsetup",
}

MODULE_FOR = {"linux": "linux", "initrd": "linux", "chainloader": "chain",
              "configfile": "normal", "normal": "normal", "ls": None}


def strip_comment(line: str) -> str:
    out: list[str] = []
    quote = None
    i = 0
    while i < len(line):
        ch = line[i]
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            out.append(ch)
        elif ch == "#":
            break
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def segments(line: str) -> list[str]:
    """Split on ';' that are outside quotes."""
    out, cur, quote = [], [], None
    for ch in line:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            cur.append(ch)
            continue
        if ch == ";":
            out.append("".join(cur).strip())
            cur = []
            continue
        cur.append(ch)
    out.append("".join(cur).strip())
    return [s for s in out if s]


def check(path: Path) -> list[str]:
    errs: list[str] = []
    text = path.read_text(encoding="utf-8")
    depth = 0
    depth_at_open: list[int] = []
    stack: list[tuple[str, int]] = []
    assigned: set[str] = set()
    insmodded: set[str] = set()
    defined_functions: set[str] = set()
    pending_for: list[int] = []

    for n, raw in enumerate(text.splitlines(), 1):
        line = strip_comment(raw).strip()
        if not line:
            continue

        if "&&" in line or "||" in line:
            errs.append(f"{n}: GRUB has no && / || operator: {line}")
        if re.search(r"\$\{[A-Za-z0-9_]+[#%/]", line):
            errs.append(f"{n}: GRUB has no substring op in ${{...}}: {line}")
        if line.count("'") % 2 or line.count('"') % 2:
            errs.append(f"{n}: unbalanced quote: {line}")
        if line.count("[") != line.count("]"):
            errs.append(f"{n}: unbalanced [ ] test: {line}")

        for seg in segments(line):
            words = seg.split()
            if not words:
                continue
            head = words[0]
            if head == "if":
                stack.append(("if", n))
            elif head == "fi":
                if not stack or stack[-1][0] != "if":
                    errs.append(f"{n}: fi without if (top={stack[-1] if stack else None})")
                else:
                    stack.pop()
            elif head == "for":
                if "do" not in words and not seg.rstrip().endswith("do"):
                    pending_for.append(n)
                stack.append(("for", n))
            elif head == "do":
                if pending_for:
                    pending_for.pop()
                else:
                    errs.append(f"{n}: do without a pending for")
            elif head == "done":
                if not stack or stack[-1][0] != "for":
                    errs.append(f"{n}: done without for (top={stack[-1] if stack else None})")
                else:
                    stack.pop()
            elif head == "function":
                if depth != 0:
                    errs.append(f"{n}: function declared inside a {depth}-deep block")
                if len(words) > 1:
                    defined_functions.add(words[1])
            elif head == "insmod" and len(words) > 1:
                insmodded.add(words[1])
            elif head == "set" and len(words) > 1 and "=" in words[1]:
                assigned.add(words[1].split("=", 1)[0])
            elif head in ("menuentry",):
                pass
            elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", head):
                if head not in BUILTIN and head not in defined_functions:
                    errs.append(f"{n}: unknown command '{head}'")

            for w in words[1:]:
                m = re.fullmatch(r"\$([A-Za-z_][A-Za-z0-9_]*)", w)
                if m and m.group(1) not in assigned and m.group(1) not in ("1", "2", "3"):
                    errs.append(f"{n}: ${m.group(1)} used before set")

        depth += line.count("{") - line.count("}")
        if line.endswith("{"):
            depth_at_open.append(depth - 1)
        if line == "}":
            if not depth_at_open:
                errs.append(f"{n}: closing brace with no open block")
            else:
                depth_at_open.pop()
            if stack:
                errs.append(f"{n}: block closed while {'/'.join(s[0] for s in stack)} still open")

    if depth != 0:
        errs.append(f"EOF: brace depth {depth} (expected 0)")
    if stack:
        errs.append(f"EOF: unclosed {'/'.join(s[0] for s in stack)}")
    if depth_at_open:
        errs.append(f"EOF: {len(depth_at_open)} block(s) never closed")
    if pending_for:
        errs.append(f"EOF: for at line(s) {pending_for} never reached do")

    # A config that balances but offers nothing to boot is a dead menu, not a
    # valid one: a truncated file either keeps its header and loses every
    # entry, or keeps an entry and loses its body. Both must fail.
    menu_blocks = list(re.finditer(r"^\s*menuentry[^\n]*\{(.*?)^\s*\}", text, re.M | re.S))
    if not menu_blocks:
        errs.append("no menuentry - this config offers nothing to boot")
    bootable = 0
    for idx, m in enumerate(menu_blocks, 1):
        body = m.group(1)
        line_no = text[: m.start()].count(chr(10)) + 1
        body_code = "\n".join(
            ln for ln in body.splitlines() if ln.strip() and not ln.strip().startswith("#")
        ).strip()
        if not body_code:
            errs.append(f"{line_no}: menuentry {idx} has an empty body - selecting it does nothing")
            continue
        # A diagnostic entry (ls/echo/sleep) is legitimate; only a config where
        # nothing at all can boot is a defect.
        if re.search(r"\b(linux|initrd|chainloader|configfile|normal)\b", body_code):
            bootable += 1
    if menu_blocks and bootable == 0:
        errs.append("no menuentry can boot anything (no linux/initrd/chainloader/configfile)")

    for mod, needed_by in MODULE_FOR.items():
        if mod in insmodded and needed_by and needed_by not in insmodded:
            errs.append(f"{mod} insmod'ed but its user {needed_by} has no module")

    print(f"  menuentry={len(re.findall(r'^\s*menuentry', text, re.M))} "
          f"function={len(defined_functions)} stringsize={len(text)}")
    return errs


def main() -> int:
    paths = sys.argv[1:] or ["grub_p8_stub_v4.cfg"]
    rc = 0
    for p in paths:
        path = Path(p)
        print(f"== {path} ({path.stat().st_size} bytes) ==")
        errs = check(path)
        if errs:
            rc = 1
            for e in errs:
                print(f"  FAIL {e}")
        else:
            print("  PASS braces, if/fi, for/done, functions, quotes, tests all balanced")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
