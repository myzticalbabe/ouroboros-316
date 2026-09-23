import time, os, traceback
LOG = r"C:\Users\clint\edge0-intel\try8b.log"
log = open(LOG, "w")

def say(*a):
    msg = " ".join(str(x) for x in a)
    print(msg, flush=True)
    log.write(msg + "\n")
    log.flush()

def main():
    t0 = time.time()
    say("tok...")
    from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig
    import torch
    d = r"C:\Users\clint\edge0-intel\models\edge0-8b"
    tok = AutoTokenizer.from_pretrained(d, local_files_only=True, trust_remote_code=True)
    say("model...")
    cfg = AutoConfig.from_pretrained(d, local_files_only=True, trust_remote_code=True)
    cfg.quantization_config = None  # custom 4-bit affine; modeling code dequants itself
    m = AutoModelForCausalLM.from_pretrained(d, config=cfg, local_files_only=True, trust_remote_code=True,
                                             torch_dtype="auto", device_map="cpu",
                                             low_cpu_mem_usage=True)
    say(f"loaded {time.time()-t0:.0f}s")
    x = tok("Hello, I am", return_tensors="pt")
    t1 = time.time()
    with torch.no_grad():
        y = m.generate(**x, max_new_tokens=20, do_sample=False)
    say(tok.decode(y[0]))
    say(f"gen {time.time()-t1:.0f}s total {time.time()-t0:.0f}s")

try:
    main()
except Exception:
    say(traceback.format_exc())
    raise
