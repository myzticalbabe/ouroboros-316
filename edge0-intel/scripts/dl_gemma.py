import huggingface_hub as H
H.snapshot_download("google/gemma-4-E4B-it",
                    local_dir=r"C:\Users\clint\edge0-intel\models\gemma-4-e4b-it",
                    ignore_patterns=["*.mp4", "*.jpg", "*.png"])
print("DL_GEMMA_DONE")
