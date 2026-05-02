---
title: Theodore — FastAPI & LangGraph Patterns
inclusion: fileMatch
fileMatch: "backend/**"
---

# FastAPI & LangGraph Patterns

## FastAPI Conventions
- Single `app/main.py` creates the FastAPI app with WebSocket and SSE endpoints
- Use `@app.websocket("/ws/bear")` for ESP32 communication
- Use `@app.get("/sse/events")` with `StreamingResponse` for dashboard live updates
- Dependency injection via `Depends()` for Chroma client, SQLite, agent state
- Pydantic models in `app/models/` for all message types
- No ORM — raw SQLite via `aiosqlite` for event logging

## LangGraph Agent Architecture
```
Perception → Risk Assessment → Memory Retrieval → Planner → Executor
```
- Each node is a function that takes `State` and returns updated `State`
- State is a TypedDict with: `sensor_data`, `semantic_observation`, `agitation_score`, `risk_level`, `memories`, `plan`, `actions`
- Perception node uses Haiku (fast, cheap) for IoT-LLM translation
- Planner node uses Sonnet (smart) for intervention decisions
- Conditional edges based on `risk_level`: low → log only, medium → gentle intervention, high → full response + notify

## Claude Tool Definitions
Define tools as Pydantic models with `@tool` decorator:
- `speak(text: str, tone: Literal["warm", "gentle", "reassuring"])` — TTS to bear
- `play_breathing_pattern(bpm: int, duration_seconds: int)` — haptic motor
- `play_family_voice(clip_id: str)` — play stored family recording
- `change_led(color: Literal["green", "amber", "blue"], pattern: Literal["steady", "pulse"])` — nose LED
- `notify_caregiver(message: str, priority: Literal["info", "warning", "urgent"])` — dashboard alert
- `consolidate_pattern(episode_ids: list[str])` — memory curation
- `store_comfort_recipe(trigger: str, actions: list[str], outcome: str)` — workflow memory

## WebSocket Protocol (ESP32 ↔ Backend)
Messages are JSON with `type` field:
- `sensor_data` — ESP32 → backend (every 100ms for IMU, 1s for HR/touch)
- `audio_chunk` — ESP32 → backend (16kHz PCM, 512-sample frames)
- `command` — backend → ESP32 (`speak`, `breathe`, `led`, `play_clip`)
- `status` — bidirectional heartbeat

## FastAPI WebSocket Handler Pattern

```python
@app.websocket("/ws/bear")
async def bear_websocket(ws: WebSocket):
    await ws.accept()
    buffer = SensorBuffer()
    graph = build_theodore_graph()

    try:
        while True:
            data = await ws.receive_json()
            if data["type"] == "sensor_data":
                buffer.push(data)
                if buffer.ready_for_fusion():
                    snapshot = buffer.build_snapshot()
                    result = await graph.ainvoke({"raw_sensor": snapshot})
                    for action in result.get("executed_actions", []):
                        await ws.send_json(action)
            elif data["type"] == "audio_chunk":
                await audio_pipeline.process(base64.b64decode(data["payload"]))
    except WebSocketDisconnect:
        logger.info("Bear disconnected")
```

## SSE Endpoint Pattern

```python
@app.get("/sse/events")
async def sse_events(request: Request):
    async def event_generator():
        queue = event_bus.subscribe()
        try:
            while True:
                if await request.is_disconnected():
                    break
                event = await queue.get()
                yield f"data: {event.model_dump_json()}\n\n"
        finally:
            event_bus.unsubscribe(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```
