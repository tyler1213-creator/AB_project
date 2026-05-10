# Profile / Structural Match Node — Stage 3：Data Contract Spec

## 1. Stage 范围

本 Stage 3 只定义 `Profile / Structural Match Node` 的 implementation-facing data contract。

前置依据是：

- `new system/new_system.md`
- `new system/node_stage_designs/profile_structural_match_node__stage_1__functional_intent.md`
- `new system/node_stage_designs/profile_structural_match_node__stage_2__logic_and_boundaries.md`

本文件把 Stage 1/2 已批准的 profile-backed structural transaction gate、authority boundary、candidate-only boundary 和 no-memory-mutation boundary 转换为输入对象、输出对象、字段语义、字段 authority、runtime / durable memory 边界、validation rules 和 compact examples。

本阶段不定义：

- step-by-step execution algorithm 或 branch sequence
- technical implementation map
- repo module path、class、API、storage engine、DB migration 或代码布局
- test matrix、fixture plan 或 coding-agent task contract
- `Profile` 的完整全局 schema
- JE Generation、Coordinator、Review、Governance Review 或 Transaction Logging 的完整下游 schema
- 新 product authority、legacy replacement mapping 或历史 spec 迁移关系

## 2. Contract Position in Workflow

`Profile / Structural Match Node` 位于：

```text
Evidence Intake / Preprocessing Node
→ Transaction Identity Node
→ Profile / Structural Match Node
→ Entity Resolution Node / structural downstream flow
```

### 2.1 Upstream Handoff Consumed

本节点消费 runtime `profile_structural_match_request`。

上游必须已经完成或明确给出：

- objective transaction basis；
- evidence references；
- stable `transaction_id`；
- current batch / client context；
- identity / duplicate 状态；
- 可供读取的 current `Profile` structural snapshot。

如果 evidence intake 或 transaction identity 尚未完成，本节点输入无效。

### 2.2 Downstream Handoff Produced

本节点输出 runtime `profile_structural_match_result`。

下游按结果类别消费：

- `Entity Resolution Node`：只消费 `non_structural_entity_resolution_handoff`，表示当前交易未被结构性路径完成。
- `Coordinator / Pending Node`：消费 `structural_pending_handoff` 和聚焦问题语境。
- `Review Node` / `Governance Review Node`：消费 `structural_issue_signal` 或 `profile_governance_candidate_signal`；这些 signal 不是 approval。
- `JE Generation Node`：可消费 `structural_handled_result` 中的 approved structural accounting basis；具体 journal entry 仍由 JE Generation Node 计算。
- `Transaction Logging Node`：不直接消费本节点作为 runtime decision source；最终审计记录由后续 final outcome / JE / review flow 进入 Transaction Logging Node。

### 2.3 Logs / Memory Stores Read

本节点可以读取或消费：

- `Evidence Log` references：用于追溯 current transaction evidence，不作为业务结论。
- stable transaction identity：来自 `Transaction Identity Node`。
- `Profile`：客户结构事实，例如 bank accounts、internal transfer relationships、loan relationships、tax config 或其他已确认结构 facts。
- profile authority / confirmation context：只用于判断某个 profile fact 是否具备 stable authority。
- upstream evidence / identity issue context：用于限制结构性判断。

本节点不读取：

- `Transaction Log` 做 runtime structural decision；
- `Entity Log` 做普通 entity identity；
- `Case Log` 做 case precedent；
- `Rule Log` 做 deterministic rule match；
- `Knowledge Log / Summary Log` 作为 stable profile authority。

### 2.4 Logs / Memory Stores Written or Candidate-Only

本节点不直接写入任何 durable log / memory store。

它不能写：

- `Transaction Log`
- `Profile`
- `Entity Log`
- `Case Log`
- `Rule Log`
- `Governance Log`
- `Knowledge Log / Summary Log`
- approved profile fact、stable entity、approved alias、confirmed role、active rule 或 automation policy

本节点只可以输出 candidate-only / issue signals，例如：

- `profile_fact_candidate_signal`
- `internal_transfer_relationship_candidate`
- `loan_relationship_candidate`
- `bank_account_relationship_issue`
- `profile_conflict_issue`
- `missing_profile_fact_issue`
- `profile_governance_candidate_signal`

这些 signal 可以被 Coordinator、Review、Profile update 或 Governance Review workflow 评估。它们本身不能创建 stable `Profile` truth，不能支持 `structural_handled`，也不能支持 rule match、rule promotion 或 durable memory mutation。

## 3. Input Contracts

### 3.1 `profile_structural_match_request`

Purpose：本节点的单次 runtime input envelope。

Source authority：workflow orchestrator / upstream handoff。它汇总上游已产生的 runtime facts 和 profile snapshot references，不自行创建 product authority。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `transaction_basis` | 当前交易的客观结构基础 | Evidence Intake / Transaction Identity | runtime object with durable refs |
| `upstream_workflow_context` | evidence / identity gate 状态和 issue context | upstream workflow | runtime |
| `profile_structural_snapshot` | 当前客户 stable profile structural facts 的只读快照 | `Profile` | runtime view over durable store |

Optional fields：

