"""
SpeakerBridge.py — Sends a WAV file from the laptop to the ESP32 speaker over WebSocket.

This bridge:
  1. Runs a WebSocket server that the ESP32 connects to
  2. Waits for the ESP32 to connect and send a "hello"
  3. Reads a WAV file, extracts raw PCM data
  4. Applies volume scaling
  5. Streams the PCM data in chunks to the ESP32
  6. Sends an EOF marker so the ESP32 knows playback is done

Usage:
    pip install websockets
    python SpeakerBridge.py <audio_file.wav>
    python SpeakerBridge.py <audio_file.wav> --volume 0.5
    python SpeakerBridge.py --volume 2.0    # interactive mode, 2x louder

Volume: 0.0 = silent, 1.0 = original, 2.0 = 2x louder, etc.
"""

import argparse
import array
import asyncio
import json
import socket
import struct
import sys
import wave
from pathlib import Path

import websockets

# ── Configuration ─────────────────────────────────────────────────────

BRIDGE_PORT = 8082
CHUNK_SIZE = 512
volume = 1.0  # Set via --volume flag

# ── State ─────────────────────────────────────────────────────────────

esp32_ws = None
esp32_ready = asyncio.Event()
file_queue: asyncio.Queue = asyncio.Queue()


# ── Utilities ─────────────────────────────────────────────────────────

def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def read_wav(filepath: str):
    with wave.open(filepath, "rb") as wf:
        sample_rate = wf.getframerate()
        num_channels = wf.getnchannels()
        bits_per_sample = wf.getsampwidth() * 8
        pcm_data = wf.readframes(wf.getnframes())

    # Apply volume scaling
    if volume != 1.0 and bits_per_sample == 16:
        samples = array.array("h", pcm_data)
        for i in range(len(samples)):
            scaled = int(samples[i] * volume)
            # Clamp to 16-bit range
            if scaled > 32767:
                scaled = 32767
            elif scaled < -32768:
                scaled = -32768
            samples[i] = scaled
        pcm_data = samples.tobytes()

    return sample_rate, bits_per_sample, num_channels, pcm_data


# ── Audio Streaming ──────────────────────────────────────────────────

