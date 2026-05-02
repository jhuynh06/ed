# Design: Synthetic Evaluation Harness

## Architecture Overview

```
┌─────────────────────────┐
│   Scenario Generator    │  ← Claude Sonnet (one-time generation)
│   (synthetic profiles   │
│    + sensor streams)    │
└───────────┬─────────────┘
            │ generates
            ▼
┌─────────────────────────┐
│   Scenario Library      │  ← JSON files in backend/eval/scenarios/
│   5+ pre-built scenarios│
└───────────┬─────────────┘
            │ feeds
            ▼
┌─────────────────────────┐
│   Scenario Runner       │  ← replays sensor_data into pipeline
│   (mock WebSocket)      │
└───────────┬─────────────┘
            │ produces
            ▼
┌─────────────────────────┐
│   Intervention Log      │  ← actions taken by Ed
└───────────┬─────────────┘
            │ evaluated by
            ▼
┌─────────────────────────┐
│   Evaluator Agent       │  ← Claude Sonnet
│   scores: appropriate,  │
│   timely, personalized  │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Results Table         │  ← summary for demo display
└─────────────────────────┘
```

## Synthetic User Profile

```python
class SyntheticProfile(BaseModel):
    name: str
    age: int
    dementia_stage: Literal["mild", "moderate"]
    family_members: list[dict]       # {name, relationship, voice_clip_id}
    known_triggers: list[str]        # "loud noises", "unfamiliar visitors"
    calming_preferences: list[str]   # "Beatles music", "grandson's voice"
    baseline_hr: int
    typical_agitation_times: list[str]  # "4pm-6pm"
    personality_notes: str           # "former teacher, loves gardening"
```

## Scenario Format

```python
class SyntheticScenario(BaseModel):
    id: str
    name: str                        # "Sundowning Episode at 4:30pm"
    profile: SyntheticProfile
    description: str                 # what happens in this scenario
    duration_seconds: int
    sensor_stream: list[SensorFrame] # time-ordered sensor data
    expected_risk_level: str         # what risk level should be detected
    expected_intervention_type: str  # "full_intervention", "gentle", "none"

class SensorFrame(BaseModel):
    offset_ms: int                   # milliseconds from scenario start
    sensor_data: dict                # matches ESP32 WebSocket format exactly
    audio_chunk: bytes | None        # optional simulated audio
    speech_text: str | None          # pre-transcribed (skip Whisper in eval)
    vocal_emotion: dict | None       # pre-extracted (skip wav2vec2 in eval)
```

## Pre-Built Scenarios

| # | Name | Profile | Duration | Expected |
|---|------|---------|----------|----------|
| 1 | Calm Baseline | Margaret, 78, mild | 5 min | low risk, no intervention |
| 2 | Gradual Sundowning | Margaret, 78, mild | 8 min | escalating to high, full intervention |
| 3 | Sudden Fall | George, 82, moderate | 30 sec | immediate high, urgent notification |
| 4 | Verbal Distress | Margaret, 78, mild | 3 min | medium→high, speech + notification |
| 5 | Comfort Recipe Hit | Margaret, 78, mild | 5 min | medium, recipe-based intervention |

## Evaluator Prompt

```
You are evaluating an AI companion's response to an elderly care scenario.

Scenario: {scenario.description}
User Profile: {scenario.profile}
Expected: {scenario.expected_intervention_type}

Ed's actions: {intervention_log}

Score each dimension 0-10:

1. APPROPRIATENESS: Were the actions suitable for this user's condition and preferences?
   - 0 = harmful or irrelevant, 5 = generic but safe, 10 = perfectly tailored

2. TIMELINESS: Did Ed respond at the right time?
   - 0 = dangerously late, 5 = acceptable delay, 10 = optimal timing

3. PERSONALIZATION: Did Ed use knowledge of this specific user?
   - 0 = completely generic, 5 = some personalization, 10 = deeply personalized

Respond as JSON: {"appropriateness": N, "timeliness": N, "personalization": N, "reasoning": "..."}
```

## Scenario Runner

```python
async def run_scenario(scenario: SyntheticScenario, graph) -> EvalResult:
    intervention_log = []

    # Mock the executor to capture actions instead of sending to ESP32
    async def mock_executor(state):
        intervention_log.append({
            "timestamp": state["observation"].timestamp,
            "actions": state["planned_actions"],
            "notification": state.get("notification"),
        })
        return state

    # Replay sensor frames with timing
    for frame in scenario.sensor_stream:
        state = {"raw_sensor": frame.sensor_data}
        if frame.speech_text:
            state["pre_transcribed"] = frame.speech_text
        if frame.vocal_emotion:
            state["pre_emotion"] = frame.vocal_emotion

        result = await graph.ainvoke(state)

    # Evaluate
    scores = await evaluate(scenario, intervention_log)
    return EvalResult(scenario_id=scenario.id, scores=scores, log=intervention_log)
```

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Pre-generate scenarios, don't generate live | Reproducibility | Same scenarios every run = comparable scores |
| Skip Whisper/wav2vec2 in eval | Pre-transcribed text + emotion | Faster, deterministic, tests pipeline logic not ML APIs |
| 5 scenarios minimum | Cover key paths | Calm, gradual, sudden, verbal, recipe — covers all risk levels |
| Evaluator uses Sonnet | Needs reasoning quality | Scoring intervention quality requires nuanced judgment |

## Dependencies
- Agent pipeline (graph to invoke)
- Memory system (for recipe matching scenario)
- Anthropic SDK (Sonnet for evaluation)
