"use client"

import { useEffect, useState, useCallback } from 'react'
import { SSEEventSchema, type UseSSEReturn, type SSEEvent, type AgitationUpdate, type EpisodeStart, type EpisodeEnd, type Notification, type VitalsUpdate } from './sse-types'

export function useSSE(): UseSSEReturn {
  const [connected, setConnected] = useState(false)
  const [latestAgitation, setLatestAgitation] = useState<AgitationUpdate | null>(null)
  const [agitationHistory, setAgitationHistory] = useState<AgitationUpdate[]>([])
  const [episodes, setEpisodes] = useState<Array<{ start: EpisodeStart; end?: EpisodeEnd }>>([])
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [latestVitals, setLatestVitals] = useState<VitalsUpdate | null>(null)

  const handleEvent = useCallback((event: SSEEvent) => {
    switch (event.type) {
      case 'agitation_update':
        setLatestAgitation(event)
        setAgitationHistory(prev => [...prev, event].slice(-360)) // 6 hours at 1/min
        break

      case 'episode_start':
        setEpisodes(prev => [...prev, { start: event }])
        break

      case 'episode_end':
        setEpisodes(prev =>
          prev.map(ep =>
            ep.start.id === event.id
              ? { ...ep, end: event }
              : ep
          )
        )
        break

      case 'notification':
        setNotifications(prev => [event, ...prev].slice(0, 50))
        break

      case 'vitals_update':
        setLatestVitals(event)
        break
    }
  }, [])

  useEffect(() => {
    let eventSource: EventSource | null = null
    let reconnectTimeout: NodeJS.Timeout | null = null
    let retryDelay = 1000

    const connect = () => {
      try {
        eventSource = new EventSource('/api/sse')

        eventSource.onopen = () => {
          setConnected(true)
          retryDelay = 1000 // reset on successful connect
          console.log('SSE connected')
        }

        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            const parsed = SSEEventSchema.safeParse(data)

            if (parsed.success) {
              handleEvent(parsed.data)
            } else {
              console.warn('Invalid SSE event:', parsed.error)
            }
          } catch (error) {
            console.error('Failed to parse SSE event:', error)
          }
        }

        eventSource.onerror = () => {
          setConnected(false)
          eventSource?.close()

          reconnectTimeout = setTimeout(() => {
            console.log(`Reconnecting SSE (delay: ${retryDelay}ms)...`)
            retryDelay = Math.min(retryDelay * 2, 30000)
            connect()
          }, retryDelay)
        }
      } catch (error) {
        console.error('Failed to connect SSE:', error)
        setConnected(false)
      }
    }

    connect()

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout)
      if (eventSource) eventSource.close()
    }
  }, [handleEvent])

  return {
    connected,
    latestAgitation,
    agitationHistory,
    episodes,
    notifications,
    latestVitals
  }
}
