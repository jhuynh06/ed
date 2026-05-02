/**
 * Integration test for useSSE hook.
 * Uses a mock EventSource to simulate SSE events.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useSSE } from '../use-sse'

// Mock EventSource
class MockEventSource {
  static instance: MockEventSource | null = null
  onopen: (() => void) | null = null
  onmessage: ((event: { data: string }) => void) | null = null
  onerror: (() => void) | null = null
  url: string
  readyState = 0

  constructor(url: string) {
    this.url = url
    MockEventSource.instance = this
  }

  close() {
    this.readyState = 2
  }

  // Helper to simulate receiving an event
  emit(data: object) {
    this.onmessage?.({ data: JSON.stringify(data) })
  }
}

beforeEach(() => {
  vi.stubGlobal('EventSource', MockEventSource)
  MockEventSource.instance = null
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('useSSE', () => {
  it('starts disconnected', () => {
    const { result } = renderHook(() => useSSE())
    expect(result.current.connected).toBe(false)
  })

  it('sets connected on open', () => {
    const { result } = renderHook(() => useSSE())
    act(() => {
      MockEventSource.instance?.onopen?.()
    })
    expect(result.current.connected).toBe(true)
  })

  it('updates latestAgitation on agitation_update event', () => {
    const { result } = renderHook(() => useSSE())
    act(() => {
      MockEventSource.instance?.onopen?.()
      MockEventSource.instance?.emit({
        type: 'agitation_update',
        timestamp: 1000,
        score: 55,
        risk: 'medium',
      })
    })
    expect(result.current.latestAgitation?.score).toBe(55)
    expect(result.current.latestAgitation?.risk).toBe('medium')
  })

  it('accumulates agitation history', () => {
    const { result } = renderHook(() => useSSE())
    act(() => {
      MockEventSource.instance?.onopen?.()
      MockEventSource.instance?.emit({ type: 'agitation_update', timestamp: 1000, score: 20, risk: 'low' })
      MockEventSource.instance?.emit({ type: 'agitation_update', timestamp: 1003, score: 45, risk: 'medium' })
      MockEventSource.instance?.emit({ type: 'agitation_update', timestamp: 1006, score: 70, risk: 'high' })
    })
    expect(result.current.agitationHistory).toHaveLength(3)
    expect(result.current.agitationHistory[2].score).toBe(70)
  })

  it('caps agitation history at 120 entries', () => {
    const { result } = renderHook(() => useSSE())
    act(() => {
      MockEventSource.instance?.onopen?.()
      for (let i = 0; i < 130; i++) {
        MockEventSource.instance?.emit({ type: 'agitation_update', timestamp: 1000 + i, score: i % 100, risk: 'low' })
      }
    })
    expect(result.current.agitationHistory).toHaveLength(120)
  })

  it('adds episodes on episode_start and episode_end', () => {
    const { result } = renderHook(() => useSSE())
    act(() => {
      MockEventSource.instance?.onopen?.()
      MockEventSource.instance?.emit({ type: 'episode_start', id: 'ep1', timestamp: 1000, agitation: 65 })
    })
    expect(result.current.episodes).toHaveLength(1)
    expect(result.current.episodes[0].end).toBeUndefined()

    act(() => {
      MockEventSource.instance?.emit({ type: 'episode_end', id: 'ep1', duration: 120, peak: 78, outcome: 'calm_restored' })
    })
    expect(result.current.episodes[0].end?.outcome).toBe('calm_restored')
  })

  it('accumulates notifications up to 50', () => {
    const { result } = renderHook(() => useSSE())
    act(() => {
      MockEventSource.instance?.onopen?.()
      for (let i = 0; i < 55; i++) {
        MockEventSource.instance?.emit({
          type: 'notification',
          id: `notif_${i}`,
          message: `msg ${i}`,
          priority: 'info',
          mar_trace: null,
        })
      }
    })
    expect(result.current.notifications).toHaveLength(50)
  })

  it('sets disconnected and reconnects on error', () => {
    vi.useFakeTimers()
    const { result } = renderHook(() => useSSE())
    act(() => {
      MockEventSource.instance?.onopen?.()
    })
    expect(result.current.connected).toBe(true)

    act(() => {
      MockEventSource.instance?.onerror?.()
    })
    expect(result.current.connected).toBe(false)

    // After 3s, should reconnect
    act(() => {
      vi.advanceTimersByTime(3000)
    })
    expect(MockEventSource.instance).not.toBeNull()
    vi.useRealTimers()
  })
})
