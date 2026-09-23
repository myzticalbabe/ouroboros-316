"""STRATUM milestone 2: full refusal-direction collection, layer by layer.

No accelerate, no device_map, no full-model load. Embeddings pinned once
(~5.5GB); each of layers 0..30 is loaded, executed, and evicted in turn.
Quantity collected is EXACTLY hidden_states[30][0,-1] per prompt — the same
tensor collect_clean.py targeted — so the resulting refusal_dir.npy drops
into the handoff pipeline unchanged.

Peak RAM: embeddings + one layer. I/O-bound; expect several minutes.
"""
import os, time, traceback
LOG = r"C:\Users\clint\edge0-intel\collect_stratum.log"
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
N_LAYERS = 31
TARGET = 30

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
    from transformers import AutoTokenizer, AutoConfig
    from transformers.models.gemma4.modeling_gemma4 import (
        Gemma4TextScaledWordEmbedding, Gemma4TextDecoderLayer,
        Gemma4TextRotaryEmbedding, Gemma4RMSNorm,
    )
    from transformers.masking_utils import (
        create_causal_mask, create_sliding_window_causal_mask,
    )
    from collections import UserDict
    from safetensors import safe_open

    d = r"C:\Users\clint\edge0-intel\models\gemma-4-e4b-it"
    DT = torch.bfloat16
    t0 = time.time()

    say("tok...")
    tok = AutoTokenizer.from_pretrained(d, local_files_only=True, trust_remote_code=True)

    say("config: FULL 42 for layer structure, truncated 31 for PLE dims...")
    cfg = AutoConfig.from_pretrained(d, local_files_only=True, trust_remote_code=True)
    tc = cfg.text_config  # 42 layers: TRUE kv-sharing structure for module construction
    import copy
    tct = copy.copy(tc)  # truncated twin: PLE embedding dims only
    tct.num_hidden_layers = N_LAYERS
    ple, hs = tct.hidden_size_per_layer_input, tct.hidden_size
    need = N_LAYERS * ple

    f = safe_open(os.path.join(d, "model.safetensors"), framework="pt")
    pre = "model.language_model."

    def sliced(key, mod_shape):
        t = f.get_tensor(pre + key)
        ms = tuple(mod_shape)
        if tuple(t.shape) == ms:
            return t.to(DT)
        if len(t.shape) == 2 and t.shape[0] == ms[0] and t.shape[1] > ms[1]:
            return t[:, :ms[1]].contiguous().to(DT)
        if len(t.shape) == 2 and t.shape[1] == ms[1] and t.shape[0] > ms[0]:
            return t[:ms[0]].contiguous().to(DT)
        raise RuntimeError(f"shape {tuple(t.shape)} vs {ms} {key}")

    say("embeddings (pin once)...")
    embed = Gemma4TextScaledWordEmbedding(tc.vocab_size, hs, tc.pad_token_id,
                                          embed_scale=hs ** 0.5).to(DT)
    embed.weight.data = f.get_tensor(pre + "embed_tokens.weight").to(DT)
    embed_pl = Gemma4TextScaledWordEmbedding(tc.vocab_size_per_layer_input, need,
                                             tc.pad_token_id,
                                             embed_scale=ple ** 0.5).to(DT)
    embed_pl.weight.data = sliced("embed_tokens_per_layer.weight", embed_pl.weight.shape)
    proj = torch.nn.Linear(hs, need, bias=False).to(DT)
    proj.weight.data = sliced("per_layer_model_projection.weight", proj.weight.shape)
    proj_scale = tc.hidden_size ** -0.5
    proj_norm = Gemma4RMSNorm(ple, eps=tc.rms_norm_eps).to(DT)
    proj_norm.weight.data = f.get_tensor(pre + "per_layer_projection_norm.weight").to(DT)
    in_scale = 2.0 ** -0.5
    rotary = Gemma4TextRotaryEmbedding(tc).to(DT)
    say("embeddings pinned")

    def hs_one(prompt):
        ids = tok(prompt)["input_ids"]
        assert max(ids) < 258880, "placeholder token; merge not identity"
        input_ids = torch.tensor([ids])
        with torch.no_grad():
            inputs_embeds = embed(input_ids)
            pli = embed_pl(input_ids).reshape(1, len(ids), N_LAYERS, ple)
            pp = proj(inputs_embeds) * proj_scale
            pp = pp.reshape(1, len(ids), N_LAYERS, ple)
            pp = proj_norm(pp)
            pli = (pp + pli) * in_scale
            position_ids = torch.arange(len(ids)).unsqueeze(0)
            pos_emb = {lt: rotary(inputs_embeds, position_ids, lt)
                       for lt in set(tc.layer_types)}
            mk = {"config": tc, "inputs_embeds": inputs_embeds,
                  "attention_mask": None, "past_key_values": None,
                  "position_ids": position_ids}
            masks = {"full_attention": create_causal_mask(**mk),
                     "sliding_attention": create_sliding_window_causal_mask(**mk)}
            kv = UserDict()
            hidden = inputs_embeds
            for i in range(N_LAYERS):
                layer = Gemma4TextDecoderLayer(tc, i).to(DT)
                lp = f"layers.{i}."
                sd = {k[len(pre + lp):]: f.get_tensor(k).to(DT) for k in f.keys()
                      if k.startswith(pre + lp)}
                want = set(layer.state_dict())
                # Vestigial checkpoint weights: the file carries k/v proj+norms
                # for kv-shared layers, but the architecture ignores them
                # (mirrors _keys_to_ignore_on_load_unexpected in modeling).
                # Drop ONLY those; anything else mismatched is a real error.
                VESTIGIAL = {f"self_attn.{n}.weight" for n in
                             ("k_proj", "v_proj", "k_norm", "v_norm")}
                assert want - set(sd) == set(), f"layer {i} missing={want - set(sd)}"
                dropped = set(sd) - want
                assert dropped <= VESTIGIAL, f"layer {i} unexpected extra={dropped}"
                if dropped:
                    say(f"layer {i}: dropped vestigial {sorted(dropped)}")
                sd = {k: v for k, v in sd.items() if k in want}
                layer.load_state_dict(sd, strict=True)
                del sd
                lt = tc.layer_types[i]
                hidden = layer(hidden_states=hidden,
                               per_layer_input=pli[:, :, i, :],
                               shared_kv_states=kv,
                               position_embeddings=pos_emb[lt],
                               attention_mask=masks[lt],
                               position_ids=position_ids,
                               past_key_values=None)
                del layer
            return hidden[0, -1].float()

    vecs = {}
    for tag, prompts in (("harm", HARM), ("benign", BENIGN)):
        for j, p in enumerate(prompts):
            say(f"{tag}[{j}] forward 31 layers...")
            v = hs_one(p)
            assert torch.isfinite(v).all()
            vecs.setdefault(tag, []).append(v)
            say(f"{tag}[{j}] done norm={float(v.norm()):.3f} wall={(time.time()-t0)/60:.1f}min")

    import numpy as np
    H = torch.stack(vecs["harm"]); B = torch.stack(vecs["benign"])
    direction = (H.mean(0) - B.mean(0)).numpy()
    os.makedirs(r"C:\Users\clint\edge0-intel\models\gemma-4-e4b-abliterated", exist_ok=True)
    out = r"C:\Users\clint\edge0-intel\models\gemma-4-e4b-abliterated\refusal_dir.npy"
    np.save(out, direction)
    say(f"saved norm={float((direction**2).sum()**0.5):.3f} dim={direction.shape} -> {out}")
    say(f"COLLECT PASS wall={(time.time()-t0)/60:.1f}min")

try:
    main()
except Exception:
    say(traceback.format_exc())
    raise
