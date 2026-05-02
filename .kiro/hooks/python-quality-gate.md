---
name: python-quality-gate
description: Check Python code quality on save — type hints, Pydantic models, async patterns
trigger:
  type: fileEdited
  patterns: ["backend/**/*.py"]
---

## Instructions

When a Python file in `backend/` is edited, check:

1. **Type hints**: All function parameters and return types must have type annotations. Flag any missing ones.

2. **Pydantic boundaries**: If the file defines data structures crossing a boundary (WebSocket message, API response, tool input), they must be Pydantic `BaseModel` subclasses, not plain dicts.

3. **Async correctness**: If the file contains `async def`, verify no blocking calls (`time.sleep`, synchronous `requests`, synchronous file I/O). Suggest async alternatives.

4. **Import order**: stdlib → third-party → local, separated by blank lines.

Only report actual issues found. Don't report if everything looks good.
