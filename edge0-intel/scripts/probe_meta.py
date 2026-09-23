import torch
from transformers import AutoModelForCausalLM
d = r"C:\Users\clint\edge0-intel\models\gemma-4-e4b-it"
m = AutoModelForCausalLM.from_pretrained(
    d, local_files_only=True, trust_remote_code=True,
    torch_dtype=torch.bfloat16, device_map="auto",
    max_memory={"cpu": "6GB"},
    offload_folder=r"C:\Users\clint\edge0-intel\offload_gemma",
    low_cpu_mem_usage=True)
out = open(r"C:\Users\clint\edge0-intel\meta_tensors.txt", "w")
for n, p in list(m.named_parameters()) + list(m.named_buffers()):
    t = p if isinstance(p, torch.Tensor) else None
    if t is not None and t.device.type == "meta":
        out.write(f"{n} {tuple(t.shape)} {t.dtype}\n")
out.close()
print("wrote meta_tensors.txt")
