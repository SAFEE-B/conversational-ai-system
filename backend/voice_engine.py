import base64
import io
import json
import os
import subprocess
import tempfile
import threading

# Pharmacy-domain vocabulary injected into Vosk's language model rescoring.
# "[unk]" must stay in the list so the recognizer accepts out-of-vocab words
# instead of forcing every utterance into one of the listed phrases.
# _PHARMACY_GRAMMAR = json.dumps([
#     # Generic medication names
#     "acetaminophen", "ibuprofen", "aspirin", "naproxen",
#     "diphenhydramine", "loratadine", "cetirizine", "fexofenadine",
#     "omeprazole", "famotidine", "ranitidine", "esomeprazole",
#     "pseudoephedrine", "phenylephrine", "guaifenesin", "dextromethorphan",
#     "loperamide", "bismuth subsalicylate", "simethicone",
#     "melatonin", "clotrimazole", "hydrocortisone",
#     "neomycin", "bacitracin", "polymyxin",
#     "simvastatin", "atorvastatin", "warfarin", "metformin",
#     "metronidazole", "clopidogrel", "lisinopril", "amoxicillin",
#     # Brand names
#     "tylenol", "advil", "motrin", "aleve", "benadryl",
#     "claritin", "zyrtec", "allegra",
#     "prilosec", "nexium", "pepcid", "zantac",
#     "sudafed", "mucinex", "robitussin", "dayquil", "nyquil",
#     "imodium", "pepto bismol", "gas x",
#     "neosporin", "cortaid", "cortizone", "lotrimin",
#     # Dosage and instruction phrases
#     "milligrams", "milligram", "mg", "milliliters", "milliliter", "ml",
#     "twice a day", "three times a day", "once a day", "every four hours",
#     "every six hours", "every eight hours", "as needed",
#     "take with food", "take with water", "do not crush",
#     "maximum dose", "recommended dose", "daily dose",
#     # Intent phrases
#     "drug interaction", "side effects", "dosage", "what is it used for",
#     "can i take", "is it safe", "take together", "what is the dose",
#     "how much should i take", "how often", "tell me about",
#     "do you have", "is it available", "over the counter",
#     "pharmacy hours", "when do you open", "when do you close",
#     "my name is", "i am", "remember me",
#     # Fallback: allow anything not in the list
#     "[unk]",
# ])


_PHARMACY_GRAMMAR = json.dumps([
    # Generic medication names
    "pain relief",

    # Common OTC pain medications
    "acetaminophen", "ibuprofen", "naproxen", "aspirin","paracetamol","panadol"


    # Dosage and instruction phrases
    "milligrams", "milligram", "mg", "milliliters", "milliliter", "ml",
    "twice a day", "three times a day", "once a day", "every four hours",
    "every six hours", "every eight hours", "as needed",
    "take with food", "take with water", "do not crush",
    "maximum dose", "recommended dose", "daily dose",
    # Intent phrases
    "drug interaction", "side effects", "dosage", "what is it used for",
    "can i take", "is it safe", "take together", "what is the dose",
    "how much should i take", "how often", "tell me about",
    "do you have", "is it available", "over the counter",
    "pharmacy hours", "when do you open", "when do you close",
    "my name is", "i am", "remember me",
    # Fallback: allow anything not in the list
    "[unk]",
])

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

            recognizer = KaldiRecognizer(self.model, self.sample_rate, _PHARMACY_GRAMMAR)
            # recognizer = KaldiRecognizer(self.model, self.sample_rate)
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

