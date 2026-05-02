"""Unit tests for acoustic_features, nlp_features, session_store, cdr_mapping."""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import types
from dataclasses import asdict
from unittest.mock import MagicMock

import numpy as np
import pytest

# Force real librosa and sentence_transformers into sys.modules BEFORE any stub can register
import librosa  # noqa: F401
import sentence_transformers  # noqa: F401

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Stub sentence_transformers before nlp_features imports it
st_stub = types.ModuleType("sentence_transformers")
mock_model = MagicMock()
mock_model.encode = MagicMock(return_value=np.array([0.1] * 384))
st_stub.SentenceTransformer = MagicMock(return_value=mock_model)
sys.modules.setdefault("sentence_transformers", st_stub)

from app.acoustic_features import AcousticExtractor, AcousticFeatures  # noqa: E402
from app.nlp_features import NLPExtractor, NLPFeatures  # noqa: E402
from app.session_store import SessionStore, SessionFeatures, FeatureDelta  # noqa: E402
from app.cdr_mapping import map_to_cdr, CDRScores  # noqa: E402

SR = 16_000


def sine(freq: float = 220.0, duration: float = 1.0) -> np.ndarray:
    t = np.linspace(0, duration, int(SR * duration))
    return (np.sin(2 * np.pi * freq * t) * 0.5).astype(np.float32)


def silence(duration: float = 0.5) -> np.ndarray:
    return np.zeros(int(SR * duration), dtype=np.float32)


# ── AcousticExtractor ─────────────────────────────────────────────────

def test_acoustic_empty_returns_zeros():
    ex = AcousticExtractor()
    result = ex.extract(np.array([], dtype=np.float32))
    assert result.f0_mean == 0.0
    assert result.speaking_rate == 0.0


def test_acoustic_sine_has_nonzero_f0():
    ex = AcousticExtractor()
    result = ex.extract(sine(220.0, 1.0))
    # librosa.yin should detect ~220Hz
    assert result.f0_mean > 0


def test_acoustic_silence_returns_zeros():
    ex = AcousticExtractor()
    result = ex.extract(silence(1.0))
    assert result.f0_mean == 0.0


def test_acoustic_pause_detection():
    ex = AcousticExtractor()
    # speech + 500ms silence + speech — long enough for RMS threshold to register
    audio = np.concatenate([sine(220, 0.5), silence(0.5), sine(220, 0.5)])
    result = ex.extract(audio)
    assert result.pause_count >= 1


def test_acoustic_all_fields_present():
    ex = AcousticExtractor()
    result = ex.extract(sine(220, 1.0))
    d = asdict(result)
    assert all(k in d for k in ["f0_mean", "f0_std", "jitter", "shimmer",
                                  "speaking_rate", "pause_count", "pause_rate",
                                  "mean_pause_duration", "hnr"])


# ── NLPExtractor ─────────────────────────────────────────────────────

def make_nlp() -> NLPExtractor:
    ex = NLPExtractor.__new__(NLPExtractor)
    ex._model = mock_model
    return ex


def test_nlp_empty_text_returns_zeros():
    ex = make_nlp()
    result = ex.extract("")
    assert result.type_token_ratio == 0.0
    assert result.word_count == 0
    assert result.embedding == []


def test_nlp_ttr_all_unique():
    ex = make_nlp()
    result = ex.extract("cat dog bird fish")
    assert result.type_token_ratio == pytest.approx(1.0)


def test_nlp_ttr_all_same():
    ex = make_nlp()
    result = ex.extract("the the the the")
    assert result.type_token_ratio == pytest.approx(0.25)


def test_nlp_filler_rate():
    ex = make_nlp()
    result = ex.extract("um I uh don't know like what to say")
    assert result.filler_rate > 0


def test_nlp_no_fillers():
    ex = make_nlp()
    result = ex.extract("The weather is beautiful today")
    assert result.filler_rate == 0.0


def test_nlp_topic_coherence_no_prev():
    ex = make_nlp()
    result = ex.extract("hello world")
    assert result.topic_coherence == pytest.approx(1.0)
    assert result.topic_drift == pytest.approx(0.0)


def test_nlp_topic_coherence_with_prev():
    ex = make_nlp()
    # Same embedding → coherence = 1.0
    prev = [0.1] * 384
    result = ex.extract("hello world", prev_embedding=prev)
    assert 0.0 <= result.topic_coherence <= 1.0


def test_nlp_sentence_count():
    ex = make_nlp()
    result = ex.extract("Hello. How are you? I am fine.")
    assert result.sentence_count == 3


# ── CDR mapping ───────────────────────────────────────────────────────

def zero_acoustic(**kwargs) -> AcousticFeatures:
    base = AcousticFeatures(f0_mean=150, f0_std=10, jitter=0.01, shimmer=0.05,
                             speaking_rate=3.0, pause_count=0, pause_rate=0.0,
                             mean_pause_duration=0.0, hnr=15.0)
    from dataclasses import replace
    return replace(base, **kwargs)


def zero_nlp(**kwargs) -> NLPFeatures:
    base = NLPFeatures(type_token_ratio=0.7, filler_rate=2.0, mean_utterance_length=8.0,
                       topic_coherence=0.8, topic_drift=0.2, word_count=20,
                       sentence_count=3, embedding=[0.1] * 384)
    from dataclasses import replace
    return replace(base, **kwargs)


