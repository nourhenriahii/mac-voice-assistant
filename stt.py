"""
Speech-to-Text using faster-whisper, running fully locally (no internet needed).
"""
from faster_whisper import WhisperModel
import config

_model = None


def _get_model():
    global _model
    if _model is None:
        print(f"⏳ Loading Whisper model ({config.WHISPER_MODEL_SIZE})...")
        # compute_type="int8" is lighter and faster on typical Mac CPUs
        _model = WhisperModel(config.WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    return _model


import re


def _normalize_word(word: str) -> str:
    """Strips punctuation and lowercases a word, so 'sorry,' and 'sorry.' compare equal."""
    return re.sub(r"[^\w']", "", word).lower()


def _is_repetition_hallucination(text: str, min_repeats: int = 2) -> bool:
    """Detects the classic Whisper failure mode where it repeats the same
    short phrase over and over on noisy/ambiguous audio (e.g. 'I don't know
    what to do, I don't know what to do, ...' or 'I'm sorry, I'm sorry,
    I'm sorry.'). Returns True if the text looks like this kind of artifact
    rather than real speech."""
    words = [_normalize_word(w) for w in text.split()]
    words = [w for w in words if w]
    if len(words) < 4:
        return False
    for chunk_len in range(2, len(words) // min_repeats + 1):
        chunk = words[:chunk_len]
        repeats, i = 0, 0
        while i + chunk_len <= len(words):
            if words[i:i + chunk_len] == chunk:
                repeats += 1
                i += chunk_len
            else:
                break
        # Flag it only if the repeated chunk accounts for essentially the
        # whole utterance — avoids false positives on normal speech that
        # happens to repeat a word or two ("yes yes, open Safari").
        if repeats >= min_repeats and repeats * chunk_len >= len(words) - 1:
            return True
    return False


def transcribe(wav_path: str) -> str:
    """Returns the text extracted from an audio file, forcing English transcription
    to avoid language misdetection on short audio clips. Filters out Whisper's
    repeated-phrase hallucination artifacts, returning an empty string for those
    (treated the same as silence by the caller)."""
    model = _get_model()
    segments, info = model.transcribe(wav_path, beam_size=5, language="en")
    text = " ".join(seg.text.strip() for seg in segments).strip()

    if _is_repetition_hallucination(text):
        print(f"   (debug: filtered out likely hallucination: {text!r})")
        return ""

    return text
