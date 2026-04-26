# AGENTS.md

## Mission
- Keep changes safe, minimal, and spec-consistent.
- In this repo, the primary goal is to improve system design before implementation.

## Before coding
1. Read `TASK_STATE.md` for current objective and real status.
2. Read `PLANS.md` if the task touches system design, dry run, contracts, or multiple specs.
3. Read `CLAUDE.md` for project overview and core rules.
4. If continuing Phase 0 dry-run bug work, read `supporting documents/dry_run_buglist.md` and treat its active bugs as the immediate priority queue.
5. If touching cross-node behavior, read `supporting documents/development_workflow.md`.
6. If discussing the current onboarding mismatch, read `ai bookkeeper 8 nodes/onboarding_agent_spec.md` and `supporting documents/deferred_items.md` before proposing changes.

## Current handoff focus
- Main-workflow handling for `BUG-001` / `BUG-002` is now spec-aligned.
- The next window should start with the **Onboarding Agent discussion**, not another main-workflow rewrite.
- Treat onboarding as a separate design problem unless and until its contract is explicitly resynced with the main workflow.

## Rules
- This repo is still spec-first; do not treat docs as optional.
- Prefer first-principles reasoning over patching around bad design.
- Do not add new components unless they solve a concrete problem.
- For LLM context design, prefer progressive disclosure: keep the stable prompt minimal and let code conditionally load policy/skill packs only when their activation predicates fire.
- Keep all contract decisions consistent across related specs.
- Do not change public data contracts casually.
- If a change affects multiple nodes, update upstream/downstream specs together.
- Keep `dry_run_buglist.md` only for real design/interface bugs, not generic notes.
- Synthetic dry run is for system-design validation, not OCR/parser evaluation.

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
