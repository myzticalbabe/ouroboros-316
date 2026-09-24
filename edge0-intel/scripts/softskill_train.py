"""SoftSkill-style prefix training scaffold (Form: trained whiskers).

Trains a soft delta (length-M prefix) on frozen-backbone NTP loss over
successful (prompt, response) pairs, with VALIDATION-SELECTED checkpoints
(task metric, never train loss — loss != success). CPU-feasible constraints:
micro-base only (<=1.5B), short seqs, gradient checkpointing, Adam on prefix
params alone (backbone frozen: no optimizer state for weights).

Supervision comes from mine_supervision() (self-distillation: keep passing
(prompt, response) pairs per check()) — STaR-style bootstrapping, no labels.

Usage:
  python scripts/softskill_train.py --base <HF-or-local dir> --pairs pairs.jsonl
      --out prefix.npy [--len 32] [--steps 200] [--val-every 50]
  python scripts/softskill_train.py --mine --url URL --model M
      --tasks eval_sets/az_tasks.json --out pairs.jsonl
"""
import json
import os
import sys

BASE = r"C:\Users\clint\edge0-intel"


def mine(url, model, tasks_path, out_path, max_tokens=400):
    """Run AZ tasks, keep passing (prompt, response) pairs. Needs serving."""
    OWN = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, OWN)
    from eval_full import chat_raw, read_response
    from az_eval import check
    tasks = json.load(open(tasks_path, encoding="utf-8"))
    kept = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for i, task in enumerate(tasks):
            try:
                msg = chat_raw(url, model, task["prompt"], max_tokens=max_tokens)
                text, _ = read_response(msg)
                if check(task, text):
                    f.write(json.dumps({"prompt": task["prompt"],
                                        "response": text}) + "\n")
                    kept += 1
            except Exception as e:
                print(f"mine[{i}] ERROR {e}", flush=True)
            if (i + 1) % 10 == 0:
                print(f"mine {i+1}/{len(tasks)} kept={kept}", flush=True)
    print(f"MINED {kept}/{len(tasks)} -> {out_path}")


def train(base, pairs_path, out_path, plen=32, steps=200, val_every=50,
          lr=1e-3, batch=2, max_len=128):
    """Prefix-NTP training. Imported lazily (torch/transformers only here)."""
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    torch.manual_seed(7)
    print("tok+model...", flush=True)
    tok = AutoTokenizer.from_pretrained(base, local_files_only=True,
                                        trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        base, local_files_only=True, trust_remote_code=True,
        torch_dtype=torch.float32, device_map={"": "cpu"},
        low_cpu_mem_usage=True)
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    if hasattr(model, "gradient_checkpointing_enable"):
        model.gradient_checkpointing_enable()
    d = model.config.hidden_size
    prefix = torch.randn(plen, d, requires_grad=True)
    opt = torch.optim.Adam([prefix], lr=lr)
    pairs = [json.loads(l) for l in open(pairs_path, encoding="utf-8")
             if l.strip()]
    print(f"{len(pairs)} pairs, prefix {plen}x{d} "
          f"({prefix.numel()/1e3:.0f}K params)", flush=True)
    import numpy as np
    best = (-1, None)
    for step in range(1, steps + 1):
        opt.zero_grad()
        tot, nb = 0.0, 0
        for j in range(batch):
            ex = pairs[(step * batch + j) % len(pairs)]
            full = ex["prompt"] + "\n" + ex["response"]
            ids = tok(full, return_tensors="pt",
                      truncation=True, max_length=max_len)["input_ids"]
            n_prompt = len(tok(ex["prompt"])["input_ids"])
            emb = model.get_input_embeddings()(ids).float()
            inp = torch.cat([prefix.unsqueeze(0).expand(emb.size(0), -1, -1),
                             emb], dim=1)
            out = model(inputs_embeds=inp)
            logits = out.logits[0, plen + n_prompt - 1:plen + ids.size(1) - 1]
            tgt = ids[0, n_prompt:]
            n = min(logits.size(0), tgt.size(0))
            if n < 1:
                continue
            loss = torch.nn.functional.cross_entropy(logits[:n], tgt[:n])
            (loss / batch).backward()
            tot += float(loss)
            nb += 1
        if nb:
            torch.nn.utils.clip_grad_norm_([prefix], 1.0)
            opt.step()
        if step % 20 == 0:
            print(f"step {step}/{steps} ntp={tot/max(1,nb):.3f}", flush=True)
        if step % val_every == 0:
            # Validation gate: NTP is NOT the objective; record it, select
            # later by task metric (judge_cal-style runs score checkpoints).
            snap = os.path.join(os.path.dirname(out_path) or ".",
                                f"prefix_step{step}.npy")
            np.save(snap, prefix.detach().numpy())
            print(f"checkpoint {snap}", flush=True)
            if tot < best[0] or best[0] < 0:
                best = (tot, snap)
    import numpy as np  # noqa: F811
    np.save(out_path, prefix.detach().numpy())
    print(f"SAVED {out_path} (best-ntp {best[1]}; SELECT BY TASK METRIC, not loss)")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--mine", action="store_true")
    ap.add_argument("--url", default="http://127.0.0.1:8091")
    ap.add_argument("--model", default="spark")
    ap.add_argument("--tasks", default=os.path.join(BASE, "eval_sets", "az_tasks.json"))
    ap.add_argument("--pairs", default=os.path.join(BASE, "pairs.jsonl"))
    ap.add_argument("--base", default="")
    ap.add_argument("--out", default=os.path.join(BASE, "prefix.npy"))
    ap.add_argument("--len", type=int, default=32, dest="plen")
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--val-every", type=int, default=50)
    a = ap.parse_args()
    if a.mine:
        mine(a.url, a.model, a.tasks, a.pairs)
    else:
        if not a.base:
            print("--base <model dir> required for training")
            return 2
        train(a.base, a.pairs, a.out, a.plen, a.steps, a.val_every)


if __name__ == "__main__":
    sys.exit(main() or 0)
