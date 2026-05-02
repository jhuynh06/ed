"""Audio pipeline: Silero VAD → Groq Whisper → wav2vec2 emotion.

Accepts 16kHz mono PCM frames (numpy int16 or float32).
Returns AudioResult with transcription and vocal emotion scores.
"""

from __future__ import annotations

import io
import logging
import os
import threading
import wave
import struct
from dataclasses import dataclass, field

import numpy as np
import torch
from dotenv import load_dotenv
from groq import Groq

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
from silero_vad import load_silero_vad, get_speech_timestamps
from transformers import pipeline as hf_pipeline

from app.acoustic_features import AcousticFeatures, AcousticExtractor
from app.nlp_features import NLPFeatures, NLPExtractor
from app.cdr_mapping import CDRScores, map_to_cdr

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────
SAMPLE_RATE = 16_000
FRAME_SIZE = 512          # samples per VAD frame (32ms at 16kHz)
VAD_CHECK_INTERVAL = 5    # run VAD every N frames (160ms) instead of every frame
SPEECH_END_FRAMES = 8     # frames of trailing silence before firing inference (~256ms)


@dataclass
class AudioResult:
    speech_detected: bool = False
    transcription: str | None = None
    valence: float = 0.0
    arousal: float = 0.0
    dominant_emotion: str = "neutral"
    acoustic: "AcousticFeatures | None" = None
    nlp: "NLPFeatures | None" = None
    cdr: "CDRScores | None" = None
    language: str = "en"   # detected language from Whisper


class AudioPipeline:
    """Stateful pipeline: accumulates frames, gates on VAD, runs inference.

    The wav2vec2 emotion model (1.27GB) is loaded in a background thread
    so the pipeline can start processing audio immediately.  Transcription
    and acoustic features work right away; emotion scores default to
    neutral until the model is ready.
    """

    def __init__(self) -> None:
        self._vad_model = load_silero_vad()
        self._groq = Groq(api_key=os.environ["GROQ_API_KEY"])

        # Emotion model loads in background — None until ready
        self._emotion_pipe = None
        self._emotion_ready = threading.Event()
        self._emotion_thread = threading.Thread(
            target=self._load_emotion_model, daemon=True
        )
        self._emotion_thread.start()

        self._acoustic = AcousticExtractor()
        self._nlp = NLPExtractor()
        self._buffer: list[np.ndarray] = []
        self._frame_count: int = 0
        self._prev_nlp: NLPFeatures | None = None

    def _load_emotion_model(self) -> None:
        """Download and load wav2vec2 emotion model in background."""
        try:
            logger.info("Loading emotion model in background...")
            pipe = hf_pipeline(
                "audio-classification",
                model="ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition",
                device="cpu",
            )
            self._emotion_pipe = pipe
            self._emotion_ready.set()
            logger.info("Emotion model ready")
        except Exception as e:
            logger.error(f"Failed to load emotion model: {e}")
            self._emotion_ready.set()  # unblock, will run without emotion

    def push_frame(self, frame: np.ndarray) -> AudioResult | None:
        """Push a 512-sample frame. Returns AudioResult when speech ends, else None."""
        f32 = frame.astype(np.float32) / 32768.0 if frame.dtype == np.int16 else frame.astype(np.float32)
        self._buffer.append(f32)
        self._frame_count += 1

        # Only run VAD every N frames to avoid O(n) cost per frame
        if self._frame_count % VAD_CHECK_INTERVAL != 0:
            return None

        audio_np = np.concatenate(self._buffer)
        audio_tensor = torch.from_numpy(audio_np)
        timestamps = get_speech_timestamps(audio_tensor, self._vad_model, sampling_rate=SAMPLE_RATE)

        if not timestamps:
            if len(self._buffer) > SAMPLE_RATE // FRAME_SIZE * 3:
                self._buffer = [f32]
            return None

        # Fire when speech ended at least SPEECH_END_FRAMES ago
        total_samples = len(audio_np)
        last_end = timestamps[-1]["end"]
        if last_end >= total_samples - FRAME_SIZE * SPEECH_END_FRAMES:
            return None  # still speaking or too recent

        speech_audio = audio_np[timestamps[0]["start"]: timestamps[-1]["end"]]
        self._buffer.clear()

        min_samples = FRAME_SIZE * 8  # ~256ms minimum
        if len(speech_audio) < min_samples:
            return AudioResult(speech_detected=False)

        return self._run_inference(speech_audio)

    def process_clip(self, audio: np.ndarray) -> AudioResult:
        """Process a complete audio clip (no streaming). Useful for testing.

        Args:
            audio: 1-D float32 numpy array at 16kHz.
        """
        return self._run_inference(audio)

    def _run_inference(self, audio: np.ndarray) -> AudioResult:
        """Run Whisper + wav2vec2 on a speech segment."""
        wav_bytes = _to_wav_bytes(audio)

        # Groq Whisper transcription — language=None for auto-detect
        transcription = ""
        detected_lang = "en"
        try:
            result = self._groq.audio.transcriptions.create(
                file=("audio.wav", wav_bytes, "audio/wav"),
                model="whisper-large-v3-turbo",
                response_format="verbose_json",
            )
            transcription = result.text.strip()
            # Whisper returns full names like "English", "Chinese" — map to ISO codes
            raw_lang = (getattr(result, "language", "") or "").lower()
            _LANG_MAP = {
                "english": "en", "en": "en",
                "chinese": "zh", "mandarin": "zh", "zh": "zh",
            }
            detected_lang = _LANG_MAP.get(raw_lang, "en")
        except Exception as e:
            transcription = f"[transcription error: {e}]"

        # wav2vec2 emotion classification (skipped if model still loading)
        valence, arousal, dominant = 0.0, 0.0, "neutral"
        if self._emotion_pipe is not None:
            try:
                preds = self._emotion_pipe({"array": audio, "sampling_rate": SAMPLE_RATE})
                valence, arousal, dominant = _parse_emotion_preds(preds)
            except Exception:
                pass
        else:
            logger.debug("Emotion model still loading, skipping emotion classification")

        # Acoustic features
        acoustic = self._acoustic.extract(audio, SAMPLE_RATE)

        # NLP features (uses prev utterance embedding for coherence)
        prev_emb = self._prev_nlp.embedding if self._prev_nlp else None
        nlp = self._nlp.extract(transcription or "", prev_emb, lang=detected_lang)
        self._prev_nlp = nlp

        # CDR mapping
        cdr = map_to_cdr(acoustic, nlp, self._prev_nlp)

        return AudioResult(
            speech_detected=True,
            transcription=transcription,
            valence=valence,
            arousal=arousal,
            dominant_emotion=dominant,
            acoustic=acoustic,
            nlp=nlp,
            cdr=cdr,
            language=detected_lang,
        )


