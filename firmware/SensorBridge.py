"""
SensorBridge.py — Reads JSON from ESP32 serial and forwards to Ed backend via WebSocket.

Usage:
    pip install pyserial websockets
    python SensorBridge.py

Set COM_PORT to your ESP32's serial port (e.g. COM3 on Windows, /dev/ttyUSB0 on Linux).
Set WS_URL to your backend's WebSocket endpoint.
"""

import asyncio
import json
import sys

import serial
import websockets

# ── Configuration ─────────────────────────────────────────────────────

COM_PORT = "COM12"          # Change to your ESP32 port
BAUD_RATE = 115200
WS_URL = "ws://localhost:8000/ws/bear"

# ── Main loop ─────────────────────────────────────────────────────────

async def bridge():
    print(f"=== Ed Sensor Bridge ===")
    print(f"  Serial: {COM_PORT} @ {BAUD_RATE}")
    print(f"  Backend: {WS_URL}")
    print()

    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=0.1)
    except serial.SerialException as e:
        print(f"  ERROR: Could not open {COM_PORT}: {e}")
        print(f"  Available ports:")
        from serial.tools.list_ports import comports
        for p in comports():
            print(f"    {p.device} — {p.description}")
        sys.exit(1)

    print(f"  Serial connected. Waiting for backend WebSocket...")

    async for ws in websockets.connect(WS_URL):
        print(f"  WebSocket connected. Bridging data...\n")
        try:
            while True:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    await asyncio.sleep(0.01)
                    continue

                # Only forward lines that look like JSON sensor packets
                if not line.startswith("{"):
                    # Print non-JSON lines (boot messages, debug output)
                    print(f"  [ESP32] {line}")
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if data.get("type") != "sensor_data":
                    continue

                await ws.send(line)

                # Print a compact summary
                imu = data.get("imu", {})
                touch = data.get("touch", {})
                flags = []
                if imu.get("fall_detected"):
                    flags.append("FALL")
                if imu.get("hug_detected"):
                    flags.append("HUG")
                if imu.get("rocking_detected"):
                    flags.append("ROCKING")
                if touch.get("petting_detected"):
                    flags.append("PETTING")
                if touch.get("any_contact"):
                    flags.append(f"TOUCH({len(touch.get('active_pads', []))})")

                jerk = imu.get("jerk_magnitude", 0)
                still = imu.get("stillness_duration_s", 0)
                squeeze = touch.get("squeeze_intensity", 0)

                status = " | ".join(flags) if flags else "idle"
                print(f"  jerk={jerk:.3f} still={still:.0f}s squeeze={squeeze:.2f} [{status}]")

                # Listen for commands from backend
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=0.01)
                    print(f"  [Backend] {msg}")
                except asyncio.TimeoutError:
                    pass

        except websockets.ConnectionClosed:
            print("  WebSocket disconnected. Reconnecting...")
            continue
        except KeyboardInterrupt:
            break

    ser.close()
    print("\nBridge stopped.")


if __name__ == "__main__":
    asyncio.run(bridge())
