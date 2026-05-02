"use client"

import { useEffect, useState } from 'react'

interface HeatmapProps {
  className?: string
}

// Generate mock heatmap data (24 hours × 4 rows)
function generateHeatmapData() {
  const data = []
  const rows = ['touch', 'speech', 'motion', 'hug']
  
  for (const row of rows) {
    const rowData = []
    for (let hour = 0; hour < 24; hour++) {
      let intensity = 0
      
      // Simulate daily patterns
      if (row === 'touch') {
        // More touch during awake hours
        if (hour >= 6 && hour <= 22) {
          intensity = Math.random() * 0.8 + 0.2
        } else {
          intensity = Math.random() * 0.3
        }
      } else if (row === 'speech') {
        // Speech peaks in morning and evening
        if ((hour >= 7 && hour <= 9) || (hour >= 17 && hour <= 20)) {
          intensity = Math.random() * 0.9 + 0.1
        } else if (hour >= 6 && hour <= 22) {
          intensity = Math.random() * 0.6
        } else {
          intensity = Math.random() * 0.1
        }
      } else if (row === 'motion') {
        // Motion throughout day, less at night
        if (hour >= 6 && hour <= 22) {
          intensity = Math.random() * 0.7 + 0.1
        } else {
          intensity = Math.random() * 0.2
        }
      } else if (row === 'hug') {
        // Occasional hugs, more likely during emotional moments
        if (Math.random() < 0.15) {
          intensity = Math.random() * 0.8 + 0.2
        } else {
          intensity = 0
        }
      }
      
      rowData.push(intensity)
    }
    data.push(rowData)
  }
  
  return data
}

function getHeatColor(intensity: number): string {
  if (intensity === 0) return 'var(--paper-4)'
  if (intensity < 0.3) return 'color-mix(in oklch, var(--sage) 30%, var(--paper-4))'
  if (intensity < 0.6) return 'color-mix(in oklch, var(--sage) 60%, var(--paper-4))'
  if (intensity < 0.8) return 'var(--sage)'
  return 'color-mix(in oklch, var(--sage) 80%, var(--amber) 20%)'
}

export function Heatmap({ className = '' }: HeatmapProps) {
  const [data, setData] = useState<number[][]>([])
  
  useEffect(() => {
    setData(generateHeatmapData())
  }, [])

  const rowLabels = [
    { label: 'Touch', sub: 'contact' },
    { label: 'Speech', sub: 'voicing' },
    { label: 'Motion', sub: 'imu rms' },
    { label: 'Hug', sub: 'imu hug' }
  ]

  const timeLabels = ['00', '03', '06', '09', '12', '15', '18', '21', '24']

  return (
    <div className={`card p-3 flex flex-col gap-4 ${className}`}>
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <div className="pip on"></div>
            <span className="micro">Last 24 hours · 1h bins</span>
          </div>
          <h2 className="font-serif text-[17px] font-normal tracking-tight leading-tight m-0 mt-1">
            Engagement heatmap
          </h2>
          <div className="micro mt-1">Touch · speech · motion · hug — fused engagement signal</div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-sm" style={{ background: 'var(--sage)' }}></div>
            <span className="micro">high</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-sm" style={{ background: 'color-mix(in oklch, var(--sage) 40%, var(--paper-4))' }}></div>
            <span className="micro">mid</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-sm border border-[var(--line)]" style={{ background: 'var(--paper-4)' }}></div>
            <span className="micro">none</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-[86px_1fr] gap-3 items-center">
        {data.map((rowData, rowIndex) => (
          <>
            <div key={`label-${rowIndex}`} className="font-mono text-[10px] uppercase tracking-wider text-[var(--ink-2)]">
              {rowLabels[rowIndex].label}
              <div className="font-mono text-[9px] text-[var(--ink-3)] tracking-normal lowercase mt-0.5">
                {rowLabels[rowIndex].sub}
              </div>
            </div>
            <div key={`data-${rowIndex}`} className="grid grid-cols-24 gap-1">
              {rowData.map((intensity, hourIndex) => (
                <div
                  key={`${rowIndex}-${hourIndex}`}
                  className="heatdot"
                  style={{ backgroundColor: getHeatColor(intensity) }}
                  title={`${rowLabels[rowIndex].label} at ${hourIndex}:00 - ${Math.round(intensity * 100)}%`}
                />
              ))}
            </div>
          </>
        ))}
        
        {/* Time axis */}
        <div></div>
        <div className="flex justify-between px-0.5 font-mono text-[9px] text-[var(--ink-3)] tracking-wider">
          {timeLabels.map((label, index) => (
            <span key={index} className={index % 2 === 1 ? 'text-[var(--ink-2)]' : ''}>
              {label}
            </span>
          ))}
        </div>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-4 gap-2 pt-2 border-t border-[var(--line-soft)]">
        <div className="flex flex-col gap-0.5">
          <div className="font-mono text-[9px] uppercase tracking-wider text-[var(--ink-3)]">Active hours</div>
          <div className="font-serif text-[18px] tracking-tight leading-none">
            11.5<span className="font-mono text-[11px] text-[var(--ink-3)] ml-1">h</span>
          </div>
          <div className="font-mono text-[9.5px] text-[var(--sage)] tracking-wider">↑ +1.2h vs. 14d</div>
        </div>
        <div className="flex flex-col gap-0.5">
          <div className="font-mono text-[9px] uppercase tracking-wider text-[var(--ink-3)]">Peak window</div>
          <div className="font-serif text-[18px] tracking-tight leading-none">
            06:30<span className="font-mono text-[11px] text-[var(--ink-3)] ml-1">–08:00</span>
          </div>
          <div className="font-mono text-[9.5px] text-[var(--ink-2)] tracking-wider">morning routine</div>
        </div>
        <div className="flex flex-col gap-0.5">
          <div className="font-mono text-[9px] uppercase tracking-wider text-[var(--ink-3)]">Quiet stretch</div>
          <div className="font-serif text-[18px] tracking-tight leading-none">
            22:00<span className="font-mono text-[11px] text-[var(--ink-3)] ml-1">–05:30</span>
          </div>
          <div className="font-mono text-[9.5px] text-[var(--ink-2)] tracking-wider">restful sleep</div>
        </div>
        <div className="flex flex-col gap-0.5">
          <div className="font-mono text-[9px] uppercase tracking-wider text-[var(--ink-3)]">Hug events</div>
          <div className="font-serif text-[18px] tracking-tight leading-none">
            4<span className="font-mono text-[11px] text-[var(--ink-3)] ml-1">today</span>
          </div>
          <div className="font-mono text-[9.5px] text-[var(--sage)] tracking-wider">↑ longest 4m 12s</div>
        </div>
      </div>
    </div>
  )
}