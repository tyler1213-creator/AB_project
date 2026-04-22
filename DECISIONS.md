# DECISIONS.md

## 2026-04-21

### Chose synthetic-first Phase 0 dry run
Reason:
- better for validating system design, contracts, and state flow
- avoids mixing OCR/parser noise with architecture problems

Tradeoff:
- does not test real-world ingestion robustness
- still requires later real-world dry run

### Chose permanent transaction identity over date-seq IDs
Reason:
- transaction identity is needed for split, review, intervention, and audit chain
- date-based sequence IDs are too fragile when parsing or import context changes

Tradeoff:
- requires persistent ingestion registry
- identity can no longer be reconstructed without registry

### Chose txn_<ULID> for transaction_id
Reason:
- stable permanent object key
- time-sortable and implementation-friendly

Tradeoff:
- depends on registration at first ingestion
- less human-readable than date-based IDs

### Chose a separate transaction identity / dedupe tool spec
Reason:
- this is a system-level contract, not just a Data Preprocessing detail
- keeps Transaction Log and preprocessing responsibilities clean

Tradeoff:
- adds one new shared tool and one new persistence concept

### Chose amount-as-absolute-value plus explicit direction
Reason:
- avoids duplicated sign semantics
- cleaner for JE generation and shared contracts

Tradeoff:
- all downstream consumers must respect direction as authoritative

### Chose bank_account as the transaction field name
Reason:
- prevents confusion with COA account classification field
- aligns transaction data with profile account IDs

Tradeoff:
- required cross-spec updates

### Chose to propagate pattern_source
Reason:
- helps auditability and downstream interpretation of pattern quality

Tradeoff:
- one more field in the shared transaction contract

### Chose not to write fallback patterns into observations
Reason:
- unstable patterns would pollute learning and future rule promotion

Tradeoff:
- more transactions may remain pending until pattern quality improves

### Intentionally left Node 1 transfer matching unresolved
Reason:
- current design question is cross-node and not safe to patch casually

Tradeoff:
- remains an explicit open issue in `dry_run_buglist.md`
