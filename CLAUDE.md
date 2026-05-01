# AI Bookkeeper

## Document Role

`CLAUDE.md` is the stable project charter.

It keeps long-lived principles, architecture constraints, and durable project boundaries.

It does not own:

- current task handoff
- temporary focus
- current risks
- next action
- phase execution detail

Use `AGENTS.md` for agent operating rules, `TASK_STATE.md` for the live handoff, and `PLANS.md` for phase planning.

## Project Context

AI bookkeeping system for Canadian accounting workflows. The intended operating context includes:

- Canadian GST / HST handling
- double-entry bookkeeping
- CRA audit traceability and long-retention expectations

This repo remains spec-first and design-first. It is primarily a design repository, not an implementation repository.

## Stable Repository Boundary

The repo intentionally contains two design layers:

- legacy node specs under `ai bookkeeper 8 nodes/`
- the evidence-first redesign under `new system/`

Their roles are different:

- `new system/new_system.md` is the only active new-system design source.
- `new system/different_node.md` and `new system/memory_node_design.md` are historical drafts and should not continue to be updated.
- Legacy node specs are reusable constraints / reference material, not the default baseline.

This dual-track state is intentional until the new-system baseline is coherent enough to drive the next synthetic dry run and later migration work.

## Stable Project Principles

- Spec-first: design documents are part of the system, not optional notes.
- First-principles reasoning beats patching around bad structure.
- Stable contracts matter more than local convenience.
- Do not create new components unless they solve a concrete problem.
- Preserve source-of-truth clarity across related docs.
- Separate active design authority from historical reference material.

## Stable Architecture Principles

### Responsibility Split

- `workflow` describes state flow and operating procedure
- `agent` makes judgments and orchestration decisions
- `tool` performs deterministic execution, storage, or computation

The stable design preference is:

- AI for judgment and orchestration
- code for deterministic behavior

### Authority and Governance

- Accountant authority remains final on accounting decisions and durable governance changes.
- High-authority changes to long-term memory or automation behavior must not be inferred casually from a single runtime event.
- Rule promotion requires governance; one-off outcomes must not automatically become long-term policy.
- Exceptions must not silently contaminate durable learning layers.

### Memory and Audit Discipline

- Evidence should remain recoverable and auditable.
- Transaction identity should stay stable across review and reprocessing flows.
- Long-term memory layers should each have a clear single responsibility.
- Audit-facing records should preserve why the system acted, not just what it output.

### Context Design Principle

For LLM-context design, prefer progressive disclosure:

- keep the stable prompt minimal
- load policy or skill packs only when their activation predicates fire

## Durable Working Constraint

When borrowing from the legacy system, preserve constraints explicitly rather than implicitly carrying over structure. The question is not whether a legacy node existed, but which reusable boundary or behavior still survives in the evidence-first system.
