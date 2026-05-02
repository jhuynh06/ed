from dataclasses import dataclass
from collections import defaultdict
import time
import numpy as np


@dataclass
class SundowningStatus:
    is_sundowning_window: bool
    preemptive_flag: bool
    risk_multiplier: float
    pattern_confidence: float
    peak_hour: int | None
    message: str


class SundowningDetector:
    def __init__(self) -> None:
        self._hourly: dict[int, list[float]] = defaultdict(list)

    def record(self, agitation: float, hour: int | None = None) -> None:
        self._hourly[hour if hour is not None else time.localtime().tm_hour].append(agitation)

    def status(self, hour: int | None = None) -> SundowningStatus:
        current_hour = hour if hour is not None else time.localtime().tm_hour

        means = {h: float(np.mean(scores)) for h, scores in self._hourly.items() if len(scores) >= 3}
        total_readings = sum(len(v) for v in self._hourly.values())
        pattern_confidence = min(total_readings / 20.0, 1.0)

        peak_hour: int | None = max(means, key=lambda h: means[h]) if means else None

        is_sundowning_window = False
        preemptive_flag = False

        if peak_hour is not None and 13 <= peak_hour <= 20 and means[peak_hour] > 45:
            window = {(peak_hour - 1) % 24, peak_hour % 24, (peak_hour + 1) % 24, (peak_hour + 2) % 24}
            is_sundowning_window = current_hour in window
            preemptive_flag = current_hour == (peak_hour - 1) % 24

        if is_sundowning_window:
            risk_multiplier = 1.5
            message = f"Currently in sundowning window (peak hour {peak_hour}:00, confidence {pattern_confidence:.0%})."
        elif preemptive_flag:
            risk_multiplier = 1.3
            message = f"Approaching sundowning window in ~1 hour (peak hour {peak_hour}:00, confidence {pattern_confidence:.0%})."
        else:
            risk_multiplier = 1.0
            message = "No sundowning pattern active." if peak_hour is None else f"Outside sundowning window (peak hour {peak_hour}:00, confidence {pattern_confidence:.0%})."

        return SundowningStatus(
            is_sundowning_window=is_sundowning_window,
            preemptive_flag=preemptive_flag,
            risk_multiplier=risk_multiplier,
            pattern_confidence=pattern_confidence,
            peak_hour=peak_hour,
            message=message,
        )


_detector = SundowningDetector()


def record_agitation(agitation: float, hour: int | None = None) -> None:
    _detector.record(agitation, hour)


def get_sundowning_status(hour: int | None = None) -> SundowningStatus:
    return _detector.status(hour)
