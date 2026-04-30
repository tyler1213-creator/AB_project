# PLANS.md

## Document Role

`PLANS.md` owns the project phase model and high-level planning questions.

It does not own current execution state, handoff detail, accepted design tradeoffs, agent entry rules, stable project charter, or system design content. Those responsibilities belong to:

- `TASK_STATE.md` — current execution state, active risks, and next step
- `DECISIONS.md` — important accepted tradeoffs
- `AGENTS.md` — agent entry rules and current reading order
- `CLAUDE.md` — stable project charter
- `new system/new_system.md` — current active system design baseline

## Planning Objective

Move the repo from design convergence to implementation readiness without creating source-of-truth ambiguity.

The near-term planning goal is to stabilize the new-system baseline enough that synthetic validation can test the current design instead of reopening legacy routing questions by default.

## Non-Goals

- Do not redesign product logic in this planning document.
- Do not use this file as a handoff log.
- Do not add low-level field design questions here.
- Do not add implementation task briefs before contracts are frozen.
- Do not treat OCR/parser quality or real-world ingestion noise as the next design-validation target.

## Phase Model

### Phase 1: Design Stabilization

Purpose:  
Converge the active design baseline and remove source-of-truth ambiguity.

Exit gate:  
The current active baseline is coherent enough for synthetic validation.

Before this phase exits, the repo should make clear:

- which legacy constraints must be preserved in the new baseline
- what the synthetic pack remap target is
- how expected behavior and routing expectations should be rewritten for the new baseline
- that no unresolved source-of-truth conflict remains among canonical docs

### Phase 2: Synthetic Baseline Validation

Purpose:  
Remap the synthetic pack and expected behavior to the new-system baseline, then run a synthetic dry run to expose design, interface, and state-flow problems.

Exit gate:  
Synthetic findings are concrete and categorized as design bugs, contract gaps, or deferred issues.

### Phase 3: Contract Freeze

Purpose:  
Turn validated shared data structures and behavior expectations into implementation-facing contracts.

Exit gate:  
Core contracts are stable enough that implementation agents can work without inventing fields or behavior.

### Phase 4: Implementation Foundation

Purpose:  
Implement shared schemas, deterministic tools, storage foundations, and test scaffolding.

Exit gate:  
Foundation components pass tests and match frozen contracts.

### Phase 5: Pipeline Implementation

Purpose:  
Implement processing workflow components against the frozen contracts.

Exit gate:  
Pipeline can run end-to-end on synthetic baseline cases.

### Phase 6: Integration and Real-World Validation

Purpose:  
Use real-world data to separate ingestion, OCR, and parser noise from system design issues.

Exit gate:  
Real-world blockers are categorized and the system is ready for product hardening.

## Current Roadmap Position

The repo is currently in Phase 1: Design Stabilization, specifically new-system baseline convergence.

A synthetic dry run has already been executed against the legacy pattern-first baseline. The next meaningful synthetic dry run should target the new-system baseline after the baseline is coherent enough to validate.

`TASK_STATE.md` remains the source of truth for the current objective, current risks, and immediate next step.

## Open Planning Questions

- What is the smallest coherent new-system baseline for the next synthetic dry run?
- Which legacy constraints must be preserved in the new baseline?
- How should the synthetic pack and expected behavior be remapped to the new baseline?
- What needs to be contract-frozen before implementation can begin?
- What rewrite or migration order best prevents source-of-truth conflicts after the new baseline stabilizes?
