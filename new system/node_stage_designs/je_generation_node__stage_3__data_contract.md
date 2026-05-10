# JE Generation Node — Stage 3：Data Contract Spec

## 1. Stage 范围

本 Stage 3 只定义 `JE Generation Node` 的 implementation-facing data contracts。

前置设计依据是：

- `new system/node_stage_designs/je_generation_node__stage_1__functional_intent.md`
- `new system/node_stage_designs/je_generation_node__stage_2__logic_and_boundaries.md`

本文件把 Stage 1/2 已批准的 pure journal-entry computation、authority boundary、tax / account consistency boundary 和 no-memory-mutation boundary 转换为输入对象、输出对象、字段含义、字段 authority、runtime-only / durable reference 边界和 validation rules。

本文件不定义：

- step-by-step execution algorithm 或 branch sequence
- repo module path、class、API、storage engine、DB migration 或代码布局
- test matrix、fixture plan 或 coding-agent task contract
- 全局 shared accounting classification schema
- Review / Coordinator / Transaction Logging 的完整 routing state machine
- 新 product authority、legacy replacement mapping 或历史 spec 迁移关系

## 2. Contract Position in Workflow

`JE Generation Node` 位于：

```text
finalizable current transaction outcome
→ JE Generation Node
→ journal entry result / JE-blocked handoff
→ Transaction Logging Node / Review / Coordinator / Governance Review / output flow
```

### 2.1 Upstream handoff consumed

本节点消费一个 runtime `je_generation_request`。

上游必须已经完成或明确给出：

- objective transaction basis；
- stable `transaction_id`；
- 当前交易的 accounting outcome；
- account basis；
- tax treatment basis；
- authority / review basis；
- audit-support references。

典型上游来源包括 structural result、approved rule result、case-supported runtime result、pending clarification 后的可继续结果、accountant-approved result 或 accountant-corrected result。

本节点不决定哪些 upstream path 可以绕过逐笔 Review。Stage 3 只要求：进入本节点的 request 必须显式携带 `finalization_authority_basis`，并且该 basis 足以支持当前交易生成 JE。

### 2.2 Downstream handoff produced

本节点输出一个 runtime `je_generation_result`。

下游按结果类别消费：

- `Transaction Logging Node`：消费 `journal_entry_result`、JE rationale 和 authority trace，用于 final audit logging；它才负责写 `Transaction Log`。
- `Review Node` / `Coordinator / Pending Node`：消费 `je_blocked_handoff` 或 `consistency_issue_signal`，处理缺失、冲突、review-required 或 accountant clarification。
- `Governance Review Node`：只可消费 candidate-only governance / configuration signal。
- output flow：可消费已生成的 journal entry result；不能把 output artifact 当作 durable memory。

### 2.3 Logs / memory stores read

本节点可以读取或消费：

- `Evidence Log` references；
- objective transaction record / transaction identity；
- upstream finalizable outcome；
- approved account basis / customer COA context；
- approved tax treatment basis / customer tax config；
- review / intervention context that establishes current authority；
- upstream rationale and authority trace；
- `Profile` 中与 bank account、tax config 或 structural transaction 有关的稳定配置引用。

本节点不能把 `Transaction Log` 当作 runtime decision source。`Transaction Log` 是 audit-facing，只写和查询，不参与当前 JE decision，也不是 learning layer。

本节点可以携带 Entity / Case / Rule / Governance context 的 reference 或 summary，但只能用于 authority trace、blocked reason 或 candidate signal，不能重新执行 entity resolution、case judgment、rule match 或 governance approval。

### 2.4 Logs / memory stores written or candidate-only

本节点不直接写入任何 durable log / memory store。

它不能写：

- `Transaction Log`
- `Case Log`
- `Rule Log`
- `Entity Log`
- `Governance Log`
- `Knowledge Log / Summary Log`
- `Profile`
- COA / tax config / automation policy

本节点只可以输出 candidate-only signals，例如：

- `account_mapping_review_candidate`
- `tax_configuration_review_candidate`
- `profile_structural_issue_candidate`
- `rule_condition_gap_candidate`
- `governance_review_candidate`

这些 signal 不是 durable approval，不改变当前交易 authority，也不能支持 rule match、rule promotion 或 long-term memory mutation。

## 3. Input Contracts

### 3.1 `je_generation_request`

Purpose：本节点的单次 runtime input envelope。

Source authority：workflow orchestrator / upstream handoff。它汇总上游已形成的 runtime facts、approved outcome references 和 authority basis；它自身不创造 product authority。

Required fields：

- `transaction_basis`
- `finalizable_accounting_outcome`
- `account_mapping_basis`
- `tax_treatment_basis`
- `finalization_authority_basis`
- `audit_support_context`

Optional fields：

- `complex_treatment_basis`
- `effective_governance_constraints`
- `request_trace`

Validation / rejection rules：

- 缺少 `transaction_basis.transaction_id` 时，input invalid。
- 缺少 `finalizable_accounting_outcome.outcome_status` 时，input invalid。
- `finalization_authority_basis.finalization_status != finalizable` 时，不得生成 JE。
- 如果 request 只包含 candidate signal、review draft、pending context、governance candidate 或 unapproved proposal，不得生成 JE。
- `request_trace` 只能用于 runtime diagnostics，不能成为 account、tax 或 authority source。

Runtime-only vs durable references：

