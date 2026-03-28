import os
import shutil
import zipfile

from huggingface_hub import hf_hub_download


VOSK_REPO_ID = "rhasspy/vosk-models"
VOSK_ZIP_FILENAME = "en/vosk-model-en-us-0.22-lgraph.zip"
VOSK_TARGET_DIR = os.path.join("models", "vosk-model-en-us-0.22-lgraph")

PIPER_REPO_ID = "rhasspy/piper-voices"
PIPER_ONNX_FILENAME = "en/en_US/ryan/low/en_US-ryan-low.onnx"
PIPER_JSON_FILENAME = "en/en_US/ryan/low/en_US-ryan-low.onnx.json"
PIPER_TARGET_DIR = os.path.join("models", "piper-voices")


def ensure_vosk_model():
    if os.path.exists(os.path.join(VOSK_TARGET_DIR, "conf")):
        return

    os.makedirs(VOSK_TARGET_DIR, exist_ok=True)

    cache_dir = os.path.join("models", ".cache_vosk")
    os.makedirs(cache_dir, exist_ok=True)

    zip_path = hf_hub_download(
        repo_id=VOSK_REPO_ID,
        filename=VOSK_ZIP_FILENAME,
        local_dir=cache_dir,
        local_dir_use_symlinks=False,
    )

    # Extract into a temporary directory first.
    tmp_extract_dir = os.path.join(cache_dir, "_extracted")
    if os.path.exists(tmp_extract_dir):
        shutil.rmtree(tmp_extract_dir)
    os.makedirs(tmp_extract_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(tmp_extract_dir)

    # The zip normally contains a single top-level folder.
    candidates = [d for d in os.listdir(tmp_extract_dir) if os.path.isdir(os.path.join(tmp_extract_dir, d))]
    if not candidates:
        raise RuntimeError("Could not locate extracted Vosk model directory in the zip.")

    extracted_model_dir = os.path.join(tmp_extract_dir, candidates[0])

    # Replace target dir contents.
    if os.path.exists(VOSK_TARGET_DIR):
        # Keep the dir itself, replace contents.
        for name in os.listdir(VOSK_TARGET_DIR):
            path = os.path.join(VOSK_TARGET_DIR, name)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)

    for name in os.listdir(extracted_model_dir):
        src = os.path.join(extracted_model_dir, name)
        dst = os.path.join(VOSK_TARGET_DIR, name)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)


def ensure_piper_model():
    onnx_path = os.path.join(PIPER_TARGET_DIR, "en", "en_US", "ryan", "low", "en_US-ryan-low.onnx")
    json_path = os.path.join(PIPER_TARGET_DIR, "en", "en_US", "ryan", "low", "en_US-ryan-low.onnx.json")

    if os.path.exists(onnx_path) and os.path.exists(json_path):
        return

    os.makedirs(PIPER_TARGET_DIR, exist_ok=True)

    hf_hub_download(
        repo_id=PIPER_REPO_ID,
        filename=PIPER_ONNX_FILENAME,
        local_dir=PIPER_TARGET_DIR,
        local_dir_use_symlinks=False,
    )
    hf_hub_download(
        repo_id=PIPER_REPO_ID,
        filename=PIPER_JSON_FILENAME,
        local_dir=PIPER_TARGET_DIR,
        local_dir_use_symlinks=False,
    )


def main():
    ensure_vosk_model()
    ensure_piper_model()

    print("Voice models ready.")
    print("Vosk dir:", VOSK_TARGET_DIR)
    print("Piper onnx:", os.path.join(PIPER_TARGET_DIR, "en", "en_US", "ryan", "low", "en_US-ryan-low.onnx"))


if __name__ == "__main__":
    main()

