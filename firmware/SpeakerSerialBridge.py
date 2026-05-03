"""
SpeakerSerialBridge.py — Receives TTS audio from backend, sends raw PCM to ESP32 over serial.

Includes audio processing: gain, soft clipping, low-pass filter, fade-in/out.

Usage:
    python SpeakerSerialBridge.py COM12       # explicit port
    python SpeakerSerialBridge.py             # auto-detect (looks for SPEAKER_READY)
"""

import asyncio
import json
import math
import struct
import sys
import time

import serial
import serial.tools.list_ports
import websockets

BAUD_RATE = 921600
BACKEND_WS_URL = "ws://localhost:8000/ws/speaker"
SAMPLE_RATE = 16000
GAIN = 3.0


# ── Audio Processing ─────────────────────────────────────────────────

class AudioProcessor:
    """Processes PCM chunks with gain, soft clip, low-pass filter, and fade."""

    def __init__(self, sample_rate: int = 16000, gain: float = 3.0):
        self.gain = gain
        # Single-pole low-pass filter at 7kHz (removes serial artifacts)
        rc = 1.0 / (2.0 * math.pi * 7000)
        dt = 1.0 / sample_rate
        self.alpha = dt / (rc + dt)
        self.prev = 0.0
        self.first_chunk = True

    def soft_clip(self, x: float) -> float:
        """Tanh soft clipping — smooth saturation instead of hard clip."""
        return math.tanh(x / 32768.0) * 32768.0

    def process(self, pcm: bytes) -> bytes:
        n = len(pcm) // 2
        samples = struct.unpack(f"<{n}h", pcm)
        out = []

        for i, s in enumerate(samples):
            # Gain
            x = s * self.gain
            # Soft clip
            x = self.soft_clip(x)
            # Low-pass filter
            x = self.prev + self.alpha * (x - self.prev)
            self.prev = x
            # Fade-in first 200 samples (~12ms) to avoid initial pop
            if self.first_chunk and i < 200:
                x *= i / 200.0
            out.append(max(-32768, min(32767, int(x))))

        self.first_chunk = False
        return struct.pack(f"<{n}h", *out)

    def fade_out(self, pcm: bytes) -> bytes:
        """Apply fade-out to final chunk to avoid end pop."""
        n = len(pcm) // 2
        samples = list(struct.unpack(f"<{n}h", pcm))
        fade_len = min(200, n)
        for i in range(fade_len):
            idx = n - fade_len + i
            samples[idx] = int(samples[idx] * (1.0 - i / fade_len))
        return struct.pack(f"<{n}h", *samples)

    def reset(self):
        """Reset filter state between utterances."""
        self.prev = 0.0
        self.first_chunk = True


# ── Port Detection ───────────────────────────────────────────────────

def find_speaker_port() -> str | None:
    candidates = [
        p.device for p in serial.tools.list_ports.comports()
        if "CP210" in (p.description or "") or "CH340" in (p.description or "")
    ]
    for port in candidates:
        try:
            s = serial.Serial(port, BAUD_RATE, timeout=2, dsrdtr=False, rtscts=False)
            s.dtr = False
            s.rts = False
            time.sleep(0.1)
            s.reset_input_buffer()
            for _ in range(20):
                line = s.readline().decode(errors="replace").strip()
                if "SPEAKER_READY" in line:
                    s.close()
                    return port
            s.close()
        except (serial.SerialException, OSError):
            continue
    return None


# ── Main ─────────────────────────────────────────────────────────────

async def main():
    port = sys.argv[1] if len(sys.argv) > 1 else find_speaker_port()
    if not port:
        print("No speaker ESP32 found. Specify COM port.")
        return

    print(f"=== Ed Speaker Serial Bridge ===")
    print(f"  Serial: {port} @ {BAUD_RATE}")
    print(f"  Backend: {BACKEND_WS_URL}")
    print(f"  Gain: {GAIN}x | LPF: 7kHz | Soft clip: tanh")
    print()

    ser = serial.Serial(port, BAUD_RATE, timeout=1, dsrdtr=False, rtscts=False)
    ser.dtr = False
    ser.rts = False
    time.sleep(0.1)
    ser.reset_input_buffer()

    processor = AudioProcessor(SAMPLE_RATE, GAIN)

    print(f"  Serial open. Connecting to backend...")

    while True:
        try:
            async with websockets.connect(BACKEND_WS_URL) as ws:
                await ws.send(json.dumps({
                    "type": "speaker_hello",
                    "sample_rate": SAMPLE_RATE,
                    "transport": "serial",
                }))
                print(f"  Backend connected. Waiting for TTS audio...\n")

                chunks = []
                async for message in ws:
                    if isinstance(message, bytes):
                        chunks.append(message)
                        processed = processor.process(message)
                        ser.write(processed)
                        print(f"  [TTS] Sent {len(message)} bytes (chunk {len(chunks)})")
                    else:
                        data = json.loads(message)
                        msg_type = data.get("type")
                        if msg_type == "tts_start":
                            processor.reset()
                            chunks.clear()
                            print(f"  [TTS] Starting: {data.get('text', '')[:50]}")
                        elif msg_type == "tts_end":
                            print(f"  [TTS] Complete ({len(chunks)} chunks)")

        except (websockets.ConnectionClosed, ConnectionRefusedError, OSError) as e:
            print(f"  Backend disconnected ({e}), reconnecting...")
            await asyncio.sleep(2)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
