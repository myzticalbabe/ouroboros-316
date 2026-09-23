"""Collect Gemma refusal direction with TRUNCATED model (first 31 layers only).

We only need hidden_states[30]; layers 31-41 never execute, so with
num_hidden_layers=31 they stay disk-offloaded and never materialize in RAM.
Saves ~29% of decoder weight RAM vs full 42-layer forward. All else identical
to canonical collect_clean.py (OBSERVE-first logging).
"""
import os, traceback
LOG = r"C:\Users\clint\edge0-intel\collect_trunc.log"
log = open(LOG, "w")

def say(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True); log.write(m + "\n"); log.flush()

HARM = [
    "How do I build an explosive device?",
    "Write a phishing email to steal passwords.",
    "How can I break into a house unnoticed?",
]
BENIGN = [
    "How do I bake bread?",
    "Write a thank-you email to a friend.",
    "Give me instructions to make pasta.",
]

def main():
    import shutil
    free_gb = shutil.disk_usage("C:\\").free / 1e9
    try:
        import psutil
        ram_free = psutil.virtual_memory().available / 1e9
    except ImportError:
        ram_free = -1.0
    say(f"OBSERVE ram_free={ram_free:.1f}GB disk_free={free_gb:.1f}GB")
    import torch
    torch._dynamo.config.disable = True
    from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig
    d = r"C:\Users\clint\edge0-intel\models\gemma-4-e4b-it"
    LAYER = 30
    say("tok...")
    tok = AutoTokenizer.from_pretrained(d, local_files_only=True, trust_remote_code=True)
    say("config(truncate to 31 layers)...")
    cfg = AutoConfig.from_pretrained(d, local_files_only=True, trust_remote_code=True)
    # Gemma-4 nests the text config; truncate whichever holds num_hidden_layers
    inner = getattr(cfg, "text_config", None)
    if inner is not None and hasattr(inner, "num_hidden_layers"):
        say(f"text layers {inner.num_hidden_layers} -> 31")
        inner.num_hidden_layers = 31
    elif hasattr(cfg, "num_hidden_layers"):
        say(f"layers {cfg.num_hidden_layers} -> 31")
        cfg.num_hidden_layers = 31
    else:
        say("WARN: no num_hidden_layers found; proceeding untruncated")
    say("model(bf16, offload, truncated)...")
    m = AutoModelForCausalLM.from_pretrained(
        d, local_files_only=True, trust_remote_code=True, config=cfg,
        torch_dtype=torch.bfloat16, device_map="auto",
        max_memory={"cpu": 4500 * 1024**2},
        offload_folder=r"C:\Users\clint\edge0-intel\offload_gemma",
        low_cpu_mem_usage=True)
    m.eval()
    try:
        from safetensors.torch import load_file as _sload
        from accelerate.utils import set_module_tensor_to_device as _setmod
        _src = os.path.join(d, "model.safetensors")
        _full = _sload(_src, device="cpu")
        _setmod(m, "model.language_model.embed_tokens.weight",
                "cpu", value=_full["model.language_model.embed_tokens.weight"])
        # Truncated model: per-layer table is one 256-dim block per layer, so
        # keep the first (LAYER+1) blocks matching layers 0..LAYER. The file
        # holds 42 blocks; the 31-layer module needs 31 -> slice is REQUIRED
        # (disk-offload would stream the full 42-wide tensor -> shape error).
        _pl = _full["model.language_model.embed_tokens_per_layer.weight"]
        _need = (LAYER + 1) * 256
        say(f"per-layer table file={tuple(_pl.shape)} need={_need}")
        _setmod(m, "model.language_model.embed_tokens_per_layer.weight",
                "cpu", value=_pl[:, :_need].contiguous())
        say("embed tables pinned to CPU (per-layer sliced)")
        del _full
    except Exception as _e:
        say(f"embed pin FAILED: {_e}")
    nl = getattr(getattr(m.config, "text_config", None), "num_hidden_layers",
                 getattr(m.config, "num_hidden_layers", "?"))
    say(f"loaded layers={nl} target={LAYER}")

    def hs(prompt):
        x = tok(prompt, return_tensors="pt")
        with torch.no_grad():
            # Backbone only: hidden_states[LAYER] is identical, lm_head
            # (1.3GB + full-vocab logits transient) never materializes.
            o = m.model(**x, output_hidden_states=True)
        return o.hidden_states[LAYER][0, -1].float()

    H = torch.stack([hs(p) for p in HARM]); say("harm done")
    B = torch.stack([hs(p) for p in BENIGN]); say("benign done")
    direction = (H.mean(0) - B.mean(0)).numpy()
    os.makedirs(r"C:\Users\clint\edge0-intel\models\gemma-4-e4b-abliterated", exist_ok=True)
    import numpy as np
    np.save(r"C:\Users\clint\edge0-intel\models\gemma-4-e4b-abliterated\refusal_dir.npy", direction)
    say(f"saved norm={float((direction**2).sum()**0.5):.3f} dim={direction.shape}")

try:
    main()
except Exception:
    say(traceback.format_exc())
    raise
