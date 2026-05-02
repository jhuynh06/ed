---
title: Ed — Sensor Patterns & IoT-LLM Translation
inclusion: always
---

# Sensor Patterns

## IoT-LLM Translation Layer (Paper: arxiv.org/html/2410.02429)
NEVER send raw sensor values to Claude. Always translate to semantic descriptions first.

### Bad (raw numbers)
```
{"ax": 0.3, "ay": -0.1, "az": 0.9, "hr": 92, "spo2": 97, "touch": [1,0,1,0]}
```

### Good (semantic description)
```
"User has been still for 4 minutes. Heart rate elevated 15bpm above baseline.
Gentle holding motion detected in left paw. No speech detected in last 2 minutes."
```

## Sensor Fusion Pipeline
1. **IMU (MPU6050)** → compute jerk magnitude, detect: hug, fall, tremor, rocking, stillness
2. **Heart Rate (MAX30102)** → baseline tracking, elevation %, variability
3. **Touch (MPR121)** → paw squeeze intensity, petting pattern, grip duration
4. **Audio (INMP441)** → Silero VAD gates chunks → Whisper transcription + wav2vec2 emotion
5. **Fused observation** → semantic description string for LLM consumption

## Feature Extraction Rules
- IMU jerk: `sqrt(d²ax + d²ay + d²az)` over 100ms windows
- Hug detection: sustained bilateral pressure (both paws) + elevated accelerometer contact
- Fall detection: freefall (< 0.3g) followed by impact spike (> 3g)
- Tremor: FFT peak in 4–6 Hz band on accelerometer
- Rocking: periodic oscillation in pitch axis, 0.5–2 Hz

## Agitation Score (0–100)
Weighted fusion:
- IMU jerk magnitude: 25%
- HR elevation above baseline: 25%
- Vocal emotion (distress/anger/fear): 30%
- Touch absence (no contact in N minutes): 20%

Thresholds: < 30 calm, 30–60 mild, 60–80 moderate, > 80 severe

```python
def compute_agitation_score(snapshot: SensorSnapshot) -> float:
    imu_score = min(snapshot.imu.jerk_magnitude / 2.0, 1.0) * 100
    hr_score = min(abs(snapshot.hr.elevation_pct) / 30.0, 1.0) * 100 if snapshot.hr.valid else 0
    vocal_score = (snapshot.vocal_emotion.arousal * 100) if snapshot.vocal_emotion else 0
    touch_score = min(snapshot.touch.grip_duration_s / 300.0, 1.0) * 100 if not snapshot.touch.any_contact else 0

    weights = {"imu": 0.25, "hr": 0.25, "vocal": 0.30, "touch": 0.20}
    if not snapshot.hr.valid:
        weights = {"imu": 0.30, "hr": 0.0, "vocal": 0.40, "touch": 0.30}

    return (
        weights["imu"] * imu_score +
        weights["hr"] * hr_score +
        weights["vocal"] * vocal_score +
        weights["touch"] * touch_score
    )
```

## IoT-LLM Translation Example

Input snapshot:
```json
{"imu": {"jerk": 0.1, "stillness_s": 240}, "hr": {"bpm": 92, "baseline": 72, "elevation_pct": 27.8}, "touch": {"any_contact": true, "squeeze_intensity": 0.6}, "speech": null, "vocal_emotion": null}
```

Output semantic text:
```
"Margaret has been sitting still for 4 minutes while holding Ed's paw with moderate pressure. Her heart rate is noticeably elevated at 92 bpm, about 28% above her usual baseline of 72. She hasn't spoken recently. The combination of stillness, elevated heart rate, and paw-gripping suggests growing internal anxiety."
```
