from dataclasses import dataclass

from app.lang import Language, detect_language

DISORIENTATION_PHRASES: list[str] = [
    # English
    "where am i",
    "where are we",
    "i want to go home",
    "i need to go home",
    "take me home",
    "who are you",
    "i don't know you",
    "i don't recognize",
    "what day is it",
    "what year is it",
    "what time is it",
    "i'm lost",
    "i don't know where",
    "i can't find",
    "where is everyone",
    "where did everyone go",
    "i'm alone",
    # Mandarin (zh)
    "我在哪里",
    "我在哪儿",
    "我要回家",
    "我想回家",
    "带我回家",
    "你是谁",
    "我不认识你",
    "我不知道你",
    "今天是几号",
    "今年是哪年",
    "现在几点",
    "我迷路了",
    "我不知道在哪",
    "找不到",
    "大家都去哪了",
    "我一个人",
    "没有人",
]


@dataclass
class WanderingAlert:
    triggered: bool
    matched_phrases: list[str]
    confidence: float
    urgency: str
    message: str


def detect_wandering(transcript: str) -> WanderingAlert:
    lang = detect_language(transcript)
    # For zh, match as-is; for en, lowercase
    text = transcript if lang == "zh" else transcript.lower()
    matches = [p for p in DISORIENTATION_PHRASES if p in text]
    count = len(matches)
    urgency = "low" if count == 0 else ("medium" if count == 1 else "high")
    message = (
        f"Patient may be disoriented — said: '{matches[0]}'"
        if matches
        else "No disorientation detected."
    )
    return WanderingAlert(
        triggered=count > 0,
        matched_phrases=matches,
        confidence=count / len(DISORIENTATION_PHRASES),
        urgency=urgency,
        message=message,
    )
