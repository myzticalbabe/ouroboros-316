# RAM Runbook + Future-Dev Principles (2026-09-23)

## The incident that wrote this
Gemma torch-forward died 8 times across 2.4/7.4/10.7/10.9 GB free. Assumed
OOM for 6 of those runs. Windows Event Log then showed the truth:
`torch_cpu.dll, 0xc0000005` — native segfault, plus a meta-device
`torch.where` crash. RAM was never the (only) killer. Lesson: MEASURE,
don't theorize (see Principles).

## RAM runbook (this machine: 15.4 GB total, ~10-11 GB attainable free)
1. Identify holders: `Get-Process | Sort WorkingSet64 -Desc`. Usual suspect
   is our own llama-server (9.4 GB for 7.6 GB F16 GGUF; 6 GB for 5 GB Q4).
2. Free RAM by REVERSIBLE means first: stop fitness backends (`:8089`/`:8090`)
   before any big job. Never serve + collect simultaneously.
3. Verify: OBSERVE line (`ram_free=XGB`) at the top of every workload log.
   No OBSERVE = untrusted run.
4. Budget rule: need ≈ weights×1.0 resident + 2 GB headroom. If need > free,
   shrink the job (truncation, fewer residents) — don't hope.
5. Reboot is authorized when compression/standby eats free (2026-09-22:
   2.4 → 7.4 GB). Check boot time: `systeminfo | findstr Boot`.
6. ONE run at a time. Two concurrent 3.14t surgeries (double double-click)
   fought over one 5 GB file for 40 min at 1 core each. Click once.
7. Kill strays before starting: duplicate PIDs, dead servers holding ports.

## Principles (adopted — violations are bugs)
1. **No silent runs.** Unbuffered (`-u`), staged prints from second zero,
   per-unit progress. A run that can't say where it is can't be debugged.
   (Cost of learning this: one full day.)
2. **One run, one window.** Detached + visible console for long jobs
   (`RUN_*.bat` pattern with `pause`); no second launch until the first
   resolves.
3. **Evidence before synthesis.** Event Log > log text > theory. The
   PREFLIGHT gate wrote plausible math that was wrong about the mechanism.
4. **Controls for every claim.** N>=50 fitness; stock N=100 baseline before
   declaring any effect. Subset baselines are junk (measured 3.5x error).
5. **Abandon dead paths; don't patch them.** 8 accelerate failures →
   STRATUM replaced the stack instead of a 9th patch. Patch budget: 3,
   then replace.
6. **Ledger everything.** Every eval appends to `evolve_log.jsonl` with tag.
   Unledgered runs didn't happen.
7. **Fix classes, not instances.** transpose bug → regression test 5;
   parse_kv crash → library parsing; GGUF.* corruption → skip + comment.
   Each fix must make its bug un-reproducible, with a test where possible.
8. **Byte-exactness is proven, not assumed.** Roundtrip + re-parse + serve
   before any claim of a working artifact (s10 served only after dims+KV
   verified; the corrupt build was caught by re-parse, not by serving).
