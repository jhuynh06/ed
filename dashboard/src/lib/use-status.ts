"use client"

import { useEffect, useState } from 'react'
import type { SundowningStatus, BackendStatus } from './sse-types'

export function useSundowningStatus(pollMs = 30000) {
  const [status, setStatus] = useState<SundowningStatus | null>(null)

  useEffect(() => {
    const fetch_ = () =>
      fetch('/api/sundowning')
        .then(r => r.json())
        .then(setStatus)
        .catch(() => {})

    fetch_()
    const id = setInterval(fetch_, pollMs)
    return () => clearInterval(id)
  }, [pollMs])

  return status
}

export function useBearStatus(pollMs = 5000) {
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    const fetch_ = () =>
      fetch('/api/status')
        .then(r => r.json())
        .then((d: BackendStatus) => setConnected(d.bear_connected))
        .catch(() => setConnected(false))

    fetch_()
    const id = setInterval(fetch_, pollMs)
    return () => clearInterval(id)
  }, [pollMs])

  return connected
}
