"""
AudioBridge.py — Receives audio from ESP32 over WebSocket and forwards to Ed backend.

This bridge:
  1. Runs a WebSocket server that the ESP32 connects to
  2. Receives raw 16-bit PCM audio chunks from ESP32
  3. Forwards audio to the backend's /ws/audio endpoint
  4. Relays TTS audio from backend back to ESP32

Usage:
    pip install websockets
    python AudioBridge.py

Configuration:
    - ESP32 connects to this bridge on port 8081
    - This bridge connects to backend on port 8000
"""

import asyncio
import json
import struct
import socket
import time
from dataclasses import dataclass, field

import websockets

# ── Configuration ─────────────────────────────────────────────────────

ESP32_PORT = 8081                          # Port ESP32 connects to
BACKEND_WS_URL = "ws://localhost:8000/ws/audio"  # Backend audio endpoint
SAMPLE_RATE = 16000
CHUNK_SAMPLES = 512                        # Must match ESP32 config

# ── State ─────────────────────────────────────────────────────────────

@dataclass
class BridgeState:
    esp32_ws: object = None
    backend_ws: object = None
    audio_chunks_received: int = 0
    audio_bytes_forwarded: int = 0
    connected_at: float = 0.0


state = BridgeState()


# ── Utilities ─────────────────────────────────────────────────────────

def get_local_ip() -> str:
    """Get this machine's IP on the local network."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def calculate_rms(pcm_data: bytes) -> int:
    """Calculate RMS level from 16-bit PCM data."""
    if len(pcm_data) < 2:
        return 0
    samples = struct.unpack(f"<{len(pcm_data)//2}h", pcm_data)
    sum_squares = sum(s * s for s in samples)
    return int((sum_squares / len(samples)) ** 0.5)


# ── Backend Connection ────────────────────────────────────────────────

async def connect_to_backend():
    """Establish and maintain connection to backend."""
    while True:
        try:
            print(f"  Connecting to backend: {BACKEND_WS_URL}")
            async with websockets.connect(BACKEND_WS_URL) as ws:
                state.backend_ws = ws
                print(f"  Backend connected")

                # Send hello
                await ws.send(json.dumps({
                    "type": "bridge_hello",
                    "sample_rate": SAMPLE_RATE,
                    "chunk_samples": CHUNK_SAMPLES,
                }))

                # Listen for messages from backend (TTS audio, commands)
                async for message in ws:
                    if isinstance(message, bytes):
                        # TTS audio to forward to ESP32
                        if state.esp32_ws:
                            try:
                                await state.esp32_ws.send(message)
                            except Exception as e:
                                print(f"  Error forwarding TTS to ESP32: {e}")
                    else:
                        # JSON command
                        try:
                            data = json.loads(message)
                            msg_type = data.get("type")
                            if msg_type == "tts_start":
                                print(f"  [Backend] TTS starting...")
                            elif msg_type == "tts_end":
                                print(f"  [Backend] TTS complete")
                            elif msg_type == "command":
                                # Forward command to ESP32
                                if state.esp32_ws:
                                    await state.esp32_ws.send(message)
                        except json.JSONDecodeError:
                            pass

        except websockets.ConnectionClosed:
            print(f"  Backend disconnected, reconnecting...")
        except Exception as e:
            print(f"  Backend connection error: {e}")

        state.backend_ws = None
        await asyncio.sleep(2)


# ── ESP32 Connection Handler ──────────────────────────────────────────

async def handle_esp32(websocket):
    """Handle incoming ESP32 WebSocket connection."""
    state.esp32_ws = websocket
    state.connected_at = time.time()
    state.audio_chunks_received = 0
    state.audio_bytes_forwarded = 0

    remote = websocket.remote_address
    print(f"\n  ESP32 connected from {remote[0]}:{remote[1]}")

    last_stats_time = time.time()

    try:
        async for message in websocket:
            if isinstance(message, bytes):
                # Raw PCM audio from ESP32
                state.audio_chunks_received += 1

                # Forward to backend if connected
                if state.backend_ws:
                    try:
                        await state.backend_ws.send(message)
                        state.audio_bytes_forwarded += len(message)
                    except Exception as e:
                        print(f"  Error forwarding to backend: {e}")

                # Print stats every 5 seconds
                now = time.time()
                if now - last_stats_time >= 5.0:
                    duration = now - state.connected_at
                    chunks_per_sec = state.audio_chunks_received / duration
                    kbps = (state.audio_bytes_forwarded * 8) / duration / 1000
                    rms = calculate_rms(message)
                    print(f"  [Audio] {chunks_per_sec:.1f} chunks/s, {kbps:.1f} kbps, RMS: {rms}")
                    last_stats_time = now

            else:
                # JSON message from ESP32
                try:
                    data = json.loads(message)
                    msg_type = data.get("type")

                    if msg_type == "hello":
                        print(f"  [ESP32] Hello: {data}")
                        # Forward device info to backend
                        if state.backend_ws:
                            await state.backend_ws.send(json.dumps({
                                "type": "device_connected",
                                "device": data.get("device", "esp32"),
                                "sample_rate": data.get("sample_rate", SAMPLE_RATE),
                            }))
                    else:
                        print(f"  [ESP32] {message}")

                except json.JSONDecodeError:
                    print(f"  [ESP32] Invalid JSON: {message[:100]}")

    except websockets.ConnectionClosed:
        print(f"  ESP32 disconnected")
    except Exception as e:
        print(f"  ESP32 error: {e}")
    finally:
        state.esp32_ws = None
        # Notify backend
        if state.backend_ws:
            try:
                await state.backend_ws.send(json.dumps({"type": "device_disconnected"}))
            except Exception:
                pass


# ── Main ──────────────────────────────────────────────────────────────

async def main():
    local_ip = get_local_ip()

    print(f"=== Ed Audio Bridge ===")
    print()
    print(f"  ESP32 WebSocket Server:")
    print(f"    ws://{local_ip}:{ESP32_PORT}/audio")
    print()
    print(f"  Backend connection:")
    print(f"    {BACKEND_WS_URL}")
    print()
    print(f"  Update your ESP32 firmware with:")
    print(f'    const char* WS_HOST = "{local_ip}";')
    print(f'    const uint16_t WS_PORT = {ESP32_PORT};')
    print()
    print(f"  Waiting for connections...")
    print()

    # Start backend connection task
    backend_task = asyncio.create_task(connect_to_backend())

    # Start ESP32 WebSocket server
    async with websockets.serve(handle_esp32, "0.0.0.0", ESP32_PORT, ping_interval=None, ping_timeout=None, max_size=None):
        try:
            await asyncio.Future()  # Run forever
        except asyncio.CancelledError:
            pass

    backend_task.cancel()
    print("\nBridge stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
