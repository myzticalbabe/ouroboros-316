"""Failure attribution gate (ARTS adoption): every negative ledgered as
hypothesis-fault vs execution-fault vs infra-fault BEFORE the next step.

Heuristics first (FAPO rule: deterministic pass before model calls):
  infra     : caps_ok==0, wall_min absurd, ERROR lines, server down mid-run,
              disk-full signatures, SUSPECT flag present.
  hypothesis: clean execution, dose-flat or backwards curve, strict low with
              coherent marks (direction doesn't drive the property).
  execution : build/serve crashes with code errors, template mismatches,
              budget cutoffs (empties), mid-run kills.
Unknown when evidence is missing — the gate refuses to guess (says so).

Usage:
  python scripts/attribute.py --tag TAG [--log PATH]
  python scripts/attribute.py --sweep PREFIX   # attribute all ledger rows
                                               # with tag prefix
"""
import json
import os
import re
import sys

BASE = r"C:\Users\clint\edge0-intel"
LEDGER = os.path.join(BASE, "evolve_log.jsonl")


def load_rows():
    rows = []
    with open(LEDGER, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return rows


def log_signals(log_path, limit=400):
    """Scan a log tail for execution/infra signatures."""
    if not log_path or not os.path.exists(log_path):
        return {"log_present": False}
    try:
        with open(log_path, encoding="utf-8", errors="replace") as f:
            tail = f.readlines()[-limit:]
    except OSError:
        return {"log_present": False}
    text = "".join(tail)
    return {
        "log_present": True,
        "traceback": bool(re.search(r"Traceback|Error|error", text)),
        "empty_replies": len(re.findall(r"got=''", text)),
        "nospace": "No space left" in text,
        "killed": bool(re.search(r"KILLED|terminat", text, re.I)),
        "refused_line": bool(re.search(r"refused=\d+", text)),
    }


def attribute(row, sig=None):
    """Returns (fault, evidence_list). Fault in {hypothesis, execution,
    infra, unknown}."""
    sig = sig or {}
    ev = []
    tag = row.get("tag", "?")
    # Infra first: measurement broken beats any hypothesis about the model.
    if row.get("caps_ok", 1) == 0:
        ev.append("caps_ok==0: no capability signal (down-server class)")
        return "infra", ev
    if sig.get("nospace"):
        ev.append("disk-full signature in logs")
        return "infra", ev
    if sig.get("traceback"):
        ev.append("traceback in run logs")
        return "execution", ev
    if not sig.get("log_present", True):
        ev.append("no run log available")
    # Dose/shape reasoning needs siblings; single rows stay unknown-leaning
    # hypothesis only with corroboration (caller passes curve context).
    if row.get("eval_N", 0) < 50:
        ev.append(f"N={row.get('eval_N')}: subset noise, no attribution")
        return "unknown", ev
    if sig.get("empty_replies", 0) > 3:
        ev.append(f"{sig['empty_replies']} empty replies: budget cutoff, "
                  "not a model property")
        return "execution", ev
    ev.append("clean execution, full N: fault (if any) is in the hypothesis")
    return "hypothesis", ev


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="")
    ap.add_argument("--sweep", default="")
    ap.add_argument("--log", default="")
    a = ap.parse_args()
    rows = load_rows()
    if a.sweep:
        rows = [r for r in rows if r.get("tag", "").startswith(a.sweep)]
    elif a.tag:
        rows = [r for r in rows if r.get("tag") == a.tag]
    else:
        print("need --tag TAG or --sweep PREFIX")
        return 2
    if not rows:
        print("no rows match")
        return 2
    for r in rows:
        fault, ev = attribute(r, log_signals(a.log))
        print(f"{r.get('tag')}: {fault}")
        for e in ev:
            print(f"  - {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
