# TASK_STATE.md

## Current objective
- Finish feeding the synthetic dry run findings back into the specs, settle the deferred `profile_change_request -> Review Agent` flow, and design a policy-pack activation layer for Node 3 before the next synthetic rerun.

## Completed
- clarified that dry run exists to optimize system design for smoother implementation
- changed shared transaction contract to absolute `amount` + explicit `direction`
- standardized `bank_account` as the profile account ID field
- clarified `description` as canonical pattern and propagated `pattern_source`
- decided fallback patterns must not write to observations or participate in rules promotion
- created `tools/transaction_identity_and_dedup_spec.md`
- updated specs to use permanent `transaction_id = txn_<ULID>`
- created `Synthetic Dry Run Pack v1`
- updated `development_workflow.md` to use synthetic-first Phase 0
- updated dry run workflow command to recognize synthetic pack usage
- executed a manual synthetic dry run against `synthetic_pack_v1`
- recorded run findings in `dry_run_codex/dry-run-pipeline-workflow/runs/2026-04-21-synthetic-pack-v1/summary.md`
- aligned Output Report with workflow by separating `report_draft` from final export
- standardized JE / Transaction Log / Output Report to `HST/GST Receivable` and `HST/GST Payable`
- relaxed Node 3 retail confidence rule so strong evidence can override `owner_uses_company_account`
- propagated `report_draft` semantics into `review_agent_spec_v3.md` so the consumer side no longer assumes final `.xlsx`
- changed profile handling to deferred review-time application:
  - Coordinator records structured `profile_change_request`
  - Review Agent processes pending profile changes before transaction review
- agreed that future Node 3 exception handling should prefer progressive disclosure via code-selected policy/skill packs instead of continuing to bloat the always-on stable prompt

## Current state
- repo is still design/spec only; implementation has not started
- synthetic pack has now been executed as a manual spec dry run
- key cross-spec findings have been written back into the relevant specs
- profile change ownership has been revised after follow-up design discussion: current direction is deferred review-time application, not Coordinator direct write
- the next major design task is to refactor Node 3 context strategy toward conditional policy-pack activation
- transaction identity / dedupe design is documented, but still not tested by executable workflow code

## Files touched
- `tools/transaction_identity_and_dedup_spec.md`
- `tools/pattern_standardization_spec.md`
- `ai bookkeeper 8 nodes/data_preprocessing_agent_spec_v3.md`
- `ai bookkeeper 8 nodes/transaction_log_spec.md`
- `ai bookkeeper 8 nodes/confidence_classifier_spec.md`
- `ai bookkeeper 8 nodes/coordinator_agent_spec_v3.md`
- `ai bookkeeper 8 nodes/output_report_spec.md`
- `ai bookkeeper 8 nodes/observations_spec_v2.md`
- `ai bookkeeper 8 nodes/je_generator_spec.md`
- `supporting documents/development_workflow.md`
- `supporting documents/dry_run_buglist.md`
- `.claude/commands/dry-run-pipeline-workflow.md`
- `dry_run_codex/dry-run-pipeline-workflow/references/synthetic_pack_v1/*`
- `dry_run_codex/dry-run-pipeline-workflow/references/synthetic_pack_v1/expected_routing_map.md`
- `dry_run_codex/dry-run-pipeline-workflow/references/synthetic_pack_v1/accountant_simulation_script.md`
- `dry_run_codex/dry-run-pipeline-workflow/runs/2026-04-21-synthetic-pack-v1/summary.md`
- `ai bookkeeper 8 nodes/confidence_classifier_spec.md`
- `ai bookkeeper 8 nodes/output_report_spec.md`
- `ai bookkeeper 8 nodes/je_generator_spec.md`
- `ai bookkeeper 8 nodes/transaction_log_spec.md`
- `ai bookkeeper 8 nodes/profile_spec.md`
- `ai bookkeeper 8 nodes/review_agent_spec_v3.md`
- `AGENTS.md`

## Risks / caveats
- `BUG-001`: cheque transaction standardization still collapses payee signal
- `BUG-002`: Node 1 transfer matching field contract is still unresolved
- a clean synthetic rerun has not yet been performed against the updated specs
- Node 3 still lacks a formal `policy pack / activation predicate / evidence override` contract; current text captures intent but not a full framework
- synthetic dry run validates design and interfaces, not OCR/parser realism
- workflow timeout / retry / partial-result behavior is still underdesigned

## Next step
- formalize the Node 3 policy-pack activation design
- rerun the synthetic pack against the updated specs
- confirm T03 / T12 now cleanly exercise the intended Section B path
- resolve `BUG-001` and `BUG-002` before Phase 5 real-world dry run
