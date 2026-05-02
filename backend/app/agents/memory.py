"""Memory node — retrieves relevant episodic/semantic memories and comfort recipes.

Uses Chroma for embedding search with confidence × similarity × time_boost ranking.
Reference: memory-architecture steering doc, DAM-LLM pattern.
"""

from __future__ import annotations

import time

import chromadb

from app.agents.state import AgentState
from app.memory.bandit import select_recipe
from app.memory.store import get_chroma


def _ensure_collections(client: chromadb.ClientAPI) -> tuple:
    """Get or create the three memory collections."""
    episodic = client.get_or_create_collection("episodic")
    semantic = client.get_or_create_collection("semantic")
    recipes = client.get_or_create_collection("comfort_recipes")
    return episodic, semantic, recipes


def _rank_results(docs: list[str], metas: list[dict], distances: list[float]) -> list[dict]:
    """Re-rank by confidence × (1 - distance) × time_boost."""
    ranked = []
    now = time.time()
    for doc, meta, dist in zip(docs, metas, distances):
        age_hours = (now - meta.get("timestamp", now)) / 3600
        time_boost = 1.2 if age_hours < 24 else (1.0 if age_hours < 168 else 0.8)
        confidence = meta.get("confidence", 0.5)
        score = (1 - dist) * confidence * time_boost
        ranked.append({"text": doc, "score": score, **meta})
    return sorted(ranked, key=lambda x: x["score"], reverse=True)


async def memory_node(state: AgentState) -> AgentState:
    """Retrieve relevant memories and best-matching comfort recipe."""
    observation = state.get("semantic_observation", "")
    if not observation:
        return {**state, "memories": [], "comfort_recipe": None}

    client = get_chroma()
    episodic_col, semantic_col, recipes_col = _ensure_collections(client)

    memories: list[dict] = []

    # Query episodic memories (unconsolidated only)
    try:
        if episodic_col.count() > 0:
            ep_results = episodic_col.query(
                query_texts=[observation],
                n_results=min(3, episodic_col.count()),
                where={"consolidated": False} if episodic_col.count() > 0 else None,
            )
            if ep_results["documents"] and ep_results["documents"][0]:
                memories.extend(
                    _rank_results(
                        ep_results["documents"][0],
                        ep_results["metadatas"][0],
                        ep_results["distances"][0],
                    )
                )
    except Exception:
        pass  # Empty collection — fine for first run

    # Query semantic memories
    try:
        if semantic_col.count() > 0:
            sem_results = semantic_col.query(
                query_texts=[observation],
                n_results=min(3, semantic_col.count()),
            )
            if sem_results["documents"] and sem_results["documents"][0]:
                memories.extend(
                    _rank_results(
                        sem_results["documents"][0],
                        sem_results["metadatas"][0],
                        sem_results["distances"][0],
                    )
                )
    except Exception:
        pass

    # Find best comfort recipe — fetch top 3 by similarity, select via Thompson sampling
    comfort_recipe = None
    try:
        if recipes_col.count() > 0:
            n = min(3, recipes_col.count())
            recipe_results = recipes_col.query(
                query_texts=[observation],
                n_results=n,
            )
            if recipe_results["documents"] and recipe_results["documents"][0]:
                candidates = [
                    {"description": doc, "id": rid, **meta}
                    for doc, meta, rid in zip(
                        recipe_results["documents"][0],
                        recipe_results["metadatas"][0],
                        recipe_results["ids"][0],
                    )
                ]
                # Thompson sampling picks best recipe for current time-of-day
                best_id = select_recipe([c["id"] for c in candidates])
                comfort_recipe = next(c for c in candidates if c["id"] == best_id)
    except Exception:
        pass

    # Sort all memories by score, keep top 5
    memories.sort(key=lambda x: x.get("score", 0), reverse=True)

    return {**state, "memories": memories[:5], "comfort_recipe": comfort_recipe}
