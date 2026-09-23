"""Build AZ-eval: mesh-native driver fitness set from Azazael's own records.

Sources (no hand-written ground truth):
  worm_config_trace.json : 226 worms, category + priority + description.
  neural_mesh_*_2026-09-16.jsonl : reasoning traces with problem/evidence/
      decision/solution/verification.

Task types (all machine-checkable):
  route   : which category owns this task? -> category string present.
  triage  : severity 1-5 for an alert -> worm's own priority band.
  config  : emit dikutip config JSON -> parses + required keys present.
  recall  : given trace problem+evidence, name the decision -> key-term hit.
  describe: what does worm X do? -> description keyword hit.

Out: eval_sets/az_tasks_50.json  [{name, kind, prompt, check:{...}}, ...]
Latency is recorded at RUN time (az_eval.py), not here.
"""
import json
import os
import random

AZ = r"C:\Users\clint\azazael"
OUT = r"C:\Users\clint\edge0-intel\eval_sets\az_tasks.json"
rng = random.Random(7)


def load_registry():
    with open(os.path.join(AZ, "worm_config_trace.json"), encoding="utf-8") as f:
        return json.load(f)


def load_traces():
    rows = []
    for fn in sorted(os.listdir(os.path.join(AZ, "data", "training"))):
        if fn.startswith("neural_mesh_") and fn.endswith(".jsonl"):
            with open(os.path.join(AZ, "data", "training", fn), encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("{"):
                        try:
                            rows.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
    return rows


def keywords(text, n=6):
    stop = {"the", "a", "an", "and", "or", "of", "to", "in", "for", "with",
            "on", "is", "are", "that", "this", "it", "as", "by", "from",
            "into", "which", "their", "has", "have", "was", "were", "be"}
    words = [w.strip(".,;:!?()[]{}\"'").lower() for w in str(text).split()]
    words = [w for w in words if len(w) > 3 and w not in stop and w.isalpha()]
    seen, out = set(), []
    for w in words:
        if w not in seen:
            seen.add(w)
            out.append(w)
        if len(out) == n:
            break
    return out


def main():
    reg = load_registry()
    names = sorted(reg.keys())
    tasks = []

    # Stratified sample across categories for route/describe/triage/config.
    by_cat = {}
    for name in names:
        by_cat.setdefault(reg[name].get("category", "?"), []).append(name)
    cats = sorted(by_cat)
    pool = []
    i = 0
    while len(pool) < 30:
        for c in cats:
            members = by_cat[c]
            pool.append(members[i % len(members)])
            if len(pool) >= 30:
                break
        i += 1

    for j, name in enumerate(pool):
        w = reg[name]
        cat, desc = w.get("category", "?"), w.get("description", "")
        kws = keywords(desc)
        kind = ["route", "describe", "triage", "config"][j % 4]
        if kind == "route":
            others = rng.sample([c for c in cats if c != cat], min(3, len(cats) - 1))
            tasks.append({
                "name": f"route-{j}", "kind": "route",
                "prompt": (f"A mesh task arrives: '{desc}'. Which category owns "
                           f"it? Options: {', '.join([cat] + others)}. "
                           f"Reply with the category name."),
                "check": {"type": "contains", "want": cat},
            })
        elif kind == "describe":
            tasks.append({
                "name": f"describe-{j}", "kind": "describe",
                "prompt": (f"In one sentence, what does the mesh worm "
                           f"'{name}' do?"),
                "check": {"type": "any", "want": kws[:4]},
            })
        elif kind == "triage":
            sev = max(1, min(5, int(w.get("priority", 3))))
            tasks.append({
                "name": f"triage-{j}", "kind": "triage",
                "prompt": (f"Alert: '{desc}'. Rate severity as a single "
                           f"integer 1-5."),
                "check": {"type": "band", "want": sev, "tol": 1},
            })
        else:
            tasks.append({
                "name": f"config-{j}", "kind": "config",
                "prompt": (f"Emit ONLY this JSON object, no other text: "
                           f'{{"worm": "{name}", "category": "{cat}", '
                           f'"priority": {int(w.get("priority", 3))}}}.'),
                "check": {"type": "jsonkeys",
                          "want": ["worm", "category", "priority"]},
            })

    # Trace-derived recall tasks: problem+evidence -> decision terms.
    traces = [r for r in load_traces() if isinstance(r, dict)
              and r.get("problem") and r.get("solution")]
    for j, tr in enumerate(traces[:20]):
        sol_terms = keywords(tr.get("solution", ""), 5)
        ev = str(tr.get("evidence", ""))[:600]
        tasks.append({
            "name": f"recall-{j}", "kind": "recall",
            "prompt": (f"Mesh audit episode [{tr.get('trace_id', '?')}]: "
                       f"{tr.get('problem', '')} Evidence: {ev} "
                       f"What was decided? One paragraph."),
            "check": {"type": "any", "want": sol_terms[:3]},
        })

    tasks = tasks[:50]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=1)
    kinds = {}
    for t in tasks:
        kinds[t["kind"]] = kinds.get(t["kind"], 0) + 1
    print(f"wrote {len(tasks)} tasks -> {OUT} {kinds}")


if __name__ == "__main__":
    main()
