# Design: Sensor Fusion & IoT-LLM Perception

## Architecture Overview

```
ESP32 WebSocket ──→ FastAPI /ws/bear
                         │
                    SensorBuffer (ring buffer, last 5s per channel)
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
         IMU Features  HR Tracker  Touch Decoder
         (NumPy)       (baseline)  (pattern match)
              │          │          │
              └──────────┼──────────┘
                         ▼
                  Audio Pipeline
                  (Silero VAD → Whisper → wav2vec2)
                         │
                         ▼
              ┌─────────────────────┐
              │  IoT-LLM Translator │  ← Claude Haiku
              │  (semantic string)  │
              └─────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  Agitation Scorer   │  ← deterministic, no LLM
              │  (weighted fusion)  │
              └─────────────────────┘
                         │
                         ▼
              FusedObservation(semantic_text, agitation_score, features_dict)
```

## Data Flow

1. ESP32 sends `sensor_data` JSON every 100ms (IMU) / 1s (HR, touch)
2. `SensorBuffer` accumulates into sliding windows
3. Feature extractors run in parallel on each channel:
   - `imu_features(window) → IMUFeatures(jerk, hug, fall, tremor, rocking, stillness_duration)`
   - `hr_tracker.update(bpm, spo2) → HRState(current, baseline, elevation_pct, variability)`
   - `touch_decoder(pads) → TouchState(squeeze_intensity, petting, grip_duration)`
4. Audio pipeline runs asynchronously on VAD-gated chunks:
   - `transcribe(chunk) → text`
   - `extract_emotion(chunk) → VocalEmotion(valence, arousal, dominant_emotion)`
5. All features merge into `SensorSnapshot` dataclass
6. IoT-LLM translator (Haiku) converts `SensorSnapshot` → semantic string
7. Agitation scorer computes weighted score from numeric features (no LLM needed)
8. Output: `FusedObservation` enters LangGraph state

## Data Models

```python
class IMUFeatures(BaseModel):
    jerk_magnitude: float          # sqrt(d²ax + d²ay + d²az)
    hug_detected: bool
    fall_detected: bool
    tremor_power: float            # FFT 4-6Hz band energy
    rocking_detected: bool
    stillness_duration_s: float

class HRState(BaseModel):
    bpm: int
    spo2: int
    valid: bool
    baseline_bpm: float
    elevation_pct: float           # (current - baseline) / baseline * 100
    variability: float             # RMSSD over last 60s

class TouchState(BaseModel):
    any_contact: bool
    squeeze_intensity: float       # 0-1 normalized
    petting_detected: bool
    grip_duration_s: float
    active_pads: list[int]

class VocalEmotion(BaseModel):
    valence: float                 # -1 to 1
    arousal: float                 # 0 to 1
    dominant_emotion: str          # calm, sad, angry, fearful, neutral

class SensorSnapshot(BaseModel):
    timestamp: float
    imu: IMUFeatures
    hr: HRState
    touch: TouchState
    speech_text: str | None
    vocal_emotion: VocalEmotion | None

class FusedObservation(BaseModel):
    timestamp: float
    semantic_text: str             # IoT-LLM translated description
    agitation_score: float         # 0-100
    features: SensorSnapshot
    risk_level: str                # low, medium, high
```

## IoT-LLM Translation Prompt (Haiku)

```
You are a sensor interpreter for an elderly care companion.
Given these sensor readings, produce a 2-3 sentence natural language
description of what the user is currently experiencing.
Focus on: physical state, emotional indicators, and any concerning patterns.
Do NOT include raw numbers. Speak as if describing to a caregiver.

Sensor data:
{sensor_snapshot_json}
```

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agitation score is deterministic | Weighted formula, no LLM | Reproducible, fast, debuggable |
| IoT-LLM uses Haiku not Sonnet | Cost + latency on high-frequency path | Runs every ~2s, needs to be cheap |
| Audio pipeline is async | Separate from sensor loop | Transcription takes 200-500ms, can't block IMU |
| Baseline HR is rolling 1-hour average | Simple, no calibration needed | Good enough for demo, avoids cold-start |

## Dependencies
- NumPy for IMU feature extraction
- Silero VAD model (torch, loaded once at startup)
- Groq Whisper API key
- Anthropic API key (Haiku)
