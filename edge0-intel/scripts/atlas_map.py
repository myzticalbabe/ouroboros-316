"""Atlas map: the explicit causal model (revision operator PHI included).

The ledger records WHAT happened. This map records what we BELIEVE:
versioned edit->fitness causal structure, counterfactual query, and
structural revision on violation. The Yu-Inamura (Mt, PHI) correspondence,
implemented rather than asserted.

Schema (atlas_map.json):
  version   : int, bumped on every structural revision
  base      : {family: {tag, svi}} — reference rows per model family
  deltas    : {edit_tag: {d_svi, base_tag}} — single-edit causal effects
  violations: [{combo, predicted, measured, epsilon}] — |eps| > EPS_SIG,
              i.e. where additivity breaks and the map must be revised
  revisions : [{v, reason, time}] — append-only history of map changes

Usage:
  python scripts/atlas_map.py build     # (re)build v1 from ledger
  python scripts/atlas_map.py show      # print map summary
  python scripts/atlas_map.py predict --adds TAG [...] [--measured TAG]
      Counterfactual: SVI without serving. Same math as svi --predict;
      this is the formal counterfactual stage (evaluate under the map
      before executing serves).
  python scripts/atlas_map.py revise --measured TAG --adds TAG [...]
      PHI step: ingest a measured combo, compute epsilon, record violation
      and bump version when |eps| > EPS_SIG.
"""
import copy
import json
import os
import sys
import time

BASE = r"C:\Users\clint\edge0-intel"
LEDGER = os.path.join(BASE, "evolve_log.jsonl")
MAPF = os.path.join(BASE, "atlas_map.json")

EPS_SIG = 0.05  # SVI epsilon magnitude that counts as structural break
W_R, W_C, W_T = 0.5, 0.5, 0.02


def svi(row):
    return (W_R * float(row.get("f_refusal", 0.0))
            + W_C * float(row.get("f_caps", 0.0))
            - W_T * float(row.get("wall_min", 0.0)))


