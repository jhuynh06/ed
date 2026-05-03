"use client"

import { useEffect, useState } from 'react'
import { Topbar } from '@/components/topbar'
import { FamilyClips } from '@/components/family-clips'
import { useSSE } from '@/lib/use-sse'

interface Clip {
  id: string
  name: string
  duration_s: number
  uploaded_at: number
}

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function FamilyPage() {
  const sse = useSSE()
  const [clips, setClips] = useState<Clip[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API}/family/clips`)
      .then(r => r.ok ? r.json() : [])
      .then(setClips)
      .catch(() => setClips([]))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="relative z-10 h-screen overflow-hidden max-w-[900px] mx-auto p-3 grid grid-rows-[auto_1fr] gap-3">
      <Topbar connected={sse.connected} />
      <div className="overflow-y-auto">
        {loading ? (
          <div className="card p-8 flex items-center justify-center">
            <div className="font-serif text-[15px] text-[var(--ink-3)]">Loading clips\u2026</div>
          </div>
        ) : (
          <FamilyClips clips={clips} />
        )}
      </div>
    </div>
  )
}
