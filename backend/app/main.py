"""Ed — FastAPI entry point.

Endpoints:
  WS  /ws/bear                — ESP32 sensor stream + command dispatch
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
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Annotated

import aiosqlite
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

from app.agents.graph import build_ed_graph
from app.daily_digest import DigestInput, generate_digest
from app.models import (
    AgitationUpdateEvent,
    EpisodeEndEvent,
    EpisodeStartEvent,
    NotificationEvent,
    VitalsUpdateEvent,
)
from app.sse import event_bus

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

DB_PATH = os.environ.get("SQLITE_PATH", "ed.db")

# ── DB schema ────────────────────────────────────────────────────────

_SCHEMA = """
CREATE TABLE IF NOT EXISTS episodes (
    id          TEXT PRIMARY KEY,
    started_at  REAL NOT NULL,
    ended_at    REAL,
    peak        REAL,
    outcome     TEXT,
    mar_trace   TEXT
);

CREATE TABLE IF NOT EXISTS vitals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    recorded_at REAL NOT NULL,
    bpm         INTEGER,
    spo2        INTEGER,
    baseline    REAL
);

CREATE TABLE IF NOT EXISTS family_clips (
    id          TEXT PRIMARY KEY,
    label       TEXT NOT NULL,
    relation    TEXT NOT NULL,
    filename    TEXT NOT NULL,
    uploaded_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS medications (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    dosage      TEXT NOT NULL,
    schedule    TEXT NOT NULL,
    notes       TEXT DEFAULT '',
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

# Daily summary cache — invalidated when episode count changes
_summary_cache: dict = {"episode_count": -1, "result": None}


# ── WebSocket — ESP32 ────────────────────────────────────────────────

@app.websocket("/ws/bear")
async def bear_websocket(ws: WebSocket):
    await ws.accept()
    _last_status["bear_connected"] = True
    graph = build_ed_graph()
    active_episode_id: str | None = None
    agitation_before: float | None = None

    try:
        while True:
            data = await ws.receive_json()

            if data["type"] == "sensor_data":
                result = await graph.ainvoke({"raw_sensor": data})

                score: float = result.get("agitation_score", 0.0)
                risk: str = result.get("risk_level", "low")

                # Publish live agitation update
                _last_status.update(score=score, risk=risk, updated_at=time.time())
                await event_bus.publish(AgitationUpdateEvent(
                    timestamp=time.time(), score=score, risk=risk,
                ))

                # Publish vitals if HR valid
                snap = result.get("sensor_snapshot")
                if snap and snap.hr.valid:
                    await event_bus.publish(VitalsUpdateEvent(
                        bpm=snap.hr.bpm, spo2=snap.hr.spo2, baseline_bpm=snap.hr.baseline_bpm,
                    ))

                # Episode lifecycle
                if risk in ("medium", "high") and active_episode_id is None:
                    active_episode_id = result.get("episode_id") or str(uuid.uuid4())
                    agitation_before = score
                    await event_bus.publish(EpisodeStartEvent(
                        id=active_episode_id, timestamp=time.time(), agitation=score,
                    ))

                elif risk == "low" and active_episode_id is not None:
                    mar = result.get("mar_result") or {}
                    await event_bus.publish(EpisodeEndEvent(
                        id=active_episode_id,
                        duration=0.0,  # caller can compute from start event
                        peak=agitation_before or score,
                        outcome=mar.get("final_notification", "calm restored"),
                    ))
                    active_episode_id = None
                    agitation_before = None

                # Notification
                mar = result.get("mar_result")
                if mar and mar.get("approved"):
                    await event_bus.publish(NotificationEvent(
                        message=mar["final_notification"],
                        priority="warning",
                        mar_trace=mar.get("debate_trace"),
                    ))

                # Send commands back to bear
                for action in result.get("executed_actions", []):
                    await ws.send_json(action)

                # Stream TTS audio chunks to bear
                import base64 as _b64
                for chunks in result.get("tts_chunks", []):
                    for chunk in chunks:
                        await ws.send_json({
                            "type": "audio_stream",
                            "payload": _b64.b64encode(chunk).decode(),
                        })
                    await ws.send_json({"type": "audio_stream_end"})

            elif data["type"] == "audio_chunk":
                # Audio pipeline handled separately — no-op here for now
                pass

    except WebSocketDisconnect:
        _last_status["bear_connected"] = False
        logger.info("Bear disconnected")


# ── SSE — Dashboard live feed ────────────────────────────────────────

@app.get("/sse/events")
async def sse_events():
    async def generator():
        q = event_bus.subscribe()
        try:
            while True:
                event = await asyncio.wait_for(q.get(), timeout=30.0)
                yield event_bus.format_sse(event)
        except asyncio.TimeoutError:
            yield ": keepalive\n\n"  # prevent proxy timeout
        except asyncio.CancelledError:
            pass
        finally:
            event_bus.unsubscribe(q)

    return StreamingResponse(generator(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


# ── REST — Status ─────────────────────────────────────────────────────

@app.get("/status")
async def get_status():
    return _last_status


# ── REST — Episodes ──────────────────────────────────────────────────

@app.get("/episodes")
async def list_episodes(
    db: DB,
    limit: int = Query(default=20, le=100),
):
    import json as _json
    async with db.execute(
        "SELECT * FROM episodes ORDER BY started_at DESC LIMIT ?", (limit,)
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
    hours: float = Query(default=24.0, description="Look-back window in hours"),
):
    since = time.time() - hours * 3600
    async with db.execute(
        "SELECT * FROM vitals WHERE recorded_at >= ? ORDER BY recorded_at ASC", (since,)
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

    # Return cached result if episode count hasn't changed
    if _summary_cache["result"] and _summary_cache["episode_count"] == len(rows):
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
    _summary_cache.update(episode_count=len(rows), result=result)
    return result


# ── REST — Family clips ──────────────────────────────────────────────

CLIPS_DIR = os.environ.get("CLIPS_DIR", "clips")


@app.get("/family/clips")
async def list_clips(db: DB):
    async with db.execute(
        "SELECT * FROM family_clips ORDER BY uploaded_at DESC"
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
    filename = f"{clip_id}_{file.filename}"
    dest = os.path.join(CLIPS_DIR, filename)

    content = await file.read()
    with open(dest, "wb") as f:
        f.write(content)

    async with aiosqlite.connect(DB_PATH) as db_write:
        await db_write.execute(
            "INSERT INTO family_clips (id, label, relation, filename, uploaded_at) VALUES (?,?,?,?,?)",
            (clip_id, label, relation, filename, time.time()),
        )
        await db_write.commit()

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
    async with aiosqlite.connect(DB_PATH) as db_write:
        await db_write.execute("DELETE FROM family_clips WHERE id = ?", (clip_id,))
        await db_write.commit()



# ── REST — Medications ────────────────────────────────────────────────


@app.get("/medications")
async def list_medications(db: DB):
    async with db.execute(
        "SELECT * FROM medications ORDER BY created_at DESC"
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
    async with aiosqlite.connect(DB_PATH) as db_write:
        await db_write.execute(
            "INSERT INTO medications (id, name, dosage, schedule, notes, created_at) VALUES (?,?,?,?,?,?)",
            (med_id, name, dosage, schedule, notes, time.time()),
        )
        await db_write.commit()
    return {"id": med_id, "name": name, "dosage": dosage, "schedule": schedule, "notes": notes}


@app.delete("/medications/{med_id}", status_code=204)
async def delete_medication(db: DB, med_id: str):
    async with db.execute("SELECT id FROM medications WHERE id = ?", (med_id,)) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Medication not found")
    async with aiosqlite.connect(DB_PATH) as db_write:
        await db_write.execute("DELETE FROM medications WHERE id = ?", (med_id,))
        await db_write.commit()
