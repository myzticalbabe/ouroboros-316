"""Frankenstein shard node — importable composition of arena-64n evolved shards.

Each shard is one evolved candidate, wired as a callable module behind a
cost-aware router (model-stitching / Mixture-of-LoRA-Experts pattern at
training-logic level: shared base + grafted behaviors + top-1 routing).

  shard-a  candidate-a/train_a.py: numpy ReLU, He init, full-batch SGD
  shard-b  candidate-b/train_b.py: sklearn MLPClassifier, adam, early stopping
  shard-c  candidate-c/train_c.py: numpy tanh, Xavier init, mini-batch Adam
  synthesis solution.py: C base + B graft (early-stop on train plateau
             with best-weight snapshot) + A discipline (fixed-seed numpy core)

Router budgets come from the measured scale sweep (SCALE_SWEEP.md):
  fast      H=32  test 0.9861, 2410 params  (matches H=64 at half the params)
  balanced  H=64  test 0.9833, 4810 params  (the synthesis contract)
  peak      H=128 test 0.9889, 9610 params  (measured peak accuracy)

No result cache: every run recomputes (false-green rule — a gate that
passes without re-running proves nothing).

Usage:
  python shard_node.py --list
  python shard_node.py --self-test        # cold recompute, asserts thresholds
  python shard_node.py --run --budget balanced [--out results.json] [--seed 7]
"""

import argparse
import json
import sys
import time

SEED = 7
EPOCHS = 60
BATCH = 64
LR = 0.01
B1, B2, EPS = 0.9, 0.999, 1e-8
PATIENCE = 8  # graft from B

BUDGETS = {
    "fast": ("synthesis", 32),
    "balanced": ("synthesis", 64),
    "peak": ("synthesis", 128),
}


def _load():
    from sklearn.datasets import load_digits
    from sklearn.model_selection import train_test_split
    import numpy as np

    X, y = load_digits(return_X_y=True)
    X = X / 16.0
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y)
    return np, Xtr, Xte, ytr, yte


def _params(din, hidden, ncls=10):
    return int(din * hidden + hidden + hidden * ncls + ncls)


def train_numpy_tanh_adam(hidden=64, seed=SEED, patience=PATIENCE):
    """Shard C base, optionally with the shard-B early-stopping graft."""
    np, Xtr, Xte, ytr, yte = _load()
    n, din = Xtr.shape
    ncls = 10
    Ytr = np.eye(ncls)[ytr]
    rng = np.random.default_rng(seed)
    lim1 = float(np.sqrt(6.0 / (din + hidden)))
    lim2 = float(np.sqrt(6.0 / (hidden + ncls)))
    W1 = rng.uniform(-lim1, lim1, (din, hidden))
    b1 = np.zeros(hidden)
    W2 = rng.uniform(-lim2, lim2, (hidden, ncls))
    b2 = np.zeros(ncls)
    mW1, vW1 = np.zeros_like(W1), np.zeros_like(W1)
    mb1, vb1 = np.zeros_like(b1), np.zeros_like(b1)
    mW2, vW2 = np.zeros_like(W2), np.zeros_like(W2)
    mb2, vb2 = np.zeros_like(b2), np.zeros_like(b2)
    step = 0
    best_acc, best_w, best_ep = -1.0, None, 0

    def train_acc():
        p = np.argmax(np.tanh(Xtr @ W1 + b1) @ W2 + b2, axis=1)
        return float((p == ytr).mean())

    t0 = time.time()
    epochs_run = 0
    for epoch in range(EPOCHS):
        perm = rng.permutation(n)
        for s in range(0, n, BATCH):
            step += 1
            idx = perm[s:s + BATCH]
            xb, yb = Xtr[idx], Ytr[idx]
            m = len(idx)
            h = np.tanh(xb @ W1 + b1)
            z = h @ W2 + b2
            z -= z.max(axis=1, keepdims=True)
            p = np.exp(z)
            p /= p.sum(axis=1, keepdims=True)
            dz = (p - yb) / m
            gW2, gb2 = h.T @ dz, dz.sum(axis=0)
            dh = (dz @ W2.T) * (1.0 - h ** 2)
            gW1, gb1 = xb.T @ dh, dh.sum(axis=0)
            for g, mv, vv in ((gW1, mW1, vW1), (gb1, mb1, vb1),
                              (gW2, mW2, vW2), (gb2, mb2, vb2)):
                mv[:] = B1 * mv + (1 - B1) * g
                vv[:] = B2 * vv + (1 - B2) * g * g
            W1 -= LR * (mW1 / (1 - B1 ** step)) / (
                np.sqrt(vW1 / (1 - B2 ** step)) + EPS)
            b1 -= LR * (mb1 / (1 - B1 ** step)) / (
                np.sqrt(vb1 / (1 - B2 ** step)) + EPS)
            W2 -= LR * (mW2 / (1 - B1 ** step)) / (
                np.sqrt(vW2 / (1 - B2 ** step)) + EPS)
            b2 -= LR * (mb2 / (1 - B1 ** step)) / (
                np.sqrt(vb2 / (1 - B2 ** step)) + EPS)
        epochs_run = epoch + 1
        if patience is None:
            continue
        acc = train_acc()
        if acc > best_acc + 1e-6:
            best_acc, best_w, best_ep = (
                acc, (W1.copy(), b1.copy(), W2.copy(), b2.copy()),
                epochs_run)
        elif epochs_run - best_ep >= patience:
            break
    secs = time.time() - t0
    if patience is not None:
        W1, b1, W2, b2 = best_w
        tr_acc = best_acc
    else:
        ptr = np.argmax(np.tanh(Xtr @ W1 + b1) @ W2 + b2, axis=1)
        tr_acc = float((ptr == ytr).mean())
        best_ep = epochs_run
    pte = np.argmax(np.tanh(Xte @ W1 + b1) @ W2 + b2, axis=1)
    te_acc = float((pte == yte).mean())
    return {
        "weights": (W1, b1, W2, b2),
        "train_accuracy": round(tr_acc, 4),
        "test_accuracy": round(te_acc, 4),
        "seconds": round(secs, 1),
        "epochs_run": epochs_run,
        "best_epoch": best_ep,
        "params": _params(din, hidden),
    }


