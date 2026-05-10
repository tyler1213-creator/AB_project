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

Implementation has not started.

Current node-stage design status:

- all 15 current workflow nodes have Stage 1 functional-intent documents
- all 15 current workflow nodes have Stage 2 logic-and-boundaries documents
- all 15 current workflow nodes have Stage 3 data-contract documents
- Stage 3 docs are first-pass Codex-generated and independently structure-validated
- A read-only Codex Stage 3 cross-node contract + field-lineage audit has been generated and Hermes sample-verified; the next step is Tyler-gated core shared-contract decision review before any revision pass, Stage 4, implementation, or synthetic remapping

## Active Objective

Converge the evidence-first redesign into the repo's next working baseline by expressing the current system in workflow-node/log terms and implementation-facing data contracts, then prepare the next synthetic dry run against that new baseline after contract boundaries are reviewed.

## Active Baseline

- `new system/new_system.md` is the only active new-system design source.
- `new system/different_node.md` and `new system/memory_node_design.md` are historical drafts and should not continue to be updated.
- Legacy node specs are reusable constraints / reference material, not the default baseline.

## Immediate Next Step

Continue Tyler-gated review of the 8 core shared contract decisions from the Stage 3 field-lineage audit. The “three questions” in the current discussion mean Decisions 1–3 from that 8-item list, not the separate correction/finalization task ideas.

Current status:
- Decision 1 accepted: establish shared `ObjectiveTransactionBasis` / `TransactionBasis` as a contract/glossary target, not a node, Log, memory store, or business rule.
- Decision 2 accepted: canonical `direction = inflow | outflow | unknown`.
- Decision 3 accepted at product-intent level: case-supported results may proceed to JE / final logging when a controlled authority path is satisfied; old `ai_reasoning` is now `ai_decision_summary`; old `policy_trace` remains a legacy placeholder; all replacement names beyond `ai_decision_summary` remain Tyler-gated; `decision_control_trace` is rejected as an independent concept.
- Next user question: Decision 4 — whether blocked / not-finalizable / JE-blocked outcomes need a durable terminal audit record.

Do not start Stage 4 execution algorithms, implementation, test matrices, coding-agent task contracts, Codex revision, Stage 3 schema cleanup, or synthetic dry-run remapping unless explicitly requested.

## User-Designated Core Decision Queue

This queue tracks the 8 core shared contract decisions from `/Users/kingbayue/Desktop/AugustWang_Summary_Notes/2026-05-06_135026_PDT_stage3_cross_node_field_lineage_audit.md`. It is not an implementation queue.

1. Decision 1 — canonical shared `TransactionBasis` contract.
   - Status: accepted.
   - Accepted direction: use shared `ObjectiveTransactionBasis` / `TransactionBasis` contract/glossary plus explicit local aliases where needed.

2. Decision 2 — global direction enum.
   - Status: accepted.
   - Accepted direction: `direction = inflow | outflow | unknown`.

3. Decision 3 — case-supported result direct JE / final logging.
   - Status: accepted at product-intent level; naming/details still Tyler-gated.
   - Accepted direction: controlled case-supported automation is allowed in principle.
   - Confirmed naming: `ai_reasoning -> ai_decision_summary`.
   - Rejected: `decision_control_trace` as an independent object/contract/Log/memory store, and the prior risk/blocker/exception-pack/override/finalization-gate field cluster as an accepted design object.
   - Open later: exact current-system names replacing legacy `policy_trace`, exact authority/review/correction records, and exact contract fields if needed.

4. Decision 4 — blocked / not-finalizable / JE-blocked terminal audit record.
   - Status: next Tyler decision.
   - Question: should these outcomes create no Transaction Log record, a separate terminal audit record, or an expanded Transaction Log entry status?

5. Decision 5 — candidate persistence locus.
   - Status: pending Tyler decision after Decision 4.

6. Decision 6 — Governance Review durable memory mutation locus.
   - Status: pending Tyler decision after Decision 5.

7. Decision 7 — Post-Batch Lint auto-downgrade event / mutation authority.
   - Status: pending Tyler decision after Decision 6.

8. Decision 8 — Onboarding stable foundation creation authority.
   - Status: pending Tyler decision after Decision 7.

