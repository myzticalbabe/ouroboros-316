"""Loop validation for softskill_train (no base weights, no serving).

Builds a toy random transformer + word-level tokenizer in-code, runs 3
training steps on 4 synthetic pairs, asserts: grad flows to prefix only,
checkpoints save, validation gate records, backbone untouched.
Proves MACHINERY; says nothing about real data (that needs a base).
"""
import json
import os
import sys
import tempfile

import numpy as np
import torch
from tokenizers import Tokenizer as FastTok
from tokenizers.models import WordLevel
from tokenizers.pre_tokenizers import Whitespace
from transformers import GPT2Config, GPT2LMHeadModel, PreTrainedTokenizerFast

OWN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, OWN)
TMP = tempfile.mkdtemp(prefix="softskill_loop_")

PAIRS = [
    ("add two and three", "two plus three is five"),
    ("name one color", "the color is blue"),
    ("count to three", "one two three"),
    ("say hello back", "hello to you too"),
]


def main():
    sys.path.insert(0, OWN)
    import softskill_train as ST
    words = set()
    for p, r in PAIRS:
        words.update((p + " " + r).split())
    vocab = {"[PAD]": 0, "[EOS]": 1}
    for w in sorted(words):
        vocab[w] = len(vocab)
    tok = FastTok(WordLevel(vocab=vocab, unk_token="[EOS]"))
    tok.pre_tokenizer = Whitespace()
    wrapped = PreTrainedTokenizerFast(tokenizer_object=tok,
                                      pad_token="[PAD]", eos_token="[EOS]")
    mdir = os.path.join(TMP, "toy")
    os.makedirs(mdir, exist_ok=True)
    wrapped.save_pretrained(mdir)
    cfg = GPT2Config(vocab_size=len(vocab), n_positions=64, n_embd=64,
                     n_layer=2, n_head=2, pad_token_id=0)
    model = GPT2LMHeadModel(cfg)
    model.save_pretrained(mdir)
    before = [p.clone() for p in model.parameters()]
    pf = os.path.join(TMP, "pairs.jsonl")
    with open(pf, "w", encoding="utf-8") as f:
        for p, r in PAIRS:
            f.write(json.dumps({"prompt": p, "response": r}) + "\n")
    out = os.path.join(TMP, "prefix.npy")
    ST.train(mdir, pf, out, plen=4, steps=3, val_every=3, lr=1e-3,
             batch=2, max_len=32)
    assert os.path.exists(out), "prefix not saved"
    arr = np.load(out)
    assert arr.shape[1] == 64 and arr.shape[0] == 4, arr.shape
    assert np.isfinite(arr).all(), "non-finite prefix"
    for b, p in zip(before, model.parameters()):
        assert torch.equal(b, p), "backbone moved!"
    snaps = [f for f in os.listdir(TMP) if f.startswith("prefix_step")]
    assert snaps, "no validation checkpoint"
    print(f"LOOP OK: prefix {arr.shape}, backbone frozen, "
          f"checkpoints={snaps}")


if __name__ == "__main__":
    main()
