# LangGraph — Quick Reference for Ed

Source: langchain-ai.github.io/langgraph/

## Core Concepts

### StateGraph
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal

class MyState(TypedDict):
    messages: list
    next_step: str

graph = StateGraph(MyState)
```

### Nodes (functions that transform state)
```python
def my_node(state: MyState) -> dict:
    # Return only the keys you want to update
    return {"messages": state["messages"] + ["new message"]}

graph.add_node("my_node", my_node)
```

### Edges
```python
# Fixed edge: always go from A to B
graph.add_edge("node_a", "node_b")

# Conditional edge: route based on state
def router(state: MyState) -> str:
    if state["next_step"] == "done":
        return "end"
    return "continue"

graph.add_conditional_edges(
    "node_a",
    router,
    {"continue": "node_b", "end": END}
)
```

### Entry point and compile
```python
graph.set_entry_point("first_node")
app = graph.compile()
```

### Invoke
```python
# Sync
result = app.invoke({"messages": [], "next_step": ""})

# Async
result = await app.ainvoke({"messages": [], "next_step": ""})
```

## Ed's Graph Pattern

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal

class EdState(TypedDict):
    raw_sensor: dict
    observation: dict | None
    semantic_text: str
    agitation_score: float
    risk_level: Literal["low", "medium", "high"]
    relevant_memories: list
    matched_recipe: dict | None
    planned_actions: list
    notification: dict | None
    mar_debate: list | None
    notification_approved: bool
    executed_actions: list
    episode_id: str | None

def route_by_risk(state: EdState) -> str:
    if state["risk_level"] == "low":
        return "log_only"
    return "memory_retrieval"

def route_notification(state: EdState) -> str:
    if state.get("notification"):
        return "mar_gate"
    return "executor"

graph = StateGraph(EdState)

graph.add_node("perception", perception_node)
graph.add_node("risk_assessment", risk_node)
graph.add_node("log_only", log_node)
graph.add_node("memory_retrieval", memory_node)
graph.add_node("planner", planner_node)
graph.add_node("mar_gate", mar_node)
graph.add_node("executor", executor_node)

graph.set_entry_point("perception")
graph.add_edge("perception", "risk_assessment")
graph.add_conditional_edges("risk_assessment", route_by_risk,
    {"log_only": "log_only", "memory_retrieval": "memory_retrieval"})
graph.add_edge("log_only", END)
graph.add_edge("memory_retrieval", "planner")
graph.add_conditional_edges("planner", route_notification,
    {"mar_gate": "mar_gate", "executor": "executor"})
graph.add_edge("mar_gate", "executor")
graph.add_edge("executor", END)

app = graph.compile()
```

## Async Node Pattern
```python
async def perception_node(state: EdState) -> dict:
    snapshot = build_snapshot(state["raw_sensor"])
    semantic = await translate_iot_llm(snapshot)  # Haiku call
    score = compute_agitation_score(snapshot)
    return {
        "observation": snapshot.model_dump(),
        "semantic_text": semantic,
        "agitation_score": score,
    }
```

## Key LangGraph Tips
- Nodes return dicts with only the keys they update (partial state updates)
- Use `TypedDict` not `dataclass` for state
- Conditional edges return string keys that map to node names
- `END` is a special node that terminates the graph
- `ainvoke` for async, `invoke` for sync
- State is immutable between nodes — each node gets a fresh copy
