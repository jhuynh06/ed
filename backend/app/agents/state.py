"""Theodore agent state — shared TypedDict passed through the LangGraph pipeline."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from app.models import SensorSnapshot


class AgentState(TypedDict, total=False):
    # Input
    raw_sensor: dict[str, Any]                  # raw WebSocket sensor_data payload
    sensor_snapshot: SensorSnapshot | None       # parsed + validated snapshot

    # Perception node output
    semantic_observation: str                    # IoT-LLM translated text

    # Risk node output
    agitation_score: float                       # 0–100
    risk_level: Literal["low", "medium", "high"]

    # Memory node output
    memories: list[dict[str, Any]]              # retrieved episodic + semantic memories
    comfort_recipe: dict[str, Any] | None       # matched comfort recipe if any

    # Planner node output
    plan: str                                    # natural language plan
    actions: list[dict[str, Any]]               # structured action list for executor
    notification: str | None                    # caregiver notification draft

    # Executor node output
    executed_actions: list[dict[str, Any]]      # commands sent to bear
    mar_result: dict[str, Any] | None           # MAR gate result if notification sent

    # Outcome tracking (for recipe EMA update)
    agitation_before: float | None              # score at episode start
    recipe_id: str | None                       # recipe used this episode

    # Enriched signals
    fused_emotion: dict[str, Any] | None        # FusedEmotion.asdict() from emotion_fusion
    anomaly: dict[str, Any] | None              # AnomalyResult from anomaly detector
    acoustic_features: dict[str, Any] | None    # AcousticFeatures from librosa
    nlp_features: dict[str, Any] | None         # NLPFeatures from transcript
    cdr_scores: dict[str, Any] | None           # CDRScores mapped from features
    sundowning: dict[str, Any] | None           # SundowningStatus from sundowning detector
    wandering_alert: dict[str, Any] | None      # WanderingAlert from wandering detector

    # CST (Cognitive Stimulation Therapy) probe tracking
    last_probe_dimension: str | None            # CDR dimension of last probe (enforces alternation)
    used_probe_ids: list[str]                   # probe IDs used this session (avoid repeats)
    last_probe_result: dict[str, Any] | None    # ProbeResult from last graded response

    # Metadata
    episode_id: str | None
    error: str | None
