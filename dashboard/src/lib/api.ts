/**
 * API client — connects to the FastAPI backend.
 * All functions return typed data matching the backend Pydantic models.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) throw new Error(`API ${path}: ${res.status}`)
  return res.json()
}

async function post<T>(path: string, body?: FormData | Record<string, unknown>): Promise<T> {
  const opts: RequestInit = { method: "POST" }
  if (body instanceof FormData) {
    opts.body = body
  } else if (body) {
    opts.headers = { "Content-Type": "application/json" }
    opts.body = JSON.stringify(body)
  }
  const res = await fetch(`${API_BASE}${path}`, opts)
  if (!res.ok) throw new Error(`API POST ${path}: ${res.status}`)
  return res.json()
}

async function del(path: string): Promise<void> {
  const res = await fetch(`${API_BASE}${path}`, { method: "DELETE" })
  if (!res.ok && res.status !== 204) throw new Error(`API DELETE ${path}: ${res.status}`)
}

// ── Status ───────────────────────────────────────────────────────────

export interface Status {
  score: number
  risk: string
  bear_connected: boolean
  updated_at: number
}

export const fetchStatus = () => get<Status>("/status")

// ── Episodes ─────────────────────────────────────────────────────────

export interface Episode {
  id: string
  started_at: number
  ended_at: number | null
  peak: number | null
  outcome: string | null
  mar_trace: Array<{ critic: string; verdict: string; feedback: string }> | null
}

export const fetchEpisodes = (limit = 20) =>
  get<Episode[]>(`/episodes?limit=${limit}`)

export const fetchEpisode = (id: string) =>
  get<Episode>(`/episodes/${id}`)

// ── Vitals ───────────────────────────────────────────────────────────

export interface Vital {
  id: number
  recorded_at: number
  bpm: number
  spo2: number
  baseline: number
}

export const fetchVitals = (hours = 24) =>
  get<Vital[]>(`/vitals?hours=${hours}`)

// ── Daily Summary ────────────────────────────────────────────────────

export interface DailySummary {
  patient_name: string
  date: string
  summary: string
  mood_arc: string
  episode_count: number
  sundowning_detected: boolean
  trend: string
  cdr_total: number | null
  action_items: string[]
  generated_at: number
}

export const fetchDailySummary = () => get<DailySummary>("/summary/daily")

// ── Family Clips ─────────────────────────────────────────────────────

export interface Clip {
  id: string
  label: string
  relation: string
  filename: string
  uploaded_at: number
}

export const fetchClips = () => get<Clip[]>("/family/clips")

export const uploadClip = (file: File, label: string, relation: string) => {
  const form = new FormData()
  form.append("file", file)
  return post<Clip>(`/family/clips?label=${encodeURIComponent(label)}&relation=${encodeURIComponent(relation)}`, form)
}

export const deleteClip = (id: string) => del(`/family/clips/${id}`)

export const clipAudioUrl = (id: string) => `${API_BASE}/family/clips/${id}/audio`

// ── Medications ──────────────────────────────────────────────────────

export interface Medication {
  id: string
  name: string
  dosage: string
  schedule: string
  notes: string
}

export const fetchMedications = () => get<Medication[]>("/medications")

export const addMedication = (name: string, dosage: string, schedule: string, notes = "") =>
  post<Medication>(`/medications?name=${encodeURIComponent(name)}&dosage=${encodeURIComponent(dosage)}&schedule=${encodeURIComponent(schedule)}&notes=${encodeURIComponent(notes)}`)

export const deleteMedication = (id: string) => del(`/medications/${id}`)

// ── Metrics ──────────────────────────────────────────────────────────

export interface DailyMetrics {
  date_str: string
  hr_baseline: number
  agitation_baseline: number
  hrv_rmssd: number | null
  speech_minutes: number
  utterance_count: number
  mean_pause_s: number
  long_pause_ratio: number
  vocabulary_ttr: number
  suppression: { suppressed: boolean; remaining_s: number }
}

export interface WeeklyMetrics {
  period: string
  days_recorded: number
  avg_day_quality: number
  total_episodes: number
  avg_sleep_hours: number
  avg_speech_minutes: number
  avg_vocabulary_ttr: number | null
  daily: DailyMetrics[]
}

export const fetchDailyMetrics = () => get<DailyMetrics>("/metrics/daily")
export const fetchWeeklyMetrics = () => get<WeeklyMetrics>("/metrics/weekly")

// ── Caregiver Notes ──────────────────────────────────────────────────

export interface CaregiverNote {
  id: string
  note_type: string
  content: string
  created_at: number
}

export const fetchNotes = (days = 7) => get<CaregiverNote[]>(`/notes?days=${days}`)

export const addNote = (noteType: string, content: string) =>
  post<CaregiverNote>(`/notes?note_type=${encodeURIComponent(noteType)}&content=${encodeURIComponent(content)}`)

// ── Reports ──────────────────────────────────────────────────────────

export interface ExportReport {
  report_period_days: number
  generated_at: number
  patient_name: string
  summary: { total_episodes: number; avg_day_quality?: number; avg_sleep_hours?: number; avg_vocabulary_ttr?: number | null }
  episodes: Episode[]
  daily_metrics: DailyMetrics[]
  caregiver_notes: CaregiverNote[]
  medications: Medication[]
}

export const fetchReport = (days = 30) => get<ExportReport>(`/reports/export?days=${days}`)

// ── Mock Scenario (demo) ─────────────────────────────────────────────

export const triggerMockScenario = () => get<{ status: string }>("/mock/scenario")

// ── SSE URL ──────────────────────────────────────────────────────────

export const SSE_URL = `${API_BASE}/sse/events`
