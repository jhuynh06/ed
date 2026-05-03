"""Direct speaker test — sends raw PCM with NO pacing. Ring buffer handles smoothing."""
import math, struct, time, sys, serial

PORT = sys.argv[1] if len(sys.argv) > 1 else "COM12"
BAUD = 921600
RATE = 16000
DURATION = 3
VOLUME = 30000

print(f"Sending {DURATION}s 440Hz sine to {PORT} (burst, no pacing)...")
ser = serial.Serial(PORT, BAUD, timeout=1, dsrdtr=False, rtscts=False)
ser.dtr = False
ser.rts = False
time.sleep(1)
ser.reset_input_buffer()

for _ in range(10):
    line = ser.readline().decode(errors="replace").strip()
    if line:
        print(f"  ESP32: {line}")
    if "SPEAKER_READY" in line:
        break

# Generate ALL samples upfront
total = RATE * DURATION
samples = [int(VOLUME * math.sin(2 * math.pi * 440 * i / RATE)) for i in range(total)]
pcm = struct.pack(f"<{total}h", *samples)
print(f"  Generated {len(pcm)} bytes ({DURATION}s)")

# Send in 1024-byte chunks with just ser.write (no sleep, serial baud rate is the throttle)
for i in range(0, len(pcm), 1024):
    ser.write(pcm[i:i+1024])
ser.flush()

print(f"  All data sent. Waiting for playback...")
time.sleep(DURATION + 1)
print("Done")
ser.close()
