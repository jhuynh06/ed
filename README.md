# 🧸 Ed — Emotionally Intelligent Companion Bear

> A plush teddy bear that senses when grandma is upset and does something about it. No cameras. No wearables. Just a bear on the couch.

**Built by [Jason Huynh](https://github.com/jasonhuynh), [Tristan Au](https://github.com/tristanau), and [Vincent Wu Zhang](https://github.com/vincentwuzhang)**

---

## The Problem

6.7 million Americans have Alzheimer's. Sundowning — that late-afternoon agitation spike — hits up to 66% of them. If you're an adult child living two hours away, you have no idea what's happening between visits. Cameras feel invasive. Wearables get ripped off. You're left guessing.

## What Ed Does

Ed is a teddy bear with sensors inside. Accelerometer, capacitive touch pads, a microphone, a heart rate sensor, and a speaker. He sits on the couch and pays attention.

When Ed detects distress — restlessness, gripping, whimpering, elevated heart rate — he responds. Maybe he plays a recording of the grandson's voice. Maybe he starts a guided breathing pattern through a haptic motor. Maybe he just says "I'm right here with you" in a warm voice.

Then he tells the family what happened. Not a data dump — a story. "Margaret had a restless moment this afternoon. Ed played Jake's voice and she calmed down in a few minutes. No action needed."

Before that message reaches anyone, three AI critics review it: Is it medically appropriate? Will it scare the daughter? Does it share too much? If any critic objects, the message gets rewritten. The full debate is logged.

Everything shows up on a real-time dashboard. Agitation patterns over time. Episode history. Circadian heatmaps. A daily digest that reads like a note from a caregiver, not a spreadsheet.

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                        Ed (Plush Bear)                          │
│  ESP32-S3 × 3                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │ Sensors  │  │   Mic    │  │ Speaker  │                       │
│  │ IMU+Touch│  │ INMP441  │  │ MAX98357A│                       │
│  │ MPU6050  │  │ 16kHz PCM│  │ I2S DAC  │                       │
│  │ MPR121   │  │ Silero   │  │ Cartesia │                       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                      │
│       │ Serial       │ Serial      │ Serial                     │
└───────┼──────────────┼─────────────┼────────────────────────────┘
        │              │             │
   SensorBridge   AudioBridge   SpeakerBridge
        │              │             │
        └──────────────┼─────────────┘
                       │ WebSocket
              ┌────────▼────────┐
              │  FastAPI Backend │
              │                  │
              │  LangGraph Agent │
              │  ┌──────────────┐│
              │  │ Perception   ││  IoT-LLM translation
              │  │ Risk         ││  Agitation scoring
              │  │ Memory       ││  What worked before
              │  │ Planner      ││  What to do now
              │  │ Executor     ││  TTS + safety gate
              │  └──────────────┘│
              │                  │
              │  Chroma (RAG)    │
              │  SQLite (events) │
              └────────┬─────────┘
                       │ SSE
              ┌────────▼────────┐
              │  Next.js 15     │
              │  Dashboard      │
              └──────────────────┘
```

### The Bear

Three ESP32s inside the bear, each with a dedicated Python bridge on the host machine:

| Board | What it does | Bridge |
|-------|-------------|--------|
| Sensors | MPU6050 accelerometer + 8-pad capacitive touch | `SensorBridge.py` — JSON @ 115200 baud |
| Microphone | INMP441 I2S mic → Silero VAD → Whisper → emotion detection | `SerialAudioBridge.py` — raw PCM @ 921600 |
| Speaker | MAX98357A amp, dual-core firmware with ring buffer | `SpeakerSerialBridge.py` — raw PCM @ 921600 |

### The Brain

A LangGraph pipeline that never sees raw sensor numbers (following the [IoT-LLM paper](https://arxiv.org/html/2410.02429)):

1. **Perception** — translates sensor data into plain English ("she's gripping the bear tightly and her heart rate is up")
2. **Risk** — weighted agitation score with a sundowning time-of-day multiplier
3. **Memory** — three tiers: episodic (what happened), semantic (patterns), workflow (comfort recipes that worked before, ranked by Thompson sampling)
4. **Planner** — Claude Sonnet picks an intervention from proven recipes
5. **Executor** — fires TTS through Cartesia, runs the MAR safety gate on notifications

### The Dashboard

Next.js 15 with SSE for real-time updates:
- Agitation timeline (6h, color-coded)
- Episode cards with expandable MAR debate traces
- Live touch sensor visualization on the bear
- Voice & language analysis with CDR cognitive tracking
- Claude-generated daily digest with mood arc
- Family voice clip management
- Circadian heatmap showing weekly patterns

---

## Tech Stack

| Layer | What |
|-------|------|
| Hardware | ESP32-S3, MPU6050, MPR121, INMP441, MAX98357A, MAX30102 |
| Firmware | PlatformIO + Arduino C++ |
| Backend | Python 3.11, FastAPI, LangGraph, aiosqlite |
| AI | Claude Sonnet 4.5 (planner), Claude Haiku 4.5 (perception), Cartesia Sonic (TTS) |
| Audio | Silero VAD, Groq Whisper, wav2vec2 emotion |
| Storage | ChromaDB (vectors), SQLite (events) |
| Dashboard | Next.js 15, React 19, TypeScript, shadcn/ui, Tailwind 4 |

---

## Running It

```bash
# Backend
cd backend
uv sync
.venv/Scripts/python -m uvicorn app.main:app --port 8000

# Dashboard
cd dashboard
pnpm install
pnpm dev

# Seed demo data
cd backend
python seed_demo.py
# Then open http://localhost:8000/mock/seed in browser

# Bridges (one terminal each)
cd firmware
python SensorBridge.py
python SerialAudioBridge.py COM15
python SpeakerSerialBridge.py COM11
```

---

## What's Next

**Docker Compose** — one-command deployment. Backend, dashboard, and ChromaDB in containers. Horizontal scaling for facilities with multiple bears.

**Privacy-preserving computer vision** — thermal camera (MLX90640) for fall detection and sleep monitoring. Depth sensing for room-level activity. On-device pose estimation for gait analysis. No RGB cameras, ever. Privacy is the whole point.

**Clinical integration** — FHIR data export for EHR systems. Longitudinal CDR tracking from speech patterns. Medication adherence correlation. Multi-site clinician dashboard.

**Better sensing** — HRV stress detection, ambient sound classification, sleep quality scoring, multi-bear mesh networking for facility-wide mapping.

**Personalization** — voice cloning via Cartesia so Ed can speak in a family member's voice. Adaptive comfort recipes that learn per patient. Circadian-aware pre-emptive interventions. Multilingual TTS.

---

## License

MIT

---

*Built at KiroHacks 2025*
