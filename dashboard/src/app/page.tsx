"use client"

import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { useSSE } from '@/lib/use-sse'
import { useBearStatus } from '@/lib/use-status'
import type { SensorUpdate, Transcription } from '@/lib/sse-types'
import Link from 'next/link'
import { usePatient } from '@/lib/patient-context'
import { Mic, Play, Pause, Plus, Check, X, Send, ArrowRight, Trash2 } from 'lucide-react'
import { getChatMessages, sendChatMessage, clearChat } from '@/lib/api'

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
          {active?.avatar ?? 'T'}
        </button>
        <div>
          <div className="micro">Caregiver dashboard{active ? ` · ${active.name}` : ''}</div>
          <h1 className="font-serif text-[24px] font-normal tracking-tight leading-tight m-0">
            {active?.companion ?? 'Theodore'} <span className="text-[var(--ink-3)] font-light">· {timeLabel || 'loading'}</span>
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
  const meds = [
    { id: '1', name: 'Donepezil', freq: '1×/day', weekly: '7×/wk', done: 1, total: 1, status: 'done' },
    { id: '2', name: 'Memantine', freq: '2×/day', weekly: '7×/wk', done: 1, total: 2, status: 'partial' },
    { id: '3', name: 'Vitamin D', freq: '1×/day', weekly: '3×/wk', done: 0, total: 1, status: 'pending' },
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
          <div key={med.id} className="sunken p-3 flex items-center gap-3">
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
function BodyStatusCard({ sensor }: { sensor: SensorUpdate | null }) {
  const hasData = sensor !== null
  const pads = hasData ? sensor.touch_active_pads : []
  const isActive = (idx: number) => pads.includes(idx)
  const activeCount = pads.length

  // ESP32 touch pad mapping:
  // 0: front_left, 1: front_right, 2: back_left, 3: back_right
  // 4: upper_back, 5: lower_back, 6: upper_chest, 7: lower_chest
  const padPositions = [
    { idx: 0, label: "Front left",   top: "55%", left: "8%" },
    { idx: 1, label: "Front right",  top: "55%", right: "8%" },
    { idx: 2, label: "Back left",    top: "42%", left: "18%" },
    { idx: 3, label: "Back right",   top: "42%", right: "18%" },
    { idx: 4, label: "Upper back",   top: "35%", left: "50%", transform: "translateX(-50%)" },
    { idx: 5, label: "Lower back",   top: "70%", left: "50%", transform: "translateX(-50%)" },
    { idx: 6, label: "Upper chest",  top: "48%", left: "50%", transform: "translateX(-50%)" },
    { idx: 7, label: "Lower chest",  top: "62%", left: "50%", transform: "translateX(-50%)" },
  ]

  return (
    <div className="card p-4 flex flex-col gap-3 h-full">
      <div className="flex items-center justify-between">
        <div>
          <div className="micro">Touch sensors</div>
          <h2 className="font-serif text-[17px] font-normal tracking-tight leading-tight m-0 mt-0.5">Body status</h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="micro">{hasData ? `${activeCount}/8 active` : 'No data'}</span>
          <div className={`pip ${hasData ? (activeCount > 0 ? 'on' : 'idle') : 'off'}`} />
          <span className="micro">{hasData ? 'Live' : 'Waiting'}</span>
        </div>
      </div>

      <div className="relative flex items-center justify-center flex-1 py-2">
        <div className="relative w-48 h-full max-h-64">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/ed-plushie.png"
            alt="Ed plushie touch sensor map"
            className="w-full h-full object-contain drift"
            draggable={false}
          />

          {padPositions.map((pad) => (
            <div
              key={pad.idx}
              className="absolute"
              style={{ top: pad.top, left: pad.left, right: pad.right, transform: pad.transform }}
            >
              <div
                className={`pip ${isActive(pad.idx) ? 'on' : 'off'}`}
                title={`${pad.label}: ${isActive(pad.idx) ? 'Touched' : 'Idle'}`}
              />
            </div>
          ))}
        </div>
      </div>

      {hasData && (
        <div className="flex gap-4 text-[12px] flex-wrap">
          <div><span className="micro">Squeeze</span> <span className="font-mono">{sensor.touch_squeeze.toFixed(2)}</span></div>
          <div><span className="micro">Grip</span> <span className="font-mono">{sensor.touch_grip_s.toFixed(0)}s</span></div>
          {sensor.touch_petting && <span className="chip warm">Petting</span>}
          {sensor.imu_hug && <span className="chip calm">Hug</span>}
        </div>
      )}
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
function VoiceTransmitCard({ latestTranscription }: { latestTranscription: Transcription | null }) {
  const [recording, setRecording] = useState(false)
  const [seconds, setSeconds] = useState(0)

  const isRecent = latestTranscription && (Date.now() / 1000 - latestTranscription.timestamp) < 10

  const handleToggle = () => {
    if (recording) {
      setRecording(false)
      setSeconds(0)
    } else {
      setRecording(true)
    }
  }

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
      {isRecent && (
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-[var(--sage)] animate-pulse" />
          <span className="chip calm">{latestTranscription.emotion}</span>
        </div>
      )}
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
interface ChatMsg {
  sender: string
  content: string
  msg_type: string
  created_at: number
  emotion?: string
}

function ChatLog({ transcriptions }: { transcriptions: Transcription[] }) {
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState<ChatMsg[]>([])
  const [sending, setSending] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const { active } = usePatient()
  const pid = active?.id ?? 'p1'

  const load = useCallback(() => {
    getChatMessages(pid).then((rows) => setMessages(rows as unknown as ChatMsg[])).catch(() => {})
  }, [pid])

  useEffect(() => { load() }, [load])
  useEffect(() => { const id = setInterval(load, 5000); return () => clearInterval(id) }, [load])

  const merged = useMemo(() => {
    const transcriptionMsgs: ChatMsg[] = transcriptions.map(t => ({
      sender: 'patient',
      content: t.text,
      msg_type: 'transcription',
      created_at: t.timestamp,
      emotion: t.emotion,
    }))
    return [...messages, ...transcriptionMsgs].sort((a, b) => a.created_at - b.created_at)
  }, [messages, transcriptions])

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [merged.length])

  const handleSend = async () => {
    const text = message.trim()
    if (!text || sending) return
    setSending(true)
    setMessage('')
    setMessages(prev => [...prev, { sender: 'user', content: text, msg_type: 'text', created_at: Date.now() / 1000 }])
    try {
      await sendChatMessage(pid, 'user', text)
      load()
    } catch { /* keep optimistic msg */ }
    setSending(false)
  }

  const handleClear = async () => {
    await clearChat(pid)
    setMessages([])
  }

  const fmtTime = (ts: number) => new Date(ts * 1000).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })

  const senderLabel = (sender: string) => {
    if (sender === 'patient') return 'Patient'
    if (sender === 'theodore') return 'Theodore'
    return 'You'
  }

  return (
    <div className="card flex flex-col h-full min-h-0">
      <div className="p-4 pb-3 border-b border-[var(--line-soft)] flex items-center justify-between">
        <div className="flex items-center gap-2">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/message.png" alt="Chat" width={18} height={18} draggable={false} />
          <div>
            <span className="font-serif text-[15px] font-medium">Chat log</span>
            <span className="micro ml-2">{merged.length} messages</span>
          </div>
        </div>
        <button className="btn btn-icon btn-ghost" aria-label="Delete conversation" onClick={handleClear}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/trash.png" alt="Delete" width={18} height={18} draggable={false} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
        {merged.map((msg, i) => (
          <div key={i}>
            <div className="micro mb-1">
              {senderLabel(msg.sender)} · {fmtTime(msg.created_at)}
              {msg.emotion && <span className="chip calm ml-1.5 text-[10px]">{msg.emotion}</span>}
            </div>
            <div
              className={`inline-block px-4 py-3 rounded-2xl max-w-[85%] font-serif text-[14.5px] leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-[var(--ink)] text-[var(--paper)] rounded-br-md'
                  : msg.sender === 'patient'
                    ? 'bg-[var(--paper-3)] text-[var(--ink)] rounded-bl-md border border-[var(--line)]'
                    : 'bg-[var(--paper-3)] text-[var(--ink)] rounded-bl-md'
              }`}
              style={msg.sender === 'user' ? { marginLeft: 'auto', display: 'block', textAlign: 'left', float: 'right', clear: 'both' } : { clear: 'both' }}
            >
              {msg.content}
            </div>
            <div className="clear-both" />
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="p-3 pt-2 border-t border-[var(--line-soft)]">
        <form className="flex items-center gap-2" onSubmit={(e) => { e.preventDefault(); handleSend() }}>
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Send a message to Theodore..."
            className="flex-1 bg-[var(--paper-3)] border border-[var(--line)] rounded-full px-4 py-2.5 text-[13px] placeholder:text-[var(--ink-4)]"
          />
          <button type="submit" disabled={sending || !message.trim()} className="btn btn-primary gap-1.5 py-2.5">
            <Send size={13} /> Send
          </button>
        </form>
      </div>
    </div>
  )
}

/* ─── Main Dashboard ─────────────────────────────────────── */
export default function Dashboard() {
  const sse = useSSE()
  const bearConnected = useBearStatus()
  const connected = sse.connected && bearConnected

  const latestTranscription = sse.transcriptions.length > 0
    ? sse.transcriptions[sse.transcriptions.length - 1]
    : null

  return (
    <div className="relative z-10 h-screen max-w-[1560px] mx-auto px-3.5 py-2.5 grid grid-rows-[auto_1fr] gap-2.5">
      <Topbar connected={connected} />

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
            <BodyStatusCard sensor={sse.latestSensor} />
          </div>
          <VoiceTransmitCard latestTranscription={latestTranscription} />
        </div>

        {/* Center bottom: Today's Insight */}
        <div className="min-h-0 overflow-hidden" style={{ gridArea: 'mid-bot' }}>
          <TodaysInsightCard />
        </div>

        {/* Right: Chat log spans both rows */}
        <div className="min-h-0" style={{ gridArea: 'chat' }}>
          <ChatLog transcriptions={sse.transcriptions} />
        </div>
      </div>
    </div>
  )
}
