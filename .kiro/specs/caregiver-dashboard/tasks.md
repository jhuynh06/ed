# Tasks: Caregiver Dashboard

## Implementation Order

### Phase 1: Project Setup
- [ ] Initialize Next.js 15 project with TypeScript, Tailwind, App Router | `dashboard/`
- [ ] Install shadcn/ui, add components: Button, Card, Badge, Dialog, Tabs, Toast | `dashboard/`
- [ ] Install Recharts, react-markdown | `dashboard/package.json`
- [ ] Create root layout with sidebar navigation | `dashboard/src/app/layout.tsx`

### Phase 2: SSE Infrastructure
- [ ] Implement `useSSE<T>` hook with auto-reconnect | `dashboard/src/lib/sse.ts`
- [ ] Create `SSEProvider` context that connects to backend `/sse/events` | `dashboard/src/components/providers/sse-provider.tsx`
- [ ] Define TypeScript types for all SSE event payloads | `dashboard/src/lib/types.ts`
- [ ] [P] Implement `NotificationToast` component — listens to SSE notifications | `dashboard/src/components/notification-toast.tsx`

### Phase 3: Dashboard Home
- [ ] `StatusCard` — current agitation level, bear connection status, color-coded | `dashboard/src/components/status-card.tsx`
- [ ] `AgitationTimeline` — Recharts area chart, last 6h, 1-min resolution, color bands | `dashboard/src/components/timeline/agitation-timeline.tsx`
- [ ] `RecentEpisodes` — server component, fetch last 5 episodes from `/api/episodes` | `dashboard/src/components/episodes/recent-episodes.tsx`
- [ ] Wire home page with all components | `dashboard/src/app/page.tsx`

### Phase 4: Feature Pages
- [ ] Episodes page — `EpisodeList` with `EpisodeCard` (expandable MAR trace) | `dashboard/src/app/episodes/page.tsx`
- [ ] [P] Vitals page — `HRChart` (24h line) + `CircadianHeatmap` (agitation by hour) | `dashboard/src/app/vitals/page.tsx`
- [ ] [P] Family page — `ClipUploader` + `ClipList` with `ClipPlayer` | `dashboard/src/app/family/page.tsx`
- [ ] Summary page — `DailySummary` (markdown render) + `ExportPDF` button | `dashboard/src/app/summary/page.tsx`

### Phase 5: Polish
- [ ] Add aria-labels to all charts and interactive elements | all chart components
- [ ] Ensure color is never the only indicator (add icons to severity badges) | `dashboard/src/components/`
- [ ] Add loading skeletons for server component data fetches | `dashboard/src/components/`

## Verification
- [ ] SSE connection establishes to backend, receives agitation_update events
- [ ] Agitation timeline renders with correct color bands (green/yellow/orange/red)
- [ ] Notification toast appears within 1s of backend SSE event
- [ ] Episode cards expand to show MAR debate trace
- [ ] Voice clip upload → stored on backend → playable from clip list
- [ ] Daily summary renders Claude-generated markdown correctly
- [ ] All interactive elements keyboard-navigable
