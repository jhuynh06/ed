"use client"

import { useState } from 'react'
import { usePatient } from '@/lib/patient-context'
import { X, Plus, Trash2 } from 'lucide-react'

function AddPatientForm({ onDone }: { onDone: () => void }) {
  const { addPatient } = usePatient()
  const [name, setName] = useState('')
  const [birthday, setBirthday] = useState('')
  const [companion, setCompanion] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim() || !birthday) return
    addPatient({
      name: name.trim(),
      birthday,
      companion: companion.trim() || 'Theodore',
    })
    setName('')
    setBirthday('')
    setCompanion('')
    onDone()
  }

  return (
    <form onSubmit={handleSubmit} className="p-3 space-y-2">
      <div className="micro mb-1">New patient</div>
      <input
        type="text"
        placeholder="Full name *"
        value={name}
        onChange={e => setName(e.target.value)}
        required
        className="w-full bg-[var(--paper-3)] border border-[var(--line)] rounded-lg px-3 py-2 text-[13px] placeholder:text-[var(--ink-4)]"
      />
      <div>
        <div className="micro mb-1">Birthday *</div>
        <input
          type="date"
          value={birthday}
          onChange={e => setBirthday(e.target.value)}
          required
          className="w-full bg-[var(--paper-3)] border border-[var(--line)] rounded-lg px-3 py-2 text-[13px]"
        />
      </div>
      <input
        type="text"
        placeholder="Plushy name (e.g. Theodore)"
        value={companion}
        onChange={e => setCompanion(e.target.value)}
        className="w-full bg-[var(--paper-3)] border border-[var(--line)] rounded-lg px-3 py-2 text-[13px] placeholder:text-[var(--ink-4)]"
      />
      <div className="flex gap-2 pt-1">
        <button type="submit" className="btn btn-primary flex-1 justify-center">Add patient</button>
        <button type="button" onClick={onDone} className="btn btn-ghost">Cancel</button>
      </div>
    </form>
  )
}

export function PatientSidebar() {
  const { patients, active, setActiveId, removePatient, sidebarOpen, toggleSidebar } = usePatient()
  const [showForm, setShowForm] = useState(false)
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null)

  if (!sidebarOpen) return null

  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-[oklch(0.15_0.01_60_/_0.3)]"
        onClick={toggleSidebar}
      />

      <div className="fixed top-0 left-0 z-50 h-full w-80 bg-[var(--paper-2)] border-r border-[var(--line)] shadow-[4px_0_24px_oklch(0.3_0.02_60_/_0.12)] flex flex-col">
        <div className="p-4 pb-3 border-b border-[var(--line-soft)] flex items-center justify-between">
          <div>
            <div className="micro">Patient roster</div>
            <h2 className="font-serif text-[18px] font-normal tracking-tight leading-tight m-0 mt-0.5">
              Patients
            </h2>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setShowForm(true)}
              className="btn btn-icon btn-ghost"
              aria-label="Add patient"
            >
              <Plus size={16} />
            </button>
            <button
              onClick={toggleSidebar}
              className="btn btn-icon btn-ghost"
              aria-label="Close sidebar"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {showForm && (
          <div className="border-b border-[var(--line-soft)]">
            <AddPatientForm onDone={() => setShowForm(false)} />
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
          {patients.length === 0 && !showForm && (
            <div className="text-center py-8">
              <div className="micro mb-2">No patients yet</div>
              <button onClick={() => setShowForm(true)} className="btn btn-primary gap-1.5">
                <Plus size={14} /> Add patient
              </button>
            </div>
          )}

          {patients.map((patient) => {
            const isActive = active?.id === patient.id
            return (
              <div
                key={patient.id}
                className={`w-full text-left p-3 rounded-xl border transition-all ${
                  isActive
                    ? 'bg-[var(--paper)] border-[var(--ink-4)] shadow-[var(--shadow-card)]'
                    : 'bg-transparent border-transparent hover:bg-[var(--paper-3)] hover:border-[var(--line)]'
                }`}
              >
                <div
                  className="flex items-center gap-3 cursor-pointer"
                  onClick={() => { setActiveId(patient.id); toggleSidebar() }}
                >
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
                      {patient.age}y · {patient.companion}
                    </div>
                  </div>

                  <button
                    onClick={(e) => { e.stopPropagation(); setConfirmDeleteId(patient.id) }}
                    className="btn btn-icon btn-ghost"
                    style={{ opacity: 0.3 }}
                    aria-label="Remove patient"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>

                {/* Confirm delete inline */}
                {confirmDeleteId === patient.id && (
                  <div className="mt-2 ml-[52px] flex items-center gap-2 p-2 bg-[var(--rose-soft)] border border-[color-mix(in_oklch,var(--rose)_30%,var(--line))] rounded-lg">
                    <span className="font-mono text-[10px] text-[oklch(0.45_0.09_25)] flex-1">Remove {patient.name}?</span>
                    <button
                      onClick={(e) => { e.stopPropagation(); removePatient(patient.id); setConfirmDeleteId(null) }}
                      className="font-mono text-[10px] px-2 py-1 rounded bg-[var(--rose)] text-white border-0 cursor-pointer"
                    >
                      Remove
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); setConfirmDeleteId(null) }}
                      className="font-mono text-[10px] px-2 py-1 rounded bg-[var(--paper-3)] border border-[var(--line)] cursor-pointer"
                    >
                      Cancel
                    </button>
                  </div>
                )}

                <div className="flex gap-4 mt-2 ml-[52px]">
                  <div>
                    <div className="font-mono text-[8px] text-[var(--ink-3)] uppercase tracking-widest">Age</div>
                    <div className="font-mono text-[12px] text-[var(--ink)]">{patient.age}y</div>
                  </div>
                  <div>
                    <div className="font-mono text-[8px] text-[var(--ink-3)] uppercase tracking-widest">Plushy</div>
                    <div className="font-mono text-[12px] text-[var(--ink)]">{patient.companion}</div>
                  </div>
                  <div>
                    <div className="font-mono text-[8px] text-[var(--ink-3)] uppercase tracking-widest">Since</div>
                    <div className="font-mono text-[12px] text-[var(--ink)]">{patient.since}</div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        <div className="p-4 pt-3 border-t border-[var(--line-soft)]">
          <div className="micro text-center">{patients.length} patient{patients.length !== 1 ? 's' : ''} enrolled</div>
        </div>
      </div>
    </>
  )
}
