"""Tests for app/sse.py (EventBus) and app/main.py (REST + SSE endpoints).

Run with:
    pytest tests/test_main.py -v

These tests are fully offline — no Claude calls, no ESP32, no Chroma.
The LangGraph graph is patched to return a canned low-risk result.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
import httpx
from fastapi.testclient import TestClient

# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture()
def client(tmp_path):
    """TestClient with an isolated SQLite DB and a stubbed LangGraph graph."""
    import os
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

    # Patch build_ed_graph before importing main so the graph is never built for real
    canned_result = {
        "agitation_score": 15.0,
        "risk_level": "low",
        "semantic_observation": "User is calm.",
        "executed_actions": [],
        "mar_result": None,
        "sensor_snapshot": None,
    }
    mock_graph = AsyncMock()
    mock_graph.ainvoke = AsyncMock(return_value=canned_result)

    with patch("app.agents.graph.build_ed_graph", return_value=mock_graph):
        import importlib
        import app.main as main_mod
        importlib.reload(main_mod)  # re-run module with patched graph factory

        main_mod.DB_PATH = str(tmp_path / "test.db")
        main_mod.CLIPS_DIR = str(tmp_path / "clips")

        # Re-run lifespan manually to create schema
        import aiosqlite
        async def _init():
            async with aiosqlite.connect(main_mod.DB_PATH) as db:
                for stmt in main_mod._SCHEMA.strip().split(";"):
                    if stmt.strip():
                        await db.execute(stmt)
                await db.commit()
        asyncio.get_event_loop().run_until_complete(_init())

        with TestClient(main_mod.app, raise_server_exceptions=True) as c:
            yield c


# ── EventBus unit tests ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_eventbus_subscribe_and_receive():
    from app.sse import EventBus
    from app.models import AgitationUpdateEvent

    bus = EventBus()
    q = bus.subscribe()
    event = AgitationUpdateEvent(timestamp=time.time(), score=42.0, risk="medium")
    await bus.publish(event)
    received = await asyncio.wait_for(q.get(), timeout=1.0)
    assert received.score == 42.0
    assert received.risk == "medium"


@pytest.mark.asyncio
async def test_eventbus_fan_out_to_multiple_subscribers():
    from app.sse import EventBus
    from app.models import VitalsUpdateEvent

    bus = EventBus()
    q1, q2 = bus.subscribe(), bus.subscribe()
    event = VitalsUpdateEvent(bpm=80, spo2=98, baseline_bpm=72.0)
    await bus.publish(event)
    r1 = await asyncio.wait_for(q1.get(), timeout=1.0)
    r2 = await asyncio.wait_for(q2.get(), timeout=1.0)
    assert r1.bpm == r2.bpm == 80


@pytest.mark.asyncio
async def test_eventbus_unsubscribe_stops_delivery():
    from app.sse import EventBus
    from app.models import AgitationUpdateEvent

    bus = EventBus()
    q = bus.subscribe()
    bus.unsubscribe(q)
    await bus.publish(AgitationUpdateEvent(timestamp=time.time(), score=50.0, risk="high"))
    assert q.empty()


@pytest.mark.asyncio
async def test_eventbus_full_queue_drops_without_blocking():
    from app.sse import EventBus
    from app.models import AgitationUpdateEvent

    bus = EventBus()
    q = bus.subscribe()  # maxsize=100
    # Overfill — should not raise
    for i in range(110):
        await bus.publish(AgitationUpdateEvent(timestamp=time.time(), score=float(i), risk="low"))
    assert q.qsize() == 100  # capped at maxsize


def test_eventbus_format_sse():
    from app.sse import EventBus
    from app.models import NotificationEvent

    bus = EventBus()
    event = NotificationEvent(message="Test alert", priority="warning")
    formatted = bus.format_sse(event)
    assert formatted.startswith("event: notification\n")
    assert "Test alert" in formatted
    assert formatted.endswith("\n\n")


# ── REST endpoint tests ───────────────────────────────────────────────


def test_episodes_empty(client):
    r = client.get("/episodes")
    assert r.status_code == 200
    assert r.json() == []


def test_episodes_limit_param(client):
    r = client.get("/episodes?limit=5")
    assert r.status_code == 200


def test_vitals_empty(client):
    r = client.get("/vitals")
    assert r.status_code == 200
    assert r.json() == []


def test_vitals_hours_param(client):
    r = client.get("/vitals?hours=1")
    assert r.status_code == 200


def test_list_clips_empty(client):
    r = client.get("/family/clips")
    assert r.status_code == 200
    assert r.json() == []


def test_upload_clip(client, tmp_path):
    audio_bytes = b"\x00\xff" * 100  # fake PCM
    r = client.post(
        "/family/clips?label=I+love+you+grandma&relation=Jake",
        files={"file": ("jake.wav", audio_bytes, "audio/wav")},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["label"] == "I love you grandma"
    assert body["relation"] == "Jake"
    assert "id" in body


def test_upload_clip_then_list(client):
    audio_bytes = b"\x00\xff" * 50
    client.post(
        "/family/clips?label=Good+morning&relation=Sarah",
        files={"file": ("sarah.wav", audio_bytes, "audio/wav")},
    )
    r = client.get("/family/clips")
    assert r.status_code == 200
    clips = r.json()
    assert len(clips) == 1
    assert clips[0]["relation"] == "Sarah"


def test_upload_multiple_clips_ordered_newest_first(client):
    import time as _time
    for i, name in enumerate(["clip_a.wav", "clip_b.wav"]):
        client.post(
            f"/family/clips?label=Clip+{i}&relation=Relative",
            files={"file": (name, b"\x00" * 10, "audio/wav")},
        )
        _time.sleep(0.01)  # ensure distinct uploaded_at timestamps
    clips = client.get("/family/clips").json()
    assert len(clips) == 2
    labels = [c["label"] for c in clips]
    assert "Clip 0" in labels and "Clip 1" in labels
    # newest first
    assert clips[0]["label"] == "Clip 1"


# ── SSE endpoint smoke test ───────────────────────────────────────────


def test_sse_endpoint_returns_event_stream(client):
    """SSE endpoint should return text/event-stream content type."""
    with client.stream("GET", "/sse/events") as r:
        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]


# ── Daily summary — patched Claude ───────────────────────────────────


def test_daily_summary_no_episodes(client):
    """With no episodes in DB, summary endpoint should still return a valid shape."""
    from app.daily_digest import DailyDigest
    import datetime

    fake_digest = DailyDigest(
        patient_name="Margaret",
        date_str="Saturday, May 2",
        summary_markdown="Margaret had a calm day.",
        mood_arc="calm all day",
        episode_count=0,
        sundowning_detected=False,
        trend_direction="stable",
        cdr_total=None,
        action_items=["Keep current routine"],
        generated_at=time.time(),
    )

    with patch("app.main.generate_digest", new=AsyncMock(return_value=fake_digest)):
        r = client.get("/summary/daily")

    assert r.status_code == 200
    body = r.json()
    assert body["patient_name"] == "Margaret"
    assert body["episode_count"] == 0
    assert isinstance(body["action_items"], list)
    assert "summary" in body
    assert "mood_arc" in body


# ── Status endpoint ───────────────────────────────────────────────────


def test_status_returns_default(client):
    r = client.get("/status")
    assert r.status_code == 200
    body = r.json()
    assert "score" in body
    assert "risk" in body
    assert "bear_connected" in body


# ── Episode detail endpoint ───────────────────────────────────────────


def test_episode_detail_not_found(client):
    r = client.get("/episodes/nonexistent-id")
    assert r.status_code == 404


# ── Clip audio stream endpoint ────────────────────────────────────────


def test_clip_audio_stream(client):
    audio = b"\x00\xff" * 100
    upload = client.post(
        "/family/clips?label=test&relation=Jake",
        files={"file": ("test.wav", audio, "audio/wav")},
    )
    clip_id = upload.json()["id"]
    r = client.get(f"/family/clips/{clip_id}/audio")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("audio/")
    assert r.content == audio


def test_clip_audio_not_found(client):
    r = client.get("/family/clips/nonexistent/audio")
    assert r.status_code == 404


# ── Clip delete endpoint ──────────────────────────────────────────────


def test_delete_clip(client):
    audio = b"\x00" * 50
    upload = client.post(
        "/family/clips?label=delete_me&relation=Sarah",
        files={"file": ("del.wav", audio, "audio/wav")},
    )
    clip_id = upload.json()["id"]

    r = client.delete(f"/family/clips/{clip_id}")
    assert r.status_code == 204

    # Verify it's gone
    clips = client.get("/family/clips").json()
    assert all(c["id"] != clip_id for c in clips)


def test_delete_clip_not_found(client):
    r = client.delete("/family/clips/nonexistent")
    assert r.status_code == 404



# ── Medication endpoints ──────────────────────────────────────────────


def test_medications_empty(client):
    r = client.get("/medications")
    assert r.status_code == 200
    assert r.json() == []


def test_add_medication(client):
    r = client.post("/medications?name=Donepezil&dosage=10mg&schedule=bedtime&notes=For+memory")
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Donepezil"
    assert body["dosage"] == "10mg"
    assert body["schedule"] == "bedtime"
    assert body["notes"] == "For memory"
    assert "id" in body


def test_add_then_list_medications(client):
    client.post("/medications?name=Donepezil&dosage=10mg&schedule=bedtime")
    client.post("/medications?name=Melatonin&dosage=3mg&schedule=9pm")
    meds = client.get("/medications").json()
    assert len(meds) == 2
    names = {m["name"] for m in meds}
    assert names == {"Donepezil", "Melatonin"}


def test_delete_medication(client):
    r = client.post("/medications?name=Temp&dosage=1mg&schedule=daily")
    med_id = r.json()["id"]
    d = client.delete(f"/medications/{med_id}")
    assert d.status_code == 204
    meds = client.get("/medications").json()
    assert all(m["id"] != med_id for m in meds)


def test_delete_medication_not_found(client):
    r = client.delete("/medications/nonexistent")
    assert r.status_code == 404