- `bank_raw_signal_basis`：银行原始信号视图，用于 internal-transfer 或类似 structural relation 的 raw-signal matching。
- `structural_candidate_issue_context`：上游或当前批次暴露的 profile candidate、missing-profile、conflict 或 accountant-context signal。
- `request_trace`：runtime diagnostics；不能作为 profile authority。

Validation / rejection rules：

- 缺少 `transaction_basis.transaction_id`、`transaction_basis.client_id`、`transaction_basis.evidence_refs` 或 `profile_structural_snapshot.client_id` 时，input invalid。
- `transaction_basis.client_id` 必须与 `profile_structural_snapshot.client_id` 一致。
- `upstream_workflow_context.evidence_status` 必须表示 evidence foundation ready。
- `upstream_workflow_context.transaction_identity_status` 必须表示 stable identity assigned。
- 如果上游已标记 duplicate blocked、identity blocked 或 evidence blocked，本节点不能输出 `structural_handled`。
- `request_trace`、candidate context、LLM explanation 或 raw bank signal 不能替代 stable profile authority。

Runtime-only vs durable references：

- `profile_structural_match_request` 是 runtime-only envelope。
- `transaction_id`、`client_id`、`evidence_refs`、profile fact refs 是 durable references。
- 本节点收到 request 不表示拥有任何 durable write authority。

### 3.2 `transaction_basis`

Purpose：描述当前交易的客观事实，用于判断是否能落入 stable profile structural relation。

Source authority：`Evidence Intake / Preprocessing Node`、`Transaction Identity Node`、`Evidence Log`。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `transaction_id` | 稳定交易身份 | Transaction Identity Node | durable reference |
| `client_id` | 当前客户标识 | batch / client context | durable reference |
| `batch_id` | 当前处理批次 | workflow runtime | runtime |
| `transaction_date` | 交易日期 | Evidence Intake | runtime with evidence ref |
| `amount_abs` | 交易金额绝对值 | Evidence Intake | runtime with evidence ref |
| `direction` | 交易方向 | Evidence Intake | runtime with evidence ref |
| `bank_account` | 当前交易所属银行账户 | Evidence Intake / Profile account context | durable reference or runtime account key |
| `evidence_refs` | 支撑当前交易基础的 evidence references | Evidence Log | durable references |

Allowed `direction` values：

- `inflow`
- `outflow`

Optional fields：

- `raw_description`：银行原始描述；可用于 bank raw signal，但不是普通 entity identity authority。
- `description`：兼容或展示用 canonical description；本节点不能依赖它替代 bank raw signal。
- `pattern_source`：兼容字段；可为 `null`。
- `currency`
- `receipt_refs`
- `cheque_info_refs`
- `statement_line_ref`
- `counterparty_surface_text`
- `objective_tags`

Validation / rejection rules：

- `amount_abs` 必须为正数；不得用 signed amount 重复表达 direction。
- `direction` 必须显式给出，不能从金额正负号推断。
- `evidence_refs` 不能为空。
- `bank_account` 必须存在；否则本节点不能判断 bank-account structural relation。
- `description = null` 和 `pattern_source = null` 是有效状态；本节点不能要求 canonical description。
- `raw_description` 缺失时，涉及 bank-raw-signal 的结构匹配不能完成，但非 bank-raw-signal 的 stable profile relation 仍可在证据足够时被评估。

Runtime-only vs durable references：

- 客观字段来自 current transaction record。
- `transaction_id` 和 `evidence_refs` 是 durable references。
- `raw_description` 是 evidence surface，不是 durable profile fact。

### 3.3 `upstream_workflow_context`

Purpose：说明上游 gate 是否已完成，以及哪些上游问题必须限制本节点输出。

Source authority：Evidence Intake / Preprocessing、Transaction Identity、workflow orchestrator。

Required fields：

| Field | Meaning | Authority |
| --- | --- | --- |
| `evidence_status` | evidence foundation 状态 | Evidence Intake |
| `transaction_identity_status` | transaction identity 状态 | Transaction Identity Node |
| `duplicate_status` | duplicate / same-transaction 判断状态 | Transaction Identity Node |
| `already_entered_entity_workflow` | 当前交易是否已进入 entity-first workflow | workflow runtime |

Allowed `evidence_status` values：

- `ready`
- `blocked`

Allowed `transaction_identity_status` values：

- `assigned`
- `blocked`

Allowed `duplicate_status` values：

- `not_duplicate`
- `duplicate_blocked`
- `duplicate_warning`

Optional fields：

- `upstream_issue_flags`
- `identity_issue_refs`
- `evidence_issue_refs`
- `accountant_context_refs`
- `profile_context_refs`

Validation / rejection rules：

- `evidence_status != ready` 时，本节点不能输出 `structural_handled`。
- `transaction_identity_status != assigned` 时，本节点输入无效。
- `duplicate_status = duplicate_blocked` 时，本节点不能继续当前交易 structural handling。
- `already_entered_entity_workflow = true` 时，本节点输入无效；本节点不能在普通 entity / rule / case path 后回头吸收下游职责。
- `upstream_issue_flags` 可以限制输出，但不能单独支持 structural handled。

Runtime-only vs durable references：

