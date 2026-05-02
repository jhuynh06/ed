"""Executor node — dispatches planned actions to the bear and runs MAR gate on notifications.

In production, actions are sent via the WebSocket connection to the ESP32.
This stub logs actions and runs the MAR gate if a notification is present.
Reference: 07-safety-ethics.md (MAR pattern), 08-fastapi-langgraph.md
"""

from __future__ import annotations

import asyncio
import logging
import os

import anthropic

from app.agents.state import AgentState
from app.anomaly import check_anomaly
from app.memory.bandit import update_recipe
from app.memory.workflow import update_recipe_outcome
from app.models import CriticVerdict, MARResult
from app.wandering import detect_wandering

logger = logging.getLogger(__name__)

_client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

_CRITICS = [
    (
        "Clinical Safety",
        "Is this medically appropriate? Could delay cause harm? Could it cause unnecessary medical anxiety?",
    ),
    (
        "Family Tone",
        "Will this scare the family member unnecessarily? Is the language warm but clear?",
    ),
    (
        "Privacy",
        "Does this share more information than necessary? Could it be more concise?",
    ),
]


async def _call_critic(name: str, criteria: str, notification: str, context: str) -> CriticVerdict:
    response = await _client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=150,
        messages=[
            {
                "role": "user",
                "content": (
                    f"You are the {name} critic reviewing a caregiver notification.\n\n"
                    f"Criteria: {criteria}\n\n"
                    f"Context: {context}\n\n"
                    f"Notification: {notification}\n\n"
                    "Reply with exactly: APPROVE or REVISE, then a newline, then one sentence of feedback."
                ),
            }
        ],
    )
    text = response.content[0].text.strip()
    lines = text.split("\n", 1)
    verdict_str = lines[0].strip().upper()
    feedback = lines[1].strip() if len(lines) > 1 else ""
    verdict = "APPROVE" if "APPROVE" in verdict_str else "REVISE"
    return CriticVerdict(critic=name, verdict=verdict, feedback=feedback)


async def _rewrite_notification(notification: str, feedback: str) -> str:
    response = await _client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=150,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Rewrite this caregiver notification based on the feedback.\n\n"
                    f"Original: {notification}\n\n"
                    f"Feedback:\n{feedback}\n\n"
                    "Return only the rewritten notification, nothing else."
                ),
            }
        ],
    )
    return response.content[0].text.strip()


async def _run_mar_gate(notification: str, context: str) -> MARResult:
    """Run 3 critics in parallel, rewrite up to 2 rounds if any say REVISE."""
    verdicts = list(await asyncio.gather(*[_call_critic(name, criteria, notification, context) for name, criteria in _CRITICS]))

    rounds = 0
    for _ in range(2):
        revisions = [v for v in verdicts if v.verdict == "REVISE"]
        if not revisions:
            break
        feedback = "\n".join(f"[{v.critic}]: {v.feedback}" for v in revisions)
        notification = await _rewrite_notification(notification, feedback)
        verdicts = list(await asyncio.gather(*[_call_critic(name, criteria, notification, context) for name, criteria in _CRITICS]))
        rounds += 1

    return MARResult(
        final_notification=notification,
        approved=all(v.verdict == "APPROVE" for v in verdicts),
        debate_trace=[v.model_dump() for v in verdicts],
        rounds=rounds,
    )


async def executor_node(state: AgentState) -> AgentState:
    """Dispatch actions to bear (stub) and run MAR gate on any notification.

    For 'speak' actions, generates TTS audio chunks via Cartesia and
    stores them in state for the WebSocket handler to stream to the ESP32.
    """
    actions = state.get("actions", [])
    executed: list[dict] = []
    tts_chunks: list[list[bytes]] = []

    for action in actions:
        logger.info("BEAR ACTION: %s", action)
        executed.append({**action, "status": "dispatched"})

        # Generate TTS audio for speak actions
        if action.get("action") == "speak" and action.get("payload", {}).get("text"):
            try:
                from app.tts import stream_tts
                chunks: list[bytes] = []
                async for chunk in stream_tts(action["payload"]["text"]):
                    chunks.append(chunk)
                tts_chunks.append(chunks)
            except Exception as exc:
                logger.warning("TTS failed for action %s: %s", action, exc)

    # Wandering/disorientation detection from transcript
    snap = state.get("sensor_snapshot")
    transcript = snap.speech_text if snap else None
    wandering_alert = None
    if transcript:
        wandering_alert = detect_wandering(transcript)
        if wandering_alert.triggered and wandering_alert.urgency == "high":
            logger.warning("WANDERING ALERT: %s", wandering_alert.message)
            # Inject as urgent notification if no notification already queued
            if not state.get("notification"):
                state = {**state, "notification": wandering_alert.message}

    notification = state.get("notification")
    mar_result = None
    if notification:
        context = state.get("semantic_observation", "")
        mar = await _run_mar_gate(notification, context)
        mar_result = mar.model_dump()
        logger.info(
            "MAR gate: approved=%s rounds=%d notification=%r",
            mar.approved,
            mar.rounds,
            mar.final_notification,
        )

    # Update comfort recipe outcome using EMA + Thompson sampling bandit
    recipe_id = state.get("recipe_id")
    agitation_before = state.get("agitation_before")
    agitation_after = state.get("agitation_score")
    if recipe_id and agitation_before is not None and agitation_after is not None:
        update_recipe_outcome(recipe_id, agitation_before, agitation_after)
        success = (agitation_before - agitation_after) >= 15.0
        update_recipe(recipe_id, success=success)
        logger.info(
            "Recipe %s outcome: %.1f → %.1f (success=%s)",
            recipe_id, agitation_before, agitation_after, success,
        )

    # Anomaly detection — flag unusual agitation readings (no HR sensor available)
    anomaly_result = None
    if agitation_after is not None:
        anomaly_result = check_anomaly(agitation_after, hr_bpm=None)
        if anomaly_result.is_anomaly:
            logger.warning("ANOMALY: %s", anomaly_result.message)

    return {**state, "executed_actions": executed, "mar_result": mar_result, "anomaly": anomaly_result.__dict__ if anomaly_result else None, "wandering_alert": wandering_alert.__dict__ if wandering_alert else None, "tts_chunks": tts_chunks}
