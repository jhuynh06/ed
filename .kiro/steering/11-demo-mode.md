---
title: Theodore — Demo Mode
inclusion: manual
---

# Demo Mode — 3-Minute Hackathon Presentation

When the user says "start demo" or "demo mode", Theodore enters a scripted demonstration sequence. This steering doc defines the exact timing, actions, and talking points.

## Pre-Demo Checklist
- [ ] Backend running (`uv run uvicorn app.main:app`)
- [ ] Dashboard open in browser (http://localhost:3000)
- [ ] Chroma running (`chroma run`)
- [ ] ESP32 connected (or synthetic scenario runner ready)
- [ ] Pre-loaded: Margaret's profile, 3 prior episodes, 1 comfort recipe, grandson voice clip

## Demo Sequence (3 minutes)

### Act 1: Distress Detection (0:00–1:00)
**Narrative**: "Meet Margaret. She's 78, lives alone, has mild dementia. It's 4:30pm — sundowning hour. Theodore already knows this."

**What happens**:
1. Dashboard shows sundowning indicator: "⚠ Approaching sundowning window — peak hour 16:00, 85% confidence"
2. Synthetic scenario starts: gradual agitation ramp
   - IMU: increasing restlessness (jerk rising from 0.1 → 0.8)
   - Touch: gripping Theodore's paw tightly
   - Audio: soft whimpering detected by VAD, vocal arousal rising
3. Dashboard shows: agitation timeline climbing from green → yellow → orange (risk multiplier 1.5× applied)
4. IoT-LLM translation visible: "Margaret is becoming increasingly restless. She's gripping Theodore tightly and making distressed sounds. Vocal analysis detects rising anxiety."
5. Risk assessment triggers: **medium → high**

**Talking point**: "Theodore doesn't just react — it anticipates. It learned Margaret's sundowning pattern from prior sessions and pre-emptively raised its sensitivity at 3pm. By 4:30 it was already watching."

### Act 2: Intelligent Response + Dashboard (1:00–2:00)
**Narrative**: "Now watch Theodore respond — and watch the dashboard capture everything."

**What happens**:
1. Memory retrieval finds: "Margaret responds well to grandson's voice at 4pm" (confidence: 0.85)
2. Comfort recipe matched: `play_grandson_voice → pause → breathing_pacer → reassurance`
3. Planner uses the proven recipe instead of generating from scratch
4. Bear actions fire in sequence:
   - LED shifts to warm amber pulse
   - Grandson's voice plays: "I love you grandma, everything's okay"
   - 30-second pause
   - Haptic breathing pacer starts (6 bpm)
   - Theodore speaks: "I'm right here with you, Margaret. Let's breathe together."
5. Dashboard shows:
   - Episode card appearing in real-time
   - Agitation timeline starting to decline (orange → yellow → green)
   - Notification prepared for caregiver

**Talking point**: "Theodore remembered what worked last time. That comfort recipe was learned from 3 prior episodes — not hardcoded."

### Act 3: MAR + Emotional Moment (2:00–3:00)
**Narrative**: "Before any notification reaches Margaret's daughter, it goes through three AI critics."

**What happens**:
1. Show MAR debate trace on dashboard (expand the notification card):
   - Clinical Safety: "APPROVE — appropriate comfort intervention, no medical concern"
   - Family Tone: "REVISE — 'agitation episode' sounds clinical, suggest 'Margaret had a restless moment'"
   - Privacy: "APPROVE — no unnecessary detail shared"
2. Show the revised notification: "Margaret had a restless moment this afternoon. Theodore played Jake's voice message and guided breathing, and she calmed down within a few minutes. No action needed."
3. Show daily summary: Claude-generated paragraph with circadian pattern ("3rd episode this week between 4-5pm, consistent with sundowning pattern")
   - Mood arc: "calm morning, agitated late afternoon, calm evening"
   - Action items: "Consider earlier dinner time", "Play familiar music at 3pm tomorrow"
   - CDR trend: stable, vocabulary diversity holding

**Emotional close**: Play the grandson's voice clip one more time. Let it land.

**Talking point**: "Every notification is reviewed by three AI critics before it reaches a family member. Because the worst thing a care tool can do is make a daughter panic at 4am. And every evening, the caregiver gets a digest — not a data dump, but a story about their loved one's day."

## Synthetic Scenario for Demo

If no ESP32 hardware is available, use the pre-built scenario:
```python
# backend/eval/scenarios/demo_sundowning.json
# Duration: 180 seconds
# Profile: Margaret, 78, mild dementia
# Pattern: gradual agitation ramp with successful comfort recipe intervention
```

## Dashboard State for Demo
Pre-seed the database with:
- 3 prior episodes (2 at ~4pm, 1 at ~5pm) showing sundowning pattern
- 1 comfort recipe with 75% success rate
- Margaret's profile with grandson Jake's voice clip
- 2 prior daily summaries showing the pattern emerging
