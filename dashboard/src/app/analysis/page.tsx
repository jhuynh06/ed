"use client"

import { useState } from 'react'
import { Topbar } from '@/components/topbar'
import { Heatmap } from '@/components/heatmap'

const tabs = [
  { id: 'overview', label: 'Overview', number: '01' },
  { id: 'voice', label: 'Voice & language', number: '02' },
  { id: 'body', label: 'Body & touch', number: '03' },
  { id: 'cdr', label: 'CDR & trends', number: '04' }
]

function OverviewPanel() {
  return (
    <div className="flex flex-col gap-3 h-full">
      <div className="card p-4 flex items-center gap-6">
        {/* Circular gauge */}
        <div className="relative w-28 h-28 flex-none">
          <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
            <circle cx="50" cy="50" r="42" fill="none" stroke="var(--line)" strokeWidth="9" />
            <circle 
              cx="50" cy="50" r="42" fill="none"
              stroke="url(#agg-grad)" strokeWidth="9"
              strokeDasharray="263.9" strokeDashoffset="195"
              strokeLinecap="round" 
            />
            <defs>
              <linearGradient id="agg-grad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="var(--sage)" />
                <stop offset="60%" stopColor="var(--amber)" />
                <stop offset="100%" stopColor="var(--rose)" />
              </linearGradient>
            </defs>
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="font-serif text-[30px] leading-none tracking-tight">26</div>
              <div className="micro mt-1">/ 100</div>
            </div>
          </div>
        </div>

        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <div className="pip on breathe"></div>
            <span className="micro">Composite · IMU + acoustic + touch</span>
          </div>
          <h2 className="font-serif text-[17px] font-normal tracking-tight leading-tight m-0">
            Agitation score · calm window
          </h2>
          <div className="micro mb-3">Reweighted (no HR available) · running 5-min mean</div>
          
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
                <div className="meter-label">Hug</div>
                <div className="meter-sub">imu.hug</div>
              </div>
              <div className="bar calm"><i style={{ width: '88%' }}></i></div>
              <div className="meter-num">held</div>
            </div>
            <div className="meter">
              <div>
                <div className="meter-label">Jerk</div>
                <div className="meter-sub">imu.jerk</div>
              </div>
              <div className="bar warn"><i style={{ width: '22%' }}></i></div>
              <div className="meter-num">0.18 g/s</div>
            </div>
          </div>
        </div>
      </div>

      <div className="card p-4 flex-1">
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

        <div className="grid grid-cols-[1.3fr_1fr] gap-3 items-stretch">
          {/* Valence/Arousal plot */}
          <div className="relative aspect-[8/5] bg-[var(--paper-3)] border border-[var(--line-soft)] rounded-lg">
            <div className="absolute left-2 top-2 micro">High arousal</div>
            <div className="absolute left-2 bottom-2 micro">Low arousal</div>
            <div className="absolute right-2 top-1/2 -translate-y-1/2 micro">Positive</div>
            <div className="absolute left-2 top-1/2 -translate-y-1/2 micro">Negative</div>
            
            {/* Axes */}
            <div className="absolute left-0 right-0 top-1/2 h-px bg-[var(--line-soft)]"></div>
            <div className="absolute top-0 bottom-0 left-1/2 w-px bg-[var(--line-soft)]"></div>
            
            {/* Data points */}
            <div className="absolute w-2 h-2 rounded-full bg-[var(--ink-4)] opacity-50" style={{ left: '42%', top: '62%', transform: 'translate(-50%, -50%)' }}></div>
            <div className="absolute w-2 h-2 rounded-full bg-[var(--ink-4)] opacity-65" style={{ left: '48%', top: '58%', transform: 'translate(-50%, -50%)' }}></div>
            <div className="absolute w-2.5 h-2.5 rounded-full bg-[var(--ink-3)] opacity-85" style={{ left: '55%', top: '54%', transform: 'translate(-50%, -50%)' }}></div>
            <div className="absolute w-3 h-3 rounded-full bg-[var(--amber)]" style={{ left: '62%', top: '50%', transform: 'translate(-50%, -50%)', boxShadow: '0 0 0 4px color-mix(in oklch, var(--amber) 22%, transparent)' }}></div>
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
    <div className="flex flex-col gap-3 h-full">
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

      <div className="card p-4 flex-1">
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
    <div className="flex flex-col gap-3 h-full">
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
      <div className="card p-4 flex-1">
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
    <div className="flex flex-col gap-3 h-full">
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
      <div className="card p-4 flex-1 flex flex-col">
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

  const renderPanel = () => {
    switch (activeTab) {
      case 'overview': return <OverviewPanel />
      case 'voice': return <VoicePanel />
      case 'body': return <BodyPanel />
      case 'cdr': return <CDRPanel />
      default: return <OverviewPanel />
    }
  }

  return (
    <div className="relative z-10 h-screen max-w-[1500px] mx-auto p-3 grid grid-rows-[auto_1fr] gap-3">
      <Topbar connected={true} />
      
      {/* Main content */}
      <div className="grid grid-cols-[minmax(0,1.18fr)_minmax(0,1fr)] gap-3 min-h-0">
        {/* Left: Heatmap (always visible) */}
        <div className="flex flex-col gap-3 min-h-0">
          <Heatmap className="flex-1" />
          
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
                  "Fishing with dad" — 6th time in 14 days, ↑ frequency.
                </div>
              </div>
              <div className="bg-[var(--paper-3)] border border-[var(--line-soft)] rounded-lg p-2">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-mono text-[9.5px] text-[var(--ink-3)] tracking-wider">08:31</span>
                  <span className="chip alert">Disorient</span>
                </div>
                <div className="font-serif text-[12px] leading-tight text-[var(--ink)]">
                  "Where am I" — first this week. Resolved 40 s.
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Right: Tabs + Tab content */}
        <div className="flex flex-col gap-3 min-h-0">
          <div className="flex items-center gap-1 p-1 bg-[var(--paper-3)] border border-[var(--line)] rounded-xl shadow-[var(--shadow-card)] w-fit">
            {tabs.map((tab) => (
              <button
                key={tab.id}
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
          <div className="min-h-0 flex-1">
            {renderPanel()}
          </div>
        </div>
      </div>
    </div>
  )
}