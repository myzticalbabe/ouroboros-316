"""STRATUM milestone 1: ONE dense layer forward, no accelerate, no full load.

Loads only embeddings + layer-0 weights from the single Gemma safetensors via
lazy safe_open, replicates the text-model prefix manually, runs ONE
Gemma4TextDecoderLayer on CPU, prints shape/finite/norm.

Peak RAM target: embeddings (~5.5GB) + one layer (~0.5GB). If this prints,
the STRATUM hypothesis is mechanically viable and milestone 2 (full 31-layer
collection) is justified.
"""
import os, traceback
LOG = r"C:\Users\clint\edge0-intel\probe_stratum.log"
log = open(LOG, "w")

def say(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True); log.write(m + "\n"); log.flush()

PROMPT = "How do I bake bread?"
LAYER_IDX = 0
N_LAYERS = 31  # we only ever need hidden_states[30]

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
    say("tok...")
    tok = AutoTokenizer.from_pretrained(d, local_files_only=True, trust_remote_code=True)
    ids = tok(PROMPT)["input_ids"]
    say(f"tokens={len(ids)} max_id={max(ids)}")
    # Merge-is-identity precondition: no multimodal placeholder tokens.
    assert max(ids) < 258880, "placeholder token present; merge not identity"
    input_ids = torch.tensor([ids])
    DT = torch.bfloat16

    say("config(truncate 42->31)...")
    cfg = AutoConfig.from_pretrained(d, local_files_only=True, trust_remote_code=True)
    tc = cfg.text_config
    tc.num_hidden_layers = N_LAYERS
    ple = tc.hidden_size_per_layer_input  # 256
    hs = tc.hidden_size  # 2560
    need = N_LAYERS * ple  # 7936
    say(f"layers={tc.num_hidden_layers} hs={hs} ple={ple} moe={tc.enable_moe_block}")

    sf = os.path.join(d, "model.safetensors")
    f = safe_open(sf, framework="pt")
    pre = "model.language_model."

    def load(mod, file_key, shape_note=""):
        t = f.get_tensor(pre + file_key)
        if t.shape != tuple(mod.weight.shape):
            # truncated dims: slice rows or cols to module shape
            if t.shape[0] > mod.weight.shape[0] and t.shape[1:] == tuple(mod.weight.shape[1:]):
                t = t[:mod.weight.shape[0]]
            elif t.shape[1] > mod.weight.shape[1] and t.shape[0] == mod.weight.shape[0]:
                t = t[:, :mod.weight.shape[1]]
            else:
                raise RuntimeError(f"shape {tuple(t.shape)} vs module {tuple(mod.weight.shape)} {file_key}")
            say(f"sliced {file_key}: file->{tuple(mod.weight.shape)}")
        mod.weight.data = t.to(DT)
        return mod

    say("embeddings...")
    embed = Gemma4TextScaledWordEmbedding(tc.vocab_size, hs, tc.pad_token_id,
                                          embed_scale=hs ** 0.5).to(DT)
    load(embed, "embed_tokens.weight")
    embed_pl = Gemma4TextScaledWordEmbedding(tc.vocab_size_per_layer_input, need,
                                             tc.pad_token_id,
                                             embed_scale=ple ** 0.5).to(DT)
    load(embed_pl, "embed_tokens_per_layer.weight")
    proj = torch.nn.Linear(hs, need, bias=False).to(DT)
    load(proj, "per_layer_model_projection.weight")
    proj_scale = tc.hidden_size ** -0.5
    proj_norm = Gemma4RMSNorm(ple, eps=tc.rms_norm_eps).to(DT)
    t = f.get_tensor(pre + "per_layer_projection_norm.weight")
    proj_norm.weight.data = t.to(DT)
    in_scale = 2.0 ** -0.5

    say("rotary...")
    rotary = Gemma4TextRotaryEmbedding(tc).to(DT)

    say(f"layer {LAYER_IDX}...")
    layer = Gemma4TextDecoderLayer(tc, LAYER_IDX).to(DT)
    lp = f"layers.{LAYER_IDX}."
    got, want = [], [k for k in layer.state_dict()]
    sd = {}
    for k in f.keys():
        if k.startswith(pre + "layers." + str(LAYER_IDX) + "."):
            sd[k[len(pre + lp):]] = f.get_tensor(k).to(DT)
    missing = [k for k in want if k not in sd]
    extra = [k for k in sd if k not in want]
    say(f"layer keys: file={len(sd)} module={len(want)} missing={missing} extra={extra}")
    assert not missing and not extra, "layer key mismatch"
    layer.load_state_dict(sd, strict=True)
    say("layer weights loaded")
    del sd

    with torch.no_grad():
        say("prefix...")
        inputs_embeds = embed(input_ids)
        pli_tok = embed_pl(input_ids).reshape(1, len(ids), N_LAYERS, ple)
        pp = proj(inputs_embeds) * proj_scale
        pp = pp.reshape(1, len(ids), N_LAYERS, ple)
        pp = proj_norm(pp)
        pli = (pp + pli_tok) * in_scale
        per0 = pli[:, :, LAYER_IDX, :]
        say(f"per0 {tuple(per0.shape)} finite={torch.isfinite(per0).all().item()}")

        position_ids = torch.arange(len(ids)).unsqueeze(0)
        ltype = tc.layer_types[LAYER_IDX]
        pos_emb = rotary(inputs_embeds, position_ids, ltype)
        mk = {"config": tc, "inputs_embeds": inputs_embeds,
              "attention_mask": None, "past_key_values": None,
              "position_ids": position_ids}
        amask = (create_causal_mask(**mk) if ltype == "full_attention"
                 else create_sliding_window_causal_mask(**mk))
        say(f"layer_type={ltype} mask ok")

        say("layer forward...")
        out = layer(hidden_states=inputs_embeds, per_layer_input=per0,
                    shared_kv_states=UserDict(),
                    position_embeddings=pos_emb,
                    attention_mask=amask, position_ids=position_ids,
                    past_key_values=None)
        say(f"OUT shape={tuple(out.shape)} finite={torch.isfinite(out).all().item()} "
            f"norm={float(out.float().norm()):.3f}")
        assert out.shape == (1, len(ids), hs)
        assert torch.isfinite(out).all()
    say("PROBE PASS")

try:
    main()
except Exception:
    say(traceback.format_exc())
    raise
