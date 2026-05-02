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
    <div className="card p-4 flex flex-col gap-3 h-full">
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

/* ─── Body Status (Horse Plushie) ────────────────────────── */
function BodyStatusCard() {
  return (
    <div className="card p-4 flex flex-col gap-3 h-full">
      <div className="flex items-center justify-between">
        <div>
          <div className="micro">Sensor presence</div>
          <h2 className="font-serif text-[17px] font-normal tracking-tight leading-tight m-0 mt-0.5">Body status</h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="micro">5/6 OK</span>
          <div className="pip on" />
          <span className="micro">Live</span>
        </div>
      </div>

      <div className="relative flex items-center justify-center flex-1 py-2">
        <div className="relative w-48 h-full max-h-64">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/theodore-plushie.png"
            alt="Theodore plushie — sensor body status"
            className="w-full h-full object-contain drift"
            draggable={false}
          />

          {/* Sensor indicators — 6 total, none on head */}
          {/* Body: two vertically aligned on chest/belly */}
          <div className="absolute top-[42%] left-1/2 -translate-x-1/2">
            <div className="pip on" title="Mic: OK" />
          </div>
          <div className="absolute top-[58%] left-1/2 -translate-x-1/2">
            <div className="pip on" title="IMU: OK" />
          </div>
          {/* Hands: on each hoof/hand tip */}
          <div className="absolute top-[55%] left-[8%]">
            <div className="pip on" title="Touch L: OK" />
          </div>
          <div className="absolute top-[55%] right-[8%]">
            <div className="pip on" title="Touch R: OK" />
          </div>
          {/* Feet: centered on each black hoof */}
          <div className="absolute bottom-[10%] left-[24%] -translate-x-1/2">
            <div className="pip off" title="HR L: No signal" />
          </div>
          <div className="absolute bottom-[10%] right-[24%] translate-x-1/2">
            <div className="pip on" title="HR R: OK" />
          </div>
        </div>
      </div>
    </div>
  )
}

/* ─── Today's Insight Card (expanded) ────────────────────── */
function TodaysInsightCard() {
  return (
    <div className="card p-4 flex flex-col gap-3 h-full">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="micro">★ Today&apos;s insight · Wed, May 1</span>
        </div>
        <span className="chip warm">Warm</span>
      </div>

      <p className="font-serif text-[14.5px] leading-relaxed text-[var(--ink)] m-0">
        Theodore held the cushion for over four minutes this morning — his longest contact this week.
        His tone has been warm with several spontaneous stories, and yesterday&apos;s restlessness has
        eased noticeably. He mentioned Margie twice and asked about the grandkids unprompted.
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
        <div>
          <div className="micro mb-0.5">Engagement</div>
          <span className="text-[13px]">4h 18m conversation</span>
        </div>
      </div>

      <div className="flex gap-6 pt-2 border-t border-[var(--line-soft)]">
        <div>
          <div className="micro mb-0.5">Episodes today</div>
          <span className="text-[13px]">2 · both resolved</span>
        </div>
        <div>
          <div className="micro mb-0.5">Sundowning</div>
          <span className="text-[13px]">Pattern detected at 5pm</span>
        </div>
        <div>
          <div className="micro mb-0.5">CDR total</div>
          <span className="text-[13px]">2.0 · mild stage</span>
        </div>
      </div>
    </div>
  )
}

