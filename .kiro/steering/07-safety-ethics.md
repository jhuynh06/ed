---
title: Ed — Safety & Ethics
inclusion: always
---

# Safety & Ethics

## Clinical Safety Rules
- Ed is NOT a medical device. Never claim diagnostic capability.
- All interventions are comfort-oriented, never medical advice.
- Fall detection triggers caregiver notification immediately — no delay for "assessment."
- Never suppress or delay a caregiver notification to "avoid bothering them."

## Multi-Agent Reflexion on Notifications (MAR pattern)
Before sending any caregiver notification, run through three persona critics:
1. **Clinical Safety Critic**: Is this medically appropriate? Could delay cause harm?
2. **Family Tone Critic**: Will this scare the family member unnecessarily? Is the language warm but clear?
3. **Privacy Critic**: Does this notification leak more information than necessary?

The planner synthesizes critic feedback before dispatching. Log the debate trace for dashboard display.

### MAR Implementation Pattern

```python
async def run_mar_gate(notification: str, context: str) -> MARResult:
    critics = [
        ("Clinical Safety", "Is this medically appropriate? Could delay cause harm? Could it cause unnecessary medical anxiety?"),
        ("Family Tone", "Will this scare the family member unnecessarily? Is the language warm but clear?"),
        ("Privacy", "Does this share more information than necessary? Could it be more concise?"),
    ]

    # Run all 3 critics in parallel
    tasks = [
        call_critic(name, prompt, notification, context)
        for name, prompt in critics
    ]
    verdicts = await asyncio.gather(*tasks)

    # If any says REVISE, rewrite (max 2 rounds)
    for round in range(2):
        revisions = [v for v in verdicts if v.verdict == "REVISE"]
        if not revisions:
            break
        feedback = "\n".join(f"[{v.critic}]: {v.feedback}" for v in revisions)
        notification = await rewrite_notification(notification, feedback)
        verdicts = await asyncio.gather(*[
            call_critic(name, prompt, notification, context)
            for name, prompt in critics
        ])

    return MARResult(
        final_notification=notification,
        approved=all(v.verdict == "APPROVE" for v in verdicts),
        debate_trace=[v.model_dump() for v in verdicts],
        rounds=round + 1,
    )
```

## Voice Interaction Safety
- Never impersonate a real person (family voice clips are clearly labeled as recordings)
- Never make promises about health outcomes
- If user expresses suicidal ideation or self-harm, immediately notify caregiver
- Keep voice responses short (< 15 seconds) — long monologues increase confusion
- Use simple, warm language. No jargon. No conditional clauses.

## Data Privacy
- Audio is processed for transcription/emotion, then the raw audio is discarded
- Only transcriptions and extracted features are stored, not raw sensor streams
- Family voice clips are stored locally in Chroma, not sent to external APIs
- Dashboard access should be authenticated (basic auth acceptable for demo)
- Event log is the single source of truth — all actions are auditable

## Ethical Framing for Demo
- Present as "assistive companion" not "surveillance device"
- Emphasize user agency — the bear responds to the user, doesn't control them
- Acknowledge limitations honestly in the demo narrative
