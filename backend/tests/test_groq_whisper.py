"""Test Groq Whisper — transcription API contract check."""

import os
import wave
import struct
from dotenv import load_dotenv
from groq import Groq

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

client = Groq(api_key=os.environ["GROQ_API_KEY"])

# List available models to confirm whisper is available
models = client.models.list()
whisper_models = [m for m in models.data if "whisper" in m.id.lower()]
print(f"Whisper models available: {[m.id for m in whisper_models]}")

# Generate a minimal valid WAV file (1 second of silence at 16kHz mono)
wav_path = os.path.join(os.path.dirname(__file__), "test_silence.wav")
num_samples = 16000
with wave.open(wav_path, "w") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)  # 16-bit
    wf.setframerate(16000)
    wf.writeframes(struct.pack("<" + "h" * num_samples, *([0] * num_samples)))

print(f"Created test WAV: {wav_path}")

# Transcribe
with open(wav_path, "rb") as f:
    result = client.audio.transcriptions.create(
        file=("test_silence.wav", f, "audio/wav"),
        model="whisper-large-v3-turbo",
        response_format="json",
        language="en",
    )

print(f"Transcription: '{result.text}'")
print(f"Response type: {type(result)}")
print("Groq Whisper OK")

# Cleanup
os.remove(wav_path)
