from __future__ import annotations

import datetime
from collections import deque
from dataclasses import dataclass

import numpy as np


@dataclass
class AnomalyResult:
    is_anomaly: bool
    z_score: float
    metric: str    # 'agitation' | 'hr' | 'combined'
    severity: str  # 'normal' | 'elevated' | 'critical'
    message: str


def _z_score(values: deque, current: float) -> float:
    arr = np.array(values)
    std = arr.std()
    if std < 1e-6:
        return 0.0
    return float((current - arr.mean()) / std)


def _severity(z: float, enough_data: bool) -> str:
    if not enough_data:
        return "normal"
    if abs(z) > 3.0:
        return "critical"
    if abs(z) > 2.0:
        return "elevated"
    return "normal"


def _unusual_hour() -> bool:
    hour = datetime.datetime.now().hour
    return 0 <= hour < 5


class BaselineTracker:
    def __init__(self, window: int = 50) -> None:
        self._window = window
        self._agitation: deque[float] = deque(maxlen=window)
        self._hr: deque[float] = deque(maxlen=window)

    def update(self, agitation: float, hr_bpm: float | None = None) -> AnomalyResult:
        enough = len(self._agitation) >= 10

        # Compute z-scores before appending so current value isn't in baseline
        ag_z = _z_score(self._agitation, agitation) if enough else 0.0
        hr_z = 0.0
        if hr_bpm is not None and len(self._hr) >= 10:
            hr_z = _z_score(self._hr, hr_bpm)

        self._agitation.append(agitation)
        if hr_bpm is not None:
            self._hr.append(hr_bpm)

        # Pick dominant metric
        if abs(hr_z) > abs(ag_z) and hr_bpm is not None:
            z, metric = hr_z, "hr"
        elif hr_bpm is not None and abs(ag_z) > 0 and abs(hr_z) > 0:
            z, metric = (ag_z + hr_z) / 2, "combined"
        else:
            z, metric = ag_z, "agitation"

        severity = _severity(z, enough)
        is_anomaly = enough and abs(z) > 2.0

        if not enough:
            message = f"Insufficient baseline ({len(self._agitation)} samples)"
        elif metric == "hr":
            message = f"HR {abs(z):.1f} std devs {'above' if z > 0 else 'below'} baseline"
        elif metric == "combined":
            message = f"Combined anomaly {abs(z):.1f} std devs from baseline"
        else:
            msg = f"Agitation {abs(ag_z):.1f} std devs above baseline"
            if ag_z > 3.0 and _unusual_hour():
                msg += " at an unusual hour"
            message = msg

        return AnomalyResult(
            is_anomaly=is_anomaly,
            z_score=round(z, 4),
            metric=metric,
            severity=severity,
            message=message,
        )


_tracker = BaselineTracker()


def check_anomaly(agitation: float, hr_bpm: float | None = None) -> AnomalyResult:
    return _tracker.update(agitation, hr_bpm)
