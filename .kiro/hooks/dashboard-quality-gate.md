---
name: dashboard-quality-gate
description: Check React/TypeScript quality on save — no any types, accessibility, component patterns
trigger:
  type: fileEdited
  patterns: ["dashboard/**/*.tsx", "dashboard/**/*.ts"]
---

## Instructions

When a TypeScript/React file in `dashboard/` is edited, check:

1. **No `any` types**: Flag any use of `any`. Suggest proper types or `unknown`.

2. **Accessibility**: If the file renders interactive elements, verify `aria-label` or `aria-describedby` is present. Charts must have text descriptions.

3. **Client directive**: If the file uses hooks (`useState`, `useEffect`, event handlers), verify `"use client"` is at the top. If it doesn't use any client features, it should NOT have the directive.

4. **shadcn/ui**: If the file creates UI elements that shadcn/ui provides (buttons, cards, dialogs, badges), suggest using the shadcn component instead of custom HTML.

Only report actual issues found.
