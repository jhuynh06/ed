"""
Generate a simple test WAV file that plays "Twinkle Twinkle Little Star".
Easy to recognize if the speaker is working.

Usage:
    python generate_test_tone.py

Outputs: test_song.wav in the same directory.
"""

import math
import struct
import wave

SAMPLE_RATE = 16000
DURATION_PER_NOTE = 0.4  # seconds per note
PAUSE = 0.05             # short gap between notes
AMPLITUDE = 20000        # volume (max 32767 for 16-bit)

# Note frequencies (Hz)
NOTES = {
    "C4": 261.63,
    "D4": 293.66,
    "E4": 329.63,
    "F4": 349.23,
    "G4": 392.00,
    "A4": 440.00,
    "B4": 493.88,
    "C5": 523.25,
}

# Twinkle Twinkle Little Star melody
MELODY = [
    "C4", "C4", "G4", "G4", "A4", "A4", "G4", None,
    "F4", "F4", "E4", "E4", "D4", "D4", "C4", None,
    "G4", "G4", "F4", "F4", "E4", "E4", "D4", None,
    "G4", "G4", "F4", "F4", "E4", "E4", "D4", None,
    "C4", "C4", "G4", "G4", "A4", "A4", "G4", None,
    "F4", "F4", "E4", "E4", "D4", "D4", "C4", None,
]


def generate_tone(freq, duration, sample_rate, amplitude):
    """Generate a sine wave tone."""
    samples = []
    num_samples = int(sample_rate * duration)
    for i in range(num_samples):
        t = i / sample_rate
        # Apply a simple envelope to avoid clicks
        envelope = 1.0
        fade = int(sample_rate * 0.02)  # 20ms fade
        if i < fade:
            envelope = i / fade
        elif i > num_samples - fade:
            envelope = (num_samples - i) / fade

        value = amplitude * envelope * math.sin(2 * math.pi * freq * t)
        samples.append(int(value))
    return samples


def generate_silence(duration, sample_rate):
    """Generate silence."""
    return [0] * int(sample_rate * duration)


def main():
    all_samples = []

    for note in MELODY:
        if note is None:
            # Rest / pause
            all_samples.extend(generate_silence(DURATION_PER_NOTE, SAMPLE_RATE))
        else:
            freq = NOTES[note]
            all_samples.extend(generate_tone(freq, DURATION_PER_NOTE, SAMPLE_RATE, AMPLITUDE))
        # Small gap between notes
        all_samples.extend(generate_silence(PAUSE, SAMPLE_RATE))

    # Write WAV file
    output_path = "test_song.wav"
    with wave.open(output_path, "w") as wf:
        wf.setnchannels(1)          # mono
        wf.setsampwidth(2)          # 16-bit
        wf.setframerate(SAMPLE_RATE)
        raw = struct.pack(f"<{len(all_samples)}h", *all_samples)
        wf.writeframes(raw)

    duration = len(all_samples) / SAMPLE_RATE
    print(f"Generated: {output_path}")
    print(f"  {SAMPLE_RATE} Hz, 16-bit, mono")
    print(f"  {len(all_samples)} samples ({duration:.1f}s)")
    print(f"  Melody: Twinkle Twinkle Little Star")


if __name__ == "__main__":
    main()