- `je_generation_request` 是 runtime-only envelope。
- `transaction_id`、`evidence_refs`、`rule_id`、`entity_id`、review refs、governance refs、COA refs、tax config refs 是 durable references；它们不表示本节点拥有写入权。

### 3.2 `transaction_basis`

Purpose：描述当前交易的客观金额、方向、日期、银行账户和证据基础，用于 JE amount line 计算和 traceability binding。

Source authority：Evidence Intake / Preprocessing Node、Transaction Identity Node、Evidence Log、Profile 中的 bank account context。

Required fields：

- `transaction_id`：稳定交易 ID。
- `transaction_date`
- `amount_abs`：绝对值金额。
- `direction`；allowed values: `inflow`, `outflow`。
- `bank_account`
- `currency`
- `evidence_refs`：至少一个 evidence reference。

Optional fields：

- `raw_description`
- `description`
- `pattern_source`
- `receipt_refs`
- `cheque_info_refs`
- `import_batch_id`
- `bank_account_control_account_ref`

Validation / rejection rules：

- `amount_abs` 必须为正数；金额正负号不能重复表达 direction。
- `direction` 必须显式给出，不能从 signed amount 推断。
- `currency` 缺失时不得生成 final JE，除非上游 shared transaction contract 已明确默认货币。
- `evidence_refs` 不能为空。
- `description = null` 和 `pattern_source = null` 是有效状态；本节点不能要求 canonical description。
- 如果 `bank_account_control_account_ref` 缺失，必须能从 approved Profile / COA context 追溯到客户侧银行账户对应的会计科目，否则 JE blocked。

Runtime-only vs durable references：

- 客观字段来自 current transaction record。
- `evidence_refs` 是 durable evidence references。
- `bank_account_control_account_ref` 是 COA / Profile reference；本节点不能创建或修改该 mapping。

### 3.3 `finalizable_accounting_outcome`

Purpose：表达当前交易已经由上游形成的 accounting outcome，本节点只把它转换成 journal entry，不重新判断分类。

Source authority：Profile / Structural Match、Rule Match、Case Judgment 后续 authority path、Coordinator / Pending 后的 clarification result、Review Node accountant approval / correction，或其他 active baseline 允许的 upstream finalization source。

Required fields：

- `outcome_id`
- `outcome_source_type`
- `outcome_status`
- `accounting_treatment_ref`
- `primary_account_ref`
- `classification_summary`
- `tax_treatment_ref`
- `source_evidence_refs`

Allowed `outcome_source_type` values：

- `profile_structural_result`
- `approved_rule_result`
- `case_supported_result`
- `pending_clarification_resolved`
- `accountant_review_approved`
- `accountant_review_corrected`

Allowed `outcome_status` values：

- `finalizable`
- `pending`
- `review_required`
- `not_approved`
- `governance_blocked`
- `conflicting`
- `candidate_only`

Optional fields：

- `entity_ref`
- `rule_ref`
- `case_refs_used`
- `review_decision_ref`
- `intervention_refs`
- `accountant_correction_ref`
- `upstream_rationale`
- `confidence_label`
- `classification_basis`

Validation / rejection rules：

- 只有 `outcome_status = finalizable` 可以支持 normal JE generation。
- `case_supported_result` 只有在 `finalization_authority_basis` 明确允许当前交易 operational finalization 时才可支持 JE；本节点不能把 Case Judgment recommendation 当作 accountant approval。
- `candidate_only`、`review_required`、`pending`、`not_approved`、`governance_blocked` 或 `conflicting` 不能支持 JE。
- `primary_account_ref` 必须来自 approved accounting outcome、approved rule、accountant correction、structural mapping 或 approved COA context；不能由本节点推断。
- `classification_summary` 只是 human-readable summary，不能替代 `primary_account_ref` 或 `accounting_treatment_ref`。

Runtime-only vs durable references：

- 该对象是 runtime handoff。
- 其中的 refs 可以指向 durable sources，但本节点不能把 outcome 写入 `Case Log`、`Rule Log`、`Entity Log` 或 `Transaction Log`。

### 3.4 `account_mapping_basis`

Purpose：提供生成 JE lines 所需的 approved account references。

Source authority：approved accounting outcome、customer COA / accounting configuration、Profile structural context、approved Rule Log record 或 accountant correction。

Required fields：

- `primary_account_ref`
- `bank_account_control_account_ref`
- `account_mapping_authority`
- `account_refs_source`

Optional fields：

- `receivable_or_payable_account_ref`
- `clearing_account_ref`
- `contra_account_ref`
- `split_account_refs`
- `account_mapping_notes`

Allowed `account_mapping_authority` values：

- `profile_structural_mapping`
- `approved_rule_mapping`
- `accountant_review_mapping`
- `accountant_correction_mapping`
- `approved_coa_config`

Validation / rejection rules：

- `primary_account_ref` 与 `finalizable_accounting_outcome.primary_account_ref` 必须一致，或必须有 accountant correction / approved mapping 解释差异。
- `bank_account_control_account_ref` 必须能绑定到 `transaction_basis.bank_account`。
- 如果 outcome 需要 split / multi-line classification，必须提供 `split_account_refs` 或等价 approved account basis；否则 JE blocked。
- 本节点不能创建 COA account、选择 fallback account、合并 account 或把 unmatched account name 当作 approved account reference。

