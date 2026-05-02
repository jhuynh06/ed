# Feature: Sensor Fusion & IoT-LLM Perception

## Status: draft

## Problem Statement
Raw sensor data from ESP32 (IMU, HR, touch, audio) must be fused into a coherent semantic observation that Claude can reason about. Sending raw numbers produces poor LLM reasoning.

## User Stories
- As the planner agent, I want a semantic description of the user's state so that I can make informed intervention decisions
- As a caregiver viewing the dashboard, I want to see a human-readable summary of what Ed is sensing

## Functional Requirements
- REQ-001: When sensor_data arrives via WebSocket, the perception agent shall compute IMU features (jerk, hug, fall, tremor, rocking) within 100ms
- REQ-002: When audio_chunk arrives, the system shall gate through Silero VAD and only transcribe speech segments
- REQ-003: When all sensor channels have fresh data, the perception agent shall produce a semantic observation string using IoT-LLM translation (Haiku)
- REQ-004: While HR sensor reports `valid: false`, the system shall exclude HR from the agitation score and note "HR unavailable" in the observation
- REQ-005: The system shall compute an agitation score (0–100) from weighted sensor fusion per the formula in steering doc 05

## Acceptance Criteria
- [ ] Synthetic sensor data produces a readable semantic observation
- [ ] Agitation score matches expected range for calm/mild/moderate/severe test cases
- [ ] Fall detection triggers immediate high-priority observation
- [ ] Invalid HR gracefully excluded without crashing the pipeline

## Out of Scope
- Custom ML models for emotion detection (use wav2vec2 API)
- On-device (ESP32) feature extraction beyond raw reads
