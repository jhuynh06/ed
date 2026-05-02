# Design: LangGraph Agent Pipeline

## Architecture Overview

```
                         ┌──────────────┐
                         │  WebSocket   │
                         │  sensor_data │
                         └──────┬───────┘
                                ▼
                    ┌───────────────────────┐
                    │   PERCEPTION NODE     │  ← Haiku
                    │  IoT-LLM translation  │
                    │  agitation scoring    │
                    └───────────┬───────────┘
                                ▼
                    ┌───────────────────────┐
                    │  RISK ASSESSMENT NODE │  ← deterministic
                    │  classify: low/med/hi │
                    └───────────┬───────────┘
                                │
                 ┌──────────────┼──────────────┐
                 ▼              ▼              ▼
              low           medium          high
                │              │              │
                ▼              ▼              ▼
            log_only    ┌─────────────┐  ┌─────────────┐
                        │  MEMORY     │  │  MEMORY     │
                        │  RETRIEVAL  │  │  RETRIEVAL  │
                        └──────┬──────┘  └──────┬──────┘
                               ▼                ▼
                        ┌─────────────┐  ┌─────────────┐
                        │  PLANNER    │  │  PLANNER    │  ← Sonnet
                        │  (gentle)   │  │  (full +    │
                        │             │  │   notify)   │
                        └──────┬──────┘  └──────┬──────┘
                               ▼                │
                               │         ┌──────▼──────┐
                               │         │  MAR GATE   │
                               │         │ 3 critics   │
                               │         └──────┬──────┘
                               ▼                ▼
                        ┌─────────────────────────────┐
                        │        EXECUTOR NODE        │
                        │  dispatch actions → ESP32   │
                        │  store episode → memory     │
                        │  emit SSE → dashboard       │
                        └─────────────────────────────┘
```

## LangGraph State

```python
class TheodoreState(TypedDict):
    # Input
    raw_sensor: dict                    # latest sensor_data JSON
    audio_buffer: list[bytes]           # VAD-gated audio chunks

    # Perception output
    observation: FusedObservation | None
    semantic_text: str

    # Risk
    risk_level: Literal["low", "medium", "high"]
    agitation_score: float

    # Memory
    relevant_memories: list[dict]
    matched_recipe: ComfortRecipe | None

    # Planning
    planned_actions: list[dict]         # tool call specs
    notification: dict | None           # if caregiver notification needed

    # MAR
    mar_debate: list[dict] | None       # critic responses
    notification_approved: bool

    # Execution
    executed_actions: list[str]
    episode_id: str | None
```

## Node Implementations

### Perception Node (Haiku)
- Calls sensor fusion pipeline from sensor-fusion spec
- Sets `observation`, `semantic_text`, `agitation_score`, `risk_level`

### Risk Assessment Node (deterministic)
```python
def assess_risk(state: TheodoreState) -> dict:
    score = state["agitation_score"]
    if state["observation"].features.imu.fall_detected:
        return {"risk_level": "high"}
    if score < 30:
        return {"risk_level": "low"}
    if score < 60:
        return {"risk_level": "medium"}
    return {"risk_level": "high"}
```

### Memory Retrieval Node
- Query episodic + semantic memories relevant to current observation
- Check for matching comfort recipe
- Sets `relevant_memories`, `matched_recipe`

### Planner Node (Sonnet)
System prompt includes:
- Current observation (semantic text)
- Retrieved memories
- Matched comfort recipe (if any)
- Available tools list
- Risk level context

If `matched_recipe` exists and `success_rate > 0.7`, prefer the recipe's action sequence.

### MAR Gate (3 critics, Haiku each)
Only runs when `notification` is present in state.

```python
CRITICS = [
    {
        "name": "Clinical Safety Critic",
        "prompt": "You are a clinical safety reviewer. Evaluate this caregiver notification: {notification}. Is it medically appropriate? Could delay cause harm? Could it cause unnecessary medical anxiety? Respond with APPROVE or REVISE with specific feedback."
    },
    {
        "name": "Family Tone Critic",
        "prompt": "You are a family communication specialist. Evaluate this notification: {notification}. Will it scare the family member unnecessarily? Is the language warm but clear? Respond with APPROVE or REVISE with specific feedback."
    },
    {
        "name": "Privacy Critic",
        "prompt": "You are a privacy advocate. Evaluate this notification: {notification}. Does it share more information than necessary? Could it be more concise while remaining useful? Respond with APPROVE or REVISE with specific feedback."
    }
]
```

All three critics run in parallel. If any says REVISE, the planner rewrites the notification incorporating feedback. Max 2 revision rounds.

### Executor Node
- Dispatches each action as a WebSocket command to ESP32
- Stores the episode in memory system
- Emits SSE events to dashboard
- If notification approved, sends to dashboard notification stream

## Conditional Edges

```python
def route_by_risk(state: TheodoreState) -> str:
    if state["risk_level"] == "low":
        return "log_only"
    return "memory_retrieval"

def route_notification(state: TheodoreState) -> str:
    if state.get("notification"):
        return "mar_gate"
    return "executor"

graph = StateGraph(TheodoreState)
graph.add_node("perception", perception_node)
graph.add_node("risk_assessment", assess_risk)
graph.add_node("memory_retrieval", memory_retrieval_node)
graph.add_node("planner", planner_node)
graph.add_node("mar_gate", mar_gate_node)
graph.add_node("executor", executor_node)
graph.add_node("log_only", log_only_node)

graph.add_edge("perception", "risk_assessment")
graph.add_conditional_edges("risk_assessment", route_by_risk,
    {"low": "log_only", "memory_retrieval": "memory_retrieval"})
graph.add_edge("memory_retrieval", "planner")
graph.add_conditional_edges("planner", route_notification,
    {"mar_gate": "mar_gate", "executor": "executor"})
graph.add_edge("mar_gate", "executor")
graph.add_edge("log_only", END)
graph.add_edge("executor", END)

graph.set_entry_point("perception")
```

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Haiku for perception, Sonnet for planning | Cost/latency vs. reasoning quality | Perception runs every 2s (cheap+fast), planning runs per-episode (needs quality) |
| MAR only on notifications | Not on every action | Most actions are low-stakes (LED, speech). Notifications reach humans — higher bar. |
| Max 2 MAR revision rounds | Prevent infinite loops | Diminishing returns after 2 rounds |
| Fall detection bypasses risk scoring | Immediate high priority | Falls are time-critical, can't wait for agitation score |
| Recipe preference when success > 0.7 | Proven sequences over novel plans | Reduces hallucination risk, faster response |

## Dependencies
- sensor-fusion spec (provides FusedObservation)
- memory-system spec (provides retrieval + tools)
- LangGraph library
- Anthropic SDK (Sonnet + Haiku)
