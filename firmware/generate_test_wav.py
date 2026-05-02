"""Generate a short test melody WAV file for the ESP32 speaker."""
import struct
import math

SAMPLE_RATE = 16000
BITS_PER_SAMPLE = 16
NUM_CHANNELS = 1

# Simple melody: C4, E4, G4, C5 (quarter notes)
notes = [
    (262, 0.4),  # C4
    (330, 0.4),  # E4
    (392, 0.4),  # G4
    (523, 0.4),  # C5
    (392, 0.4),  # G4
    (330, 0.4),  # E4
    (262, 0.8),  # C4 (held longer)
]

def generate_samples():
    samples = []
    for freq, duration in notes:
        num_samples = int(SAMPLE_RATE * duration)
        for i in range(num_samples):
            # Sine wave with fade in/out to avoid clicks
            t = i / SAMPLE_RATE
            envelope = 1.0
            fade = int(SAMPLE_RATE * 0.02)  # 20ms fade
            if i < fade:
                envelope = i / fade
            elif i > num_samples - fade:
                envelope = (num_samples - i) / fade
            sample = math.sin(2 * math.pi * freq * t) * 0.8 * envelope
            samples.append(int(sample * 32767))
    return samples

def write_wav(filename, samples):
    data_size = len(samples) * NUM_CHANNELS * (BITS_PER_SAMPLE // 8)
    file_size = 36 + data_size

    with open(filename, 'wb') as f:
        # RIFF header
        f.write(b'RIFF')
        f.write(struct.pack('<I', file_size))
        f.write(b'WAVE')
        # fmt chunk
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))  # chunk size
        f.write(struct.pack('<H', 1))   # PCM format
        f.write(struct.pack('<H', NUM_CHANNELS))
        f.write(struct.pack('<I', SAMPLE_RATE))
        f.write(struct.pack('<I', SAMPLE_RATE * NUM_CHANNELS * BITS_PER_SAMPLE // 8))
        f.write(struct.pack('<H', NUM_CHANNELS * BITS_PER_SAMPLE // 8))
        f.write(struct.pack('<H', BITS_PER_SAMPLE))
        # data chunk
        f.write(b'data')
        f.write(struct.pack('<I', data_size))
        for sample in samples:
            f.write(struct.pack('<h', sample))

samples = generate_samples()
write_wav('Speaker/data/sound.wav', samples)
print(f"Generated test melody: {len(samples)/SAMPLE_RATE:.1f}s, {SAMPLE_RATE}Hz, 16-bit mono")
print(f"File size: ~{len(samples)*2//1024} KB")
