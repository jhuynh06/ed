"""Language abstraction layer — tokenization and word lists for en and zh.

Supports English (en) and Mandarin Chinese (zh).
All NLP features route through here for language-aware processing.
"""

from __future__ import annotations

from typing import Literal

Language = Literal["en", "zh"]


def detect_language(text: str) -> Language:
    """Heuristic language detection — count CJK characters."""
    if not text:
        return "en"
    cjk = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    return "zh" if cjk / max(len(text), 1) > 0.2 else "en"


def tokenize(text: str, lang: Language) -> list[str]:
    """Tokenize text into words. Uses jieba for zh, whitespace split for en."""
    if lang == "zh":
        import jieba
        return list(jieba.cut(text, cut_all=False))
    import re
    return re.findall(r"[a-z']+", text.lower())


def split_sentences(text: str, lang: Language) -> list[str]:
    """Split text into sentences."""
    import re
    if lang == "zh":
        # Chinese sentence-ending punctuation
        parts = re.split(r"[。！？…]+", text)
    else:
        parts = re.split(r"[.!?]+", text)
    return [s.strip() for s in parts if s.strip()]


# ── Per-language filler words ─────────────────────────────────────────

FILLERS: dict[Language, set[str]] = {
    "en": {
        "um", "uh", "like", "you know", "i mean", "sort of", "kind of",
        "basically", "literally", "actually", "well", "so", "right",
    },
    "zh": {
        "那个", "就是", "然后", "嗯", "啊", "哦", "呢", "吧",
        "这个", "对对对", "就", "然后就", "怎么说",
    },
}

# ── Per-language temporal anchor words (for ORIENT grading) ──────────

TEMPORAL_WORDS: dict[Language, set[str]] = {
    "en": {
        "today", "tomorrow", "yesterday", "monday", "tuesday", "wednesday",
        "thursday", "friday", "saturday", "sunday", "morning", "afternoon",
        "evening", "night", "week", "weekend", "spring", "summer", "fall",
        "autumn", "winter", "january", "february", "march", "april", "may",
        "june", "july", "august", "september", "october", "november", "december",
    },
    "zh": {
        "今天", "明天", "昨天", "早上", "上午", "中午", "下午", "晚上",
        "星期", "周", "月", "年", "春天", "夏天", "秋天", "冬天",
        "周一", "周二", "周三", "周四", "周五", "周六", "周日",
        "周末", "这周", "上周", "下周", "这个月", "上个月",
        "星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日", "星期天",
        "一月", "二月", "三月", "四月", "五月", "六月",
        "七月", "八月", "九月", "十月", "十一月", "十二月",
        "春", "夏", "秋", "冬", "早", "晚", "今年", "明年", "去年",
    },
}

# ── Per-language action/planning words (for JUDGMENT grading) ────────

ACTION_WORDS: dict[Language, set[str]] = {
    "en": {
        "bring", "take", "wear", "get", "use", "call", "ask", "find",
        "look", "put", "grab", "carry", "umbrella", "coat", "blanket",
        "sweater", "phone", "number",
    },
    "zh": {
        "带", "拿", "穿", "用", "打电话", "找", "问", "雨伞",
        "外套", "毯子", "毛衣", "手机", "号码", "去", "拿来",
    },
}

# ── Confusion phrases (for grading override) ─────────────────────────

CONFUSION_PHRASES: dict[Language, set[str]] = {
    "en": {"i don't know", "i dont know", "i'm not sure", "i have no idea", "no idea"},
    "zh": {"不知道", "我不知道", "不清楚", "忘了", "想不起来", "不记得"},
}
