# PLANS.md

## Objective
- Use Phase 0 dry runs to improve system design and contract clarity so later coding is smoother and lower-risk.
- Prioritize design validation over demo quality.

## Non-goals
- No production code implementation in this phase.
- No OCR/parser quality optimization as the main goal.
- No attempt to maximize automation rate on incomplete real client data.
- No premature productization of the dry run harness.

## Phases

### Phase 1: Contract and spec alignment
- unify transaction record contract
- settle transaction identity / dedupe design
- update cross-node specs for amount, bank_account, pattern_source, fallback behavior
- Done when core shared contracts are reflected consistently across specs

### Phase 2: Synthetic dry run harness design
- define synthetic-first Phase 0 approach
- prepare synthetic pack, routing expectations, and accountant simulation
- tighten workflow orchestrator assumptions
- Done when a full synthetic pack can be used to test system design end-to-end

### Phase 3: Execute synthetic dry run
- run the synthetic pack through the workflow
- compare actual routing with expected routing
- record design bugs, interface mismatches, schema gaps, and state-flow issues
- Done when findings are concrete enough to drive spec updates

### Phase 4: Feed findings back into specs
- revise specs based on synthetic dry run findings
- separate true design bugs from real-world input problems
- Done when Phase 0 produces an implementation-ready blueprint

### Phase 5: Real-world dry run
- use real statements to test ingestion noise, missing context, and practical blockers
- Done when real-world issues are clearly distinguished from system-design issues

## Current status
- Current phase: post-first-dry-run baseline convergence for the evidence-first redesign
- Last updated: 2026-04-30
- Immediate planning priority: finish the smallest coherent new-system baseline directly in `new system/new_system.md`, then rerun the synthetic pack against it

## Open questions
- Which legacy constraints are mandatory to preserve in the new baseline: deterministic gates, audit isolation, governance writes, coordinator/review boundaries, or other pieces?
- What is the smallest end-to-end new-system path that is coherent enough for the next synthetic rerun?
- How should the synthetic pack and expected routing map be rewritten to test evidence-first identity, case-memory usage, and governance boundaries instead of legacy pattern-first routing?
- Once the new baseline stabilizes, what is the right rewrite order for legacy node specs and migration-facing docs?
- Dry run timeout / retry / partial-result behavior is not yet hardened enough
