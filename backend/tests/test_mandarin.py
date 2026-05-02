"""Tests for Mandarin language support — lang.py, wandering zh, CST zh grading."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.lang import detect_language, tokenize, split_sentences, FILLERS, TEMPORAL_WORDS
from app.wandering import detect_wandering, DISORIENTATION_PHRASES
from app.cst import grade_response, select_probe, PROBES, _BY_DIMENSION


# ── Language detection ────────────────────────────────────────────────

def test_detect_english():
    assert detect_language("Hello, how are you today?") == "en"


def test_detect_mandarin():
    assert detect_language("你好，今天怎么样？") == "zh"


def test_detect_mixed_mostly_chinese():
    assert detect_language("我今天去了park") == "zh"


def test_detect_empty_defaults_english():
    assert detect_language("") == "en"


def test_detect_mostly_english_with_few_cjk():
    assert detect_language("I went to 北京 last year") == "en"


# ── Tokenization ──────────────────────────────────────────────────────

def test_tokenize_english_splits_on_space():
    tokens = tokenize("hello world foo", "en")
    assert tokens == ["hello", "world", "foo"]


def test_tokenize_mandarin_uses_jieba():
    tokens = tokenize("我今天吃了苹果", "zh")
    # jieba should segment into meaningful words
    assert len(tokens) > 1
    assert "苹果" in tokens or any("苹" in t for t in tokens)


def test_tokenize_mandarin_no_spaces_needed():
    tokens = tokenize("今天天气很好", "zh")
    assert len(tokens) >= 2  # at minimum splits into some words


def test_split_sentences_english():
    sentences = split_sentences("Hello. How are you? I am fine.", "en")
    assert len(sentences) == 3


def test_split_sentences_mandarin():
    sentences = split_sentences("你好。今天怎么样？我很好！", "zh")
    assert len(sentences) == 3


# ── Filler words ──────────────────────────────────────────────────────

def test_zh_fillers_exist():
    assert "那个" in FILLERS["zh"]
    assert "嗯" in FILLERS["zh"]


def test_en_fillers_exist():
    assert "um" in FILLERS["en"]
    assert "like" in FILLERS["en"]


# ── Temporal words ────────────────────────────────────────────────────

def test_zh_temporal_words_exist():
    assert "今天" in TEMPORAL_WORDS["zh"]
    assert "星期" in TEMPORAL_WORDS["zh"]
    assert "下午" in TEMPORAL_WORDS["zh"]


# ── Wandering detection — Mandarin ────────────────────────────────────

def test_zh_wandering_phrases_in_list():
    zh_phrases = [p for p in DISORIENTATION_PHRASES if any("\u4e00" <= c <= "\u9fff" for c in p)]
    assert len(zh_phrases) >= 5


def test_zh_wandering_detected():
    result = detect_wandering("我在哪里？我不认识这个地方。")
    assert result.triggered
    assert result.urgency in ("medium", "high")


def test_zh_wandering_go_home():
    result = detect_wandering("我要回家，带我回家。")
    assert result.triggered
    assert result.urgency == "high"


def test_zh_wandering_who_are_you():
    result = detect_wandering("你是谁？我不认识你。")
    assert result.triggered


def test_zh_no_wandering_normal_speech():
    result = detect_wandering("今天天气真好，我们去公园吧。")
    assert not result.triggered


def test_en_wandering_still_works():
    result = detect_wandering("Where am I? I want to go home.")
    assert result.triggered
    assert result.urgency == "high"


# ── CST Mandarin probes exist ─────────────────────────────────────────

def test_zh_probes_in_all_dimensions():
    zh_probes = [p for p in PROBES if p.id.startswith("zh_")]
    dims = {p.dimension for p in zh_probes}
    assert dims == {"ORIENT", "MEMORY", "COMMUN", "JUDGMENT"}


def test_zh_probes_have_chinese_questions():
    zh_probes = [p for p in PROBES if p.id.startswith("zh_")]
    for p in zh_probes:
        has_cjk = any("\u4e00" <= c <= "\u9fff" for c in p.question)
        assert has_cjk, f"Probe {p.id} question has no Chinese characters"


# ── CST grading — Mandarin responses ─────────────────────────────────

def get_probe(pid: str):
    return next(p for p in PROBES if p.id == pid)


def test_zh_orient_accurate():
    probe = get_probe("zh_orient_weekend")
    result = grade_response(probe, "这个周末我们要去看孙子，星期六出发。")
    assert result.grade == "accurate"


def test_zh_orient_confused():
    probe = get_probe("zh_orient_weekend")
    result = grade_response(probe, "不知道，随便吧。")
    assert result.grade in ("confused", "no_response")


def test_zh_confusion_phrase_detected():
    probe = get_probe("zh_orient_season")
    result = grade_response(probe, "我不知道。")
    assert result.grade == "confused"


def test_zh_memory_detailed():
    probe = get_probe("zh_memory_family")
    result = grade_response(probe, "有小明、小红，还有最小的那个叫小花，她才三岁，特别可爱。")
    assert result.grade == "accurate"


def test_zh_commun_fruit_fluency():
    probe = get_probe("zh_commun_fruit")
    result = grade_response(probe, "苹果、香蕉、橙子、葡萄、西瓜、草莓都喜欢。")
    assert result.grade == "accurate"


def test_zh_commun_fruit_partial():
    probe = get_probe("zh_commun_fruit")
    result = grade_response(probe, "苹果和香蕉。")
    assert result.grade == "partial"


def test_zh_judgment_rain_accurate():
    probe = get_probe("zh_judgment_rain")
    result = grade_response(probe, "我会带雨伞，穿雨衣出门。")
    assert result.grade == "accurate"


def test_zh_judgment_confused():
    probe = get_probe("zh_judgment_rain")
    result = grade_response(probe, "不知道。")
    assert result.grade in ("confused", "no_response")