Runtime-only vs durable references：

- Account refs 指向 durable COA / Profile / rule / review authority。
- 本节点只读这些 references；不能修改 account mapping。

### 3.5 `tax_treatment_basis`

Purpose：提供生成 tax lines 与核对 gross / net / tax relationship 所需的 approved tax basis。

Source authority：approved accounting outcome、customer tax config、approved rule、structural logic、accountant review / correction，或 Profile 中已确认的 tax config。

Required fields：

- `tax_treatment_status`
- `tax_authority_source`
- `tax_amount_basis`
- `tax_control_treatment`

Allowed `tax_treatment_status` values：

- `not_applicable`
- `taxable`
- `exempt`
- `zero_rated`
- `out_of_scope`
- `reverse_charge_or_special`
- `unresolved`
- `conflicting`

Required fields inside `tax_amount_basis`：

- `basis_type`; allowed values: `tax_included`, `tax_excluded`, `explicit_tax_amount`, `no_tax`
- `gross_amount`
- `net_amount`
- `tax_amount`
- `tax_rate_ref`

Allowed `tax_control_treatment` values：

- `none`
- `HST_GST_Receivable`
- `HST_GST_Payable`
- `approved_special_tax_control`

Optional fields：

- `jurisdiction`
- `tax_config_ref`
- `receipt_tax_refs`
- `tax_explanation`
- `tax_review_requirement`

Validation / rejection rules：

- `tax_treatment_status = unresolved` 或 `conflicting` 时不得生成 JE。
- `tax_amount_basis` 的 `gross_amount` 必须与 `transaction_basis.amount_abs` 一致，除非 `complex_treatment_basis` 明确解释 split / partial-tax / foreign-currency basis。
- `net_amount + tax_amount` 必须等于 `gross_amount`，允许的 rounding policy 留给后续 shared contract；本节点不能静默吸收 material difference。
- `tax_control_treatment = HST_GST_Receivable` 或 `HST_GST_Payable` 时，必须能追溯到 approved tax config / accountant decision / approved rule。
- 本节点不能自行判断 taxable、exempt、zero-rated、ITC eligibility、tax rate 或 tax control account。

Runtime-only vs durable references：

- Tax basis 是 runtime handoff + durable tax config / evidence references。
- 本节点不能修改 tax config，也不能把 tax calculation outcome 写成长期 tax policy。

### 3.6 `finalization_authority_basis`

Purpose：定义当前 outcome 是否可以进入 JE 的 authority 上限，防止本节点把 pending / review-required / candidate-only 内容推进为 JE。

Source authority：upstream workflow authority trace、automation policy、rule lifecycle、review decision、accountant correction、pending resolution、governance restriction。

Required fields：

- `finalization_status`
- `authority_source_type`
- `authority_refs`
- `review_requirement_status`
- `governance_block_status`

Allowed `finalization_status` values：

- `finalizable`
- `not_finalizable`
- `requires_review`
- `requires_pending_clarification`
- `governance_blocked`
- `invalid`

Allowed `authority_source_type` values：

- `structural_authority`
- `approved_rule_authority`
- `case_operational_authority`
- `accountant_review_approval`
- `accountant_correction`
- `resolved_pending_context`

Allowed `review_requirement_status` values：

- `not_required_by_current_authority`
- `already_approved`
- `required_not_completed`
- `rejected`
- `ambiguous`

Allowed `governance_block_status` values：

- `none`
- `active_block`
- `approval_required`
- `conflict_unresolved`

Optional fields：

- `automation_policy_snapshot`
- `rule_lifecycle_snapshot`
- `review_decision_ref`
- `intervention_resolution_ref`
- `governance_constraint_refs`
- `authority_notes`

Validation / rejection rules：

- `finalization_status` 必须为 `finalizable` 才能生成 JE。
- `review_requirement_status = required_not_completed`、`rejected` 或 `ambiguous` 时不得生成 JE。
- `governance_block_status != none` 时不得生成 JE。
- `case_operational_authority` 不能自动等同 accountant approval；是否可进入 JE 必须由 upstream authority context 明确表达。
- 模糊 accountant answer 不能作为 `accountant_review_approval` 或 `accountant_correction`。

Runtime-only vs durable references：

- Authority envelope 是 runtime-only。
- Accountant decision、rule approval、governance event 等 refs 指向 durable authority source；本节点不创建或修改它们。

### 3.7 `audit_support_context`

Purpose：保留后续 `Transaction Logging Node` 和 output flow 需要的 traceability context。

Source authority：上游 workflow handoff、Evidence Log references、review / intervention records、rule / case / entity / governance references、JE calculation context。

Required fields：

- `transaction_id`
- `source_evidence_refs`
- `upstream_path_trace`
- `authority_trace_refs`

Optional fields：

- `entity_refs`
- `rule_refs`
- `case_refs`
- `review_refs`
- `intervention_refs`
- `governance_refs`
- `policy_trace_refs`
- `audit_note_seed`

Validation / rejection rules：

- `audit_support_context.transaction_id` 必须等于 `transaction_basis.transaction_id`。
- `source_evidence_refs` 不能为空，且必须覆盖生成 outcome 所依赖的关键 evidence。
- `upstream_path_trace` 只能说明路径，不得成为新的 accounting authority。
- 不能把 `Transaction Log` history 作为当前 JE authority trace。

Runtime-only vs durable references：

