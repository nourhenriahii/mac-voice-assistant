"""
Wake word detection using openWakeWord — runs fully locally, no internet needed.
This file is optional: if openwakeword isn't installed, main.py automatically
falls back to "press Enter then speak" mode, which is simpler to get started with.

To fully enable it:
    pip install openwakeword
    Then use a ready-made model like "hey_jarvis", or train a custom one for your
    assistant's name.

Note: we force the ONNX inference backend instead of the default TFLite one,
because tflite-runtime doesn't ship prebuilt wheels for every macOS/Python
combination (e.g. Python 3.14 on Apple Silicon). ONNX runtime is already
installed as a dependency of faster-whisper, so this works out of the box.
"""
import os
import numpy as np
import sounddevice as sd
import openwakeword
from openwakeword.model import Model

SAMPLE_RATE = 16000
CHUNK = 1280  # chunk size expected by openWakeWord

_oww_model = None


def _models_already_downloaded() -> bool:
    """Checks whether the pretrained ONNX models are already on disk, so we
    don't hit the network (and potentially hang on a flaky connection) on
    every single run."""
    models_dir = os.path.join(os.path.dirname(openwakeword.__file__), "resources", "models")
    marker_file = os.path.join(models_dir, "hey_jarvis_v0.1.onnx")
    return os.path.isfile(marker_file)


def _get_model():
    global _oww_model
    if _oww_model is None:
        if not _models_already_downloaded():
            print("⏳ Downloading wake word models (first run only)...")
            try:
                openwakeword.utils.download_models()
            except Exception as e:
                print(f"⚠️  Couldn't download wake word models ({e}). "
                      f"Check your internet connection and try again.")
                raise
        # You can specify particular models here, e.g. wakeword_models=["hey_jarvis"]
        _oww_model = Model(inference_framework="onnx")
    return _oww_model


def listen_for_wake_word(threshold: float = 0.35, debug: bool = True):
    """Blocks until the wake word is heard, then returns."""
    model = _get_model()
    frame_count = 0
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=CHUNK) as stream:
        while True:
            audio_chunk, _ = stream.read(CHUNK)
            audio_chunk = audio_chunk.flatten()
            predictions = model.predict(audio_chunk)

            if debug:
                frame_count += 1
                # Print the top score roughly twice per second so you can see
                # how close your voice is getting to the threshold live.
                if frame_count % 10 == 0:
                    best_name = max(predictions, key=predictions.get)
                    best_score = predictions[best_name]
                    print(f"   (listening... best: {best_name}={best_score:.2f}, threshold={threshold})", end="\r")

            if any(score > threshold for score in predictions.values()):
                print("\n✅ Wake word detected!")
                return
