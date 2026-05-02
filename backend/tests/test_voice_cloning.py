"""Tests for Cartesia voice cloning feature.

Run with:
    pytest tests/test_voice_cloning.py -v
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── clone_voice tests ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_clone_voice_success(tmp_path):
    """clone_voice sends audio to Cartesia and returns voice_id."""
    from app import tts
    
    # Create a fake audio file
    audio_file = tmp_path / "test_clip.wav"
    audio_file.write_bytes(b"RIFF" + b"\x00" * 100)  # Minimal WAV-like content
    
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "id": "voice_abc123",
        "name": "Test Voice",
        "user_id": "user_123",
        "is_public": False,
        "description": "",
        "created_at": "2024-01-01T00:00:00Z",
        "language": "en",
    })
    
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)
    
    with patch("app.tts.httpx.AsyncClient", return_value=mock_client):
        voice_id = await tts.clone_voice(audio_file, "Grandson Jake")
    
    assert voice_id == "voice_abc123"
    
    # Verify the API was called correctly
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert call_args[0][0] == "https://api.cartesia.ai/voices/clone"
    assert "Authorization" in call_args[1]["headers"]


@pytest.mark.asyncio
async def test_clone_voice_file_not_found():
    """clone_voice raises FileNotFoundError for missing audio."""
    from app import tts
    
    with pytest.raises(FileNotFoundError):
        await tts.clone_voice("/nonexistent/path.wav", "Test")


@pytest.mark.asyncio
async def test_clone_voice_with_description(tmp_path):
    """clone_voice includes description in API call when provided."""
    from app import tts
    
    audio_file = tmp_path / "clip.wav"
    audio_file.write_bytes(b"RIFF" + b"\x00" * 100)
    
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"id": "voice_xyz"})
    
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)
    
    with patch("app.tts.httpx.AsyncClient", return_value=mock_client):
        await tts.clone_voice(audio_file, "Test", description="Family voice")
    
    call_data = mock_client.post.call_args[1]["data"]
    assert call_data["description"] == "Family voice"


# ── stream_tts_with_voice tests ───────────────────────────────────────


@pytest.mark.asyncio
async def test_stream_tts_with_voice_uses_provided_voice_id():
    """stream_tts_with_voice uses the specified voice_id, not default."""
    from app import tts
    
    fake_audio = b"\xaa\xbb" * 500
    
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
    
    with patch("app.tts.httpx.AsyncClient", return_value=mock_client):
        chunks = []
        async for chunk in tts.stream_tts_with_voice("Hello grandma", "custom_voice_123"):
            chunks.append(chunk)
    
    result = b"".join(chunks)
    assert result == fake_audio
    
    # Verify the custom voice_id was used
    call_args = mock_client.stream.call_args
    payload = call_args[1]["json"]
    assert payload["voice"]["id"] == "custom_voice_123"


# ── Endpoint tests ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_clone_endpoint_success(tmp_path):
    """POST /family/clips/{id}/clone clones voice and stores ID."""
    import aiosqlite
    from fastapi.testclient import TestClient
    
    # Setup test DB
    db_path = tmp_path / "test.db"
    clips_dir = tmp_path / "clips"
    clips_dir.mkdir()
    
    # Create a test audio file
    audio_file = clips_dir / "test_abc_clip.wav"
    audio_file.write_bytes(b"RIFF" + b"\x00" * 100)
    
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE family_clips (
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                relation TEXT NOT NULL,
                filename TEXT NOT NULL,
                uploaded_at REAL NOT NULL,
                cartesia_voice_id TEXT
            )
        """)
        await db.execute(
            "INSERT INTO family_clips VALUES (?, ?, ?, ?, ?, ?)",
            ("clip_123", "I love you grandma", "Grandson Jake", "test_abc_clip.wav", 1234567890.0, None)
        )
        await db.commit()
    
    # Patch environment and clone function
    with patch.dict(os.environ, {"SQLITE_PATH": str(db_path)}):
        with patch("app.main.CLIPS_DIR", str(clips_dir)):
            with patch("app.tts.clone_voice", new_callable=AsyncMock) as mock_clone:
                mock_clone.return_value = "cloned_voice_xyz"
                
                # Import app after patching
                from app.main import app
                
                with TestClient(app) as client:
                    resp = client.post("/family/clips/clip_123/clone")
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["voice_id"] == "cloned_voice_xyz"
    assert data["already_cloned"] is False


@pytest.mark.asyncio
async def test_clone_endpoint_already_cloned(tmp_path):
    """POST /family/clips/{id}/clone returns existing voice_id if already cloned."""
    import aiosqlite
    import sys
    from fastapi.testclient import TestClient
    
    db_path = tmp_path / "test.db"
    
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE family_clips (
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                relation TEXT NOT NULL,
                filename TEXT NOT NULL,
                uploaded_at REAL NOT NULL,
                cartesia_voice_id TEXT
            )
        """)
        await db.execute(
            "INSERT INTO family_clips VALUES (?, ?, ?, ?, ?, ?)",
            ("clip_456", "Hello", "Mom", "clip.wav", 1234567890.0, "existing_voice_id")
        )
        await db.commit()
    
    # Remove cached module to pick up new DB_PATH
    for mod in list(sys.modules.keys()):
        if mod.startswith("app"):
            del sys.modules[mod]
    
    with patch.dict(os.environ, {"SQLITE_PATH": str(db_path)}):
        from app.main import app
        
        with TestClient(app) as client:
            resp = client.post("/family/clips/clip_456/clone")
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["voice_id"] == "existing_voice_id"
    assert data["already_cloned"] is True


@pytest.mark.asyncio
async def test_clone_endpoint_clip_not_found(tmp_path):
    """POST /family/clips/{id}/clone returns 404 for unknown clip."""
    import aiosqlite
    from fastapi.testclient import TestClient
    
    db_path = tmp_path / "test.db"
    
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE family_clips (
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                relation TEXT NOT NULL,
                filename TEXT NOT NULL,
                uploaded_at REAL NOT NULL,
                cartesia_voice_id TEXT
            )
        """)
        await db.commit()
    
    with patch.dict(os.environ, {"SQLITE_PATH": str(db_path)}):
        from app.main import app
        
        with TestClient(app) as client:
            resp = client.post("/family/clips/nonexistent/clone")
    
    assert resp.status_code == 404


# ── Helper ────────────────────────────────────────────────────────────


async def _async_iter(items):
    for item in items:
        yield item