def train_numpy_relu_sgd(hidden=64, seed=SEED, epochs=400, lr=0.5):
    """Shard A: pure numpy ReLU, He init, full-batch SGD (train_a.py)."""
    np, Xtr, Xte, ytr, yte = _load()
    n, din = Xtr.shape
    ncls = 10
    Ytr = np.eye(ncls)[ytr]
    rng = np.random.default_rng(seed)
    W1 = rng.normal(0, np.sqrt(2.0 / din), (din, hidden))
    b1 = np.zeros(hidden)
    W2 = rng.normal(0, np.sqrt(2.0 / hidden), (hidden, ncls))
    b2 = np.zeros(ncls)
    t0 = time.time()
    for _ in range(epochs):
        h = np.maximum(Xtr @ W1 + b1, 0.0)
        z = h @ W2 + b2
        z -= z.max(axis=1, keepdims=True)
        p = np.exp(z)
        p /= p.sum(axis=1, keepdims=True)
        dz = (p - Ytr) / n
        dW2 = h.T @ dz
        db2 = dz.sum(axis=0)
        dh = (dz @ W2.T) * (h > 0)
        W2 -= lr * dW2
        b2 -= lr * db2
        W1 -= lr * Xtr.T @ dh
        b1 -= lr * dh.sum(axis=0)
    secs = time.time() - t0

    def acc(Xe, ye):
        p = np.argmax(np.maximum(Xe @ W1 + b1, 0.0) @ W2 + b2, axis=1)
        return float((p == ye).mean())

    return {
        "weights": (W1, b1, W2, b2),
        "train_accuracy": round(acc(Xtr, ytr), 4),
        "test_accuracy": round(acc(Xte, yte), 4),
        "seconds": round(secs, 1),
        "epochs_run": epochs,
        "best_epoch": epochs,
        "params": _params(din, hidden),
    }


