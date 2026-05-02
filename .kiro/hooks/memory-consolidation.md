---
name: memory-consolidation
description: Trigger episodic-to-semantic memory consolidation — showcases Kiro hooks for judges
trigger:
  type: userTriggered
---

## Instructions

When triggered, run the memory consolidation process:

1. Read the memory architecture from steering doc `06-memory-architecture.md`.

2. Query the backend's episodic memory store for episodes from the last 24 hours.

3. Cluster episodes by embedding similarity (threshold: cosine distance < 0.2).

4. For clusters with 3+ episodes, generate a semantic summary describing the pattern.

5. Store the semantic memory and mark source episodes as "consolidated."

6. Update confidence scores: reinforced patterns get +0.1, unreinforced decay by 0.05.

7. Output a summary of what was consolidated for display on the dashboard.

This hook demonstrates the episodic → semantic consolidation pipeline described in the memory architecture. It's designed to be triggered during the demo to show judges how Ed learns patterns over time.
