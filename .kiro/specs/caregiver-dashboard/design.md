# Design: Caregiver Dashboard

## Architecture Overview

```
Backend (FastAPI)                    Dashboard (Next.js 15)
┌──────────────┐                    ┌──────────────────────────────┐
│ GET /sse/    │ ──── SSE ────────→ │  useSSE() hook               │
│   events     │                    │    ├─ agitation_update       │
│              │                    │    ├─ episode_start/end      │
│              │                    │    ├─ notification           │
│              │                    │    └─ vitals_update          │
├──────────────┤                    ├──────────────────────────────┤
│ GET /api/    │ ──── REST ───────→ │  Server Components           │
│   episodes   │                    │    ├─ Episode list (initial) │
│   summary    │                    │    ├─ Daily summary          │
│   vitals     │                    │    └─ Family clips           │
│   clips      │                    │                              │
├──────────────┤                    ├──────────────────────────────┤
│ POST /api/   │ ←── REST ──────── │  Client Actions              │
│   clips      │                    │    └─ Upload voice clip      │
└──────────────┘                    └──────────────────────────────┘
```

## Page Structure

```
app/
├── layout.tsx          # Sidebar nav + SSE provider
├── page.tsx            # Dashboard home — live timeline + status card
├── episodes/
│   └── page.tsx        # Event log with episode cards
├── vitals/
│   └── page.tsx        # HR trends + circadian patterns
├── family/
│   └── page.tsx        # Voice clip management
└── summary/
    └── page.tsx        # Claude-generated daily summary
```

## Component Tree

```
<RootLayout>
  <SSEProvider>                          ← "use client", connects to /sse/events
    <Sidebar />                          ← server component, static nav
    <main>
      {children}                         ← page content
    </main>
    <NotificationToast />                ← "use client", listens to SSE notifications
  </SSEProvider>
</RootLayout>

Dashboard Home (page.tsx):
  <StatusCard />                         ← current agitation level, bear connection status
  <AgitationTimeline />                  ← "use client", Recharts area chart, last 6h
  <RecentEpisodes limit={5} />           ← server component, fetches from /api/episodes
  <ActiveNotifications />                ← "use client", SSE-driven

Episodes Page:
  <EpisodeList />                        ← server component, paginated
    <EpisodeCard />                      ← expandable, shows MAR debate trace
      <AudioPlayer />                    ← "use client", plays episode audio

Vitals Page:
  <HRChart />                            ← "use client", Recharts line chart, 24h
  <CircadianHeatmap />                   ← "use client", agitation by hour-of-day
  <BaselineCard />                       ← server component, current baselines

Family Page:
  <ClipUploader />                       ← "use client", file input + upload
  <ClipList />                           ← server component, list with play/delete
    <ClipPlayer />                       ← "use client", audio playback

Summary Page:
  <DailySummary />                       ← server component, fetches + renders markdown
  <ExportPDF />                          ← "use client", triggers PDF generation
```

## SSE Event Types

```typescript
type SSEEvent =
  | { type: "agitation_update"; data: { timestamp: number; score: number; risk: string } }
  | { type: "episode_start"; data: { id: string; timestamp: number; agitation: number } }
  | { type: "episode_end"; data: { id: string; duration: number; peak: number; outcome: string } }
  | { type: "notification"; data: { id: string; message: string; priority: "info" | "warning" | "urgent"; mar_trace?: object } }
  | { type: "vitals_update"; data: { bpm: number; spo2: number; baseline_bpm: number } }
```

## SSE Hook

```typescript
// lib/sse.ts
"use client"
import { useEffect, useRef, useState, useCallback } from "react"

export function useSSE<T>(url: string) {
  const [data, setData] = useState<T | null>(null)
  const [connected, setConnected] = useState(false)
  const esRef = useRef<EventSource | null>(null)

  useEffect(() => {
    const es = new EventSource(url)
    esRef.current = es
    es.onopen = () => setConnected(true)
    es.onmessage = (e) => setData(JSON.parse(e.data))
    es.onerror = () => {
      setConnected(false)
      // reconnect with exponential backoff handled by EventSource spec
    }
    return () => es.close()
  }, [url])

  return { data, connected }
}
```

## Color System

| Agitation Level | Score Range | Color | Tailwind Class |
|----------------|-------------|-------|----------------|
| Calm | 0–29 | Green | `bg-emerald-500` |
| Mild | 30–59 | Yellow | `bg-amber-400` |
| Moderate | 60–79 | Orange | `bg-orange-500` |
| Severe | 80–100 | Red | `bg-red-600` |

| Notification Priority | Color | Icon |
|----------------------|-------|------|
| info | Blue | ℹ️ InfoCircle |
| warning | Amber | ⚠️ AlertTriangle |
| urgent | Red | 🚨 AlertOctagon |

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| SSE not WebSocket for dashboard | Simpler, unidirectional, auto-reconnect | Dashboard only receives, never sends real-time data |
| Server Components for initial data | Fetch on server, stream HTML | Faster first paint, less client JS |
| Recharts over Tremor | More customizable for timeline chart | Tremor is simpler but less flexible for custom time axes |
| shadcn/ui for all primitives | Consistent, accessible, Tailwind-native | Don't reinvent buttons/cards/dialogs |
| No auth beyond basic | Demo scope | Real product would need proper auth |

## Dependencies
- Next.js 15, React 19
- shadcn/ui (install: Button, Card, Badge, Dialog, Tabs, Toast)
- Recharts
- react-markdown (for daily summary)
- Tailwind CSS 4
