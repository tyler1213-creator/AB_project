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

### Split review-facing report_draft from final output export
Reason:
- the workflow and Review Agent need a pre-review snapshot
- the final `.xlsx` should remain a post-review deliverable

Tradeoff:
- output layer now has two artifacts instead of one
- review and export timing must be described separately

### Chose HST/GST Receivable and HST/GST Payable as canonical control-account names
Reason:
- matches the synthetic foundation pack and JE builder contract
- avoids downstream ambiguity in JE validation and reporting

Tradeoff:
- required cross-spec cleanup in JE, Transaction Log, and Output Report docs

### Chose owner_uses_company_account as a default downgrade, not an absolute veto
Reason:
- receipt-backed and stable-observation cases still need a path to Section B
- keeps synthetic dry run review-correction scenarios reachable

Tradeoff:
- Node 3 guidance becomes slightly more nuanced
- stronger evidence thresholds must stay explicit to avoid overconfidence

### Replaced Coordinator-direct profile writes with deferred profile_change_request handling
Reason:
- after removing the practical need for same-batch retrigger, Coordinator no longer needed direct write access to `profile.md`
- Coordinator can capture the signal precisely while Review Agent keeps the write path centralized and review-confirmed
- avoids mid-batch profile mutations while still preserving the accountant's original statement as structured input

Tradeoff:
- profile changes now primarily benefit the next batch, not the already-produced current-batch routing
- synthetic references and dry-run expectations that assumed Coordinator direct writes must be updated

### Prefer progressive disclosure for Node 3 exception logic
Reason:
- stable prompt growth will otherwise keep absorbing low-frequency risk rules
- the existing classifier already has a good split between stable context, transaction context, and conditional loading
- code-selected policy/skill packs are a cleaner way to represent exceptional risk logic such as retail-personal-use warnings

Tradeoff:
- requires a more explicit activation-predicate and evidence-override design
- adds one more orchestration layer around the LLM call

## 2026-04-22

### Reframed Node 3 around a four-layer context model
Reason:
- the prior spec had started layering new policy-pack ideas on top of the old narrative without a single dominant structure
- separating `Core Skill`, `Domain Packs`, `Risk / Exception Packs`, and `Evidence Overrides` makes Node 3's prompt strategy easier to reason about from first principles
- this gives a cleaner home for low-frequency risk logic such as retail mixed-use warnings, payroll/profile conflicts, force-review gating, and fallback caution

Tradeoff:
- introduces more explicit orchestration concepts into the spec
- requires careful downstream alignment so new concepts do not remain Node-3-only terminology

### Chose code-driven risk-pack activation over profile-field rules embedded in always-on prompt text
Reason:
- profile flags such as `owner_uses_company_account` and `has_employees` are not themselves decisions; they are deterministic activation inputs for risk logic
- letting code activate packs keeps the stable prompt smaller and makes the reason for a downgrade or block auditable
- this structure also cleanly separates soft risk from blocking conditions

Tradeoff:
- classifier orchestration becomes more complex than a single static prompt recipe
- downstream specs may need explicit contracts if they later want to consume pack traces

### Chose current-batch profile snapshot semantics for Node 3
Reason:
- this keeps Node 3 consistent with deferred `profile_change_request -> Review Agent` ownership
- avoids batch-midstream profile mutation changing classification behavior after some transactions have already run
- preserves a clean rule: Coordinator captures profile change signals, Review Agent confirms and writes them, future batches benefit

Tradeoff:
- Node 3 cannot self-heal the current batch using newly surfaced profile corrections
- some structurally blocked transactions must still be resolved via Coordinator / Review even when the accountant has already explained the issue

### Chose to keep `policy_trace` as a Node 3 output before promoting it to a cross-spec contract
Reason:
- the new activation framework benefits from an explicit internal trace of activated packs and override evidence
- but downstream interfaces should not be changed casually before deciding whether they truly need to consume that structure
- this lets Node 3 stabilize first while preserving optionality for Coordinator / Transaction Log / report_draft integration

Tradeoff:
- for now, `policy_trace` exists as a local Node 3 design concept rather than a fully propagated system-wide field
- follow-up work is still required if audit/reporting surfaces need to display it formally

### Promoted `policy_trace` into Coordinator handoff and Transaction Log, but not `report_draft`
Reason:
- Coordinator needs structured pack/risk context to ask better questions for PENDING transactions, especially for blocking/profile-conflict cases
- Transaction Log is the right audit surface for retaining AI-side pack activation and override evidence on `ai_high_confidence` decisions
- `report_draft` should stay review-facing; exposing raw pack traces there would mix audit/debug detail into the accountant's primary review view

Tradeoff:
- downstream interfaces now carry one more structured field in the AI path
- Review Agent must use Transaction Log, not the visible report, when it needs to inspect `policy_trace`

## 2026-04-26

### Chose an identity-signal-first contract for `description`
Reason:
- not every transaction contains a usable business-identity signal in `raw_description`
- forcing all transactions through one canonical-pattern pipeline caused cheque and transfer edge cases to pollute learning
- the correct first-principles question is whether the transaction exposes a recognizable counterparty / identity signal at all

Tradeoff:
- `description` can no longer be assumed present everywhere
- downstream specs must explicitly handle `description = null`

### Chose to allow `pattern_source = null`
Reason:
- some valid `description` values now come from outside `standardize_description` (for example cheque `payee`)
- some transactions intentionally skip standardization entirely when no recognizable identity signal exists
- forcing synthetic source labels onto those paths would blur audit semantics

