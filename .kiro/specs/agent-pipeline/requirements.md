# Feature: LangGraph Agent Pipeline

## Status: draft

## Problem Statement
Ed needs a multi-agent pipeline that takes fused sensor observations and produces appropriate interventions. The pipeline must handle different risk levels, use memory for personalization, and apply MAR (Multi-Agent Reflexion) on caregiver notifications.

## User Stories
- As Ed, I want to automatically respond to user distress with the right intervention
- As a caregiver, I want notifications that are clinically appropriate, not alarmist, and privacy-respecting
- As the system, I want to route low-risk observations to logging only, avoiding unnecessary interventions

## Functional Requirements
- REQ-001: The pipeline shall execute: Perception → Risk Assessment → Memory Retrieval → Planner → Executor
- REQ-002: When risk_level is "low", the system shall log the observation and skip intervention
- REQ-003: When risk_level is "medium", the planner shall choose a gentle intervention (LED change, soft speech)
- REQ-004: When risk_level is "high", the planner shall execute a full intervention sequence and notify caregiver
- REQ-005: Before dispatching any caregiver notification, the system shall run MAR with three critics (Clinical Safety, Family Tone, Privacy) and log the debate trace
- REQ-006: The planner shall use Sonnet; perception and risk assessment shall use Haiku
- REQ-007: The executor shall dispatch actions to the ESP32 via WebSocket commands
- REQ-008: When a comfort recipe matches the current state, the planner shall prefer the proven sequence over generating a new plan

## Acceptance Criteria
- [ ] Pipeline executes end-to-end with synthetic sensor input
- [ ] Risk routing correctly separates low/medium/high paths
- [ ] MAR debate trace is logged and visible on dashboard
- [ ] Comfort recipe retrieval influences planner output
- [ ] Actions are dispatched as valid WebSocket commands

## Out of Scope
- Reinforcement learning for orchestrator evolution (use heuristic routing)
- Real-time model switching (fixed Sonnet/Haiku assignment)
