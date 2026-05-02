---
name: env-validation
description: Validate environment files don't contain real secrets and all required vars are present
trigger:
  type: fileEdited
  patterns: ["**/.env", "**/.env.*"]
---

## Instructions

When an `.env` or `.env.*` file is edited:

1. Check that no real API keys or secrets are present (look for patterns like `sk-`, `key-`, base64 strings > 40 chars). If found, warn the user and suggest using placeholder values.

2. Verify these required environment variables are defined (can be placeholder values):
   - `ANTHROPIC_API_KEY`
   - `GROQ_API_KEY`
   - `CARTESIA_API_KEY` or `ELEVENLABS_API_KEY`
   - `CHROMA_HOST` (default: `localhost`)
   - `CHROMA_PORT` (default: `8000`)

3. If any required variable is missing, list what's missing and suggest adding it.
