"""Planner node — decides intervention using Claude Sonnet + retrieved memories.

Uses comfort recipe if available (workflow memory pattern).
Falls back to Sonnet reasoning for novel situations.
Reference: 08-fastapi-langgraph.md, 07-safety-ethics.md
"""

from __future__ import annotations

import json
import os

import anthropic

from app.agents.state import AgentState
from app.cst import select_probe, grade_response, CSTProbe

_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

_SYSTEM = """You are Ed's intervention planner for an elderly dementia care companion bear.

Given a semantic observation, risk level, and retrieved memories, decide on the best intervention.

Respond with a JSON object:
{
  "plan": "brief description of what you'll do and why",
  "actions": [
    {"action": "speak|breathe|led|play_clip", "payload": {...}},
    ...
  ],
  "notification": "caregiver message or null if not needed"
}

Rules:
- low risk: no intervention needed, return empty actions
- medium risk: gentle comfort (LED change, soft speech, breathing pacer)
- high risk: full response (family voice clip, breathing, speech, notify caregiver)
- If a comfort recipe is available and matches, prefer it over generating new actions
- Notifications must be warm, not clinical. Never say "agitation episode" — say "restless moment"
- Keep speech actions under 15 seconds of audio
- Never make medical claims or promises about outcomes
"""


def _build_prompt(state: AgentState) -> str:
    observation = state.get("semantic_observation", "No observation available.")
    risk = state.get("risk_level", "low")
    score = state.get("agitation_score", 0.0)
    memories = state.get("memories", [])
    recipe = state.get("comfort_recipe")

    memory_text = "\n".join(
        f"- [{m.get('score', 0):.2f}] {m.get('text', '')}" for m in memories[:3]
    ) or "No relevant memories found."

    recipe_text = (
        f"Comfort recipe available: {recipe.get('description', '')} "
        f"(success rate: {recipe.get('success_rate', 0):.0%})"
        if recipe
        else "No comfort recipe available."
    )

    return f"""Current observation: {observation}
Risk level: {risk} (score: {score:.1f}/100)

Relevant memories:
{memory_text}

{recipe_text}

Decide on the appropriate intervention."""


async def planner_node(state: AgentState) -> AgentState:
    """Plan intervention using Sonnet. Low risk returns immediately without LLM call."""
    risk = state.get("risk_level", "low")

    # Grade previous CST probe response if one was pending
    cdr = state.get("cdr_scores") or {}
    last_probe_result = state.get("last_probe_result")
    used_probe_ids = set(state.get("used_probe_ids") or [])
    last_probe_dimension = state.get("last_probe_dimension")
    transcript = (state.get("sensor_snapshot") and state["sensor_snapshot"].speech_text) or ""

    # If last turn had a probe and patient said something, grade it
    pending_probe_id = state.get("_pending_probe_id")
    pending_probe = None
    if pending_probe_id and transcript:
        from app.cst import PROBES
        pending_probe_obj = next((p for p in PROBES if p.id == pending_probe_id), None)
        if pending_probe_obj:
            graded = grade_response(pending_probe_obj, transcript)
            last_probe_result = graded.__dict__
            last_probe_dimension = None  # reset — graded, ready for next probe turn

    # Low risk — good time for a CST probe (calm conversation)
    if risk == "low":
        probe = select_probe(cdr, last_probe_dimension, used_probe_ids)
        if probe:
            used_probe_ids.add(probe.id)
            return {
                **state,
                "plan": f"CST probe: {probe.dimension} — asking '{probe.question}'",
                "actions": [{"action": "speak", "payload": {"text": probe.question, "tone": "warm"}}],
                "notification": None,
                "last_probe_dimension": probe.dimension,
                "used_probe_ids": list(used_probe_ids),
                "last_probe_result": last_probe_result,
                "_pending_probe_id": probe.id,
            }
        return {
            **state,
            "plan": "No intervention needed — agitation within normal range.",
            "actions": [],
            "notification": None,
            "last_probe_dimension": None,
            "used_probe_ids": list(used_probe_ids),
            "last_probe_result": last_probe_result,
        }

    prompt = _build_prompt(state)

    response = _client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=500,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "plan": "JSON parse failed — applying safe default gentle intervention.",
            "actions": [
                {"action": "led", "payload": {"color": "amber", "pattern": "pulse"}},
                {"action": "speak", "payload": {"text": "I'm right here with you.", "tone": "warm"}},
            ],
            "notification": None,
        }

    return {
        **state,
        "plan": result.get("plan", ""),
        "actions": result.get("actions", []),
        "notification": result.get("notification"),
        "last_probe_dimension": None,  # intervention turn resets probe alternation
        "used_probe_ids": list(used_probe_ids),
        "last_probe_result": last_probe_result,
    }
