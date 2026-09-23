import faulthandler, sys
faulthandler.dump_traceback_later(240)
import traceback
d = r"C:\Users\clint\edge0-intel\models\gemma-4-e4b-it"
try:
    print("stage: imports", flush=True)
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    print("stage: tokenizer", flush=True)
    tok = AutoTokenizer.from_pretrained(d, local_files_only=True, trust_remote_code=True)
    print("stage: load", flush=True)
    m = AutoModelForCausalLM.from_pretrained(
        d, local_files_only=True, trust_remote_code=True,
        torch_dtype=torch.bfloat16, device_map="auto",
        max_memory={"cpu": "6GB"},
        offload_folder=r"C:\Users\clint\edge0-intel\offload_gemma",
        low_cpu_mem_usage=True)
    print("stage: loaded", flush=True)
except Exception:
    traceback.print_exc()
