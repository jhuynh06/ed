"use client"

import { useState } from 'react'
import { AlertTriangle, Clock, Info, ChevronDown, ChevronRight } from 'lucide-react'
import type { Notification, CriticVerdict } from '@/lib/sse-types'

interface NotificationFeedProps {
  notifications: Notification[]
}

function getNotificationIcon(priority: string) {
  switch (priority) {
    case 'urgent':
      return <AlertTriangle size={14} />
    case 'warning':
      return <Clock size={14} />
    case 'info':
    default:
      return <Info size={14} />
  }
}

function getNotificationClass(priority: string) {
  switch (priority) {
    case 'urgent':
      return 'notif urgent'
    case 'warning':
      return 'notif warn'
    case 'info':
    default:
      return 'notif calm'
  }
}

function formatTimeAgo(timestamp: number): string {
  const now = Date.now()
  const diff = now - timestamp
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

function MARTrace({ verdicts }: { verdicts: CriticVerdict[] }) {
  return (
    <div className="mt-3 pt-3 border-t border-[var(--line-soft)]">
      <div className="micro mb-2">MAR debate trace</div>
      <div className="space-y-2">
        {verdicts.map((verdict, index) => (
          <div key={index} className="flex items-start gap-3 p-2 bg-[var(--paper-3)] rounded-lg border border-[var(--line-soft)]">
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <span className="font-mono text-[9.5px] text-[var(--ink-3)] uppercase tracking-wider">
                  {verdict.critic}
                </span>
                <span className={`comp-tag ${verdict.verdict === 'APPROVE' ? 'ack' : 'miss'}`}>
                  {verdict.verdict}
                </span>
              </div>
              <div className="font-serif text-[12px] leading-relaxed text-[var(--ink-2)]">
                {verdict.feedback}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function NotificationItem({ notification }: { notification: Notification }) {
  const [expanded, setExpanded] = useState(false)
  const hasMARTrace = notification.mar_trace && notification.mar_trace.length > 0
  
  // Mock timestamp for demo
  const timestamp = Date.now() - Math.random() * 3600000 // Random time in last hour

  return (
    <div className={getNotificationClass(notification.priority)}>
      <div className="notif-head">
        <div className="notif-icon">
          {getNotificationIcon(notification.priority)}
        </div>
        <span className="font-mono text-[10px] tracking-wider uppercase text-[var(--ink-3)]">
          Theodore · live
        </span>
        <span className="notif-priority">
          {notification.priority}
        </span>
        <span className="font-mono text-[10px] text-[var(--ink-3)] tracking-wider ml-auto">
          {formatTimeAgo(timestamp)}
        </span>
      </div>
      
      <div className="notif-body">
        <h3 className="notif-title">
          {notification.priority === 'urgent' && 'Intervention needed'}
          {notification.priority === 'warning' && 'Behavioral alert'}
          {notification.priority === 'info' && 'Daily update'}
        </h3>
        <p className="notif-desc">
          {notification.message}
        </p>
      </div>
      
      <div className="notif-actions">
        {notification.priority === 'urgent' && (
          <>
            <button className="btn btn-primary">Call Theodore</button>
            <button className="btn">Listen in</button>
            <button className="btn btn-ghost">I'm on my way</button>
          </>
        )}
        {notification.priority === 'warning' && (
          <>
            <button className="btn btn-primary">Hear the moment</button>
            <button className="btn">Mark resolved</button>
          </>
        )}
        {notification.priority === 'info' && (
          <button className="btn">View full digest</button>
        )}
        
        {hasMARTrace && (
          <button 
            className="btn btn-ghost"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            MAR trace
          </button>
        )}
      </div>
      
      {expanded && hasMARTrace && (
        <MARTrace verdicts={notification.mar_trace!} />
      )}
    </div>
  )
}

export function NotificationFeed({ notifications }: NotificationFeedProps) {
  // Sort notifications by priority and timestamp
  const sortedNotifications = [...notifications].sort((a, b) => {
    const priorityOrder = { urgent: 3, warning: 2, info: 1 }
    const aPriority = priorityOrder[a.priority as keyof typeof priorityOrder] || 0
    const bPriority = priorityOrder[b.priority as keyof typeof priorityOrder] || 0
    
    if (aPriority !== bPriority) {
      return bPriority - aPriority // Higher priority first
    }
    
    // If same priority, sort by timestamp (mock for now)
    return 0
  })

  return (
    <div className="card p-4 flex flex-col gap-4 min-h-0">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <div className="pip on breathe"></div>
            <span className="micro">Live feed · MAR filtered</span>
          </div>
          <h2 className="font-serif text-[17px] font-normal tracking-tight leading-tight m-0 mt-1">
            Notifications
          </h2>
          <div className="micro mt-1">Real-time alerts · caregiver actions · daily summaries</div>
        </div>
        <span className="micro">{notifications.length} today</span>
      </div>
      
      <div className="flex-1 overflow-y-auto space-y-3 min-h-0">
        {sortedNotifications.length > 0 ? (
          sortedNotifications.map((notification) => (
            <NotificationItem key={notification.id} notification={notification} />
          ))
        ) : (
          <div className="flex items-center justify-center h-32 text-[var(--ink-3)]">
            <div className="text-center">
              <div className="micro mb-1">No notifications</div>
              <div className="font-serif text-[13px]">All systems nominal</div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}