- 该对象是 runtime handoff。
- issue refs 如存在，是 durable logs 或 current batch issue 的引用；本节点不能修改它们。

### 3.4 `profile_structural_snapshot`

Purpose：提供当前客户 `Profile` 中可支持 structural handling 的 stable structural facts。

Source authority：`Profile`。只有 accountant / governance / approved onboarding authority 已确认的事实可以支持 `structural_handled`。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `client_id` | 当前客户标识 | Profile / client context | durable reference |
| `profile_version_ref` | profile snapshot 或版本引用 | Profile | durable reference |
| `as_of` | snapshot 生效时间 | Profile / workflow runtime | runtime |
| `bank_accounts` | 已确认客户银行账户列表 | Profile | runtime view over durable facts |
| `structural_facts` | 已确认结构事实列表 | Profile | runtime view over durable facts |
| `authority_context` | profile fact authority / confirmation context | Profile / Governance / Review | runtime view over durable refs |

Each `bank_account` required fields：

| Field | Meaning | Authority |
| --- | --- | --- |
| `bank_account_id` | profile 中的银行账户标识 | Profile |
| `display_name` | 展示名称 | Profile |
| `account_status` | 账户状态 | Profile |
| `control_account_ref` | 对应 COA bank/control account reference | Profile / approved COA context |
| `authority_status` | 账户事实确认状态 | Profile / Governance |

Allowed `account_status` values：

- `active`
- `inactive`
- `archived`

Each `structural_fact` required fields：

| Field | Meaning | Authority |
| --- | --- | --- |
| `profile_fact_id` | profile structural fact 唯一引用 | Profile |
| `structural_type` | 结构事实类型 | Profile |
| `authority_status` | 该 fact 的 authority 状态 | Profile / Governance |
| `effective_status` | 该 fact 当前是否可用 | Profile |
| `evidence_refs` | 支撑该 fact 的证据或 approval references | Evidence / Review / Governance |
| `structural_match_conditions` | 已批准的结构匹配条件 | Profile |
| `structural_accounting_basis` | downstream JE 所需的 approved accounting / profile reference | Profile / approved COA / tax context |

Allowed `structural_type` values：

- `internal_transfer_relationship`
- `known_loan_repayment_relationship`
- `confirmed_bank_account_relationship`
- `other_confirmed_profile_structural_fact`

Allowed `authority_status` values：

- `accountant_confirmed`
- `governance_approved`
- `approved_onboarding_import`
- `candidate`
- `unconfirmed`
- `rejected`

Allowed `effective_status` values：

- `active`
- `inactive`
- `archived`
- `conflicted`

Optional fields：

- `tax_config_refs`
- `loan_account_refs`
- `related_bank_account_refs`
- `profile_risk_flags`
- `governance_constraint_refs`
- `profile_notes_refs`

Validation / rejection rules：

- Only `authority_status in {accountant_confirmed, governance_approved, approved_onboarding_import}` and `effective_status = active` can support `structural_handled`.
- `candidate`、`unconfirmed`、`rejected`、`conflicted`、`inactive` 或 `archived` facts 不能支持 `structural_handled`。
- `other_confirmed_profile_structural_fact` 只能在 `Profile` 已经保存 approved structural accounting basis 时使用；不能作为普通 vendor/entity 分类的兜底桶。
- `structural_accounting_basis` 缺失时，不能输出 finalizable `structural_handled_result`，但可以输出 review / pending / issue context。
- `Knowledge Log / Summary Log` 摘要不能填充 `authority_context`。

Runtime-only vs durable references：

- snapshot 是 runtime read view。
- profile facts、profile version、evidence refs 和 governance refs 是 durable references。
- 本节点不能修改 snapshot 或将 candidate fact 写回 `Profile`。

### 3.5 `bank_raw_signal_basis`

Purpose：提供当前交易的银行原始信号，用于 internal transfer 或类似 bank-raw-signal structural relation 判断。

Source authority：`Evidence Log`、Evidence Intake / Preprocessing。

Required when present：

| Field | Meaning | Authority |
| --- | --- | --- |
| `raw_description` | 银行原始描述或近原始描述 | Evidence Log |
| `source_evidence_ref` | 原始银行行或 statement evidence ref | Evidence Log |

Optional fields：

- `bank_counterparty_text`
- `bank_reference_number`
- `bank_trace_id`
- `paired_statement_line_refs`
- `raw_direction_marker`
- `raw_account_marker`
- `raw_signal_quality`

Allowed `raw_signal_quality` values：

- `strong`
- `usable`
- `weak`
- `conflicting`
- `missing`

Validation / rejection rules：

- `bank_raw_signal_basis` 只能支持 stable profile fact 已授权的 structural relation matching。
- `raw_description` 或 paired raw markers 不能单独创建 internal transfer relationship。
- `description` / canonical pattern 不能替代 `raw_description` 作为 bank-raw-signal authority。
- `raw_signal_quality in {weak, conflicting, missing}` 时，不能单独支持 `structural_handled`。

Runtime-only vs durable references：

- raw signal object 是 runtime-only。
- `source_evidence_ref` 和 paired evidence refs 是 durable references。
- raw signal 可被 candidate signal 引用，但不能由本节点写入 stable profile truth。

