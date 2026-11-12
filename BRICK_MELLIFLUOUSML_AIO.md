# BRICK — MellifluousML A-I-O Optimal Model Set (measured 2026-11-12)

**Purpose:** architecturally analyze EVERY local model, keep the optimal
All-In-One set for MellifluousML evolution, brick (distill-then-delete) the
rest. C: is at 6.4GB free; the memory-backup 10GB floor cannot pass until
~15GB is reclaimed. This file is the execution authority for the brick.

## 1. Measured inventory (all stores, `du` + `ollama list`)

| Store | Contents | Size |
|---|---|---|
| Ollama (`ollama list`) | eve-v2u 3.4GB, olmoe 3.0GB, qwen3-embedding:0.6b 639MB, nomic-embed-text 274MB | ~7.3GB logical / 3.7GB blobs |
| `llama-server/models/` | ov_export 12GB, gemma-4-12B 6.0GB, InternVL3-8B 5.0GB, Eve-V2-Unleashed 4.1GB, Bonsai-27B 3.6GB, gemma-4-E2B 2.8GB, Spark-X2.5-4B 2.5GB, Qwen3-4B-Abliterated 2.4GB, Qwen2.5-1.5B 1.1GB, mxbai-embed-large-v1 206MB, nomic-embed-text-v1.5 81MB, .cache 107MB | ~43GB |
| `~/.lmstudio/models/` | mradermacher 5.6GB, gemma-4-E4B-it 5.4GB, Heretic-Llama3.3-8B 4.4GB, Qwen2.5-Coder-7B 4.4GB, lmstudio-community 4.2GB, unsloth 3.7GB, BennyDaBall 2.3GB, bartowski 0 | ~30GB |
| `~/.cache/huggingface/hub` | blip-image-captioning-base, cross-encoder ms-marco-MiniLM-L-6-v2, distilbert-sst2, mxbai-embed-large-v1, paraphrase-multilingual-MiniLM-L12-v2 | 1.6GB |

**Total: ~81GB of models. The A-I-O set below needs ~9GB. Brick frees ~55GB+.**

## 2. Architectural analysis — every model mapped to its consumer

- **CHAT (live):** `llama-server/models/gemma-4-E2B` (2.8GB) — active per
  `~/.lmstudio/models/use_model.dat`. Sole instruct path. PROTECT.
- **EMBED (live):** `llama-server/models/mxbai-embed-large-v1` (206MB, 1024-dim)
  — serves PAMS `:8080`. HF hub copy is its regenerable source. PROTECT both.
- **RERANK (live):** HF `cross-encoder ms-marco-MiniLM-L-6-v2` — retrieval
  stack. PROTECT (KBs–MBs, part of 1.6GB HF set).
- **MULTILINGUAL (live):** HF `paraphrase-multilingual-MiniLM-L12-v2` —
  symmetric search. PROTECT.
- **VISION (live):** HF `blip-image-captioning-base` — captioning organ.
  PROTECT. (`InternVL3-8B` 5.0GB is the heavy alternative — brick unless a
  lane proves it in use.)
- **SENTIMENT (live):** HF `distilbert-sst-2` — classifier organ. PROTECT.
- **EVE (live):** `Eve-V2-Unleashed` 4.1GB **duplicates** Ollama `eve-v2u`
  3.4GB — same weights, two copies. Keep ONE (llama-server copy, native
  path), brick the Ollama copy after weight-hash match.
- **DEAD (no consumer):** `ov_export/*` (12GB regenerable MXBAI exports),
  Ollama `olmoe` (7 wks untouched), Ollama `nomic-embed-text` (superseded by
  mxbai+qwen), `Bonsai-27B`, `Spark-X2.5-4B`, `Qwen3-4B-Abliterated`,
  `Qwen2.5-1.5B`, `gemma-4-12B` (E2B is the chosen gemma), all 30GB LMStudio
  publishers (work happens on the llama-server copy).

## 3. A-I-O optimal set (keep — ~9GB)

gemma-4-E2B (chat) + mxbai-embed-large-v1 (embed) + cross-encoder (rerank) +
paraphrase-multilingual (search) + blip (vision) + distilbert (sentiment) +
Eve-V2-Unleashed single copy (evolution subject). One organ per function —
that is what All-In-One means.

## 4. Brick order (distill recipe, then delete; verify after each)

1. `rm -rf ~/llama-server/models/ov_export` → +12GB (artifacts, respawn via
   export script; live mxbai untouched).
2. `ollama rm sam860/olmoe-1b-7b-0924:latest` → +3.0GB.
3. `ollama rm nomic-embed-text:latest` → +274MB (mxbai+qwen cover embed).
4. Eve dedupe: `sha256sum` both Eve weight files; if match,
   `ollama rm eve-v2u:latest` → +3.4GB (native copy stays).
5. `InternVL3-8B`, `Bonsai-27B`, `Spark-X2.5-4B`, `Qwen3-4B-Abliterated`,
   `Qwen2.5-1.5B`, `gemma-4-12B` → +20.5GB (no live consumer; blip covers
   vision; E2B covers chat).
6. LMStudio publisher dirs → +~30GB (llama-server copy is the work copy).
7. Re-run `memory_backup.py` (floor should pass), then restart for 3.7.1.

**Evolve note (E2R-9, native instruments only):** bricking is deletion, not
training. MellifluousML evolution itself runs through the developed loop
(`eve bypass` / `eve e2e`, GeneticAlgorithm on live experience) — this brick
only clears the disk so that loop can run and its logs can persist.

## 5. Verification (commands that prove each claim)

- `ollama list` — remaining set matches §3 + §4 holds.
- `cat ~/.lmstudio/models/use_model.dat` — still gemma-4-E2B.
- `curl localhost:8080/v1/embeddings` (PAMS health) — embed path alive.
- `C:/Azazael/.venvs/py316t/Scripts/python.exe C:/Azazael/azazael/tools/memory_backup.py` — exit 0, floor passes.
