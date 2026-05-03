"""Ed — FastAPI entry point.

Endpoints:
  WS  /ws/bear                — ESP32 sensor stream + command dispatch
  WS  /ws/audio               — ESP32 audio stream from AudioBridge
  GET /sse/events             — SSE live updates for dashboard
  GET /status                 — current agitation score + bear connection state
  GET /episodes               — episode list with MAR traces
  GET /episodes/{id}          — single episode detail
  GET /vitals                 — HR history (last N readings)
  GET /summary/daily          — Claude-generated daily digest
  GET /family/clips           — voice clip list
  GET /family/clips/{id}/audio — stream clip audio file
  POST /family/clips          — upload a new voice clip
  DELETE /family/clips/{id}   — delete a voice clip
  GET /medications            — list active medications
  POST /medications           — add a medication
  DELETE /medications/{id}    — remove a medication
  GET /metrics/daily          — today's observability metrics
  GET /metrics/weekly         — 7-day metrics for weekly digest
  POST /notes                 — add a caregiver incident note
  GET /notes                  — list caregiver notes
  GET /reports/export         — exportable JSON report (30/90 day)
"""

from __future__ import annotations

import asyncio
import hashlib
import base64
import json
import logging
import os
import struct
import time
import uuid
from contextlib import asynccontextmanager
from typing import Annotated

import aiosqlite
import numpy as np
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

from app.agents.graph import build_ed_graph
from app.audio_pipeline import AudioPipeline, AudioResult
from app.daily_digest import DigestInput, generate_digest
from app.models import (
    AgitationUpdateEvent,
    EpisodeEndEvent,
    EpisodeStartEvent,
    NotificationEvent,
    SensorUpdateEvent,
    TranscriptionEvent,
    VitalsUpdateEvent,
)
from app.sse import event_bus

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

DB_PATH = os.environ.get("SQLITE_PATH", "ed.db")

# ── DB schema ────────────────────────────────────────────────────────

_SCHEMA = """
CREATE TABLE IF NOT EXISTS patients (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    age         INTEGER NOT NULL,
    stage       TEXT NOT NULL,
    companion   TEXT NOT NULL,
    baseline_hr INTEGER NOT NULL DEFAULT 72,
    since_date  TEXT NOT NULL,
    created_at  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS episodes (
    id          TEXT PRIMARY KEY,
    patient_id  TEXT NOT NULL DEFAULT 'p1',
    started_at  REAL NOT NULL,
    ended_at    REAL,
    peak        REAL,
    outcome     TEXT,
    mar_trace   TEXT
);

CREATE TABLE IF NOT EXISTS vitals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id  TEXT NOT NULL DEFAULT 'p1',
    recorded_at REAL NOT NULL,
    bpm         INTEGER,
    spo2        INTEGER,
    baseline    REAL
);

CREATE TABLE IF NOT EXISTS family_clips (
    id          TEXT PRIMARY KEY,
    patient_id  TEXT NOT NULL DEFAULT 'p1',
    label       TEXT NOT NULL,
    relation    TEXT NOT NULL,
    filename    TEXT NOT NULL,
    uploaded_at REAL NOT NULL,
    cartesia_voice_id TEXT
);

CREATE TABLE IF NOT EXISTS medications (
    id          TEXT PRIMARY KEY,
    patient_id  TEXT NOT NULL DEFAULT 'p1',
    name        TEXT NOT NULL,
    dosage      TEXT NOT NULL,
    schedule    TEXT NOT NULL,
    notes       TEXT DEFAULT '',
    created_at  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS daily_metrics (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      TEXT NOT NULL DEFAULT 'p1',
    date_str        TEXT NOT NULL,
    day_quality     INTEGER,
    episode_count   INTEGER DEFAULT 0,
    avg_agitation   REAL DEFAULT 0,
    sleep_hours     REAL DEFAULT 0,
    sleep_wake_count INTEGER DEFAULT 0,
    speech_minutes  REAL DEFAULT 0,
    utterance_count INTEGER DEFAULT 0,
    hrv_rmssd       REAL,
    mean_pause_s    REAL,
    long_pause_ratio REAL,
    vocabulary_ttr  REAL,
    hr_baseline     REAL,
    agitation_baseline REAL,
    drift_alert     TEXT,
    created_at      REAL NOT NULL,
    UNIQUE(patient_id, date_str)
);

CREATE TABLE IF NOT EXISTS caregiver_notes (
    id          TEXT PRIMARY KEY,
    patient_id  TEXT NOT NULL DEFAULT 'p1',
    note_type   TEXT NOT NULL,
    content     TEXT NOT NULL,
    created_at  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS notification_log (
    id          TEXT PRIMARY KEY,
    patient_id  TEXT NOT NULL DEFAULT 'p1',
    message     TEXT NOT NULL,
    priority    TEXT NOT NULL,
    suppressed  INTEGER DEFAULT 0,
    created_at  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id  TEXT NOT NULL DEFAULT 'p1',
    sender      TEXT NOT NULL,
    content     TEXT NOT NULL,
    msg_type    TEXT NOT NULL DEFAULT 'text',
    created_at  REAL NOT NULL
);
"""