# ── Helpers ──────────────────────────────────────────────────────────

def _to_wav_bytes(audio: np.ndarray) -> bytes:
    """Convert float32 numpy array to WAV bytes (16-bit PCM)."""
    pcm = (audio * 32767).clip(-32768, 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(struct.pack(f"<{len(pcm)}h", *pcm))
    return buf.getvalue()


# Emotion label → (valence, arousal) rough mapping
_EMOTION_MAP: dict[str, tuple[float, float]] = {
    "angry":    (-0.7,  0.9),
    "disgust":  (-0.6,  0.5),
    "fearful":  (-0.8,  0.8),
    "happy":    ( 0.8,  0.6),
    "neutral":  ( 0.0,  0.1),
    "sad":      (-0.6,  0.2),
    "surprised":( 0.2,  0.8),
    "calm":     ( 0.3,  0.0),
}


def _parse_emotion_preds(preds: list[dict]) -> tuple[float, float, str]:
    """Convert wav2vec2 predictions to (valence, arousal, dominant_label)."""
    if not preds:
        return 0.0, 0.0, "neutral"

    top = max(preds, key=lambda x: x["score"])
    label = top["label"].lower()

    # Weighted average across all predictions
    valence = sum(
        p["score"] * _EMOTION_MAP.get(p["label"].lower(), (0.0, 0.1))[0]
        for p in preds
    )
    arousal = sum(
        p["score"] * _EMOTION_MAP.get(p["label"].lower(), (0.0, 0.1))[1]
        for p in preds
    )

    return float(valence), float(arousal), label
