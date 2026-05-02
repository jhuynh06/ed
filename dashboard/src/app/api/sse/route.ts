import { NextRequest } from 'next/server'

export const dynamic = 'force-dynamic'

export async function GET(request: NextRequest) {
  const encoder = new TextEncoder()

  let agitationInterval: ReturnType<typeof setInterval> | null = null
  let vitalsInterval: ReturnType<typeof setInterval> | null = null
  let notificationInterval: ReturnType<typeof setInterval> | null = null
  let closed = false

  function cleanup() {
    closed = true
    if (agitationInterval) clearInterval(agitationInterval)
    if (vitalsInterval) clearInterval(vitalsInterval)
    if (notificationInterval) clearInterval(notificationInterval)
  }

  // Abort when client disconnects
  request.signal.addEventListener('abort', cleanup)

  const stream = new ReadableStream({
    start(controller) {
      function safeSend(data: string) {
        if (closed) return
        try {
          controller.enqueue(encoder.encode(`data: ${data}\n\n`))
        } catch {
          cleanup()
        }
      }

      // Initial event
      safeSend(JSON.stringify({
        type: "agitation_update",
        timestamp: Date.now() / 1000,
        score: 26,
        risk: "low"
      }))

      // Agitation updates every 3s
      agitationInterval = setInterval(() => {
        const score = 20 + Math.random() * 60
        const risk = score < 30 ? "low" : score < 60 ? "medium" : "high"
        safeSend(JSON.stringify({
          type: "agitation_update",
          timestamp: Date.now() / 1000,
          score: Math.round(score),
          risk
        }))
      }, 3000)

      // Vitals every 10s
      vitalsInterval = setInterval(() => {
        const baselineBpm = 72
        const bpm = Math.round(baselineBpm + (Math.random() - 0.5) * 20)
        const spo2 = Math.round(95 + Math.random() * 4)
        safeSend(JSON.stringify({
          type: "vitals_update",
          bpm,
          spo2,
          baseline_bpm: baselineBpm
        }))
      }, 10000)

      // Occasional notifications
      notificationInterval = setInterval(() => {
        if (Math.random() < 0.3) {
          const messages = [
            "Ed detected elevated agitation - trying music intervention",
            "Wandering language detected - 'I need to go home' - resolved quickly",
            "Heart rate elevated 15% above baseline for 3 minutes",
            "No speech detected for 10 minutes - may have dozed off",
            "Sustained hug detected - 2 minutes and counting"
          ]
          const priorities = ["info", "warning", "urgent"] as const
          const priority = priorities[Math.floor(Math.random() * priorities.length)]

          safeSend(JSON.stringify({
            type: "notification",
            id: `notif_${Date.now()}`,
            message: messages[Math.floor(Math.random() * messages.length)],
            priority,
            mar_trace: priority === "urgent" ? [
              { critic: "Clinical Safety", verdict: "APPROVE", feedback: "Appropriate escalation given sustained elevated agitation" },
              { critic: "Family Tone", verdict: "REVISE", feedback: "Language could be less clinical and more reassuring" },
              { critic: "Privacy", verdict: "APPROVE", feedback: "Shares necessary information without excessive detail" }
            ] : null
          }))
        }
      }, 15000)
    },
    cancel() {
      cleanup()
    }
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      'Connection': 'keep-alive',
    }
  })
}
