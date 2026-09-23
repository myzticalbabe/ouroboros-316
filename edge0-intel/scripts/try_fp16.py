import traceback
import os
LOG = r"C:\Users\clint\edge0-intel\tryfp16.log"
log = open(LOG, "w")

def say(*a):
    msg = " ".join(str(x) for x in a)
    print(msg, flush=True)
    log.write(msg + "\n")
    log.flush()

def main():
    import time
    t0 = time.time()
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    from fla_torch_fallback import install as install_fla_cpu
    install_fla_cpu()
    say("fla-cpu-fallback installed")
    d = r"C:\Users\clint\edge0-intel\models\edge0-8b-fp16"
    say("tok...")
    tok = AutoTokenizer.from_pretrained(d, local_files_only=True, trust_remote_code=True)
    say("model(disk-offload)...")
    m = AutoModelForCausalLM.from_pretrained(
        d, local_files_only=True, trust_remote_code=True,
        torch_dtype=torch.float32, device_map="auto",
        max_memory={"cpu": "6GB"}, offload_folder=r"C:\Users\clint\edge0-intel\offload",
        low_cpu_mem_usage=True)
    say(f"loaded {time.time()-t0:.0f}s")
    x = tok("Hello, I am", return_tensors="pt")
    t1 = time.time()
    with torch.no_grad():
        y = m.generate(**x, max_new_tokens=5, do_sample=False)
    say(tok.decode(y[0]))
    say(f"gen {time.time()-t1:.0f}s total {time.time()-t0:.0f}s")

try:
    main()
except Exception:
    say(traceback.format_exc())
    raise
