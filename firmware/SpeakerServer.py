"""
SpeakerServer.py — Streams a WAV file to the ESP32 speaker over WiFi.

Usage:
    python SpeakerServer.py <path_to_wav_file>

The ESP32 connects to this server and plays the audio in real-time.
No file size limit — streams directly from disk.
"""

import socket
import struct
import sys
import os
import time

PORT = 8081


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


def read_wav_header(f):
    """Read and parse WAV header, return audio params and data offset."""
    riff = f.read(4)
    if riff != b'RIFF':
        raise ValueError("Not a valid WAV file")
    f.read(4)  # file size
    wave = f.read(4)
    if wave != b'WAVE':
        raise ValueError("Not a valid WAV file")

    sample_rate = 0
    bits_per_sample = 0
    num_channels = 0
    data_size = 0

    while True:
        chunk_id = f.read(4)
        if len(chunk_id) < 4:
            break
        chunk_size = struct.unpack('<I', f.read(4))[0]

        if chunk_id == b'fmt ':
            audio_format = struct.unpack('<H', f.read(2))[0]
            num_channels = struct.unpack('<H', f.read(2))[0]
            sample_rate = struct.unpack('<I', f.read(4))[0]
            f.read(4)  # byte rate
            f.read(2)  # block align
            bits_per_sample = struct.unpack('<H', f.read(2))[0]
            # Skip any extra fmt bytes
            remaining = chunk_size - 16
            if remaining > 0:
                f.read(remaining)
        elif chunk_id == b'data':
            data_size = chunk_size
            break
        else:
            f.read(chunk_size)

    return sample_rate, bits_per_sample, num_channels, data_size


def stream_wav(conn, filepath):
    """Stream WAV file over TCP to the ESP32."""
    with open(filepath, 'rb') as f:
        sample_rate, bits_per_sample, num_channels, data_size = read_wav_header(f)

        print(f"  WAV: {sample_rate} Hz, {bits_per_sample}-bit, {num_channels} ch, "
              f"{data_size / 1024:.1f} KB")

        # Send audio parameters as a simple header (12 bytes)
        header = struct.pack('<III', sample_rate, bits_per_sample, num_channels)
        conn.sendall(header)

        # Send data size (4 bytes)
        conn.sendall(struct.pack('<I', data_size))

        # Stream audio data in chunks
        chunk_size = 1024
        bytes_sent = 0

        while bytes_sent < data_size:
            to_read = min(chunk_size, data_size - bytes_sent)
            data = f.read(to_read)
            if not data:
                break
            try:
                conn.sendall(data)
                bytes_sent += len(data)
            except (BrokenPipeError, ConnectionResetError):
                print("  Client disconnected")
                return

        print(f"  Streamed {bytes_sent / 1024:.1f} KB")


def main():
    if len(sys.argv) < 2:
        print("Usage: python SpeakerServer.py <path_to_wav_file>")
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        sys.exit(1)

    ip = get_local_ip()
    print(f"=== Speaker Stream Server ===")
    print(f"")
    print(f"  Streaming: {filepath}")
    print(f"  Listening on: {ip}:{PORT}")
    print(f"")
    print(f"  Put this in your ESP32 code:")
    print(f'  const char* SERVER_IP = "{ip}";')
    print(f'  const uint16_t SERVER_PORT = {PORT};')
    print(f"")
    print(f"  Waiting for ESP32 to connect...")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", PORT))
    server.listen(1)

    try:
        while True:
            conn, addr = server.accept()
            print(f"\n  ESP32 connected from {addr[0]}")
            stream_wav(conn, filepath)
            conn.close()
            print("  Done. Waiting for next connection...")
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.close()


if __name__ == "__main__":
    main()
