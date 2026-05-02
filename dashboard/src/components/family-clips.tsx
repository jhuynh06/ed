"use client"

import { useState } from 'react'
import { Play, Pause, Upload, Trash2 } from 'lucide-react'

interface FamilyClip {
  id: string
  name: string
  duration_s: number
  uploaded_at: number
}

interface FamilyClipsProps {
  clips: FamilyClip[]
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function formatUploadDate(timestamp: number): string {
  const date = new Date(timestamp * 1000)
  const now = new Date()
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays} days ago`
  
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function ClipItem({ clip }: { clip: FamilyClip }) {
  const [playing, setPlaying] = useState(false)
  const [progress, setProgress] = useState(0)

  const handlePlayPause = () => {
    setPlaying(!playing)
    // In real implementation, this would control actual audio playback
    if (!playing) {
      // Simulate playback progress
      const interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 100) {
            setPlaying(false)
            clearInterval(interval)
            return 0
          }
          return prev + (100 / clip.duration_s) * 0.1 // Update every 100ms
        })
      }, 100)
    }
  }

  return (
    <div className="speak-bubble">
      <div className="flex items-center gap-3">
        <div className="w-7 h-7 rounded-full bg-[var(--sage)] flex items-center justify-center text-[var(--paper)] font-serif text-[13px]">
          {clip.name.charAt(0)}
        </div>
        <div className="flex-1">
          <div className="font-mono text-[10px] uppercase tracking-wider text-[var(--ink-3)]">
            {clip.name}
          </div>
          <div className="font-serif text-[17px] leading-tight text-[var(--ink)] mt-1">
            "Hey grandpa, it's me..."
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button 
            className="btn btn-icon"
            onClick={handlePlayPause}
            aria-label={playing ? 'Pause' : 'Play'}
          >
            {playing ? <Pause size={14} /> : <Play size={14} />}
          </button>
          <button 
            className="btn btn-icon btn-ghost"
            aria-label="Delete clip"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>
      
      {/* Waveform visualization */}
      <div className="flex items-center gap-1 h-5 pt-1">
        {Array.from({ length: 24 }, (_, i) => (
          <div 
            key={i}
            className="w-0.5 bg-[var(--ink-3)] rounded-full opacity-55"
            style={{ 
              height: `${Math.random() * 12 + 4}px`,
              opacity: playing && (i / 24) * 100 <= progress ? 0.9 : 0.3
            }}
          />
        ))}
      </div>
      
      <div className="flex items-center justify-between pt-2 border-t border-dashed border-[var(--line)]">
        <div className="font-mono text-[9.5px] uppercase tracking-wider text-[var(--ink-3)]">
          {formatDuration(clip.duration_s)} · {formatUploadDate(clip.uploaded_at)}
        </div>
        <div className="font-mono text-[9.5px] text-[var(--ink-3)]">
          Used 3 times this week
        </div>
      </div>
    </div>
  )
}

export function FamilyClips({ clips }: FamilyClipsProps) {
  const [uploading, setUploading] = useState(false)

  const handleUpload = () => {
    setUploading(true)
    // Simulate upload process
    setTimeout(() => {
      setUploading(false)
      // In real implementation, this would trigger a file picker and upload
    }, 2000)
  }

  return (
    <div className="card p-4 flex flex-col gap-4 min-h-0">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <div className="pip on"></div>
            <span className="micro">Family voice library · Chroma stored</span>
          </div>
          <h2 className="font-serif text-[17px] font-normal tracking-tight leading-tight m-0 mt-1">
            Family clips
          </h2>
          <div className="micro mt-1">Comfort voices · 15s max · triggered by agitation</div>
        </div>
        <button 
          className="btn btn-primary"
          onClick={handleUpload}
          disabled={uploading}
        >
          <Upload size={14} />
          {uploading ? 'Uploading...' : 'Upload'}
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto space-y-3 min-h-0">
        {clips.length > 0 ? (
          clips.map((clip) => (
            <ClipItem key={clip.id} clip={clip} />
          ))
        ) : (
          <div className="flex items-center justify-center h-32 text-[var(--ink-3)]">
            <div className="text-center">
              <div className="micro mb-1">No clips uploaded</div>
              <div className="font-serif text-[13px]">Upload family voices for comfort</div>
            </div>
          </div>
        )}
      </div>
      
      {clips.length > 0 && (
        <div className="pt-2 border-t border-[var(--line-soft)]">
          <div className="micro">
            {clips.length} clips · Total {clips.reduce((sum, clip) => sum + clip.duration_s, 0)}s
          </div>
        </div>
      )}
    </div>
  )
}