Tradeoff:
- downstream consumers must distinguish `null` from `fallback`
- the shared transaction contract becomes slightly more nuanced

### Chose direct cheque payee as the current canonical pattern
Reason:
- cheque `payee` is the best available identity source in the current design
- reusing the existing raw-description standardizer would incorrectly apply bank-description assumptions to cheque payees
- delaying lightweight normalization is safer than over-designing it before more evidence exists

Tradeoff:
- cheque payee formatting may be less normalized than card / PAD patterns for now
- a later cleanup pass may be needed once real-world cheque variation is better understood

### Chose Node 1 internal-transfer matching to read `raw_description`
Reason:
- internal transfer recognition is a bank-raw-signal problem, not a canonical-pattern problem
- `Profile.account_relationships.pattern` already expresses raw bank text fragments
- keeping the match on `raw_description` avoids forcing transfer semantics into the learning-oriented pattern layer

Tradeoff:
- Node 1 is an explicit raw-signal consumer rather than a default-description consumer
- `Profile` field names remain imperfect until a future naming cleanup

## 2026-04-27

### Chose to document the evidence-first redesign in separate specs instead of rewriting legacy node specs in place
Reason:
- the redesign changes the system at the memory-architecture level, not just one node
- rewriting old node specs before adoption would blur the boundary between legacy baseline and proposed replacement
- separate specs make it possible to compare architectures cleanly and decide migration order from first principles

Tradeoff:
- the repo now intentionally carries two parallel design layers for a period of time
- future discussions must be explicit about whether they refer to the legacy node baseline or the new evidence-first redesign

### Slimmed `CLAUDE.md` and moved active entry responsibility to `AGENTS.md`
Reason:
- `CLAUDE.md` had started mixing stable project charter content with dynamic focus, handoff, and migration status
- `AGENTS.md`, `TASK_STATE.md`, and `PLANS.md` already carry the dynamic working context more cleanly
- keeping `CLAUDE.md` as a low-churn charter reduces drift and duplicate maintenance

Tradeoff:
- readers must now follow the documented entry order instead of expecting `CLAUDE.md` to contain current task state
- some cross-file navigation becomes more explicit, but less self-contained in one document

### Chose to make new-system convergence the current working phase before the next synthetic rerun
Reason:
- the main unresolved problems now sit in the new system's memory, matching, and governance design, not in another round of legacy main-workflow patching
- the most useful next dry run is one that validates the evidence-first baseline after it has absorbed the legacy system's valuable hard boundaries
- keeping legacy specs untouched while using them as reference sources is a cleaner way to preserve good constraints without pretending they are still the active design target

Tradeoff:
- entry docs must now say more clearly that old specs are reference material while `new system/` is the current design target
- dry-run work is temporarily delayed until the new baseline is coherent enough to test end-to-end
- migration order for rewriting legacy specs is still deferred until after that new-baseline dry run

## 2026-04-29

### Chose entity memory as counterparty/vendor/payee plus confirmed role/context
Reason:
- the new system needs to distinguish ambiguous names and different client relationships without turning entity identity into accounting classification
- runtime role guesses are too close to business judgment to persist as stable memory without accountant confirmation
- onboarding may still preserve accountant-derived historical role signals when the source is accountant-prepared books and authority metadata is explicit

Tradeoff:
- more transactions may require role confirmation before deterministic automation
- entity resolution must carry candidate-role context separately from the long-term entity record

### Separated entity lifecycle status from automation policy
Reason:
- `active` should mean a usable long-term entity, not automatic permission to classify
- automation eligibility depends on aliases, roles, rules, case history, and governance risk, so it needs a separate policy field

Tradeoff:
- the entity contract has one more dimension to manage
- rule matching must check both lifecycle state and automation policy rather than reading one status field

### Let lint pass downgrade entity automation while keeping upgrades accountant-approved
Reason:
- automatic downgrades reduce risk after bad outcomes or repeated interventions
- upgrades expand automation authority, so they should require accountant approval
- entity automation policy is separate from active rule lifecycle

Tradeoff:
- lint pass must produce auditable downgrade reasons
- accountant review still needs to handle policy upgrades and contested downgrades

### Kept active rule changes under accountant approval
Reason:
- rules are deterministic execution authority, so creation, promotion, modification, deletion, and downgrade must remain accountant-governed
- the system can detect candidates and risks, but should not silently change active deterministic behavior

Tradeoff:
- rule governance requires review workflow support
- automation gains from case memory and entity memory must be staged through review before becoming deterministic rules

### Made entity merge and split governance-only operations
Reason:
- merge and split change long-term memory identity and can affect cases, aliases, rules, and audit interpretation
- runtime can detect candidates, but direct automatic mutation would make the audit chain unstable
- Transaction Log should keep historical references and rely on governance events for later interpretation

Tradeoff:
- Review Agent must support entity-governance workflows before the memory layer is fully maintainable
- some duplicate or over-broad entities may persist until accountant review resolves them

## 2026-04-30

### Consolidated new-system design authority into `new_system.md`
Reason:
- `new_system.md`, `different_node.md`, and `memory_node_design.md` had started duplicating the same memory-layer contract
- duplicated active specs make future windows prone to drift and partial updates
- keeping one active new-system design source is safer for contract convergence before the next synthetic dry run

Tradeoff:
- `new_system.md` becomes longer and must carry both baseline narrative and key contract details
- `different_node.md` and `memory_node_design.md` remain useful historical context, but they are no longer maintained as active specs