def load_ledger():
    rows = []
    with open(LEDGER, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "f_refusal" in r and r.get("tag") != "CORRECTION":
                    rows.append(r)
    return rows


def family_of(tag):
    t = tag.lower()
    if t.startswith("gemma"):
        return "gemma"
    if t.startswith("ling") or t.startswith("sc117") or t.startswith("exp-k"):
        return "ling"
    if t.startswith("spark"):
        return "spark"
    return "other"


BASE_CANDS = {"gemma": ["gemma-stock-full100"],
              "ling": ["ling-abl-s05-full", "sc117-compact-full"],
              "spark": ["spark-x25-stock100"]}


def pick_base(rows, fam):
    """Highest-SVI eligible row among candidates (N>=50, caps signal real).
    Never the SUSPECT caps-0 artifact class."""
    best = None
    for tag in BASE_CANDS.get(fam, []):
        r = rows.get(tag)
        if not r or int(r.get("eval_N", 0)) < 50 or r.get("caps_ok", 0) == 0:
            continue
        if best is None or svi(r) > svi(best):
            best = r
    return best


def load_map():
    if os.path.exists(MAPF):
        return json.load(open(MAPF, encoding="utf-8"))
    return None


def cmd_build():
    rows = {r["tag"]: r for r in load_ledger()}
    base, deltas = {}, {}
    base_tags = set()
    for fam in BASE_CANDS:
        b = pick_base(rows, fam)
        if b is not None:
            base[fam] = {"tag": b["tag"], "svi": round(svi(b), 4)}
            base_tags.add(b["tag"])
    for tag, r in rows.items():
        if int(r.get("eval_N", 0)) < 50 or tag in base_tags:
            continue
        if r.get("caps_ok", 0) == 0:
            continue  # SUSPECT quarantine applies to the map too
        fam = family_of(tag)
        if fam in base:
            deltas[tag] = {"d_svi": round(svi(r) - base[fam]["svi"], 4),
                           "base_tag": base[fam]["tag"]}
    m = {"version": 1, "base": base, "deltas": deltas,
         "violations": [],
         "revisions": [{"v": 1,
                        "reason": "initial build from ledger",
                        "time": time.strftime("%Y-%m-%dT%H:%M:%S")}]}
    json.dump(m, open(MAPF, "w"), indent=1)
    print(f"atlas v1: {len(base)} bases, {len(deltas)} deltas -> {MAPF}")
    return 0


def cmd_show():
    m = load_map()
    if not m:
        print("no map; run `build` first")
        return 2
    print(f"atlas v{m['version']}: {len(m['base'])} bases, "
          f"{len(m['deltas'])} deltas, {len(m['violations'])} violations")
    for fam, b in m["base"].items():
        print(f"  base[{fam}] {b['tag']} SVI={b['svi']:.3f}")
    for tag, d in sorted(m["deltas"].items(), key=lambda x: x[1]["d_svi"]):
        print(f"  delta {tag}: {d['d_svi']:+.3f} (vs {d['base_tag']})")
    for v in m["violations"]:
        print(f"  VIOLATION {v['combo']}: pred={v['predicted']:.3f} "
              f"meas={v['measured']:.3f} eps={v['epsilon']:+.3f}")
    return 0


def predict(m, adds):
    base = None
    total = 0.0
    for tag in adds:
        d = m["deltas"].get(tag)
        if d is None:
            return None, f"unknown edit {tag!r} (not a single in map)"
        if base is None:
            base = m["base"].get(family_of(tag))
        total += d["d_svi"]
    if base is None:
        return None, "no adds given"
    return round(base["svi"] + total, 4), None


def cmd_predict(a):
    m = load_map()
    if not m:
        print("no map; run `build` first")
        return 2
    pred, err = predict(m, a.adds)
    if err:
        print(err)
        return 2
    print(f"SVI_predicted = {pred:.3f}  (counterfactual, no serving)")
    if a.measured:
        rows = {r["tag"]: r for r in load_ledger()}
        if a.measured not in rows:
            print(f"unknown --measured {a.measured!r}")
            return 2
        meas = round(svi(rows[a.measured]), 4)
        print(f"SVI_measured({a.measured}) = {meas:.3f}  "
              f"epistasis epsilon = {meas - pred:+.3f}")
    return 0


def cmd_revise(a):
    m = load_map()
    if not m:
        print("no map; run `build` first")
        return 2
    pred, err = predict(m, a.adds)
    if err:
        print(err)
        return 2
    rows = {r["tag"]: r for r in load_ledger()}
    if a.measured not in rows:
        print(f"unknown --measured {a.measured!r}")
        return 2
    meas = round(svi(rows[a.measured]), 4)
    eps = round(meas - pred, 4)
    print(f"pred={pred:.3f} meas={meas:.3f} eps={eps:+.3f}")
    if abs(eps) > EPS_SIG:
        m["version"] += 1
        m["violations"].append({"combo": list(a.adds), "predicted": pred,
                                "measured": meas, "epsilon": eps})
        m["revisions"].append(
            {"v": m["version"],
             "reason": f"structural break on {a.measured} (|eps|={abs(eps):.3f})",
             "time": time.strftime("%Y-%m-%dT%H:%M:%S")})
        json.dump(m, open(MAPF, "w"), indent=1)
        print(f"PHI: map revised to v{m['version']} (additivity violated here)")
    else:
        print("PHI: within noise, map unchanged")
    return 0


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="atlas_map")
    ap.add_argument("cmd", nargs="?", default="show")
    ap.add_argument("--adds", nargs="*", default=[])
    ap.add_argument("--measured", default="")
    a = ap.parse_args(argv)
    if a.cmd == "build":
        return cmd_build()
    if a.cmd == "predict":
        return cmd_predict(a)
    if a.cmd == "revise":
        if not a.measured or not a.adds:
            print("revise needs --adds TAG [...] and --measured TAG")
            return 2
        return cmd_revise(a)
    return cmd_show()


if __name__ == "__main__":
    sys.exit(main())