- 该对象是 runtime audit handoff。
- 它可被 `Transaction Logging Node` 用于 durable audit record，但本节点不写 durable log。

### 3.8 `complex_treatment_basis`

Purpose：在上游已经批准复杂会计处理时，表达 split、refund、reversal、multi-line、partial-tax、foreign-currency 或 special tax treatment 的最低 contract basis。

Source authority：approved accounting outcome、accountant correction、approved rule、approved structural treatment 或 active product docs 后续冻结的 shared contract。

Required when applicable：

- `complex_treatment_type`
- `approved_line_basis_refs`
- `amount_allocation_basis`
- `authority_refs`

Allowed `complex_treatment_type` values：

- `split`
- `refund`
- `reversal`
- `multi_line`
- `partial_tax`
- `foreign_currency`
- `special_tax`

Optional fields：

- `original_transaction_ref`
- `fx_rate_basis`
- `allocation_notes`
- `rounding_basis`

Validation / rejection rules：

- 如果当前交易显然需要复杂处理，但缺少 approved `complex_treatment_basis`，不得生成 JE。
- `refund` / `reversal` 必须能引用原始交易或 approved reversal basis；不能仅凭负数金额推断。
- `foreign_currency` 必须有 approved currency / FX basis；本节点不能自行选择汇率。
- `split` / `partial_tax` 必须有 approved amount allocation；本节点不能用 LLM 或 fallback 比例补齐。

Runtime-only vs durable references：

- `complex_treatment_basis` 是 runtime handoff。
- 其中的 references 可指向 durable transaction、review、rule 或 evidence records；本节点不修改这些 records。

## 4. Output Contracts

### 4.1 `je_generation_result`

Purpose：本节点对当前交易的 JE generation outcome envelope。

Consumer / downstream authority：Transaction Logging Node、Review Node、Coordinator / Pending Node、Governance Review Node、output flow。下游必须按 `status` 和 authority boundary 使用结果。

Required fields：

- `transaction_id`
- `status`
- `result_reason`
- `memory_write_effect`

Allowed `status` values：

- `journal_entry_generated`
- `je_blocked`
- `consistency_issue`
- `invalid_input`

Conditionally required fields：

- `journal_entry_result`：当 `status = journal_entry_generated` 时 required。
- `je_blocked_handoff`：当 `status = je_blocked` 时 required。
- `consistency_issue_signal`：当 `status = consistency_issue` 时 required。
- `invalid_input_errors`：当 `status = invalid_input` 时 required。

Optional fields：

- `candidate_signals`
- `audit_support_handoff`
- `runtime_trace`

Allowed `memory_write_effect` value：

- `none`

Validation rules：

- `transaction_id` 必须等于 input transaction_id。
- `journal_entry_generated` 必须有 balanced `journal_entry_result`。
- `je_blocked` 和 `consistency_issue` 不得同时携带 finalized journal entry。
- `candidate_signals` 不能改变当前 status，也不能作为 JE authority。
- `memory_write_effect` 必须为 `none`。

Durable memory effect：

- runtime-only output。
- 本节点不写 `Transaction Log`；下游可记录其结果作为 audit input。

### 4.2 `journal_entry_result`

Purpose：当前 finalizable accounting outcome 被转换后的 journal entry payload。

Consumer / downstream authority：Transaction Logging Node、output flow、Review Node 的审阅语境。它是 JE computation result，不是 accountant approval，也不是 durable audit write。

Required fields：

- `journal_entry_id`
- `transaction_id`
- `entry_date`
- `currency`
- `source_outcome_ref`
- `finalization_authority_refs`
- `je_lines`
- `debit_total`
- `credit_total`
- `balance_status`
- `tax_summary`

Allowed `balance_status` values：

- `balanced`

Validation rules：

- `debit_total` 必须等于 `credit_total`。
- `balance_status` 只能在实际借贷平衡时为 `balanced`。
- `entry_date` 默认应等于 `transaction_basis.transaction_date`，除非上游 approved accounting treatment 明确另有 posting date basis。
- `source_outcome_ref` 必须绑定到 `finalizable_accounting_outcome.outcome_id`。
- `finalization_authority_refs` 不能为空。
- `je_lines` 至少两行；每行只能有 debit 或 credit 一边有金额。

Durable memory effect：

- runtime-only JE result。
- 只有 Transaction Logging Node 或后续 output / accounting export flow 可以消费；本节点不落盘。

### 4.3 `je_line`

Purpose：journal entry 的单条借贷行。

Consumer / downstream authority：Transaction Logging Node、output flow、review display。

Required fields per line：

- `line_id`
- `account_ref`
- `debit_credit`; allowed values: `debit`, `credit`。
- `amount`
- `line_role`
- `source_basis_ref`

Allowed `line_role` values：

- `bank_control`
- `primary_accounting`
- `tax_control`
- `receivable_or_payable`
- `clearing_or_special`

Optional fields per line：

- `account_display_name`
- `tax_component`
- `allocation_ref`
- `line_note`

Validation rules：

- `amount` 必须为正数。
- `account_ref` 必须来自 approved account basis；不能是 free-text account name。
- `tax_control` line 必须对应 `tax_treatment_basis.tax_control_treatment`。
- `clearing_or_special` line 只能在 upstream approved `complex_treatment_basis` 或 approved special accounting outcome 中出现。
- 本节点不能为了平衡分录而发明 `clearing_or_special` line。

