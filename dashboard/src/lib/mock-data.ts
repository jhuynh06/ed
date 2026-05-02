import type { AgitationUpdate, EpisodeStart, EpisodeEnd, Notification, VitalsUpdate, CriticVerdict } from './sse-types'

export const mockAgitation: AgitationUpdate = {
  type: "agitation_update",
  timestamp: Date.now() / 1000,
  score: 34,
  risk: "medium"
}

export const mockEpisodes: Array<{ start: EpisodeStart; end?: EpisodeEnd }> = [
  {
    start: {
      type: "episode_start",
      id: "ep_001",
      timestamp: Date.now() / 1000 - 3600,
      agitation: 65
    },
    end: {
      type: "episode_end",
      id: "ep_001",
      duration: 420,
      peak: 78,
      outcome: "calm_restored"
    }
  },
  {
    start: {
      type: "episode_start",
      id: "ep_002",
      timestamp: Date.now() / 1000 - 7200,
      agitation: 45
    },
    end: {
      type: "episode_end",
      id: "ep_002",
      duration: 180,
      peak: 52,
      outcome: "no_change"
    }
  },
  {
    start: {
      type: "episode_start",
      id: "ep_003",
      timestamp: Date.now() / 1000 - 10800,
      agitation: 72
    },
    end: {
      type: "episode_end",
      id: "ep_003",
      duration: 840,
      peak: 85,
      outcome: "escalated"
    }
  }
]

export const mockCriticVerdicts: CriticVerdict[] = [
  {
    critic: "Clinical Safety",
    verdict: "APPROVE",
    feedback: "Appropriate escalation given sustained elevated agitation above baseline"
  },
  {
    critic: "Family Tone",
    verdict: "REVISE",
    feedback: "Language could be less clinical and more reassuring for family member"
  },
  {
    critic: "Privacy",
    verdict: "APPROVE",
    feedback: "Shares necessary information without excessive detail"
  }
]

export const mockNotifications: Notification[] = [
  {
    type: "notification",
    id: "notif_001",
    message: "Agitation didn't settle after intervention - spike began 9:34a, Theodore tried music and breathing but jerk magnitude still elevated after 7 minutes",
    priority: "urgent",
    mar_trace: mockCriticVerdicts
  },
  {
    type: "notification",
    id: "notif_002",
    message: "Wandering language detected - 'I need to go home' said 3 times, resolved within 40s with gentle reorientation",
    priority: "warning",
    mar_trace: null
  },
  {
    type: "notification",
    id: "notif_003",
    message: "Daily summary ready - 4h 18m conversation, one disorientation moment, longest hug of the week",
    priority: "info",
    mar_trace: null
  }
]

export const mockVitals: VitalsUpdate = {
  type: "vitals_update",
  bpm: 78,
  spo2: 97,
  baseline_bpm: 72
}

export const mockDailyDigest = {
  summary_markdown: "A warmer day — longest hug of the week, one disorientation moment at 8:31.",
  mood_arc: "calm morning, restless afternoon, calm evening",
  episode_count: 2,
  sundowning_detected: true,
  trend_direction: "stable" as const,
  cdr_total: 2.0,
  action_items: [
    "Consider earlier bedtime routine",
    "Sundowning pattern emerging at 5pm - monitor closely"
  ]
}

export const mockFamilyClips = [
  {
    id: "clip_001",
    name: "Grandson Michael",
    duration_s: 12,
    uploaded_at: Date.now() / 1000 - 86400
  },
  {
    id: "clip_002", 
    name: "Daughter Sarah",
    duration_s: 8,
    uploaded_at: Date.now() / 1000 - 172800
  },
  {
    id: "clip_003",
    name: "Son David",
    duration_s: 15,
    uploaded_at: Date.now() / 1000 - 259200
  }
]

export const mockHRHistory = Array.from({ length: 20 }, (_, i) => ({
  timestamp: Date.now() / 1000 - (19 - i) * 300, // 5-minute intervals
  bpm: 72 + Math.sin(i * 0.3) * 8 + Math.random() * 4
}))

export const mockAgitationHistory = Array.from({ length: 20 }, (_, i) => ({
  timestamp: Date.now() / 1000 - (19 - i) * 300,
  score: 25 + Math.sin(i * 0.2) * 15 + Math.random() * 10
}))