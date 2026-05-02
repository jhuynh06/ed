# Tasks: Synthetic Evaluation Harness

## Implementation Order

### Phase 1: Data Models
- [ ] Define `SyntheticProfile`, `SensorFrame`, `SyntheticScenario`, `EvalResult` | `backend/app/models/eval.py`
- [ ] Define evaluator score schema: `EvalScores(appropriateness, timeliness, personalization, reasoning)` | `backend/app/models/eval.py`

### Phase 2: Scenario Generation
- [ ] Create scenario generator prompt — Claude generates profile + sensor stream from description | `backend/app/eval/generator.py`
- [ ] Generate 5 pre-built scenarios and save as JSON files | `backend/eval/scenarios/`
- [ ] Validate all scenarios produce valid sensor_data matching ESP32 format | `backend/app/eval/generator.py`

### Phase 3: Scenario Runner
- [ ] Implement `run_scenario()` — replay sensor frames through pipeline with mock executor | `backend/app/eval/runner.py`
- [ ] Mock executor captures actions instead of dispatching to ESP32 | `backend/app/eval/runner.py`
- [ ] Support pre-transcribed speech and pre-extracted emotion (skip ML APIs) | `backend/app/eval/runner.py`
- [ ] Collect intervention log with timestamps and actions | `backend/app/eval/runner.py`

### Phase 4: Evaluator
- [ ] Implement evaluator agent — Sonnet scores intervention on 3 dimensions | `backend/app/eval/evaluator.py`
- [ ] Parse JSON scores with Pydantic validation | `backend/app/eval/evaluator.py`
- [ ] `run_eval_suite()` — run all scenarios, collect results, compute averages | `backend/app/eval/suite.py`

### Phase 5: Reporting
- [ ] Generate results summary table (scenario × dimension scores) | `backend/app/eval/report.py`
- [ ] [P] Add `/api/eval/run` endpoint to trigger eval suite from dashboard | `backend/app/main.py`
- [ ] [P] Add eval results display component on dashboard | `dashboard/src/app/eval/page.tsx`

## Verification
- [ ] All 5 scenarios load and parse without errors
- [ ] Calm baseline scenario → low risk, no intervention, high appropriateness score
- [ ] Fall scenario → immediate high risk, urgent notification, high timeliness score
- [ ] Evaluator scores are consistent across 3 repeated runs (±1 point per dimension)
- [ ] Results table renders correctly on dashboard
