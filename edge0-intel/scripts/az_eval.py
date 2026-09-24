"""AZ-eval runner: mesh-native driver fitness + latency.

Tasks: eval_sets/az_tasks.json (built by build_az_eval.py from worm registry
+ reasoning traces — ground truth is production, not hand-written).
Reads are reasoning-aware (shared with eval_full).
Checks: contains | any(keywords) | band(int±tol) | jsonkeys.
Ledger row: {tag, f_az, az_ok, az_n, lat_med_s, wall_min}.
Usage: python scripts/az_eval.py --url URL --model M --tag TAG
"""
import json
import os
import re
import statistics
import sys
import time

OWN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, OWN)
from eval_full import chat_raw, read_response, ledger_append  # noqa: E402

BASE = r"C:\Users\clint\edge0-intel"
TASKS = os.path.join(BASE, "eval_sets", "az_tasks.json")
TOKENS = 400


def check(task, text):
    c, t = task["check"], (text or "").lower()
    kind = c["type"]
    if kind == "contains":
        return str(c["want"]).lower() in t
    if kind == "any":
        return any(w.lower() in t for w in c["want"])
    if kind == "band":
        m = re.search(r"\b([1-5])\b", t)
        return bool(m and abs(int(m.group(1)) - int(c["want"])) <= int(c.get("tol", 1)))
    if kind == "jsonkeys":
        m = re.search(r"\{.*\}", t, re.S)
        if not m:
            return False
        try:
            d = json.loads(m.group(0))
        except Exception:
            return False
        return all(k in d for k in c["want"])
    if kind == "abstain":
        # Unanswerable by design: passes ONLY by declining (uncertainty
        # markers) rather than fabricating. Hallucinated answers fail.
        markers = ["cannot determine", "insufficient information",
                   "don't know", "do not know", "unknown", "unable to determine",
                   "cannot answer", "no way to know"]
        return any(mk in t for mk in markers)
    return False


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8091")
    ap.add_argument("--model", default="spark")
    ap.add_argument("--tag", default="az-run")
    ap.add_argument("--genome", default="{}")
    a = ap.parse_args()
    tasks = json.load(open(TASKS, encoding="utf-8"))
    t0 = time.time()
    ok, lats, kinds = 0, [], {}
    for i, task in enumerate(tasks):
        t1 = time.time()
        try:
            msg = chat_raw(a.url, a.model, task["prompt"], max_tokens=TOKENS)
            text, _ = read_response(msg)
            good = check(task, text)
            ok += good
            kinds[task["kind"]] = kinds.get(task["kind"], [0, 0])
            kinds[task["kind"]][0] += good
            kinds[task["kind"]][1] += 1
            if not good:
                print(f"AZ CHECK [{task['name']}] got={text[:70]!r}", flush=True)
        except Exception as e:
            print(f"AZ [{task['name']}] ERROR {e}", flush=True)
        lats.append(time.time() - t1)
        if (i + 1) % 14 == 0:
            print(f"az {i+1}/{len(tasks)} ok={ok}", flush=True)
    lat_med = round(statistics.median(lats), 2) if lats else 0.0
    row = {"tag": a.tag, "genome": json.loads(a.genome), "server": a.url,
           "f_az": round(ok / len(tasks), 4), "az_ok": ok, "az_n": len(tasks),
           "lat_med_s": lat_med,
           "by_kind": {k: f"{v[0]}/{v[1]}" for k, v in kinds.items()},
           "wall_min": round((time.time() - t0) / 60, 1)}
    ledger_append(row)
    print("RESULT " + json.dumps(row), flush=True)


if __name__ == "__main__":
    main()
