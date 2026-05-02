"""Cognitive Stimulation Therapy (CST) probe system.

Probes are disguised as natural conversation — never clinical-sounding.
The planner selects probes based on which CDR dimension needs assessment,
enforces alternation (no two probes in a row), and grades responses inline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

CDRDimension = Literal["ORIENT", "MEMORY", "COMMUN", "JUDGMENT"]
ProbeGrade = Literal["accurate", "partial", "confused", "no_response"]


@dataclass
class CSTProbe:
    id: str
    dimension: CDRDimension
    question: str                    # what Ed says
    grading_hint: str                # what a good answer looks like (for LLM grader)
    follow_up: str | None = None     # optional follow-up if patient engages


@dataclass
class ProbeResult:
    probe_id: str
    dimension: CDRDimension
    question: str
    response: str
    grade: ProbeGrade
    notes: str                       # grader's reasoning


# ── Question taxonomy ─────────────────────────────────────────────────
# Grouped by CDR dimension. Questions feel like natural conversation.

PROBES: list[CSTProbe] = [
    # ORIENT — temporal and spatial orientation
    CSTProbe("orient_weekend", "ORIENT",
             "Are you doing anything special this weekend?",
             "Patient should anchor to current day/week. Confusion about what day it is signals disorientation.",
             follow_up="Oh nice — and what day is it today, do you know?"),
    CSTProbe("orient_lunch", "ORIENT",
             "Did you have lunch yet today?",
             "In the afternoon/evening, patient should know whether they've eaten. Confusion signals temporal disorientation."),
    CSTProbe("orient_season", "ORIENT",
             "It's been such interesting weather lately — what season does it feel like to you?",
             "Patient should correctly identify the current season."),
    CSTProbe("orient_morning", "ORIENT",
             "How has your morning been so far?",
             "If asked in the afternoon/evening, patient should recognize it's no longer morning."),

    # MEMORY — episodic recall and repetition detection
    CSTProbe("memory_story_followup", "MEMORY",
             "You mentioned something interesting last time we talked — I'd love to hear more about it.",
             "If patient repeats the same story without recognizing it's a repeat, that's a MEMORY signal. If they recall sharing it before, that's positive.",
             follow_up="Did you tell me about that before? I feel like I've heard this story — it's a good one."),
    CSTProbe("memory_family", "MEMORY",
             "Tell me about your grandchildren — what are their names?",
             "Ability to recall family members' names. Hesitation or confusion on close family is significant."),
    CSTProbe("memory_recent_event", "MEMORY",
             "What have you been up to lately? Anything fun happen this week?",
             "Ability to recall recent events. Vague or empty responses suggest episodic memory difficulty."),

    # COMMUN — vocabulary diversity and semantic fluency
    CSTProbe("commun_fruit_fluency", "COMMUN",
             "What's your favorite fruit? I love a good peach myself — what other fruits do you like?",
             "Category fluency task. Count distinct fruits named. 5+ is normal, 2-3 is reduced, 1 is impaired.",
             follow_up="Can you think of any more? I'm trying to remember all the ones at the market."),
    CSTProbe("commun_animal_fluency", "COMMUN",
             "I was thinking about animals today — what's your favorite animal? Can you name a few more you like?",
             "Category fluency. Same scoring as fruit task. Variety and speed of retrieval matter."),
    CSTProbe("commun_word_finding", "COMMUN",
             "I'm trying to remember the word for that thing you use to water plants — you know, the long one with a nozzle. Do you know what I mean?",
             "Naming task. 'Hose' or 'garden hose' is correct. Circumlocution (describing without naming) is partial credit."),

    # JUDGMENT — planning and practical reasoning
    CSTProbe("judgment_rain", "JUDGMENT",
             "It's supposed to rain tomorrow — what would you bring if you went outside?",
             "Tests practical planning. Umbrella, raincoat, boots are correct. Inability to plan for a simple scenario is significant."),
    CSTProbe("judgment_cold", "JUDGMENT",
             "If you were feeling a bit cold right now, what would you do?",
             "Simple problem-solving. Get a blanket, put on a sweater, turn up heat are all correct."),
    CSTProbe("judgment_phone", "JUDGMENT",
             "If you needed to reach your daughter but couldn't remember her number, what would you do?",
             "Tests adaptive problem-solving. Looking it up, asking someone, using a phone book are all valid."),

    # ── Mandarin (zh) probes ──────────────────────────────────────────

    # ORIENT
    CSTProbe("zh_orient_weekend", "ORIENT",
             "这个周末您有什么安排吗？",
             "Patient should anchor to current day/week. 周末/星期/今天 are positive signals.",
             follow_up="今天是星期几，您知道吗？"),
    CSTProbe("zh_orient_meal", "ORIENT",
             "您今天吃午饭了吗？",
             "In afternoon/evening, patient should know whether they've eaten. Temporal confusion is significant."),
    CSTProbe("zh_orient_season", "ORIENT",
             "最近天气怎么样？现在是什么季节？",
             "Patient should correctly identify the current season (春夏秋冬)."),

    # MEMORY
    CSTProbe("zh_memory_family", "MEMORY",
             "跟我说说您的孙子孙女吧，他们叫什么名字？",
             "Ability to recall family members' names. Hesitation on close family is significant."),
    CSTProbe("zh_memory_recent", "MEMORY",
             "最近有什么有趣的事情发生吗？",
             "Ability to recall recent events. Vague responses suggest episodic memory difficulty."),

    # COMMUN
    CSTProbe("zh_commun_fruit", "COMMUN",
             "您最喜欢吃什么水果？还有哪些水果您喜欢？",
             "Category fluency. Count distinct fruits named. 5+ normal, 2-3 reduced, 1 impaired.",
             follow_up="还能想到其他的吗？"),
    CSTProbe("zh_commun_animal", "COMMUN",
             "您最喜欢什么动物？能说几种您喜欢的动物吗？",
             "Category fluency. Same scoring as fruit task."),
    CSTProbe("zh_commun_word_finding", "COMMUN",
             "我想不起来那个浇花用的东西叫什么了，就是那个长长的、接在水龙头上的——您知道吗？",
             "Naming task. 水管/软管/浇水管 is correct. Circumlocution is partial credit."),

    # JUDGMENT
    CSTProbe("zh_judgment_rain", "JUDGMENT",
             "明天要下雨，如果您要出门的话，会带什么？",
             "Tests practical planning. 雨伞/雨衣 are correct responses.",),
    CSTProbe("zh_judgment_cold", "JUDGMENT",
             "如果您现在觉得有点冷，您会怎么做？",
             "Simple problem-solving. 穿外套/拿毯子/开暖气 are correct."),
]

# Index by dimension for fast lookup
_BY_DIMENSION: dict[CDRDimension, list[CSTProbe]] = {}
for _p in PROBES:
    _BY_DIMENSION.setdefault(_p.dimension, []).append(_p)


# ── Probe selector ────────────────────────────────────────────────────

def select_probe(
    cdr_scores: dict,
    last_probe_dimension: CDRDimension | None,
    used_probe_ids: set[str],
) -> CSTProbe | None:
    """Select the next probe based on CDR scores, avoiding repetition and consecutive probes.

    Returns None if no suitable probe found (all used, or alternation constraint).
    The caller is responsible for enforcing the alternation rule (last_probe_dimension
    being set means the previous turn was a probe — skip this turn).
    """
    if last_probe_dimension is not None:
        return None  # Alternate: last turn was a probe, this turn is social conversation

    # Pick the dimension with the highest CDR score (most impaired)
    dim_scores = {
        "ORIENT": float(cdr_scores.get("orient", 0)),
        "MEMORY": float(cdr_scores.get("memory", 0)),
        "COMMUN": float(cdr_scores.get("commun", 0)),
        "JUDGMENT": float(cdr_scores.get("judgment", 0)),
    }

    # Sort dimensions by score descending, try each until we find an unused probe
    for dim in sorted(dim_scores, key=lambda d: dim_scores[d], reverse=True):
        candidates = [p for p in _BY_DIMENSION.get(dim, []) if p.id not in used_probe_ids]
        if candidates:
            return candidates[0]

    return None  # All probes exhausted


# ── Response grader ───────────────────────────────────────────────────

def grade_response(probe: CSTProbe, response: str) -> ProbeResult:
    """Grade a patient response to a CST probe using heuristics."""
    import re
    from app.lang import (detect_language, tokenize,
                          TEMPORAL_WORDS, ACTION_WORDS, CONFUSION_PHRASES)

    lang = detect_language(response)
    words = tokenize(response, lang)

    if not words or len(words) < 2:
        return ProbeResult(probe.id, probe.dimension, probe.question, response,
                           "no_response", "Response too short or empty.")

    # Confusion override — check before dimension logic
    confusion = CONFUSION_PHRASES[lang]
    text_joined = "".join(words) if lang == "zh" else " ".join(words)
    if any(phrase in text_joined for phrase in confusion):
        return ProbeResult(probe.id, probe.dimension, probe.question, response,
                           "confused", "Patient expressed uncertainty.")

    grade: ProbeGrade
    notes: str

    if probe.dimension == "ORIENT":
        temporal = TEMPORAL_WORDS[lang]
        anchors = [w for w in words if w in temporal]
        if anchors:
            grade, notes = "accurate", f"Temporal anchors found: {anchors}"
        elif any(w.isdigit() and len(w) == 4 for w in words):
            grade, notes = "accurate", "Year referenced."
        else:
            grade, notes = "confused", "No temporal anchors in response."

    elif probe.dimension == "MEMORY":
        if len(words) >= 8:
            grade, notes = "accurate", "Detailed response suggests intact episodic recall."
        elif len(words) >= 3:
            grade, notes = "partial", "Brief response — limited detail."
        else:
            grade, notes = "confused", "Very sparse response."

    elif probe.dimension == "COMMUN":
        if "fruit" in probe.id or "animal" in probe.id or "commun_fruit" in probe.id or "commun_animal" in probe.id:
            stopwords_en = {"i", "like", "love", "and", "or", "the", "a", "my", "favorite",
                            "also", "too", "well", "um", "uh", "yes", "no"}
            stopwords_zh = {"我", "你", "的", "了", "是", "也", "和", "还", "有", "喜欢", "最"}
            stopwords = stopwords_zh if lang == "zh" else stopwords_en
            content = [w for w in words if w not in stopwords and len(w) > (1 if lang == "zh" else 2)]
            unique = len(set(content))
            if unique >= 5:
                grade, notes = "accurate", f"{unique} distinct items named."
            elif unique >= 2:
                grade, notes = "partial", f"Only {unique} items — reduced fluency."
            else:
                grade, notes = "confused", f"Only {unique} items — impaired fluency."
        else:
            # Word-finding
            targets_en = {"hose", "watering", "sprinkler"}
            targets_zh = {"水管", "软管", "浇水管", "水龙头"}
            targets = targets_zh if lang == "zh" else targets_en
            if any(t in text_joined for t in targets):
                grade, notes = "accurate", "Target word retrieved."
            elif len(words) >= 5:
                grade, notes = "partial", "Circumlocution — described without naming."
            else:
                grade, notes = "confused", "Could not retrieve or describe target."

    else:  # JUDGMENT
        action = ACTION_WORDS[lang]
        actions_found = [w for w in words if w in action]
        if actions_found:
            grade, notes = "accurate", f"Concrete plan identified: {actions_found}"
        elif len(words) >= 6:
            grade, notes = "partial", "Response present but no clear action plan."
        else:
            grade, notes = "confused", "No actionable response."

    return ProbeResult(probe.id, probe.dimension, probe.question, response, grade, notes)
