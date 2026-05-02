"""Tests for perception cache and TTS phrase cache.

Run with:
    pytest tests/test_caching_tts.py -v
"""

from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Perception cache tests ────────────────────────────────────────────


def _make_snap(**overrides):
    """Build a minimal SensorSnapshot for cache key testing."""
    from app.models import IMUFeatures, HRState, TouchState, SensorSnapshot
    defaults = dict(
        imu=IMUFeatures(jerk_magnitude=0.1, stillness_duration_s=120.0),
        hr=HRState(bpm=72, valid=True, baseline_bpm=72.0, elevation_pct=0.0),
        touch=TouchState(any_contact=True, squeeze_intensity=0.1),
    )
    defaults.update(overrides)
    return SensorSnapshot(**defaults)


def test_quantize_key_stable_for_same_input():
    from app.agents.perception import _quantize_key
    snap = _make_snap()
    assert _quantize_key(snap) == _quantize_key(snap)


def test_quantize_key_same_within_bucket():
    """Small HR changes within the 5bpm bucket produce the same key."""
    from app.agents.perception import _quantize_key
    from app.models import HRState
    snap1 = _make_snap(hr=HRState(bpm=71, valid=True, baseline_bpm=72.0, elevation_pct=0.0))
    snap2 = _make_snap(hr=HRState(bpm=72, valid=True, baseline_bpm=72.0, elevation_pct=0.0))
    assert _quantize_key(snap1) == _quantize_key(snap2)


def test_quantize_key_differs_across_buckets():
    """Large HR change crosses bucket boundary → different key."""
    from app.agents.perception import _quantize_key
    from app.models import HRState
    snap_low = _make_snap(hr=HRState(bpm=72, valid=True, baseline_bpm=72.0, elevation_pct=0.0))
    snap_high = _make_snap(hr=HRState(bpm=95, valid=True, baseline_bpm=72.0, elevation_pct=30.0))
    assert _quantize_key(snap_low) != _quantize_key(snap_high)


def test_quantize_key_speech_changes_key():
    from app.agents.perception import _quantize_key
    snap_silent = _make_snap()
    snap_speech = _make_snap(speech_text="I want to go home")
    assert _quantize_key(snap_silent) != _quantize_key(snap_speech)


def test_perception_cache_lru_eviction():
    from app.agents.perception import _cache, _CACHE_MAX, clear_perception_cache
    clear_perception_cache()
    for i in range(_CACHE_MAX + 10):
        _cache[f"key_{i}"] = f"value_{i}"
        if len(_cache) > _CACHE_MAX:
            _cache.popitem(last=False)
    assert len(_cache) == _CACHE_MAX
    assert "key_0" not in _cache
    assert f"key_{_CACHE_MAX + 9}" in _cache
    clear_perception_cache()


# ── TTS phrase cache tests ────────────────────────────────────────────


def test_phrase_cache_path_deterministic():
    from app.tts import _phrase_cache_path
    p1 = _phrase_cache_path("Hello world")
    p2 = _phrase_cache_path("Hello world")
    assert p1 == p2


def test_phrase_cache_path_case_insensitive():
    from app.tts import _phrase_cache_path
    p1 = _phrase_cache_path("I'm right here with you.")
    p2 = _phrase_cache_path("i'm right here with you.")
    assert p1 == p2


def test_phrase_cache_path_different_text():
    from app.tts import _phrase_cache_path
    p1 = _phrase_cache_path("Hello")
    p2 = _phrase_cache_path("Goodbye")
    assert p1 != p2


@pytest.mark.asyncio
async def test_stream_tts_cache_hit(tmp_path):
    """When a cached file exists, stream_tts yields from disk without calling Cartesia."""
    from app import tts
    original_cache_dir = tts.CACHE_DIR
    tts.CACHE_DIR = tmp_path

    try:
        # Pre-populate cache
        text = "Test phrase"
        cache_path = tts._phrase_cache_path(text)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        fake_audio = b"\x00\x01" * 2048
        cache_path.write_bytes(fake_audio)

        # Stream should yield from cache, not call Cartesia
        chunks = []
        async for chunk in tts.stream_tts(text):
            chunks.append(chunk)

        result = b"".join(chunks)
        assert result == fake_audio
    finally:
        tts.CACHE_DIR = original_cache_dir


@pytest.mark.asyncio
async def test_stream_tts_cache_miss_calls_cartesia(tmp_path):
    """On cache miss, stream_tts calls Cartesia and saves to cache."""
    from app import tts
    original_cache_dir = tts.CACHE_DIR
    tts.CACHE_DIR = tmp_path

    fake_audio = b"\xaa\xbb" * 1000

    # Mock httpx async streaming
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.aiter_bytes = MagicMock(return_value=_async_iter([fake_audio]))

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_stream_ctx = AsyncMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_client.stream = MagicMock(return_value=mock_stream_ctx)

    try:
        with patch("app.tts.httpx.AsyncClient", return_value=mock_client):
            chunks = []
            async for chunk in tts.stream_tts("Novel phrase"):
                chunks.append(chunk)

        result = b"".join(chunks)
        assert result == fake_audio

        # Verify it was cached
        cache_path = tts._phrase_cache_path("Novel phrase")
        assert cache_path.exists()
        assert cache_path.read_bytes() == fake_audio
    finally:
        tts.CACHE_DIR = original_cache_dir


def test_clear_tts_cache(tmp_path):
    from app import tts
    original_cache_dir = tts.CACHE_DIR
    tts.CACHE_DIR = tmp_path

    try:
        tmp_path.mkdir(parents=True, exist_ok=True)
        (tmp_path / "test.pcm").write_bytes(b"\x00")
        assert len(list(tmp_path.glob("*.pcm"))) == 1
        tts.clear_tts_cache()
        assert len(list(tmp_path.glob("*.pcm"))) == 0
    finally:
        tts.CACHE_DIR = original_cache_dir


# ── Helper ────────────────────────────────────────────────────────────


async def _async_iter(items):
    for item in items:
        yield item
