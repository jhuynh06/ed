"use client"

import { useState } from 'react'
import { Topbar } from '@/components/topbar'
import { Heatmap } from '@/components/heatmap'
import { useSSE } from '@/lib/use-sse'
import { AgitationScoreCard } from '@/components/agitation-score-card'
import { AgitationTimeline } from '@/components/agitation-timeline'
import { EpisodeList } from '@/components/episode-list'
import { NotificationFeed } from '@/components/notification-feed'

const tabs = [
  { id: 'overview', label: 'Overview', number: '01' },
  { id: 'voice', label: 'Voice & language', number: '02' },
  { id: 'body', label: 'Body & touch', number: '03' },
  { id: 'cdr', label: 'CDR & trends', number: '04' },
  { id: 'episodes', label: 'Episodes', number: '05' },
]

function OverviewPanel({ sse }: { sse: ReturnType<typeof useSSE> }) {
  return (
    <div className="flex flex-col gap-3">
      <AgitationScoreCard agitation={sse.latestAgitation} vitals={sse.latestVitals} />
      <AgitationTimeline agitation={sse.latestAgitation} agitationHistory={sse.agitationHistory} episodes={sse.episodes} connected={sse.connected} />

      <div className="card p-4">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2">
              <div className="pip" style={{ background: 'var(--plum)' }}></div>
              <span className="micro">Fused emotion · audio + text</span>
            </div>
            <h2 className="font-serif text-[17px] font-normal tracking-tight leading-tight m-0 mt-1">
              Affect right now
            </h2>
            <div className="micro mt-1">Valence × arousal — last 30 minutes</div>
          </div>
          <span className="tag">
            <span className="pip" style={{ background: 'var(--amber)' }}></span>
            Warm · agreeable
          </span>
        </div>

        <div className="grid grid-cols-[1.3fr_1fr] gap-3 items-start">
          {/* Valence/Arousal plot — compact SVG with quadrants + trail */}
          <div className="bg-[var(--paper-3)] border border-[var(--line-soft)] rounded-lg p-1">
            <svg viewBox="0 0 200 160" className="w-full" style={{ maxHeight: '180px' }}>
              {/* Axes */}
              <line x1="100" y1="10" x2="100" y2="150" stroke="var(--line)" strokeWidth="0.5" />
              <line x1="10" y1="80" x2="190" y2="80" stroke="var(--line)" strokeWidth="0.5" />
              {/* Quadrant labels */}
              <text x="32" y="26" fill="var(--ink-3)" fontSize="7" fontFamily="var(--font-mono)" textAnchor="middle" letterSpacing="0.5">ANXIOUS</text>
              <text x="168" y="26" fill="var(--ink-3)" fontSize="7" fontFamily="var(--font-mono)" textAnchor="middle" letterSpacing="0.5">EXCITED</text>
              <text x="32" y="146" fill="var(--ink-3)" fontSize="7" fontFamily="var(--font-mono)" textAnchor="middle" letterSpacing="0.5">SAD</text>
              <text x="168" y="146" fill="var(--ink-3)" fontSize="7" fontFamily="var(--font-mono)" textAnchor="middle" letterSpacing="0.5">CALM</text>
              {/* Axis endpoint labels */}
              <text x="100" y="8" fill="var(--ink-2)" fontSize="5.5" fontFamily="var(--font-mono)" textAnchor="middle" letterSpacing="1">↑ AROUSAL</text>
              <text x="190" y="76" fill="var(--ink-2)" fontSize="5.5" fontFamily="var(--font-mono)" textAnchor="end">+VAL</text>
              <text x="10" y="76" fill="var(--ink-2)" fontSize="5.5" fontFamily="var(--font-mono)" textAnchor="start">−VAL</text>
              {/* Trail line */}
              <polyline points="84,99 96,93 110,86 124,80" fill="none" stroke="var(--ink-4)" strokeWidth="1" strokeDasharray="2 2" />
              {/* Data points oldest → newest */}
              <circle cx="84" cy="99" r="3" fill="var(--ink-4)" opacity="0.35" />
              <circle cx="96" cy="93" r="3.5" fill="var(--ink-4)" opacity="0.5" />
              <circle cx="110" cy="86" r="4" fill="var(--ink-3)" opacity="0.7" />
              <circle cx="124" cy="80" r="9" fill="var(--amber)" opacity="0.15" />
              <circle cx="124" cy="80" r="5" fill="var(--amber)" />
            </svg>
          </div>
          
          {/* Stats */}
          <div className="grid grid-cols-2 gap-2 content-start">
            <div className="stat">
              <div className="stat-label">Audio valence</div>
              <div className="stat-value">+0.34</div>
            </div>
            <div className="stat">
              <div className="stat-label">Audio arousal</div>
              <div className="stat-value">0.41</div>
            </div>
            <div className="stat">
              <div className="stat-label">Text sentiment</div>
              <div className="stat-value">+0.52</div>
            </div>
            <div className="stat">
              <div className="stat-label">Disagreement</div>
              <div className="stat-value">0.08</div>
              <div className="stat-trend" style={{ color: 'var(--sage)' }}>aligned</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function VoicePanel() {
  return (
    <div className="flex flex-col gap-3">
      <div className="card p-4">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2">
              <div className="pip" style={{ background: 'var(--sky)' }}></div>
              <span className="micro">Acoustic features · mic</span>
            </div>
            <h2 className="font-serif text-[17px] font-normal tracking-tight leading-tight m-0 mt-1">
              Voice signature
            </h2>
            <div className="micro mt-1">F0 · perturbation · rate · 14d baseline</div>
          </div>
          <span className="tag">12 min · 1,420 words</span>
        </div>

        <div className="grid grid-cols-3 gap-2 mb-4">
          <div className="stat">
            <div className="stat-label">F0 mean</div>
            <div className="stat-value">118<span className="stat-unit">Hz</span></div>
            <div className="stat-trend">baseline 122 · −3%</div>
          </div>
          <div className="stat">
            <div className="stat-label">F0 std</div>
            <div className="stat-value">14.3<span className="stat-unit">Hz</span></div>
            <div className="stat-trend" style={{ color: 'var(--sage)' }}>expressive</div>
          </div>
          <div className="stat">
            <div className="stat-label">Jitter</div>
            <div className="stat-value">0.71<span className="stat-unit">%</span></div>
            <div className="stat-trend">in range</div>
          </div>
          <div className="stat">
            <div className="stat-label">Shimmer</div>
            <div className="stat-value">3.4<span className="stat-unit">%</span></div>
            <div className="stat-trend" style={{ color: 'var(--amber)' }}>↑ elevated</div>
          </div>
          <div className="stat">
            <div className="stat-label">HNR</div>
            <div className="stat-value">19.2<span className="stat-unit">dB</span></div>
            <div className="stat-trend" style={{ color: 'var(--sage)' }}>clean</div>
          </div>
          <div className="stat">
            <div className="stat-label">Speaking rate</div>
            <div className="stat-value">132<span className="stat-unit">wpm</span></div>
            <div className="stat-trend">baseline 138</div>
          </div>
        </div>

        <div>
          <div className="flex justify-between items-baseline mb-1">
            <div className="micro">Pause rate · per minute · 14d</div>
            <div className="num text-[10.5px] text-[var(--ink-2)]">today 6.4/min</div>
          </div>
          <svg className="w-full h-9" viewBox="0 0 300 36" preserveAspectRatio="none">
            <polyline 
              points="0,18 22,16 44,20 66,15 88,18 110,12 132,16 154,14 176,17 198,13 220,15 242,12 264,16 286,11 300,12"
              fill="none" stroke="var(--sky)" strokeWidth="1.6" strokeLinejoin="round" 
            />
            <line x1="0" y1="18" x2="300" y2="18" stroke="var(--line)" strokeDasharray="2 4" />
          </svg>
        </div>
      </div>

      <div className="card p-4">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2">
              <div className="pip on"></div>
              <span className="micro">NLP features</span>
            </div>
            <h2 className="font-serif text-[17px] font-normal tracking-tight leading-tight m-0 mt-1">
              Language & cognition
            </h2>
            <div className="micro mt-1">Vocabulary diversity · fluency · coherence</div>
          </div>
          <span className="tag">
            <span className="pip on"></span>
            +6% vs. 14d
          </span>
        </div>

        <div className="grid grid-cols-4 gap-2 mb-4">
          <div className="stat">
            <div className="stat-label">Type-token</div>
            <div className="stat-value">0.61</div>
            <div className="stat-trend" style={{ color: 'var(--sage)' }}>↑ rich</div>
          </div>
          <div className="stat">
            <div className="stat-label">Filler rate</div>
            <div className="stat-value">2.4<span className="stat-unit">%</span></div>
            <div className="stat-trend">um · uh</div>
          </div>
          <div className="stat">
            <div className="stat-label">Mean utt.</div>
            <div className="stat-value">11.3<span className="stat-unit">w</span></div>
            <div className="stat-trend">base 9.4</div>
          </div>
          <div className="stat">
            <div className="stat-label">Coherence</div>
            <div className="stat-value">0.78</div>
            <div className="stat-trend" style={{ color: 'var(--sage)' }}>on thread</div>
          </div>
        </div>

        <div>
          <div className="micro mb-2">Topic clusters · this session</div>
          <div className="flex flex-wrap gap-1">
            <span className="chip warm">Fishing × 6</span>
            <span className="chip warm">Margie × 4</span>
            <span className="chip">Canoe trip × 3</span>
            <span className="chip">Weather × 2</span>
            <span className="chip">Breakfast × 2</span>
          </div>
        </div>
      </div>
    </div>
  )
}

function BodyPanel() {
  return (
    <div className="flex flex-col gap-3">
      {/* Touch card */}
      <div className="card p-4">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2">
              <div className="pip off"></div>
              <span className="micro">Touch sensor</span>
            </div>
            <h2 className="font-serif text-[17px] font-normal tracking-tight leading-tight m-0 mt-1">
              Holding & grip
            </h2>
          </div>
          <span className="tag">
            <span className="pip on"></span>
            Engaged
          </span>
        </div>

        <div className="grid grid-cols-3 gap-2 mb-4">
          <div className="stat">
            <div className="stat-label">Squeeze</div>
            <div className="stat-value">0.42<span className="stat-unit">/1</span></div>
            <div className="stat-trend" style={{ color: 'var(--sage)' }}>↓ softened</div>
          </div>
          <div className="stat">
            <div className="stat-label">Grip duration</div>
            <div className="stat-value">4:12<span className="stat-unit">m</span></div>
            <div className="stat-trend" style={{ color: 'var(--sage)' }}>↑ longest wk</div>
          </div>
          <div className="stat">
            <div className="stat-label">Contact %</div>
            <div className="stat-value">68<span className="stat-unit">%</span></div>
            <div className="stat-trend">of session</div>
          </div>
        </div>

        <div>
          <div className="micro mb-1">touch.any_contact · last 30 min</div>
          <svg className="w-full h-9" viewBox="0 0 300 36" preserveAspectRatio="none">
            <defs>
              <linearGradient id="touch-fill-2" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="var(--sage)" stopOpacity="0.45" />
                <stop offset="100%" stopColor="var(--sage)" stopOpacity="0" />
              </linearGradient>
            </defs>
            <path d="M0,30 L8,30 L8,12 L42,12 L42,30 L60,30 L60,16 L120,16 L120,30 L140,30 L140,8 L220,8 L220,30 L260,30 L260,18 L290,18 L290,30 L300,30 Z"
              fill="url(#touch-fill-2)" />
            <path d="M0,30 L8,30 L8,12 L42,12 L42,30 L60,30 L60,16 L120,16 L120,30 L140,30 L140,8 L220,8 L220,30 L260,30 L260,18 L290,18 L290,30 L300,30"
              fill="none" stroke="var(--sage)" strokeWidth="1.5" strokeLinejoin="round" />
          </svg>
        </div>
      </div>

      {/* Body motion card */}
      <div className="card p-4">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2">
              <div className="pip" style={{ background: 'var(--amber)' }}></div>
              <span className="micro">IMU · accelerometer + gyro</span>
            </div>
            <h2 className="font-serif text-[17px] font-normal tracking-tight leading-tight m-0 mt-1">
              Body motion
            </h2>
            <div className="micro mt-1">Stillness · jerk · rocking · hug — last 30 min</div>
          </div>
        </div>

        <div className="space-y-0">
          <div className="meter">
            <div>
              <div className="meter-label">Stillness</div>
              <div className="meter-sub">imu.stillness</div>
            </div>
            <div className="bar calm"><i style={{ width: '68%' }}></i></div>
            <div className="meter-num">4m 32s</div>
          </div>
          <div className="meter">
            <div>
              <div className="meter-label">Jerk magnitude</div>
              <div className="meter-sub">imu.jerk</div>
            </div>
            <div className="bar warn"><i style={{ width: '22%' }}></i></div>
            <div className="meter-num">0.18 g/s</div>
          </div>
          <div className="meter">
            <div>
              <div className="meter-label">Rocking</div>
              <div className="meter-sub">imu.rock @ 0.6 Hz</div>
            </div>
            <div className="bar warn"><i style={{ width: '14%' }}></i></div>
            <div className="meter-num">0.6 Hz</div>
          </div>
          <div className="meter">
            <div>
              <div className="meter-label">Hug detected</div>
              <div className="meter-sub">imu.hug</div>
            </div>
            <div className="bar calm"><i style={{ width: '88%' }}></i></div>
            <div className="meter-num">held</div>
          </div>
          <div className="meter">
            <div>
              <div className="meter-label">Postural drift</div>
              <div className="meter-sub">imu.tilt</div>
            </div>
            <div className="bar cool"><i style={{ width: '32%' }}></i></div>
            <div className="meter-num">8°</div>
          </div>
          <div className="meter">
            <div>
              <div className="meter-label">Activity index</div>
              <div className="meter-sub">imu.rms</div>
            </div>
            <div className="bar warn"><i style={{ width: '36%' }}></i></div>
            <div className="meter-num">0.22 g</div>
          </div>
        </div>
      </div>
    </div>
  )
}

function CDRPanel() {
  return (
    <div className="flex flex-col gap-3">
      {/* CDR domain scores */}
      <div className="card p-4">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2">
              <div className="pip" style={{ background: 'var(--amber)' }}></div>
              <span className="micro">Clinical Dementia Rating · model-inferred</span>
            </div>
            <h2 className="font-serif text-[17px] font-normal tracking-tight leading-tight m-0 mt-1">
              Domain scores
            </h2>
            <div className="micro mt-1">0 none · 0.5 questionable · 1 mild · 2 moderate · 3 severe</div>
          </div>
          <div className="text-right">
            <div className="micro">Sum of boxes</div>
            <div className="font-serif text-[26px] leading-none tracking-tight mt-1">2.0</div>
            <div className="meter-sub mt-1">↓ from 2.5</div>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-2">
          <div className="cdr-cell" style={{ '--c': 'var(--sky)' } as React.CSSProperties}>
            <div className="font-mono text-[8.5px] uppercase tracking-widest text-[var(--ink-3)]">Communication</div>
            <div className="font-serif text-[22px] tracking-tight leading-none">0.5</div>
            <svg className="w-full h-6" viewBox="0 0 100 24" preserveAspectRatio="none">
              <polyline points="0,8 12,8 24,10 36,9 48,12 60,11 72,12 84,12 96,11" fill="none" stroke="var(--sky)" strokeWidth="1.5" />
            </svg>
            <div className="font-mono text-[9px] text-[var(--ink-2)]">stable · expressive</div>
          </div>
          <div className="cdr-cell" style={{ '--c': 'var(--amber)' } as React.CSSProperties}>
            <div className="font-mono text-[8.5px] uppercase tracking-widest text-[var(--ink-3)]">Orientation</div>
            <div className="font-serif text-[22px] tracking-tight leading-none">1.0</div>
            <svg className="w-full h-6" viewBox="0 0 100 24" preserveAspectRatio="none">
              <polyline points="0,14 12,12 24,14 36,16 48,15 60,17 72,16 84,18 96,18" fill="none" stroke="var(--amber)" strokeWidth="1.5" />
            </svg>
            <div className="font-mono text-[9px] text-[var(--ink-2)]">↘ slow drift</div>
          </div>
          <div className="cdr-cell" style={{ '--c': 'var(--rose)' } as React.CSSProperties}>
            <div className="font-mono text-[8.5px] uppercase tracking-widest text-[var(--ink-3)]">Memory</div>
            <div className="font-serif text-[22px] tracking-tight leading-none">1.0</div>
            <svg className="w-full h-6" viewBox="0 0 100 24" preserveAspectRatio="none">
              <polyline points="0,12 12,14 24,13 36,16 48,15 60,17 72,16 84,18 96,17" fill="none" stroke="var(--rose)" strokeWidth="1.5" />
            </svg>
            <div className="font-mono text-[9px] text-[var(--ink-2)]">recurring stories ↑</div>
          </div>
          <div className="cdr-cell" style={{ '--c': 'var(--sage)' } as React.CSSProperties}>
            <div className="font-mono text-[8.5px] uppercase tracking-widest text-[var(--ink-3)]">Judgment</div>
            <div className="font-serif text-[22px] tracking-tight leading-none">0.5</div>
            <svg className="w-full h-6" viewBox="0 0 100 24" preserveAspectRatio="none">
              <polyline points="0,11 12,10 24,12 36,11 48,12 60,11 72,12 84,11 96,12" fill="none" stroke="var(--sage)" strokeWidth="1.5" />
            </svg>
            <div className="font-mono text-[9px] text-[var(--ink-2)]">good problem-solving</div>
          </div>
        </div>
      </div>

      {/* 14-day trends */}
      <div className="card p-4 flex flex-col">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2">
              <div className="pip" style={{ background: 'var(--plum)' }}></div>
              <span className="micro">14-day trends</span>
            </div>
            <h2 className="font-serif text-[17px] font-normal tracking-tight leading-tight m-0 mt-1">
              What&apos;s changing
            </h2>
            <div className="micro mt-1">Daily aggregates over the last two weeks</div>
          </div>
        </div>

        {/* Multi-line trend chart */}
        <svg viewBox="0 0 320 120" preserveAspectRatio="none" className="w-full flex-1 min-h-0" style={{ maxHeight: '160px' }}>
          {/* Gridlines */}
          <line x1="0" y1="20" x2="320" y2="20" stroke="var(--line-soft)" strokeDasharray="2 4" />
          <line x1="0" y1="60" x2="320" y2="60" stroke="var(--line-soft)" strokeDasharray="2 4" />
          <line x1="0" y1="100" x2="320" y2="100" stroke="var(--line-soft)" strokeDasharray="2 4" />

          {/* Engagement (sage) */}
          <polyline points="0,80 22,72 44,76 66,68 88,70 110,62 132,64 154,58 176,60 198,52 220,55 242,48 264,50 286,42 308,46 320,44"
            fill="none" stroke="var(--sage)" strokeWidth="1.8" strokeLinejoin="round" />

          {/* Agitation (rose) */}
          <polyline points="0,40 22,42 44,38 66,46 88,42 110,50 132,46 154,52 176,48 198,56 220,54 242,60 264,58 286,62 308,60 320,64"
            fill="none" stroke="var(--rose)" strokeWidth="1.8" strokeLinejoin="round" />

          {/* Cognition (sky) */}
          <polyline points="0,60 22,58 44,62 66,60 88,64 110,60 132,62 154,58 176,60 198,56 220,58 242,55 264,56 286,52 308,54 320,52"
            fill="none" stroke="var(--sky)" strokeWidth="1.8" strokeLinejoin="round" />
        </svg>

        <div className="grid grid-cols-3 gap-2 mt-3">
          <div className="stat">
            <div className="stat-label flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--sage)]"></span>
              Engagement
            </div>
            <div className="stat-value">+18<span className="stat-unit">%</span></div>
            <div className="stat-trend" style={{ color: 'var(--sage)' }}>trending up</div>
          </div>
          <div className="stat">
            <div className="stat-label flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--rose)]"></span>
              Agitation
            </div>
            <div className="stat-value">−12<span className="stat-unit">%</span></div>
            <div className="stat-trend" style={{ color: 'var(--sage)' }}>calmer week</div>
          </div>
          <div className="stat">
            <div className="stat-label flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--sky)]"></span>
              Cognition
            </div>
            <div className="stat-value">+4<span className="stat-unit">%</span></div>
            <div className="stat-trend">stable</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function AnalysisPage() {
  const [activeTab, setActiveTab] = useState('overview')
  const sse = useSSE()

  const renderPanel = () => {
    switch (activeTab) {
      case 'overview': return <OverviewPanel sse={sse} />
      case 'voice': return <VoicePanel />
      case 'body': return <BodyPanel />
      case 'cdr': return <CDRPanel />
      case 'episodes': return <EpisodeList episodes={sse.episodes} />
      default: return <OverviewPanel sse={sse} />
    }
  }

  return (
    <div className="relative z-10 h-screen overflow-hidden max-w-[1500px] mx-auto p-3 grid grid-rows-[auto_1fr] gap-3">
      <Topbar connected={sse.connected} />
      
      {/* Main content */}
      <div className="grid grid-cols-[minmax(0,1.18fr)_minmax(0,1fr)] gap-3 min-h-0 h-full">
        {/* Left column */}
        <div className="flex flex-col gap-3 min-h-0 overflow-y-auto">
          <NotificationFeed notifications={sse.notifications} />
          <Heatmap />
          
          {/* Events strip */}
          <div className="card p-3">
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="flex items-center gap-2">
                  <div className="pip" style={{ background: 'var(--amber)' }}></div>
                  <span className="micro">Notable today</span>
                </div>
              </div>
              <span className="micro">6 events</span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <div className="bg-[var(--paper-3)] border border-[var(--line-soft)] rounded-lg p-2">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-mono text-[9.5px] text-[var(--ink-3)] tracking-wider">06:42</span>
                  <span className="chip calm">Hug</span>
                </div>
                <div className="font-serif text-[12px] leading-tight text-[var(--ink)]">
                  Sustained hug · 4m 12s — longest this week.
                </div>
              </div>
              <div className="bg-[var(--paper-3)] border border-[var(--line-soft)] rounded-lg p-2">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-mono text-[9.5px] text-[var(--ink-3)] tracking-wider">07:18</span>
                  <span className="chip warm">Story</span>
                </div>
                <div className="font-serif text-[12px] leading-tight text-[var(--ink)]">
                  &quot;Fishing with dad&quot; — 6th time in 14 days, ↑ frequency.
                </div>
              </div>
              <div className="bg-[var(--paper-3)] border border-[var(--line-soft)] rounded-lg p-2">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-mono text-[9.5px] text-[var(--ink-3)] tracking-wider">08:31</span>
                  <span className="chip alert">Disorient</span>
                </div>
                <div className="font-serif text-[12px] leading-tight text-[var(--ink)]">
                  &quot;Where am I&quot; — first this week. Resolved 40 s.
                </div>
              </div>
            </div>
          </div>

          {/* Memory Timeline */}
          <div className="card p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="micro">Memory timeline · Recurring topics & people</span>
              <span className="chip alert">1 flagged</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              <span className="chip alert">Fishing with dad × 6</span>
              <span className="chip warm">Margie × 4</span>
              <span className="chip">Sunday roast × 3</span>
              <span className="chip">The old dog × 2</span>
              <span className="chip">Canoe trip × 2</span>
              <span className="chip">Frank × 1</span>
            </div>
          </div>
        </div>
        
        {/* Right: Tabs + Tab content */}
        <div className="flex flex-col gap-3 min-h-0 overflow-y-auto">
          <div className="flex items-center gap-1 p-1 bg-[var(--paper-3)] border border-[var(--line)] rounded-xl shadow-[var(--shadow-card)] w-fit sticky top-0 z-10" role="tablist">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={activeTab === tab.id}
                className={`flex items-center gap-2 py-2 px-4 rounded-lg font-medium text-[12.5px] tracking-wide transition-all ${
                  activeTab === tab.id
                    ? 'bg-[var(--paper)] text-[var(--ink)] shadow-[0_1px_0_oklch(1_0_0_/_0.9)_inset,_0_1px_2px_oklch(0.4_0.02_60_/_0.10)]'
                    : 'text-[var(--ink-2)] hover:text-[var(--ink)]'
                }`}
                onClick={() => setActiveTab(tab.id)}
              >
                <div className={`w-1.5 h-1.5 rounded-full ${activeTab === tab.id ? 'bg-[var(--sage)]' : 'bg-[var(--ink-4)]'}`}></div>
                {tab.label}
                <span className="font-mono text-[10px] text-[var(--ink-3)] ml-1 tracking-wider">{tab.number}</span>
              </button>
            ))}
          </div>
          <div className="min-h-0">
            {renderPanel()}
          </div>
        </div>
      </div>
    </div>
  )
}