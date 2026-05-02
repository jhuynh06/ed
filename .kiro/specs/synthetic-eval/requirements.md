# Feature: Synthetic Evaluation Harness

## Status: draft

## Problem Statement
No real elderly users at the hackathon. We need Claude to generate synthetic user scenarios (agitation patterns, life histories, family contexts), run Ed's pipeline on them, and score intervention quality. This doubles as our testing framework and a demo talking point ("self-evaluating system").

## User Stories
- As a developer, I want to test Ed's pipeline without real hardware so that I can iterate quickly
- As a demo presenter, I want to show that Ed evaluates its own intervention quality

## Functional Requirements
- REQ-001: The system shall generate synthetic user profiles with: name, age, dementia stage, family members, known triggers, preferred music, baseline vitals
- REQ-002: The system shall generate synthetic sensor scenarios: calm baseline, gradual agitation, sudden fall, sundowning episode, verbal distress
- REQ-003: Each scenario shall produce a stream of synthetic sensor_data messages matching the ESP32 WebSocket format
- REQ-004: After Ed responds to a scenario, an evaluator agent shall score the intervention on: appropriateness (0–10), timeliness (0–10), personalization (0–10)
- REQ-005: Evaluation results shall be logged and displayable as a summary table

## Acceptance Criteria
- [ ] At least 5 distinct synthetic scenarios are generated
- [ ] Scenarios produce valid sensor_data JSON streams
- [ ] Pipeline processes synthetic data identically to real data
- [ ] Evaluator scores are consistent across repeated runs (±1 point)

## Out of Scope
- Self-Challenging Agent full loop (no retraining, just evaluation)
- Automated scenario generation during demo (pre-generate scenarios)
