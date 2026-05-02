"""Risk node — computes agitation score and assigns risk level.

Uses the weighted fusion formula from sensor-patterns steering doc.
No LLM call — pure heuristic, fast.
"""

from __future__ import annotations

from typing import Literal

from app.agents.state import AgentState
from app.models import SensorSnapshot
from app.sundowning import record_agitation, get_sundowning_status


def compute_agitation_score(snap: SensorSnapshot) -> float:
    """Weighted fusion of IMU, HR, vocal, and touch signals. Returns 0–100."""
    imu_score = min(snap.imu.jerk_magnitude / 2.0, 1.0) * 100

    if snap.hr.valid:
        hr_score = min(abs(snap.hr.elevation_pct) / 30.0, 1.0) * 100
    else:
        hr_score = 0.0

    vocal_score = (snap.vocal_emotion.arousal * 100) if snap.vocal_emotion else 0.0

    # Touch absence (no contact for extended period) signals distress
    touch_score = (
        min(snap.touch.grip_duration_s / 300.0, 1.0) * 100
        if not snap.touch.any_contact
        else 0.0
    )

    if snap.hr.valid:
        weights = {"imu": 0.25, "hr": 0.25, "vocal": 0.30, "touch": 0.20}
    else:
        weights = {"imu": 0.30, "hr": 0.0, "vocal": 0.40, "touch": 0.30}

    return (
        weights["imu"] * imu_score
        + weights["hr"] * hr_score
        + weights["vocal"] * vocal_score
        + weights["touch"] * touch_score
    )


def score_to_risk(score: float) -> Literal["low", "medium", "high"]:
    if score < 30:
        return "low"
    elif score < 60:
        return "medium"
    else:
        return "high"


async def risk_node(state: AgentState) -> AgentState:
    """Compute agitation score and risk level from the parsed sensor snapshot."""
    snap: SensorSnapshot | None = state.get("sensor_snapshot")

    # If perception already set risk (e.g. fall detection), pass through
    if state.get("risk_level") and state.get("agitation_score") is not None:
        return state

    if snap is None:
        return {**state, "agitation_score": 0.0, "risk_level": "low"}

    score = compute_agitation_score(snap)

    # Apply sundowning risk multiplier and record for pattern learning
    sundowning = get_sundowning_status()
    score = min(score * sundowning.risk_multiplier, 100.0)
    record_agitation(score)

    risk = score_to_risk(score)

    return {
        **state,
        "agitation_score": score,
        "risk_level": risk,
        "sundowning": sundowning.__dict__,
    }


def route_by_risk(state: AgentState) -> str:
    """Conditional edge: route to memory retrieval or log-only based on risk."""
    risk = state.get("risk_level", "low")
    if risk == "low":
        return "log_only"
    return "memory"
