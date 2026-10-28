"""Candidate B — battle-tested-library direction: sklearn MLPClassifier with a
single 64-neuron hidden layer, adam solver, early stopping."""
import json
import time

from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier

SEED = 7
HIDDEN = 64


def main():
    X, y = load_digits(return_X_y=True)
    X = X / 16.0
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y)
    clf = MLPClassifier(hidden_layer_sizes=(HIDDEN,), activation="relu",
                        solver="adam", alpha=1e-4, batch_size=64,
                        max_iter=300, early_stopping=True, n_iter_no_change=20,
                        random_state=SEED)
    t0 = time.time()
    clf.fit(Xtr, ytr)
    secs = time.time() - t0
    out = {"candidate": "B-sklearn-mlp-adam", "hidden": HIDDEN,
           "train_accuracy": round(float(clf.score(Xtr, ytr)), 4),
           "test_accuracy": round(float(clf.score(Xte, yte)), 4),
           "seconds": round(secs, 1), "seed": SEED,
           "n_iter": int(clf.n_iter_)}
    with open("results.json", "w") as f:
        json.dump(out, f, indent=1)
    print(f"B done: test={out['test_accuracy']} train={out['train_accuracy']} "
          f"secs={out['seconds']} iters={out['n_iter']}")


if __name__ == "__main__":
    main()
