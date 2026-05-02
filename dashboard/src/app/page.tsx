"use client"

import { useState } from 'react'
import Link from 'next/link'
import { Mic, Play, Pause, Plus, Check, X, Send, ArrowRight } from 'lucide-react'

/* ─── Topbar ─────────────────────────────────────────────── */
function Topbar({ connected }: { connected: boolean }) {
  const now = new Date()
  const dayName = now.toLocaleDateString('en-US', { weekday: 'long' })
  const timeOfDay = now.getHours() < 12 ? 'morning' : now.getHours() < 17 ? 'afternoon' : 'evening'

  return (
    <div className="flex items-center justify-between px-1">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-[10px] bg-[var(--ink)] text-[var(--paper)] flex items-center justify-center font-serif text-[17px] tracking-tight">
          T
        </div>
        <div>
          <div className="micro">Caregiver dashboard</div>
          <h1 className="font-serif text-[24px] font-normal tracking-tight leading-tight m-0">
            Theodore <span className="text-[var(--ink-3)] font-light">· {dayName} {timeOfDay}</span>
          </h1>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <div className={`pip ${connected ? 'on' : 'off'}`} />
          <span className="micro">{connected ? 'Connected · 14 s' : 'Offline'}</span>
        </div>
        <Link
          href="/analysis"
          className="no-underline inline-flex items-center gap-2.5 px-5 py-3 rounded-full text-[13.5px] font-medium text-[var(--paper)] border border-[oklch(0.18_0.012_60)]"
          style={{
            background: 'linear-gradient(135deg, var(--ink) 0%, oklch(0.32 0.02 60) 100%)',
            boxShadow: '0 1px 0 oklch(1 0 0 / 0.06) inset, 0 8px 24px -10px oklch(0.20 0.012 60 / 0.45)',
          }}
        >
          Open full analysis <ArrowRight size={15} />
        </Link>
      </div>
    </div>
  )
}

