# Ed Audio Bridge

This system streams audio from the ESP32 microphone to the Ed backend for real-time speech processing.

## Architecture

```
┌─────────────┐     WiFi/WebSocket     ┌──────────────┐     WebSocket     ┌─────────────┐
│   ESP32     │ ──────────────────────▶│ AudioBridge  │ ─────────────────▶│  Backend    │
│ (Microphone)│    Raw 16-bit PCM      │   (Python)   │   Raw 16-bit PCM  │  (FastAPI)  │
└─────────────┘                        └──────────────┘                    └─────────────┘
                                              │
                                              │ Runs on your laptop
                                              │ (bridges ESP32 to backend)
```

## Components

### 1. ESP32 Firmware (`Microphone/src/main.cpp`)
- Captures audio from INMP441 I2S microphone at 16kHz
- Streams raw 16-bit PCM over WebSocket
- Built-in Voice Activity Detection (VAD) to reduce bandwidth
- Auto-reconnect on connection loss

### 2. Audio Bridge (`AudioBridge.py`)
- Python script that runs on your laptop
- Receives audio from ESP32 over WebSocket (port 8081)
- Forwards audio to backend WebSocket endpoint
- Relays TTS audio from backend back to ESP32

### 3. Backend Endpoint (`/ws/audio`)
- Receives audio stream from AudioBridge
- Processes through audio pipeline:
  - Silero VAD (Voice Activity Detection)
  - Groq Whisper (Speech-to-Text)
  - wav2vec2 (Emotion Recognition)
- Publishes transcription events to dashboard

## Setup

### Prerequisites
- ESP32-WROOM-32 with INMP441 microphone
- Python 3.10+ with `websockets` and `aiohttp`
- Backend running with required ML models

### Step 1: Configure WiFi
Edit `Microphone/src/main.cpp`:
```cpp
const char* WIFI_SSID     = "your-wifi-ssid";
const char* WIFI_PASSWORD = "your-wifi-password";
```

### Step 2: Start the Audio Bridge
```bash
cd firmware
pip install websockets aiohttp
python AudioBridge.py
```

The bridge will print your laptop's IP address. Update the ESP32 firmware:
```cpp
const char* WS_HOST = "192.168.x.x";  // Your laptop's IP
const uint16_t WS_PORT = 8081;
```

### Step 3: Flash the ESP32
```bash
cd Microphone
pio run -t upload
pio device monitor
```

### Step 4: Start the Backend
```bash
cd backend
uvicorn app.main:app --reload
```

## Hardware Wiring (INMP441 → ESP32)

| INMP441 | ESP32 |
|---------|-------|
| VDD     | 3.3V  |
| GND     | GND   |
| WS      | GPIO25|
| SCK     | GPIO26|
| SD      | GPIO33|
| L/R     | GND (left channel) |

## Troubleshooting

### ESP32 won't connect to WiFi
- Check SSID and password
- Ensure your phone hotspot is 2.4GHz (ESP32 doesn't support 5GHz)

### No audio being received
- Check serial monitor for connection status
- Verify the AudioBridge is running and shows "ESP32 connected"
- Check VAD threshold if audio is too quiet

### High latency
- Reduce `CHUNK_SAMPLES` in firmware (trades latency for bandwidth)
- Ensure good WiFi signal strength

### Transcription errors
- Check `GROQ_API_KEY` is set in backend `.env`
- Verify audio quality (RMS levels in serial monitor)

## Configuration

### ESP32 (`main.cpp`)
```cpp
#define CHUNK_SAMPLES  512      // Samples per message (32ms at 16kHz)
#define VAD_THRESHOLD  500      // RMS threshold for voice detection
#define VAD_HOLDOFF_MS 300      // Keep streaming after voice stops
```

### Audio Bridge (`AudioBridge.py`)
```python
ESP32_PORT = 8081               # Port ESP32 connects to
BACKEND_WS_URL = "ws://localhost:8000/ws/audio"
```

## Data Flow

1. **ESP32** captures 512 samples (32ms) of audio
2. **VAD** checks if voice is present (RMS > threshold)
3. If voice detected, sends raw PCM bytes over WebSocket
4. **AudioBridge** receives and forwards to backend
5. **Backend** accumulates frames until speech ends
6. **Whisper** transcribes the speech segment
7. **wav2vec2** classifies emotion
8. Results published to dashboard via SSE
