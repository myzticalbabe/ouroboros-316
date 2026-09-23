"""GGUF-domain abliteration (fast iteration loop: edit -> serve -> eval).

- Reads src GGUF, dequantizes target tensors to fp32, projects refusal dir,
  writes back as F16 (no requant risk), copies all other tensors byte-identical
  and all KV metadata generically. s=0 roundtrip must serve+eval == baseline.
- Refusal dim 1536: rule per tensor — 1536 on axis1 -> W -= s*outer(W@r, r);
  on axis0 -> W -= s*outer(r, W.T@r); else skip.
- Targets: blk.N.attn_output.weight + blk.N.ffn_down_exps.weight (+shexp).

Usage:
  python scripts/gguf_abliterate.py --src FILE --dst FILE --dir refusal.npy
    --strength 1.0 [--dry]   (dry = s=0 roundtrip validation)
"""
import os
import numpy as np

TYPE_MAP = {0: "u8", 1: "i8", 2: "u16", 3: "i16", 4: "u32", 5: "i32",
            6: "f32", 7: "bool", 8: "str", 9: "array", 10: "u64", 11: "i64",
            12: "f64"}


def _raw(parts, i):
    return np.frombuffer(parts[i], dtype=np.uint8).tobytes()


def _u(parts, i):
    return int.from_bytes(_raw(parts, i)[:8], "little")


def _u32(parts, i):
    return int.from_bytes(_raw(parts, i)[:4], "little")


def _bytes(parts, i):
    return _raw(parts, i)


def parse_kv(parts):
    """parts -> (key, type_enum, value) or None for pseudo/header fields.
    scalar [klen][key][type][val]; string [klen][key][8][len][bytes];
    array [klen][key][9][arrtype][len][item...] (one part per item)."""
    if len(parts) < 4:
        return None
    key = _raw(parts, 1).decode()
    t = _u32(parts, 2)
    if t == 8:  # string
        n = _u(parts, 3)
        return key, t, _raw(parts, 4)[:n].decode()
    if t == 9:  # array
        at = _u32(parts, 3)
        n = _u(parts, 4)
        items = parts[5:5 + n]
        if at == 8:
            # byte-exact: items arrive as [len,value] part pairs
            out, rest = [], parts[5:]
            import struct as _st
            while rest and len(out) < n:
                ln = _st.unpack("<Q", bytes(bytearray(_raw(rest, 0)))[:8])[0] \
                    if len(_raw(rest, 0)) >= 8 else None
                if ln is None:
                    break
                data = _raw(rest, 1) if len(rest) > 1 else b""
                out.append(bytes(data[:ln]))
                rest = rest[2:]
            if len(out) != n:  # fallback: bare-bytes items, no len parts
                out = [np.frombuffer(p, dtype=np.uint8).tobytes()
                       for p in parts[5:5 + n]]
            return key, t, (at, out)
        dt = {"u8": np.uint8, "i8": np.int8, "u16": np.uint16, "i16": np.int16,
              "u32": np.uint32, "i32": np.int32, "f32": np.float32,
              "bool": np.bool_, "u64": np.uint64, "i64": np.int64,
              "f64": np.float64}[TYPE_MAP[at]]
        vals = [np.frombuffer(p, dtype=dt, count=1)[0].item() for p in items]
        return key, t, (at, vals)
    if t == 7:
        return key, t, bool(_raw(parts, 3)[0])
    dt = {"u8": np.uint8, "i8": np.int8, "u16": np.uint16, "i16": np.int16,
          "u32": np.uint32, "i32": np.int32, "f32": np.float32,
          "u64": np.uint64, "i64": np.int64, "f64": np.float64}[TYPE_MAP[t]]
    return key, t, np.frombuffer(_raw(parts, 3), dtype=dt, count=1)[0].item()


