"""Unit tests for comfort recipe EMA outcome updater."""

from __future__ import annotations

import sys
import os

import chromadb
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app.memory.store as store_module
from app.memory.workflow import store_recipe, update_recipe_outcome, EMA_ALPHA, SUCCESS_THRESHOLD


@pytest.fixture(autouse=True)
def fresh_chroma():
    """Give each test an isolated in-memory Chroma client."""
    store_module._chroma = chromadb.Client()
    yield
    store_module._chroma = None


def test_store_recipe_returns_id():
    rid = store_recipe("restless at 4pm", ["play_grandson_voice", "breathing_pacer"], "calm_restored")
    assert isinstance(rid, str) and len(rid) == 36  # UUID


def test_update_success_increases_rate():
    rid = store_recipe("trigger", ["speak"], "calm")
    # Initial rate is 0.5
    # Drop of 20 > SUCCESS_THRESHOLD(15) → success=1.0
    update_recipe_outcome(rid, agitation_before=70.0, agitation_after=50.0)

    col = store_module.get_chroma().get_collection("comfort_recipes")
    meta = col.get(ids=[rid])["metadatas"][0]
    expected = (1 - EMA_ALPHA) * 0.5 + EMA_ALPHA * 1.0  # 0.6
    assert abs(meta["success_rate"] - expected) < 0.001
    assert meta["times_used"] == 1


def test_update_failure_decreases_rate():
    rid = store_recipe("trigger", ["speak"], "calm")
    # Drop of 5 < SUCCESS_THRESHOLD(15) → success=0.0
    update_recipe_outcome(rid, agitation_before=70.0, agitation_after=65.0)

    col = store_module.get_chroma().get_collection("comfort_recipes")
    meta = col.get(ids=[rid])["metadatas"][0]
    expected = (1 - EMA_ALPHA) * 0.5 + EMA_ALPHA * 0.0  # 0.4
    assert abs(meta["success_rate"] - expected) < 0.001


def test_repeated_successes_converge_toward_one():
    rid = store_recipe("trigger", ["speak"], "calm")
    for _ in range(20):
        update_recipe_outcome(rid, agitation_before=80.0, agitation_after=40.0)

    col = store_module.get_chroma().get_collection("comfort_recipes")
    meta = col.get(ids=[rid])["metadatas"][0]
    assert meta["success_rate"] > 0.9
    assert meta["times_used"] == 20


def test_repeated_failures_converge_toward_zero():
    rid = store_recipe("trigger", ["speak"], "calm")
    for _ in range(20):
        update_recipe_outcome(rid, agitation_before=50.0, agitation_after=48.0)

    col = store_module.get_chroma().get_collection("comfort_recipes")
    meta = col.get(ids=[rid])["metadatas"][0]
    assert meta["success_rate"] < 0.1


def test_update_unknown_recipe_is_noop():
    """Updating a non-existent recipe should not raise."""
    update_recipe_outcome("nonexistent-id", 70.0, 30.0)  # should not raise


def test_exact_threshold_counts_as_success():
    """A drop of exactly SUCCESS_THRESHOLD counts as success (>= comparison)."""
    rid = store_recipe("trigger", ["speak"], "calm")
    update_recipe_outcome(rid, agitation_before=70.0, agitation_after=70.0 - SUCCESS_THRESHOLD)

    col = store_module.get_chroma().get_collection("comfort_recipes")
    meta = col.get(ids=[rid])["metadatas"][0]
    expected = (1 - EMA_ALPHA) * 0.5 + EMA_ALPHA * 1.0  # 0.6
    assert abs(meta["success_rate"] - expected) < 0.001
