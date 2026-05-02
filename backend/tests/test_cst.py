"""Tests for CST probe taxonomy, selector, and response grader."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.cst import (
    PROBES, CSTProbe, ProbeResult,
    select_probe, grade_response,
    _BY_DIMENSION,
)


# ── Taxonomy sanity ───────────────────────────────────────────────────

def test_all_dimensions_covered():
    dims = {p.dimension for p in PROBES}
    assert dims == {"ORIENT", "MEMORY", "COMMUN", "JUDGMENT"}


def test_all_probe_ids_unique():
    ids = [p.id for p in PROBES]
    assert len(ids) == len(set(ids))


def test_probes_have_grading_hints():
    for p in PROBES:
        assert p.grading_hint, f"Probe {p.id} missing grading_hint"


# ── Probe selector ────────────────────────────────────────────────────

def test_select_returns_none_when_last_was_probe():
    """Alternation rule: if last turn was a probe, return None."""
    result = select_probe(
        cdr_scores={"orient": 2.0, "memory": 1.0, "commun": 0.5, "judgment": 0.0},
        last_probe_dimension="ORIENT",
        used_probe_ids=set(),
    )
    assert result is None


def test_select_picks_highest_cdr_dimension():
    """Should pick from the dimension with the highest CDR score."""
    result = select_probe(
        cdr_scores={"orient": 0.0, "memory": 2.5, "commun": 0.5, "judgment": 0.0},
        last_probe_dimension=None,
        used_probe_ids=set(),
    )
    assert result is not None
    assert result.dimension == "MEMORY"


def test_select_skips_used_probes():
    memory_ids = {p.id for p in _BY_DIMENSION["MEMORY"]}
    result = select_probe(
        cdr_scores={"orient": 0.0, "memory": 2.5, "commun": 0.5, "judgment": 0.0},
        last_probe_dimension=None,
        used_probe_ids=memory_ids,  # all MEMORY probes used
    )
    # Should fall back to next highest dimension (COMMUN)
    assert result is not None
    assert result.dimension != "MEMORY"


def test_select_returns_none_when_all_used():
    all_ids = {p.id for p in PROBES}
    result = select_probe(
        cdr_scores={"orient": 1.0, "memory": 1.0, "commun": 1.0, "judgment": 1.0},
        last_probe_dimension=None,
        used_probe_ids=all_ids,
    )
    assert result is None


def test_select_with_equal_scores_returns_something():
    result = select_probe(
        cdr_scores={"orient": 1.0, "memory": 1.0, "commun": 1.0, "judgment": 1.0},
        last_probe_dimension=None,
        used_probe_ids=set(),
    )
    assert result is not None


# ── Response grader — ORIENT ──────────────────────────────────────────

def get_probe(probe_id: str) -> CSTProbe:
    return next(p for p in PROBES if p.id == probe_id)


def test_orient_accurate_with_temporal_anchors():
    probe = get_probe("orient_weekend")
    result = grade_response(probe, "Yes, we're going to the park on Saturday with the grandkids.")
    assert result.grade == "accurate"


def test_orient_partial_weak_anchor():
    probe = get_probe("orient_weekend")
    result = grade_response(probe, "Maybe this weekend.")
    assert result.grade in ("accurate", "partial")


def test_orient_confused_no_anchors():
    probe = get_probe("orient_weekend")
    result = grade_response(probe, "I don't know, maybe something.")
    assert result.grade == "confused"


def test_orient_no_response():
    probe = get_probe("orient_lunch")
    result = grade_response(probe, "Um.")
    assert result.grade == "no_response"


# ── Response grader — MEMORY ──────────────────────────────────────────

def test_memory_accurate_detailed_response():
    probe = get_probe("memory_family")
    result = grade_response(probe, "Oh yes, there's Jake and Emma and little Sophie, she just turned three.")
    assert result.grade == "accurate"


def test_memory_partial_brief():
    probe = get_probe("memory_family")
    result = grade_response(probe, "Jake and Emma.")
    assert result.grade == "partial"


def test_memory_confused_very_sparse():
    probe = get_probe("memory_family")
    result = grade_response(probe, "I don't know.")
    assert result.grade in ("confused", "no_response")


# ── Response grader — COMMUN ──────────────────────────────────────────

def test_commun_fluency_accurate_many_items():
    probe = get_probe("commun_fruit_fluency")
    result = grade_response(probe, "I love peaches, apples, bananas, grapes, strawberries, and watermelon.")
    assert result.grade == "accurate"


def test_commun_fluency_partial_few_items():
    probe = get_probe("commun_fruit_fluency")
    result = grade_response(probe, "Apples and oranges.")
    assert result.grade == "partial"


def test_commun_word_finding_accurate():
    probe = get_probe("commun_word_finding")
    result = grade_response(probe, "Oh, you mean a garden hose!")
    assert result.grade == "accurate"


def test_commun_word_finding_circumlocution():
    probe = get_probe("commun_word_finding")
    result = grade_response(probe, "It's that long green thing you attach to the tap outside to water things.")
    assert result.grade == "partial"


def test_commun_word_finding_confused():
    probe = get_probe("commun_word_finding")
    result = grade_response(probe, "I don't know.")
    assert result.grade in ("confused", "no_response")


# ── Response grader — JUDGMENT ────────────────────────────────────────

def test_judgment_accurate_concrete_plan():
    probe = get_probe("judgment_rain")
    result = grade_response(probe, "I'd bring my umbrella and wear my raincoat.")
    assert result.grade == "accurate"


def test_judgment_partial_vague():
    probe = get_probe("judgment_rain")
    result = grade_response(probe, "I would be careful and maybe stay inside or something.")
    assert result.grade in ("partial", "confused")


def test_judgment_confused_no_plan():
    probe = get_probe("judgment_rain")
    result = grade_response(probe, "I don't know.")
    assert result.grade in ("confused", "no_response")


# ── ProbeResult structure ─────────────────────────────────────────────

def test_probe_result_has_all_fields():
    probe = get_probe("orient_weekend")
    result = grade_response(probe, "We're going to church on Sunday.")
    assert result.probe_id == "orient_weekend"
    assert result.dimension == "ORIENT"
    assert result.question == probe.question
    assert result.grade in ("accurate", "partial", "confused", "no_response")
    assert isinstance(result.notes, str)
