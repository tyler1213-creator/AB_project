# Synthetic Dry Run Pack v1 — Run Summary

Date: 2026-04-21
Mode: manual spec-execution against the synthetic pack
Scope: `T01-T12` in `synthetic_pack_v1`

## Outcome

The synthetic pack was sufficient to validate the main workflow shape, but it exposed four real cross-spec problems:

1. Node 3's retail-confidence gate was too absolute, so receipt-backed or clean-observation cases could not reach the intended high-confidence path.
2. Output Report spec only described a post-review final export, while the workflow and Review Agent require a pre-review `report_draft`.
3. JE / Transaction Log / Output Report disagreed on the canonical HST control-account names, and `validate_je` did not clearly allow revenue-side `HST/GST Payable`.
4. Profile ownership rules conflicted on whether Review Agent may write profile updates.

Known watchpoints `BUG-001` and `BUG-002` were confirmed, but remain open.

## Routing Review

| Case | Expected | Dry-run reading of current spec | Result |
| --- | --- | --- | --- |
| T01 | `DP -> Node 1 -> JE` | Intended to hit Node 1, but still depends on unresolved transfer match contract between `raw_description`, `description`, and `account_relationships.pattern`. | `interface_mismatch` |
| T02 | `DP -> N1 miss -> N2 -> JE` | Rule path is clean. `ROGERS WIRELESS` exact-match rule is spec-consistent. | `pass` |
| T03 | `DP -> N1 miss -> N2 miss -> N3 high -> JE` | Receipt gives strong business evidence, but current Node 3 high-confidence rule still hard-blocked retail vendors when `owner_uses_company_account = true`. | `design_bug` |
| T04 | `DP -> ... -> N3 pending -> Coordinator` | Pending-with-options path is coherent. | `pass` |
| T05 | `DP -> ... -> N3 pending -> Coordinator` | Pending-without-context path is coherent. | `pass` |
| T06 | `DP -> ... -> N3 pending -> Coordinator split -> retrigger` | Current Coordinator spec also allows direct completion after split when accountant already gives explicit classification for each child. | `acceptable alternate path` |
| T07 | `DP -> ... -> N3 or pending` | `cheque_info` can support classification, but pattern standardization still collapses cheque learning path. | `acceptable alternate path` + confirms `BUG-001` |
| T08 | `DP -> ... -> N3 pending` | Fallback-pattern contract is coherent and correctly excluded from observations. | `pass` |
| T09 | `DP -> ... -> N3 pending anomaly -> Coordinator` | Payroll anomaly and same-batch profile update path are coherent. | `pass` |
| T10 | `DP -> N1 miss -> N2 -> JE` | Rule path is clean. | `pass` |
| T11 | `DP -> ... -> N3 pending` | `force_review` path is coherent. | `pass` |
| T12 | `DP -> ... -> N3 high -> JE -> Review` | Same retail-confidence issue as T03 prevents the intended Section B review-correction path from being exercised. | `design_bug` |

## Findings Applied Back Into Specs

- Output layer now distinguishes `report_draft` for review from the final `.xlsx` export.
- HST control-account naming is standardized to `HST/GST Receivable` and `HST/GST Payable`.
- Node 3 now treats `owner_uses_company_account = true` as a confidence downgrade by default, not an absolute veto when strong disambiguating evidence exists.
- Follow-up design discussion later replaced this with a deferred model:
  - Coordinator records structured `profile_change_request`
  - Review Agent applies pending profile changes at the start of review

## Post-Run Follow-up

On 2026-04-22, two follow-up design decisions superseded part of the original remediation:

1. Profile changes are no longer written directly by Coordinator; they are captured as structured requests and applied by Review Agent before transaction review.
2. Future Node 3 exception handling should move toward progressive disclosure via code-selected policy/skill packs rather than continuing to expand the always-on stable prompt.

## Still Open

- `BUG-001`: cheque pattern standardization still lacks a clean cheque-aware canonicalization contract.
- `BUG-002`: Node 1 transfer matching field contract is still unresolved.
- timeout / retry / partial-result behavior is still underdesigned.
