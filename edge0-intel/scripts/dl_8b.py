import huggingface_hub as H
H.snapshot_download("Edge0/Edge0-8B-A1B-preview",
                    local_dir=r"C:\Users\clint\edge0-intel\models\edge0-8b")
print("DL8B_DONE")
