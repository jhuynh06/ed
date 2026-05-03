"use client"

import { useEffect, useState } from 'react'
import { DailyDigestCard } from '@/components/daily-digest-card'
import { Topbar } from '@/components/topbar'

type Digest = {
  patient_name: string
  date: string
  summary: string
  mood_arc: string
  episode_count: number
  sundowning_detected: boolean
  trend_direction: string
  cdr_total: number
  action_items: string[]
  generated_at: number
}

export default function SummaryPage() {
  const [digest, setDigest] = useState<Digest | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/summary/daily')
      .then(r => {
        if (!r.ok) throw new Error(`${r.status}`)
        return r.json()
      })
      .then(setDigest)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="relative z-10 h-screen overflow-hidden max-w-[900px] mx-auto p-3 grid grid-rows-[auto_1fr] gap-3">
      <Topbar />
      <div className="overflow-y-auto">
        {loading && (
          <div className="card p-8 flex items-center justify-center">
            <div className="font-serif text-[15px] text-[var(--ink-3)]">Generating summary…</div>
          </div>
        )}
        {error && (
          <div className="card p-8 flex items-center justify-center">
            <div className="font-serif text-[15px] text-[var(--rose)]">Backend offline — start the server to generate a summary.</div>
          </div>
        )}
        {digest && (
          <DailyDigestCard digest={{
            summary_markdown: digest.summary,
            mood_arc: digest.mood_arc,
            episode_count: digest.episode_count,
            sundowning_detected: digest.sundowning_detected,
            trend_direction: digest.trend_direction,
            cdr_total: digest.cdr_total,
            action_items: digest.action_items,
          }} />
        )}
      </div>
    </div>
  )
}
