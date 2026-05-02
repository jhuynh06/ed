"use client"

import Link from 'next/link'
import { usePatient } from '@/lib/patient-context'

interface TopbarProps {
  connected?: boolean
}

export function Topbar({ connected = false }: TopbarProps) {
  const { active, toggleSidebar } = usePatient()

  return (
    <div className="flex items-center justify-between px-1">
      <div className="flex items-center gap-3">
        <button
          onClick={toggleSidebar}
          className="w-8 h-8 rounded-lg bg-[var(--ink)] text-[var(--paper)] flex items-center justify-center font-serif text-base font-normal tracking-tight cursor-pointer border-0 hover:opacity-80 transition-opacity"
          aria-label="Open patient roster"
          title="Switch patient"
        >
          {active?.avatar ?? 'T'}
        </button>
        <div>
          <div className="micro">Caregiver dashboard{active ? ` · ${active.name}` : ''}</div>
          <h1 className="font-serif text-[22px] font-normal tracking-tight leading-tight m-0">
            {active ? active.companion : 'Theodore'}{' '}
            <span className="text-[var(--ink-3)] font-light">
              · {active ? `${active.age}y` : 'no patient selected'}
            </span>
          </h1>
        </div>
      </div>
      
      <div className="flex items-center gap-4">
        <nav className="flex items-center gap-2">
          <Link 
            href="/" 
            className="text-[var(--ink-2)] no-underline py-1 px-3 rounded-full border border-[var(--line)] bg-[var(--paper-2)] font-mono text-[11px] tracking-wider uppercase hover:text-[var(--ink)] hover:border-[var(--ink-4)] transition-colors"
          >
            ← Return to dashboard
          </Link>
        </nav>
        
        <div className="flex items-center gap-2">
          <div className={`pip ${connected ? 'on' : 'off'}`}></div>
          <span className="micro">{connected ? 'Live' : 'Offline'}</span>
        </div>
      </div>
    </div>
  )
}
