"""
SensorBridge.py — Reads JSON from ESP32 serial and forwards to Ed backend via WebSocket.
"""

import asyncio
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import serial
import websockets

COM_PORT = "COM13"
BAUD_RATE = 115200
WS_URL = "ws://localhost:8000/ws/bear"

executor = ThreadPoolExecutor(max_workers=1)


def read_serial_line(ser):
    """Blocking serial read — runs in thread pool."""
    return ser.readline().decode("utf-8", errors="ignore").strip()


async def bridge():
    print(f"=== Ed Sensor Bridge ===")
    print(f"  Serial: {COM_PORT} @ {BAUD_RATE}")
    print(f"  Backend: {WS_URL}")
    print()

    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=0.5)
    except serial.SerialException as e:
        print(f"  ERROR: Could not open {COM_PORT}: {e}")
        from serial.tools.list_ports import comports
        for p in comports():
            print(f"    {p.device} — {p.description}")
        sys.exit(1)

    time.sleep(0.3)
    ser.reset_input_buffer()
    print("  Serial ready.")

    loop = asyncio.get_event_loop()

    while True:
        try:
            print("  Connecting to backend...")
            ws = await websockets.connect(WS_URL)
            print("  WebSocket connected. Bridging data...\n")

            while True:
                # Non-blocking serial read via thread pool
                line = await loop.run_in_executor(executor, read_serial_line, ser)
                if not line:
                    continue

                if not (line.startswith("{") and line.endswith("}")):
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if data.get("type") != "sensor_data":
                    continue

                await ws.send(line)

                imu = data.get("imu", {})
                pads = data.get("touch", {}).get("pads", [])
                status = f"pads={pads}" if pads else "idle"
                print(f"  ax={imu.get('ax',0):.3f} ay={imu.get('ay',0):.3f} az={imu.get('az',0):.3f} [{status}]")

        except (websockets.ConnectionClosed, ConnectionRefusedError, OSError) as e:
            print(f"  WebSocket error: {e}. Reconnecting in 2s...")
            await asyncio.sleep(2)
        except KeyboardInterrupt:
            break

    ser.close()
    print("\nBridge stopped.")


if __name__ == "__main__":
    asyncio.run(bridge())