async def stream_file(ws, filepath: str):
    path = Path(filepath)
    if not path.exists():
        print(f"  ERROR: File not found: {filepath}")
        return

    print(f"\n  Streaming: {path.name}")

    try:
        sample_rate, bits_per_sample, num_channels, pcm_data = read_wav(filepath)
    except Exception as e:
        print(f"  ERROR: Could not read WAV: {e}")
        return

    total_bytes = len(pcm_data)
    bytes_per_sec = sample_rate * num_channels * (bits_per_sample // 8)
    duration = total_bytes / bytes_per_sec
    print(f"  Format: {sample_rate} Hz, {bits_per_sample}-bit, {num_channels} ch, volume: {volume:.0%}")
    print(f"  Size: {total_bytes:,} bytes ({duration:.1f}s)")

    # 12-byte header: sampleRate(u32) | bitsPerSample(u16) | numChannels(u16) | totalBytes(u32)
    header = struct.pack("<IHHI", sample_rate, bits_per_sample, num_channels, total_bytes)
    await ws.send(header)

    # Pace chunks to ~1.5x real-time so the DMA buffer stays fed but doesn't overflow
    seconds_per_chunk = CHUNK_SIZE / bytes_per_sec
    chunk_delay = seconds_per_chunk / 1.5  # send slightly faster than real-time

    sent = 0
    while sent < total_bytes:
        end = min(sent + CHUNK_SIZE, total_bytes)
        await ws.send(pcm_data[sent:end])
        sent = end

        if (sent // CHUNK_SIZE) % 100 == 0:
            pct = sent * 100 / total_bytes
            print(f"  Sent {sent:,} / {total_bytes:,} bytes ({pct:.0f}%)")

        await asyncio.sleep(chunk_delay)

    print(f"  Done: {total_bytes:,} bytes sent")
    await ws.send(json.dumps({"type": "eof"}))
    print("  EOF sent, waiting for ESP32 to finish playback...")


# ── ESP32 Connection Handler ──────────────────────────────────────────

async def handle_esp32(websocket):
    global esp32_ws

    esp32_ws = websocket
    remote = websocket.remote_address
    print(f"\n  ESP32 connected from {remote[0]}:{remote[1]}")

    try:
        async for message in websocket:
            if isinstance(message, str):
                try:
                    data = json.loads(message)
                    msg_type = data.get("type")

                    if msg_type == "hello":
                        print(f"  [ESP32] Hello: {data}")
                        esp32_ready.set()

                        if not file_queue.empty():
                            filepath = await file_queue.get()
                            await stream_file(websocket, filepath)

                    elif msg_type == "ready":
                        print(f"  [ESP32] Ready for next file")
                        esp32_ready.set()

                        if not file_queue.empty():
                            filepath = await file_queue.get()
                            await stream_file(websocket, filepath)

                    else:
                        print(f"  [ESP32] {message}")

                except json.JSONDecodeError:
                    print(f"  [ESP32] {message}")
            else:
                print(f"  [ESP32] Binary: {len(message)} bytes")

    except websockets.ConnectionClosed:
        print("  ESP32 disconnected")
    finally:
        esp32_ws = None
        esp32_ready.clear()


# ── Interactive Console ───────────────────────────────────────────────

async def console_input():
    global volume
    loop = asyncio.get_event_loop()

    while True:
        line = await loop.run_in_executor(None, sys.stdin.readline)
        line = line.strip()

        if not line:
            continue

        if line.lower() in ("quit", "exit", "q"):
            print("  Shutting down...")
            break

        # Volume command: "volume 0.5" or "v 2.0"
        parts = line.split()
        if parts[0].lower() in ("volume", "v") and len(parts) == 2:
            try:
                volume = float(parts[1])
                print(f"  Volume set to {volume:.0%}")
            except ValueError:
                print(f"  Invalid volume value: {parts[1]}")
            continue

        # Help
        if line.lower() in ("help", "h", "?"):
            print("  Commands:")
            print("    <filepath>       Stream a WAV file")
            print("    volume <0.0-N>   Set volume (1.0 = original)")
            print("    quit             Exit")
            continue

        filepath = line.strip('"').strip("'")

        if not Path(filepath).exists():
            print(f"  File not found: {filepath}")
            continue

        if esp32_ws and esp32_ready.is_set():
            esp32_ready.clear()
            await stream_file(esp32_ws, filepath)
        else:
            await file_queue.put(filepath)
            if not esp32_ws:
                print(f"  Queued: {filepath} (waiting for ESP32 to connect)")
            else:
                print(f"  Queued: {filepath} (waiting for ESP32 to be ready)")


# ── Main ──────────────────────────────────────────────────────────────

async def main(args):
    global volume
    volume = args.volume

    local_ip = get_local_ip()

    print(f"=== Ed Speaker Bridge ===")
    print()
    print(f"  WebSocket Server:")
    print(f"    ws://{local_ip}:{BRIDGE_PORT}/speaker")
    print(f"  Volume: {volume:.0%}")
    print()
    print(f"  Update your ESP32 firmware with:")
    print(f'    const char* WS_HOST = "{local_ip}";')
    print(f"    const uint16_t WS_PORT = {BRIDGE_PORT};")
    print()

    if args.file:
        filepath = args.file
        if Path(filepath).exists():
            await file_queue.put(filepath)
            print(f"  File queued: {filepath}")
        else:
            print(f"  WARNING: File not found: {filepath}")

    print(f"  Waiting for ESP32 to connect...")
    print(f"  Type a file path to stream, or 'quit' to exit.\n")

    async with websockets.serve(handle_esp32, "0.0.0.0", BRIDGE_PORT):
        try:
            await console_input()
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass

    print("\nBridge stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stream WAV audio to ESP32 speaker over WebSocket")
    parser.add_argument("file", nargs="?", default=None, help="WAV file to stream")
    parser.add_argument("--volume", "-v", type=float, default=1.0,
                        help="Volume multiplier (0.0=silent, 1.0=original, 2.0=2x louder)")
    args = parser.parse_args()

    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        print("\nShutting down...")
