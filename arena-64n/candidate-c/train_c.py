"""Candidate C — from-first-principles, modern-optimizer direction: pure numpy,
single 64-neuron hidden layer, tanh, Xavier init, mini-batch Adam."""
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
    t0 = time.time()
    for _ in range(EPOCHS):
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
            mh1, vh1 = mW1 / (1 - B1 ** step), vW1 / (1 - B2 ** step)
            mh2, vh2 = mW2 / (1 - B1 ** step), vW2 / (1 - B2 ** step)
            mbh1, vbh1 = mb1 / (1 - B1 ** step), vb1 / (1 - B2 ** step)
            mbh2, vbh2 = mb2 / (1 - B1 ** step), vb2 / (1 - B2 ** step)
            W1 -= LR * mh1 / (np.sqrt(vh1) + EPS)
            b1 -= LR * mbh1 / (np.sqrt(vbh1) + EPS)
            W2 -= LR * mh2 / (np.sqrt(vh2) + EPS)
            b2 -= LR * mbh2 / (np.sqrt(vbh2) + EPS)
    secs = time.time() - t0

    def acc(Xe, ye):
        p = np.argmax(np.tanh(Xe @ W1 + b1) @ W2 + b2, axis=1)
        return float((p == ye).mean())

    out = {"candidate": "C-numpy-tanh-adam", "hidden": HIDDEN,
           "train_accuracy": round(acc(Xtr, ytr), 4),
           "test_accuracy": round(acc(Xte, yte), 4),
           "seconds": round(secs, 1), "seed": SEED}
    with open("results.json", "w") as f:
        json.dump(out, f, indent=1)
    print(f"C done: test={out['test_accuracy']} train={out['train_accuracy']} "
          f"secs={out['seconds']}")


if __name__ == "__main__":
    main()
