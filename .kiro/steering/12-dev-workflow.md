---
title: Ed — Development Workflow & Build Order
inclusion: always
---

# Development Workflow

## Build Order (dependency graph)

```
Phase 1 — Foundation (parallel)
├── [firmware] ESP32 sensor reads + WebSocket client
├── [backend]  Pydantic models + FastAPI skeleton + SQLite schema
└── [dashboard] Next.js init + layout + SSE hook

Phase 2 — Perception (backend, depends on Phase 1 models)
└── [backend]  Sensor buffer → feature extractors → IoT-LLM → agitation score

Phase 3 — Memory (backend, depends on Phase 1 schema)
└── [backend]  Chroma collections → episodic store → retrieval → memory tools

Phase 4 — Agent Pipeline (backend, depends on Phase 2 + 3)
└── [backend]  LangGraph graph → risk routing → planner → MAR gate → executor

Phase 5 — Dashboard Features (parallel, depends on Phase 1 + 4 SSE)
├── [dashboard] Agitation timeline + status card
├── [dashboard] Episode list + MAR trace display
├── [dashboard] Vitals charts + circadian heatmap
└── [dashboard] Family voice clips + daily summary

Phase 6 — Integration & Demo (depends on all above)
├── [backend]  Synthetic eval harness
├── [all]      End-to-end test with synthetic scenario
└── [all]      Demo mode pre-seed data + rehearsal
```

## Agent Routing

Kiro auto-selects subagents by task, but here's the explicit routing:

| Task involves... | Use subagent | Why |
|-----------------|-------------|-----|
| `firmware/**` files, PlatformIO, C++, sensors | `/firmware-expert` | Scoped to embedded patterns, no web tools |
| `backend/**` FastAPI, LangGraph, WebSocket, SSE | `/backend-expert` | Full tool access, knows the agent architecture |
| `dashboard/**` React, Next.js, TypeScript, shadcn | `/dashboard-expert` | Knows shadcn/ui, SSE patterns, accessibility |
| Silero VAD, Whisper, wav2vec2, NumPy FFT, audio | `/ml-audio-expert` | Signal processing + ML pipeline specialist |
| Chroma, memory tiers, consolidation, retrieval | `/memory-architect` | Embedding tuning, confidence logic, dual storage |
| Synthetic scenarios, eval scoring, test harness | `/eval-specialist` | Scenario generation, mock infrastructure, scoring |
| Docker, compose, env setup, dependency management | `/devops-agent` | Service orchestration, build config |
| Looking up docs, APIs, datasheets, papers | `/research-agent` | Read + web only, can't accidentally modify code |

## Parallelization Strategy

On hackathon day with Kiro, maximize parallel work:

1. **Start 3 parallel tracks** in Phase 1:
   - "Use firmware-expert to scaffold ESP32 sensor reads and WebSocket client"
   - "Use backend-expert to create all Pydantic models and FastAPI skeleton"
   - "Use dashboard-expert to initialize Next.js project with layout and SSE hook"

2. **Phase 2–3 are backend-only** but can run in parallel with each other:
   - Perception pipeline doesn't depend on memory system
   - Memory system doesn't depend on perception pipeline
   - Both feed into Phase 4

3. **Phase 5 dashboard pages are independent** — can all be built in parallel

## Spec-to-Implementation Mapping

| When building... | Reference spec | Reference steering |
|-----------------|---------------|-------------------|
| Sensor reads + fusion | `sensor-fusion/` | `05-sensor-patterns.md` |
| Memory system | `memory-system/` | `06-memory-architecture.md` |
| Agent pipeline | `agent-pipeline/` | `08-fastapi-langgraph.md`, `07-safety-ethics.md` |
| Dashboard | `caregiver-dashboard/` | `09-nextjs-dashboard.md` |
| Eval harness | `synthetic-eval/` | `11-demo-mode.md` |
| Firmware | (no spec, simpler) | `10-esp32-firmware.md` |

## Time Budget (13 hours)

| Phase | Hours | Priority |
|-------|-------|----------|
| 1. Foundation | 2h | Must have |
| 2. Perception | 2h | Must have |
| 3. Memory | 2h | Must have |
| 4. Agent Pipeline | 3h | Must have |
| 5. Dashboard | 2h | Must have |
| 6. Integration + Demo | 2h | Must have |
| Docker compose | +30min | Time permitting |
| Extra dashboard polish | +1h | Time permitting |
