# Ouroboros-316

Unified multi-version Python runtime (scaffold). Implements the design in
`C:/tmp/OUROBOROS_316_DESIGN.md` at the Python level:

- Version discovery across installed interpreters (via `py` launcher + known paths)
- Cross-version marshaling (tagged JSON, stdlib-only, works 3.8-3.16t)
- Sequential execution engine running a DAG of version-annotated steps
- `.owh` package format (zip with `ouroboros.json` metadata)

## Usage

```sh
python -m ouroboros versions
python -m ouroboros run examples/plan.json
python -m ouroboros make-owh metadata.json -o out.owh
```

## Tests

```sh
python -m pytest ouroboros/tests
```
