"""Tests for wandering detection, sundowning detector, and daily digest."""

from __future__ import annotations

import asyncio
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.wandering import detect_wandering, DISORIENTATION_PHRASES, WanderingAlert
from app.sundowning import SundowningDetector, SundowningStatus
from app.daily_digest import DigestInput, DailyDigest, _build_prompt, _parse_response


# ── Wandering detection ───────────────────────────────────────────────

def test_no_disorientation_not_triggered():
    result = detect_wandering("I love this music, it's a beautiful day.")
    assert not result.triggered
    assert result.urgency == "low"
    assert result.matched_phrases == []


def test_single_phrase_medium_urgency():
    result = detect_wandering("Excuse me, where am I? I feel confused.")
    assert result.triggered
    assert result.urgency == "medium"
    assert "where am i" in result.matched_phrases


def test_multiple_phrases_high_urgency():
    result = detect_wandering("Where am I? I want to go home. Who are you?")
    assert result.triggered
    assert result.urgency == "high"
    assert len(result.matched_phrases) >= 2


def test_case_insensitive():
    result = detect_wandering("WHERE AM I? I NEED TO GO HOME!")
    assert result.triggered
    assert result.urgency == "high"


def test_confidence_proportional_to_matches():
    result = detect_wandering("where am i and i want to go home and who are you")
    assert result.confidence == pytest.approx(3 / len(DISORIENTATION_PHRASES))


def test_message_contains_matched_phrase():
    result = detect_wandering("I want to go home right now.")
    assert "i want to go home" in result.message.lower()


def test_no_match_message():
    result = detect_wandering("Everything is fine today.")
    assert "No disorientation" in result.message


# ── Sundowning detector ───────────────────────────────────────────────

def make_detector_with_pattern(peak_hour: int = 16, agitation: float = 65.0) -> SundowningDetector:
    """Prime a detector with a clear sundowning pattern at peak_hour."""
    d = SundowningDetector()
    for _ in range(5):
        d.record(agitation, hour=peak_hour)
    # Low agitation at other hours
    for h in [9, 10, 11, 12, 20, 21]:
        for _ in range(3):
            d.record(15.0, hour=h)
    return d


def test_no_data_no_sundowning():
    d = SundowningDetector()
    status = d.status(hour=16)
    assert not status.is_sundowning_window
    assert not status.preemptive_flag
    assert status.risk_multiplier == 1.0
    assert status.peak_hour is None


def test_insufficient_readings_no_pattern():
    d = SundowningDetector()
    d.record(80.0, hour=16)
    d.record(80.0, hour=16)  # only 2, need 3
    status = d.status(hour=16)
    assert status.peak_hour is None


def test_sundowning_window_detected():
    d = make_detector_with_pattern(peak_hour=16)
    status = d.status(hour=16)
    assert status.is_sundowning_window
    assert status.risk_multiplier == 1.5
    assert status.peak_hour == 16


def test_preemptive_flag_one_hour_before():
    """Hour peak-1 is inside the window (window = peak-1 to peak+2), so multiplier is 1.5."""
    d = make_detector_with_pattern(peak_hour=16)
    status = d.status(hour=15)
    assert status.preemptive_flag
    assert status.is_sundowning_window  # peak-1 is inside the window
    assert status.risk_multiplier == 1.5


def test_preemptive_flag_two_hours_before():
    """Two hours before peak is outside the window — preemptive only."""
    d = make_detector_with_pattern(peak_hour=16)
    status = d.status(hour=14)
    assert not status.preemptive_flag  # only peak-1 triggers preemptive
    assert not status.is_sundowning_window
    assert status.risk_multiplier == 1.0


def test_outside_window_normal_multiplier():
    d = make_detector_with_pattern(peak_hour=16)
    status = d.status(hour=10)
    assert not status.is_sundowning_window
    assert not status.preemptive_flag
    assert status.risk_multiplier == 1.0


