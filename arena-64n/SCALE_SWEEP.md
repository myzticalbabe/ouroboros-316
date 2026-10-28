# Neuron scale sweep — recorded 2026-10-27 (user-ordered, keep for future circumstances)

Same contract as arena solution: sklearn digits, 80/20 stratified split, seed 7,
numpy tanh / Xavier / mini-batch Adam, early-stop patience 8, max 60 epochs.
Runner: `scale_test.py` → `scale_results.json`.

| Hidden | Params | Train | Test | Secs | Epochs |
|---|---|---|---|---|---|
| 16 | 1210 | 1.0 | 0.9778 | 0.1 | 45 |
| 32 | 2410 | 1.0 | 0.9861 | 0.1 | 35 |
| 64 | 4810 | 1.0 | 0.9833 | 0.1 | 30 |
| 128 | 9610 | 1.0 | 0.9889 | 0.3 | 29 |
| 256 | 19210 | 0.9972 | 0.9778 | 0.4 | 21 |
| 512 | 38410 | 0.9965 | 0.9806 | 1.3 | 21 |
| 1024 | 76810 | 0.9854 | 0.9556 | 2.2 | 18 |
| 2048 | 153610 | 0.9819 | 0.9556 | 6.9 | 24 |
| 4096 | 307210 | 0.9770 | 0.9500 | 11.6 | 22 |

Recorded findings:
- Measured peak accuracy: H=128, test 0.9889.
- Sweet spot: 32–128 (32 matches 64 at half the params).
- Degrades past 512; 1024+ falls to ~0.95 (dataset too small to fill the net).
- Biggest verified working: 4096 hidden / 307k params / ~12s CPU. Larger (8k/16k) untested, RAM-trivial (~10MB at 16k).
- Kept for other circumstances: rerun `scale_test.py` with extended SIZES if a bigger net is ever needed.
