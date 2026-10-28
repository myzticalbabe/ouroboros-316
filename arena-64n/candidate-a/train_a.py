"""Candidate A — from-first-principles direction: pure numpy, single 64-neuron
hidden layer, ReLU, He init, full-batch SGD, softmax cross-entropy."""
import json
import time

import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

SEED = 7
HIDDEN = 64
EPOCHS = 400
LR = 0.5


def main():
    rng = np.random.default_rng(SEED)
    X, y = load_digits(return_X_y=True)
    X = X / 16.0
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y)
    n, din = Xtr.shape
    ncls = 10
    Ytr = np.eye(ncls)[ytr]

    W1 = rng.normal(0, np.sqrt(2.0 / din), (din, HIDDEN))
    b1 = np.zeros(HIDDEN)
    W2 = rng.normal(0, np.sqrt(2.0 / HIDDEN), (HIDDEN, ncls))
    b2 = np.zeros(ncls)

    t0 = time.time()
    for _ in range(EPOCHS):
        h = np.maximum(Xtr @ W1 + b1, 0.0)
        z = h @ W2 + b2
        z -= z.max(axis=1, keepdims=True)
        p = np.exp(z)
        p /= p.sum(axis=1, keepdims=True)
        dz = (p - Ytr) / n
        dW2 = h.T @ dz
        db2 = dz.sum(axis=0)
        dh = (dz @ W2.T) * (h > 0)
        dW1 = Xtr.T @ dh
        db1 = dh.sum(axis=0)
        W2 -= LR * dW2
        b2 -= LR * db2
        W1 -= LR * dW1
        b1 -= LR * db1
    secs = time.time() - t0

    def acc(Xe, ye):
        p = np.argmax(np.maximum(Xe @ W1 + b1, 0.0) @ W2 + b2, axis=1)
        return float((p == ye).mean())

    out = {"candidate": "A-numpy-relu-sgd", "hidden": HIDDEN,
           "train_accuracy": round(acc(Xtr, ytr), 4),
           "test_accuracy": round(acc(Xte, yte), 4),
           "seconds": round(secs, 1), "seed": SEED}
    with open("results.json", "w") as f:
        json.dump(out, f, indent=1)
    print(f"A done: test={out['test_accuracy']} train={out['train_accuracy']} "
          f"secs={out['seconds']}")


if __name__ == "__main__":
    main()
