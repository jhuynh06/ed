# Feature: Three-Tier Memory System

## Status: draft

## Problem Statement
Ed needs to learn about each user over time — what calms them, what triggers agitation, family context. A simple RAG system loses nuance. We need episodic capture, semantic consolidation, and reusable comfort recipes with confidence-weighted retrieval.

## User Stories
- As the planner agent, I want to retrieve relevant memories so that interventions are personalized
- As the planner agent, I want to store successful interventions as comfort recipes so that proven sequences can be reused
- As the memory system, I want to consolidate repeated episodic patterns into semantic facts so that retrieval is efficient
- As a caregiver, I want to see discovered patterns on the dashboard so that I understand Ed's learning

## Functional Requirements
- REQ-001: When an episode ends, the system shall store it as an episodic memory in Chroma with timestamp, sensor summary, actions taken, and outcome
- REQ-002: When the planner needs context, the system shall retrieve top-k memories ranked by relevance × confidence score
- REQ-003: The planner agent shall have access to `consolidate_pattern()`, `evict_stale_memory()`, `link_episodes()`, and `store_comfort_recipe()` as Claude tool calls
- REQ-004: When a comfort recipe's trigger pattern matches the current observation (cosine similarity > 0.8), the system shall suggest the stored action sequence to the planner
- REQ-005: Each memory unit shall have a confidence score (0–1) that increases on reinforcement and decays at 0.05/day without refresh
- REQ-006: When 3+ episodes share a pattern (embedding cluster), consolidation shall produce a semantic memory

## Acceptance Criteria
- [ ] Episodes are stored and retrievable by time range and similarity
- [ ] Comfort recipes are matched and suggested correctly
- [ ] Confidence decay works over simulated time
- [ ] Consolidation produces semantic memories from clustered episodes
- [ ] Memory tools are callable by Claude and produce correct state changes

## Out of Scope
- Full Zettelkasten bidirectional linking (approximate with link_episodes tool)
- Graph database (use Chroma metadata + SQLite relations)
