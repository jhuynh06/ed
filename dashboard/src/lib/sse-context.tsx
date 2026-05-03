"use client"

import { createContext, useContext } from 'react'
import { useSSE } from './use-sse'
import type { UseSSEReturn } from './sse-types'

const SSEContext = createContext<UseSSEReturn | null>(null)

export function SSEProvider({ children }: { children: React.ReactNode }) {
  const sse = useSSE()
  return <SSEContext.Provider value={sse}>{children}</SSEContext.Provider>
}

export function useSharedSSE(): UseSSEReturn {
  const ctx = useContext(SSEContext)
  if (!ctx) throw new Error('useSharedSSE must be inside SSEProvider')
  return ctx
}
