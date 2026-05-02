"""Record WAV fixture files for unit tests.

Run from backend/ with the venv active:
    python tests/record_fixtures.py

Records three clips into tests/fixtures/:
  - calm_speech.wav     — speak calmly: "Everything is okay, I'm right here with you"
  - distressed_speech.wav — speak with distress/urgency: "I don't know where I am, I'm scared"
  - silence.wav         — stay quiet

Each clip is 3 seconds, 16kHz mono.
"""

import os
import sys
import time

import numpy as np
import sounddevice as sd
import soundfile as sf

SAMPLE_RATE = 16_000
DURATION = 3  # seconds
OUT_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

CLIPS = [
    ("calm_speech.wav",      'Speak CALMLY: "Everything is okay, I\'m right here with you"'),
    ("distressed_speech.wav", 'Speak with DISTRESS: "I don\'t know where I am, I\'m scared"'),
    ("silence.wav",           "Stay SILENT"),
]


def record(label: str, filename: str) -> None:
    out_path = os.path.join(OUT_DIR, filename)
    print(f"\n{label}")
    print(f"Recording in 3...", end="", flush=True)
    for i in (2, 1):
        time.sleep(1)
        print(f" {i}...", end="", flush=True)
    time.sleep(1)
    print(" GO!", flush=True)

    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
    )
    sd.wait()
    sf.write(out_path, audio, SAMPLE_RATE)
    peak = float(np.abs(audio).max())
    print(f"Saved {out_path}  (peak={peak:.3f})")
    if peak < 0.01:
        print("  ⚠ Very quiet — check your mic level")


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Recording {len(CLIPS)} fixtures at {SAMPLE_RATE}Hz, {DURATION}s each.")
    print("Press Enter before each clip when ready.")

    for filename, label in CLIPS:
        input(f"\nNext: {label}\n  → Press Enter to start...")
        record(label, filename)

    print("\nAll fixtures recorded. Run the tests:")
    print("  python -m pytest tests/test_audio_pipeline_unit.py -v")


if __name__ == "__main__":
    main()
