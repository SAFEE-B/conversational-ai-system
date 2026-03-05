import os
from huggingface_hub import hf_hub_download

repo_id = "Qwen/Qwen2.5-0.5B-Instruct-GGUF"
filename = "qwen2.5-0.5b-instruct-q8_0.gguf"

print(f"Downloading {filename} from {repo_id}...")
model_path = hf_hub_download(
    repo_id=repo_id,
    filename=filename,
    local_dir="models",
    local_dir_use_symlinks=False
)
print(f"Model downloaded to: {model_path}")
