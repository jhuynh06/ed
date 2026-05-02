"""Unit tests for Thompson sampling contextual bandit."""

from __future__ import annotations

import sys
import os

import pytest
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.memory.bandit import BetaPrior, RecipeBandit, SUCCESS_THRESHOLD


# ── BetaPrior ─────────────────────────────────────────────────────────

def test_beta_prior_uniform_init():
    p = BetaPrior()
    assert p.alpha == 1.0
    assert p.beta == 1.0


def test_beta_prior_success_increments_alpha():
    p = BetaPrior()
    p.update(success=True)
    assert p.alpha == 2.0
    assert p.beta == 1.0


def test_beta_prior_failure_increments_beta():
    p = BetaPrior()
    p.update(success=False)
    assert p.alpha == 1.0
    assert p.beta == 2.0


def test_beta_prior_sample_in_range():
    p = BetaPrior(alpha=5.0, beta=2.0)
    for _ in range(100):
        s = p.sample()
        assert 0.0 <= s <= 1.0


def test_beta_prior_high_alpha_samples_high():
    """With many successes, samples should be mostly > 0.5."""
    p = BetaPrior(alpha=50.0, beta=2.0)
    samples = [p.sample() for _ in range(200)]
    assert sum(s > 0.5 for s in samples) > 180


# ── RecipeBandit ──────────────────────────────────────────────────────

def test_register_creates_4_buckets():
    b = RecipeBandit()
    b.register_recipe("r1")
    assert set(b._priors["r1"].keys()) == {0, 1, 2, 3}


def test_select_returns_one_of_candidates():
    b = RecipeBandit()
    ids = ["r1", "r2", "r3"]
    chosen = b.select(ids, hour=14)
    assert chosen in ids


def test_select_single_candidate_always_returns_it():
    b = RecipeBandit()
    assert b.select(["only"], hour=10) == "only"


def test_select_prefers_high_success_recipe_over_time():
    """After many successes for r1 and failures for r2, r1 should win most of the time."""
    b = RecipeBandit()
    for _ in range(30):
        b.update("r1", success=True, hour=14)
    for _ in range(30):
        b.update("r2", success=False, hour=14)

    wins = sum(b.select(["r1", "r2"], hour=14) == "r1" for _ in range(100))
    assert wins > 85  # r1 should win >85% of the time


def test_time_bucket_isolation():
    """Successes in afternoon bucket don't affect night bucket."""
    b = RecipeBandit()
    for _ in range(20):
        b.update("r1", success=True, hour=14)   # afternoon bucket=2
    for _ in range(20):
        b.update("r2", success=True, hour=14)

    # In night bucket (hour=2), both start uniform — r1 shouldn't dominate
    night_wins_r1 = sum(b.select(["r1", "r2"], hour=2) == "r1" for _ in range(100))
    # Should be roughly 50/50 (uniform priors in night bucket)
    assert 30 < night_wins_r1 < 70


def test_bucket_mapping():
    b = RecipeBandit()
    assert b._bucket(0) == 0   # night
    assert b._bucket(6) == 1   # morning
    assert b._bucket(12) == 2  # afternoon
    assert b._bucket(18) == 3  # evening
    assert b._bucket(23) == 3  # still evening


def test_success_threshold_constant():
    assert SUCCESS_THRESHOLD == 15.0
