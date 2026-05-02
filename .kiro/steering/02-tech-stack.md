---
title: Ed — Tech Stack
inclusion: always
---

# Tech Stack

## Hardware (in-bear)
- ESP32-S3-DevKitC-1 — main compute, WiFi, dual I²S
- INMP441 I²S microphone — voice and ambient audio
- MPU6050 IMU — accelerometer + gyroscope (hugs, falls, tremor)
- MAX30102 pulse oximeter — heart rate + SpO2 (paw-mounted)
- MPR121 capacitive touch — paw squeezes and petting
- MAX98357A I²S amp + 3W 4Ω speaker — voice output
- 10mm coin vibration motor — haptic breathing pacer
- 5mm common-anode RGB LED — emotional state indicator (behind nose)
- 5V 2A USB power bank

## Firmware
- PlatformIO + Arduino framework (C++)
- ArduinoWebsockets for backend comms
- ArduinoJson for message serialization
- Adafruit/SparkFun sensor libraries (MPU6050, MAX3010x, MPR121)

## Backend (Python 3.11)
- FastAPI — async WebSocket server
- LangGraph — multi-agent orchestration
- Claude Sonnet 4.5 — planner agent
- Claude Haiku 4.5 — high-frequency perception loops
- Anthropic SDK + Pydantic — structured tool outputs
- Silero VAD — voice activity detection
- Groq Whisper — speech transcription
- wav2vec2 — vocal emotion extraction
- NumPy — IMU feature computation
- Cartesia or ElevenLabs — TTS streaming

## Storage
- Chroma — vector DB for RAG memory + family voice library
- SQLite — event logging and episode storage
- LangSmith — agent trace observability

## Dashboard (Next.js 15)
- React 19 + TypeScript
- shadcn/ui — component library
- Tremor or Recharts — data visualizations
- Server-Sent Events — live updates from backend
- Tailwind CSS 4

## Dev Tools
- pnpm — package manager (dashboard)
- uv — Python package manager (backend)
- PlatformIO CLI — firmware builds
- Docker Compose — optional deployment (time permitting)
