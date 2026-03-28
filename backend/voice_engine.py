import base64
import io
import json
import os
import subprocess
import tempfile
import threading


class ASREngine:
    """
    Local speech-to-text using Vosk.

    Input: arbitrary encoded audio bytes (webm/opus, mp3, etc.)
    Output: transcript string.
    """

    def __init__(self, model_dir: str, sample_rate: int = 16000):
        from vosk import Model

        self.sample_rate = sample_rate
        self.model = Model(model_path=model_dir)

    def transcribe_audio_bytes(self, audio_bytes: bytes, input_ext: str = "webm") -> str:
        # Write to a temp file for ffmpeg to decode/convert.
        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = os.path.join(tmpdir, f"input_audio.{input_ext.lstrip('.')}")
            with open(in_path, "wb") as f:
                f.write(audio_bytes)

            # Convert to 16kHz mono PCM (signed 16-bit little-endian).
            pcm_path = os.path.join(tmpdir, "audio_16khz_mono.pcm")
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                in_path,
                "-ac",
                "1",
                "-ar",
                str(self.sample_rate),
                "-af",
                "highpass=f=200,lowpass=f=3000,afftdn",
                "-f",
                "s16le",
                pcm_path,
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                raise RuntimeError(f"ffmpeg failed: {proc.stderr[-500:]}")

            with open(pcm_path, "rb") as f:
                pcm_bytes = f.read()

            from vosk import KaldiRecognizer

            recognizer = KaldiRecognizer(self.model, self.sample_rate)
            recognizer.AcceptWaveform(pcm_bytes)
            result = json.loads(recognizer.FinalResult())
            return (result.get("text") or "").strip()


class TTSEngine:
    """
    Local text-to-speech using Piper (ONNX).

    We synthesize each chunk into a standalone WAV byte payload.
    """

    def __init__(self, onnx_path: str):
        from piper import PiperVoice

        self.voice = PiperVoice.load(onnx_path)
        # Piper voice/model execution may not be thread-safe; guard calls.
        self._lock = threading.Lock()

    def synthesize_wav_bytes(self, text: str) -> bytes:
        import wave

        buf = io.BytesIO()
        # Piper writes a WAV header and raw frames into the given wave file.
        with wave.open(buf, "wb") as wav_file:
            with self._lock:
                self.voice.synthesize_wav(text, wav_file)
        return buf.getvalue()


def audio_bytes_to_base64(audio_bytes: bytes) -> str:
    return base64.b64encode(audio_bytes).decode("ascii")

