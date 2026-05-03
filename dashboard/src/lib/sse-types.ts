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

export const SensorUpdateSchema = z.object({
  type: z.literal("sensor_update"),
  timestamp: z.number(),
  imu_jerk: z.number(),
  imu_stillness_s: z.number(),
  imu_hug: z.boolean(),
  imu_rocking: z.boolean(),
  imu_fall: z.boolean(),
  touch_any: z.boolean(),
  touch_squeeze: z.number(),
  touch_petting: z.boolean(),
  touch_grip_s: z.number(),
  touch_active_pads: z.array(z.number()),
  hr_valid: z.boolean(),
  hr_bpm: z.number(),
});

export const TranscriptionSchema = z.object({
  type: z.literal("transcription"),
  text: z.string(),
  emotion: z.string(),
  valence: z.number(),
  arousal: z.number(),
  language: z.string().optional(),
  timestamp: z.number(),
});

export const SSEEventSchema = z.discriminatedUnion("type", [
  AgitationUpdateSchema,
  EpisodeStartSchema,
  EpisodeEndSchema,
  NotificationSchema,
  VitalsUpdateSchema,
  SensorUpdateSchema,
  TranscriptionSchema,
]);

// ── TypeScript types (inferred from Zod) ─────────────────────────────

export type AgitationUpdate = z.infer<typeof AgitationUpdateSchema>;
export type EpisodeStart = z.infer<typeof EpisodeStartSchema>;
export type EpisodeEnd = z.infer<typeof EpisodeEndSchema>;
export type CriticVerdict = z.infer<typeof CriticVerdictSchema>;
export type Notification = z.infer<typeof NotificationSchema>;
export type VitalsUpdate = z.infer<typeof VitalsUpdateSchema>;
export type SensorUpdate = z.infer<typeof SensorUpdateSchema>;
export type Transcription = z.infer<typeof TranscriptionSchema>;
export type SSEEvent = z.infer<typeof SSEEventSchema>;

export type RiskLevel = "low" | "medium" | "high";
export type NotificationPriority = "info" | "warning" | "urgent";

// ── Backend REST types ────────────────────────────────────────────────

export interface BackendStatus {
  score: number;
  risk: string;
  bear_connected: boolean;
  updated_at: number;
}

export interface SundowningStatus {
  active: boolean;
  confidence: number;
  peak_hour: number | null;
}

// ── SSE hook return type ──────────────────────────────────────────────

export interface UseSSEReturn {
  connected: boolean;
  latestAgitation: AgitationUpdate | null;
  agitationHistory: AgitationUpdate[];
  episodes: Array<{ start: EpisodeStart; end?: EpisodeEnd }>;
  notifications: Notification[];
  latestVitals: VitalsUpdate | null;
  latestSensor: SensorUpdate | null;
  transcriptions: Transcription[];
}
