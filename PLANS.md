# PLANS.md

## Document Role

`PLANS.md` owns the phase-level plan, exit criteria, and planning questions.

It does not own:

- live handoff status
- temporary risks
- next action
- stable charter
- accepted decision history

## Planning Objective

Move the repo from design convergence to implementation readiness without creating source-of-truth ambiguity.

The near-term planning target is to converge the new-system baseline enough that the next synthetic dry run validates the current design instead of reopening legacy routing questions by default.

## Current Roadmap Position

The repo is currently in Phase 1: Design Stabilization.

Current planning emphasis:

1. converge the active new-system baseline
2. identify which legacy constraints must be preserved in that baseline
3. prepare the next synthetic dry run against the new baseline

`TASK_STATE.md` remains the source of truth for the immediate next step and active risks.

## Phase Model

### Phase 1: Design Stabilization

Purpose:
Converge the active design baseline and remove source-of-truth ambiguity.

Success criteria:

- the active new-system baseline is coherent enough to validate
- preserved legacy constraints are identified explicitly rather than imported implicitly
- canonical governance docs no longer conflict about ownership or status
- the next synthetic dry-run target is clear

### Phase 2: Synthetic Baseline Validation

Purpose:
Remap the synthetic pack and expected behavior to the new-system baseline, then run a synthetic dry run to expose design, interface, and state-flow problems.

Success criteria:

- synthetic inputs target the new-system baseline rather than the retired legacy baseline
- expected behavior and routing expectations are rewritten for that baseline
- findings are categorized as design bugs, contract gaps, or deferred issues

### Phase 3: Contract Freeze

Purpose:
Turn validated shared data structures and behavior expectations into implementation-facing contracts.

Success criteria:

- core contracts are stable enough for implementation work
- contract authority is explicit and consistent across related specs

### Phase 4: Implementation Foundation

Purpose:
Implement shared schemas, deterministic tools, storage foundations, and test scaffolding.

Success criteria:

- foundation components match frozen contracts
- implementation scaffolding is sufficient for pipeline work

### Phase 5: Pipeline Implementation

Purpose:
Implement processing workflow components against the frozen contracts.

Success criteria:

- the pipeline can run end-to-end on the synthetic baseline
- node behavior matches the frozen contracts closely enough for integration debugging

### Phase 6: Integration and Real-World Validation

Purpose:
Use real-world data to separate ingestion / OCR / parser noise from system-design issues.

Success criteria:

- real-world blockers are categorized cleanly
- the system is ready for product hardening

## Non-Goals For This Document

- do not use this file as a running handoff log
- do not redesign product logic here
- do not store low-level field debates here
- do not turn this file into the current task brief

## Open Planning Questions

- What is the smallest coherent new-system baseline for the next synthetic dry run?
- Which legacy constraints must be preserved in the new baseline?
- How should the synthetic pack and expected behavior be remapped to the new baseline?
- What must be contract-frozen before implementation begins?
- What migration order best prevents source-of-truth conflicts after baseline convergence?
