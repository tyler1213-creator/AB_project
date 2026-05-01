# TASK_STATE.md

## Document Role

`TASK_STATE.md` records the current execution state only.

It does not own the phase model, accepted design tradeoffs, agent entry rules, stable project charter, or detailed system design.

- `PLANS.md` owns project phases and gates.
- `DECISIONS.md` owns accepted tradeoffs.
- `AGENTS.md` owns agent entry rules.
- `CLAUDE.md` owns stable project charter.
- `new system/new_system.md` owns the active system design baseline.

## Current Phase

Phase 1: Design Stabilization

Current sub-focus:  
New-system baseline convergence.

## Current Objective

Converge the evidence-first redesign into the repo's next working baseline, then prepare the next synthetic dry run against that new baseline.

## Active Baseline

Active design source:

- `new system/new_system.md`

Reference / historical sources:

- `ai bookkeeper 8 nodes/` - legacy node specs; reference and migration source only
- `new system/different_node.md` - historical draft / background
- `new system/memory_node_design.md` - historical draft / background
- previous dry-run artifacts - historical evidence, not current baseline

Implementation has not started.

## Current Focus

Continue baseline convergence in `new system/new_system.md`, especially unresolved boundaries that must be coherent before the next synthetic dry run.

The immediate design focus should remain high-level contract coherence, not low-level product-field expansion.

## Active Blockers / Risks

- case-memory authority is not fully settled
- runtime evidence-pack handoff is not fully settled
- rule promotion / governance boundaries are not fully settled
- synthetic pack and expected behavior have not yet been remapped to the new baseline
- timeout / retry / partial-result behavior remains underdesigned
- legacy constraints may be imported into the new system without explicit translation

## Immediate Next Action

Continue new-system baseline convergence, starting with the unresolved Case Memory contract.

Then define the smallest coherent end-to-end baseline for the next synthetic dry run.

## Do Not Do Next

- do not resume legacy `BUG-001` / `BUG-002` chasing as the main task
- do not rerun the old legacy synthetic dry run
- do not rewrite legacy node specs unless migration order is explicitly being handled
- do not start implementation
- do not treat historical drafts as active design sources

## Last Meaningful Checkpoint

- `new system/new_system.md` is the only active new-system design source
- `new system/different_node.md` and `new system/memory_node_design.md` are historical drafts
- `PLANS.md` now owns the unified phase model