/* ─── Voices Card ────────────────────────────────────────── */
function VoicesCard() {
  const [playing, setPlaying] = useState(false)

  return (
    <div className="card p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div>
          <div className="micro">Plushy voice</div>
          <h2 className="font-serif text-[17px] font-normal tracking-tight leading-tight m-0 mt-0.5">Voices</h2>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="pip on" />
          <span className="micro">Speaking now</span>
        </div>
      </div>

      <div>
        <div className="micro mb-1.5">Active voice</div>
        <div className="sunken p-3 flex items-center justify-between">
          <span className="text-[13px]">Soft male (default) · 0:18</span>
          <button className="btn-ghost p-1" onClick={() => setPlaying(!playing)}>
            {playing ? <Pause size={14} /> : <Play size={14} />}
          </button>
        </div>
      </div>

      <button className="btn btn-primary w-full justify-center gap-2">
        <Mic size={14} /> Record new voice
      </button>

      <div>
        <div className="micro mb-1.5">Saved · 2</div>
        <div className="space-y-1.5">
          <div className="sunken p-3 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="pip on" />
              <div>
                <div className="text-[13px] font-medium">Soft male (default)</div>
                <div className="micro">0:18 · built-in</div>
              </div>
            </div>
            <span className="tag">Active</span>
          </div>
          <div className="sunken p-3 flex items-center justify-between opacity-60">
            <div className="flex items-center gap-2.5">
              <div className="pip idle" />
              <div>
                <div className="text-[13px] font-medium">Margie&apos;s voice</div>
                <div className="micro">0:12 · recorded</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ─── Medications Card ───────────────────────────────────── */
function MedicationsCard() {
  const meds = [
    { name: 'Donepezil', freq: '1×/day', weekly: '7×/wk', done: 1, total: 1, status: 'done' },
    { name: 'Memantine', freq: '2×/day', weekly: '7×/wk', done: 1, total: 2, status: 'partial' },
    { name: 'Vitamin D', freq: '1×/day', weekly: '3×/wk', done: 0, total: 1, status: 'pending' },
  ]

  return (
    <div className="card p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div>
          <div className="micro">Daily reminders</div>
          <h2 className="font-serif text-[17px] font-normal tracking-tight leading-tight m-0 mt-0.5">Medications</h2>
        </div>
        <button className="btn btn-ghost gap-1 text-[12px]">
          <Plus size={14} /> Add
        </button>
      </div>

      <div className="space-y-2">
        {meds.map((med) => (
          <div key={med.name} className="sunken p-3 flex items-center gap-3">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-none ${
              med.status === 'done' ? 'bg-[var(--sage)] text-white' :
              med.status === 'partial' ? 'bg-[var(--amber)] text-white' :
              'border-2 border-[var(--line)] text-[var(--ink-4)]'
            }`}>
              {med.status === 'done' && <Check size={13} />}
              {med.status === 'partial' && <span className="text-[10px] font-mono font-bold">½</span>}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline gap-2">
                <span className="font-serif text-[15px]">{med.name}</span>
                <span className="micro">{med.freq} · {med.weekly}</span>
              </div>
              <div className="micro mt-0.5">
                {med.done}/{med.total} today
              </div>
            </div>
            <X size={14} className="text-[var(--ink-4)] cursor-pointer hover:text-[var(--ink-2)]" />
          </div>
        ))}
      </div>
    </div>
  )
}

/* ─── Body Status (Bear) ─────────────────────────────────── */
function BodyStatusCard() {
  return (
    <div className="card p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div>
          <div className="micro">Sensor presence</div>
          <h2 className="font-serif text-[17px] font-normal tracking-tight leading-tight m-0 mt-0.5">Body status</h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="micro">3/4 OK</span>
          <div className="pip on" />
          <span className="micro">Live</span>
        </div>
      </div>

      {/* Bear illustration area */}
      <div className="relative flex items-center justify-center py-6">
        <div className="relative w-48 h-48">
          {/* Simplified bear SVG */}
          <svg viewBox="0 0 200 200" className="w-full h-full drift">
            {/* Body */}
            <ellipse cx="100" cy="130" rx="55" ry="50" fill="oklch(0.88 0.04 70)" stroke="oklch(0.78 0.04 70)" strokeWidth="1.5"/>
            {/* Head */}
            <ellipse cx="100" cy="72" rx="42" ry="38" fill="oklch(0.88 0.04 70)" stroke="oklch(0.78 0.04 70)" strokeWidth="1.5"/>
            {/* Ears */}
            <circle cx="65" cy="42" r="16" fill="oklch(0.88 0.04 70)" stroke="oklch(0.78 0.04 70)" strokeWidth="1.5"/>
            <circle cx="65" cy="42" r="9" fill="oklch(0.82 0.06 30)" opacity="0.5"/>
            <circle cx="135" cy="42" r="16" fill="oklch(0.88 0.04 70)" stroke="oklch(0.78 0.04 70)" strokeWidth="1.5"/>
            <circle cx="135" cy="42" r="9" fill="oklch(0.82 0.06 30)" opacity="0.5"/>
            {/* Eyes */}
            <circle cx="85" cy="68" r="4" fill="oklch(0.25 0.01 60)"/>
            <circle cx="115" cy="68" r="4" fill="oklch(0.25 0.01 60)"/>
            <circle cx="86.5" cy="66.5" r="1.5" fill="white"/>
            <circle cx="116.5" cy="66.5" r="1.5" fill="white"/>
            {/* Nose */}
            <ellipse cx="100" cy="80" rx="6" ry="4" fill="oklch(0.55 0.06 50)"/>
            {/* Mouth */}
            <path d="M94,85 Q100,90 106,85" fill="none" stroke="oklch(0.55 0.06 50)" strokeWidth="1.2" strokeLinecap="round"/>
            {/* Belly patch */}
            <ellipse cx="100" cy="135" rx="30" ry="25" fill="oklch(0.92 0.03 75)" stroke="oklch(0.85 0.03 75)" strokeWidth="1"/>
            {/* Spiral on belly */}
            <path d="M100,125 Q108,125 108,132 Q108,140 100,140 Q94,140 94,135 Q94,130 100,130" fill="none" stroke="oklch(0.78 0.06 60)" strokeWidth="1.2" strokeLinecap="round"/>
            {/* Paws */}
            <ellipse cx="60" cy="155" rx="18" ry="12" fill="oklch(0.88 0.04 70)" stroke="oklch(0.78 0.04 70)" strokeWidth="1.5"/>
            <ellipse cx="140" cy="155" rx="18" ry="12" fill="oklch(0.88 0.04 70)" stroke="oklch(0.78 0.04 70)" strokeWidth="1.5"/>
            {/* Feet */}
            <ellipse cx="75" cy="178" rx="16" ry="10" fill="oklch(0.88 0.04 70)" stroke="oklch(0.78 0.04 70)" strokeWidth="1.5"/>
            <ellipse cx="125" cy="178" rx="16" ry="10" fill="oklch(0.88 0.04 70)" stroke="oklch(0.78 0.04 70)" strokeWidth="1.5"/>
          </svg>

          {/* Sensor indicators */}
          <div className="absolute top-2 left-1/2 -translate-x-1/2 flex items-center gap-1">
            <div className="pip on" title="Audio: OK" />
          </div>
          <div className="absolute top-1/2 -left-2 -translate-y-1/2">
            <div className="pip on" title="Touch L: OK" />
          </div>
          <div className="absolute top-1/2 -right-2 -translate-y-1/2">
            <div className="pip on" title="Touch R: OK" />
          </div>
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2">
            <div className="pip off" title="HR: No signal" />
          </div>
        </div>
      </div>
    </div>
  )
}

/* ─── Today's Insight Card ───────────────────────────────── */
function TodaysInsightCard() {
  return (
    <div className="card p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="micro">★ Today&apos;s insight · Wed, May 1</span>
        </div>
        <span className="chip warm">Warm</span>
      </div>

      <p className="font-serif text-[14.5px] leading-relaxed text-[var(--ink)] m-0">
        Theodore held the cushion for over four minutes this morning — his longest contact this week.
        His tone has been warm with several spontaneous stories, and yesterday&apos;s restlessness has&hellip;
      </p>

      <div className="flex gap-6">
        <div>
          <div className="micro mb-0.5">Topics</div>
          <span className="text-[13px]">Fishing · Margie</span>
        </div>
        <div>
          <div className="micro mb-0.5">Mood arc</div>
          <span className="text-[13px]">Warm → calm</span>
        </div>
      </div>
    </div>
  )
}

/* ─── Engagement Garden ──────────────────────────────────── */
function EngagementGarden() {
  const days = Array.from({ length: 14 }, (_, i) => {
    const date = new Date()
    date.setDate(date.getDate() - 13 + i)
    return {
      day: date.getDate(),
      engagement: Math.random() * 0.8 + 0.2,
      hasFlower: Math.random() > 0.3,
    }
  })

  const getFlowerColor = (engagement: number) => {
    if (engagement > 0.7) return 'var(--sage)'
    if (engagement > 0.4) return 'var(--amber)'
    return 'var(--ink-4)'
  }

  return (
    <div className="card p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div>
          <div className="micro">Engagement garden · 14d</div>
          <h2 className="font-serif text-[17px] font-normal tracking-tight leading-tight m-0 mt-0.5">
            A fuller week than last
          </h2>
        </div>
        <div className="flex items-center gap-1">
          <span className="tag">14D</span>
          <span className="micro ml-1">30D</span>
          <span className="micro ml-1">YR</span>
        </div>
      </div>

      {/* Garden visualization */}
      <div className="flex items-end justify-between gap-1 h-24 px-1">
        {days.map((day, i) => (
          <div key={i} className="flex flex-col items-center gap-1 flex-1">
            {/* Flower/dot */}
            <div className="flex flex-col items-center">
              {day.hasFlower ? (
                <svg width="20" height={Math.round(20 + day.engagement * 30)} viewBox={`0 0 20 ${Math.round(20 + day.engagement * 30)}`}>
                  {/* Stem */}
                  <line x1="10" y1={Math.round(20 + day.engagement * 30)} x2="10" y2="12" stroke="var(--sage)" strokeWidth="1.2" opacity="0.5"/>
                  {/* Petals */}
                  <circle cx="10" cy="8" r={3 + day.engagement * 3} fill={getFlowerColor(day.engagement)} opacity={0.6 + day.engagement * 0.4}/>
                  <circle cx="10" cy="8" r={1.5 + day.engagement} fill="oklch(0.94 0.04 75)"/>
                </svg>
              ) : (
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ background: 'var(--ink-4)', opacity: 0.4 }}
                />
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Day labels */}
      <div className="flex justify-between px-1">
        {days.map((day, i) => (
          <span key={i} className="font-mono text-[8px] text-[var(--ink-3)] text-center flex-1">
            {day.day}
          </span>
        ))}
      </div>
    </div>
  )
}

/* ─── Memory Timeline ────────────────────────────────────── */
function MemoryTimeline() {
  const memories = [
    { topic: 'Fishing with dad', count: 6, flagged: true },
    { topic: 'Margie', count: 4, flagged: false },
    { topic: 'Sunday roast', count: 3, flagged: false },
    { topic: 'The old dog', count: 2, flagged: false },
  ]

  return (
    <div className="card p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="micro">Memory timeline</span>
          <span className="text-[13px] text-[var(--ink-2)]">Recurring topics & people</span>
        </div>
        <span className="chip alert">1 flagged</span>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {memories.map((m) => (
          <span key={m.topic} className={`chip ${m.flagged ? 'alert' : m.count > 3 ? 'warm' : ''}`}>
            {m.topic} × {m.count}
          </span>
        ))}
      </div>
    </div>
  )
}

/* ─── Chat Log ───────────────────────────────────────────── */

function ChatLog() {
  const [message, setMessage] = useState('')

  const messages = [
    { from: 'theodore', time: '9:42', text: 'Good morning, Theodore. Did you sleep well?' },
    { from: 'user', time: '9:42', type: 'audio', duration: '0:14' },
    { from: 'theodore', time: '9:43', text: "Margie called yesterday — would you like to hear what she said?" },
    { from: 'user', time: '9:43', text: 'Yes, please. Did she mention the grandkids?' },
    { from: 'theodore', time: '9:44', text: "Lily started piano lessons. The dog still won't eat the new food." },
    { from: 'user', time: '9:45', text: "Ha — that dog. Reminds me of the old setter we had on the lake." },
  ]

  return (
    <div className="card flex flex-col h-full min-h-0">
      {/* Chat header */}
      <div className="p-4 pb-3 border-b border-[var(--line-soft)] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-[16px]">💬</span>
          <div>
            <span className="font-serif text-[15px] font-medium">Chat log</span>
            <span className="micro ml-2">This morning</span>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button className="btn btn-icon btn-ghost" aria-label="Notifications">🔔</button>
          <button className="btn btn-icon btn-ghost" aria-label="Pin">📌</button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
        <div className="text-center">
          <span className="micro">Today · 9:42 AM</span>
        </div>

        {messages.map((msg, i) => (
          <div key={i}>
            <div className="micro mb-1">
              {msg.from === 'theodore' ? 'Theodore' : 'You'} · {msg.time}
            </div>
            {msg.type === 'audio' ? (
              <div className={`inline-flex items-center gap-3 px-4 py-3 rounded-2xl max-w-[85%] ${
                msg.from === 'user'
                  ? 'bg-[var(--ink)] text-[var(--paper)] ml-auto'
                  : 'bg-[var(--paper-3)]'
              }`} style={msg.from === 'user' ? { marginLeft: 'auto', display: 'flex' } : {}}>
                <button className="w-7 h-7 rounded-full bg-[var(--paper)] text-[var(--ink)] flex items-center justify-center flex-none">
                  <Play size={12} />
                </button>
                {/* Waveform bars */}
                <div className="flex items-center gap-0.5 h-5">
                  {Array.from({ length: 16 }, (_, j) => (
                    <div
                      key={j}
                      className="w-[2px] rounded-full"
                      style={{
                        height: `${4 + Math.random() * 14}px`,
                        background: msg.from === 'user' ? 'var(--paper)' : 'var(--ink-3)',
                        opacity: 0.7,
                      }}
                    />
                  ))}
                </div>
                <span className="font-mono text-[11px] opacity-80">{msg.duration}</span>
              </div>
            ) : (
              <div
                className={`inline-block px-4 py-3 rounded-2xl max-w-[85%] font-serif text-[14.5px] leading-relaxed ${
                  msg.from === 'user'
                    ? 'bg-[var(--ink)] text-[var(--paper)] rounded-br-md'
                    : 'bg-[var(--paper-3)] text-[var(--ink)] rounded-bl-md'
                }`}
                style={msg.from === 'user' ? { marginLeft: 'auto', display: 'block', textAlign: 'left', float: 'right', clear: 'both' } : { clear: 'both' }}
              >
                {msg.text}
              </div>
            )}
            <div className="clear-both" />
          </div>
        ))}
      </div>

      {/* Input */}
      <div className="p-3 pt-2 border-t border-[var(--line-soft)]">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Send a message to Theodore..."
            className="flex-1 bg-[var(--paper-3)] border border-[var(--line)] rounded-full px-4 py-2.5 text-[13px] placeholder:text-[var(--ink-4)]"
          />
          <button className="btn btn-primary gap-1.5 py-2.5">
            <Send size={13} /> Send
          </button>
        </div>
      </div>
    </div>
  )
}

/* ─── Main Dashboard ─────────────────────────────────────── */
export default function Dashboard() {
  const connected = true // Static for main dashboard; live SSE is on /analysis

  return (
    <div className="relative z-10 h-screen max-w-[1560px] mx-auto px-3.5 py-2.5 grid grid-rows-[auto_1fr] gap-2.5">
      <Topbar connected={connected} />

      {/* Main 3-column grid matching Theodore.html layout */}
      <div
        className="grid gap-2.5 min-h-0"
        style={{
          gridTemplateColumns: 'minmax(260px, 1fr) minmax(320px, 1.15fr) minmax(280px, 1fr)',
          gridTemplateRows: 'minmax(420px, 1.2fr) minmax(0, 0.85fr)',
          gridTemplateAreas: '"left-top mid-top chat" "bottom bottom chat"',
        }}
      >
        {/* Left: Voices + Medications */}
        <div className="flex flex-col gap-2.5 min-h-0 overflow-y-auto" style={{ gridArea: 'left-top' }}>
          <VoicesCard />
          <MedicationsCard />
        </div>

        {/* Center top: Body status + Today's Insight */}
        <div className="flex flex-col gap-2.5 min-h-0" style={{ gridArea: 'mid-top' }}>
          <BodyStatusCard />
          <TodaysInsightCard />
        </div>

        {/* Right: Chat log (spans both rows) */}
        <div className="min-h-0" style={{ gridArea: 'chat' }}>
          <ChatLog />
        </div>

        {/* Bottom: Engagement Garden + Memory Timeline */}
        <div className="flex flex-col gap-2.5 min-h-0" style={{ gridArea: 'bottom' }}>
          <EngagementGarden />
          <MemoryTimeline />
        </div>
      </div>
    </div>
  )
}
