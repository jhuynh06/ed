"use client"

import { createContext, useContext, useState, type ReactNode } from 'react'

export interface Patient {
  id: string
  name: string
  birthday: string   // ISO date string e.g. "1946-03-15"
  age: number        // derived from birthday
  avatar: string
  companion: string
  since: string
}

interface PatientContextValue {
  patients: Patient[]
  active: Patient | null
  setActiveId: (id: string) => void
  addPatient: (p: { name: string; birthday: string; companion: string }) => void
  removePatient: (id: string) => void
  sidebarOpen: boolean
  toggleSidebar: () => void
}

const PatientContext = createContext<PatientContextValue | null>(null)

let nextId = 1

export function PatientProvider({ children }: { children: ReactNode }) {
  const [patients, setPatients] = useState<Patient[]>([])
  const [activeId, setActiveId] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const active = patients.find(p => p.id === activeId) ?? patients[0] ?? null

  function addPatient(p: { name: string; birthday: string; companion: string }) {
    const id = `p${nextId++}`
    const now = new Date()
    const since = now.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
    const birthDate = new Date(p.birthday)
    const age = Math.floor((now.getTime() - birthDate.getTime()) / (365.25 * 24 * 60 * 60 * 1000))
    const newPatient: Patient = {
      id,
      name: p.name,
      birthday: p.birthday,
      age,
      avatar: p.name.charAt(0).toUpperCase(),
      companion: p.companion || 'Theodore',
      since,
    }
    setPatients(prev => [...prev, newPatient])
    if (!activeId) setActiveId(id)
  }

  function removePatient(id: string) {
    setPatients(prev => prev.filter(p => p.id !== id))
    if (activeId === id) setActiveId(null)
  }

  return (
    <PatientContext.Provider value={{
      patients,
      active,
      setActiveId,
      addPatient,
      removePatient,
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
