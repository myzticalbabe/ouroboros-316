# Ouroboros-316 Architecture

## Layers
- Layer 0: Base VM (platform abstraction) — *planned, not implemented (requires C/Rust)*
- Layer 1: Version adapters — implemented as subprocess-based `VersionAdapter`
- Layer 2: Sequential execution engine — `SequentialEngine` with DAG + checkpointing
- Layer 3: `.owh` package format — `OwhPackage`
- Layer 4: Base interpreter host — *planned (Python 3.6 host, requires C)*

## Python-level components (implemented)
- `versions.py` — interpreter discovery
- `marshal.py` — tagged-JSON cross-version marshaler
- `adapter.py` — subprocess adapter
- `plan.py` — DAG plan
- `engine.py` — executor (sequential + parallel, retries, checkpointing)
- `checkpoint.py` — per-step state checkpoints
- `owh.py` — package format + assembler
- `validate.py` — schema validation
- `cli.py` — CLI

## Available versions
All of 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14, 3.14t, 3.15, 3.15t,
3.16t. Python 3.6.8 and 3.7.9 were installed from python.org installers.

## Limitations
The C host embeds CPython 3.14 specifically. True in-process multi-version
embedding (loading libpython for multiple versions in one process) is not
implemented due to ABI symbol conflicts; adapters run as subprocesses.