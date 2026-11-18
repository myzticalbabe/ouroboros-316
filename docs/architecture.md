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

## Limitations
C/Rust components (base VM, shared-lib adapters, .so loading) are not built:
no C/C++/Rust toolchain is available in this environment. The Python-level
scaffold proves the concept end-to-end via subprocess interpreters.