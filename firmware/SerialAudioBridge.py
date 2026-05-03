"""
SerialAudioBridge.py — Reads PCM audio from ESP32 over USB serial, forwards to backend.

No WiFi needed on the ESP32. Just a USB cable.

Usage:
    pip install pyserial websockets
    python SerialAudioBridge.py          # auto-detects COM port
    python SerialAudioBridge.py COM11    # explicit port
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
BACKEND_WS_URL = "ws://localhost:8000/ws/audio"
SAMPLE_RATE = 16000
SYNC_MARKER = bytes([0xED, 0x0A])

# ── Auto-detect ESP32 COM port ────────────────────────────────────────

def find_esp32_port() -> str | None:
    for p in serial.tools.list_ports.comports():
        if "CP210" in (p.description or "") or "CH340" in (p.description or "") or "USB" in (p.description or ""):
            return p.device
    return None


# ── Serial reader ─────────────────────────────────────────────────────

def read_chunk(ser: serial.Serial) -> bytes | None:
    """Read one framed audio chunk: sync(2) + count(2) + PCM data."""
    # Find sync marker
    buf = ser.read(1)
    if not buf:
        return None
    if buf[0] != SYNC_MARKER[0]:
        return None
    buf = ser.read(1)
    if not buf or buf[0] != SYNC_MARKER[1]:
        return None

    # Read sample count (2 bytes LE)
    count_bytes = ser.read(2)
    if len(count_bytes) < 2:
        return None
    sample_count = struct.unpack("<H", count_bytes)[0]

    if sample_count == 0 or sample_count > 2048:
        return None

    # Read PCM data
    pcm_bytes = ser.read(sample_count * 2)
    if len(pcm_bytes) < sample_count * 2:
        return None

    return pcm_bytes


# ── Main ──────────────────────────────────────────────────────────────

async def main():
    # Determine COM port
    port = sys.argv[1] if len(sys.argv) > 1 else find_esp32_port()
    if not port:
        print("No ESP32 found. Specify COM port: python SerialAudioBridge.py COM11")
        return

    print(f"=== Ed Serial Audio Bridge ===")
    print(f"  Serial: {port} @ {BAUD_RATE}")
    print(f"  Backend: {BACKEND_WS_URL}")
    print()

    # Open serial (dsrdtr/rtscts off to avoid resetting ESP32)
    ser = serial.Serial(port, BAUD_RATE, timeout=1, dsrdtr=False, rtscts=False)
    ser.dtr = False
    ser.rts = False
    time.sleep(0.1)
    ser.reset_input_buffer()

    print(f"  Serial open. Connecting to backend...")

    chunks_forwarded = 0
    bytes_forwarded = 0
    last_stats = time.time()

    while True:
        try:
            async with websockets.connect(BACKEND_WS_URL) as ws:
                await ws.send(json.dumps({
                    "type": "bridge_hello",
                    "sample_rate": SAMPLE_RATE,
                    "chunk_samples": 512,
                    "transport": "serial",
                }))
                print(f"  Backend connected. Streaming...")
                print()

                while True:
                    # Read from serial (blocking, in thread to not block asyncio)
                    pcm = await asyncio.get_event_loop().run_in_executor(None, read_chunk, ser)

                    if pcm is None:
                        continue

                    # Forward to backend
                    await ws.send(pcm)
                    chunks_forwarded += 1
                    bytes_forwarded += len(pcm)

                    # Stats every 5s
                    now = time.time()
                    if now - last_stats >= 5.0:
                        elapsed = now - last_stats
                        kbps = (bytes_forwarded * 8) / elapsed / 1000
                        rms = _rms(pcm)
                        print(f"  [Audio] {chunks_forwarded/elapsed:.1f} chunks/s, {kbps:.1f} kbps, RMS: {rms}")
                        chunks_forwarded = 0
                        bytes_forwarded = 0
                        last_stats = now

        except (websockets.ConnectionClosed, ConnectionRefusedError, OSError) as e:
            print(f"  Backend disconnected ({e}), reconnecting...")
            await asyncio.sleep(2)


def _rms(pcm: bytes) -> int:
    if len(pcm) < 2:
        return 0
    samples = struct.unpack(f"<{len(pcm)//2}h", pcm)
    return int((sum(s * s for s in samples) / len(samples)) ** 0.5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