Deferred until after all 8 decisions:
- redesign wrong-system-result correction loop from first principles;
- redesign auto-finalization / review-surfacing model from first principles;
- perform any bounded Stage 3 revision or naming cleanup.

## Active Risks

- all workflow nodes now have Stage 1, Stage 2, and Stage 3 documents, but Stage 3 data contracts are first-pass design artifacts and still need Tyler-gated shared-contract decision review before revision.
- Decisions 1–2 are accepted and Decision 3 is accepted at product-intent level, but Decisions 4–8 remain open.
- future Stage 3 revision must not treat `finalization_authority_basis`, `review_attention_signal`, `decision_control_trace`, or legacy `policy_trace` as accepted final names.
- shared handoff details, exact routing states, thresholds, execution algorithms, implementation tasks, and test matrices remain intentionally unfrozen.
- synthetic pack and expected behavior have not yet been remapped to the new baseline.
- timeout / retry / partial-result behavior remains underdesigned.
- legacy constraints may be imported without explicit translation into the new-system baseline.
- future agents may treat first-pass Stage 3 contracts as implementation-ready too early unless Open Contract Boundaries are reviewed and resolved.
- entity-centered case organization vs Case Log authority boundary remains underdefined; see `Tyler_buglist/entity_case_log_relationship_ambiguity.md`.
- deterministic rule execution vs case-based semantic judgment remains underdefined where supporting evidence must become rule-eligible predicates; see `Tyler_buglist/rule_mechanism_evidence_predicate_ambiguity.md`.

## Current Do-Not-Do List

- do not resume legacy `BUG-001` / `BUG-002` chasing as the main task
- do not rerun the old legacy synthetic dry run
- do not rewrite legacy node specs unless migration order is explicitly being defined
- do not start implementation
- do not start Stage 4 execution algorithms, Stage 5 implementation maps, Stage 6 test matrices, or Stage 7 coding-agent task contracts unless explicitly requested
- do not treat first-pass Stage 3 data contracts as implementation-ready before cross-node review
- do not start synthetic dry-run remapping until Stage 3 open boundaries / shared handoffs are reviewed
- do not treat historical drafts as active design sources

## Latest Meaningful Checkpoint

- 2026-05-08: Recorded two Tyler-raised design bugs under `Tyler_buglist/`: entity/case-log relationship ambiguity and rule/evidence-predicate mechanism ambiguity. These are open design issues, not accepted contract changes.

- 2026-05-06 17:16 PDT: Clarified that the current “three questions” are Decisions 1–3 from the 8-item Stage 3 shared-contract decision queue. Decisions 1–2 are accepted; Decision 3 is accepted at product-intent level with `ai_reasoning -> ai_decision_summary`, legacy `policy_trace` as placeholder only, and `decision_control_trace` rejected. Decision 4 is next.

- 2026-05-06 13:50 PDT: Ran a fresh read-only Codex Stage 3 cross-node contract + field-lineage audit with live-doc reading and Superpowers enforcement. Hermes sample-verified representative citations. Audit report saved to `/Users/kingbayue/Desktop/AugustWang_Summary_Notes/2026-05-06_135026_PDT_stage3_cross_node_field_lineage_audit.md`. Next step is Tyler-gated review of the core shared contract decisions before any bounded Codex revision pass.

- 2026-05-06 02:28 PDT: all current workflow nodes now have Stage 3 data-contract documents saved under `new system/node_stage_designs/`.
- Stage 3 generation used fresh Codex sessions per node, forced live-doc reading and Superpowers usage, and produced 15 `__stage_3__data_contract.md` files.
- Independent verification passed for expected file count, required Stage 3 sections, absence of BLOCKED/TODO/TBD markers, whitespace, and `git diff --check`.
- Stage 3 docs were corrected to record that `supporting documents/node_design_roadmap_zh.md` and the optional project workflow skill were absent; repo `node_design_roadmap.md` plus Stage 1/2 docs were used as workflow authority.
- The next major project step is user-gated: review Stage 3 cross-node contract consistency / Open Contract Boundaries before Stage 4, implementation, synthetic remapping, tests, or coding-agent task contracts.
