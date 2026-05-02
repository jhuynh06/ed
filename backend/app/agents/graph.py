"""Ed LangGraph — wires all nodes with conditional routing.

Pipeline:
  perception → risk → [low: END] [medium/high: memory → planner → executor → END]
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.agents.executor import executor_node
from app.agents.memory import memory_node
from app.agents.perception import perception_node
from app.agents.planner import planner_node
from app.agents.risk import risk_node, route_by_risk
from app.agents.state import AgentState


def build_ed_graph() -> StateGraph:
    """Build and compile the Ed agent graph."""
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("perception", perception_node)
    graph.add_node("risk", risk_node)
    graph.add_node("memory", memory_node)
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)

    # Entry point
    graph.set_entry_point("perception")

    # Linear edges
    graph.add_edge("perception", "risk")
    graph.add_edge("memory", "planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", END)

    # Conditional routing after risk assessment
    graph.add_conditional_edges(
        "risk",
        route_by_risk,
        {
            "log_only": END,   # low risk — no intervention
            "memory": "memory",  # medium/high — full pipeline
        },
    )

    return graph.compile()


# Module-level singleton for the FastAPI app to import
ed_graph = build_ed_graph()
