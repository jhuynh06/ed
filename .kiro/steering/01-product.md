---
title: Ed — Product Context
inclusion: always
---

# Ed — Emotionally Intelligent Companion Bear

## What It Is
An emotionally intelligent teddy bear for elderly users with mild-to-moderate dementia. Ed detects distress through audio, motion, heart rate, and touch, then responds with calming voice, haptic breathing, and visual indicators. A connected dashboard surfaces patterns for family caregivers and clinicians.

## Target Users
- **Primary**: Elderly individuals with mild-to-moderate dementia, anxiety, or loneliness
- **Secondary buyer**: Adult children (45–60) managing aging parents remotely
- **Tertiary**: Clinicians needing behavioral data between visits

## Core Value Proposition
Ambient emotional sensing without the surveillance feel of a camera or wearable. The plush form factor is the trojan horse for behavioral data collection that would otherwise be rejected.

## Key Design Constraints
- No camera — privacy is core to the value prop
- No cloud-only dependency for the core sensing loop
- All caregiver notifications must be auditable via the event log
- Voice responses must feel warm — TTS quality is non-negotiable
- Must work on phone hotspot WiFi (venue-resilient)

## Domain Terms
- **Sundowning**: Late-afternoon agitation common in dementia patients
- **Comfort recipe**: A stored sequence of interventions proven effective for a specific user
- **Agitation score**: Fused metric from IMU jerk, HR elevation, vocal emotion, and touch absence
- **Episode**: A detected period of elevated distress with start/end timestamps
- **Consolidation**: Nightly process that abstracts episodic memories into semantic patterns

## Out of Scope (v1)
- Mobile app (web dashboard only)
- Multi-bear / multi-user accounts
- Custom-trained ML models (use APIs + heuristics)
- LiPo battery + charging circuit (USB power bank only)
- HIPAA compliance (demo, not deployed product)
