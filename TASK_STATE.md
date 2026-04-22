# TASK_STATE.md

## Current objective
- Execute the synthetic dry run pack and use the results to improve system design, contracts, and workflow clarity before coding begins.

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

## Current state
- repo is still design/spec only; implementation has not started
- synthetic pack materials exist and are internally consistent
- no synthetic dry run execution has happened yet in the new scheme
- transaction identity / dedupe design is documented, not yet tested by workflow execution

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

## Risks / caveats
- `BUG-001`: cheque transaction standardization still collapses payee signal
- `BUG-002`: Node 1 transfer matching field contract is still unresolved
- synthetic dry run validates design and interfaces, not OCR/parser realism
- workflow timeout / retry / partial-result behavior is still underdesigned

## Next step
- run the synthetic pack through the workflow
- compare actual routing with `expected_routing_map.md`
- update `dry_run_buglist.md` and related specs based on findings
