# TASK_STATE.md

## Current objective

- Converge the evidence-first redesign into the repo's next working baseline by integrating the legacy system's reusable hard-boundary logic, then run the next synthetic dry run against that new baseline.

## Completed

- settled the current main-workflow direction for `description` / `pattern_source` / cheque payee handling
- aligned Node 1 / Node 3 / Coordinator / Review / Transaction Log around the current `BUG-001` / `BUG-002` baseline
- documented transaction identity / dedupe as a separate shared tool contract
- executed a synthetic dry run and wrote key findings back into the relevant specs
- documented the separate evidence-first redesign in:
  - `new system/new_system.md`
  - `new system/different_node.md`
- completed the first memory-layer brainstorming section for `Entity Memory / Entity Resolution` in `new system/memory_node_design.md`
- consolidated the accepted memory-layer details into `new system/new_system.md` and made it the only active new-system design source
- moved dynamic working entry responsibility to `AGENTS.md` and reduced `CLAUDE.md` to a stable charter

## Current state

- repo is still design/spec only; implementation has not started
- `new system/new_system.md` is now the only active new-system design source for ongoing discussion and contract convergence
- `new system/different_node.md` and `new system/memory_node_design.md` are retained only as historical background / draft material and should not receive further updates
- legacy node specs remain unchanged, but should now be read as reference sources for reusable constraints and migration planning
- the legacy onboarding mismatch is no longer the main task; it is only relevant when deciding what should be preserved or discarded in the new baseline
- one synthetic dry run has already been executed on the legacy pattern-first baseline
- no synthetic rerun has yet been executed against the new-system baseline

## Active risks

- the evidence-first redesign still has unresolved boundaries around case-memory authority, runtime evidence-pack handoff, rule promotion, and cross-spec migration
- legacy concepts may still get imported into the new system without an explicit translation of why they survive
- the synthetic pack and expected routing map have not yet been rewritten for the new baseline
- timeout / retry / partial-result behavior is still underdesigned

## Next step

- continue new-system convergence directly in `new system/new_system.md`, starting with the unresolved `Case Memory` contract
- keep refining the new-system contract and state explicitly which legacy constraints are being preserved
- define the smallest end-to-end baseline that is coherent enough for a new synthetic dry run
- remap the synthetic pack and expected routing to that new baseline
- run the next synthetic dry run against the new-system baseline, then use its findings to decide spec rewrite and migration order
