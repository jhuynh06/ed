"use client"

import { useEffect, useState, useCallback } from 'react'
import { SSEEventSchema, type UseSSEReturn, type SSEEvent, type AgitationUpdate, type EpisodeStart, type EpisodeEnd, type Notification, type VitalsUpdate } from './sse-types'

export function useSSE(): UseSSEReturn {
  const [connected, setConnected] = useState(false)
  const [latestAgitation, setLatestAgitation] = useState<AgitationUpdate | null>(null)
  const [episodes, setEpisodes] = useState<Array<{ start: EpisodeStart; end?: EpisodeEnd }>>([])
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [latestVitals, setLatestVitals] = useState<VitalsUpdate | null>(null)

  const handleEvent = useCallback((event: SSEEvent) => {
    switch (event.type) {
      case 'agitation_update':
        setLatestAgitation(event)
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
        setNotifications(prev => [event, ...prev].slice(0, 50)) // Keep last 50
        break
      
      case 'vitals_update':
        setLatestVitals(event)
        break
    }
  }, [])

  useEffect(() => {
    let eventSource: EventSource | null = null
    let reconnectTimeout: NodeJS.Timeout | null = null

    const connect = () => {
      try {
        eventSource = new EventSource('/api/sse')
        
        eventSource.onopen = () => {
          setConnected(true)
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
          
          // Reconnect after 3 seconds
          reconnectTimeout = setTimeout(() => {
            console.log('Reconnecting SSE...')
            connect()
          }, 3000)
        }
      } catch (error) {
        console.error('Failed to connect SSE:', error)
        setConnected(false)
      }
    }

    connect()

    return () => {
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout)
      }
      if (eventSource) {
        eventSource.close()
      }
    }
  }, [handleEvent])

  return {
    connected,
    latestAgitation,
    episodes,
    notifications,
    latestVitals
  }
}