async def get_db() -> aiosqlite.Connection:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with aiosqlite.connect(DB_PATH) as db:
        for stmt in _SCHEMA.strip().split(";"):
            if stmt.strip():
                await db.execute(stmt)
        await db.commit()
    yield


# ── App ──────────────────────────────────────────────────────────────

app = FastAPI(title="Ed Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB = Annotated[aiosqlite.Connection, Depends(get_db)]

# In-memory state for /status endpoint
_last_status: dict = {"score": 0.0, "risk": "low", "bear_connected": False, "updated_at": 0.0}

# Daily summary cache — invalidated when episode count or IDs change
_summary_cache: dict = {"episode_count": -1, "episode_hash": "", "result": None}


# ── WebSocket — ESP32 ────────────────────────────────────────────────

@app.websocket("/ws/bear")
async def bear_websocket(ws: WebSocket):
    await ws.accept()
    _last_status["bear_connected"] = True
    graph = build_ed_graph()
    active_episode_id: str | None = None
    agitation_before: float | None = None
    episode_start_time: float | None = None

    try:
        while True:
            data = await ws.receive_json()

            msg_type = data.get("type")
            if msg_type is None:
                continue

            if msg_type == "sensor_data":
                imu_raw = data.get("imu", {})
                touch_raw = data.get("touch", {})

                # Publish sensor data to dashboard
                await event_bus.publish(SensorUpdateEvent(
                    imu_jerk=imu_raw.get("jerk_magnitude", 0.0),
                    imu_stillness_s=imu_raw.get("stillness_duration_s", 0.0),
                    imu_hug=imu_raw.get("hug_detected", False),
                    imu_rocking=imu_raw.get("rocking_detected", False),
                    imu_fall=imu_raw.get("fall_detected", False),
                    touch_any=touch_raw.get("any_contact", False),
                    touch_squeeze=touch_raw.get("squeeze_intensity", 0.0),
                    touch_petting=touch_raw.get("petting_detected", False),
                    touch_grip_s=touch_raw.get("grip_duration_s", 0.0),
                    touch_active_pads=touch_raw.get("active_pads", []),
                ))

                # Compute agitation locally (no API calls)
                jerk = imu_raw.get("jerk_magnitude", 0.0)
                vocal_arousal = _latest_audio_result.arousal if _latest_audio_result and _latest_audio_result.speech_detected else 0.0
                touch_absent = 1.0 if not touch_raw.get("any_contact", False) else 0.0
                score = min(100.0, (
                    0.30 * min(jerk / 2.0, 1.0) * 100 +
                    0.40 * vocal_arousal * 100 +
                    0.30 * touch_absent * min(touch_raw.get("grip_duration_s", 0) / 300.0, 1.0) * 100
                ))
                risk = "high" if score >= 60 else "medium" if score >= 30 else "low"

                _last_status.update(score=score, risk=risk, updated_at=time.time())
                await event_bus.publish(AgitationUpdateEvent(
                    timestamp=time.time(), score=score, risk=risk,
                ))

                # Episode lifecycle
                if risk in ("medium", "high") and active_episode_id is None:
                    active_episode_id = str(uuid.uuid4())
                    agitation_before = score
                    episode_start_time = time.time()
                    await event_bus.publish(EpisodeStartEvent(
                        id=active_episode_id, timestamp=time.time(), agitation=score,
                    ))
                elif risk == "low" and active_episode_id is not None:
                    await event_bus.publish(EpisodeEndEvent(
                        id=active_episode_id,
                        duration=time.time() - (episode_start_time or time.time()),
                        peak=agitation_before or score,
                        outcome="calm restored",
                    ))
                    active_episode_id = None
                    agitation_before = None
                    episode_start_time = None

            elif msg_type == "audio_chunk":
                # Audio pipeline handled separately — no-op here for now
                pass

    except WebSocketDisconnect:
        _last_status["bear_connected"] = False
        logger.info("Bear disconnected")


# ── WebSocket — Audio Stream from ESP32 via AudioBridge ──────────────

# Audio pipeline instance (stateful for VAD)
_audio_pipeline: AudioPipeline | None = None
_audio_bridge_connected: bool = False
_latest_audio_result: AudioResult | None = None  # shared with perception node


def _get_audio_pipeline() -> AudioPipeline:
    """Lazy-load audio pipeline to avoid startup cost if not used."""
    global _audio_pipeline
    if _audio_pipeline is None:
        _audio_pipeline = AudioPipeline()
    return _audio_pipeline


@app.websocket("/ws/audio")
async def audio_websocket(ws: WebSocket):
    """
    Receives audio from ESP32 via AudioBridge.
    
    Protocol:
      - Binary messages: Raw 16-bit PCM audio at 16kHz (512 samples = 1024 bytes)
      - JSON messages: Control messages (hello, device_connected, etc.)
    
    Processes audio through the pipeline (VAD → Whisper → emotion) and
    publishes results to the event bus for dashboard updates.
    """
    global _audio_bridge_connected
    
    await ws.accept()
    _audio_bridge_connected = True
    logger.info("AudioBridge connected")
    
    pipeline = _get_audio_pipeline()
    
    try:
        while True:
            try:
                message = await ws.receive()
            except RuntimeError:
                # Client already disconnected
                break
            
            if message.get("type") == "websocket.disconnect":
                break
            
            if "bytes" in message:
                # Raw PCM audio chunk from ESP32
                pcm_bytes = message["bytes"]
                
                # Convert bytes to numpy int16 array
                num_samples = len(pcm_bytes) // 2
                samples = np.array(
                    struct.unpack(f"<{num_samples}h", pcm_bytes),
                    dtype=np.int16
                )
                
                # Push through audio pipeline (VAD + inference when speech ends)
                try:
                    result = pipeline.push_frame(samples)
                except Exception as e:
                    logger.warning(f"Audio pipeline error: {e}")
                    result = None
                
                if result:
                    global _latest_audio_result
                    _latest_audio_result = result

                if result and result.speech_detected:
                  try:
                    # Speech segment processed — log and publish
                    logger.info(
                        f"Audio: '{result.transcription[:50]}...' "
                        f"emotion={result.dominant_emotion} "
                        f"lang={result.language}"
                    )
                    
                    # Publish transcription event for dashboard
                    # Build analytics kwargs from audio result
                    _ak = {}
                    if result.acoustic:
                        a = result.acoustic
                        _ak.update(f0_mean=a.f0_mean, f0_std=a.f0_std, jitter=a.jitter,
                                   shimmer=a.shimmer, hnr=a.hnr, speaking_rate=a.speaking_rate,
                                   pause_rate=a.pause_rate)
                    if result.nlp:
                        n = result.nlp
                        _ak.update(type_token_ratio=n.type_token_ratio, filler_rate=n.filler_rate,
                                   mean_utterance_length=n.mean_utterance_length, coherence=n.topic_coherence)
                    if result.cdr:
                        c = result.cdr
                        _ak.update(cdr_memory=c.memory, cdr_orientation=c.orient,
                                   cdr_communication=c.commun, cdr_judgment=c.judgment,
                                   cdr_sum_of_boxes=c.total)
                    await event_bus.publish(TranscriptionEvent(
                        text=result.transcription,
                        emotion=result.dominant_emotion,
                        valence=result.valence,
                        arousal=result.arousal,
                        language=result.language,
                        **_ak,
                    ))
                    
                    # If high arousal detected, could trigger agitation update
                    if result.arousal > 0.6:
                        await event_bus.publish(NotificationEvent(
                            message=f"Elevated vocal arousal detected: {result.dominant_emotion}",
                            priority="info",
                        ))
                  except Exception as e:
                    logger.warning(f"Audio publish error: {e}")
                    
            elif "text" in message:
                # JSON control message
                try:
                    data = json.loads(message["text"])
                    msg_type = data.get("type")
                    
                    if msg_type == "bridge_hello":
                        logger.info(f"AudioBridge hello: sample_rate={data.get('sample_rate')}")
                        
                    elif msg_type == "device_connected":
                        logger.info(f"ESP32 audio device connected: {data}")
                        
                    elif msg_type == "device_disconnected":
                        logger.info("ESP32 audio device disconnected")
                        
                except json.JSONDecodeError:
                    pass
                    
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        _audio_bridge_connected = False
        logger.info("AudioBridge disconnected")


# ── WebSocket — Speaker Stream via SpeakerSerialBridge ───────────────

_speaker_ws: WebSocket | None = None
_speaker_queue: asyncio.Queue[bytes] = asyncio.Queue()


async def send_tts_to_speaker(pcm_chunks: list[bytes]) -> None:
    """Queue TTS PCM chunks for the speaker bridge."""
    for chunk in pcm_chunks:
        await _speaker_queue.put(chunk)


@app.websocket("/ws/speaker")
async def speaker_websocket(ws: WebSocket):
    """Streams TTS audio to the SpeakerSerialBridge."""
    global _speaker_ws
    await ws.accept()
    _speaker_ws = ws
    logger.info("SpeakerBridge connected")

    try:
        while True:
            # Wait for TTS audio in the queue
            chunk = await _speaker_queue.get()
            try:
                await ws.send_bytes(chunk)
            except Exception:
                # Re-queue on failure so audio isn't lost
                await _speaker_queue.put(chunk)
                break
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        _speaker_ws = None
        logger.info("SpeakerBridge disconnected")


@app.post("/speak")
async def speak_endpoint(request: Request):
    """Trigger TTS and stream to the speaker ESP32.

    Body: {"text": "Hello Margaret", "voice_id": null}
    """
    body = await request.json()
    text = body.get("text", "")
    voice_id = body.get("voice_id")
    if not text:
        raise HTTPException(400, "text is required")

    if _speaker_ws is None:
        raise HTTPException(503, "Speaker not connected")

    from app.tts import stream_tts, stream_tts_with_voice

    chunks_sent = 0
    total_bytes = 0
    tts_fn = stream_tts_with_voice(text, voice_id) if voice_id else stream_tts(text)
    async for chunk in tts_fn:
        await _speaker_queue.put(chunk)
        chunks_sent += 1
        total_bytes += len(chunk)

    return {"status": "ok", "chunks": chunks_sent, "bytes": total_bytes}





# ── SSE — Dashboard live feed ────────────────────────────────────────

@app.get("/sse/events")
async def sse_events(request: Request):
    async def generator():
        q = event_bus.subscribe()
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield event_bus.format_sse(event)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            event_bus.unsubscribe(q)

    return StreamingResponse(generator(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


_scenario_tasks: list[asyncio.Task] = []


@app.get("/mock/scenario")
async def trigger_mock_scenario():
    """Trigger a scripted sundowning scenario. Cancels any already-running scenario first."""
    for t in _scenario_tasks:
        t.cancel()
    _scenario_tasks.clear()

    async def _run_scenario():
        import time as _time
        steps = [
            (22, "low"), (35, "low"), (48, "medium"), (62, "medium"),
            (71, "high"), (78, "high"), (82, "high"),
            (65, "medium"), (45, "medium"), (28, "low"), (18, "low"),
        ]
        episode_id = str(uuid.uuid4())
        episode_started = False
        for score, risk in steps:
            await asyncio.sleep(3)
            await event_bus.publish(AgitationUpdateEvent(timestamp=_time.time(), score=score, risk=risk))

            # Synthetic sensor data correlated with agitation
            jerk = score / 100 * 1.5
            grip_s = max(0, (score - 20) * 2)
            pads = [0, 1] if score < 40 else [0, 1, 2, 3] if score < 70 else [0, 1, 2, 3, 4, 6]
            await event_bus.publish(SensorUpdateEvent(
                imu_jerk=jerk, imu_stillness_s=max(0, 300 - score * 3),
                imu_hug=score > 50, imu_rocking=score > 60, imu_fall=False,
                touch_any=True, touch_squeeze=min(score / 100, 1.0),
                touch_petting=score < 35, touch_grip_s=grip_s,
                touch_active_pads=pads,
            ))

            if score > 40:
                await event_bus.publish(TranscriptionEvent(
                    text="I don't know where I am..." if score > 60 else "Where is everyone?",
                    emotion="fearful" if score > 60 else "sad",
                    arousal=score / 100,
                    valence=-(score / 100),
                ))

            if risk in ("medium", "high") and not episode_started:
                episode_started = True
                await event_bus.publish(EpisodeStartEvent(id=episode_id, timestamp=_time.time(), agitation=score))
            elif risk == "low" and episode_started:
                episode_started = False
                await event_bus.publish(EpisodeEndEvent(id=episode_id, duration=30.0, peak=82.0, outcome="calm restored after comfort recipe"))
                await event_bus.publish(NotificationEvent(
                    message="Margaret had a restless moment this afternoon. Ed played Jake's voice message and guided breathing, and she calmed down within a few minutes. No action needed.",
                    priority="info",
                    mar_trace=[
                        {"critic": "Clinical Safety", "verdict": "APPROVE", "feedback": "Appropriate comfort intervention, no medical concern"},
                        {"critic": "Family Tone", "verdict": "APPROVE", "feedback": "Language is warm and clear"},
                        {"critic": "Privacy", "verdict": "APPROVE", "feedback": "No unnecessary detail shared"},
                    ],
                ))

    task = asyncio.create_task(_run_scenario())
    _scenario_tasks.append(task)
    return {"status": "scenario started", "duration_s": 33}


@app.get("/mock/cancel")
async def cancel_mock_scenario():
    """Cancel all running scenario tasks."""
    for t in _scenario_tasks:
        t.cancel()
    count = len(_scenario_tasks)
    _scenario_tasks.clear()
    return {"cancelled": count}


# ── REST — Status ─────────────────────────────────────────────────────

@app.get("/patients")
async def list_patients(db: DB):
    async with db.execute("SELECT * FROM patients ORDER BY name ASC") as cur:
        rows = await cur.fetchall()
    return [dict(row) for row in rows]


@app.get("/patients/{patient_id}")
async def get_patient(db: DB, patient_id: str):
    async with db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")
    return dict(row)


@app.post("/patients", status_code=201)
async def add_patient(
    db: DB,
    name: str = Query(...),
    age: int = Query(...),
    stage: str = Query(default="Mild", description="Mild or Moderate"),
    companion: str = Query(default="Theodore"),
    baseline_hr: int = Query(default=72),
):
    import datetime
    patient_id = str(uuid.uuid4())[:8]
    since = datetime.date.today().strftime("%b %Y")
    await db.execute(
        "INSERT INTO patients (id, name, age, stage, companion, baseline_hr, since_date, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (patient_id, name, age, stage, companion, baseline_hr, since, time.time()),
    )
    await db.commit()
    return {"id": patient_id, "name": name, "age": age, "stage": stage, "companion": companion, "baseline_hr": baseline_hr, "since_date": since}


@app.delete("/patients/{patient_id}", status_code=204)
async def delete_patient(db: DB, patient_id: str):
    async with db.execute("SELECT id FROM patients WHERE id = ?", (patient_id,)) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")
    # Delete patient and all related data
    for table in ("episodes", "vitals", "family_clips", "medications", "daily_metrics", "caregiver_notes", "notification_log", "chat_messages"):
        await db.execute(f"DELETE FROM {table} WHERE patient_id = ?", (patient_id,))
    await db.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    await db.commit()


@app.get("/status")
async def get_status():
    return _last_status


# ── REST — Episodes ──────────────────────────────────────────────────

@app.get("/episodes")
async def list_episodes(
    db: DB,
    patient_id: str = Query(default="p1"),
    limit: int = Query(default=20, le=100),
):
    import json as _json
    async with db.execute(
        "SELECT * FROM episodes WHERE patient_id = ? ORDER BY started_at DESC LIMIT ?", (patient_id, limit,)
    ) as cur:
        rows = await cur.fetchall()

    return [
        {**dict(row), "mar_trace": _json.loads(row["mar_trace"]) if row["mar_trace"] else None}
        for row in rows
    ]


@app.get("/episodes/{episode_id}")
async def get_episode(db: DB, episode_id: str):
    import json as _json
    async with db.execute("SELECT * FROM episodes WHERE id = ?", (episode_id,)) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Episode not found")
    return {**dict(row), "mar_trace": _json.loads(row["mar_trace"]) if row["mar_trace"] else None}


# ── REST — Vitals ────────────────────────────────────────────────────

@app.get("/vitals")
async def list_vitals(
    db: DB,
    patient_id: str = Query(default="p1"),
    hours: float = Query(default=24.0, description="Look-back window in hours"),
):
    since = time.time() - hours * 3600
    async with db.execute(
        "SELECT * FROM vitals WHERE patient_id = ? AND recorded_at >= ? ORDER BY recorded_at ASC", (patient_id, since,)
    ) as cur:
        rows = await cur.fetchall()
    return [dict(row) for row in rows]


# ── REST — Daily summary ─────────────────────────────────────────────

@app.get("/summary/daily")
async def daily_summary(db: DB):
    import datetime, json as _json

    since = time.time() - 86400
    async with db.execute(
        "SELECT * FROM episodes WHERE started_at >= ? ORDER BY started_at ASC", (since,)
    ) as cur:
        rows = await cur.fetchall()

    _ep_hash = hashlib.md5(",".join(r["id"] for r in rows).encode()).hexdigest()
    # Return cached result if episode IDs haven't changed
    if _summary_cache["result"] and _summary_cache["episode_hash"] == _ep_hash:
        return _summary_cache["result"]

    episodes = [
        {
            "time": datetime.datetime.fromtimestamp(row["started_at"]).strftime("%I:%M%p"),
            "peak_agitation": row["peak"],
            "duration_s": (row["ended_at"] or row["started_at"]) - row["started_at"],
            "intervention": "comfort recipe",
            "outcome": row["outcome"] or "unknown",
        }
        for row in rows
    ]

    digest = await generate_digest(DigestInput(
        patient_name="Margaret",
        date_str=datetime.date.today().strftime("%A, %B %d").replace(" 0", " "),
        episodes=episodes,
        cdr_scores=None,
        anomalies=[],
        trend_direction="stable",
        sundowning_occurred=any(
            16 <= datetime.datetime.fromtimestamp(r["started_at"]).hour < 18
            for r in rows
        ),
        peak_agitation_hour=None,
        top_flags=[],
    ))

    result = {
        "patient_name": digest.patient_name,
        "date": digest.date_str,
        "summary": digest.summary_markdown,
        "mood_arc": digest.mood_arc,
        "episode_count": digest.episode_count,
        "sundowning_detected": digest.sundowning_detected,
        "trend": digest.trend_direction,
        "cdr_total": digest.cdr_total,
        "action_items": digest.action_items,
        "generated_at": digest.generated_at,
    }
    _summary_cache.update(episode_count=len(rows), episode_hash=_ep_hash, result=result)
    return result


# ── REST — Family clips ──────────────────────────────────────────────

CLIPS_DIR = os.environ.get("CLIPS_DIR", "clips")


@app.get("/family/clips")
async def list_clips(db: DB, patient_id: str = Query(default="p1")):
    async with db.execute(
        "SELECT * FROM family_clips WHERE patient_id = ? ORDER BY uploaded_at DESC", (patient_id,)
    ) as cur:
        rows = await cur.fetchall()
    return [dict(row) for row in rows]


@app.post("/family/clips", status_code=201)
async def upload_clip(
    db: DB,
    file: UploadFile,
    label: str = Query(...),
    relation: str = Query(...),
):
    os.makedirs(CLIPS_DIR, exist_ok=True)
    clip_id = str(uuid.uuid4())
    filename = f"{clip_id}_{os.path.basename(file.filename)}"
    dest = os.path.join(CLIPS_DIR, filename)

    content = await file.read()
    with open(dest, "wb") as f:
        f.write(content)

    await db.execute(
        "INSERT INTO family_clips (id, label, relation, filename, uploaded_at) VALUES (?,?,?,?,?)",
        (clip_id, label, relation, filename, time.time()),
    )
    await db.commit()

    return {"id": clip_id, "label": label, "relation": relation, "filename": filename}


@app.get("/family/clips/{clip_id}/audio")
async def stream_clip(db: DB, clip_id: str):
    async with db.execute("SELECT filename FROM family_clips WHERE id = ?", (clip_id,)) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Clip not found")
    path = os.path.join(CLIPS_DIR, row["filename"])
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Audio file missing")
    return FileResponse(path, media_type="audio/wav")


@app.delete("/family/clips/{clip_id}", status_code=204)
async def delete_clip(db: DB, clip_id: str):
    async with db.execute("SELECT filename FROM family_clips WHERE id = ?", (clip_id,)) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Clip not found")
    # Remove file from disk
    path = os.path.join(CLIPS_DIR, row["filename"])
    if os.path.isfile(path):
        os.remove(path)
    # Remove DB row
    await db.execute("DELETE FROM family_clips WHERE id = ?", (clip_id,))
    await db.commit()


@app.post("/family/clips/{clip_id}/clone")
async def clone_clip_voice(db: DB, clip_id: str):
    """Clone a voice from a family clip using Cartesia. Stores voice_id in DB."""
    from app.tts import clone_voice
    
    async with db.execute(
        "SELECT id, label, relation, filename, cartesia_voice_id FROM family_clips WHERE id = ?",
        (clip_id,)
    ) as cur:
        row = await cur.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    # Already cloned?
    if row["cartesia_voice_id"]:
        return {"voice_id": row["cartesia_voice_id"], "already_cloned": True}
    
    audio_path = os.path.join(CLIPS_DIR, row["filename"])
    if not os.path.isfile(audio_path):
        raise HTTPException(status_code=404, detail="Audio file missing")
    
    # Clone via Cartesia
    voice_name = f"{row['relation']} - {row['label']}"
    voice_id = await clone_voice(audio_path, voice_name, f"Family voice for Ed companion")
    
    # Store in DB
    await db.execute(
        "UPDATE family_clips SET cartesia_voice_id = ? WHERE id = ?",
        (voice_id, clip_id)
    )
    await db.commit()
    
    return {"voice_id": voice_id, "already_cloned": False}


# ── REST — Medications ────────────────────────────────────────────────


@app.get("/medications")
async def list_medications(db: DB, patient_id: str = Query(default="p1")):
    async with db.execute(
        "SELECT * FROM medications WHERE patient_id = ? ORDER BY created_at DESC", (patient_id,)
    ) as cur:
        rows = await cur.fetchall()
    return [dict(row) for row in rows]


@app.post("/medications", status_code=201)
async def add_medication(
    db: DB,
    name: str = Query(...),
    dosage: str = Query(...),
    schedule: str = Query(..., description="e.g. 'twice daily', 'bedtime', '8am and 8pm'"),
    notes: str = Query(default=""),
):
    med_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO medications (id, name, dosage, schedule, notes, created_at) VALUES (?,?,?,?,?,?)",
        (med_id, name, dosage, schedule, notes, time.time()),
    )
    await db.commit()
    return {"id": med_id, "name": name, "dosage": dosage, "schedule": schedule, "notes": notes}


@app.delete("/medications/{med_id}", status_code=204)
async def delete_medication(db: DB, med_id: str):
    async with db.execute("SELECT id FROM medications WHERE id = ?", (med_id,)) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Medication not found")
    await db.execute("DELETE FROM medications WHERE id = ?", (med_id,))
    await db.commit()



# ── REST — Observability Metrics ──────────────────────────────────────


@app.get("/metrics/daily")
async def get_daily_metrics(db: DB):
    import datetime
    today = datetime.date.today().isoformat()
    async with db.execute("SELECT * FROM daily_metrics WHERE date_str = ?", (today,)) as cur:
        row = await cur.fetchone()
    if row:
        return dict(row)
    # Compute live from observability module
    from app.observability import (
        hr_baseline, agitation_baseline, compute_rmssd,
        get_speech_engagement, get_pause_stats, compute_ttr,
        get_suppression_state,
    )
    eng = get_speech_engagement()
    pauses = get_pause_stats()
    return {
        "date_str": today,
        "hr_baseline": round(hr_baseline.value, 1),
        "agitation_baseline": round(agitation_baseline.value, 1),
        "hrv_rmssd": compute_rmssd(),
        "speech_minutes": eng.speech_minutes,
        "utterance_count": eng.utterance_count,
        "mean_pause_s": pauses["mean_pause_s"],
        "long_pause_ratio": pauses["long_pause_ratio"],
        "vocabulary_ttr": compute_ttr(),
        "suppression": get_suppression_state(),
    }


@app.get("/metrics/weekly")
async def get_weekly_metrics(db: DB):
    import datetime
    today = datetime.date.today()
    week_ago = (today - datetime.timedelta(days=7)).isoformat()
    async with db.execute(
        "SELECT * FROM daily_metrics WHERE date_str >= ? ORDER BY date_str ASC", (week_ago,)
    ) as cur:
        rows = await cur.fetchall()
    days = [dict(r) for r in rows]

    # Compute weekly aggregates
    if days:
        avg_quality = round(sum(d.get("day_quality") or 0 for d in days) / len(days), 1)
        total_episodes = sum(d.get("episode_count") or 0 for d in days)
        avg_sleep = round(sum(d.get("sleep_hours") or 0 for d in days) / len(days), 1)
        avg_speech = round(sum(d.get("speech_minutes") or 0 for d in days) / len(days), 1)
        ttr_values = [d["vocabulary_ttr"] for d in days if d.get("vocabulary_ttr")]
        avg_ttr = round(sum(ttr_values) / len(ttr_values), 3) if ttr_values else None
    else:
        avg_quality = total_episodes = avg_sleep = avg_speech = avg_ttr = 0

    return {
        "period": f"{week_ago} to {today.isoformat()}",
        "days_recorded": len(days),
        "avg_day_quality": avg_quality,
        "total_episodes": total_episodes,
        "avg_sleep_hours": avg_sleep,
        "avg_speech_minutes": avg_speech,
        "avg_vocabulary_ttr": avg_ttr,
        "daily": days,
    }


# ── REST — Caregiver Notes ───────────────────────────────────────────


@app.post("/notes", status_code=201)
async def add_note(
    db: DB,
    note_type: str = Query(..., description="fall|uti|hospital|upset|visitor|other"),
    content_text: str = Query(..., alias="content"),
):
    note_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO caregiver_notes (id, note_type, content, created_at) VALUES (?,?,?,?)",
        (note_id, note_type, content_text, time.time()),
    )
    await db.commit()
    return {"id": note_id, "note_type": note_type, "content": content_text}


@app.get("/notes")
async def list_notes(
    db: DB,
    patient_id: str = Query(default="p1"),
    days: int = Query(default=7, description="Look-back window in days"),
):
    since = time.time() - days * 86400
    async with db.execute(
        "SELECT * FROM caregiver_notes WHERE patient_id = ? AND created_at >= ? ORDER BY created_at DESC", (patient_id, since,)
    ) as cur:
        rows = await cur.fetchall()
    return [dict(row) for row in rows]


# ── REST — Exportable Report ─────────────────────────────────────────


@app.get("/chat")
async def list_chat(
    db: DB,
    patient_id: str = Query(default="p1"),
    limit: int = Query(default=50, le=200),
):
    async with db.execute(
        "SELECT * FROM chat_messages WHERE patient_id = ? ORDER BY created_at DESC LIMIT ?",
        (patient_id, limit),
    ) as cur:
        rows = await cur.fetchall()
    return [dict(row) for row in reversed(rows)]


@app.post("/chat", status_code=201)
async def add_chat_message(
    db: DB,
    patient_id: str = Query(default="p1"),
    sender: str = Query(..., description="'user' or 'theodore'"),
    content: str = Query(...),
    msg_type: str = Query(default="text", description="'text' or 'audio'"),
):
    await db.execute(
        "INSERT INTO chat_messages (patient_id, sender, content, msg_type, created_at) VALUES (?,?,?,?,?)",
        (patient_id, sender, content, msg_type, time.time()),
    )
    await db.commit()
    return {"status": "ok"}


@app.delete("/chat", status_code=204)
async def clear_chat(db: DB, patient_id: str = Query(default="p1")):
    await db.execute("DELETE FROM chat_messages WHERE patient_id = ?", (patient_id,))
    await db.commit()


@app.get("/reports/export")
async def export_report(
    db: DB,
    days: int = Query(default=30, le=90, description="Report window: 30 or 90"),
):
    import datetime, json as _json
    since = time.time() - days * 86400

    # Episodes
    async with db.execute(
        "SELECT * FROM episodes WHERE started_at >= ? ORDER BY started_at ASC", (since,)
    ) as cur:
        episode_rows = await cur.fetchall()
    episodes = [
        {**dict(r), "mar_trace": _json.loads(r["mar_trace"]) if r["mar_trace"] else None}
        for r in episode_rows
    ]

    # Daily metrics
    cutoff = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    async with db.execute(
        "SELECT * FROM daily_metrics WHERE date_str >= ? ORDER BY date_str ASC", (cutoff,)
    ) as cur:
        metric_rows = await cur.fetchall()
    metrics = [dict(r) for r in metric_rows]

    # Caregiver notes
    async with db.execute(
        "SELECT * FROM caregiver_notes WHERE created_at >= ? ORDER BY created_at ASC", (since,)
    ) as cur:
        note_rows = await cur.fetchall()
    notes = [dict(r) for r in note_rows]

    # Medications
    async with db.execute("SELECT * FROM medications ORDER BY created_at DESC") as cur:
        med_rows = await cur.fetchall()
    medications = [dict(r) for r in med_rows]

    # Aggregate stats
    ep_count = len(episodes)
    if metrics:
        avg_quality = round(sum(m.get("day_quality") or 0 for m in metrics) / len(metrics), 1)
        avg_sleep = round(sum(m.get("sleep_hours") or 0 for m in metrics) / len(metrics), 1)
        ttr_vals = [m["vocabulary_ttr"] for m in metrics if m.get("vocabulary_ttr")]
        avg_ttr = round(sum(ttr_vals) / len(ttr_vals), 3) if ttr_vals else None
    else:
        avg_quality = avg_sleep = avg_ttr = None

    return {
        "report_period_days": days,
        "generated_at": time.time(),
        "patient_name": "Margaret",
        "summary": {
            "total_episodes": ep_count,
            "avg_day_quality": avg_quality,
            "avg_sleep_hours": avg_sleep,
            "avg_vocabulary_ttr": avg_ttr,
            "days_with_data": len(metrics),
            "caregiver_notes_count": len(notes),
        },
        "episodes": episodes,
        "daily_metrics": metrics,
        "caregiver_notes": notes,
        "medications": medications,
    }
