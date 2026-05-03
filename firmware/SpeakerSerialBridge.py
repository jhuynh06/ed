"""
SpeakerSerialBridge.py — Receives TTS audio from backend, sends to ESP32 speaker over serial.

Usage:
    python SpeakerSerialBridge.py COM13       # explicit port
    python SpeakerSerialBridge.py             # auto-detect (looks for SPEAKER_READY)
"""

import asyncio
import json
import struct
import sys
import time

import serial
import serial.tools.list_ports
import websockets

# ── Config ────────────────────────────────────────────────────────────
BAUD_RATE = 921600
BACKEND_WS_URL = "ws://localhost:8000/ws/speaker"
SYNC_MARKER = bytes([0xED, 0x0A])
CHUNK_SAMPLES = 512  # send in 512-sample frames to match mic protocol


# ── Auto-detect speaker port ─────────────────────────────────────────

def find_speaker_port(exclude: list[str] | None = None) -> str | None:
    """Try each serial port, look for SPEAKER_READY identification."""
    exclude = exclude or []
    candidates = [
        p.device for p in serial.tools.list_ports.comports()
        if ("CP210" in (p.description or "") or "CH340" in (p.description or ""))
        and p.device not in exclude
    ]
    for port in candidates:
        try:
            s = serial.Serial(port, BAUD_RATE, timeout=2, dsrdtr=False, rtscts=False)
            s.dtr = False
            s.rts = False
            time.sleep(0.1)
            s.reset_input_buffer()
            # Wait for identification
            for _ in range(20):
                line = s.readline().decode(errors="replace").strip()
                if "SPEAKER_READY" in line:
                    s.close()
                    return port
            s.close()
        except (serial.SerialException, OSError):
            continue
    return None


# ── Send framed PCM to ESP32 ─────────────────────────────────────────

def send_pcm_chunk(ser: serial.Serial, pcm: bytes) -> None:
    """Send PCM data in framed chunks to the speaker ESP32."""
    offset = 0
    frame_bytes = CHUNK_SAMPLES * 2
    while offset < len(pcm):
        chunk = pcm[offset:offset + frame_bytes]
        sample_count = len(chunk) // 2
        ser.write(SYNC_MARKER)
        ser.write(struct.pack("<H", sample_count))
        ser.write(chunk)
        offset += frame_bytes


# ── Main ──────────────────────────────────────────────────────────────

async def main():
    port = sys.argv[1] if len(sys.argv) > 1 else find_speaker_port()
    if not port:
        print("No speaker ESP32 found. Specify COM port: python SpeakerSerialBridge.py COM13")
        return

    print(f"=== Ed Speaker Serial Bridge ===")
    print(f"  Serial: {port} @ {BAUD_RATE}")
    print(f"  Backend: {BACKEND_WS_URL}")
    print()

    ser = serial.Serial(port, BAUD_RATE, timeout=1, dsrdtr=False, rtscts=False)
    ser.dtr = False
    ser.rts = False
    time.sleep(0.1)
    ser.reset_input_buffer()

    print(f"  Serial open. Connecting to backend...")

    while True:
        try:
            async with websockets.connect(BACKEND_WS_URL) as ws:
                await ws.send(json.dumps({
                    "type": "speaker_hello",
                    "sample_rate": 16000,
                    "transport": "serial",
                }))
                print(f"  Backend connected. Waiting for TTS audio...")
                print()

                async for message in ws:
                    if isinstance(message, bytes):
                        # PCM audio from backend TTS
                        send_pcm_chunk(ser, message)
                        print(f"  [TTS] Sent {len(message)} bytes to speaker")
                    else:
                        data = json.loads(message)
                        msg_type = data.get("type")
                        if msg_type == "tts_start":
                            print(f"  [TTS] Starting: {data.get('text', '')[:50]}")
                        elif msg_type == "tts_end":
                            print(f"  [TTS] Complete")

        except (websockets.ConnectionClosed, ConnectionRefusedError, OSError) as e:
            print(f"  Backend disconnected ({e}), reconnecting...")
            await asyncio.sleep(2)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
