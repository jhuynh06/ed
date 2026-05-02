---
name: block-secrets
description: Scan staged files for API keys, tokens, and secrets before commit. Hard block — no exceptions.
trigger:
  type: userTriggered
---

## Instructions

When triggered (before committing), scan all staged files for secrets:

1. Run `git diff --cached --name-only` to get staged files.

2. For each staged file, scan for these patterns:
   - `sk-ant-` (Anthropic keys)
   - `sk-` followed by 20+ alphanumeric chars (generic secret keys)
   - `gsk_` (Groq keys)
   - `sk-cart-` (Cartesia keys)
   - `AKIA` (AWS access keys)
   - `ghp_` or `gho_` (GitHub tokens)
   - `-----BEGIN.*PRIVATE KEY-----`
   - Base64 strings longer than 50 characters that look like tokens
   - Any line matching `password\s*=\s*["\'][^"\']+["\']` (hardcoded passwords)

3. Exclude from scanning:
   - `.env.example` (contains placeholder patterns, not real keys)
   - `*.md` files (documentation may reference key formats)
   - Binary files

4. If ANY secret pattern is found:
   - **BLOCK the commit**
   - List each file and line number where a secret was detected
   - Suggest: "Move this value to .env and reference via environment variable"

5. If no secrets found, confirm it's safe to proceed.
