"""Rule pool maintainer (JERP adoption): experiential rules with utility,
provenance, scope, expiry. Rules are retrieved at decision time (prompted
or consulted); outcomes vote them up/down; stale rules prune. The policy
half of JERP stays parked — this is the rule half, and it runs on ledger
outcomes that already exist.

Schema per rule: {id, text, source, scope, utility, status, created,
expires, history:[{t, op, evidence}]}. Status: active|merged|retired.
Capacity: warn above 64 active (merge pressure, JERP capacity limit).

Usage:
  python scripts/rules_pool.py list [--open]
  python scripts/rules_pool.py add --text "..." --source TAG [--scope S]
  python scripts/rules_pool.py vote --id R003 up|down --evidence TAG
  python scripts/rules_pool.py merge --ids R001,R002 --into "..." [--evidence T]
  python scripts/rules_pool.py prune            # lists expired/utility<=-2
  python scripts/rules_pool.py retire --id R003 --reason "..."
"""
import json
import os
import sys
import time

BASE = r"C:\Users\clint\edge0-intel"
POOL = os.path.join(BASE, "rules.json")
RETIRE_AT = -2


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def load():
    if os.path.exists(POOL):
        try:
            d = json.load(open(POOL, encoding="utf-8"))
            if isinstance(d, dict) and "rules" in d:
                return d
        except json.JSONDecodeError:
            pass
    return {"rules": [], "version": 1}


def save(d):
    json.dump(d, open(POOL, "w"), indent=1)


def find(d, rid):
    for r in d["rules"]:
        if r["id"] == rid:
            return r
    return None


def cmd_list(a):
    d = load()
    act = [r for r in d["rules"] if r.get("status") == "active"]
    if a.open:
        rows = act
    else:
        rows = d["rules"]
    for r in sorted(rows, key=lambda x: x.get("utility", 0)):
        print(f"{r['id']} u={r.get('utility',0):+d} [{r.get('status')}] "
              f"({r.get('scope','general')}) {r['text'][:90]}")
    if len(act) > 64:
        print(f"WARNING: {len(act)} active rules exceed capacity 64 (merge pressure)")
    return 0


def cmd_add(a):
    d = load()
    n = len(d["rules"]) + 1
    rid = f"R{n:03d}"
    while find(d, rid):
        n += 1
        rid = f"R{n:03d}"
    d["rules"].append({"id": rid, "text": a.text, "source": a.source,
                       "scope": a.scope, "utility": 0, "status": "active",
                       "created": _now(), "expires": "",
                       "history": [{"t": _now(), "op": "add",
                                    "evidence": a.source}]})
    save(d)
    print(f"added {rid}")
    return 0


def cmd_vote(a):
    d = load()
    r = find(d, a.id)
    if not r:
        print(f"unknown {a.id}")
        return 2
    dlt = 1 if a.direction == "up" else -1
    r["utility"] = int(r.get("utility", 0)) + dlt
    r.setdefault("history", []).append(
        {"t": _now(), "op": f"vote-{a.direction}", "evidence": a.evidence})
    if r["utility"] <= RETIRE_AT and r.get("status") == "active":
        r["status"] = "retired"
        r["history"].append({"t": _now(), "op": "auto-retire",
                             "evidence": f"utility<={RETIRE_AT}"})
        print(f"{a.id} auto-retired (utility {r['utility']})")
    else:
        print(f"{a.id} utility={r['utility']}")
    save(d)
    return 0


def cmd_merge(a):
    d = load()
    ids = [x.strip() for x in a.ids.split(",") if x.strip()]
    if len(ids) < 2 or not all(find(d, i) for i in ids):
        print("need 2+ existing ids")
        return 2
    n = len(d["rules"]) + 1
    rid = f"R{n:03d}"
    while find(d, rid):
        n += 1
        rid = f"R{n:03d}"
    util = sum(int(find(d, i).get("utility", 0)) for i in ids)
    d["rules"].append({"id": rid, "text": a.into, "source": "merge:" + "+".join(ids),
                       "scope": "general", "utility": util, "status": "active",
                       "created": _now(), "expires": "",
                       "history": [{"t": _now(), "op": "merge",
                                    "evidence": a.evidence or "+".join(ids)}]})
    for i in ids:
        r = find(d, i)
        r["status"] = "merged"
        r.setdefault("history", []).append(
            {"t": _now(), "op": f"merged-into-{rid}", "evidence": a.evidence or ""})
    save(d)
    print(f"merged {ids} -> {rid} (utility {util})")
    return 0


def cmd_prune(a):
    d = load()
    today = time.strftime("%Y-%m-%d")
    for r in d["rules"]:
        if r.get("status") != "active":
            continue
        reasons = []
        if int(r.get("utility", 0)) <= RETIRE_AT:
            reasons.append(f"utility {r['utility']}")
        if r.get("expires") and r["expires"][:10] < today:
            reasons.append(f"expired {r['expires'][:10]}")
        if reasons:
            print(f"{r['id']} PRUNE-CANDIDATE ({'; '.join(reasons)}): {r['text'][:70]}")
    return 0


def cmd_retire(a):
    d = load()
    r = find(d, a.id)
    if not r:
        print(f"unknown {a.id}")
        return 2
    r["status"] = "retired"
    r.setdefault("history", []).append(
        {"t": _now(), "op": "retire", "evidence": a.reason})
    save(d)
    print(f"retired {a.id}")
    return 0


def main():
    import argparse
    ap = argparse.ArgumentParser(prog="rules_pool")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("list")
    p.add_argument("--open", action="store_true")
    p = sub.add_parser("add")
    p.add_argument("--text", required=True)
    p.add_argument("--source", default="")
    p.add_argument("--scope", default="general")
    p = sub.add_parser("vote")
    p.add_argument("--id", required=True)
    p.add_argument("direction", choices=("up", "down"))
    p.add_argument("--evidence", default="")
    p = sub.add_parser("merge")
    p.add_argument("--ids", required=True)
    p.add_argument("--into", required=True)
    p.add_argument("--evidence", default="")
    sub.add_parser("prune")
    p = sub.add_parser("retire")
    p.add_argument("--id", required=True)
    p.add_argument("--reason", default="")
    a = ap.parse_args()
    if a.cmd == "list":
        return cmd_list(a)
    if a.cmd == "add":
        return cmd_add(a)
    if a.cmd == "vote":
        return cmd_vote(a)
    if a.cmd == "merge":
        return cmd_merge(a)
    if a.cmd == "prune":
        return cmd_prune(a)
    if a.cmd == "retire":
        return cmd_retire(a)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
