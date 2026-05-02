# TASK_STATE.md

## Document Role

`TASK_STATE.md` records the live handoff only:

- current status
- active objective
- next step
- active risks

It does not own phase policy, stable charter, or historical decision rationale.

## Current Status

Current phase position:

- Phase 1: Design Stabilization
- Current workstream: new-system baseline convergence

Current governance baseline:

- Governance docs define clearer boundaries between agent operating rules, live handoff, phase planning, stable charter, workflow method, and communication preferences.
- This governance cleanup did not change product design contracts or business-spec substance.
- `new system/mvp_core_brief.md` now defines the MVP scope, validation intent, and core-loop boundary for MVP-path design work.

Implementation has not started.

## Active Objective

Converge the evidence-first redesign into the repo's next working baseline under the MVP core loop defined in `new system/mvp_core_brief.md`, then prepare the next synthetic dry run against that new baseline.

## Active Baseline

- `new system/new_system.md` is the only active new-system design source.
- `new system/mvp_core_brief.md` owns MVP scope, validation intent, and core-loop boundary; it does not own node schemas or implementation contracts.
- `new system/different_node.md` and `new system/memory_node_design.md` are historical drafts and should not continue to be updated.
- Legacy node specs are reusable constraints / reference material, not the default baseline.

## Immediate Next Step

Use `new system/mvp_core_brief.md` to gate the next baseline-convergence discussion: first confirm the minimal functional logic required for the MVP loop, then derive the necessary minimal executable contracts before synthetic dry run or implementation.

## Active Risks

- case-memory authority is not fully settled
- runtime evidence-pack handoff is not fully settled
- rule promotion / governance boundaries are not fully settled
- synthetic pack and expected behavior have not yet been remapped to the new baseline
- timeout / retry / partial-result behavior remains underdesigned
- legacy constraints may be imported without explicit translation into the new-system baseline

## Current Do-Not-Do List

- do not resume legacy `BUG-001` / `BUG-002` chasing as the main task
- do not rerun the old legacy synthetic dry run
- do not rewrite legacy node specs unless migration order is explicitly being defined
- do not start implementation
- do not treat historical drafts as active design sources

## Latest Meaningful Checkpoint

- `new system/mvp_core_brief.md` was added as the standalone MVP scope / core-loop / validation-boundary brief.
- Governance docs now separate operating rules, stable charter, live status, phase planning, workflow method, and communication preferences more explicitly.
- The next major project step remains: converge the new-system baseline and prepare a new synthetic dry run.
