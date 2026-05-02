"""Observability metrics — EWMA baselines, sleep estimate, engagement,
day quality, behavioral drift, HRV, speech pause trends, vocabulary diversity,
and alert suppression.

All functions are pure computation over data from SQLite/in-memory buffers.
No LLM calls.
"""

from __future__ import annotations

import math
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field

# ── EWMA Baselines ───────────────────────────────────────────────────

EWMA_ALPHA = 0.2  # weight for new observation


@dataclass
class EWMABaseline:
    value: float = 0.0
    updated_at: float = 0.0

    def update(self, observation: float) -> float:
        if self.updated_at == 0.0:
            self.value = observation
        else:
            self.value = EWMA_ALPHA * observation + (1 - EWMA_ALPHA) * self.value
        self.updated_at = time.time()
        return self.value

    def deviation(self, observation: float) -> float:
        if self.updated_at == 0.0:
            return 0.0
        return observation - self.value


# Module-level baselines
hr_baseline = EWMABaseline()
agitation_baseline = EWMABaseline()


# ── HRV (RMSSD) from R-R intervals ──────────────────────────────────

_RR_MAX = 120  # ~2 minutes of beats at 60bpm
_rr_buffer: deque = deque(maxlen=_RR_MAX)


def push_rr_interval(rr_ms: float) -> None:
    """Add an R-R interval (milliseconds) to the rolling buffer."""
    _rr_buffer.append(rr_ms)


def compute_rmssd() -> float | None:
    """Compute RMSSD from buffered R-R intervals. Returns None if insufficient data."""
    if len(_rr_buffer) < 10:
        return None
    diffs = [_rr_buffer[i + 1] - _rr_buffer[i] for i in range(len(_rr_buffer) - 1)]
    return math.sqrt(sum(d * d for d in diffs) / len(diffs))


def clear_rr_buffer() -> None:
    _rr_buffer.clear()


# ── Sleep Estimate ───────────────────────────────────────────────────

@dataclass
class SleepEstimate:
    total_hours: float = 0.0
    wake_count: int = 0
    sleep_efficiency_pct: float = 0.0
    estimated: bool = True  # always True — no dedicated sleep sensor


def estimate_sleep(
    stillness_periods: list[tuple[float, float]],  # (start_ts, end_ts) of IMU stillness
    night_start_hour: int = 22,
    night_end_hour: int = 7,
) -> SleepEstimate:
    """Estimate sleep from IMU stillness periods during nighttime hours."""
    night_minutes = 0.0
    sleep_minutes = 0.0
    wake_transitions = 0
    was_still = False

    for start, end in stillness_periods:
        h_start = time.localtime(start).tm_hour
        h_end = time.localtime(end).tm_hour
        # Check if period overlaps nighttime
        in_night = (h_start >= night_start_hour or h_start < night_end_hour or
                    h_end >= night_start_hour or h_end < night_end_hour)
        if not in_night:
            continue
        duration_min = (end - start) / 60.0
        if duration_min >= 5:  # 5+ min stillness = sleep
            sleep_minutes += duration_min
            if not was_still:
                was_still = True
        else:
            if was_still:
                wake_transitions += 1
                was_still = False

    night_minutes = (night_end_hour + 24 - night_start_hour) * 60.0
    efficiency = (sleep_minutes / night_minutes * 100) if night_minutes > 0 else 0.0

    return SleepEstimate(
        total_hours=round(sleep_minutes / 60, 1),
        wake_count=wake_transitions,
        sleep_efficiency_pct=round(min(efficiency, 100.0), 1),
    )


# ── Speech Engagement ────────────────────────────────────────────────

@dataclass
class SpeechEngagement:
    speech_minutes: float = 0.0
    utterance_count: int = 0


_speech_segments: list[float] = []  # durations in seconds


def record_speech_segment(duration_s: float) -> None:
    _speech_segments.append(duration_s)


