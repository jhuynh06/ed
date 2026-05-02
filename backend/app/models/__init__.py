"""Ed — All Pydantic models in one place."""

from __future__ import annotations

import uuid
import time
from typing import Literal

from pydantic import BaseModel, Field


# ── Sensor Models (from sensor-fusion spec) ──────────────────────────

class IMUFeatures(BaseModel):
    jerk_magnitude: float
    hug_detected: bool = False
    fall_detected: bool = False
    tremor_power: float = 0.0
    rocking_detected: bool = False
    stillness_duration_s: float = 0.0


class HRState(BaseModel):
    bpm: int = 0
    spo2: int = 0
    valid: bool = False
    baseline_bpm: float = 72.0
    elevation_pct: float = 0.0
    variability: float = 0.0


class TouchState(BaseModel):
    any_contact: bool = False
    squeeze_intensity: float = 0.0
    petting_detected: bool = False
    grip_duration_s: float = 0.0
    active_pads: list[int] = []


class VocalEmotion(BaseModel):
    valence: float = 0.0
    arousal: float = 0.0
    dominant_emotion: Literal["calm", "sad", "angry", "fearful", "neutral"] = "neutral"


class SensorSnapshot(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    imu: IMUFeatures
    hr: HRState
    touch: TouchState
    speech_text: str | None = None
    vocal_emotion: VocalEmotion | None = None


class FusedObservation(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    semantic_text: str
    agitation_score: float
    features: SensorSnapshot
    risk_level: Literal["low", "medium", "high"] = "low"


# ── Memory Models (from memory-system spec) ──────────────────────────

class EpisodicMemory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    sensor_summary: str
    user_speech: str | None = None
    agent_actions: list[str] = []
    outcome: Literal["calm_restored", "escalated", "no_change"] = "no_change"
    agitation_before: float = 0.0
    agitation_after: float = 0.0
    confidence: float = 0.3
    consolidated: bool = False
    linked_episodes: list[str] = []


class SemanticMemory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = Field(default_factory=time.time)
    pattern: str
    source_episode_ids: list[str] = []
    confidence: float = 0.5
    keywords: list[str] = []
    last_reinforced: float = Field(default_factory=time.time)


class ComfortRecipe(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trigger_pattern: str
    trigger_embedding: list[float] = []
    action_sequence: list[str]
    success_rate: float = 0.0
    times_used: int = 0
    last_used: float = Field(default_factory=time.time)


class MemoryQuery(BaseModel):
    query_text: str
    time_range_hours: float | None = None
    min_confidence: float = 0.2
    top_k: int = 5
    include_recipes: bool = True


# ── WebSocket Messages (ESP32 ↔ Backend) ─────────────────────────────

class SensorDataMsg(BaseModel):
    type: Literal["sensor_data"] = "sensor_data"
    ts: float
    imu: dict
    hr: dict
    touch: dict


class AudioChunkMsg(BaseModel):
    type: Literal["audio_chunk"] = "audio_chunk"
    payload: str  # base64-encoded PCM


class CommandMsg(BaseModel):
    type: Literal["command"] = "command"
    action: Literal["speak", "breathe", "led", "play_clip"]
    payload: dict


class StatusMsg(BaseModel):
    type: Literal["status"] = "status"
    connected: bool = True
    uptime_s: float = 0.0


# ── SSE Events (Backend → Dashboard) ─────────────────────────────────

class AgitationUpdateEvent(BaseModel):
    type: Literal["agitation_update"] = "agitation_update"
    timestamp: float
    score: float
    risk: Literal["low", "medium", "high"]


class EpisodeStartEvent(BaseModel):
    type: Literal["episode_start"] = "episode_start"
    id: str
    timestamp: float
    agitation: float


class EpisodeEndEvent(BaseModel):
    type: Literal["episode_end"] = "episode_end"
    id: str
    duration: float
    peak: float
    outcome: str


class NotificationEvent(BaseModel):
    type: Literal["notification"] = "notification"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str
    priority: Literal["info", "warning", "urgent"]
    mar_trace: list[dict] | None = None


class VitalsUpdateEvent(BaseModel):
    type: Literal["vitals_update"] = "vitals_update"
    bpm: int
    spo2: int
    baseline_bpm: float


# ── MAR Models (from agent-pipeline spec) ─────────────────────────────

class CriticVerdict(BaseModel):
    critic: str
    verdict: Literal["APPROVE", "REVISE"]
    feedback: str


class MARResult(BaseModel):
    final_notification: str
    approved: bool
    debate_trace: list[dict]
    rounds: int


# ── Eval Models (from synthetic-eval spec) ────────────────────────────

class SyntheticProfile(BaseModel):
    name: str
    age: int
    dementia_stage: Literal["mild", "moderate"]
    family_members: list[dict] = []
    known_triggers: list[str] = []
    calming_preferences: list[str] = []
    baseline_hr: int = 72
    typical_agitation_times: list[str] = []
    personality_notes: str = ""


class SensorFrame(BaseModel):
    offset_ms: int
    sensor_data: dict
    speech_text: str | None = None
    vocal_emotion: dict | None = None


class SyntheticScenario(BaseModel):
    id: str
    name: str
    profile: SyntheticProfile
    description: str
    duration_seconds: int
    sensor_stream: list[SensorFrame]
    expected_risk_level: Literal["low", "medium", "high"]
    expected_intervention_type: Literal["none", "gentle", "full_intervention"]


class EvalScores(BaseModel):
    appropriateness: int = Field(ge=0, le=10)
    timeliness: int = Field(ge=0, le=10)
    personalization: int = Field(ge=0, le=10)
    reasoning: str = ""


class EvalResult(BaseModel):
    scenario_id: str
    scores: EvalScores
    log: list[dict] = []
