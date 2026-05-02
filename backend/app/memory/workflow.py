"""Workflow memory — comfort recipe storage and EMA outcome updates.

Recipes are stored in Chroma (for similarity retrieval) and tracked in a
module-level dict for fast in-process updates during a session.
"""

from __future__ import annotations

import time
import uuid

import chromadb

from app.memory.store import get_chroma

EMA_ALPHA = 0.2          # weight for new outcome vs history
SUCCESS_THRESHOLD = 15.0  # agitation must drop by this much to count as success


def _recipes_col() -> chromadb.Collection:
    return get_chroma().get_or_create_collection("comfort_recipes")


def store_recipe(trigger: str, action_sequence: list[str], outcome: str) -> str:
    """Store a new comfort recipe. Returns the recipe_id."""
    recipe_id = str(uuid.uuid4())
    col = _recipes_col()
    col.add(
        ids=[recipe_id],
        documents=[trigger],
        metadatas=[{
            "action_sequence": ",".join(action_sequence),
            "outcome": outcome,
            "success_rate": 0.5,  # start neutral
            "times_used": 0,
            "last_used": time.time(),
        }],
    )
    return recipe_id


def update_recipe_outcome(recipe_id: str, agitation_before: float, agitation_after: float) -> None:
    """Update recipe success_rate with EMA based on observed agitation change.

    success = 1.0 if agitation dropped by >= SUCCESS_THRESHOLD, else 0.0
    new_rate = (1 - EMA_ALPHA) * old_rate + EMA_ALPHA * success
    """
    col = _recipes_col()
    try:
        result = col.get(ids=[recipe_id], include=["metadatas"])
    except Exception:
        return

    if not result["ids"]:
        return

    meta = result["metadatas"][0]
    old_rate = float(meta.get("success_rate", 0.5))
    success = 1.0 if (agitation_before - agitation_after) >= SUCCESS_THRESHOLD else 0.0
    new_rate = (1 - EMA_ALPHA) * old_rate + EMA_ALPHA * success

    col.update(
        ids=[recipe_id],
        metadatas=[{
            **meta,
            "success_rate": round(new_rate, 4),
            "times_used": int(meta.get("times_used", 0)) + 1,
            "last_used": time.time(),
        }],
    )
