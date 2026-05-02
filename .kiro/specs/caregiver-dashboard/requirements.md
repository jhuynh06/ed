# Feature: Caregiver Dashboard

## Status: draft

## Problem Statement
Family caregivers and clinicians need a real-time view of Theodore's observations, interventions, and discovered patterns. The dashboard must surface actionable insights without requiring technical knowledge.

## User Stories
- As a family caregiver, I want to see a live agitation timeline so that I know how my parent is doing right now
- As a family caregiver, I want to receive notifications with appropriate urgency so that I'm not overwhelmed
- As a clinician, I want to see circadian patterns and daily summaries so that I can adjust care plans between visits
- As a family member, I want to upload voice clips so that Theodore can play them during distress

## Functional Requirements
- REQ-001: The dashboard shall display a live agitation timeline (last 6 hours, 1-minute resolution, color-coded)
- REQ-002: The dashboard shall show real-time notifications via SSE with toast + persistent list
- REQ-003: The dashboard shall display HR trends (last 24 hours, 5-minute averages with baseline overlay)
- REQ-004: The dashboard shall show an event log with episode cards (timestamp, duration, peak agitation, intervention, outcome)
- REQ-005: The dashboard shall display a Claude-generated daily caregiver summary
- REQ-006: The dashboard shall provide a family voice clip upload and management interface
- REQ-007: The dashboard shall show MAR debate traces for caregiver notifications (expandable detail)
- REQ-008: The dashboard shall support PDF export of daily/weekly summaries for clinician visits

## Acceptance Criteria
- [ ] SSE connection establishes and receives live updates
- [ ] Agitation timeline renders with correct color coding
- [ ] Notification toasts appear within 1 second of backend event
- [ ] Episode cards display all required fields
- [ ] Voice clip upload stores to backend and is playable
- [ ] Daily summary renders markdown correctly

## Out of Scope
- User authentication beyond basic auth
- Mobile-responsive layout (desktop-first for demo)
- Multi-user/multi-bear views
