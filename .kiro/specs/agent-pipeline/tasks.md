# Tasks: LangGraph Agent Pipeline

## Implementation Order

### Phase 1: State & Graph Skeleton
- [ ] Define `EdState` TypedDict with all fields | `backend/app/agents/state.py`
- [ ] Create LangGraph `StateGraph` with all nodes as stubs (pass-through) | `backend/app/agents/graph.py`
- [ ] Add conditional edges for risk routing and notification routing | `backend/app/agents/graph.py`
- [ ] Verify graph compiles and runs with empty state | `backend/app/agents/graph.py`

### Phase 2: Core Nodes
- [ ] Implement `perception_node` — calls sensor fusion, sets observation + score + risk | `backend/app/agents/perception.py`
- [ ] Implement `assess_risk` — deterministic risk classification with fall override | `backend/app/agents/risk.py`
- [ ] Implement `log_only_node` — store observation to SQLite event log, emit SSE | `backend/app/agents/log.py`
- [ ] Implement `memory_retrieval_node` — query memories + match recipe | `backend/app/agents/memory_node.py`

### Phase 3: Planner
- [ ] Build planner system prompt with observation, memories, recipe, tools | `backend/app/agents/planner.py`
- [ ] Implement `planner_node` — Sonnet call with tool use, parse planned actions | `backend/app/agents/planner.py`
- [ ] Recipe preference logic: if matched recipe with success > 0.7, use it | `backend/app/agents/planner.py`

### Phase 4: MAR Gate
- [ ] Define 3 critic prompts (Clinical Safety, Family Tone, Privacy) | `backend/app/agents/mar.py`
- [ ] Implement `mar_gate_node` — run 3 critics in parallel (asyncio.gather), collect verdicts | `backend/app/agents/mar.py`
- [ ] Revision loop: if any REVISE, rewrite notification (max 2 rounds) | `backend/app/agents/mar.py`
- [ ] Log full debate trace to state for dashboard display | `backend/app/agents/mar.py`

### Phase 5: Executor & Integration
- [ ] Implement `executor_node` — dispatch actions as WebSocket commands to ESP32 | `backend/app/agents/executor.py`
- [ ] Store completed episode in memory system after execution | `backend/app/agents/executor.py`
- [ ] Emit SSE events: `episode_start`, `episode_end`, `notification`, `agitation_update` | `backend/app/agents/executor.py`
- [ ] Wire graph invocation to WebSocket message handler in main.py | `backend/app/main.py`

## Verification
- [ ] Low-risk synthetic input → log_only path, no actions dispatched
- [ ] Medium-risk input → gentle intervention (LED + speech), no notification
- [ ] High-risk input → full intervention + caregiver notification
- [ ] Fall detection → immediate high-risk path regardless of agitation score
- [ ] MAR debate trace contains 3 critic responses with APPROVE/REVISE
- [ ] Notification revised when critic says REVISE, max 2 rounds
- [ ] Comfort recipe used when match found with success > 0.7
- [ ] Episode stored in memory after execution completes
- [ ] SSE events received by dashboard for each pipeline run
