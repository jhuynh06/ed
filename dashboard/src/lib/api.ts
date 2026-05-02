/**
 * API helpers — fetch from the FastAPI backend.
 * Falls back to mock data when the backend is unreachable.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`)
  return res.json()
}

// ── Patients ──

export interface PatientAPI {
  id: string
  name: string
  age: number
  stage: string
  companion: string
  baseline_hr: number
  since_date: string
}

export function getPatients() {
  return apiFetch<PatientAPI[]>('/patients')
}

export function getPatient(id: string) {
  return apiFetch<PatientAPI>(`/patients/${id}`)
}

// ── Episodes ──

export function getEpisodes(patientId: string, limit = 20) {
  return apiFetch<Record<string, unknown>[]>(`/episodes?patient_id=${patientId}&limit=${limit}`)
}

// ── Vitals ──

export function getVitals(patientId: string, hours = 24) {
  return apiFetch<Record<string, unknown>[]>(`/vitals?patient_id=${patientId}&hours=${hours}`)
}

// ── Daily Summary ──

export function getDailySummary(patientId: string) {
  return apiFetch<Record<string, unknown>>(`/summary/daily?patient_id=${patientId}`)
}

// ── Family Clips ──

export function getFamilyClips(patientId: string) {
  return apiFetch<Record<string, unknown>[]>(`/family/clips?patient_id=${patientId}`)
}

// ── Medications ──

export function getMedications(patientId: string) {
  return apiFetch<Record<string, unknown>[]>(`/medications?patient_id=${patientId}`)
}

// ── Chat ──

export function getChatMessages(patientId: string, limit = 50) {
  return apiFetch<Record<string, unknown>[]>(`/chat?patient_id=${patientId}&limit=${limit}`)
}

export function sendChatMessage(patientId: string, sender: string, content: string, msgType = 'text') {
  return apiFetch<{ status: string }>(`/chat?patient_id=${patientId}&sender=${sender}&content=${encodeURIComponent(content)}&msg_type=${msgType}`, {
    method: 'POST',
  })
}

export function clearChat(patientId: string) {
  return fetch(`${API_BASE}/chat?patient_id=${patientId}`, { method: 'DELETE' })
}

// ── Notes ──

export function getNotes(patientId: string, days = 7) {
  return apiFetch<Record<string, unknown>[]>(`/notes?patient_id=${patientId}&days=${days}`)
}

// ── Status ──

export function getStatus() {
  return apiFetch<Record<string, unknown>>('/status')
}
