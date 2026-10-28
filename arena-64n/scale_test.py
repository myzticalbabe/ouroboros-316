"""Scale sweep: how big a net can we have on sklearn digits, same contract as solution.py."""
import json, time
import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

SEED = 7
EPOCHS = 60
BATCH = 64
LR = 0.01
B1, B2, EPS = 0.9, 0.999, 1e-8
PATIENCE = 8
SIZES = [16, 32, 64, 128, 256, 512, 1024, 2048, 4096]

X, y = load_digits(return_X_y=True)
X = X / 16.0
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=SEED, stratify=y)
n, din = Xtr.shape
ncls = 10
Ytr = np.eye(ncls)[ytr]

def run_one(HIDDEN):
    rng = np.random.default_rng(SEED)
    lim1 = np.sqrt(6.0 / (din + HIDDEN))
    lim2 = np.sqrt(6.0 / (HIDDEN + ncls))
    W1 = rng.uniform(-lim1, lim1, (din, HIDDEN)); b1 = np.zeros(HIDDEN)
    W2 = rng.uniform(-lim2, lim2, (HIDDEN, ncls)); b2 = np.zeros(ncls)
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
            idx = perm[s:s+BATCH]
            xb, yb = Xtr[idx], Ytr[idx]
            m = len(idx)
            h = np.tanh(xb @ W1 + b1)
            z = h @ W2 + b2
            z -= z.max(axis=1, keepdims=True)
            p = np.exp(z); p /= p.sum(axis=1, keepdims=True)
            dz = (p - yb) / m
            gW2, gb2 = h.T @ dz, dz.sum(axis=0)
            dh = (dz @ W2.T) * (1.0 - h ** 2)
            gW1, gb1 = xb.T @ dh, dh.sum(axis=0)
            for g, mv, vv in ((gW1, mW1, vW1), (gb1, mb1, vb1), (gW2, mW2, vW2), (gb2, mb2, vb2)):
                mv[:] = B1*mv + (1-B1)*g
                vv[:] = B2*vv + (1-B2)*g*g
            W1 -= LR*(mW1/(1-B1**step))/(np.sqrt(vW1/(1-B2**step))+EPS)
            b1 -= LR*(mb1/(1-B1**step))/(np.sqrt(vb1/(1-B2**step))+EPS)
            W2 -= LR*(mW2/(1-B1**step))/(np.sqrt(vW2/(1-B2**step))+EPS)
            b2 -= LR*(mb2/(1-B1**step))/(np.sqrt(vb2/(1-B2**step))+EPS)
        epochs_run = epoch + 1
        acc = train_acc()
        if acc > best_acc + 1e-6:
            best_acc, best_w, best_ep = acc, (W1.copy(), b1.copy(), W2.copy(), b2.copy()), epochs_run
        elif epochs_run - best_ep >= PATIENCE:
            break
    secs = time.time() - t0
    W1, b1, W2, b2 = best_w
    pte = np.argmax(np.tanh(Xte @ W1 + b1) @ W2 + b2, axis=1)
    test = float((pte == yte).mean())
    params = int(din*HIDDEN + HIDDEN + HIDDEN*ncls + ncls)
    return {"hidden": HIDDEN, "params": params, "train_accuracy": round(best_acc,4),
            "test_accuracy": round(test,4), "seconds": round(secs,1),
            "epochs_run": epochs_run, "best_epoch": best_ep}

results = []
for h in SIZES:
    r = run_one(h)
    results.append(r)
    print(f"H={h:5d} params={r['params']:8d} train={r['train_accuracy']} test={r['test_accuracy']} secs={r['seconds']} epochs={r['epochs_run']}", flush=True)

with open("scale_results.json", "w") as f:
    json.dump(results, f, indent=1)
print("SWEEP done")
