"use client"

import type { AgitationUpdate } from '@/lib/sse-types'

interface AgitationScoreCardProps {
  agitation: AgitationUpdate | null
  sundowning?: boolean
}

export function AgitationScoreCard({ agitation, sundowning = false }: AgitationScoreCardProps) {
  const score = agitation?.score ?? 0
  const risk = agitation?.risk ?? 'low'
  
  // Calculate stroke-dashoffset for circular progress (circumference = 2π × 42 = 263.9)
  const circumference = 263.9
  const progress = score / 100
  const strokeDashoffset = circumference - (progress * circumference)
  
  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'var(--sage)'
      case 'medium': return 'var(--amber)'
      case 'high': return 'var(--rose)'
      default: return 'var(--ink-4)'
    }
  }

  const getRiskLabel = (risk: string) => {
    switch (risk) {
      case 'low': return 'Calm'
      case 'medium': return 'Elevated'
      case 'high': return 'High'
      default: return 'Unknown'
    }
  }

  return (
    <div className="card p-4 flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <div className={`pip ${risk === 'low' ? 'on' : risk === 'medium' ? 'idle' : 'off'} breathe`}></div>
          <span className="micro">Composite · IMU + acoustic + touch</span>
        </div>
        {sundowning && (
          <span className="chip warm">Sundowning</span>
        )}
      </div>

      <div className="flex items-center gap-6">
        {/* Circular gauge */}
        <div className="relative w-28 h-28 flex-none">
          <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
            <circle 
              cx="50" 
              cy="50" 
              r="42" 
              fill="none" 
              stroke="var(--line)" 
              strokeWidth="9" 
            />
            <circle 
              cx="50" 
              cy="50" 
              r="42" 
              fill="none"
              stroke={getRiskColor(risk)}
              strokeWidth="9"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              className="transition-all duration-1000 ease-out"
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
              <div className="font-serif text-[30px] leading-none tracking-tight">{Math.round(score)}</div>
              <div className="micro mt-1">/ 100</div>
            </div>
          </div>
        </div>

        {/* Risk level and metrics */}
        <div className="flex-1 min-w-0">
          <div className="mb-3">
            <h2 className="font-serif text-[17px] font-normal tracking-tight leading-tight m-0">
              Agitation score · {getRiskLabel(risk).toLowerCase()} window
            </h2>
            <div className="micro mt-1">Reweighted (no HR available) · running 5-min mean</div>
          </div>

          {/* Meters */}
          <div className="space-y-0">
            <div className="meter">
              <div>
                <div className="meter-label">Stillness</div>
                <div className="meter-sub">imu.stillness</div>
              </div>
              <div className="bar calm">
                <i style={{ width: '68%' }}></i>
              </div>
              <div className="meter-num">4m 32s</div>
            </div>
            
            <div className="meter">
              <div>
                <div className="meter-label">Hug</div>
                <div className="meter-sub">imu.hug</div>
              </div>
              <div className="bar calm">
                <i style={{ width: '88%' }}></i>
              </div>
              <div className="meter-num">held</div>
            </div>
            
            <div className="meter">
              <div>
                <div className="meter-label">Jerk</div>
                <div className="meter-sub">imu.jerk</div>
              </div>
              <div className="bar warn">
                <i style={{ width: '22%' }}></i>
              </div>
              <div className="meter-num">0.18 g/s</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}