def copy_kv(writer, key, t, val):
    if t == 8:
        writer.add_string(key, val)
    elif t == 7:
        writer.add_bool(key, val)
    elif t == 9:
        at, vals = val
        if at == 8:
            writer.add_array(key, vals)
        else:
            writer.add_array(key, vals)
    elif TYPE_MAP[t] == "u8":
        writer.add_uint8(key, int(val))
    elif TYPE_MAP[t] == "u16":
        writer.add_uint16(key, int(val))
    elif TYPE_MAP[t] == "u32":
        writer.add_uint32(key, int(val))
    elif TYPE_MAP[t] == "u64":
        writer.add_uint64(key, int(val))
    elif TYPE_MAP[t] == "i8":
        writer.add_int8(key, int(val))
    elif TYPE_MAP[t] == "i16":
        writer.add_int16(key, int(val))
    elif TYPE_MAP[t] == "i32":
        writer.add_int32(key, int(val))
    elif TYPE_MAP[t] == "i64":
        writer.add_int64(key, int(val))
    elif TYPE_MAP[t] in ("f32", "f64"):
        writer.add_float32(key, float(val))


def ablaterate_gguf(W2d_or_3d, r, strength):
    """Apply output-side projection along whichever axis is 1536.

    NOTE: gguf.quants.dequantize returns arrays in REVERSED dim order vs the
    GGUF metadata (t.shape). E.g. t.shape (2048,1536) -> dq.shape (1536,2048);
    fused experts t.shape (512,1536,128) -> dq.shape (128,1536,512) with the
    expert axis FIRST. Callers must pass dq as-is (never .reshape(t.shape) —
    that scrambles row-major data AND flips stored dims, producing unloadable
    files). GGUFWriter stores numpy shape reversed, so writing dq-orientation
    arrays back with raw_shape=None reproduces the original metadata dims.
    """
    W = np.asarray(W2d_or_3d, dtype=np.float32)
    r = np.asarray(r, dtype=np.float32)
    rh = r / (np.linalg.norm(r) + 1e-12)
    if W.ndim == 2:
        a0 = W.shape[0] == rh.shape[0]
        a1 = W.shape[1] == rh.shape[0]
        if not (a0 ^ a1):
            raise ValueError(f"no refusal axis in {W.shape} for dim {rh.shape[0]}")
        if a1:
            return (W - strength * np.outer(W @ rh, rh))
        return (W - strength * np.outer(rh, W.T @ rh))
    # fused experts in DEQUANTIZED orientation: expert axis FIRST
    # (dq.shape (E, O, I); GGUF metadata is the reverse (I, O, E)).
    # Per-expert slice dq[e] is 2D and handled by the branch above.
    outs = []
    for e in range(W.shape[0]):
        outs.append(ablaterate_gguf(W[e], r, strength)[None, ...])
    return np.concatenate(outs, axis=0)


