---
title: Ed — Next.js Dashboard Patterns
inclusion: fileMatch
fileMatch: "dashboard/**"
---

# Next.js Dashboard Patterns

## App Router Structure
- `app/page.tsx` — dashboard home (live agitation timeline + current status)
- `app/episodes/page.tsx` — event log with audio playback
- `app/vitals/page.tsx` — HR trends, circadian patterns
- `app/family/page.tsx` — voice clip management
- `app/summary/page.tsx` — Claude-generated daily caregiver summary
- `app/layout.tsx` — sidebar nav, global providers

## Component Conventions
- Server Components by default. Add `"use client"` only for interactivity.
- shadcn/ui for all UI primitives (Button, Card, Badge, Dialog, etc.)
- Tremor or Recharts for charts — pick one and stick with it
- All components in `src/components/` grouped by feature domain
- Props interfaces defined inline above the component, not in separate files

## SSE Integration
```typescript
// lib/sse.ts — reusable SSE hook
function useSSE<T>(url: string): { data: T | null; connected: boolean }
```
- Connect to `GET /sse/events` on the backend
- Parse event types: `agitation_update`, `episode_start`, `episode_end`, `notification`, `vitals`
- Use React state to accumulate timeline data
- Reconnect automatically on disconnect with exponential backoff

## Data Display Rules
- Agitation timeline: last 6 hours, 1-minute resolution, color-coded by severity
- HR chart: last 24 hours, 5-minute averages, baseline overlay
- Episode cards: timestamp, duration, peak agitation, intervention used, outcome
- Notifications: real-time toast + persistent list, color by priority
- Daily summary: Claude-generated markdown rendered with `react-markdown`

## Accessibility
- All charts must have `aria-label` descriptions
- Color is never the only indicator — use icons/patterns alongside
- Keyboard navigable — all interactive elements focusable
- Minimum contrast ratio 4.5:1 for text

## Page Wireframes

### Dashboard Home (`/`)
```
┌─────────────────────────────────────────────────────────┐
│ [Sidebar]  │  Ed Dashboard                        │
│            │                                            │
│ 🏠 Home    │  ┌─ Status Card ──────────────────────┐   │
│ 📋 Episodes│  │ 🟢 Calm (score: 22)  │ 🔗 Connected│   │
│ ❤️ Vitals  │  └────────────────────────────────────┘   │
│ 👨‍👩‍👧 Family │                                            │
│ 📝 Summary │  ┌─ Agitation Timeline (6h) ──────────┐   │
│            │  │ ▁▁▂▂▃▅▇█▇▅▃▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁ │   │
│            │  │ green──yellow──orange──red──orange── │   │
│            │  └────────────────────────────────────┘   │
│            │                                            │
│            │  ┌─ Recent Episodes ──────────────────┐   │
│            │  │ 4:32pm  Moderate (62) → Calm (18)  │   │
│            │  │ 2:15pm  Mild (35) → Calm (12)      │   │
│            │  └────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Episodes Page (`/episodes`)
```
┌─────────────────────────────────────────────────────────┐
│ [Sidebar]  │  Episodes                                  │
│            │                                            │
│            │  ┌─ Episode Card (expandable) ─────────┐  │
│            │  │ 🟠 4:32pm │ 8min │ Peak: 72         │  │
│            │  │ Intervention: comfort recipe #3      │  │
│            │  │ Outcome: calm restored               │  │
│            │  │                                      │  │
│            │  │ ▼ MAR Debate Trace                   │  │
│            │  │ ┌──────────────────────────────────┐ │  │
│            │  │ │ ✅ Clinical: APPROVE              │ │  │
│            │  │ │ ✏️ Tone: REVISE → rewrote msg     │ │  │
│            │  │ │ ✅ Privacy: APPROVE               │ │  │
│            │  │ └──────────────────────────────────┘ │  │
│            │  └──────────────────────────────────────┘  │
│            │                                            │
│            │  ┌─ Episode Card ──────────────────────┐  │
│            │  │ 🟡 2:15pm │ 3min │ Peak: 41         │  │
│            │  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Vitals Page (`/vitals`)
```
┌─────────────────────────────────────────────────────────┐
│ [Sidebar]  │  Vitals                                    │
│            │                                            │
│            │  ┌─ Heart Rate (24h) ─────────────────┐   │
│            │  │ 100─┐                               │   │
│            │  │  80─┤──baseline─────────────────    │   │
│            │  │  60─┤  ╱╲    ╱╲╱╲                   │   │
│            │  │     └──────────────────────────     │   │
│            │  │     12am  6am  12pm  6pm  now       │   │
│            │  └────────────────────────────────────┘   │
│            │                                            │
│            │  ┌─ Circadian Heatmap ────────────────┐   │
│            │  │ Mon  ░░░░░░░░░░▓▓░░░░▓▓██░░░░     │   │
│            │  │ Tue  ░░░░░░░░░░░░░░░░▓▓██▓▓░░     │   │
│            │  │ Wed  ░░░░░░░░░░░░░░░▓▓▓▓██░░░     │   │
│            │  │      12a  6a  12p  6p  12a          │   │
│            │  │ ░ calm  ▓ mild  █ moderate+         │   │
│            │  └────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Family Page (`/family`)
```
┌─────────────────────────────────────────────────────────┐
│ [Sidebar]  │  Family Voice Clips                        │
│            │                                            │
│            │  ┌─ Upload ───────────────────────────┐   │
│            │  │ [Drop audio file or click to browse]│   │
│            │  │ Label: ________  Relation: [v Jake] │   │
│            │  │                        [Upload]     │   │
│            │  └────────────────────────────────────┘   │
│            │                                            │
│            │  ┌─ Clips ───────────────────────────┐    │
│            │  │ 🎵 "I love you grandma" — Jake     │   │
│            │  │    ▶ [====●=========] 0:04  [🗑️]   │   │
│            │  │                                     │   │
│            │  │ 🎵 "Good morning mom" — Sarah       │   │
│            │  │    ▶ [====●=========] 0:06  [🗑️]   │   │
│            │  └────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```