### 3.6 `structural_candidate_issue_context`

Purpose：表达当前交易暴露的 profile candidate、missing fact、conflict 或 accountant-context issue，供本节点决定是否输出 pending / review / candidate signal。

Source authority：upstream evidence / identity flow、current batch accountant context、onboarding candidate reference、prior unresolved review context。

Optional fields：

- `profile_fact_candidates`
- `missing_profile_fact_signals`
- `profile_conflict_signals`
- `unconfirmed_accountant_context_refs`
- `onboarding_candidate_refs`
- `prior_profile_issue_refs`

Each candidate / issue recommended fields：

| Field | Meaning | Authority |
| --- | --- | --- |
| `signal_id` | runtime signal 标识 | workflow runtime |
| `signal_type` | signal 类型 | source node / workflow |
| `reason` | 为什么该 signal 与当前交易有关 | source node / workflow |
| `evidence_refs` | 支撑 signal 的 evidence references | Evidence Log / source |
| `authority_status` | candidate / unconfirmed / conflicted / approved 等来源状态 | source authority |

Allowed `signal_type` values：

- `internal_transfer_relationship_candidate`
- `loan_relationship_candidate`
- `missing_bank_account_relationship`
- `profile_fact_conflict`
- `profile_fact_missing`
- `evidence_clarification_needed`
- `governance_review_candidate`

Validation / rejection rules：

- Candidate / issue context 可以支持 `structural_pending`、`structural_review_needed` 或 candidate signal。
- Candidate / issue context 不能支持 `structural_handled`，除非同一 profile fact 已在 `profile_structural_snapshot` 中以 approved authority 出现。
- accountant context ref 若未被 review / governance 确认，不能被当作 stable profile truth。

Runtime-only vs durable references：

- issue context 是 runtime-only。
- evidence refs、review refs、onboarding refs 如存在，是 durable references。
- 本节点只能转发或组织 signal，不能把 signal 变成 durable approval。

## 4. Output Contracts

### 4.1 `profile_structural_match_result`

Purpose：本节点的单次 runtime output envelope，表达当前交易的 structural gate 结果。

Consumer / downstream authority：workflow orchestrator、Entity Resolution、Coordinator / Pending、Review、Governance Review、JE Generation。该 result 自身不写 durable memory。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `transaction_id` | 当前交易稳定身份 | Transaction Identity Node | durable reference |
| `client_id` | 当前客户标识 | input request | durable reference |
| `structural_match_status` | structural gate 结果 | Profile / Structural Match Node | runtime |
| `reason` | 简短可读说明 | Profile / Structural Match Node | runtime |
| `evidence_refs` | 支撑结果的 evidence references | Evidence Log / input | durable references |
| `authority_trace` | 使用了哪些 profile facts / authority refs | Profile / Governance / Review refs | runtime trace over durable refs |

Allowed `structural_match_status` values：

- `structural_handled`
- `non_structural_handoff`
- `structural_pending`
- `structural_review_needed`
- `input_invalid`

Required by status：

- `structural_handled` requires `structural_handled_result`。
- `non_structural_handoff` requires `non_structural_entity_resolution_handoff`。
- `structural_pending` requires `structural_pending_handoff`。
- `structural_review_needed` requires at least one `structural_issue_signal` or `profile_governance_candidate_signal`。
- `input_invalid` requires `invalid_reason` and must not produce downstream automation handoff。

Optional fields：

- `structural_issue_signals`
- `profile_governance_candidate_signals`
- `request_trace`
- `diagnostic_notes`

Validation rules：

- Exactly one primary status must be present.
- `structural_handled` cannot coexist with `non_structural_entity_resolution_handoff` as an active route.
- `structural_pending` / `structural_review_needed` cannot be disguised as ordinary `non_structural_handoff` if the blocking issue is profile authority or structural conflict.
- `input_invalid` is a contract failure status, not a normal business route.
- `authority_trace` must not cite `Transaction Log`, `Case Log`, `Rule Log` or `Knowledge Log / Summary Log` as runtime structural authority.

Memory boundary：

- Entire result is runtime-only unless downstream Transaction Logging / Review / Governance workflow later records a final result or approved governance event.
- 本节点不能持久化该 result。

### 4.2 `structural_handled_result`

Purpose：表达当前交易已由 stable profile structural fact 完成 structural path，并提供 downstream JE / review / logging flow 可引用的 approved structural basis。

Consumer / downstream authority：JE Generation Node、Review flow、final audit flow。它是 runtime structural outcome，不是 Transaction Log write。

Required fields：

| Field | Meaning | Authority |
| --- | --- | --- |
| `structural_result_id` | runtime result 标识 | workflow runtime |
| `structural_type` | 本次命中的结构交易类型 | Profile structural fact |
| `matched_profile_fact_id` | 命中的 stable profile fact | Profile |
| `matched_profile_fact_authority` | fact 的 authority 状态 | Profile / Governance / Review |
| `structural_accounting_basis` | downstream JE 所需的 approved profile / COA / tax references | Profile / approved COA / tax context |
| `matched_evidence_refs` | 支撑当前交易落入该 fact 的 evidence refs | Evidence Log |
| `structural_rationale` | 为什么可由 profile structural path 处理 | Profile / Structural Match Node |

