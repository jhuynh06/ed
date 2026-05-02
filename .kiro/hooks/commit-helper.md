---
name: commit-helper
description: Generate conventional commit messages scoped by subsystem
trigger:
  type: userTriggered
---

## Instructions

When triggered, analyze the current staged changes (`git diff --cached`) and generate a conventional commit message:

1. Determine the scope from changed file paths:
   - `firmware/` → scope is `firmware`
   - `backend/` → scope is `backend`
   - `dashboard/` → scope is `dashboard`
   - `.kiro/` → scope is `kiro`
   - Multiple scopes → list the primary one, mention others in body

2. Determine the type from the nature of changes:
   - New functionality → `feat`
   - Bug fix → `fix`
   - Documentation → `docs`
   - Code restructuring → `refactor`
   - Build/config → `chore`

3. Format: `type(scope): concise description`
   - Subject line ≤ 72 characters
   - Body explains "why" if not obvious
   - Reference spec name if implementing a spec feature

4. Present the message and ask for confirmation before committing.
