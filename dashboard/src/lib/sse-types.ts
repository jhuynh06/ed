/**
 * SSE event types — mirror the Pydantic models in backend/app/models/__init__.py
 * Validated at runtime with Zod before use in components.
 */

import { z } from "zod";

// ── Zod schemas (runtime validation) ─────────────────────────────────

export const AgitationUpdateSchema = z.object({
  type: z.literal("agitation_update"),
  timestamp: z.number(),
  score: z.number().min(0).max(100),
  risk: z.enum(["low", "medium", "high"]),
});

export const EpisodeStartSchema = z.object({
  type: z.literal("episode_start"),
  id: z.string(),
  timestamp: z.number(),
  agitation: z.number(),
});

export const EpisodeEndSchema = z.object({
  type: z.literal("episode_end"),
  id: z.string(),
  duration: z.number(),
  peak: z.number(),
  outcome: z.string(),
});

export const CriticVerdictSchema = z.object({
  critic: z.string(),
  verdict: z.enum(["APPROVE", "REVISE"]),
  feedback: z.string(),
});

export const NotificationSchema = z.object({
  type: z.literal("notification"),
  id: z.string(),
  message: z.string(),
  priority: z.enum(["info", "warning", "urgent"]),
  mar_trace: z.array(CriticVerdictSchema).nullable().optional(),
});

export const VitalsUpdateSchema = z.object({
  type: z.literal("vitals_update"),
  bpm: z.number(),
  spo2: z.number(),
  baseline_bpm: z.number(),
});

export const SSEEventSchema = z.discriminatedUnion("type", [
  AgitationUpdateSchema,
  EpisodeStartSchema,
  EpisodeEndSchema,
  NotificationSchema,
  VitalsUpdateSchema,
]);

// ── TypeScript types (inferred from Zod) ─────────────────────────────

export type AgitationUpdate = z.infer<typeof AgitationUpdateSchema>;
export type EpisodeStart = z.infer<typeof EpisodeStartSchema>;
export type EpisodeEnd = z.infer<typeof EpisodeEndSchema>;
export type CriticVerdict = z.infer<typeof CriticVerdictSchema>;
export type Notification = z.infer<typeof NotificationSchema>;
export type VitalsUpdate = z.infer<typeof VitalsUpdateSchema>;
export type SSEEvent = z.infer<typeof SSEEventSchema>;

export type RiskLevel = "low" | "medium" | "high";
export type NotificationPriority = "info" | "warning" | "urgent";

// ── SSE hook return type ──────────────────────────────────────────────

export interface UseSSEReturn {
  connected: boolean;
  latestAgitation: AgitationUpdate | null;
  episodes: Array<{ start: EpisodeStart; end?: EpisodeEnd }>;
  notifications: Notification[];
  latestVitals: VitalsUpdate | null;
}
