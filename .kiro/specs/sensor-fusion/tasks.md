# Tasks: Sensor Fusion & IoT-LLM Perception

## Implementation Order

### Phase 1: Data Models & Buffer
- [ ] Define Pydantic models: `IMUFeatures`, `HRState`, `TouchState`, `VocalEmotion`, `SensorSnapshot`, `FusedObservation` | `backend/app/models/sensor.py`
- [ ] Implement `SensorBuffer` ring buffer (5s window per channel, thread-safe) | `backend/app/agents/sensor_buffer.py`
- [ ] Parse incoming `sensor_data` WebSocket JSON into buffer | `backend/app/main.py`

### Phase 2: Feature Extractors
- [ ] `compute_imu_features(window) → IMUFeatures` — jerk, hug, fall, tremor, rocking, stillness | `backend/app/agents/features/imu.py`
- [ ] [P] `HRTracker` class — rolling baseline, elevation %, variability | `backend/app/agents/features/hr.py`
- [ ] [P] `decode_touch(pads) → TouchState` — squeeze, petting, grip | `backend/app/agents/features/touch.py`

### Phase 3: Audio Pipeline
- [ ] Silero VAD integration — gate audio chunks, only forward speech segments | `backend/app/agents/features/vad.py`
- [ ] Groq Whisper transcription — async call, return text | `backend/app/agents/features/transcribe.py`
- [ ] [P] wav2vec2 emotion extraction — async call, return VocalEmotion | `backend/app/agents/features/vocal_emotion.py`

### Phase 4: Fusion
- [ ] `build_snapshot()` — merge all feature outputs into `SensorSnapshot` | `backend/app/agents/perception.py`
- [ ] IoT-LLM translator — Haiku call to convert snapshot to semantic string | `backend/app/agents/perception.py`
- [ ] `compute_agitation_score(snapshot) → float` — weighted formula, deterministic | `backend/app/agents/perception.py`
- [ ] Assemble `FusedObservation` with risk_level classification | `backend/app/agents/perception.py`

### Phase 5: Integration
- [ ] Wire perception as first LangGraph node, output to state | `backend/app/agents/graph.py`
- [ ] Emit `agitation_update` SSE event to dashboard on each observation | `backend/app/sse.py`

## Verification
- [ ] Synthetic calm sensor data → agitation score < 30, risk "low"
- [ ] Synthetic agitation data → score 60-80, risk "medium" or "high"
- [ ] Fall detection (freefall + impact) → immediate risk "high"
- [ ] Invalid HR (valid=false) → excluded from score, noted in semantic text
- [ ] Audio with speech → transcription appears in observation
- [ ] Audio without speech → no transcription, no error