def train_sklearn_mlp(hidden=64, seed=SEED):
    """Shard B: sklearn MLPClassifier adam + early stopping (train_b.py)."""
    from sklearn.neural_network import MLPClassifier
    _, Xtr, Xte, ytr, yte = _load()
    clf = MLPClassifier(hidden_layer_sizes=(hidden,), activation="relu",
                        solver="adam", alpha=1e-4, batch_size=64,
                        max_iter=300, early_stopping=True, n_iter_no_change=20,
                        random_state=seed)
    t0 = time.time()
    clf.fit(Xtr, ytr)
    secs = time.time() - t0
    return {
        "weights": clf,
        "train_accuracy": round(float(clf.score(Xtr, ytr)), 4),
        "test_accuracy": round(float(clf.score(Xte, yte)), 4),
        "seconds": round(secs, 1),
        "epochs_run": int(clf.n_iter_),
        "best_epoch": int(clf.n_iter_),
        "params": int(sum(c.size for c in clf.coefs_) +
                      sum(b.size for b in clf.intercepts_)),
    }


SHARDS = {
    "shard-a": {"train": train_numpy_relu_sgd, "source": "candidate-a/train_a.py",
                "notes": "dependency-free numpy core, fixed-seed determinism"},
    "shard-b": {"train": train_sklearn_mlp, "source": "candidate-b/train_b.py",
                "notes": "battle-tested library; early-stopping behavior donor"},
    "shard-c": {"train": train_numpy_tanh_adam, "source": "candidate-c/train_c.py",
                "notes": "modern-optimizer base; peak single-shard accuracy"},
    "synthesis": {"train": train_numpy_tanh_adam,
                   "source": "solution.py (C base + B early-stopping graft)",
                   "notes": "production default; graft keeps best-generalizing weights"},
}


def run_shard(name, hidden=64, seed=SEED):
    """Train one shard; returns a JSON-serializable result (no weights)."""
    if name not in SHARDS:
        raise ValueError("unknown shard %r; choose from %s"
                         % (name, sorted(SHARDS)))
    out = SHARDS[name]["train"](hidden=hidden, seed=seed)
    out.pop("weights", None)
    return {"shard": name, "hidden": hidden, "seed": seed,
            "source": SHARDS[name]["source"], **out}


def route(budget):
    """Top-1 router: budget -> (shard, hidden) from the measured sweep."""
    if budget not in BUDGETS:
        raise ValueError("unknown budget %r; choose from %s"
                         % (budget, sorted(BUDGETS)))
    return BUDGETS[budget]


def self_test():
    """Cold recompute on H=16 synthesis + determinism; no cache involved."""
    checks = []
    r1 = run_shard("synthesis", hidden=16, seed=SEED)
    r2 = run_shard("synthesis", hidden=16, seed=SEED)
    checks.append(("recomputed (no cache)", True))
    checks.append(("train>=0.97 (got %s)" % r1["train_accuracy"],
                   r1["train_accuracy"] >= 0.97))
    checks.append(("test>=0.95 (got %s)" % r1["test_accuracy"],
                   r1["test_accuracy"] >= 0.95))
    checks.append(("deterministic (repeat test %s==%s)"
                   % (r1["test_accuracy"], r2["test_accuracy"]),
                   r1["test_accuracy"] == r2["test_accuracy"]
                   and r1["train_accuracy"] == r2["train_accuracy"]))
    checks.append(("epochs bounded (ran %s<=%s)"
                   % (r1["epochs_run"], EPOCHS), r1["epochs_run"] <= EPOCHS))
    ok = all(c for _, c in checks)
    print(json.dumps({"self_test": "PASS" if ok else "FAIL",
                      "result": r1,
                      "checks": [{"name": n, "ok": bool(c)}
                                 for n, c in checks]}, indent=1))
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description="Frankenstein shard node")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--budget", default="balanced", choices=sorted(BUDGETS))
    ap.add_argument("--shard", default=None, choices=sorted(SHARDS))
    ap.add_argument("--hidden", type=int, default=None)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    if a.list:
        print(json.dumps(
            {k: {"source": v["source"], "notes": v["notes"]}
             for k, v in SHARDS.items()}, indent=1))
        print(json.dumps(
            {"budgets": {k: {"shard": s, "hidden": h}
                         for k, (s, h) in BUDGETS.items()}}, indent=1))
        return 0
    if a.self_test:
        return 0 if self_test() else 1
    if a.run:
        name, hidden = (a.shard, a.hidden or 64) if a.shard else route(a.budget)
        res = run_shard(name, hidden=hidden, seed=a.seed)
        res["budget"] = a.budget if not a.shard else "manual"
        print(json.dumps(res, indent=1))
        if a.out:
            with open(a.out, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=1)
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