def test_cdr_healthy_baseline_near_zero():
    scores = map_to_cdr(zero_acoustic(), zero_nlp())
    assert scores.total < 0.5
    assert scores.flags == []


def test_cdr_low_ttr_flags_commun():
    scores = map_to_cdr(zero_acoustic(), zero_nlp(type_token_ratio=0.25))
    assert scores.commun >= 1.0
    assert any("vocabulary" in f for f in scores.flags)


def test_cdr_high_filler_rate_flags_commun():
    scores = map_to_cdr(zero_acoustic(), zero_nlp(filler_rate=20.0))
    assert scores.commun >= 1.0
    assert any("filler" in f for f in scores.flags)


def test_cdr_low_topic_coherence_flags_orient():
    scores = map_to_cdr(zero_acoustic(), zero_nlp(topic_coherence=0.2, topic_drift=0.8))
    assert scores.orient >= 1.5
    assert any("topic drift" in f for f in scores.flags)


def test_cdr_high_pause_rate_flags_memory():
    scores = map_to_cdr(zero_acoustic(pause_rate=3.0), zero_nlp())
    assert scores.memory >= 0.5
    assert any("pausing" in f for f in scores.flags)


def test_cdr_poor_voice_quality_flags_judgment():
    scores = map_to_cdr(zero_acoustic(hnr=2.0, jitter=0.1, shimmer=0.2), zero_nlp())
    assert scores.judgment >= 1.0


def test_cdr_scores_clamped_to_3():
    # Pile on everything
    scores = map_to_cdr(
        zero_acoustic(hnr=1.0, jitter=0.2, shimmer=0.3, pause_rate=5.0, speaking_rate=0.5),
        zero_nlp(type_token_ratio=0.1, filler_rate=25.0, topic_coherence=0.1,
                 topic_drift=0.9, mean_utterance_length=1.0, word_count=3),
    )
    assert scores.commun <= 3.0
    assert scores.orient <= 3.0
    assert scores.memory <= 3.0
    assert scores.judgment <= 3.0


def test_cdr_prev_nlp_vocabulary_shrinking():
    prev = zero_nlp(type_token_ratio=0.8)
    curr_nlp = zero_nlp(type_token_ratio=0.5)  # dropped 0.3
    scores = map_to_cdr(zero_acoustic(), curr_nlp, prev_nlp=prev)
    assert scores.memory >= 1.0
    assert any("vocabulary shrinking" in f for f in scores.flags)


# ── SessionStore ──────────────────────────────────────────────────────

def make_session(session_id: str = "s1", timestamp: float = 1000.0, **kwargs) -> SessionFeatures:
    defaults = dict(f0_mean=150, f0_std=10, jitter=0.01, shimmer=0.05,
                    speaking_rate=3.0, pause_count=0, pause_rate=0.0, hnr=15.0,
                    type_token_ratio=0.7, filler_rate=2.0, mean_utterance_length=8.0,
                    topic_coherence=0.8, word_count=20,
                    cdr_commun=0.0, cdr_orient=0.0, cdr_memory=0.0, cdr_judgment=0.0)
    defaults.update(kwargs)
    return SessionFeatures(session_id=session_id, timestamp=timestamp, **defaults)


@pytest.fixture
def tmp_db(tmp_path):
    return str(tmp_path / "test.db")


def test_session_store_save_and_retrieve(tmp_db):
    async def run():
        store = SessionStore(tmp_db)
        await store.init()
        await store.save(make_session("s1", 1000.0))
        await store.save(make_session("s2", 2000.0))
        recent = await store.get_recent(10)
        assert len(recent) == 2
        assert recent[0].session_id == "s2"  # most recent first
    asyncio.run(run())


def test_session_store_delta_no_history(tmp_db):
    async def run():
        store = SessionStore(tmp_db)
        await store.init()
        current = make_session("s1", 1000.0, cdr_commun=1.0, cdr_memory=0.5)
        delta = await store.compute_delta(current, window=5)
        assert delta.window_size == 0
        assert delta.trend_direction == "stable"  # no history = stable
    asyncio.run(run())


def test_session_store_delta_declining_trend(tmp_db):
    async def run():
        store = SessionStore(tmp_db)
        await store.init()
        # Seed 5 healthy sessions
        for i in range(5):
            await store.save(make_session(f"s{i}", float(i * 100),
                                          cdr_commun=0.0, cdr_memory=0.0))
        # Current session shows significant CDR increase
        current = make_session("s6", 600.0, cdr_commun=1.5, cdr_memory=1.0)
        delta = await store.compute_delta(current, window=5)
        assert delta.trend_direction == "declining"
        assert delta.cdr_commun_delta > 0
    asyncio.run(run())


def test_session_store_get_recent_limit(tmp_db):
    async def run():
        store = SessionStore(tmp_db)
        await store.init()
        for i in range(10):
            await store.save(make_session(f"s{i}", float(i)))
        recent = await store.get_recent(3)
        assert len(recent) == 3
    asyncio.run(run())