/* ─── Voice Transmit Card ─────────────────────────────────── */
function VoiceTransmitCard() {
  const [recording, setRecording] = useState(false)
  const [seconds, setSeconds] = useState(0)

  const handleToggle = () => {
    if (recording) {
      setRecording(false)
      setSeconds(0)
      // In production: stop MediaRecorder, send audio via WebSocket to bear
    } else {
      setRecording(true)
      // In production: start MediaRecorder, stream PCM to backend → bear speaker
    }
  }

  // Timer display
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60

  return (
    <div className="card px-4 py-3 flex items-center gap-3">
      <button
        onClick={handleToggle}
        className={`w-10 h-10 rounded-full flex items-center justify-center flex-none transition-all ${
          recording
            ? 'bg-[var(--rose)] text-white shadow-[0_0_0_4px_var(--rose-soft)]'
            : 'bg-[var(--ink)] text-[var(--paper)]'
        }`}
        aria-label={recording ? 'Stop recording' : 'Talk to Theodore'}
      >
        {recording ? <X size={16} /> : <Mic size={16} />}
      </button>
      <div className="flex-1 min-w-0">
        <div className="font-serif text-[14px] leading-tight">
          {recording ? 'Transmitting to Theodore...' : 'Tunnel in'}
        </div>
        <div className="micro mt-0.5">
          {recording
            ? `${mins}:${secs.toString().padStart(2, '0')} · live`
            : 'Hold to speak through the horse'
          }
        </div>
      </div>
      {recording && (
        <div className="flex items-center gap-0.5 h-5">
          {Array.from({ length: 12 }, (_, i) => (
            <div
              key={i}
              className="w-[2px] rounded-full bg-[var(--rose)]"
              style={{
                height: `${3 + Math.random() * 14}px`,
                opacity: 0.5 + Math.random() * 0.5,
                animation: 'breathe 0.8s ease-in-out infinite',
                animationDelay: `${i * 0.05}s`,
              }}
            />
          ))}
        </div>
      )}
    </div>
  )
}

/* ─── Chat Log ───────────────────────────────────────────── */
function ChatLog() {
  const [message, setMessage] = useState('')

  const messages = [
    { from: 'theodore', time: '9:42', text: 'Good morning, Theodore. Did you sleep well?' },
    { from: 'user', time: '9:42', type: 'audio' as const, duration: '0:14' },
    { from: 'theodore', time: '9:43', text: "Margie called yesterday — would you like to hear what she said?" },
    { from: 'user', time: '9:43', text: 'Yes, please. Did she mention the grandkids?' },
    { from: 'theodore', time: '9:44', text: "Lily started piano lessons. The dog still won't eat the new food." },
    { from: 'user', time: '9:45', text: "Ha — that dog. Reminds me of the old setter we had on the lake." },
  ]

  return (
    <div className="card flex flex-col h-full min-h-0">
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
  const connected = true

  return (
    <div className="relative z-10 h-screen max-w-[1560px] mx-auto px-3.5 py-2.5 grid grid-rows-[auto_1fr] gap-2.5">
      <Topbar connected={connected} />

      <div
        className="grid gap-2.5 min-h-0"
        style={{
          gridTemplateColumns: 'minmax(260px, 1fr) minmax(320px, 1.15fr) minmax(280px, 1fr)',
          gridTemplateRows: '1.4fr 0.6fr',
          gridTemplateAreas: '"left mid-top chat" "left mid-bot chat"',
        }}
      >
        {/* Left: Voices + Medications stacked, meds fills remaining */}
        <div className="flex flex-col gap-2.5 min-h-0" style={{ gridArea: 'left' }}>
          <VoicesCard />
          <div className="flex-1 min-h-0">
            <MedicationsCard />
          </div>
        </div>

        {/* Center top: Body status + Tunnel in */}
        <div className="flex flex-col gap-2.5 min-h-0" style={{ gridArea: 'mid-top' }}>
          <div className="flex-1 min-h-0">
            <BodyStatusCard />
          </div>
          <VoiceTransmitCard />
        </div>

        {/* Center bottom: Today's Insight */}
        <div className="min-h-0 overflow-hidden" style={{ gridArea: 'mid-bot' }}>
          <TodaysInsightCard />
        </div>

        {/* Right: Chat log spans both rows */}
        <div className="min-h-0" style={{ gridArea: 'chat' }}>
          <ChatLog />
        </div>
      </div>
    </div>
  )
}
