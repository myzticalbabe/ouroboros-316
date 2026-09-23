import torch
from transformers import AutoConfig, AutoModelForCausalLM
from accelerate import init_empty_weights, infer_auto_device_map
d = r"C:\Users\clint\edge0-intel\models\gemma-4-e4b-it"
c = AutoConfig.from_pretrained(d, local_files_only=True, trust_remote_code=True)
print("arch:", c.architectures, flush=True)
with init_empty_weights():
    m = AutoModelForCausalLM.from_config(c, trust_remote_code=True)
print("meta ok", flush=True)
for b in ["5500MB", "6GB", "8GB"]:
    try:
        mp = infer_auto_device_map(m, max_memory={"cpu": b}, no_split_module_classes=["Gemma4DecoderLayer"] if True else None)
        from collections import Counter
        print(b, Counter(mp.values()), flush=True)
    except Exception as e:
        print(b, "ERR", str(e)[:120], flush=True)
