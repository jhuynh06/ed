"""Streaming TTS via Cartesia with phrase cache for common utterances.

Common reassurance phrases are pre-generated and cached on disk.
Novel speech streams from Cartesia in real-time, yielding PCM chunks
as they arrive so the ESP32 can start playing immediately.
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import AsyncIterator

import httpx

logger = logging.getLogger(__name__)

CARTESIA_API_KEY = os.environ.get("CARTESIA_API_KEY", "")
CARTESIA_URL = "https://api.cartesia.ai/tts/bytes"
CARTESIA_VERSION = "2024-06-10"
VOICE_ID = os.environ.get("CARTESIA_VOICE_ID", "")
SAMPLE_RATE = 16000  # 16kHz mono PCM s16le — what ESP32 MAX98357A expects
CHUNK_SIZE = 4096  # bytes per yielded chunk

CACHE_DIR = Path(os.environ.get("TTS_CACHE_DIR", "tts_cache"))

# Phrases Ed says often — pre-generate these on first use
COMMON_PHRASES = [
    "I'm right here with you.",
    "Let's breathe together.",
    "Everything's okay.",
    "You're safe. I'm here.",
    "Let's take a slow breath in, and out.",
    "I'm not going anywhere.",
    "You're doing great.",
    "It's okay to rest now.",
]


def _phrase_cache_path(text: str) -> Path:
    key = hashlib.md5(text.strip().lower().encode()).hexdigest()
    return CACHE_DIR / f"{key}.pcm"


def _cartesia_headers() -> dict:
    return {
        "X-API-Key": CARTESIA_API_KEY,
        "Cartesia-Version": CARTESIA_VERSION,
        "Content-Type": "application/json",
    }


def _cartesia_payload(text: str) -> dict:
    return {
        "model_id": "sonic-english",
        "transcript": text,
        "voice": {"mode": "id", "id": VOICE_ID},
        "output_format": {
            "container": "raw",
            "encoding": "pcm_s16le",
            "sample_rate": SAMPLE_RATE,
        },
    }


async def stream_tts(text: str) -> AsyncIterator[bytes]:
    """Yield PCM audio chunks for the given text.

    Checks the phrase cache first. On miss, streams from Cartesia
    and saves to cache for next time.
    """
    cache_path = _phrase_cache_path(text)

    # Cache hit — yield from disk
    if cache_path.exists():
        logger.debug("TTS cache hit: %s", text[:40])
        data = cache_path.read_bytes()
        for i in range(0, len(data), CHUNK_SIZE):
            yield data[i : i + CHUNK_SIZE]
        return

    # Cache miss — stream from Cartesia, save to cache
    logger.info("TTS cache miss, streaming from Cartesia: %s", text[:40])
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    collected = bytearray()

    async with httpx.AsyncClient(timeout=30) as client:
        async with client.stream(
            "POST",
            CARTESIA_URL,
            headers=_cartesia_headers(),
            json=_cartesia_payload(text),
        ) as resp:
            resp.raise_for_status()
            async for chunk in resp.aiter_bytes(CHUNK_SIZE):
                collected.extend(chunk)
                yield chunk

    # Save to cache after full response
    cache_path.write_bytes(bytes(collected))
    logger.debug("TTS cached: %s (%d bytes)", text[:40], len(collected))


async def warm_phrase_cache() -> int:
    """Pre-generate common phrases. Call at startup. Returns count cached."""
    count = 0
    for phrase in COMMON_PHRASES:
        path = _phrase_cache_path(phrase)
        if path.exists():
            count += 1
            continue
        try:
            chunks = []
            async for chunk in stream_tts(phrase):
                chunks.append(chunk)
            count += 1
        except Exception as e:
            logger.warning("Failed to pre-cache phrase %r: %s", phrase[:30], e)
    return count


def get_cached_phrases() -> list[str]:
    """Return list of phrases currently in cache."""
    return [p for p in COMMON_PHRASES if _phrase_cache_path(p).exists()]


def clear_tts_cache() -> None:
    """Remove all cached TTS files."""
    if CACHE_DIR.exists():
        for f in CACHE_DIR.glob("*.pcm"):
            f.unlink()
