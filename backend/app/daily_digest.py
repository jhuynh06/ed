from dataclasses import dataclass
from typing import Optional
import os
import time

import anthropic
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))


@dataclass
class DigestInput:
    patient_name: str
    date_str: str                    # e.g. "Friday, May 1"
    episodes: list[dict]             # list of episode dicts: {time, peak_agitation, duration_s, intervention, outcome}
    cdr_scores: dict | None          # {commun, orient, memory, judgment, total, flags}
    anomalies: list[dict]            # list of anomaly dicts: {time, message, severity}
    trend_direction: str             # 'improving' | 'stable' | 'declining'
    sundowning_occurred: bool
    peak_agitation_hour: int | None  # hour of day with highest agitation
    top_flags: list[str]             # CDR flags triggered today
    # Tier 1+2 observability
    sleep_hours: float | None = None
    sleep_wake_count: int | None = None
    speech_minutes: float | None = None
    day_quality: int | None = None   # 1-5
    vocabulary_ttr: float | None = None
    medications: list[str] | None = None  # ["Donepezil 10mg bedtime", ...]


@dataclass
class DailyDigest:
    patient_name: str
    date_str: str
    summary_markdown: str    # Claude-generated markdown paragraph
    mood_arc: str            # e.g. 'calm morning, agitated afternoon, calm evening'
    episode_count: int
    sundowning_detected: bool
    trend_direction: str
    cdr_total: float | None
    action_items: list[str]  # e.g. ['Consider earlier bedtime', 'Sundowning pattern emerging']
    generated_at: float      # timestamp


def _build_prompt(inp: DigestInput) -> str:
    episodes_text = "\n".join(
        f"  - {e.get('time', 'unknown')}: peak agitation {e.get('peak_agitation', '?')}, "
        f"duration {e.get('duration_s', '?')}s, intervention: {e.get('intervention', 'none')}, "
        f"outcome: {e.get('outcome', 'unknown')}"
        for e in inp.episodes
    ) or "  None"

    anomalies_text = "\n".join(
        f"  - [{a.get('severity', 'info')}] {a.get('time', '?')}: {a.get('message', '')}"
        for a in inp.anomalies
    ) or "  None"

    cdr_text = (
        f"total={inp.cdr_scores.get('total', '?')}, "
        f"memory={inp.cdr_scores.get('memory', '?')}, "
        f"orientation={inp.cdr_scores.get('orient', '?')}, "
        f"judgment={inp.cdr_scores.get('judgment', '?')}, "
        f"communication={inp.cdr_scores.get('commun', '?')}"
        if inp.cdr_scores else "Not available"
    )

    flags_text = ", ".join(inp.top_flags) or "None"
    peak_hour = f"{inp.peak_agitation_hour}:00" if inp.peak_agitation_hour is not None else "N/A"

    return f"""You are a compassionate clinical assistant helping family caregivers understand their loved one's day.

Patient: {inp.patient_name}
Date: {inp.date_str}
Day quality score: {inp.day_quality or 'N/A'}/5
Overall trend: {inp.trend_direction}
Sundowning occurred: {inp.sundowning_occurred}
Peak agitation hour: {peak_hour}
Sleep: {f'{inp.sleep_hours}h, woke {inp.sleep_wake_count} times' if inp.sleep_hours is not None else 'Not available'}
Speech engagement: {f'{inp.speech_minutes} minutes' if inp.speech_minutes is not None else 'Not available'}
Vocabulary diversity (TTR): {inp.vocabulary_ttr if inp.vocabulary_ttr else 'Not available'}
Medications: {', '.join(inp.medications) if inp.medications else 'None listed'}
Episodes ({len(inp.episodes)} total):
{episodes_text}
CDR scores: {cdr_text}
CDR flags today: {flags_text}
Anomalies:
{anomalies_text}

Please respond with exactly these sections. Write as if you're writing a warm letter to a family member, not a clinical report. Use the patient's name.

SUMMARY:
Write a 4-5 sentence warm summary answering these questions a family caregiver cares about most:
1. How did they sleep last night?
2. Were they upset or confused today? (episodes)
3. Did anything notable happen? (incidents, sundowning)
4. Were they social/engaged? (speech, touch)
5. Are they getting better or worse? (trend)

MOOD:
Describe the overall mood arc of the day in one short phrase (e.g. "calm morning, agitated afternoon, calm evening").

ACTIONS:
List 2-3 concrete, specific action items for the caregiver, one per line, starting with a dash (-).
"""


def _parse_response(text: str, inp: DigestInput) -> tuple[str, str, list[str]]:
    """Parse Claude response into (summary, mood, action_items). Falls back gracefully."""
    try:
        summary = ""
        mood = ""
        actions: list[str] = []

        if "SUMMARY:" not in text:
            raise ValueError("Missing SUMMARY label")

        parts = text.split("SUMMARY:", 1)[1]
        if "MOOD:" not in parts:
            raise ValueError("Missing MOOD label")

        summary_raw, rest = parts.split("MOOD:", 1)
        summary = summary_raw.strip()

        if "ACTIONS:" not in rest:
            raise ValueError("Missing ACTIONS label")

        mood_raw, actions_raw = rest.split("ACTIONS:", 1)
        mood = mood_raw.strip()

        actions = [
            line.lstrip("- ").strip()
            for line in actions_raw.strip().splitlines()
            if line.strip().startswith("-")
        ]

        return summary, mood, actions
    except Exception:
        return text.strip(), "", []


async def generate_digest(inp: DigestInput) -> DailyDigest:
    """Generate a structured daily caregiver digest using Claude Sonnet."""
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=600,
        messages=[{"role": "user", "content": _build_prompt(inp)}],
    )

    response_text = message.content[0].text
    summary, mood, action_items = _parse_response(response_text, inp)

    cdr_total = float(inp.cdr_scores["total"]) if inp.cdr_scores and "total" in inp.cdr_scores else None

    return DailyDigest(
        patient_name=inp.patient_name,
        date_str=inp.date_str,
        summary_markdown=summary,
        mood_arc=mood,
        episode_count=len(inp.episodes),
        sundowning_detected=inp.sundowning_occurred,
        trend_direction=inp.trend_direction,
        cdr_total=cdr_total,
        action_items=action_items,
        generated_at=time.time(),
    )
