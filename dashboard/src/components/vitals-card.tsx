"use client"

import type { VitalsUpdate } from '@/lib/sse-types'
import { mockHRHistory } from '@/lib/mock-data'

interface VitalsCardProps {
  vitals: VitalsUpdate | null
}

export function VitalsCard({ vitals }: VitalsCardProps) {
  const bpm = vitals?.bpm ?? 0
  const spo2 = vitals?.spo2 ?? 0
  const baseline = vitals?.baseline_bpm ?? 72
  const elevation = bpm > 0 ? ((bpm - baseline) / baseline * 100) : 0
  
  // Use mock HR history for sparkline
  const history = mockHRHistory.slice(-10) // Last 10 readings
  
  const generateSparklinePath = () => {
    if (history.length === 0) return ''
    
    const width = 100
    const height = 22
    const minBpm = Math.min(...history.map(h => h.bpm))
    const maxBpm = Math.max(...history.map(h => h.bpm))
    const range = maxBpm - minBpm || 1
    
    const points = history.map((point, index) => {
      const x = (index / (history.length - 1)) * width
      const y = height - ((point.bpm - minBpm) / range) * height
      return `${x},${y}`
    })
    
    return `M ${points.join(' L ')}`
  }

  return (
    <div className="card p-4 flex flex-col gap-4">
      <div>
        <div className="flex items-center gap-2">
          <div className={`pip ${vitals ? 'on' : 'off'}`}></div>
          <span className="micro">Heart rate · SpO2 · paw sensor</span>
        </div>
        <h2 className="font-serif text-[17px] font-normal tracking-tight leading-tight m-0 mt-1">
          Vitals
        </h2>
        <div className="micro mt-1">MAX30102 pulse oximeter · 30s average</div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Heart Rate */}
        <div className="stat">
          <div className="stat-label">Heart rate</div>
          <div className="flex items-baseline gap-2">
            <div className="stat-value">{bpm}<span className="stat-unit">bpm</span></div>
          </div>
          <div className="stat-trend">
            baseline {baseline} · {elevation > 0 ? '+' : ''}{elevation.toFixed(1)}%
          </div>
        </div>

        {/* SpO2 */}
        <div className="stat">
          <div className="stat-label">Blood oxygen</div>
          <div className="stat-value">{spo2}<span className="stat-unit">%</span></div>
          <div className="stat-trend" style={{ color: spo2 >= 95 ? 'var(--sage)' : 'var(--amber)' }}>
            {spo2 >= 95 ? 'normal' : 'monitor'}
          </div>
        </div>
      </div>

      {/* HR Elevation indicator */}
      <div className="flex items-center justify-between">
        <span className="text-[11.5px] text-[var(--ink)]">Elevation</span>
        <div className="flex items-center gap-2">
          <div className="bar calm w-20">
            <i style={{ width: `${Math.min(Math.abs(elevation), 100)}%` }}></i>
          </div>
          <span className="font-mono text-[10.5px] text-[var(--ink)] tabular-nums">
            {elevation > 0 ? '↑' : elevation < 0 ? '↓' : '→'} {Math.abs(elevation).toFixed(1)}%
          </span>
        </div>
      </div>

      {/* HR History sparkline */}
      <div>
        <div className="flex justify-between items-baseline mb-1">
          <span className="micro">HR trend · last 50 min</span>
          <span className="font-mono text-[10.5px] text-[var(--ink-2)]">
            {history.length > 0 ? `${Math.round(history[history.length - 1].bpm)} bpm` : '-- bpm'}
          </span>
        </div>
        <svg viewBox="0 0 100 22" className="w-full h-6" preserveAspectRatio="none">
          <path 
            d={generateSparklinePath()} 
            fill="none" 
            stroke="var(--sage)" 
            strokeWidth="1.6" 
            strokeLinejoin="round"
          />
          {/* Baseline reference line */}
          <line 
            x1="0" 
            y1="11" 
            x2="100" 
            y2="11" 
            stroke="var(--line)" 
            strokeWidth="1" 
            strokeDasharray="2 4" 
            opacity="0.6"
          />
        </svg>
      </div>
    </div>
  )
}