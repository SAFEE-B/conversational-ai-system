"""Download Vosk ASR and Piper TTS models into the models/ directory."""

import os
import urllib.request
import zipfile

MODELS_DIR = "models"

VOSK_MODEL_NAME = "vosk-model-en-us-daanzu-20200905"
VOSK_MODEL_DIR = os.path.join(MODELS_DIR, VOSK_MODEL_NAME)
VOSK_ZIP_URL = (
    "https://alphacephei.com/vosk/models/vosk-model-en-us-daanzu-20200905.zip"
)

PIPER_VOICE_DIR = os.path.join(MODELS_DIR, "piper-voices", "en", "en_US", "ryan", "low")
PIPER_ONNX = os.path.join(PIPER_VOICE_DIR, "en_US-ryan-low.onnx")
PIPER_JSON = os.path.join(PIPER_VOICE_DIR, "en_US-ryan-low.onnx.json")
PIPER_ONNX_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/low/en_US-ryan-low.onnx"
PIPER_JSON_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/low/en_US-ryan-low.onnx.json"


def _download(url: str, dest: str) -> None:
    print(f"  Downloading {url} -> {dest}")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    urllib.request.urlretrieve(url, dest)


def download_vosk() -> None:
    if os.path.isdir(os.path.join(VOSK_MODEL_DIR, "conf")):
        print(f"Vosk model already present at {VOSK_MODEL_DIR}, skipping.")
        return

    zip_path = VOSK_MODEL_DIR + ".zip"
    _download(VOSK_ZIP_URL, zip_path)
    print(f"  Extracting {zip_path} -> {MODELS_DIR}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(MODELS_DIR)
    os.remove(zip_path)
    print("Vosk model ready.")


def download_piper() -> None:
    if os.path.isfile(PIPER_ONNX) and os.path.isfile(PIPER_JSON):
        print("Piper voice already present, skipping.")
        return

    os.makedirs(PIPER_VOICE_DIR, exist_ok=True)
    _download(PIPER_ONNX_URL, PIPER_ONNX)
    _download(PIPER_JSON_URL, PIPER_JSON)
    print("Piper voice ready.")


if __name__ == "__main__":
    os.makedirs(MODELS_DIR, exist_ok=True)
    download_vosk()
    download_piper()
    print("All voice models downloaded successfully.")
