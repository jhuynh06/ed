---
title: Theodore — Memory Architecture
inclusion: always
---

# Memory Architecture

Theodore uses a biologically-inspired memory system with episodic capture, semantic consolidation, confidence weighting, active curation, and associative retrieval.

## Three Memory Tiers

### 1. Episodic Memory (Chroma)
Each interaction becomes a timestamped episode with embeddings.
- Fields: `timestamp`, `sensor_summary`, `user_speech`, `agent_action`, `outcome`, `agitation_before`, `agitation_after`, `confidence`
- Stored in Chroma with metadata filtering by time, agitation level, action type

### 2. Semantic Memory (Chroma + SQLite)
Consolidated patterns abstracted from episodes.
- "User responds well to grandson's voice at 4pm"
- "Rocking motion + elevated HR precedes verbal agitation by ~3 minutes"
- Promoted from episodic when pattern appears 3+ times

### 3. Workflow Memory — Comfort Recipes (SQLite)
Proven intervention sequences stored as reusable action chains.
- Schema: `trigger_pattern`, `action_sequence[]`, `success_rate`, `times_used`
- Example: `["play_grandson_voice", "pause_30s", "start_breathing_pacer", "speak_reassurance"]`
- Retrieved by similarity to current agitation pattern

## Memory as Action — Active Curation Tools
Memory operations are Claude tool calls, not passive storage:
- `consolidate_pattern(episode_ids[])` — abstract episodes into semantic fact
- `evict_stale_memory(memory_id)` — remove outdated or contradicted memories
- `link_episodes(episode_a, episode_b, relationship)` — create associative links
- `store_comfort_recipe(trigger, actions, outcome)` — save successful intervention

## Confidence-Weighted Memory (DAM-LLM pattern)
- Each memory unit has a `confidence: float` (0–1)
- Confidence increases when reinforced by similar observations
- Confidence decays over time unless refreshed
- Retrieval prioritizes high-confidence memories
- One-off observations start at 0.3; consistent patterns reach 0.9+

## Episodic → Semantic Consolidation
Background process (can be triggered by Kiro hook or scheduled):
1. Query episodes from last 24 hours
2. Cluster by similarity (embedding distance < threshold)
3. For clusters with 3+ episodes, generate semantic summary via Claude
4. Store as semantic memory, mark source episodes as "consolidated"
5. Update confidence scores on related semantic memories

## Consolidation Prompt

```
You are analyzing a cluster of similar episodes from an elderly care companion.

Episodes:
{episodes_json}

These episodes share a common pattern. Describe the pattern in one clear sentence
that a caregiver would understand. Focus on: what triggers it, when it happens,
and what response worked best.

Example: "Margaret becomes agitated around 4pm when the house gets quiet,
and responds well to her grandson's recorded voice followed by guided breathing."
```

## Retrieval Code Pattern

```python
async def retrieve_memories(observation: str, top_k: int = 5) -> list[dict]:
    # 1. Embedding search across all collections
    episodic = chroma.get_collection("episodic").query(
        query_texts=[observation], n_results=top_k,
        where={"consolidated": False}
    )
    semantic = chroma.get_collection("semantic").query(
        query_texts=[observation], n_results=top_k
    )

    # 2. Merge and re-rank by confidence × similarity × time_boost
    all_results = []
    for doc, meta, dist in zip_results(episodic, semantic):
        age_hours = (time.time() - meta["timestamp"]) / 3600
        time_boost = 1.2 if age_hours < 24 else (1.0 if age_hours < 168 else 0.8)
        score = (1 - dist) * meta["confidence"] * time_boost
        all_results.append({"text": doc, "score": score, **meta})

    return sorted(all_results, key=lambda x: x["score"], reverse=True)[:top_k]
```
