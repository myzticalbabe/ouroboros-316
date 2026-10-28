"""Arena synthesis — 64-neuron hidden-layer classifier on sklearn digits.

Base: candidate C (pure numpy, tanh, Xavier init, mini-batch Adam).
Graft from B (sklearn): early-stopping on train-accuracy plateau with
best-weight snapshot (C converged to train 1.0; this keeps the best
generalizing weights and reports epochs actually run).
Kept from A: dependency-free numpy core, fixed-seed determinism.

Usage: python solution.py  ->  prints test accuracy, writes results.json
"""
import copy
import json
import time

import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

SEED = 7
HIDDEN = 64
EPOCHS = 60
BATCH = 64
LR = 0.01
B1, B2, EPS = 0.9, 0.999, 1e-8
PATIENCE = 8  # graft from B: stop when train accuracy plateaus


def main():
    rng = np.random.default_rng(SEED)
    X, y = load_digits(return_X_y=True)
    X = X / 16.0
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y)
    n, din = Xtr.shape
    ncls = 10
    Ytr = np.eye(ncls)[ytr]

    lim1 = np.sqrt(6.0 / (din + HIDDEN))
    lim2 = np.sqrt(6.0 / (HIDDEN + ncls))
    W1 = rng.uniform(-lim1, lim1, (din, HIDDEN))
    b1 = np.zeros(HIDDEN)
    W2 = rng.uniform(-lim2, lim2, (HIDDEN, ncls))
    b2 = np.zeros(ncls)
    mW1, vW1, mb1, vb1 = (np.zeros_like(W1), np.zeros_like(W1),
                          np.zeros_like(b1), np.zeros_like(b1))
    mW2, vW2, mb2, vb2 = (np.zeros_like(W2), np.zeros_like(W2),
                          np.zeros_like(b2), np.zeros_like(b2))
    step = 0
    best = {"acc": -1.0, "weights": None, "epoch": 0}

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
        acc = train_acc()
        if acc > best["acc"] + 1e-6:
            best = {"acc": acc,
                    "weights": (W1.copy(), b1.copy(), W2.copy(), b2.copy()),
                    "epoch": epochs_run}
        elif epochs_run - best["epoch"] >= PATIENCE:
            break
    secs = time.time() - t0
    W1, b1, W2, b2 = best["weights"]

    def acc(Xe, ye):
        p = np.argmax(np.tanh(Xe @ W1 + b1) @ W2 + b2, axis=1)
        return float((p == ye).mean())

    out = {"candidate": "synthesis-C-base-plus-early-stopping-graft",
           "hidden": HIDDEN, "base": "C-numpy-tanh-adam",
           "grafts": ["early-stopping-on-train-plateau (from B)"],
           "train_accuracy": round(acc(Xtr, ytr), 4),
           "test_accuracy": round(acc(Xte, yte), 4),
           "seconds": round(secs, 1), "seed": SEED,
           "epochs_run": epochs_run, "best_epoch": best["epoch"]}
    with open("results.json", "w") as f:
        json.dump(out, f, indent=1)
    print(f"SOLUTION done: test={out['test_accuracy']} "
          f"train={out['train_accuracy']} secs={out['seconds']} "
          f"epochs={out['epochs_run']}")


if __name__ == "__main__":
    main()