Allowed `structural_type` values：

- `internal_transfer`
- `known_loan_repayment`
- `confirmed_bank_account_structural_transaction`
- `other_confirmed_profile_structural_transaction`

Allowed `matched_profile_fact_authority` values：

- `accountant_confirmed`
- `governance_approved`
- `approved_onboarding_import`

Optional fields：

- `related_bank_account_refs`
- `loan_account_refs`
- `counterparty_bank_account_ref`
- `tax_config_refs`
- `structural_limit_notes`
- `review_visibility_hint`

Validation rules：

- `matched_profile_fact_id` must refer to an `active` stable profile fact in `profile_structural_snapshot`。
- `matched_profile_fact_authority` cannot be `candidate`、`unconfirmed`、`rejected`、`conflicted`、`inactive` 或 `archived`。
- `matched_evidence_refs` must include evidence supporting this transaction, not only the historical evidence that created the profile fact。
- `structural_accounting_basis` must be an approved reference, not a newly inferred ordinary classification。
- `other_confirmed_profile_structural_transaction` must not be used to bypass Entity Resolution for normal vendor / payee / counterparty transactions。
- This output must not contain final JE lines; JE computation belongs to JE Generation Node。

Durable memory / candidate boundary：

- Runtime-only structural outcome.
- Does not write `Transaction Log`.
- Does not update `Profile`.
- May be included later in final Transaction Log only through Transaction Logging Node after downstream finalization.

### 4.3 `non_structural_entity_resolution_handoff`

Purpose：把未被 structural path 完成且不存在 profile-blocking issue 的交易交给 `Entity Resolution Node`。

Consumer / downstream authority：`Entity Resolution Node`。该 handoff 只说明 profile structural gate 已放行，不说明 entity 是否已知。

Required fields：

| Field | Meaning | Authority |
| --- | --- | --- |
| `transaction_id` | 稳定交易身份 | Transaction Identity Node |
| `client_id` | 当前客户标识 | input request |
| `batch_id` | 当前批次 | workflow runtime |
| `objective_transaction_basis` | 客观交易基础 | Evidence Intake |
| `evidence_refs` | evidence references | Evidence Log |
| `structural_match_status` | 必须为 `non_structural_handoff` | Profile / Structural Match Node |
| `structural_match_reason` | 为什么未由 profile structural path 完成 | Profile / Structural Match Node |

Optional fields：

- `upstream_issue_flags`
- `accountant_context_refs`
- `profile_context_refs`
- `non_blocking_structural_notes`

Validation rules：

- Cannot be produced if a stable profile fact was matched strongly enough for `structural_handled`。
- Cannot be produced if the current blocker is missing profile authority, profile conflict, or evidence needed to decide a likely structural transaction; those must use `structural_pending` or `structural_review_needed`。
- Must preserve evidence refs and objective transaction basis; cannot pass only a summary.
- Must not include entity_id, rule_id, case outcome, COA classification, HST/GST treatment, or JE lines.

Memory boundary：

- Runtime-only handoff.
- Does not write durable memory.

### 4.4 `structural_pending_handoff`

Purpose：表达当前交易可能属于 structural transaction，但缺少可补 evidence、accountant confirmation 或 stable profile fact，不能安全完成。

Consumer / downstream authority：`Coordinator / Pending Node`、Review flow。该 handoff 支持聚焦提问，不是 profile approval。

Required fields：

| Field | Meaning | Authority |
| --- | --- | --- |
| `transaction_id` | 当前交易身份 | Transaction Identity Node |
| `pending_reason` | 为什么需要 pending | Profile / Structural Match Node |
| `pending_category` | pending 类型 | Profile / Structural Match Node |
| `question_focus` | 下游应向 accountant 或 evidence flow 聚焦的问题 | Profile / Structural Match Node |
| `evidence_refs` | 支撑 pending 的 evidence refs | Evidence Log |

Allowed `pending_category` values：

- `missing_profile_confirmation`
- `missing_evidence`
- `unclear_internal_transfer_pairing`
- `unconfirmed_loan_relationship`
- `bank_account_relationship_missing`
- `identity_or_duplicate_dependency`

Optional fields：

- `candidate_profile_fact_refs`
- `suggested_accountant_question`
- `blocking_profile_fields`
- `related_transaction_refs`
- `profile_context_refs`

Validation rules：

- `structural_pending_handoff` cannot contain a stable profile mutation instruction。
- `suggested_accountant_question` is advisory;本节点不自行提问、不自行批准回答。
- If the issue is a durable profile conflict rather than missing information, use `structural_review_needed` instead。
- Candidate refs cannot be used by this node to complete the current transaction。

Memory boundary：

- Runtime-only pending handoff.
- Accountant answer may later become durable only through Review / Governance / Profile update authority path.

### 4.5 `structural_issue_signal`

Purpose：表达本节点发现的 structural issue、profile gap 或 evidence conflict，供 downstream review / governance / lint / pending flow 使用。

