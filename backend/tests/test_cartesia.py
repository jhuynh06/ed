"""Test Cartesia TTS — streaming audio to a file."""

import os
import httpx
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

API_KEY = os.environ["CARTESIA_API_KEY"]

# List available voices first
r = httpx.get(
    "https://api.cartesia.ai/voices",
    headers={"X-API-Key": API_KEY, "Cartesia-Version": "2024-06-10"},
)
r.raise_for_status()
voices = r.json()
# Pick a warm female voice for Margaret's bear
voice = next(
    (v for v in voices if "female" in v.get("description", "").lower()),
    voices[0],
)
print(f"Using voice: {voice['name']} ({voice['id']})")

# Generate TTS — raw PCM 16kHz mono (what ESP32 MAX98357A expects)
payload = {
    "model_id": "sonic-english",
    "transcript": "I'm right here with you. Let's breathe together.",
    "voice": {"mode": "id", "id": voice["id"]},
    "output_format": {
        "container": "raw",
        "encoding": "pcm_s16le",
        "sample_rate": 16000,
    },
}

print("Requesting TTS...")
with httpx.stream(
    "POST",
    "https://api.cartesia.ai/tts/bytes",
    headers={
        "X-API-Key": API_KEY,
        "Cartesia-Version": "2024-06-10",
        "Content-Type": "application/json",
    },
    json=payload,
    timeout=30,
) as resp:
    resp.raise_for_status()
    audio_bytes = b"".join(resp.iter_bytes())

print(f"Received {len(audio_bytes):,} bytes of PCM audio")
assert len(audio_bytes) > 1000, "Audio too short — something went wrong"

# Save for inspection
out_path = os.path.join(os.path.dirname(__file__), "test_tts_output.pcm")
with open(out_path, "wb") as f:
    f.write(audio_bytes)

duration_s = len(audio_bytes) / (16000 * 2)  # 16kHz, 16-bit = 2 bytes/sample
print(f"Duration: {duration_s:.1f}s")
print(f"Saved to: {out_path}")
print("Cartesia TTS OK")