Durable memory effect：

- JE line 是 runtime computed output。
- 它可以被 audit logging 或 export 保存，但本节点不直接写 durable store。

### 4.4 `tax_summary`

Purpose：说明 JE result 中 tax treatment 如何体现在分录行中。

Consumer / downstream authority：Transaction Logging Node、review / output flow。

Required fields：

- `tax_treatment_status`
- `tax_control_treatment`
- `gross_amount`
- `net_amount`
- `tax_amount`
- `tax_line_ids`

Optional fields：

- `tax_rate_ref`
- `tax_config_ref`
- `rounding_note`

Validation rules：

- `tax_summary` 必须与 input `tax_treatment_basis` 一致。
- `tax_line_ids` 必须引用实际存在的 `je_lines`；`tax_control_treatment = none` 时应为空。
- `tax_amount = 0` 时不得生成非零 tax control line。
- `HST_GST_Receivable` / `HST_GST_Payable` 必须分别对应 approved tax control account basis。

Durable memory effect：

- runtime-only calculation summary。
- 不能成为 future tax policy 或 rule source。

### 4.5 `je_blocked_handoff`

Purpose：说明当前交易不能安全生成 JE 的原因。

Consumer / downstream authority：Review Node、Coordinator / Pending Node、upstream workflow、Governance Review Node。

Required fields：

- `blocked_reason`
- `blocking_basis`
- `required_resolution_path`
- `why_je_generation_cannot_override`

Allowed `blocked_reason` values：

- `outcome_not_finalizable`
- `authority_insufficient`
- `review_required_unresolved`
- `governance_block`
- `missing_account_basis`
- `conflicting_account_basis`
- `missing_tax_basis`
- `conflicting_tax_basis`
- `missing_amount_direction_basis`
- `unsupported_complex_treatment`
- `traceability_missing`

Allowed `required_resolution_path` values：

- `upstream_rework`
- `coordinator_pending`
- `review_node`
- `governance_review_node`
- `tax_or_coa_configuration_review`

Optional fields：

- `missing_fields`
- `conflicting_refs`
- `suggested_review_focus`
- `candidate_signal_refs`

Validation rules：

- Blocked handoff 不能包含 generated JE。
- 如果原因是 authority / governance，不得伪装成 ordinary missing field。
- `suggested_review_focus` 只能聚焦问题，不能替 accountant 作答。

Durable memory effect：

- runtime-only handoff。
- 它可以被后续记录为 audit / intervention context，但本节点不写 log。

### 4.6 `consistency_issue_signal`

Purpose：表达输入 basis 看似存在，但在 JE consistency validation 中发现冲突或不一致。

Consumer / downstream authority：Review Node、Coordinator、Transaction Logging Node blocking context、Governance Review candidate review。

Required fields：

- `issue_type`
- `issue_summary`
- `affected_refs`
- `required_resolution_path`

Allowed `issue_type` values：

- `debit_credit_not_balanced`
- `gross_net_tax_mismatch`
- `direction_vs_entry_conflict`
- `account_basis_conflict`
- `tax_basis_conflict`
- `authority_trace_conflict`
- `transaction_binding_conflict`

Optional fields：

- `calculation_snapshot`
- `candidate_signals`
- `review_note`

Validation rules：

- Consistency issue 不能自行修正 upstream outcome。
- 不能用 adjustment line、rounding line、fallback account 或 fallback tax treatment 消除 material conflict，除非这些处理已由 upstream authority 明确批准。
- `calculation_snapshot` 只能解释问题，不能作为 durable accounting result。

Durable memory effect：

- runtime-only issue signal。
- 若暗示长期配置问题，只能形成 candidate signal，不能直接写 memory。

### 4.7 `candidate_signals`

Purpose：表达 JE generation 暴露出的长期配置、governance 或 upstream contract 候选问题。

Consumer / downstream authority：Review Node、Governance Review Node、Post-Batch Lint Node、relevant owner workflow。

Required fields per signal：

- `signal_type`
- `signal_reason`
- `source_refs`
- `requires_authority_path`

Allowed `signal_type` values：

- `account_mapping_review_candidate`
- `tax_configuration_review_candidate`
- `profile_structural_issue_candidate`
- `rule_condition_gap_candidate`
- `governance_review_candidate`
- `upstream_contract_gap_candidate`

Allowed `requires_authority_path` values：

- `review_node`
- `governance_review_node`
- `profile_or_coa_owner_workflow`
- `tax_config_owner_workflow`
- `rule_governance_workflow`

Optional fields：

- `related_account_refs`
- `related_tax_refs`
- `related_rule_refs`
- `related_profile_refs`
- `suggested_review_focus`

Validation rules：

- signal 不能包含 `approval_status = approved`。
- signal 不能改变 `Profile`、COA、tax config、Rule Log、Entity Log、Case Log 或 Governance Log。
- signal 不能支持当前交易 JE generation。

Durable memory effect：

- candidate-only。
- 长期化只能通过 accountant / governance approval 或对应 owner workflow。

## 5. Field Authority and Memory Boundary

### 5.1 Source of truth for important fields

