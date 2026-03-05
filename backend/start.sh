#!/bin/bash
set -e

MODEL_DIR="models"
MODEL_FILE="$MODEL_DIR/qwen2.5-0.5b-instruct-q4_k_m.gguf"

# Download the model if it isn't already present
if [ ! -f "$MODEL_FILE" ]; then
    echo "Model not found. Downloading from HuggingFace..."
    mkdir -p "$MODEL_DIR"
    python -c "
from huggingface_hub import hf_hub_download
hf_hub_download(
    repo_id='Qwen/Qwen2.5-0.5B-Instruct-GGUF',
    filename='qwen2.5-0.5b-instruct-q4_k_m.gguf',
    local_dir='models',
    local_dir_use_symlinks=False
)
"
    echo "Download complete."
fi

# Start the FastAPI server
exec uvicorn main:app --host 0.0.0.0 --port 8000
