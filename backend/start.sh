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

# ─── Voice models (ASR + TTS) ───────────────────────────────────────────────
# Set the model directory to the newly configured Daanzu mid-size model
export VOSK_MODEL_DIR="models/vosk-model-en-us-daanzu-20200905"
PIPER_ONNX="$MODEL_DIR/piper-voices/en/en_US/ryan/low/en_US-ryan-low.onnx"
PIPER_JSON="$MODEL_DIR/piper-voices/en/en_US/ryan/low/en_US-ryan-low.onnx.json"

if [ ! -f "$PIPER_ONNX" ] || [ ! -f "$PIPER_JSON" ] || [ ! -d "$VOSK_MODEL_DIR/conf" ]; then
    echo "Voice models not found. Downloading Vosk + Piper..."
    python download_voice_models.py
    echo "Voice model download complete."
fi

# Start the FastAPI server
exec uvicorn main:app --host 0.0.0.0 --port 8000
