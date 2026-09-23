"""Collect Gemma refusal direction (Oxford ShardFoundry canonical version).
Contrast harmful vs benign, residual stream layer 30, diff = mean(harm)-mean(benign).
Forward-only. Out: models/gemma-4-e4b-abliterated/refusal_dir.npy.
"""
import os, traceback
LOG = r"C:\Users\clint\edge0-intel\collect_clean.log"
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
    from transformers import AutoTokenizer, AutoModelForCausalLM
    d = r"C:\Users\clint\edge0-intel\models\gemma-4-e4b-it"
    LAYER = 30
    say("tok...")
    tok = AutoTokenizer.from_pretrained(d, local_files_only=True, trust_remote_code=True)
    say("model(bf16, offload)...")
    m = AutoModelForCausalLM.from_pretrained(
        d, local_files_only=True, trust_remote_code=True,
        torch_dtype=torch.bfloat16, device_map="auto",
        max_memory={"cpu": "6GB"},
        offload_folder=r"C:\Users\clint\edge0-intel\offload_gemma",
        low_cpu_mem_usage=True)
    m.eval()
    # pin giant embed tables to CPU (disk-offload leaves them meta and the
    # multimodal merge path torch.where()s them -> meta-device crash)
    try:
        from safetensors.torch import load_file as _sload
        from accelerate.utils import set_module_tensor_to_device as _setmod
        _src = os.path.join(d, "model.safetensors")
        for _tn in ["model.language_model.embed_tokens.weight",
                    "model.language_model.embed_tokens_per_layer.weight"]:
            _setmod(m, _tn, "cpu", value=_sload(_src, device="cpu")[_tn])
        say("embed tables pinned to CPU")
    except Exception as _e:
        say(f"embed pin FAILED: {_e}")
    cfg = m.config
    nl = getattr(cfg, "num_hidden_layers", getattr(getattr(cfg, "text_config", None), "num_hidden_layers", "?"))
    say(f"loaded layers={nl} target={LAYER}")

    def hs(prompt):
        x = tok(prompt, return_tensors="pt")
        with torch.no_grad():
            o = m(**x, output_hidden_states=True)
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
