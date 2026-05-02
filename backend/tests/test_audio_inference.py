"""Laptop mic → AudioPipeline → agitation score — live inference test.

Run from backend/ directory:
    uv run python tests/test_audio_inference.py

Speak into your mic. Each detected speech segment prints:
  - Transcription
  - Emotion (valence, arousal, dominant label)
  - Agitation score (0–100) from the vocal component
  - What the risk node would classify it as

Press Ctrl+C to stop.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import sounddevice as sd
from dotenv import load_dotenv

# Load .env from backend/
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# Add backend/ to path so app imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.audio_pipeline import AudioPipeline, SAMPLE_RATE, FRAME_SIZE
from app.agents.risk import score_to_risk
from app.models import IMUFeatures, HRState, TouchState, SensorSnapshot, VocalEmotion

SEPARATOR = "─" * 60


def compute_vocal_agitation(arousal: float) -> float:
    """Vocal component of agitation score (30% weight in full formula)."""
    return arousal * 100


def build_snapshot_from_audio(result) -> SensorSnapshot:
    """Build a minimal SensorSnapshot with only vocal data populated."""
    return SensorSnapshot(
        imu=IMUFeatures(jerk_magnitude=0.0),
        hr=HRState(valid=False),
        touch=TouchState(any_contact=True),  # assume contact — not testing touch
        speech_text=result.transcription,
        vocal_emotion=VocalEmotion(
            valence=result.valence,
            arousal=result.arousal,
            dominant_emotion=result.dominant_emotion,
        ) if result.speech_detected else None,
    )


def main() -> None:
    print("Loading models (wav2vec2 downloads on first run ~400MB)...")
    pipeline = AudioPipeline()
    print("Models loaded. Speak into your mic. Ctrl+C to stop.\n")
    print(SEPARATOR)

    def audio_callback(indata: np.ndarray, frames: int, time, status) -> None:
        if status:
            print(f"[sounddevice] {status}", file=sys.stderr)

        # indata is (frames, channels) — take mono
        frame = indata[:, 0].copy()

        result = pipeline.push_frame(frame)
        if result is None:
            return  # still buffering

        if not result.speech_detected:
            print("[no speech detected in segment]")
            return

        snap = build_snapshot_from_audio(result)

        # Vocal-only agitation (what the risk node would see with no other sensors)
        vocal_score = compute_vocal_agitation(result.arousal)
        risk = score_to_risk(vocal_score * 0.30)  # vocal is 30% weight

        print(f"\nTranscription : {result.transcription!r}")
        print(f"Emotion       : {result.dominant_emotion}  "
              f"(valence={result.valence:+.2f}, arousal={result.arousal:.2f})")
        print(f"Vocal score   : {vocal_score:.1f}/100")
        print(f"Risk (vocal)  : {risk}")
        print(SEPARATOR)

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=FRAME_SIZE,
        callback=audio_callback,
    ):
        print("Listening... (Ctrl+C to stop)")
        try:
            while True:
                sd.sleep(100)
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
