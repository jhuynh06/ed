"""
wav_server.py — Receives WAV audio from ESP32 over WiFi and saves to disk.

Usage:
    python wav_server.py

Then put the printed IP address into the ESP32 code's serverUrl.
Press 'r' in the ESP32 serial monitor to record and send.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
import datetime
import os

PORT = 8080
SAVE_DIR = "recordings"

os.makedirs(SAVE_DIR, exist_ok=True)


class WavHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        # Save with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(SAVE_DIR, f"recording_{timestamp}.wav")

        with open(filename, "wb") as f:
            f.write(body)

        print(f"\n  Received {len(body):,} bytes -> {filename}")

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(f"Saved {filename}".encode())

    def log_message(self, format, *args):
        pass  # Suppress default logging


def get_local_ip():
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


def main():
    ip = get_local_ip()
    print(f"=== WAV Receiver Server ===")
    print(f"")
    print(f"  Listening on: http://{ip}:{PORT}/upload")
    print(f"  Saving to:    ./{SAVE_DIR}/")
    print(f"")
    print(f"  Put this in your ESP32 code:")
    print(f'  String serverUrl = "http://{ip}:{PORT}/upload";')
    print(f"")
    print(f"  Waiting for recordings...")

    server = HTTPServer(("0.0.0.0", PORT), WavHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()