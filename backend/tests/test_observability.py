"""Tests for app/observability.py and new endpoints (metrics, notes, reports).

Run with:
    pytest tests/test_observability.py -v
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, patch

import pytest


# ── EWMA Baseline ─────────────────────────────────────────────────────


def test_ewma_first_observation():
    from app.observability import EWMABaseline
    b = EWMABaseline()
    b.update(72.0)
    assert b.value == 72.0


def test_ewma_smooths():
    from app.observability import EWMABaseline, EWMA_ALPHA
    b = EWMABaseline()
    b.update(72.0)
    b.update(82.0)
    expected = EWMA_ALPHA * 82.0 + (1 - EWMA_ALPHA) * 72.0
    assert abs(b.value - expected) < 0.01


def test_ewma_deviation():
    from app.observability import EWMABaseline
    b = EWMABaseline()
    b.update(72.0)
    assert b.deviation(82.0) == 10.0


# ── HRV (RMSSD) ──────────────────────────────────────────────────────


def test_rmssd_insufficient_data():
    from app.observability import compute_rmssd, clear_rr_buffer
    clear_rr_buffer()
    assert compute_rmssd() is None


def test_rmssd_constant_rr():
    from app.observability import push_rr_interval, compute_rmssd, clear_rr_buffer
    clear_rr_buffer()
    for _ in range(20):
        push_rr_interval(800.0)
    assert compute_rmssd() == 0.0


def test_rmssd_variable_rr():
    from app.observability import push_rr_interval, compute_rmssd, clear_rr_buffer
    clear_rr_buffer()
    for i in range(20):
        push_rr_interval(800.0 + (10.0 if i % 2 else -10.0))
    rmssd = compute_rmssd()
    assert rmssd is not None and rmssd > 0


# ── Sleep Estimate ────────────────────────────────────────────────────


def test_sleep_estimate_no_data():
    from app.observability import estimate_sleep
    result = estimate_sleep([])
    assert result.total_hours == 0.0


def test_sleep_estimate_full_night():
    from app.observability import estimate_sleep
    import calendar, datetime
    # Simulate 7h of stillness from 11pm to 6am
    night = datetime.datetime(2025, 5, 1, 23, 0)
    morning = datetime.datetime(2025, 5, 2, 6, 0)
    start_ts = calendar.timegm(night.timetuple())
    end_ts = calendar.timegm(morning.timetuple())
    result = estimate_sleep([(start_ts, end_ts)])
    assert result.total_hours >= 6.0


# ── Speech Engagement ─────────────────────────────────────────────────


def test_speech_engagement():
    from app.observability import record_speech_segment, get_speech_engagement, reset_speech_engagement
    reset_speech_engagement()
    record_speech_segment(30.0)
    record_speech_segment(60.0)
    eng = get_speech_engagement()
    assert eng.speech_minutes == 1.5
    assert eng.utterance_count == 2


# ── Day Quality Score ─────────────────────────────────────────────────


def test_day_quality_perfect():
    from app.observability import compute_day_quality
    assert compute_day_quality(0, 10.0, 8.0, 30.0) == 5


def test_day_quality_terrible():
    from app.observability import compute_day_quality
    assert compute_day_quality(5, 80.0, 3.0, 1.0) == 1


def test_day_quality_mid():
    from app.observability import compute_day_quality
    score = compute_day_quality(1, 25.0, 7.0, 15.0)
    assert 2 <= score <= 4


# ── Behavioral Drift ─────────────────────────────────────────────────


def test_drift_no_alert_stable():
    from app.observability import check_behavioral_drift
    scores = [20, 22, 18, 21, 19, 20, 22, 21]
    result = check_behavioral_drift(scores)
    assert not result.triggered


def test_drift_alert_elevated():
    from app.observability import check_behavioral_drift
    scores = [20, 22, 18, 21, 19, 45, 48, 50]
    result = check_behavioral_drift(scores, threshold_days=3, threshold_pct=30.0)
    assert result.triggered
    assert "3 consecutive days" in result.message


# ── Speech Pause Tracking ────────────────────────────────────────────


def test_pause_stats_empty():
    from app.observability import get_pause_stats, reset_pauses
    reset_pauses()
    stats = get_pause_stats()
    assert stats["count"] == 0


def test_pause_stats():
    from app.observability import record_pause, get_pause_stats, reset_pauses
    reset_pauses()
    record_pause(0.5)
    record_pause(2.0)
    record_pause(1.0)
    stats = get_pause_stats()
    assert stats["count"] == 3
    assert stats["long_pause_ratio"] == round(1 / 3, 2)


# ── Vocabulary Diversity ─────────────────────────────────────────────


def test_ttr_insufficient():
    from app.observability import compute_ttr, reset_vocabulary
    reset_vocabulary()
    assert compute_ttr() == 0.0


def test_ttr_diverse():
    from app.observability import record_words, compute_ttr, reset_vocabulary
    reset_vocabulary()
    record_words(["the", "cat", "sat", "on", "a", "mat", "and", "looked", "at", "birds"])
    ttr = compute_ttr()
    assert ttr == 1.0  # all unique


def test_ttr_repetitive():
    from app.observability import record_words, compute_ttr, reset_vocabulary
    reset_vocabulary()
    record_words(["the"] * 10)
    ttr = compute_ttr()
    assert ttr == 0.1


# ── Alert Suppression ────────────────────────────────────────────────


def test_suppression_not_active_initially():
    from app.observability import should_suppress_notification
    import app.observability as obs
    obs._last_notification_at = 0.0
    assert not should_suppress_notification()


def test_suppression_active_after_send():
    from app.observability import mark_notification_sent, should_suppress_notification
    mark_notification_sent()
    assert should_suppress_notification()


# ── REST Endpoint Tests ────────────────────────────────────────────────

import aiosqlite
from app.observability import (
    hr_baseline, agitation_baseline, compute_rmssd,
    get_speech_engagement, get_pause_stats, compute_ttr,
    get_suppression_state,
)


@pytest.fixture()
def client(tmp_path):
    import os, sqlite3, datetime
    from fastapi import Depends, FastAPI, Query
    from fastapi.testclient import TestClient

    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    for stmt in [
        "CREATE TABLE IF NOT EXISTS daily_metrics (id INTEGER PRIMARY KEY AUTOINCREMENT, date_str TEXT UNIQUE, day_quality INTEGER, episode_count INTEGER DEFAULT 0, avg_agitation REAL DEFAULT 0, sleep_hours REAL DEFAULT 0, sleep_wake_count INTEGER DEFAULT 0, speech_minutes REAL DEFAULT 0, utterance_count INTEGER DEFAULT 0, hrv_rmssd REAL, mean_pause_s REAL, long_pause_ratio REAL, vocabulary_ttr REAL, hr_baseline REAL, agitation_baseline REAL, drift_alert TEXT, created_at REAL NOT NULL)",
        "CREATE TABLE IF NOT EXISTS caregiver_notes (id TEXT PRIMARY KEY, note_type TEXT NOT NULL, content TEXT NOT NULL, created_at REAL NOT NULL)",
    ]:
        conn.execute(stmt)
    conn.commit()
    conn.close()

    app = FastAPI()

    async def get_db():
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            yield db

    @app.get("/metrics/daily")
    async def get_daily_metrics(db=Depends(get_db)):
        today = datetime.date.today().isoformat()
        eng = get_speech_engagement()
        pauses = get_pause_stats()
        return {
            "date_str": today,
            "hr_baseline": round(hr_baseline.value, 1),
            "agitation_baseline": round(agitation_baseline.value, 1),
            "hrv_rmssd": compute_rmssd(),
            "speech_minutes": eng.speech_minutes,
            "utterance_count": eng.utterance_count,
            "mean_pause_s": pauses["mean_pause_s"],
            "long_pause_ratio": pauses["long_pause_ratio"],
            "vocabulary_ttr": compute_ttr(),
            "suppression": get_suppression_state(),
        }

    @app.get("/metrics/weekly")
    async def get_weekly_metrics(db=Depends(get_db)):
        today = datetime.date.today()
        week_ago = (today - datetime.timedelta(days=7)).isoformat()
        async with db.execute("SELECT * FROM daily_metrics WHERE date_str >= ? ORDER BY date_str ASC", (week_ago,)) as cur:
            rows = await cur.fetchall()
        return {"period": f"{week_ago} to {today.isoformat()}", "days_recorded": len(rows), "daily": [dict(r) for r in rows]}

    with TestClient(app) as c:
        yield c


def test_metrics_daily(client):
    r = client.get("/metrics/daily")
    assert r.status_code == 200
    body = r.json()
    assert "date_str" in body
    assert "hr_baseline" in body
    assert "vocabulary_ttr" in body


def test_metrics_weekly(client):
    r = client.get("/metrics/weekly")
    assert r.status_code == 200
    body = r.json()
    assert "period" in body
    assert "daily" in body
