# AGENTS.md

## Mission
- Keep changes safe, minimal, and spec-consistent.
- In this repo, the primary goal is to improve system design before implementation.

## Before coding
1. Read `TASK_STATE.md` for current objective and real status.
2. Read `PLANS.md` if the task touches system design, dry run, contracts, or multiple specs.
3. Read `CLAUDE.md` for project overview and core rules.
4. If touching cross-node behavior, read `supporting documents/development_workflow.md`.

## Rules
- This repo is still spec-first; do not treat docs as optional.
- Prefer first-principles reasoning over patching around bad design.
- Do not add new components unless they solve a concrete problem.
- Keep all contract decisions consistent across related specs.
- Do not change public data contracts casually.
- If a change affects multiple nodes, update upstream/downstream specs together.
- Keep `dry_run_buglist.md` only for real design/interface bugs, not generic notes.
- Synthetic dry run is for system-design validation, not OCR/parser evaluation.

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
