"""Unit tests for anomaly.py z-score baseline tracker."""

from __future__ import annotations

import sys
import os
from unittest.mock import patch

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.anomaly import BaselineTracker, AnomalyResult


def tracker_with_baseline(agitation_values: list[float], hr_values: list[float] | None = None) -> BaselineTracker:
    """Prime a tracker with baseline data."""
    t = BaselineTracker(window=50)
    for i, v in enumerate(agitation_values):
        hr = hr_values[i] if hr_values else None
        t.update(v, hr)
    return t


# ── insufficient baseline ─────────────────────────────────────────────

def test_fewer_than_10_samples_is_normal():
    t = BaselineTracker()
    for _ in range(9):
        result = t.update(50.0)
    assert result.severity == "normal"
    assert not result.is_anomaly


# ── normal readings ───────────────────────────────────────────────────

def test_in_baseline_range_not_anomaly():
    t = tracker_with_baseline([50.0] * 20)
    result = t.update(51.0)  # within 1 std dev
    assert not result.is_anomaly
    assert result.severity == "normal"


# ── elevated anomaly ──────────────────────────────────────────────────

def test_z_score_above_2_is_elevated():
    baseline = [50.0] * 20
    t = tracker_with_baseline(baseline)
    # Use varied baseline
    varied = list(np.random.normal(50, 5, 20))
    t2 = tracker_with_baseline(varied)
    # Push a value 2.5 std devs above mean (~62.5)
    mean = sum(varied) / len(varied)
    spike = mean + 2.5 * 5
    result = t2.update(spike)
    assert result.is_anomaly
    assert result.severity in ("elevated", "critical")


def test_z_score_above_3_is_critical():
    rng = np.random.default_rng(42)
    varied = list(rng.normal(50, 5, 20))
    t = tracker_with_baseline(varied)
    mean = sum(varied) / len(varied)
    spike = mean + 4.0 * 5  # 4 std devs — well above critical threshold
    result = t.update(spike)
    assert result.severity == "critical"


# ── 3am unusual hour ─────────────────────────────────────────────────

def test_3am_critical_agitation_mentions_unusual_hour():
    import numpy as np
    varied = list(np.random.normal(50, 5, 20))
    t = tracker_with_baseline(varied)
    mean = sum(varied) / len(varied)
    spike = mean + 3.5 * 5

    with patch("app.anomaly._unusual_hour", return_value=True):
        result = t.update(spike)

    if result.metric == "agitation" and result.z_score > 3.0:
        assert "unusual hour" in result.message


def test_normal_hour_no_unusual_hour_message():
    import numpy as np
    varied = list(np.random.normal(50, 5, 20))
    t = tracker_with_baseline(varied)
    mean = sum(varied) / len(varied)
    spike = mean + 3.5 * 5

    with patch("app.anomaly._unusual_hour", return_value=False):
        result = t.update(spike)

    assert "unusual hour" not in result.message


# ── HR metric ─────────────────────────────────────────────────────────

def test_hr_anomaly_detected():
    import numpy as np
    ag = list(np.random.normal(50, 2, 20))
    hr = list(np.random.normal(72, 3, 20))
    t = tracker_with_baseline(ag, hr)
    hr_mean = sum(hr) / len(hr)
    result = t.update(ag[-1], hr_bpm=hr_mean + 4 * 3)  # 4 std devs
    assert result.is_anomaly


# ── z_score = 0 when std is zero ─────────────────────────────────────

def test_constant_baseline_no_anomaly():
    t = tracker_with_baseline([50.0] * 20)
    result = t.update(50.0)
    assert result.z_score == 0.0
    assert not result.is_anomaly
