---
title: Theodore — Code Standards
inclusion: always
---

# Code Standards

## General Rules
- Write minimal code. No speculative abstractions. YAGNI.
- Every function does one thing. If it needs a comment explaining "what", rename it.
- No hardcoded secrets. All API keys via environment variables.
- Prefer `search_symbols` and `find_references` over grep for code navigation (LSP-first).
- Use `pattern_search` for AST-level queries before text search.

## Python (Backend)
- Python 3.11, type hints on all function signatures
- Pydantic models for all data boundaries (WebSocket messages, tool inputs/outputs, API responses)
- async/await everywhere — no blocking calls in the event loop
- FastAPI dependency injection for shared state (Chroma client, SQLite connection)
- Docstrings on public functions only, Google style
- f-strings over .format() or %
- Imports: stdlib → third-party → local, separated by blank lines

## TypeScript (Dashboard)
- Strict mode enabled, no `any` types
- React Server Components by default, `"use client"` only when needed
- shadcn/ui components — don't reinvent UI primitives
- Tailwind utility classes, no custom CSS unless absolutely necessary
- Named exports, no default exports (except page.tsx / layout.tsx)
- Zod for runtime validation of SSE payloads

## C++ (Firmware)
- Arduino framework conventions
- `snake_case` for everything
- No dynamic memory allocation after setup() completes
- All sensor reads behind a driver abstraction (easy to mock)
- JSON messages via ArduinoJson — always use `StaticJsonDocument` with known sizes
- WiFi reconnection logic must be non-blocking
- Watchdog timer enabled — no infinite loops without yield

## Git
- Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`
- Scope by subsystem: `feat(firmware):`, `feat(backend):`, `feat(dashboard):`
- One logical change per commit
- Branch naming: `feat/short-description`, `fix/short-description`