- `transaction_id`：Transaction Identity Node / transaction identity layer。
- `amount_abs`、`direction`、`transaction_date`、`bank_account`、`currency`：Evidence Intake / Preprocessing 后的 transaction record；`direction` 是方向 source of truth，金额保持 absolute value。
- `evidence_refs`：Evidence Log。
- `bank_account_control_account_ref`：Profile / approved COA account mapping。
- `primary_account_ref`：approved accounting outcome、approved rule、accountant correction、structural mapping 或 approved COA context。
- `tax_treatment_status`、`tax_rate_ref`、`tax_control_treatment`：approved accounting outcome、customer tax config、approved rule、structural logic 或 accountant decision。
- `HST_GST_Receivable` / `HST_GST_Payable`：当前 canonical GST/HST control-account treatment names；实际 account ref 必须来自 approved COA / tax config mapping。
- `finalization_authority_basis`：upstream authority trace、review decision、rule approval、governance restriction 或 accountant correction。
- `journal_entry_result`：本节点 runtime computation output。
- `Transaction Log`：audit-facing final log；只写和查询，不参与本节点 runtime decision。

### 5.2 Fields that can never become durable memory by this node

以下字段或对象不能由本节点直接成为 durable memory：

- `je_generation_request`
- `je_generation_result`
- `journal_entry_result`
- `je_lines`
- `tax_summary`
- `je_blocked_handoff`
- `consistency_issue_signal`
- `candidate_signals`
- `runtime_trace`
- `calculation_snapshot`
- 任何 LLM / natural-language explanation

这些内容最多可以被 downstream Transaction Logging Node 作为 audit input 保存，或被 Review / Coordinator / Governance workflow 作为 handoff context 使用。

### 5.3 Fields that can become durable only after accountant / governance approval

以下信息只有经过对应 authority path 才可能长期化：

- account mapping change：必须经 accountant / COA owner workflow / governance approval。
- tax config or control-account treatment change：必须经 accountant / tax config owner workflow / governance approval。
- rule condition gap or rule correction：必须经 accountant / governance approval 后才可改变 `Rule Log`。
- Profile structural issue：必须经 Profile owner workflow 和必要 accountant confirmation。
- current transaction final audit record：只能由 `Transaction Logging Node` 写入 `Transaction Log`。
- completed case memory：只能由 `Case Memory Update Node` 在完成交易且具备 learning authority 后写入 `Case Log`。

### 5.4 Audit vs learning / logging boundary

`journal_entry_result` 可以成为 audit-support input，但它不是 durable audit log。

`Transaction Log` 保存每笔交易最终处理结果和审计轨迹；它只写和查询，不参与 runtime decision，也不是 learning layer。

JE generation 暴露的 account / tax / rule / profile 问题只能作为 candidate signal 交给后续 workflow。它不能直接污染 Case Log、Rule Log、Entity Log、Profile、Governance Log 或 Knowledge Summary。

## 6. Validation Rules

### 6.1 Contract-level validation rules

- 每个 input / output 必须绑定同一个 `transaction_id`。
- 只有 `outcome_status = finalizable` 且 `finalization_status = finalizable` 的 request 可以输出 `journal_entry_generated`。
- `review_requirement_status`、`governance_block_status` 和 effective governance constraints 不能被 JE computation 覆盖。
- 金额必须使用 `amount_abs + direction` 语义，不能混用 signed amount。
- JE output 必须借贷平衡。
- Tax line 必须与 approved tax basis 一致。
- Account refs 必须来自 approved account basis；不能使用 free-text fallback。
- `Transaction Log` 不能作为 runtime JE decision source。
- `memory_write_effect` 必须为 `none`。

### 6.2 Conditions that make the input invalid

- 缺少 `transaction_id`。
- 缺少 `amount_abs`、`direction`、`currency`、`bank_account` 或必要 evidence refs。
- `amount_abs <= 0`，且没有上游 approved zero / reversal treatment。
- `direction` 不是 `inflow` 或 `outflow`。
- 缺少 `finalizable_accounting_outcome.outcome_status`。
- 缺少 approved `primary_account_ref` 或 bank account control account mapping。
- tax basis unresolved / conflicting。
- request 要求本节点选择 COA、判断 tax treatment、approve review、写 Transaction Log 或修改 long-term memory。
- 把 candidate signal、review draft、pending context、governance candidate 或 Transaction Log history 当作 finalization authority。

### 6.3 Conditions that make the output invalid

- `status = journal_entry_generated` 但缺少 `journal_entry_result`。
- `journal_entry_result` 借贷不平衡。
- JE line 使用 free-text account name 或未授权 account ref。
- Tax line 与 approved tax treatment 不一致。
- JE result 在 pending、review-required、not-approved、governance-blocked 或 conflicting context 下生成。
- `je_blocked_handoff` 同时携带 finalized JE。
- candidate signal 声称已 approved、confirmed、promoted、applied 或 written。
- 输出声称本节点已写入 `Transaction Log`、`Case Log`、`Rule Log`、`Entity Log`、`Governance Log`、`Knowledge Log`、Profile、COA 或 tax config。

### 6.4 Stop / ask conditions for unresolved contract authority

后续 Stage 或实现中如遇到以下情况，应 stop and ask，不得自行补 product authority：