def get_speech_engagement() -> SpeechEngagement:
    total = sum(_speech_segments)
    return SpeechEngagement(
        speech_minutes=round(total / 60, 1),
        utterance_count=len(_speech_segments),
    )


def reset_speech_engagement() -> None:
    _speech_segments.clear()


# ── Day Quality Score ────────────────────────────────────────────────

def compute_day_quality(
    episode_count: int,
    avg_agitation: float,
    sleep_hours: float,
    speech_minutes: float,
) -> int:
    """1-5 day quality score. 5 = great day, 1 = very difficult day."""
    score = 5.0
    # Episodes penalize
    score -= min(episode_count * 0.8, 2.5)
    # High average agitation penalizes
    score -= min(avg_agitation / 40, 1.5)
    # Poor sleep penalizes
    if sleep_hours < 5:
        score -= 1.0
    elif sleep_hours < 6:
        score -= 0.5
    # Low engagement penalizes
    if speech_minutes < 5:
        score -= 0.5
    return max(1, min(5, round(score)))


# ── Behavioral Drift ────────────────────────────────────────────────

@dataclass
class DriftAlert:
    triggered: bool = False
    message: str = ""
    metric: str = ""
    days: int = 0


def check_behavioral_drift(
    daily_scores: list[float],  # last N days of avg agitation scores
    threshold_days: int = 3,
    threshold_pct: float = 30.0,
) -> DriftAlert:
    """Alert if agitation has been elevated above baseline for N consecutive days."""
    if len(daily_scores) < threshold_days + 3:
        return DriftAlert()
    baseline = sum(daily_scores[:-threshold_days]) / len(daily_scores[:-threshold_days])
    recent = daily_scores[-threshold_days:]
    if baseline == 0:
        return DriftAlert()
    all_elevated = all((s - baseline) / max(baseline, 1) * 100 > threshold_pct for s in recent)
    if all_elevated:
        return DriftAlert(
            triggered=True,
            message=f"Agitation has been elevated for {threshold_days} consecutive days — this may warrant attention.",
            metric="agitation",
            days=threshold_days,
        )
    return DriftAlert()


# ── Speech Pause Tracking ───────────────────────────────────────────

_pause_durations: list[float] = []  # seconds


def record_pause(duration_s: float) -> None:
    _pause_durations.append(duration_s)


def get_pause_stats() -> dict:
    if not _pause_durations:
        return {"mean_pause_s": 0.0, "long_pause_ratio": 0.0, "count": 0}
    mean = sum(_pause_durations) / len(_pause_durations)
    long = sum(1 for p in _pause_durations if p > 1.5)
    return {
        "mean_pause_s": round(mean, 2),
        "long_pause_ratio": round(long / len(_pause_durations), 2),
        "count": len(_pause_durations),
    }


def reset_pauses() -> None:
    _pause_durations.clear()


# ── Vocabulary Diversity ─────────────────────────────────────────────

_word_buffer: list[str] = []


def record_words(words: list[str]) -> None:
    _word_buffer.extend(w.lower().strip(".,!?;:") for w in words if w.strip())


def compute_ttr() -> float:
    """Type-token ratio. 0-1, higher = more diverse vocabulary."""
    if len(_word_buffer) < 10:
        return 0.0
    return round(len(set(_word_buffer)) / len(_word_buffer), 3)


def reset_vocabulary() -> None:
    _word_buffer.clear()


# ── Alert Suppression ────────────────────────────────────────────────

_last_notification_at: float = 0.0
SUPPRESSION_WINDOW_S = 2 * 3600  # 2 hours


def should_suppress_notification() -> bool:
    return (time.time() - _last_notification_at) < SUPPRESSION_WINDOW_S


def mark_notification_sent() -> None:
    global _last_notification_at
    _last_notification_at = time.time()


def get_suppression_state() -> dict:
    remaining = max(0, SUPPRESSION_WINDOW_S - (time.time() - _last_notification_at))
    return {"suppressed": should_suppress_notification(), "remaining_s": round(remaining)}