def main():
    import argparse
    import faulthandler as _fh
    _fh.dump_traceback_later(300, exit=True)  # auto-dump if hung >5min
    say = lambda m: (print(m, flush=True))
    import sys as _sys
    say(f"stage: startup gil_enabled={_sys._is_gil_enabled() if hasattr(_sys, '_is_gil_enabled') else '?'}")
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--dst", required=True)
    ap.add_argument("--dir", default="")
    ap.add_argument("--strength", type=float, default=0.0)
    ap.add_argument("--targets", default="attn_output.weight,ffn_down_exps.weight,ffn_down_shexp.weight")
    ap.add_argument("--layers", default="all",
                    help="'all' or comma list / range (e.g. '5' or '0-7,22'). "
                         "Limits surgery to blk.N tensors (per-layer map).")
    a = ap.parse_args()
    from gguf import GGUFReader, GGUFWriter, GGMLQuantizationType
    import gguf.quants as Q
    r = np.load(a.dir) if a.dir else None
    say(f"stage: refusal loaded dim={r.shape if r is not None else None}")
    reader = GGUFReader(a.src)
    say(f"stage: reader done tensors={len(reader.tensors)}")
    arch = None
    kv = []
    for k, f in reader.fields.items():
        # Skip GGUF.* pseudo-fields (version, tensor_count, kv_count): they
        # describe the file header, not KV data. The old hand parser skipped
        # them implicitly (too few parts); writing them as real KVs corrupts
        # the output (reader: "Duplicate GGUF.version").
        if f.name.startswith("GGUF."):
            continue
        # Library-parsed metadata. The hand-rolled parse_kv() choked on
        # Gemma's string-array KV layout (traceback via parse_kv line 64);
        # field.types gives exact type enums and field.contents() parses
        # every layout the reader itself supports. String arrays are passed
        # as bytes to match the proven Ling write path.
        t = int(f.types[0])
        if t == 8:
            val = f.contents()
        elif t == 9:
            at = int(f.types[-1])
            vals = f.contents()
            if at == 8:
                vals = [s.encode("utf-8") if isinstance(s, str) else bytes(s)
                        for s in vals]
            val = (at, list(vals))
        elif t == 7:
            val = bool(f.contents())
        else:
            val = f.contents()
        key = f.name
        if key == "general.architecture":
            arch = val
        kv.append((key, t, val))
    assert arch, "no arch"
    say(f"stage: KV parsed arch={arch}")
    w = GGUFWriter(a.dst, arch)
    for key, t, val in kv:
        copy_kv(w, key, t, val)
    tgts = set(a.targets.split(","))
    edited = 0
    F16 = GGMLQuantizationType.F16
    # Parallelize over tensors: dequant + surgery are numpy/BLAS (GIL-free
    # number-crunching), so a thread pool spreads the 84 targets over all
    # cores. Results are added to the writer IN FILE ORDER afterwards, so
    # output layout is deterministic. (GPU would NOT help here: the job is
    # 5GB in / 7GB out streaming with seconds of BLAS per tensor — PCIe
    # transfer would dominate, and 2.1GB VRAM can't hold the working set.)
    import time as _time
    from concurrent.futures import ThreadPoolExecutor
    import os as _os
    _workers = min(16, _os.cpu_count() or 8)
    _tlist = list(reader.tensors)
    _nhit = sum(1 for t in _tlist
                if any(s in t.name for s in tgts) and r is not None and a.strength != 0.0)
    say = lambda m: (print(m, flush=True))
    say(f"surgery: {_nhit} targets / {len(_tlist)} tensors, {_workers} workers")
    _done = [0]

    import re as _re
    _layspec = set()
    if a.layers != "all":
        for _part in a.layers.split(","):
            _part = _part.strip()
            if "-" in _part:
                _lo, _hi = _part.split("-", 1)
                _layspec.update(range(int(_lo), int(_hi) + 1))
            elif _part != "":
                _layspec.add(int(_part))

    def _layer_ok(name):
        if not _layspec:
            return True
        m = _re.search(r"blk\.(\d+)\.", name)
        return bool(m and int(m.group(1)) in _layspec)

    def _work(t):
        name = t.name
        hit = any(s in name for s in tgts) and _layer_ok(name)
        if hit and r is not None and a.strength != 0.0:
            try:
                dq = Q.dequantize(t.data, t.tensor_type).astype(np.float32)
                new = ablaterate_gguf(dq, r, a.strength).astype(np.float16)
            except ValueError as e:
                # Dim-mismatch skip (torch-path pattern): wrong-arch or
                # non-residual tensors pass through byte-identical.
                say(f"skip {name}: {e}")
                arr = np.asarray(t.data)
                return (name, arr, tuple(arr.shape), t.tensor_type)
            _done[0] += 1
            if _done[0] % 10 == 0 or _done[0] == _nhit:
                say(f"surgery {_done[0]}/{_nhit} ({name})")
            return (name, new, None, F16)
        arr = np.asarray(t.data)
        return (name, arr, tuple(arr.shape), t.tensor_type)

    _t0 = _time.time()
    with ThreadPoolExecutor(max_workers=_workers) as _pool:
        _results = list(_pool.map(_work, _tlist))
    say(f"surgery done {_nhit} in {_time.time()-_t0:.0f}s; writing...")
    for name, arr, raw_shape, raw_dtype in _results:
        if raw_dtype is F16 and raw_shape is None:
            w.add_tensor(name, arr, raw_shape=None, raw_dtype=F16)
            edited += 1
        else:
            w.add_tensor(name, arr, raw_shape=raw_shape, raw_dtype=raw_dtype)
    w.write_header_to_file()
    w.write_kv_data_to_file()
    w.write_tensors_to_file(progress=True)
    w.close()
    print(f"done {a.dst}: edited={edited}" + (" DRY-ROUNDTRIP" if a.strength == 0.0 else ""))


if __name__ == "__main__":
    main()