- 需要决定哪些 high-confidence structural / rule / case-supported result 可以不经逐笔 accountant review 直接进入 JE。
- 需要冻结全局 shared accounting treatment / JE-ready schema。
- 需要定义 split、refund、reversal、partial-tax、foreign-currency 或 special tax 的完整 algorithm。
- 需要允许 fallback / suspense / clearing account 用于缺失 account 或 tax basis。
- 需要决定 JE-blocked 是否也形成 terminal audit record，以及由哪个节点写。
- 需要改变 `Transaction Log` 是否参与 runtime decision。
- 需要允许 JE Generation 写 long-term memory、Profile、COA、tax config、Governance Log 或 Transaction Log。

## 7. Examples

### 7.1 Valid minimal example

```json
{
  "input": {
    "transaction_basis": {
      "transaction_id": "txn_01JEG0001",
      "transaction_date": "2026-04-30",
      "amount_abs": "113.00",
      "direction": "outflow",
      "bank_account": "operating_chequing",
      "currency": "CAD",
      "evidence_refs": ["ev_bank_001", "ev_receipt_001"],
      "bank_account_control_account_ref": "coa_1000_operating_chequing"
    },
    "finalizable_accounting_outcome": {
      "outcome_id": "out_rule_001",
      "outcome_source_type": "approved_rule_result",
      "outcome_status": "finalizable",
      "accounting_treatment_ref": "rule_treatment_001",
      "primary_account_ref": "coa_5600_office_supplies",
      "classification_summary": "Office supplies",
      "tax_treatment_ref": "tax_basis_001",
      "source_evidence_refs": ["ev_bank_001", "ev_receipt_001"]
    },
    "account_mapping_basis": {
      "primary_account_ref": "coa_5600_office_supplies",
      "bank_account_control_account_ref": "coa_1000_operating_chequing",
      "account_mapping_authority": "approved_rule_mapping",
      "account_refs_source": "rule_approved_001"
    },
    "tax_treatment_basis": {
      "tax_treatment_status": "taxable",
      "tax_authority_source": "approved_rule_mapping",
      "tax_amount_basis": {
        "basis_type": "tax_included",
        "gross_amount": "113.00",
        "net_amount": "100.00",
        "tax_amount": "13.00",
        "tax_rate_ref": "tax_hst_13"
      },
      "tax_control_treatment": "HST_GST_Receivable"
    },
    "finalization_authority_basis": {
      "finalization_status": "finalizable",
      "authority_source_type": "approved_rule_authority",
      "authority_refs": ["rule_approved_001"],
      "review_requirement_status": "not_required_by_current_authority",
      "governance_block_status": "none"
    },
    "audit_support_context": {
      "transaction_id": "txn_01JEG0001",
      "source_evidence_refs": ["ev_bank_001", "ev_receipt_001"],
      "upstream_path_trace": ["rule_match:rule_handled"],
      "authority_trace_refs": ["rule_approved_001"]
    }
  },
  "output": {
    "transaction_id": "txn_01JEG0001",
    "status": "journal_entry_generated",
    "result_reason": "approved taxable outflow treatment converted to balanced JE",
    "memory_write_effect": "none",
    "journal_entry_result": {
      "journal_entry_id": "je_txn_01JEG0001",
      "transaction_id": "txn_01JEG0001",
      "entry_date": "2026-04-30",
      "currency": "CAD",
      "source_outcome_ref": "out_rule_001",
      "finalization_authority_refs": ["rule_approved_001"],
      "je_lines": [
        {"line_id": "je_line_001", "account_ref": "coa_5600_office_supplies", "debit_credit": "debit", "amount": "100.00", "line_role": "primary_accounting", "source_basis_ref": "rule_treatment_001"},
        {"line_id": "je_line_002", "account_ref": "coa_2200_hst_gst_receivable", "debit_credit": "debit", "amount": "13.00", "line_role": "tax_control", "source_basis_ref": "tax_basis_001"},
        {"line_id": "je_line_003", "account_ref": "coa_1000_operating_chequing", "debit_credit": "credit", "amount": "113.00", "line_role": "bank_control", "source_basis_ref": "txn_01JEG0001"}
      ],
      "debit_total": "113.00",
      "credit_total": "113.00",
      "balance_status": "balanced",
      "tax_summary": {
        "tax_treatment_status": "taxable",
        "tax_control_treatment": "HST_GST_Receivable",
        "gross_amount": "113.00",
        "net_amount": "100.00",
        "tax_amount": "13.00",
        "tax_line_ids": ["je_line_002"]
      }
    }
  }
}
```

### 7.2 Valid richer example