Consumer / downstream authority：Coordinator、Review、Governance Review、Post-Batch Lint、Case Memory Update as candidate context。该 signal 不是 durable approval。

Required fields：

| Field | Meaning | Authority |
| --- | --- | --- |
| `signal_id` | runtime signal 标识 | workflow runtime |
| `signal_type` | issue 类型 | Profile / Structural Match Node |
| `severity` | 当前交易处理风险等级 | Profile / Structural Match Node |
| `reason` | 可读原因 | Profile / Structural Match Node |
| `evidence_refs` | supporting evidence refs | Evidence Log |

Allowed `signal_type` values：

- `missing_profile_fact_issue`
- `profile_conflict_issue`
- `bank_account_relationship_issue`
- `internal_transfer_pairing_issue`
- `loan_relationship_issue`
- `profile_authority_issue`
- `evidence_structural_conflict`

Allowed `severity` values：

- `info`
- `warning`
- `blocking`

Optional fields：

- `related_profile_fact_ids`
- `candidate_profile_fact_refs`
- `related_transaction_refs`
- `recommended_downstream_owner`

Allowed `recommended_downstream_owner` values：

- `coordinator_pending`
- `review_node`
- `governance_review`
- `post_batch_lint`

Validation rules：

- Blocking issue cannot be paired with active `non_structural_handoff` unless the blocker is explicitly non-structural and safe to ignore for entity workflow。
- Signal cannot update Profile or Governance Log by itself。
- Signal must include evidence or authority refs sufficient for downstream review; pure model assertion is invalid。

Memory boundary：

- Runtime-only issue signal.
- May become durable only if later written by the appropriate downstream log / governance process.

### 4.6 `profile_governance_candidate_signal`

Purpose：表达可能需要长期 profile / governance review 的候选变化。

Consumer / downstream authority：Review Node、Governance Review Node、Profile update workflow。该 signal 不是 approval，也不是 durable profile write。

Required fields：

| Field | Meaning | Authority |
| --- | --- | --- |
| `candidate_id` | runtime candidate 标识 | workflow runtime |
| `candidate_type` | 候选类型 | Profile / Structural Match Node |
| `reason` | 为什么提出候选 | Profile / Structural Match Node |
| `evidence_refs` | supporting evidence refs | Evidence Log |
| `requires_accountant_or_governance_approval` | 必须为 true | authority boundary |

Allowed `candidate_type` values：

- `profile_fact_candidate`
- `internal_transfer_relationship_candidate`
- `loan_relationship_candidate`
- `bank_account_relationship_candidate`
- `profile_fact_correction_candidate`
- `profile_conflict_review_candidate`

Optional fields：

- `proposed_profile_fact_shape`
- `related_profile_fact_ids`
- `related_transaction_refs`
- `authority_gap`
- `risk_notes`

Validation rules：

- `requires_accountant_or_governance_approval` must be `true`。
- `proposed_profile_fact_shape` is candidate-only and cannot be treated as stable profile schema or write instruction。
- Candidate cannot support `structural_handled` for the current transaction。
- Candidate cannot create Entity / Case / Rule authority。

Memory boundary：

- Runtime-only candidate.
- Can become durable only after accountant / governance approval through the proper Profile / Governance authority path.

## 5. Field Authority and Memory Boundary

### 5.1 Source of Truth for Important Fields

- `transaction_id`：source of truth 是 `Transaction Identity Node` / identity registry；本节点只引用。
- `amount_abs`、`direction`、`transaction_date`、`bank_account`、`raw_description`、`evidence_refs`：source of truth 是 Evidence Intake / Evidence Log；本节点只消费。
- `client_id`、`batch_id`：source of truth 是 workflow / client context。
- `Profile` structural facts、bank accounts、loan relationships、internal transfer relationships、tax/profile config：source of truth 是 `Profile`，并受 accountant / governance authority 控制。
- `profile_fact_id`、`authority_status`、`effective_status`、`structural_accounting_basis`：source of truth 是 `Profile` projection over approved Review / Governance / onboarding-import authority。
- `structural_match_status`、`reason`、runtime issue / candidate signals：source of truth 是本节点的 runtime result；它们不是 durable memory。

### 5.2 Fields That Can Never Become Durable Memory by This Node

本节点绝不能把以下字段直接写成长记忆：

- `structural_match_status`
- `reason`
- `request_trace`
- `diagnostic_notes`
- `bank_raw_signal_basis`
- `structural_pending_handoff`
- `structural_issue_signal`
- `profile_governance_candidate_signal`
- `proposed_profile_fact_shape`
- any LLM explanation or messy-evidence interpretation
- any candidate relationship inferred from current transaction

这些字段最多可被后续 Review / Governance / Transaction Logging flow 引用或转写；写入权不在本节点。

### 5.3 Fields That Can Become Durable Only After Accountant / Governance Approval

以下内容只有经过 accountant / governance / approved Profile update path 后，才可能成为 durable `Profile` 或 `Governance Log` authority：

- 新 bank account relationship
- internal transfer relationship
- loan relationship
- profile fact correction
- profile conflict resolution
- structural matching condition change
- structural accounting basis change
- tax/profile config change

