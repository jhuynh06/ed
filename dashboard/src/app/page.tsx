"use client"

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePatient } from '@/lib/patient-context'
import { useSSE } from '@/lib/use-sse'
import { fetchMedications, type Medication } from '@/lib/api'
import { Mic, Play, Pause, Plus, X, Send } from 'lucide-react'

/* ─── Topbar ─────────────────────────────────────────────── */
function Topbar({ connected }: { connected: boolean }) {
  const { active, toggleSidebar } = usePatient()
  const [timeLabel, setTimeLabel] = useState('')

  useEffect(() => {
    const now = new Date()
    const dayName = now.toLocaleDateString('en-US', { weekday: 'long' })
    const hour = now.getHours()
    const timeOfDay = hour < 12 ? 'morning' : hour < 17 ? 'afternoon' : 'evening'
    setTimeLabel(`${dayName} ${timeOfDay}`)
  }, [])

  return (
    <div className="flex items-center justify-between px-1">
      <div className="flex items-center gap-3">
        <button
          onClick={toggleSidebar}
          className="w-9 h-9 rounded-[10px] bg-[var(--ink)] text-[var(--paper)] flex items-center justify-center font-serif text-[17px] tracking-tight cursor-pointer border-0 hover:opacity-80 transition-opacity"
          aria-label="Open patient roster"
          title="Switch patient"
        >
          {active.avatar}
        </button>
        <div>
          <div className="micro">Caregiver dashboard · {active.name}</div>
          <h1 className="font-serif text-[24px] font-normal tracking-tight leading-tight m-0">
            {active.companion} <span className="text-[var(--ink-3)] font-light">· {timeLabel || 'loading'}</span>
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
          className="text-[var(--ink-2)] no-underline py-1 px-3 rounded-full border border-[var(--line)] bg-[var(--paper-2)] font-mono text-[11px] tracking-wider uppercase hover:text-[var(--ink)] hover:border-[var(--ink-4)] transition-colors"
        >
          Full analysis →
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
  const [meds, setMeds] = useState<Medication[]>([])

  useEffect(() => {
    fetchMedications().then(setMeds).catch(() => {})
  }, [])

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
          <div key={med.id} className="sunken p-3 flex items-center gap-3">
            <div className="w-6 h-6 rounded-full flex items-center justify-center flex-none border-2 border-[var(--line)] text-[var(--ink-4)]" />
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline gap-2">
                <span className="font-serif text-[15px]">{med.name}</span>
                <span className="micro">{med.dosage} · {med.schedule}</span>
              </div>
              {med.notes && <div className="micro mt-0.5">{med.notes}</div>}
            </div>
            <X size={14} className="text-[var(--ink-4)] cursor-pointer hover:text-[var(--ink-2)]" />
          </div>
        ))}
        {meds.length === 0 && (
          <div className="micro text-[var(--ink-4)] py-2 text-center">No medications</div>
        )}
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
            src="/ed-plushie.png"
            alt="Ed plushie — sensor body status"
            className="w-full h-full object-contain drift"
            draggable={false}
          />

          {/* Sensor indicators — 6 total, none on head */}
          {/* Body: two vertically aligned on chest/belly */}
          <div className="absolute top-[50%] left-1/2 -translate-x-1/2">
            <div className="pip on" title="Mic: OK" />
          </div>
          <div className="absolute top-[64%] left-1/2 -translate-x-1/2">
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
        Ed held the cushion for over four minutes this morning — his longest contact this week.
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
        aria-label={recording ? 'Stop recording' : 'Talk to Ed'}
      >
        {recording ? <X size={16} /> : <Mic size={16} />}
      </button>
      <div className="flex-1 min-w-0">
        <div className="font-serif text-[14px] leading-tight">
          {recording ? 'Transmitting to Ed...' : 'Tunnel in'}
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
                height: `${4 + ((i * 7 + 3) % 13)}px`,
                opacity: 0.5 + ((i * 5 + 2) % 10) / 20,
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
    { from: 'ed', time: '9:42', text: 'Good morning, Ed. Did you sleep well?' },
    { from: 'user', time: '9:42', type: 'audio' as const, duration: '0:14' },
    { from: 'ed', time: '9:43', text: "Margie called yesterday — would you like to hear what she said?" },
    { from: 'user', time: '9:43', text: 'Yes, please. Did she mention the grandkids?' },
    { from: 'ed', time: '9:44', text: "Lily started piano lessons. The dog still won't eat the new food." },
    { from: 'user', time: '9:45', text: "Ha — that dog. Reminds me of the old setter we had on the lake." },
  ]

  return (
    <div className="card flex flex-col h-full min-h-0">
      <div className="p-4 pb-3 border-b border-[var(--line-soft)] flex items-center justify-between">
        <div className="flex items-center gap-2">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/message.png" alt="Chat" width={18} height={18} draggable={false} />
          <div>
            <span className="font-serif text-[15px] font-medium">Chat log</span>
            <span className="micro ml-2">This morning</span>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button className="btn btn-icon btn-ghost" aria-label="Record voice">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/mic.png" alt="Record" width={18} height={18} draggable={false} />
          </button>
          <button className="btn btn-icon btn-ghost" aria-label="Delete conversation">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/trash.png" alt="Delete" width={18} height={18} draggable={false} />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
        <div className="text-center">
          <span className="micro">Today · 9:42 AM</span>
        </div>

        {messages.map((msg, i) => (
          <div key={i}>
            <div className="micro mb-1">
              {msg.from === 'ed' ? 'Ed' : 'You'} · {msg.time}
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
                        height: `${4 + ((j * 7 + 5) % 13)}px`,
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
            placeholder="Send a message to Ed..."
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
  const sse = useSSE()

  return (
    <div className="relative z-10 h-screen max-w-[1560px] mx-auto px-3.5 py-2.5 grid grid-rows-[auto_1fr] gap-2.5">
      <Topbar connected={sse.connected} />

      {/* Main 3-column grid matching Ed.html layout */}
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