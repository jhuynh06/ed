# Tasks: Three-Tier Memory System

## Implementation Order

### Phase 1: Data Models & Storage Setup
- [ ] Define Pydantic models: `EpisodicMemory`, `SemanticMemory`, `ComfortRecipe`, `MemoryQuery` | `backend/app/models/memory.py`
- [ ] Create SQLite schema (episodes, episode_links, comfort_recipes, semantic_patterns) | `backend/app/memory/schema.sql`
- [ ] Initialize Chroma collections (episodic, semantic, recipes) at startup | `backend/app/memory/store.py`
- [ ] Database init function that creates tables + collections | `backend/app/memory/store.py`

### Phase 2: Episodic Memory
- [ ] `store_episode(episode: EpisodicMemory)` — write to both Chroma and SQLite | `backend/app/memory/episodic.py`
- [ ] `query_episodes(query: MemoryQuery) → list[EpisodicMemory]` — embedding search + metadata filter | `backend/app/memory/episodic.py`
- [ ] Wire episode storage into LangGraph — after executor completes, store the episode | `backend/app/agents/graph.py`

### Phase 3: Memory Tools (Claude-callable)
- [ ] `consolidate_pattern` tool — fetch episodes, prompt Claude for pattern, store semantic | `backend/app/memory/tools.py`
- [ ] `store_comfort_recipe` tool — embed trigger, insert into recipes collection + SQLite | `backend/app/memory/tools.py`
- [ ] `evict_stale_memory` tool — soft delete from Chroma + SQLite | `backend/app/memory/tools.py`
- [ ] `link_episodes` tool — insert into episode_links, update linked arrays | `backend/app/memory/tools.py`
- [ ] Register all tools with the planner agent | `backend/app/agents/planner.py`

### Phase 4: Retrieval & Ranking
- [ ] `retrieve_memories(observation: str, top_k: int) → list` — combined episodic + semantic search | `backend/app/memory/retrieval.py`
- [ ] Confidence-weighted re-ranking: `score = similarity * confidence * time_boost` | `backend/app/memory/retrieval.py`
- [ ] [P] `match_comfort_recipe(observation: str) → ComfortRecipe | None` — cosine similarity > 0.8 threshold | `backend/app/memory/workflow.py`

### Phase 5: Confidence & Consolidation
- [ ] `decay_confidence()` — batch update: confidence -= 0.05 where not reinforced today | `backend/app/memory/consolidation.py`
- [ ] `reinforce(memory_id: str)` — confidence += 0.15, cap at 1.0 | `backend/app/memory/consolidation.py`
- [ ] `run_consolidation()` — cluster recent episodes, generate semantic memories for clusters ≥ 3 | `backend/app/memory/consolidation.py`
- [ ] Wire consolidation into the memory-consolidation Kiro hook | `backend/app/memory/consolidation.py`

## Verification
- [ ] Episode stored → retrievable by embedding search within 1 second
- [ ] 3 similar episodes → consolidation produces a semantic memory
- [ ] Comfort recipe with success_rate > 0.7 → matched when similar trigger occurs
- [ ] Confidence decays from 0.3 to 0.25 after 1 simulated day without reinforcement
- [ ] Evicted memory no longer appears in retrieval results
- [ ] Linked episodes appear in each other's context during retrieval
