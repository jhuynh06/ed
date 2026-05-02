"use client"

import type { AgitationUpdate, EpisodeStart, EpisodeEnd } from '@/lib/sse-types'


interface AgitationTimelineProps {
  agitation: AgitationUpdate | null
  agitationHistory: AgitationUpdate[]
  episodes: Array<{ start: EpisodeStart; end?: EpisodeEnd }>
  connected: boolean
}

export function AgitationTimeline({ agitation, agitationHistory, episodes, connected }: AgitationTimelineProps) {
  const history = agitationHistory

  const getScoreColor = (score: number) => {
    if (score < 30) return 'var(--sage)'
    if (score < 60) return 'var(--amber)'
    return 'var(--rose)'
  }

  // Derive subtitle from latest agitation data
  const subtitle = (() => {
    if (history.length === 0) return 'waiting for data'
    const latest = history[history.length - 1]
    const label = latest.score >= 60 ? 'elevated' : latest.score >= 30 ? 'mild' : 'calm'
    const time = new Date(latest.timestamp * 1000).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    })
    return `${label} at ${time}`
  })()

  // Generate SVG path for sparkline
  const generatePath = () => {
    if (history.length === 0) return ''

    const width = 300
    const height = 60
    const maxScore = 100

    const points = history.map((point, index) => {
      const x = history.length > 1 ? (index / (history.length - 1)) * width : width / 2
      const y = height - (point.score / maxScore) * height
      return `${x},${y}`
    })

    return `M ${points.join(' L ')}`
  }

  // Format time for axis labels
  const formatTime = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    })
  }

  const now = Date.now() / 1000
  const timeLabels = [
    formatTime(now - 3600), // 1 hour ago
    formatTime(now - 1800), // 30 min ago
    formatTime(now)         // now
  ]

  return (
    <div className="card p-4 flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <div className={`pip ${connected ? 'on breathe' : 'off'}`}></div>
            <span className="micro">Last 2 hours · 5-min intervals</span>
          </div>
          <h2 className="font-serif text-[17px] font-normal tracking-tight leading-tight m-0 mt-1">
            Agitation timeline
          </h2>
          <div className="micro mt-1">Real-time sensor fusion · {subtitle}</div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full" style={{ background: 'var(--sage)' }}></div>
            <span className="micro">Calm</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full" style={{ background: 'var(--amber)' }}></div>
            <span className="micro">Elevated</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full" style={{ background: 'var(--rose)' }}></div>
            <span className="micro">High</span>
          </div>
        </div>
      </div>

      {/* Sparkline */}
      <div className="relative">
        <svg
          viewBox="0 0 300 60"
          className="w-full h-16"
          preserveAspectRatio="none"
          aria-label="Agitation timeline chart"
        >
          {/* Background grid */}
          <defs>
            <pattern id="grid" width="30" height="20" patternUnits="userSpaceOnUse">
              <path d="M 30 0 L 0 0 0 20" fill="none" stroke="var(--line-soft)" strokeWidth="0.5" opacity="0.5"/>
            </pattern>
          </defs>
          <rect width="300" height="60" fill="url(#grid)" />

          {/* Threshold lines */}
          <line x1="0" y1="42" x2="300" y2="42" stroke="var(--sage)" strokeWidth="1" strokeDasharray="2 3" opacity="0.6" />
          <line x1="0" y1="24" x2="300" y2="24" stroke="var(--amber)" strokeWidth="1" strokeDasharray="2 3" opacity="0.6" />

          {/* Episode markers */}
          {episodes.map((episode) => {
            const episodeTime = episode.start.timestamp
            const relativeTime = (episodeTime - (now - 7200)) / 7200 // 2 hours
            const x = relativeTime * 300

            if (x >= 0 && x <= 300) {
              return (
                <line
                  key={episode.start.id}
                  x1={x}
                  y1="0"
                  x2={x}
                  y2="60"
                  stroke="var(--rose)"
                  strokeWidth="2"
                  opacity="0.7"
                />
              )
            }
            return null
          })}

          {/* Main sparkline */}
          <path
            d={generatePath()}
            fill="none"
            stroke="var(--ink)"
            strokeWidth="2"
            strokeLinejoin="round"
          />

          {/* Data points */}
          {history.map((point, index) => {
            const x = history.length > 1 ? (index / (history.length - 1)) * 300 : 150
            const y = 60 - (point.score / 100) * 60
            return (
              <circle
                key={index}
                cx={x}
                cy={y}
                r="2.5"
                fill={getScoreColor(point.score)}
                stroke="white"
                strokeWidth="1"
              />
            )
          })}

          {/* Current value indicator */}
          {agitation && (
            <circle
              cx="300"
              cy={60 - (agitation.score / 100) * 60}
              r="4"
              fill={getScoreColor(agitation.score)}
              stroke="white"
              strokeWidth="2"
              className={connected ? 'breathe' : ''}
            />
          )}
        </svg>

        {/* Time axis */}
        <div className="flex justify-between mt-2 px-1">
          {timeLabels.map((label, index) => (
            <span key={index} className="font-mono text-[9px] text-[var(--ink-3)] tracking-wider">
              {label}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
