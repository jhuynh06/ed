"""seed_demo.py — Pre-populate the Ed database + SSE history for hackathon demo.

Run:  cd backend && python seed_demo.py
Then hit:  GET http://localhost:8000/mock/seed
"""

import json
import math
import random
import sqlite3
import time
import uuid
from datetime import datetime, timedelta

DB_PATH = "ed.db"
random.seed(42)

def ts(hours_ago: float = 0) -> float:
    return time.time() - hours_ago * 3600

def main():
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")

    # ── Patients ─────────────────────────────────────────────
    db.execute("DELETE FROM patients")
    patients = [
        ("p1", "Margaret", 78, "Mild", "Ed", 72, "Jan 2025"),
        ("p2", "Harold", 82, "Moderate", "Ed", 68, "Mar 2025"),
        ("p3", "Dorothy", 75, "Mild", "Ed", 74, "Apr 2025"),
    ]
    for pid, name, age, stage, companion, hr, since in patients:
        db.execute(
            "INSERT INTO patients (id, name, age, stage, companion, baseline_hr, since_date, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (pid, name, age, stage, companion, hr, since, ts()),
        )

    # ── Episodes ─────────────────────────────────────────────
    db.execute("DELETE FROM episodes")
    episodes = [
        # Margaret — 3 sundowning episodes
        ("p1", ts(50), ts(49.85), 68.0, "calm restored — grandson voice + breathing pacer",
         [{"critic": "Clinical Safety", "verdict": "APPROVE", "feedback": "Appropriate comfort intervention."},
          {"critic": "Family Tone", "verdict": "REVISE", "feedback": "'Agitation episode' sounds clinical — suggest 'restless moment'."},
          {"critic": "Privacy", "verdict": "APPROVE", "feedback": "No unnecessary detail shared."}]),
        ("p1", ts(27.5), ts(27.35), 72.0, "calm restored — comfort recipe #1",
         [{"critic": "Clinical Safety", "verdict": "APPROVE", "feedback": "Standard comfort response."},
          {"critic": "Family Tone", "verdict": "APPROVE", "feedback": "Warm and reassuring."},
          {"critic": "Privacy", "verdict": "APPROVE", "feedback": "Concise and appropriate."}]),
        ("p1", ts(26.8), ts(26.7), 41.0, "self-resolved with gentle LED pulse",
         [{"critic": "Clinical Safety", "verdict": "APPROVE", "feedback": "Mild episode, no concern."},
          {"critic": "Family Tone", "verdict": "APPROVE", "feedback": "Informational tone appropriate."},
          {"critic": "Privacy", "verdict": "APPROVE", "feedback": "Minimal detail."}]),
        # Harold — 2 episodes
        ("p2", ts(30), ts(29.8), 55.0, "calm restored — music therapy",
         [{"critic": "Clinical Safety", "verdict": "APPROVE", "feedback": "Safe intervention."},
          {"critic": "Family Tone", "verdict": "APPROVE", "feedback": "Clear and warm."},
          {"critic": "Privacy", "verdict": "APPROVE", "feedback": "Appropriate."}]),
        ("p2", ts(6), ts(5.85), 63.0, "calm restored — breathing pacer + reassurance",
         [{"critic": "Clinical Safety", "verdict": "APPROVE", "feedback": "No medical concern."},
          {"critic": "Family Tone", "verdict": "REVISE", "feedback": "Soften 'distress' to 'unsettled moment'."},
          {"critic": "Privacy", "verdict": "APPROVE", "feedback": "Good."}]),
        # Dorothy — 1 mild episode
        ("p3", ts(20), ts(19.9), 35.0, "self-resolved — petting detected",
         [{"critic": "Clinical Safety", "verdict": "APPROVE", "feedback": "No intervention needed."},
          {"critic": "Family Tone", "verdict": "APPROVE", "feedback": "Gentle tone."},
          {"critic": "Privacy", "verdict": "APPROVE", "feedback": "Fine."}]),
    ]
    for pid, start, end, peak, outcome, mar in episodes:
        db.execute(
            "INSERT INTO episodes (id, patient_id, started_at, ended_at, peak, outcome, mar_trace) VALUES (?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), pid, start, end, peak, outcome, json.dumps(mar)),
        )

    # ── Vitals (24h for Margaret) ────────────────────────────
    db.execute("DELETE FROM vitals")
    for i in range(288):
        hours_ago = 24 - i / 12
        hour = (datetime.now() - timedelta(hours=hours_ago)).hour
        base = 68 if hour < 6 else 72 if hour < 12 else 76 if hour < 18 else 70
        if 16 <= hour < 17:
            base += 12
        db.execute(
            "INSERT INTO vitals (patient_id, recorded_at, bpm, spo2, baseline) VALUES (?,?,?,?,?)",
            ("p1", ts(hours_ago), base + random.randint(-3, 5), random.randint(95, 98), 72.0),
        )

    # ── Daily Metrics (7 days) ───────────────────────────────
    db.execute("DELETE FROM daily_metrics")
    today = datetime.now().date()
    for d in range(7):
        date = today - timedelta(days=d)
        ep_count = 2 if d in (1, 2) else 1 if d in (3, 5) else 0
        quality = 7 - ep_count * 2 + random.randint(-1, 1)
        db.execute(
            "INSERT INTO daily_metrics (patient_id, date_str, day_quality, episode_count, avg_agitation, "
            "sleep_hours, sleep_wake_count, speech_minutes, utterance_count, hrv_rmssd, mean_pause_s, "
            "long_pause_ratio, vocabulary_ttr, hr_baseline, agitation_baseline, drift_alert, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("p1", date.isoformat(), quality, ep_count, 15 + ep_count * 12,
             6.5 + random.random(), random.randint(1, 3),
             12 + random.randint(-3, 5), 40 + random.randint(-10, 15),
             32 + random.random() * 10, 0.8 + random.random() * 0.4,
             0.12 + random.random() * 0.08, 0.42 + random.random() * 0.1,
             72.0, 12.0, None, ts(d * 24)),
        )

    # ── Medications ──────────────────────────────────────────
    db.execute("DELETE FROM medications")
    meds = [
        ("p1", "Donepezil", "5mg", "Once daily, evening", "Cholinesterase inhibitor for mild dementia"),
        ("p1", "Melatonin", "3mg", "Bedtime", "Sleep aid — helps with sundowning"),
        ("p1", "Vitamin D", "1000 IU", "Morning with food", ""),
        ("p2", "Memantine", "10mg", "Twice daily", "NMDA receptor antagonist"),
        ("p2", "Sertraline", "50mg", "Morning", "For anxiety"),
    ]
    for pid, name, dosage, schedule, notes in meds:
        db.execute(
            "INSERT INTO medications (id, patient_id, name, dosage, schedule, notes, created_at) VALUES (?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), pid, name, dosage, schedule, notes, ts()),
        )

    # ── Caregiver Notes ──────────────────────────────────────
    db.execute("DELETE FROM caregiver_notes")
    notes = [
        ("p1", "visitor", "Jake visited for 2 hours. Margaret was very happy and engaged.", ts(48)),
        ("p1", "upset", "Got confused about where she was around 4pm. Calmed down after 10 minutes.", ts(27)),
        ("p1", "other", "Ate well today. Enjoyed the garden in the morning.", ts(24)),
        ("p2", "fall", "Minor stumble getting out of chair. No injury.", ts(72)),
        ("p2", "other", "Good day overall. Recognized his daughter on video call.", ts(30)),
    ]
    for pid, note_type, content, created in notes:
        db.execute(
            "INSERT INTO caregiver_notes (id, patient_id, note_type, content, created_at) VALUES (?,?,?,?,?)",
            (str(uuid.uuid4()), pid, note_type, content, created),
        )

    # ── Notification Log ─────────────────────────────────────
    db.execute("DELETE FROM notification_log")
    notifs = [
        ("p1", "Margaret had a restless moment this afternoon. Ed played Jake's voice message and guided breathing, and she calmed down within a few minutes. No action needed.", "info", ts(27)),
        ("p1", "Margaret's sundowning pattern is consistent — 3rd episode this week between 4-5pm. Consider earlier dinner time.", "info", ts(24)),
        ("p2", "Harold had an unsettled moment this morning. Breathing pacer helped him relax. No action needed.", "info", ts(6)),
    ]
    for pid, msg, priority, created in notifs:
        db.execute(
            "INSERT INTO notification_log (id, patient_id, message, priority, suppressed, created_at) VALUES (?,?,?,?,?,?)",
            (str(uuid.uuid4()), pid, msg, priority, 0, created),
        )

    db.commit()
    db.close()

    print("=== Demo data seeded ===")
    print(f"  Patients: {len(patients)} (Margaret, Harold, Dorothy)")
    print(f"  Episodes: {len(episodes)}")
    print(f"  Vitals: 288 readings (24h)")
    print(f"  Daily metrics: 7 days")
    print(f"  Medications: {len(meds)}")
    print(f"  Caregiver notes: {len(notes)}")
    print(f"  Notifications: {len(notifs)}")
    print()
    print("  Now hit: GET http://localhost:8000/mock/seed")
    print("  to push historical SSE data to the dashboard.")


if __name__ == "__main__":
    main()
