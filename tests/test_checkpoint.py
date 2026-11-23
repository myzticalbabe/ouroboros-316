import os, tempfile
from ouroboros.checkpoint import save_checkpoint, load_checkpoint

def test_checkpoint_roundtrip():
    d = tempfile.mkdtemp()
    p = save_checkpoint(d, "step1", "3.14", {"val": 42})
    assert os.path.isfile(p)
    data = load_checkpoint(d, "step1")
    assert data["step"] == "step1"
    assert data["version"] == "3.14"
    assert data["state"] == {"val": 42}