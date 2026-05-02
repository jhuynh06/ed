"""Perception node — translates raw sensor data into semantic text (IoT-LLM pattern).

Uses Claude Haiku for speed. Never sends raw numbers to the planner.
Includes a hash-based LRU cache on quantized sensor features to skip
redundant Haiku calls during calm/stable periods.
Reference: arxiv.org/html/2410.02429
"""

from __future__ import annotations

import hashlib
import os
from collections import OrderedDict

import anthropic

from app.agents.state import AgentState
from app.audio_pipeline import AudioResult
from app.emotion_fusion import EmotionFuser
from app.models import (
    HRState,
    IMUFeatures,
    SensorSnapshot,
    TouchState,
)

_client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
_fuser = EmotionFuser()

# ── Perception cache ──────────────────────────────────────────────────

_CACHE_MAX = 64
_cache: OrderedDict[str, str] = OrderedDict()


def _quantize_key(snap: SensorSnapshot) -> str:
    """Quantize sensor features to coarse buckets and hash them.

    Small changes (jitter, HR ±2bpm) map to the same key, avoiding
    redundant Haiku calls during stable periods.
    """
    parts = (
        round(snap.imu.jerk_magnitude, 1),
        round(snap.imu.stillness_duration_s / 30) * 30,  # 30s buckets
        int(snap.imu.rocking_detected),
        int(snap.imu.hug_detected),
        round(snap.hr.bpm / 5) * 5 if snap.hr.valid else -1,  # 5bpm buckets
        round(snap.hr.elevation_pct / 5) * 5 if snap.hr.valid else -1,
        int(snap.touch.any_contact),
        round(snap.touch.squeeze_intensity, 1),
        (snap.speech_text or "")[:50],
    )
    return hashlib.md5(str(parts).encode()).hexdigest()


def perception_cache_stats() -> dict:
    return {"size": len(_cache), "max": _CACHE_MAX}


def clear_perception_cache() -> None:
    _cache.clear()

_SYSTEM = (
    "You are a sensor interpreter for an elderly care companion bear. "
    "Translate raw sensor features into a single warm, clinical-but-human paragraph "
    "that describes what the user is experiencing right now. "
    "Focus on: movement patterns, heart rate relative to baseline, touch behavior, and speech. "
    "Do not mention sensor names or numbers directly — describe the experience. "
    "Keep it under 60 words."
)


def _build_sensor_snapshot(raw: dict) -> SensorSnapshot:
    """Parse raw WebSocket payload into a typed SensorSnapshot."""
    imu_raw = raw.get("imu", {})
    hr_raw = raw.get("hr", {})
    touch_raw = raw.get("touch", {})

    imu = IMUFeatures(
        jerk_magnitude=imu_raw.get("jerk_magnitude", 0.0),
        hug_detected=imu_raw.get("hug_detected", False),
        fall_detected=imu_raw.get("fall_detected", False),
        tremor_power=imu_raw.get("tremor_power", 0.0),
        rocking_detected=imu_raw.get("rocking_detected", False),
        stillness_duration_s=imu_raw.get("stillness_duration_s", 0.0),
    )
    hr = HRState(
        bpm=hr_raw.get("bpm", 0),
        spo2=hr_raw.get("spo2", 0),
        valid=hr_raw.get("valid", False),
        baseline_bpm=hr_raw.get("baseline_bpm", 72.0),
        elevation_pct=hr_raw.get("elevation_pct", 0.0),
    )
    touch = TouchState(
        any_contact=touch_raw.get("any_contact", False),
        squeeze_intensity=touch_raw.get("squeeze_intensity", 0.0),
        grip_duration_s=touch_raw.get("grip_duration_s", 0.0),
    )
    return SensorSnapshot(
        imu=imu,
        hr=hr,
        touch=touch,
        speech_text=raw.get("speech_text"),
    )


def _format_features(snap: SensorSnapshot) -> str:
    """Format snapshot into a structured prompt for Haiku."""
    lines = [
        f"IMU: jerk={snap.imu.jerk_magnitude:.2f}, stillness={snap.imu.stillness_duration_s:.0f}s, "
        f"hug={snap.imu.hug_detected}, rocking={snap.imu.rocking_detected}",
        f"HR: bpm={snap.hr.bpm}, baseline={snap.hr.baseline_bpm:.0f}, "
        f"elevation={snap.hr.elevation_pct:.1f}%, valid={snap.hr.valid}",
        f"Touch: contact={snap.touch.any_contact}, squeeze={snap.touch.squeeze_intensity:.2f}, "
        f"grip_duration={snap.touch.grip_duration_s:.0f}s",
        f"Speech: {snap.speech_text or 'none'}",
    ]
    return "\n".join(lines)


async def perception_node(state: AgentState) -> AgentState:
    """Parse sensor data and translate to semantic observation via Haiku."""
    raw = state.get("raw_sensor", {})

    try:
        snap = _build_sensor_snapshot(raw)
    except Exception as e:
        return {**state, "error": f"perception: failed to parse sensor data: {e}"}

    # Fall detection is a hard safety override — skip LLM, return immediately
    if snap.imu.fall_detected:
        return {
            **state,
            "sensor_snapshot": snap,
            "semantic_observation": "FALL DETECTED — immediate caregiver notification required.",
            "risk_level": "high",
            "agitation_score": 100.0,
        }

    prompt = _format_features(snap)
    cache_key = _quantize_key(snap)

    if cache_key in _cache:
        _cache.move_to_end(cache_key)
        semantic_text = _cache[cache_key]
    else:
        response = await _client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=150,
            system=_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        semantic_text = response.content[0].text.strip()
        _cache[cache_key] = semantic_text
        if len(_cache) > _CACHE_MAX:
            _cache.popitem(last=False)

    return {
        **state,
        "sensor_snapshot": snap,
        "semantic_observation": semantic_text,
        "fused_emotion": _fuser.fuse(
            AudioResult(
                speech_detected=snap.vocal_emotion is not None,
                transcription=snap.speech_text,
                valence=snap.vocal_emotion.valence if snap.vocal_emotion else 0.0,
                arousal=snap.vocal_emotion.arousal if snap.vocal_emotion else 0.0,
                dominant_emotion=snap.vocal_emotion.dominant_emotion if snap.vocal_emotion else "neutral",
            )
        ).__dict__,
    }
