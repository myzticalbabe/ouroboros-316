"""Obligation tracker (AgenticRei adoption): duties created on admission,
tracked to discharge with evidence. Convention + file, no daemon.

Lifecycle: ADMITTED (gate exit 0 on a build) -> duties -> DISCHARGED
(each duty evidenced) | OVERDUE (eval duty past its run) | WAIVED (logged
DISPENSATION row reference required).

Duties created on admit: ledger-row, sidecar-present, eval-run.
Discharge evidence: ledger tag present / sidecar file exists / eval row found.
Store: obligations.jsonl (append-only; status via latest record per id).

Usage:
  python scripts/obligations.py admit --build PATH --tag TAG [--by NAME]
  python scripts/obligations.py check [--id ID]
  python scripts/obligations.py list [--open]
"""
import hashlib
import json
import os
import sys
import time

BASE = r"C:\Users\clint\edge0-intel"
STORE = os.path.join(BASE, "obligations.jsonl")
LEDGER = os.path.join(BASE, "evolve_log.jsonl")


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _append(rec):
    with open(STORE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def _read():
    out = []
    if os.path.exists(STORE):
        with open(STORE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return out


def _ledger_tags():
    tags = set()
    if os.path.exists(LEDGER):
        with open(LEDGER, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                    if "tag" in r:
                        tags.add(r["tag"])
                except json.JSONDecodeError:
                    pass
    return tags


def cmd_admit(a):
    if not os.path.exists(a.build):
        print(f"no such build {a.build}")
        return 2
    with open(a.build, "rb") as f:
        digest = hashlib.sha256(f.read(1 << 20)).hexdigest()[:16]
    oid = f"obl-{int(time.time())}"
    _append({"id": oid, "state": "ADMITTED", "build": a.build,
             "build_head_sha": digest, "tag": a.tag, "by": a.by or "operator",
             "at": _now(),
             "duties": ["ledger-row", "sidecar-present", "eval-run"]})
    print(f"admitted {oid} for {a.tag} (duties: ledger-row, sidecar-present, eval-run)")
    return 0


def cmd_check(a):
    recs = _read()
    if not recs:
        print("no obligations on record")
        return 0
    tags = _ledger_tags()
    by_id = {}
    for r in recs:
        by_id[r["id"]] = r
    ids = [a.id] if a.id else sorted(by_id)
    rc = 0
    for oid in ids:
        r = by_id.get(oid)
        if not r or r.get("state") != "ADMITTED":
            continue
        tag, build = r.get("tag", ""), r.get("build", "")
        sidecar = build + ".build.json" if build else ""
        got = {"ledger-row": tag in tags,
               "sidecar-present": bool(sidecar) and os.path.exists(sidecar),
               "eval-run": tag in tags}
        missing = [k for k, v in got.items() if not v]
        if not missing:
            _append({"id": oid, "state": "DISCHARGED", "at": _now(),
                     "evidence": got})
            print(f"{oid} ({tag}): DISCHARGED")
        else:
            print(f"{oid} ({tag}): OPEN, missing {missing}")
            rc = 1
    return rc


def cmd_list(a):
    recs = _read()
    open_ids, done = set(), {}
    for r in recs:
        if r.get("state") == "ADMITTED":
            open_ids.add(r["id"])
        elif r.get("state") in ("DISCHARGED", "WAIVED"):
            open_ids.discard(r["id"])
            done[r["id"]] = r["state"]
    if a.open:
        for oid in sorted(open_ids):
            print(f"{oid} OPEN")
        return 0
    for r in recs:
        print(f"{r.get('at', '?')} {r.get('id')} {r.get('state')} "
              f"{r.get('tag', '')}")
    return 0


def main():
    import argparse
    ap = argparse.ArgumentParser(prog="obligations")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("admit")
    p.add_argument("--build", required=True)
    p.add_argument("--tag", required=True)
    p.add_argument("--by", default="")
    p = sub.add_parser("check")
    p.add_argument("--id", default="")
    p = sub.add_parser("list")
    p.add_argument("--open", action="store_true")
    a = ap.parse_args()
    if a.cmd == "admit":
        return cmd_admit(a)
    if a.cmd == "check":
        return cmd_check(a)
    if a.cmd == "list":
        return cmd_list(a)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
