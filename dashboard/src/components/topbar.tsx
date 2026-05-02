import Link from 'next/link'

interface TopbarProps {
  connected?: boolean
}

export function Topbar({ connected = false }: TopbarProps) {
  return (
    <div className="flex items-center justify-between px-1">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-[var(--ink)] text-[var(--paper)] flex items-center justify-center font-serif text-base font-normal tracking-tight">
          T
        </div>
        <div>
          <div className="micro">Caregiver dashboard · Wed, May 1</div>
          <h1 className="font-serif text-[22px] font-normal tracking-tight leading-tight m-0">
            Theodore <span className="text-[var(--ink-3)] font-light">· session #312</span>
          </h1>
        </div>
      </div>
      
      <div className="flex items-center gap-4">
        <nav className="flex items-center gap-2">
          <Link 
            href="/" 
            className="text-[var(--ink-2)] no-underline py-1 px-3 rounded-full border border-[var(--line)] bg-[var(--paper-2)] font-mono text-[11px] tracking-wider uppercase hover:text-[var(--ink)] hover:border-[var(--ink-4)] transition-colors"
          >
            Dashboard
          </Link>
          <Link 
            href="/analysis" 
            className="text-[var(--ink-2)] no-underline py-1 px-3 rounded-full border border-[var(--line)] bg-[var(--paper-2)] font-mono text-[11px] tracking-wider uppercase hover:text-[var(--ink)] hover:border-[var(--ink-4)] transition-colors"
          >
            Analysis
          </Link>
          <Link 
            href="/notifications" 
            className="text-[var(--ink-2)] no-underline py-1 px-3 rounded-full border border-[var(--line)] bg-[var(--paper-2)] font-mono text-[11px] tracking-wider uppercase hover:text-[var(--ink)] hover:border-[var(--ink-4)] transition-colors"
          >
            Notifications
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