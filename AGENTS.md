# AGENTS.md

## Mission
- Keep changes safe, minimal, and spec-consistent.
- In this repo, the primary goal is to improve system design before implementation.

## Before coding
1. Read `TASK_STATE.md` for current objective and real status.
2. Read `PLANS.md` if the task touches system design, dry run, contracts, or multiple specs.
3. Read `CLAUDE.md` for project overview and core rules.
4. If touching cross-node behavior, read `supporting documents/development_workflow.md`.
5. If discussing the current design target, read `new system/new_system.md` and `new system/different_node.md`.
6. If borrowing logic from the legacy system, read the relevant old node/tool spec and state explicitly what constraint is being preserved.
7. If revisiting the legacy onboarding mismatch for comparison or migration planning, read `ai bookkeeper 8 nodes/onboarding_agent_spec.md` and `supporting documents/deferred_items.md`.
8. If continuing Phase 0 dry-run bug work, read `supporting documents/dry_run_buglist.md`, but do not resume legacy dry-run bug chasing unless it serves the current new-system baseline.

## Current handoff focus
- Main-workflow handling for `BUG-001` / `BUG-002` in the legacy design is no longer the active work target; treat it as already-mined reference material.
- The current task is to converge the evidence-first redesign in `new system/` into the repo's next working baseline.
- Pull forward valuable hard-boundary logic from the legacy specs, but do not rewrite those old node specs yet unless migration order is explicitly being defined.
- Do not spend the next window on another standalone legacy onboarding fix or another legacy main-workflow pass unless the user explicitly asks for that.
- After the new-system contract is coherent end-to-end, the next major step is a synthetic dry run against that new baseline.

## Rules
- This repo is still spec-first; do not treat docs as optional.
- Prefer first-principles reasoning over patching around bad design.
- Do not add new components unless they solve a concrete problem.
- For LLM context design, prefer progressive disclosure: keep the stable prompt minimal and let code conditionally load policy/skill packs only when their activation predicates fire.
- When discussing the current design, default to `new system/new_system.md` and `new system/different_node.md`.
- Legacy node specs are now reference material for reusable constraints, not the default discussion baseline.
- If importing a legacy idea, say exactly what is being preserved and why it survives in the new system.
- Do not silently mix assumptions or file paths between `new system/` and the legacy node specs.
- Keep all contract decisions consistent across related specs.
- Do not change public data contracts casually.
- If a change affects multiple nodes, update upstream/downstream specs together.
- Keep `dry_run_buglist.md` only for real design/interface bugs, not generic notes.
- Synthetic dry run is for system-design validation, not OCR/parser evaluation.
- The next synthetic dry run should validate the new-system baseline, not reopen already-settled legacy routing questions unless they expose a reusable constraint.

## Communication preferences
- I do not need agreement. I need valuable, objective, and correct responses.
- I strongly dislike patch-style fixes. Do not propose patching unless it is truly unavoidable.
- Approach every problem from first principles. You may question any existing design.

## Validation
- For spec work: check cross-doc consistency manually.
- For dry run work: compare actual routing against `expected_routing_map.md`.
- If changing dry run design, verify it still serves Phase 0 goals in `development_workflow.md`.

## Output requirements
- In the final summary include: files changed, why, validation done, remaining risks / follow-ups.

## Long-task protocol
- Update `TASK_STATE.md` after any meaningful design move.
- Record only important tradeoffs in `DECISIONS.md`.
- Keep `PLANS.md` current when phase or success criteria changes.
- Keep `CLAUDE.md` and `dry_run_buglist.md` trimmed to current reality; remove solved items and stale focus bullets instead of letting historical status accumulate.
