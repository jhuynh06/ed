"use client"

import { usePatient } from '@/lib/patient-context'
import { X } from 'lucide-react'

export function PatientSidebar() {
  const { patients, active, setActiveId, sidebarOpen, toggleSidebar } = usePatient()

  if (!sidebarOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-[oklch(0.15_0.01_60_/_0.3)]"
        onClick={toggleSidebar}
      />

      {/* Sidebar panel */}
      <div className="fixed top-0 left-0 z-50 h-full w-80 bg-[var(--paper-2)] border-r border-[var(--line)] shadow-[4px_0_24px_oklch(0.3_0.02_60_/_0.12)] flex flex-col">
        {/* Header */}
        <div className="p-4 pb-3 border-b border-[var(--line-soft)] flex items-center justify-between">
          <div>
            <div className="micro">Patient roster</div>
            <h2 className="font-serif text-[18px] font-normal tracking-tight leading-tight m-0 mt-0.5">
              Patients
            </h2>
          </div>
          <button
            onClick={toggleSidebar}
            className="btn btn-icon btn-ghost"
            aria-label="Close sidebar"
          >
            <X size={16} />
          </button>
        </div>

        {/* Patient list */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
          {patients.map((patient) => {
            const isActive = patient.id === active.id
            return (
              <button
                key={patient.id}
                onClick={() => {
                  setActiveId(patient.id)
                  toggleSidebar()
                }}
                className={`w-full text-left p-3 rounded-xl border transition-all cursor-pointer ${
                  isActive
                    ? 'bg-[var(--paper)] border-[var(--ink-4)] shadow-[var(--shadow-card)]'
                    : 'bg-transparent border-transparent hover:bg-[var(--paper-3)] hover:border-[var(--line)]'
                }`}
              >
                <div className="flex items-center gap-3">
                  {/* Avatar */}
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center font-serif text-[16px] flex-none ${
                    isActive
                      ? 'bg-[var(--ink)] text-[var(--paper)]'
                      : 'bg-[var(--paper-3)] text-[var(--ink-2)] border border-[var(--line)]'
                  }`}>
                    {patient.avatar}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-serif text-[14px] font-medium truncate">{patient.name}</span>
                      {isActive && <span className="chip calm">Active</span>}
                    </div>
                    <div className="micro mt-0.5">
                      {patient.age}y · {patient.stage} · {patient.companion}
                    </div>
                  </div>
                </div>

                {/* Quick stats */}
                <div className="flex gap-4 mt-2 ml-[52px]">
                  <div>
                    <div className="font-mono text-[8px] text-[var(--ink-3)] uppercase tracking-widest">HR base</div>
                    <div className="font-mono text-[12px] text-[var(--ink)]">{patient.baselineHr} bpm</div>
                  </div>
                  <div>
                    <div className="font-mono text-[8px] text-[var(--ink-3)] uppercase tracking-widest">Since</div>
                    <div className="font-mono text-[12px] text-[var(--ink)]">{patient.since}</div>
                  </div>
                  <div>
                    <div className="font-mono text-[8px] text-[var(--ink-3)] uppercase tracking-widest">Stage</div>
                    <div className="font-mono text-[12px] text-[var(--ink)]">{patient.stage}</div>
                  </div>
                </div>
              </button>
            )
          })}
        </div>

        {/* Footer */}
        <div className="p-4 pt-3 border-t border-[var(--line-soft)]">
          <div className="micro text-center">{patients.length} patients enrolled</div>
        </div>
      </div>
    </>
  )
}
