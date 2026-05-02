import { Topbar } from '@/components/topbar'

export default function NotificationsPage() {
  return (
    <div className="relative z-10 h-screen max-w-[1280px] mx-auto p-7 grid grid-rows-[auto_1fr] gap-7">
      <Topbar connected={true} />
      
      <div className="overflow-y-auto space-y-11">
        {/* Urgent alerts section */}
        <section>
          <div className="flex items-start justify-between mb-4">
            <div>
              <div className="flex items-center gap-2">
                <div className="pip off"></div>
                <span className="micro">Caregiver · push</span>
              </div>
              <h2 className="font-serif text-[22px] font-normal tracking-tight leading-tight m-0 mt-1">
                Urgent alerts
              </h2>
              <p className="font-serif text-[13.5px] leading-relaxed text-[var(--ink-3)] mt-1 max-w-lg">
                Real-time interruptions. Sent only when Theodore's own intervention has already failed or there's a clear safety signal.
              </p>
            </div>
          </div>

          {/* Phone mockup with notifications */}
          <div className="grid grid-cols-[296px_1fr] gap-7 items-start">
            {/* Phone */}
            <div className="w-[296px] rounded-[38px] bg-[oklch(0.18_0.008_60)] p-2 shadow-[0_30px_60px_-30px_oklch(0.20_0.02_60_/_0.5),_0_1px_0_oklch(1_0_0_/_0.05)_inset]">
              <div className="bg-gradient-to-br from-[oklch(0.32_0.05_260)] to-[oklch(0.22_0.04_280)] rounded-[32px] h-[580px] flex flex-col overflow-hidden">
                {/* Status bar */}
                <div className="flex justify-between items-center px-6 pt-4 text-[oklch(0.95_0.01_80)] font-semibold text-sm">
                  <span>9:41</span>
                  <div className="flex items-center gap-1 opacity-90">
                    <span className="text-[10px] opacity-85">82</span>
                  </div>
                </div>
                
                {/* Time */}
                <div className="text-center text-[oklch(0.97_0.01_80)] mt-5">
                  <div className="text-[64px] font-extralight tracking-tight leading-none">9:41</div>
                  <div className="text-sm font-medium opacity-90 mt-1">Wednesday, May 1</div>
                </div>

                {/* Notification stack */}
                <div className="flex-1 px-3 pb-3 mt-4 space-y-2">
                  <div className="bg-[oklch(0.95_0.01_80_/_0.26)] backdrop-blur-xl border border-[oklch(1_0_0_/_0.12)] rounded-2xl p-3 text-[oklch(0.97_0.01_80)]">
                    <div className="flex items-center gap-2 text-[11px] uppercase tracking-wide opacity-85 mb-1">
                      <div className="w-[18px] h-[18px] rounded bg-[var(--ink)] text-[var(--paper)] flex items-center justify-center font-serif text-[10px]">T</div>
                      <span>Theodore</span>
                      <span className="ml-auto opacity-70">now</span>
                    </div>
                    <div className="font-serif text-sm font-medium leading-tight mb-1">Agitation didn't settle</div>
                    <div className="text-[12.5px] leading-tight opacity-85">Spike at 9:34 — Theodore tried hugs and music. Heart rate proxy still elevated 7 min in.</div>
                  </div>
                  
                  <div className="bg-[oklch(0.95_0.01_80_/_0.18)] backdrop-blur-xl border border-[oklch(1_0_0_/_0.12)] rounded-2xl p-3 text-[oklch(0.97_0.01_80)]">
                    <div className="flex items-center gap-2 text-[11px] uppercase tracking-wide opacity-85 mb-1">
                      <div className="w-[18px] h-[18px] rounded bg-[var(--ink)] text-[var(--paper)] flex items-center justify-center font-serif text-[10px]">T</div>
                      <span>Theodore</span>
                      <span className="ml-auto opacity-70">8:31a</span>
                    </div>
                    <div className="font-serif text-sm font-medium leading-tight mb-1">"I need to go home"</div>
                    <div className="text-[12.5px] leading-tight opacity-85">Wandering language detected — first time this week. Resolved within 40 s.</div>
                  </div>
                  
                  <div className="bg-[oklch(0.95_0.01_80_/_0.18)] backdrop-blur-xl border border-[oklch(1_0_0_/_0.12)] rounded-2xl p-3 text-[oklch(0.97_0.01_80)]">
                    <div className="flex items-center gap-2 text-[11px] uppercase tracking-wide opacity-85 mb-1">
                      <div className="w-[18px] h-[18px] rounded bg-[var(--ink)] text-[var(--paper)] flex items-center justify-center font-serif text-[10px]">T</div>
                      <span>Theodore</span>
                      <span className="ml-auto opacity-70">7:55a</span>
                    </div>
                    <div className="font-serif text-sm font-medium leading-tight mb-1">Breakfast may have been skipped</div>
                    <div className="text-[12.5px] leading-tight opacity-85">No mention of food in conversation. Worth a check-in.</div>
                  </div>
                </div>
                
                <div className="w-28 h-1 bg-[oklch(1_0_0_/_0.45)] rounded-full mx-auto mb-2"></div>
              </div>
            </div>

            {/* Detailed notifications */}
            <div className="space-y-4">
              <div className="notif urgent">
                <div className="notif-head">
                  <div className="notif-icon">
                    <svg className="w-[14px] h-[14px]" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.6">
                      <path d="M7 1 L13 12 L1 12 Z"/>
                      <line x1="7" y1="5" x2="7" y2="9"/>
                      <circle cx="7" cy="10.6" r="0.7" fill="currentColor" stroke="none"/>
                    </svg>
                  </div>
                  <span className="font-mono text-[10px] tracking-wider uppercase text-[var(--ink-3)]">Theodore · live</span>
                  <span className="notif-priority">Urgent</span>
                  <span className="font-mono text-[10px] text-[var(--ink-3)] tracking-wider ml-auto">just now</span>
                </div>
                <div className="notif-body">
                  <h3 className="notif-title">Agitation didn't settle after intervention</h3>
                  <p className="notif-desc">Spike began 9:34a · Theodore played music, prompted breathing, and offered a hug. Jerk magnitude is still 0.42 g/s seven minutes in — above his 14-day max.</p>
                </div>
                <div className="notif-actions">
                  <button className="btn" style={{ background: 'var(--rose)', color: 'var(--paper)', borderColor: 'var(--rose)' }}>Call Theodore</button>
                  <button className="btn">Listen in</button>
                  <button className="btn btn-ghost">I'm on my way</button>
                </div>
              </div>

              <div className="notif warn">
                <div className="notif-head">
                  <div className="notif-icon">
                    <svg className="w-[14px] h-[14px]" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.6">
                      <circle cx="7" cy="7" r="5.5"/>
                      <line x1="7" y1="3" x2="7" y2="7"/>
                      <line x1="7" y1="7" x2="9.5" y2="9"/>
                    </svg>
                  </div>
                  <span className="font-mono text-[10px] tracking-wider uppercase text-[var(--ink-3)]">Theodore</span>
                  <span className="notif-priority">Wandering language</span>
                  <span className="font-mono text-[10px] text-[var(--ink-3)] tracking-wider ml-auto">8:31a</span>
                </div>
                <div className="notif-body">
                  <h3 className="notif-title">"I need to go home" — first this week</h3>
                  <p className="notif-desc">Said three times in 90 s while sitting in the kitchen. Theodore reoriented him gently; he settled within 40 s.</p>
                </div>
                <div className="notif-actions">
                  <button className="btn btn-primary">Hear the moment</button>
                  <button className="btn">Mark resolved</button>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Daily digest section */}
        <section>
          <div className="flex items-start justify-between mb-4">
            <div>
              <div className="flex items-center gap-2">
                <div className="pip" style={{ background: 'var(--amber)' }}></div>
                <span className="micro">Caregiver · 7:00 pm</span>
              </div>
              <h2 className="font-serif text-[22px] font-normal tracking-tight leading-tight m-0 mt-1">
                Daily digest
              </h2>
              <p className="font-serif text-[13.5px] leading-relaxed text-[var(--ink-3)] mt-1 max-w-lg">
                Batched summary delivered once a day. Mood arc, conversation, meds, cognitive probes, and any sundowning episodes.
              </p>
            </div>
            <span className="micro">Wed · May 1</span>
          </div>

          <div className="card p-5">
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="micro">Today with Theodore</div>
                <div className="font-serif text-[18px] tracking-tight leading-tight mt-1">A warmer day — longest hug of the week, one disorientation moment at 8:31.</div>
              </div>
              <span className="num text-[13px] text-[var(--ink-3)]">12 conversations · 4h 18m</span>
            </div>

            <div className="grid grid-cols-2 gap-6">
              {/* Medication compliance */}
              <div>
                <div className="micro mb-3">Medication compliance</div>
                <div className="space-y-2">
                  <div className="comp-row">
                    <div className="font-mono text-[10.5px] text-[var(--ink-2)]">8:02a</div>
                    <div className="font-serif text-[13.5px]">Donepezil 10mg</div>
                    <div className="comp-tag ack">Taken</div>
                  </div>
                  <div className="comp-row">
                    <div className="font-mono text-[10.5px] text-[var(--ink-2)]">8:02a</div>
                    <div className="font-serif text-[13.5px]">Memantine 20mg</div>
                    <div className="comp-tag ack">Taken</div>
                  </div>
                  <div className="comp-row">
                    <div className="font-mono text-[10.5px] text-[var(--ink-2)]">6:15p</div>
                    <div className="font-serif text-[13.5px]">Donepezil 10mg</div>
                    <div className="comp-tag miss">Missed</div>
                  </div>
                </div>
              </div>

              {/* Sundowning */}
              <div>
                <div className="micro mb-3">Sundowning pattern</div>
                <div className="bg-[var(--paper-3)] border border-[var(--line-soft)] rounded-lg p-4">
                  <div className="font-serif text-[15px] leading-tight mb-2">5:15 PM onset detected</div>
                  <div className="font-serif text-[13px] leading-relaxed text-[var(--ink-2)] mb-3">
                    Agitation climbed from 22 to 67 over 12 minutes. "Where am I?" repeated 3× before Theodore's music intervention.
                  </div>
                  <div className="chip alert">3rd time this week</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Weekly trend section */}
        <section>
          <div className="flex items-start justify-between mb-4">
            <div>
              <div className="flex items-center gap-2">
                <div className="pip" style={{ background: 'var(--sky)' }}></div>
                <span className="micro">Weekly summary · automated</span>
              </div>
              <h2 className="font-serif text-[22px] font-normal tracking-tight leading-tight m-0 mt-1">
                Weekly trend
              </h2>
              <p className="font-serif text-[13.5px] leading-relaxed text-[var(--ink-3)] mt-1 max-w-lg">
                Baseline shifts and emerging patterns. Generated every Sunday evening.
              </p>
            </div>
            <div className="font-mono text-[10px] uppercase tracking-wider text-[var(--ink-3)] py-1 px-3 bg-[var(--paper-3)] border border-[var(--line)] rounded-full">
              Apr 25 – May 1
            </div>
          </div>

          <div className="card p-5">
            <div className="flex justify-between items-end mb-3">
              <div className="font-serif text-[18px] tracking-tight leading-tight">Baseline shifts this week</div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="bg-[var(--paper-3)] border border-[var(--line-soft)] rounded-lg p-3">
                <div className="font-mono text-[9.5px] uppercase tracking-wider text-[var(--ink-3)] mb-2">Heart rate</div>
                <div className="flex items-baseline gap-2 mb-2">
                  <div className="font-serif text-[22px] tracking-tight leading-none">74</div>
                  <div className="font-mono text-[10.5px] text-[var(--ink-3)]">was 72</div>
                  <div className="ml-auto font-mono text-[10px] tracking-wider py-1 px-2 rounded bg-[var(--sage-soft)] text-[oklch(0.40_0.07_145)]">↑ +3%</div>
                </div>
                <svg className="w-full h-6" viewBox="0 0 100 22" preserveAspectRatio="none">
                  <polyline points="0,15 20,14 40,16 60,13 80,15 100,12" fill="none" stroke="var(--sage)" strokeWidth="1.6"/>
                </svg>
              </div>

              <div className="bg-[var(--paper-3)] border border-[var(--line-soft)] rounded-lg p-3">
                <div className="font-mono text-[9.5px] uppercase tracking-wider text-[var(--ink-3)] mb-2">Sleep onset</div>
                <div className="flex items-baseline gap-2 mb-2">
                  <div className="font-serif text-[22px] tracking-tight leading-none">22:45</div>
                  <div className="font-mono text-[10.5px] text-[var(--ink-3)]">was 23:15</div>
                  <div className="ml-auto font-mono text-[10px] tracking-wider py-1 px-2 rounded bg-[var(--sage-soft)] text-[oklch(0.40_0.07_145)]">earlier</div>
                </div>
                <svg className="w-full h-6" viewBox="0 0 100 22" preserveAspectRatio="none">
                  <polyline points="0,18 20,16 40,14 60,12 80,10 100,8" fill="none" stroke="var(--sage)" strokeWidth="1.6"/>
                </svg>
              </div>

              <div className="bg-[var(--paper-3)] border border-[var(--line-soft)] rounded-lg p-3">
                <div className="font-mono text-[9.5px] uppercase tracking-wider text-[var(--ink-3)] mb-2">Agitation avg</div>
                <div className="flex items-baseline gap-2 mb-2">
                  <div className="font-serif text-[22px] tracking-tight leading-none">28</div>
                  <div className="font-mono text-[10.5px] text-[var(--ink-3)]">was 31</div>
                  <div className="ml-auto font-mono text-[10px] tracking-wider py-1 px-2 rounded bg-[var(--sage-soft)] text-[oklch(0.40_0.07_145)]">↓ -10%</div>
                </div>
                <svg className="w-full h-6" viewBox="0 0 100 22" preserveAspectRatio="none">
                  <polyline points="0,16 20,15 40,13 60,12 80,10 100,8" fill="none" stroke="var(--sage)" strokeWidth="1.6"/>
                </svg>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}