本节点可以提出 candidate signal，但 candidate signal 本身不能支持当前交易的 structural handled path，也不能放宽未来 automation。

### 5.4 Audit vs Learning / Logging Boundary

- `Transaction Log` 是 audit-facing final record，不参与本节点 runtime decision。
- 本节点不写 `Transaction Log`；后续 finalization / JE / logging flow 才决定如何记录最终处理结果。
- Issue / candidate signals 不是 learning layer，不能直接进入 `Case Log`、`Rule Log` 或 `Profile`。
- 当前交易若由 structural path 完成，其 final audit trace 可以 later include matched profile fact and evidence refs，但这不是本节点直接写日志。
- Runtime structural candidate 不得污染 rule promotion、case memory 或 entity authority。

## 6. Validation Rules

### 6.1 Contract-Level Validation Rules

- 输入必须绑定同一 `client_id`、稳定 `transaction_id` 和至少一个 `evidence_ref`。
- `amount_abs` 必须是绝对值；`direction` 必须显式使用 `inflow` / `outflow`。
- `Profile` snapshot 只能作为 read-only view。
- `structural_handled` 只能基于 active stable profile fact。
- Candidate、unconfirmed、conflicted、inactive、archived 或 rejected profile facts 不能支持 `structural_handled`。
- Bank raw signal 只能在 stable profile fact 允许的结构关系内使用。
- `Transaction Log`、`Case Log`、`Rule Log`、`Entity Log`、`Knowledge Log / Summary Log` 不能成为本节点 structural authority。
- Output 必须只有一个 active primary route。

### 6.2 Conditions That Make the Input Invalid

输入无效条件包括：

- 缺少 `transaction_id`、`client_id`、`transaction_basis`、`evidence_refs` 或 `profile_structural_snapshot`。
- `transaction_basis.client_id` 与 `profile_structural_snapshot.client_id` 不一致。
- evidence intake 未 ready。
- transaction identity 未 assigned。
- duplicate 已 blocked。
- 当前交易已经进入 entity-first workflow 后又回到本节点。
- profile snapshot 不能表明相关 structural facts 的 authority / effective status。
- request 试图把 candidate context、raw bank signal、LLM explanation 或 summary log 当成 stable profile authority。

### 6.3 Conditions That Make the Output Invalid

输出无效条件包括：

- `structural_handled` 缺少 `structural_handled_result`。
- `structural_handled_result` 引用 candidate / unconfirmed / conflicted / inactive / archived profile fact。
- `structural_handled_result` 缺少 current transaction evidence refs。
- `structural_handled_result` 包含 final JE lines 或普通 vendor/entity classification。
- `non_structural_entity_resolution_handoff` 在存在 profile-authority blocker 或 structural conflict 时被输出。
- `structural_pending_handoff` 包含 profile write instruction 或 accountant approval。
- `profile_governance_candidate_signal.requires_accountant_or_governance_approval != true`。
- result 同时声明 active `structural_handled` 和 active `non_structural_handoff`。
- output 直接写入或声称写入 `Profile`、`Transaction Log`、`Entity Log`、`Case Log`、`Rule Log` 或 `Governance Log`。

### 6.4 Stop / Ask Conditions for Unresolved Contract Authority

后续设计或实现遇到以下情况必须停下问产品 / spec authority，不能自行补：

- 需要新增 stable profile fact authority category。
- 需要把 `other_confirmed_profile_structural_fact` 扩展成新的 structural transaction type。
- 需要决定 profile candidate 到 stable profile truth 的具体审批 workflow。
- 需要决定 accountant 回答后是否重触发本节点，以及重触发范围。
- 需要冻结 structural handled path 与 JE Generation 的完整 accounting outcome schema。
- 需要让本节点读取 Transaction Log、Case Log、Rule Log 或 Knowledge Summary 做 runtime decision。

## 7. Examples

### 7.1 Valid Minimal Example：非结构性交易放行到 Entity Resolution

```json
{
  "profile_structural_match_result": {
    "transaction_id": "txn_01HXSTRUCT001",
    "client_id": "client_abc",
    "structural_match_status": "non_structural_handoff",
    "reason": "No active Profile structural fact applies to this transaction.",
    "evidence_refs": ["ev_stmt_1001"],
    "authority_trace": [],
    "non_structural_entity_resolution_handoff": {
      "transaction_id": "txn_01HXSTRUCT001",
      "client_id": "client_abc",
      "batch_id": "batch_2026_05",
      "objective_transaction_basis": {
        "amount_abs": "42.15",
        "direction": "outflow",
        "bank_account": "bank_rbc_chequing",
        "transaction_date": "2026-05-01"
      },
      "evidence_refs": ["ev_stmt_1001"],
      "structural_match_status": "non_structural_handoff",
      "structural_match_reason": "No profile-backed structural relation matched."
    }
  }
}
```

Reason valid：

- stable profile structural match 不存在；
- 没有 profile authority blocker；
- handoff 不声称 entity、rule、case 或 accounting classification。

### 7.2 Valid Richer Example：已确认内部转账结构性处理

