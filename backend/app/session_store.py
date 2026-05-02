from dataclasses import dataclass, fields, astuple
from typing import Optional

import aiosqlite
import numpy as np


@dataclass
class SessionFeatures:
    session_id: str
    timestamp: float
    f0_mean: float
    f0_std: float
    jitter: float
    shimmer: float
    speaking_rate: float
    pause_count: int
    pause_rate: float
    hnr: float
    type_token_ratio: float
    filler_rate: float
    mean_utterance_length: float
    topic_coherence: float
    word_count: int
    cdr_commun: float
    cdr_orient: float
    cdr_memory: float
    cdr_judgment: float


@dataclass
class FeatureDelta:
    """Change in features over a sliding window of N sessions."""
    window_size: int
    f0_mean_delta: float
    speaking_rate_delta: float
    type_token_ratio_delta: float
    filler_rate_delta: float
    topic_coherence_delta: float
    cdr_commun_delta: float
    cdr_memory_delta: float
    trend_direction: str  # 'improving' | 'stable' | 'declining'


_COLS = [f.name for f in fields(SessionFeatures)]
_CREATE = f"""
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    {', '.join(f'{c} REAL' if c not in ('session_id',) else f'{c} TEXT' for c in _COLS)}
)
"""


class SessionStore:
    def __init__(self, db_path: str = "sessions.db") -> None:
        self.db_path = db_path

    async def init(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(_CREATE)
            await db.commit()

    async def save(self, features: SessionFeatures) -> None:
        placeholders = ", ".join("?" * len(_COLS))
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"INSERT INTO sessions ({', '.join(_COLS)}) VALUES ({placeholders})",
                astuple(features),
            )
            await db.commit()

    async def get_recent(self, n: int = 10) -> list[SessionFeatures]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                f"SELECT {', '.join(_COLS)} FROM sessions ORDER BY timestamp DESC LIMIT ?", (n,)
            ) as cursor:
                rows = await cursor.fetchall()
        return [SessionFeatures(*row) for row in rows]

    async def compute_delta(self, current: SessionFeatures, window: int = 5) -> FeatureDelta:
        recent = await self.get_recent(window)

        delta_fields = ("f0_mean", "speaking_rate", "type_token_ratio",
                        "filler_rate", "topic_coherence", "cdr_commun", "cdr_memory")

        if recent:
            arr = np.array([[getattr(s, f) for f in delta_fields] for s in recent])
            means = arr.mean(axis=0)
        else:
            # No history — deltas are meaningless, return stable
            return FeatureDelta(
                window_size=0,
                f0_mean_delta=0.0, speaking_rate_delta=0.0,
                type_token_ratio_delta=0.0, filler_rate_delta=0.0,
                topic_coherence_delta=0.0, cdr_commun_delta=0.0,
                cdr_memory_delta=0.0, trend_direction="stable",
            )

        deltas = {f: float(getattr(current, f)) - float(means[i]) for i, f in enumerate(delta_fields)}

        cdr_sum = deltas["cdr_commun"] + deltas["cdr_memory"]
        trend = "declining" if cdr_sum > 0.2 else ("improving" if cdr_sum < -0.2 else "stable")

        return FeatureDelta(
            window_size=len(recent),
            f0_mean_delta=deltas["f0_mean"],
            speaking_rate_delta=deltas["speaking_rate"],
            type_token_ratio_delta=deltas["type_token_ratio"],
            filler_rate_delta=deltas["filler_rate"],
            topic_coherence_delta=deltas["topic_coherence"],
            cdr_commun_delta=deltas["cdr_commun"],
            cdr_memory_delta=deltas["cdr_memory"],
            trend_direction=trend,
        )


_store: SessionStore | None = None


async def get_store(db_path: str = "sessions.db") -> SessionStore:
    global _store
    if _store is None:
        _store = SessionStore(db_path)
        await _store.init()
    return _store
