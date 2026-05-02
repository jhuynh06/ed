"""
test_audio_bridge.py — Sends a test WAV file through the audio WebSocket endpoint.

Simulates what AudioBridge does, but using a file instead of live ESP32 audio.
Useful for testing the backend pipeline without hardware.

Usage:
    1. Start the backend:  cd backend && uv run uvicorn app.main:app --reload
    2. Run this script:    python test_audio_bridge.py [path_to_wav]

If no WAV file is given, it uses the test fixture calm_speech.wav.
"""

import asyncio
import json
import struct
import sys
import wave

import websockets

BACKEND_WS_URL = "ws://localhost:8000/ws/audio"
CHUNK_SAMPLES = 512  # Match ESP32 config


async def send_wav(wav_path: str):
    print(f"=== Audio Bridge Test ===")
    print(f"  File:    {wav_path}")
    print(f"  Backend: {BACKEND_WS_URL}")
    print()

    # Read WAV file
    with wave.open(wav_path, "rb") as wf:
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)

    print(f"  WAV: {channels}ch, {sample_width * 8}-bit, {framerate}Hz, {n_frames} frames")

    # Convert to mono 16-bit if needed
    if sample_width == 2:
        samples = struct.unpack(f"<{len(raw) // 2}h", raw)
    elif sample_width == 4:
        samples_32 = struct.unpack(f"<{len(raw) // 4}i", raw)
        samples = tuple(s >> 16 for s in samples_32)
    else:
        print(f"  ERROR: Unsupported sample width: {sample_width}")
        return

    # Take only left channel if stereo
    if channels == 2:
        samples = samples[::2]

    print(f"  Mono samples: {len(samples)}")
    print(f"  Duration: {len(samples) / framerate:.1f}s")
    print()

    # Connect and stream
    async with websockets.connect(BACKEND_WS_URL) as ws:
        print(f"  Connected to backend")

        # Send hello
        await ws.send(json.dumps({
            "type": "bridge_hello",
            "sample_rate": framerate,
            "chunk_samples": CHUNK_SAMPLES,
        }))

        # Stream in chunks, simulating real-time
        chunk_duration = CHUNK_SAMPLES / framerate
        chunks_sent = 0

        for i in range(0, len(samples), CHUNK_SAMPLES):
            chunk = samples[i:i + CHUNK_SAMPLES]

            # Pad last chunk if needed
            if len(chunk) < CHUNK_SAMPLES:
                chunk = chunk + (0,) * (CHUNK_SAMPLES - len(chunk))

            # Pack as 16-bit PCM bytes
            pcm_bytes = struct.pack(f"<{CHUNK_SAMPLES}h", *chunk)
            await ws.send(pcm_bytes)
            chunks_sent += 1

            # Simulate real-time pacing
            await asyncio.sleep(chunk_duration)

            if chunks_sent % 50 == 0:
                elapsed = chunks_sent * chunk_duration
                print(f"  Sent {chunks_sent} chunks ({elapsed:.1f}s)")

        print(f"\n  Done! Sent {chunks_sent} chunks ({chunks_sent * chunk_duration:.1f}s)")
        print(f"  Waiting a few seconds for backend to finish processing...")
        await asyncio.sleep(5)

        # Send disconnect
        try:
            await ws.send(json.dumps({"type": "device_disconnected"}))
        except Exception:
            pass

        print(f"  Check the backend terminal for transcription and emotion results.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        wav_file = sys.argv[1]
    else:
        wav_file = "../backend/tests/fixtures/calm_speech.wav"

    try:
        asyncio.run(send_wav(wav_file))
    except ConnectionRefusedError:
        print("ERROR: Can't connect to backend. Is it running?")
        print("  Start it with: cd backend && uv run uvicorn app.main:app --reload")
    except KeyboardInterrupt:
        print("\nStopped.")