```json
{
  "profile_structural_match_result": {
    "transaction_id": "txn_01HXSTRUCT002",
    "client_id": "client_abc",
    "structural_match_status": "structural_handled",
    "reason": "Transaction matches an active accountant-confirmed internal transfer relationship.",
    "evidence_refs": ["ev_stmt_2001", "ev_stmt_2002"],
    "authority_trace": [
      {
        "profile_fact_id": "pf_internal_transfer_rbc_savings",
        "authority_status": "accountant_confirmed",
        "profile_version_ref": "profile_v17"
      }
    ],
    "structural_handled_result": {
      "structural_result_id": "psm_result_002",
      "structural_type": "internal_transfer",
      "matched_profile_fact_id": "pf_internal_transfer_rbc_savings",
      "matched_profile_fact_authority": "accountant_confirmed",
      "structural_accounting_basis": {
        "source_bank_account_ref": "bank_rbc_chequing",
        "target_bank_account_ref": "bank_rbc_savings",
        "source_control_account_ref": "coa_1000",
        "target_control_account_ref": "coa_1010"
      },
      "matched_evidence_refs": ["ev_stmt_2001", "ev_stmt_2002"],
      "structural_rationale": "Bank raw signals and paired statement evidence fall inside the approved internal-transfer relationship."
    }
  }
}
```

Reason valid：

- matched fact 是 active stable profile fact；
- current transaction evidence refs 与 profile authority trace 都存在；
- output 提供 JE 所需 approved structural basis，但不生成 JE lines。

### 7.3 Invalid Example：用 candidate relationship 完成结构性处理

```json
{
  "profile_structural_match_result": {
    "transaction_id": "txn_01HXSTRUCT003",
    "client_id": "client_abc",
    "structural_match_status": "structural_handled",
    "reason": "Looks like a loan repayment based on memo text.",
    "evidence_refs": ["ev_stmt_3001"],
    "authority_trace": [
      {
        "profile_fact_id": "pf_candidate_loan_xyz",
        "authority_status": "candidate"
      }
    ],
    "structural_handled_result": {
      "structural_result_id": "psm_result_003",
      "structural_type": "known_loan_repayment",
      "matched_profile_fact_id": "pf_candidate_loan_xyz",
      "matched_profile_fact_authority": "candidate",
      "structural_accounting_basis": {
        "loan_account_ref": "coa_2300"
      },
      "matched_evidence_refs": ["ev_stmt_3001"],
      "structural_rationale": "Memo says loan payment."
    }
  }
}
```

Invalid reason：

- `candidate` profile fact 不能支持 `structural_handled`；
- memo / raw bank signal 不能创建 stable loan relationship；
- 正确输出应是 `structural_pending` 或 `structural_review_needed`，并生成 candidate / issue signal。

## 8. Open Contract Boundaries

- Stable profile fact 的 exact authority categories 仍未由 active docs 全局冻结。本文件只为本节点定义最小可用 authority labels；未来若 Profile 全局 contract 收敛，应以全局 contract 为准并回填本文件。
- `other_confirmed_profile_structural_fact` 的具体子类型未冻结。它只能表示已经由 `Profile` 明确保存 approved structural accounting basis 的结构事实，不能被实现层扩展成普通交易分类兜底。
- `structural_handled_result` 与 JE Generation Node 的完整 accounting outcome handoff 仍需后续跨节点收敛。本文件只要求提供 approved structural accounting basis，不定义 JE lines 或完整 finalizable outcome schema。
- profile candidate 到 stable profile truth 的 confirmation workflow 未冻结；本节点只输出 candidate signal。
- accountant 补充确认后是否重新触发本节点、如何限制重跑边界，仍未冻结。
- profile conflict 的人工处理与 Governance Review 的 exact event schema 未在本节点冻结。

## 9. Self-Review

- 已读取 required live repo docs：`AGENTS.md`、`TASK_STATE.md`、`PLANS.md`、`CLAUDE.md`、`DECISIONS.md`、`supporting documents/communication_preferences.md`、`supporting documents/development_workflow.md`、`supporting documents/node_design_roadmap.md`、`new system/new_system.md`。
- 已读取 prior approved stage docs：`profile_structural_match_node__stage_1__functional_intent.md`、`profile_structural_match_node__stage_2__logic_and_boundaries.md`。
- 已读取可用 Superpowers docs：`using-superpowers/SKILL.md`、`brainstorming/SKILL.md`；project workflow skill `ai-bookkeeper-node-design-facilitation` 在当前环境不存在，因此按 runner instruction 使用 repo `supporting documents/node_design_roadmap.md` 与本节点 Stage 1/2 docs 作为 workflow authority。
- 已使用 Stage 3 boundary：本文只定义 data contracts、field authority、runtime / durable boundary、validation rules 和 compact examples。
- 无 Stage 4/5/6/7 creep：未定义执行算法、技术实现地图、测试矩阵、fixture plan 或 coding-agent task contract。
- 未发明 unsupported product authority：对未冻结的 profile authority category、JE handoff、candidate approval workflow、retrigger behavior 和 governance event schema 均记录为 Open Contract Boundaries。
- 本次未编辑 `new_system.md`、Stage 1/2 docs、governance docs 或 legacy specs；若未 blocked，仅写入目标 Stage 3 文件。
