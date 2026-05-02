"use client"

import { createContext, useContext, useState, type ReactNode } from 'react'

export interface Patient {
  id: string
  name: string
  age: number
  stage: string
  avatar: string       // single letter
  baselineHr: number
  companion: string    // name of their plushie
  since: string        // e.g. "Mar 2026"
}

const PATIENTS: Patient[] = [
  { id: 'p1', name: 'Margaret Chen', age: 78, stage: 'Mild', avatar: 'M', baselineHr: 72, companion: 'Ed', since: 'Mar 2026' },
  { id: 'p2', name: 'Robert Williams', age: 82, stage: 'Moderate', avatar: 'R', baselineHr: 68, companion: 'Benny', since: 'Jan 2026' },
  { id: 'p3', name: 'Dorothy Park', age: 75, stage: 'Mild', avatar: 'D', baselineHr: 76, companion: 'Clover', since: 'Apr 2026' },
  { id: 'p4', name: 'James Okafor', age: 80, stage: 'Moderate', avatar: 'J', baselineHr: 70, companion: 'Maple', since: 'Feb 2026' },
]

interface PatientContextValue {
  patients: Patient[]
  active: Patient
  setActiveId: (id: string) => void
  sidebarOpen: boolean
  toggleSidebar: () => void
}

const PatientContext = createContext<PatientContextValue | null>(null)

export function PatientProvider({ children }: { children: ReactNode }) {
  const [activeId, setActiveId] = useState('p1')
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const active = PATIENTS.find(p => p.id === activeId) ?? PATIENTS[0]

  return (
    <PatientContext.Provider value={{
      patients: PATIENTS,
      active,
      setActiveId,
      sidebarOpen,
      toggleSidebar: () => setSidebarOpen(prev => !prev),
    }}>
      {children}
    </PatientContext.Provider>
  )
}

export function usePatient() {
  const ctx = useContext(PatientContext)
  if (!ctx) throw new Error('usePatient must be used within PatientProvider')
  return ctx
}