def test_morning_peak_not_sundowning():
    """Sundowning only applies to 1pm-8pm window."""
    d = SundowningDetector()
    for _ in range(5):
        d.record(70.0, hour=9)  # 9am peak — not sundowning
    for h in [14, 15, 16]:
        for _ in range(3):
            d.record(10.0, hour=h)
    status = d.status(hour=9)
    assert not status.is_sundowning_window


def test_low_agitation_peak_not_sundowning():
    """Peak must be > 45 agitation to count as sundowning."""
    d = SundowningDetector()
    for _ in range(5):
        d.record(30.0, hour=16)  # below threshold
    status = d.status(hour=16)
    assert not status.is_sundowning_window


def test_pattern_confidence_grows_with_readings():
    d = SundowningDetector()
    for i in range(10):
        d.record(60.0, hour=16)
    status = d.status(hour=16)
    assert status.pattern_confidence == pytest.approx(0.5)  # 10/20


def test_pattern_confidence_caps_at_1():
    d = SundowningDetector()
    for i in range(25):
        d.record(60.0, hour=16)
    status = d.status(hour=16)
    assert status.pattern_confidence == pytest.approx(1.0)


# ── Daily digest ──────────────────────────────────────────────────────

def make_input(**kwargs) -> DigestInput:
    defaults = dict(
        patient_name="Margaret",
        date_str="Friday, May 1",
        episodes=[{"time": "4:30pm", "peak_agitation": 72, "duration_s": 480,
                   "intervention": "grandson voice", "outcome": "calm restored"}],
        cdr_scores={"commun": 0.5, "orient": 1.0, "memory": 0.5, "judgment": 0.0, "total": 0.5, "flags": []},
        anomalies=[],
        trend_direction="stable",
        sundowning_occurred=True,
        peak_agitation_hour=16,
        top_flags=["mild topic drift"],
    )
    defaults.update(kwargs)
    return DigestInput(**defaults)


def test_build_prompt_contains_patient_name():
    prompt = _build_prompt(make_input())
    assert "Margaret" in prompt


def test_build_prompt_contains_sundowning():
    prompt = _build_prompt(make_input(sundowning_occurred=True))
    assert "True" in prompt


def test_build_prompt_no_episodes():
    prompt = _build_prompt(make_input(episodes=[]))
    assert "None" in prompt


def test_parse_response_valid():
    text = """SUMMARY:
Margaret had a restful morning but showed signs of sundowning around 4pm.

MOOD:
calm morning, agitated afternoon, calm evening

ACTIONS:
- Consider earlier dinner time
- Play familiar music at 3pm
"""
    summary, mood, actions = _parse_response(text, make_input())
    assert "Margaret" in summary
    assert "calm morning" in mood
    assert len(actions) == 2
    assert "Consider earlier dinner time" in actions[0]


def test_parse_response_fallback_on_missing_labels():
    text = "Something went wrong with the response format."
    summary, mood, actions = _parse_response(text, make_input())
    assert summary == text.strip()
    assert mood == ""
    assert actions == []


def test_generate_digest_calls_claude():
    """generate_digest should call Claude and return a DailyDigest."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="""SUMMARY:
Margaret had a good day overall with one episode of sundowning.

MOOD:
calm morning, agitated late afternoon, calm evening

ACTIONS:
- Play music at 3pm tomorrow
- Ensure bright lighting in afternoon
""")]

    with patch("app.daily_digest.anthropic.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        result = asyncio.run(generate_digest(make_input()))

    assert result.patient_name == "Margaret"
    assert result.episode_count == 1
    assert result.sundowning_detected is True
    assert result.trend_direction == "stable"
    assert result.cdr_total == pytest.approx(0.5)
    assert len(result.action_items) == 2
    assert "calm morning" in result.mood_arc


from app.daily_digest import generate_digest  # noqa: E402 — after mock setup
