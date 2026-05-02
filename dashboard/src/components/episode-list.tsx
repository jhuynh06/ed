"use client"

import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import type { EpisodeStart, EpisodeEnd, CriticVerdict } from '@/lib/sse-types'

interface Episode {
  start: EpisodeStart
  end?: EpisodeEnd
}

interface EpisodeListProps {
  episodes: Episode[]
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}m ${secs}s`
}

function formatTime(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit',
    hour12: false 
  })
}

function getOutcomeChip(outcome: string) {
  switch (outcome) {
    case 'calm_restored':
      return <span className="chip calm">Resolved</span>
    case 'escalated':
      return <span className="chip alert">Escalated</span>
    case 'no_change':
      return <span className="chip warm">Ongoing</span>
    default:
      return <span className="chip">Unknown</span>
  }
}

function MARTrace({ verdicts }: { verdicts: CriticVerdict[] }) {
  return (
    <div className="mt-3 pt-3 border-t border-[var(--line-soft)]">
      <div className="micro mb-2">MAR debate trace</div>
      <div className="space-y-2">
        {verdicts.map((verdict, index) => (
          <div key={index} className="flag-row">
            <div className="font-mono text-[10px] text-[var(--ink-3)] uppercase tracking-wider">
              {verdict.critic}
            </div>
            <div>
              <div className="font-serif text-[14px] leading-tight">
                {verdict.feedback}
              </div>
            </div>
            <div>
              <span className={`comp-tag ${verdict.verdict === 'APPROVE' ? 'ack' : 'miss'}`}>
                {verdict.verdict}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function EpisodeItem({ episode }: { episode: Episode }) {
  const [expanded, setExpanded] = useState(false)
  const { start, end } = episode
  
  // Mock MAR trace for demonstration
  const mockMARTrace: CriticVerdict[] = [
    {
      critic: "Clinical Safety",
      verdict: "APPROVE",
      feedback: "Appropriate escalation given sustained elevated agitation"
    },
    {
      critic: "Family Tone", 
      verdict: "REVISE",
      feedback: "Language could be less clinical and more reassuring"
    },
    {
      critic: "Privacy",
      verdict: "APPROVE", 
      feedback: "Shares necessary information without excessive detail"
    }
  ]
  
  const hasMARTrace = start.agitation > 60 // Show MAR trace for high agitation episodes

  return (
    <div className="card p-3">
      <div 
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            {hasMARTrace ? (
              expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />
            ) : (
              <div className="w-[14px]" />
            )}
            <span className="font-mono text-[10.5px] text-[var(--ink-2)] tracking-wider">
              {formatTime(start.timestamp)}
            </span>
          </div>
          
          <div className="flex-1">
            <div className="font-serif text-[13.5px] leading-tight">
              {end ? (
                <>Episode · {formatDuration(end.duration)} · peak {Math.round(end.peak)}</>
              ) : (
                <>Ongoing episode · started at {Math.round(start.agitation)}</>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {end && getOutcomeChip(end.outcome)}
          <div className="font-mono text-[10.5px] text-[var(--ink-3)] tabular-nums">
            {Math.round(start.agitation)}→{end ? Math.round(end.peak) : '...'}
          </div>
        </div>
      </div>
      
      {expanded && hasMARTrace && (
        <MARTrace verdicts={mockMARTrace} />
      )}
    </div>
  )
}

export function EpisodeList({ episodes }: EpisodeListProps) {
  // Sort episodes by timestamp, most recent first
  const sortedEpisodes = [...episodes].sort((a, b) => b.start.timestamp - a.start.timestamp)
  
  return (
    <div className="card p-4 flex flex-col gap-4 min-h-0">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <div className="pip idle"></div>
            <span className="micro">Last 24 hours · with MAR traces</span>
          </div>
          <h2 className="font-serif text-[17px] font-normal tracking-tight leading-tight m-0 mt-1">
            Episodes
          </h2>
          <div className="micro mt-1">Agitation events · start/end pairs · click to expand</div>
        </div>
        <span className="micro">{episodes.length} total</span>
      </div>
      
      <div className="flex-1 overflow-y-auto space-y-2 min-h-0">
        {sortedEpisodes.length > 0 ? (
          sortedEpisodes.map((episode) => (
            <EpisodeItem key={episode.start.id} episode={episode} />
          ))
        ) : (
          <div className="flex items-center justify-center h-32 text-[var(--ink-3)]">
            <div className="text-center">
              <div className="micro mb-1">No episodes today</div>
              <div className="font-serif text-[13px]">All quiet on the western front</div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}