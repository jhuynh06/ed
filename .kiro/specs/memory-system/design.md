# Design: Three-Tier Memory System

## Architecture Overview

```
                    ┌─────────────────────────┐
                    │     Claude Planner       │
                    │  (tool calls for memory) │
                    └────────┬────────────────┘
                             │
              ┌──────────────┼──────────────────┐
              ▼              ▼                   ▼
     ┌────────────┐  ┌──────────────┐  ┌────────────────┐
     │  Episodic   │  │   Semantic   │  │    Workflow     │
     │  (Chroma)   │  │(Chroma+SQL)  │  │ Comfort Recipes │
     │             │  │              │  │    (SQLite)     │
     └────────────┘  └──────────────┘  └────────────────┘
              ▲              ▲                   ▲
              │              │                   │
              └──────────────┼───────────────────┘
                             │
                    ┌────────────────┐
                    │  Memory Tools  │
                    │ (Claude calls) │
                    └────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     consolidate_pattern  evict_stale  store_comfort_recipe
     link_episodes        retrieve      decay_confidence
```

## Data Models

```python
class EpisodicMemory(BaseModel):
    id: str                        # uuid4
    timestamp: float
    sensor_summary: str            # semantic text from perception
    user_speech: str | None
    agent_actions: list[str]       # actions taken during episode
    outcome: str                   # calm_restored, escalated, no_change
    agitation_before: float
    agitation_after: float
    confidence: float = 0.3        # starts low, reinforced over time
    consolidated: bool = False
    linked_episodes: list[str] = []

class SemanticMemory(BaseModel):
    id: str
    created_at: float
    pattern: str                   # "User responds well to grandson's voice at 4pm"
    source_episode_ids: list[str]
    confidence: float
    keywords: list[str]            # for keyword-based retrieval fallback
    last_reinforced: float

class ComfortRecipe(BaseModel):
    id: str
    trigger_pattern: str           # semantic description of when to use
    trigger_embedding: list[float] # for cosine similarity matching
    action_sequence: list[str]     # ordered list of tool calls
    success_rate: float            # 0-1
    times_used: int
    last_used: float

class MemoryQuery(BaseModel):
    query_text: str
    time_range_hours: float | None = None
    min_confidence: float = 0.2
    top_k: int = 5
    include_recipes: bool = True
```

## Chroma Collections

| Collection | Documents | Metadata Filters |
|-----------|-----------|-----------------|
| `episodic` | sensor_summary + user_speech | timestamp, agitation_before, outcome, consolidated |
| `semantic` | pattern text | confidence, keywords, created_at |
| `recipes` | trigger_pattern | success_rate, times_used |

## SQLite Tables

```sql
CREATE TABLE episodes (
    id TEXT PRIMARY KEY,
    timestamp REAL,
    sensor_summary TEXT,
    user_speech TEXT,
    agent_actions TEXT,  -- JSON array
    outcome TEXT,
    agitation_before REAL,
    agitation_after REAL,
    confidence REAL DEFAULT 0.3,
    consolidated INTEGER DEFAULT 0
);

CREATE TABLE episode_links (
    episode_a TEXT REFERENCES episodes(id),
    episode_b TEXT REFERENCES episodes(id),
    relationship TEXT,
    created_at REAL
);

CREATE TABLE comfort_recipes (
    id TEXT PRIMARY KEY,
    trigger_pattern TEXT,
    action_sequence TEXT,  -- JSON array
    success_rate REAL DEFAULT 0.0,
    times_used INTEGER DEFAULT 0,
    last_used REAL
);

CREATE TABLE semantic_patterns (
    id TEXT PRIMARY KEY,
    pattern TEXT,
    source_episodes TEXT,  -- JSON array of episode IDs
    confidence REAL,
    keywords TEXT,         -- JSON array
    last_reinforced REAL
);
```

## Memory Tool Implementations

```python
@tool
def consolidate_pattern(episode_ids: list[str]) -> str:
    """Analyze episodes and extract a reusable semantic pattern."""
    # 1. Fetch episodes from Chroma + SQLite
    # 2. Send to Claude: "What pattern connects these episodes?"
    # 3. Store result in semantic collection
    # 4. Mark source episodes as consolidated
    # 5. Return the discovered pattern

@tool
def store_comfort_recipe(trigger: str, actions: list[str], outcome: str) -> str:
    """Save a successful intervention sequence for future reuse."""
    # 1. Embed trigger pattern
    # 2. Insert into recipes collection + SQLite
    # 3. Return recipe ID

@tool
def evict_stale_memory(memory_id: str) -> str:
    """Remove an outdated or contradicted memory."""
    # 1. Delete from Chroma collection
    # 2. Mark as evicted in SQLite (soft delete)
    # 3. Return confirmation

@tool
def link_episodes(episode_a: str, episode_b: str, relationship: str) -> str:
    """Create an associative link between two episodes."""
    # 1. Insert into episode_links table
    # 2. Update both episodes' linked_episodes arrays
    # 3. Return confirmation
```

## Retrieval Strategy

1. **Embedding search**: Query Chroma with semantic text, get top-k by cosine similarity
2. **Confidence weighting**: Re-rank results by `similarity * confidence`
3. **Recipe matching**: If agitation detected, also query recipes collection with current observation
4. **Time decay**: Boost recent memories (last 24h get 1.2x, last week 1.0x, older 0.8x)
5. **Merge**: Combine episodic + semantic + recipe results, deduplicate, return top-k

## Confidence Lifecycle

```
New episode created     → confidence = 0.3
Similar episode occurs  → confidence += 0.15 (cap at 1.0)
Promoted to semantic    → semantic confidence = avg(source episodes)
Daily decay (no reinforce) → confidence -= 0.05 (floor at 0.1)
Contradicted by new data   → confidence = max(0.1, confidence - 0.3)
```

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Dual storage (Chroma + SQLite) | Chroma for embeddings, SQLite for relational queries | Need both similarity search and time-range/metadata queries |
| Confidence starts at 0.3 | Low initial trust | One-off observations shouldn't dominate retrieval |
| Consolidation threshold = 3 episodes | Balance between signal and noise | Fewer = too noisy, more = too slow to learn |
| Recipes stored separately | Not mixed with episodic/semantic | Different retrieval pattern (trigger matching vs. context search) |

## Dependencies
- Chroma client (chromadb Python package)
- aiosqlite for async SQLite
- Anthropic SDK for consolidation prompts
