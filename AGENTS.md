# AGENTS.md

## Purpose

This is the agent operating entrypoint for the repo.

It defines:

- document authority order
- required reading by task type
- editable vs. reference-only scope
- when to stop, escalate, or defer
- required handoff / summary discipline

It does not own product design, current task status, phase planning, or historical decision rationale.

## Authority Order

When documents disagree, resolve them in this order:

1. explicit user instruction
2. `AGENTS.md`
3. `TASK_STATE.md`
4. `PLANS.md`
5. `CLAUDE.md`
6. active product spec for the task
7. historical reference material

Each document is authoritative only within its owning responsibility:

- `AGENTS.md` owns agent operating rules, document precedence, stop/escalate conditions, and output discipline.
- `TASK_STATE.md` owns the live handoff: current status, active objective, next step, and active risks.
- `PLANS.md` owns the phase model, exit criteria, and planning questions.
- `CLAUDE.md` owns stable project charter, durable principles, and long-lived constraints.
- The active product spec owns current product design content and business-spec substance for the task.
- Historical reference material only informs preserved constraints or migration context; it is not the default design authority.

Product-spec authority for current design discussion:

- `new system/new_system.md` is the only active new-system design source.
- `new system/mvp_core_brief.md` owns MVP scope, validation intent, and core-loop boundary. It constrains MVP-path design work but does not define node schemas or implementation contracts.
- `new system/different_node.md` and `new system/memory_node_design.md` are historical drafts and should not continue to be updated.
- Legacy node specs are reusable constraints / reference material, not the default baseline.

If a legacy spec is used, state explicitly what constraint is being preserved and why it still survives in the new system.

## Required Reading

Read these before substantial work:

1. `TASK_STATE.md`
2. `CLAUDE.md`

Read `supporting documents/communication_preferences.md` before substantial user-facing analysis, review, or document writing.

Read `PLANS.md` when the task touches:

- system design
- dry run planning
- contracts
- phase changes
- multi-spec coordination

Read `supporting documents/development_workflow.md` when the task touches:

- workflow discipline
- dry run method
- phase transitions
- cross-node coordination

Treat `supporting documents/development_workflow.md` as durable workflow method only. If phase labels or current phase status conflict with `PLANS.md`, `PLANS.md` owns the current phase model and exit criteria.

Read `new system/new_system.md` when the task touches the current design target.

Read `new system/mvp_core_brief.md` when the task touches MVP scope, MVP core loop, synthetic dry-run target, or new-system baseline convergence.

Read relevant legacy specs only when:

- preserving a reusable constraint
- comparing architectures
- defining migration order

Additional targeted reads:

- `ai bookkeeper 8 nodes/onboarding_agent_spec.md` and `supporting documents/deferred_items.md` for legacy onboarding comparison or migration planning
- `supporting documents/dry_run_buglist.md` only when Phase 0 dry-run findings are directly relevant to the current new-system baseline

## Editable Scope

Default editable governance / handoff docs:

- `AGENTS.md`
- `TASK_STATE.md`
- `PLANS.md`
- `DECISIONS.md`
- `supporting documents/communication_preferences.md`
- `supporting documents/development_workflow.md`
- focused governance references under `supporting documents/` when genuinely needed

`CLAUDE.md` is editable only when the stable charter, durable principles, or long-lived constraints actually change.

`new system/new_system.md` is editable only for focused active-baseline convergence tasks. Broad rewrites require explicit user approval. If a proposed edit would change product design contracts or business-spec substance, stop and ask before proceeding.

Default reference-only docs unless the task explicitly requires otherwise:

- `new system/different_node.md`
- `new system/memory_node_design.md`
- legacy node specs under `ai bookkeeper 8 nodes/`
- product specs outside the task scope

Do not silently mix assumptions, terminology, or file paths between the active new-system spec and legacy specs.

## Operating Rules

- Keep changes safe, minimal, and spec-consistent.
- This repo is spec-first; docs are not optional.
- Improve system design before implementation.
- Prefer first-principles reasoning over local patching.
- Do not add components unless they solve a concrete problem.
- Do not change public data contracts casually.
- Treat edits to `new system/new_system.md` as narrow baseline-convergence maintenance unless the user explicitly approves broader rewriting.
- If a change affects upstream/downstream interfaces, update the related governing docs together.
- For LLM context design, prefer progressive disclosure: keep the stable prompt minimal and load policy or skill packs only when activation predicates fire.

## Stop / Escalate

Stop and ask the user before proceeding if:

- the requested change would alter product design contracts or business-spec substance
- two authority sources conflict and the conflict cannot be resolved by the authority order above
- the task would require rewriting legacy specs as if they were the active baseline
- the change would blur historical vs. active design sources

Defer rather than forcing closure when:

- the current baseline needs a real design decision, not wording cleanup
- a legacy idea cannot be translated cleanly into the new-system baseline
- synthetic dry-run work would resume before the new baseline is coherent enough to validate

## Document Update Discipline

- Update `TASK_STATE.md` after any meaningful movement in current status, next action, or active risks.
- Update `PLANS.md` when phase model, gates, or success criteria change.
- Append important accepted tradeoffs to `DECISIONS.md`; do not rewrite history into fake authority.
- Keep `CLAUDE.md` stable and low-churn.
- Keep `AGENTS.md` focused on agent operation only, not temporary handoff detail.
- Keep `supporting documents/development_workflow.md` durable; do not turn it into the current task brief.
- Preserve meaningful historical design information by reframing or referencing it, not by silently deleting it.

## Output Requirements

Final summaries must include:

- files changed
- why
- validation done
- remaining risks / follow-ups

If validation is intentionally not run, say so plainly.