```json
{
  "input": {
    "transaction_basis": {
      "transaction_id": "txn_01JEG0002",
      "transaction_date": "2026-04-30",
      "amount_abs": "226.00",
      "direction": "inflow",
      "bank_account": "operating_chequing",
      "currency": "CAD",
      "evidence_refs": ["ev_bank_010", "ev_invoice_010"],
      "bank_account_control_account_ref": "coa_1000_operating_chequing"
    },
    "finalizable_accounting_outcome": {
      "outcome_id": "out_review_010",
      "outcome_source_type": "accountant_review_corrected",
      "outcome_status": "finalizable",
      "accounting_treatment_ref": "review_treatment_010",
      "primary_account_ref": "coa_4000_consulting_revenue",
      "classification_summary": "Consulting revenue corrected and approved by accountant",
      "tax_treatment_ref": "tax_basis_010",
      "source_evidence_refs": ["ev_bank_010", "ev_invoice_010"],
      "review_decision_ref": "review_decision_010"
    },
    "account_mapping_basis": {
      "primary_account_ref": "coa_4000_consulting_revenue",
      "bank_account_control_account_ref": "coa_1000_operating_chequing",
      "account_mapping_authority": "accountant_correction_mapping",
      "account_refs_source": "review_decision_010"
    },
    "tax_treatment_basis": {
      "tax_treatment_status": "taxable",
      "tax_authority_source": "accountant_correction",
      "tax_amount_basis": {
        "basis_type": "tax_included",
        "gross_amount": "226.00",
        "net_amount": "200.00",
        "tax_amount": "26.00",
        "tax_rate_ref": "tax_hst_13"
      },
      "tax_control_treatment": "HST_GST_Payable"
    },
    "finalization_authority_basis": {
      "finalization_status": "finalizable",
      "authority_source_type": "accountant_correction",
      "authority_refs": ["review_decision_010"],
      "review_requirement_status": "already_approved",
      "governance_block_status": "none"
    },
    "audit_support_context": {
      "transaction_id": "txn_01JEG0002",
      "source_evidence_refs": ["ev_bank_010", "ev_invoice_010"],
      "upstream_path_trace": ["review:accountant_corrected"],
      "authority_trace_refs": ["review_decision_010"]
    }
  },
  "output_summary": "DR bank 226.00; CR consulting revenue 200.00; CR HST/GST Payable 26.00; balanced; no memory write."
}
```

### 7.3 Invalid example

```json
{
  "input": {
    "transaction_basis": {
      "transaction_id": "txn_01JEG_BAD",
      "transaction_date": "2026-04-30",
      "amount_abs": "75.00",
      "direction": "outflow",
      "bank_account": "operating_chequing",
      "currency": "CAD",
      "evidence_refs": ["ev_bank_bad"]
    },
    "finalizable_accounting_outcome": {
      "outcome_id": "out_case_bad",
      "outcome_source_type": "case_supported_result",
      "outcome_status": "review_required",
      "accounting_treatment_ref": "case_proposal_bad",
      "primary_account_ref": "coa_5700_meals",
      "classification_summary": "Possible meals expense",
      "tax_treatment_ref": "tax_unresolved",
      "source_evidence_refs": ["ev_bank_bad"]
    },
    "finalization_authority_basis": {
      "finalization_status": "requires_review",
      "authority_source_type": "case_operational_authority",
      "authority_refs": ["case_judgment_bad"],
      "review_requirement_status": "required_not_completed",
      "governance_block_status": "none"
    }
  },
  "invalid_reason": "The outcome is review-required and tax basis is unresolved. JE Generation must return je_blocked, not journal_entry_generated."
}
```

## 8. Open Contract Boundaries

- 哪些 high-confidence structural / rule / case-supported result 可以不经逐笔 accountant review 直接进入 JE，当前仍未由 active docs 冻结。本文件只要求 upstream 明确提供 `finalization_authority_basis`。
- `approved_accounting_treatment` / `accounting_treatment_ref` 的全局 shared schema 仍需与 Rule Match、Case Judgment、Review、Transaction Logging 后续 contracts 对齐。
- split、refund、reversal、multi-line、partial-tax、foreign-currency、special tax 的完整 JE algorithm 和 rounding policy 尚未冻结；本文件只定义这类处理需要 approved `complex_treatment_basis`。
- JE-blocked handoff 的 exact routing 尚未冻结：可能回到 Coordinator、Review、upstream rework、tax / COA configuration review 或 Governance Review。
- JE-blocked / not-finalizable 是否需要 terminal audit record，以及是否由 Transaction Logging Node 记录，留给后续阶段。
- Canonical `journal_entry_id` 格式、line id 格式、amount decimal precision 和 rounding tolerance 尚未由 active docs 冻结。
- `tax_control_treatment` 的 account-role enum 是否应成为全局 tax contract，尚未最终决定。

## 9. Self-Review

- 已阅读 required repo docs：`AGENTS.md`、`TASK_STATE.md`、`PLANS.md`、`CLAUDE.md`、`DECISIONS.md`、`supporting documents/communication_preferences.md`、`supporting documents/development_workflow.md`、`supporting documents/node_design_roadmap.md`、`new system/new_system.md`。
- 已阅读 prior approved node docs：`je_generation_node__stage_1__functional_intent.md`、`je_generation_node__stage_2__logic_and_boundaries.md`。
- 已读取可用 Superpowers docs：`using-superpowers/SKILL.md`、`brainstorming/SKILL.md`；project workflow skill `ai-bookkeeper-node-design-facilitation` 在当前环境不存在，因此按 runner instruction 使用 repo `supporting documents/node_design_roadmap.md` 与本节点 Stage 1/2 docs 作为 workflow authority。
- 已注意 optional `supporting documents/node_design_roadmap_zh.md` 在工作树中缺失；未发明该文件。
- 本文只定义 Stage 3 data contract；没有进入 Stage 4 execution algorithm、Stage 5 technical implementation map、Stage 6 test matrix、Stage 7 coding-agent task contract。
- 本文没有把 `Transaction Log` 用作 runtime decision source，没有允许 JE Generation 写 durable memory。
- 本文没有发明 Review bypass 的产品 authority；相关问题保留在 Open Contract Boundaries。
- 若未 blocked，本次只写目标文件：`new system/node_stage_designs/je_generation_node__stage_3__data_contract.md`。
