
import numpy as np
import sounddevice as sd
import soundfile as sf
import tempfile
import os

SAMPLE_RATE = 16000


def record_fixed(seconds: float, samplerate: int = SAMPLE_RATE) -> str:
  
    print(f"🎙️  record ({seconds}s)...")
    audio = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=1, dtype="float32")
    sd.wait()
    tmp_path = tempfile.mktemp(suffix=".wav")
    sf.write(tmp_path, audio, samplerate)
    return tmp_path


def record_until_silence(max_seconds: float = 10, silence_thresh: float = 0.01,
                          silence_duration: float = 1.2, samplerate: int = SAMPLE_RATE) -> str:

    block_duration = 0.2
    block_size = int(samplerate * block_duration)
    silence_blocks_needed = int(silence_duration / block_duration)
    silence_count = 0
    chunks = []

    print("🎙️  listening...")
    with sd.InputStream(samplerate=samplerate, channels=1, dtype="float32") as stream:
        total_blocks = int(max_seconds / block_duration)
        started_talking = False
        for _ in range(total_blocks):
            block, _ = stream.read(block_size)
            chunks.append(block.copy())
            volume = np.abs(block).mean()

            if volume > silence_thresh:
                started_talking = True
                silence_count = 0
            elif started_talking:
                silence_count += 1
                if silence_count >= silence_blocks_needed:
                    break

    audio = np.concatenate(chunks, axis=0)
    tmp_path = tempfile.mktemp(suffix=".wav")
    sf.write(tmp_path, audio, samplerate)
    return tmp_path


def cleanup(path: str):
    try:
        os.remove(path)
    except OSError:
        pass
