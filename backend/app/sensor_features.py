"""
sensor_features.py — Computes derived IMU and touch features from raw sensor data.

The ESP32 sends raw accelerometer XYZ (in g) and active touch pad indices.
This module maintains state across frames and produces the higher-level
features (jerk, fall detection, rocking, etc.) that the rest of the
backend expects.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field


@dataclass
class SensorFeatures:
    """Derived features computed from raw sensor frames."""

    # IMU
    jerk_magnitude: float = 0.0
    fall_detected: bool = False
    hug_detected: bool = False
    rocking_detected: bool = False
    tremor_power: float = 0.0
    stillness_duration_s: float = 0.0

    # Touch
    any_contact: bool = False
    squeeze_intensity: float = 0.0
    petting_detected: bool = False
    grip_duration_s: float = 0.0
    active_pads: list[int] = field(default_factory=list)


class SensorFeatureComputer:
    """Stateful processor that turns raw sensor frames into derived features."""

    TOUCH_PAD_COUNT = 8

    # Thresholds
    FALL_JERK_THRESHOLD = 2.5
    FALL_HOLD_S = 1.0
    STILLNESS_JERK_THRESHOLD = 0.02
    ROCKING_MIN_CROSSINGS = 6
    ROCKING_JERK_MIN = 0.05
    ROCKING_JERK_MAX = 0.8
    PETTING_MIN_ACTIVATIONS = 3
    PETTING_WINDOW_S = 1.0
    PETTING_DECAY_S = 1.5

    def __init__(self) -> None:
        # IMU state
        self._prev_mag: float | None = None
        self._jerk_smoothed: float = 0.0
        self._stillness_start: float = time.monotonic()
        self._mag_history: list[float] = []
        self._mag_history_size: int = 20

        # Fall state
        self._fall_trigger_time: float = 0.0
        self._fall_armed: bool = False

        # Touch state
        self._touch_start: float | None = None
        self._last_activation_time: float = 0.0
        self._sequential_activations: int = 0
        self._prev_active_pads: set[int] = set()

    def update(self, imu_raw: dict, touch_raw: dict) -> SensorFeatures:
        """Process one sensor frame and return derived features."""
        now = time.monotonic()

        # ── IMU ──────────────────────────────────────────────
        ax = imu_raw.get("ax", 0.0)
        ay = imu_raw.get("ay", 0.0)
        az = imu_raw.get("az", 0.0)

        mag = math.sqrt(ax * ax + ay * ay + az * az)

        # Compute jerk (only with a valid previous reading)
        jerk = 0.0
        if self._prev_mag is not None and mag > 0.001:
            jerk = abs(mag - self._prev_mag)

        if mag > 0.001:
            self._prev_mag = mag
        else:
            # Zero read — don't update prev_mag, skip derived features
            self._prev_mag = None

        self._jerk_smoothed = self._jerk_smoothed * 0.7 + jerk * 0.3

        # Stillness
        if self._jerk_smoothed < self.STILLNESS_JERK_THRESHOLD:
            stillness_s = now - self._stillness_start
        else:
            self._stillness_start = now
            stillness_s = 0.0

        # Fall detection — edge-triggered with hold
        if jerk > self.FALL_JERK_THRESHOLD:
            self._fall_trigger_time = now
            self._fall_armed = True

        if self._fall_armed and (now - self._fall_trigger_time) >= self.FALL_HOLD_S:
            self._fall_armed = False

        fall_detected = self._fall_armed

        # Rocking detection via zero-crossings on magnitude deviation
        self._mag_history.append(mag - 1.0)
        if len(self._mag_history) > self._mag_history_size:
            self._mag_history.pop(0)

        zero_crossings = 0
        for i in range(1, len(self._mag_history)):
            if (self._mag_history[i - 1] >= 0) != (self._mag_history[i] >= 0):
                zero_crossings += 1

        rocking = (
            zero_crossings >= self.ROCKING_MIN_CROSSINGS
            and self.ROCKING_JERK_MIN < self._jerk_smoothed < self.ROCKING_JERK_MAX
        )

        # Hug detection
        hug = abs(ax) > 0.3 and abs(ay) > 0.3 and stillness_s > 1.5

        # ── Touch ────────────────────────────────────────────
        active_pads: list[int] = touch_raw.get("pads", [])
        active_set = set(active_pads)
        pad_count = len(active_pads)

        any_contact = pad_count > 0
        squeeze = pad_count / self.TOUCH_PAD_COUNT

        # Grip duration
        if any_contact:
            if self._touch_start is None:
                self._touch_start = now
            grip_s = now - self._touch_start
        else:
            self._touch_start = None
            grip_s = 0.0

        # Petting: sequential new pad activations
        new_pads = active_set - self._prev_active_pads
        if new_pads:
            if (now - self._last_activation_time) < 0.5:
                self._sequential_activations += len(new_pads)
            else:
                self._sequential_activations = len(new_pads)
            self._last_activation_time = now

        petting = (
            self._sequential_activations >= self.PETTING_MIN_ACTIVATIONS
            and (now - self._last_activation_time) < self.PETTING_WINDOW_S
        )

        if (now - self._last_activation_time) > self.PETTING_DECAY_S:
            self._sequential_activations = 0

        self._prev_active_pads = active_set

        return SensorFeatures(
            jerk_magnitude=self._jerk_smoothed,
            fall_detected=fall_detected,
            hug_detected=hug,
            rocking_detected=rocking,
            tremor_power=0.0,
            stillness_duration_s=stillness_s,
            any_contact=any_contact,
            squeeze_intensity=squeeze,
            petting_detected=petting,
            grip_duration_s=grip_s,
            active_pads=active_pads,
        )
