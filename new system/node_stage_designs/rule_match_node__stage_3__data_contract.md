# Rule Match Node — Stage 3：Data Contract Spec

## 1. Stage 范围

本 Stage 3 只定义 `Rule Match Node` 的 implementation-facing data contracts。

前置设计依据是：

- `new system/node_stage_designs/rule_match_node__stage_1__functional_intent.md`
- `new system/node_stage_designs/rule_match_node__stage_2__logic_and_boundaries.md`

本文件把 Stage 1/2 已批准的行为边界转换为输入、输出、字段、authority、memory boundary 和 validation rules。

本文件不定义：

- step-by-step execution algorithm
- repo module path、class、API、storage engine、DB migration 或代码布局
- test matrix、fixture plan 或 coding-agent task contract
- Rule Log 的完整全局 schema
- JE Generation、Review、Transaction Logging 的完整下游 schema
- 新 product authority 或 legacy replacement mapping

## 2. Contract Position in Workflow

`Rule Match Node` 位于：

```text
Entity Resolution Node
→ Rule Match Node
→ Case Judgment Node / downstream review and logging flow
```

### 2.1 Upstream handoff consumed

本节点消费一个 runtime `rule_match_request`，由上游 workflow 在以下前提满足后传入：

- evidence intake / preprocessing 已形成客观交易基础；
- transaction identity 已分配稳定 `transaction_id`；
- profile / structural path 已确认没有完成本笔交易；
- Entity Resolution Node 已输出 `entity_resolution_output`；
- workflow 需要判断是否存在可直接执行的 approved active rule。

### 2.2 Downstream handoff produced

本节点输出一个 runtime `rule_match_result`。

下游读取该结果来判断：

- 是否已经完成 deterministic `rule_handled` path；
- 如果没有完成，原因是 `rule_miss`、`rule_blocked`、`review_required`、`governance_needed` 还是 `rule_conflict`；
- Case Judgment Node 是否可以继续 case-based judgment；
- Coordinator / Review / Governance Review 需要哪些聚焦 context。

### 2.3 Logs / memory stores read

本节点可以读取或消费：

- runtime evidence references；
- objective transaction basis；
- Entity Resolution output；
- `Entity Log` 中的 stable entity、approved aliases、confirmed roles、status、authority、automation_policy 和已生效 governance context；
- `Rule Log` 中的 approved active deterministic rules；
- `Governance Log` 中已经生效的 alias、role、rule、policy 限制；
- `Intervention Log` 中已经转化为治理状态或 review-required constraint 的相关语境。

本节点不能把 `Transaction Log`、`Case Log`、`Knowledge Log / Summary Log`、lint warning、recent intervention 或 repeated outcomes 当作 runtime rule authority。

### 2.4 Logs / memory stores written or candidate-only

本节点不直接写入任何 durable log / memory store。

它只可以输出 runtime candidate / issue signals，例如：

- `rule_candidate_signal`
- `rule_condition_gap_signal`
- `rule_conflict_signal`
- `rule_stale_or_unstable_signal`
- `entity_alias_role_authority_signal`
- `automation_policy_governance_signal`

这些 signal 不是 durable approval。是否进入 governance queue、是否写入长期 memory、是否批准 active rule change，属于 Review / Governance Review / memory update workflow。

## 3. Input Contracts

### 3.1 `rule_match_request`

Purpose：本节点的单次 runtime 输入 envelope。

Source authority：workflow orchestrator / upstream handoff。它只汇总上游已产生的 runtime facts 和 memory snapshots，不自行创建 product authority。

Required fields：

- `transaction_basis`
- `upstream_workflow_context`
- `entity_resolution_output`
- `entity_authority_snapshot`
- `automation_policy_snapshot`
- `rule_log_snapshot`

Optional fields：

- `effective_governance_constraints`
- `effective_intervention_constraints`
- `request_trace`

Validation / rejection rules：

- 缺少 `transaction_basis.transaction_id` 时，input invalid。
- 缺少 `entity_resolution_output.status` 时，input invalid。
- 如果 `upstream_workflow_context.structural_path_status = handled`，input invalid；本节点不能重跑已由 structural path 完成的交易。
- 如果 `rule_log_snapshot` 无法表明候选 rule 的 approval / active authority，不能输出 `rule_handled`。
- `request_trace` 只能用于 runtime diagnostics，不能作为 rule authority。

Runtime-only vs durable references：

- `rule_match_request` 是 runtime-only。
- 其中的 `transaction_id`、`evidence_refs`、`entity_id`、`rule_id`、governance references 是 durable objects 的引用，不表示本节点拥有写入权。

### 3.2 `transaction_basis`

Purpose：描述当前交易的客观事实，只支持 approved rule condition matching，不承载业务分类判断。

Source authority：Evidence Intake / Preprocessing Node、Transaction Identity Node，以及客观证据引用。

Required fields：

- `transaction_id`：稳定交易 ID。
- `amount_abs`：绝对值金额。
- `direction`：交易方向；allowed values: `inflow`, `outflow`。
- `transaction_date`
- `bank_account`
- `evidence_refs`：至少一个 evidence reference。

Optional fields：

- `raw_description`
- `description`
- `pattern_source`
- `receipt_refs`
- `cheque_info_refs`
- `counterparty_surface_text`
- `currency`
- `objective_tags`

Validation / rejection rules：

- `amount_abs` 必须为正数；金额符号不能与 `direction` 重复表达。
- `direction` 只能使用允许值；不能用 signed amount 推断 direction。
- `evidence_refs` 不能为空。
- `description = null` 是有效状态；本节点不能要求所有交易都有 canonical description。
- `pattern_source = null` 是有效状态；不能把 null 当作 fallback rule source。

Runtime-only vs durable references：

- 客观字段来自 durable evidence / transaction identity。
- `objective_tags` 若存在，只是 runtime helper，不能成为 rule authority，除非其来源是 approved rule condition 或客观 evidence fact。

### 3.3 `upstream_workflow_context`

Purpose：说明上游 workflow 已经完成哪些 gate，以及哪些上游限制必须被本节点尊重。

Source authority：Evidence Intake / Preprocessing、Transaction Identity、Profile / Structural Match、Entity Resolution 的 runtime handoff。

Required fields：

- `evidence_status`；allowed values: `ready`, `blocked`。
- `transaction_identity_status`；allowed values: `assigned`, `duplicate_blocked`, `blocked`。
- `structural_path_status`；allowed values: `not_structural`, `not_handled`, `handled`, `blocked`。
- `entity_resolution_completed`：boolean。

Optional fields：

- `upstream_blocking_reasons`
- `upstream_issue_signals`
- `profile_structural_reference`

Validation / rejection rules：

- `evidence_status != ready` 时，本节点不能输出 `rule_handled`。
- `transaction_identity_status != assigned` 时，本节点不能输出 `rule_handled`。
- `structural_path_status = handled` 时，本节点输入 invalid。
- `entity_resolution_completed != true` 时，本节点输入 invalid。
- `upstream_blocking_reasons` 不能被包装成 ordinary `rule_miss` 后继续自动化。

Runtime-only vs durable references：

- 该对象是 runtime handoff。
- `profile_structural_reference` 如存在，只能说明 structural gate 的结果或限制，不给本节点 profile mutation authority。

### 3.4 `entity_resolution_output`

Purpose：说明当前交易的 entity-resolution 状态和 authority context，是 rule eligibility 的核心前置输入。

Source authority：Entity Resolution Node runtime output，并引用 `Entity Log` authority。

Required fields：

- `status`；allowed values: `resolved_entity`, `resolved_entity_with_unconfirmed_role`, `new_entity_candidate`, `ambiguous_entity_candidates`, `unresolved`。
- `confidence`
- `reason`
- `evidence_used`

Conditionally required fields：

- `entity_id`：当 `status = resolved_entity` 或 `resolved_entity_with_unconfirmed_role` 时 required。
- `matched_alias`：当 rule eligibility 依赖 alias 时 required。
- `alias_status`：当 `matched_alias` 存在时 required；allowed values: `candidate_alias`, `approved_alias`, `rejected_alias`。
- `candidate_entities`：当 `status = ambiguous_entity_candidates` 时 required。
- `blocking_reason`：当 status 不能支持 deterministic automation 时 required。

Optional fields：

- `candidate_role`
- `matched_alias_evidence_ref`
- `identity_risk_flags`

Validation / rejection rules：

- `new_entity_candidate`、`ambiguous_entity_candidates`、`unresolved` 不能支持 `rule_handled`。
- `resolved_entity_with_unconfirmed_role` 不能支持需要 confirmed role/context 的 rule。
- `alias_status = candidate_alias` 不能支持 rule match。
- `alias_status = rejected_alias` 必须输出 blocked / review / governance context，不能输出 ordinary miss。
- `confidence` 只表示 entity resolution confidence，不能替代 alias、role、rule 或 accounting authority。

Runtime-only vs durable references：

- `entity_resolution_output` 是 runtime-only。
- `candidate_role` 是 runtime-only，不能由本节点写入 durable entity roles。
- `entity_id` 和 approved alias references 指向 `Entity Log`，但本节点没有修改权。

### 3.5 `entity_authority_snapshot`

Purpose：提供 `Entity Log` 中与 rule eligibility 相关的当前有效 authority。

Source authority：`Entity Log` + 已生效 governance events。

Required fields：

- `entity_id`
- `entity_status`；allowed values: `candidate`, `active`, `merged`, `archived`。
- `approved_aliases`
- `confirmed_roles`
- `authority`
- `automation_policy`

Optional fields：

- `display_name`
- `risk_flags`
- `governance_notes`
- `effective_governance_refs`
- `merged_into_entity_id`

Validation / rejection rules：

- `entity_status != active` 不能支持 `rule_handled`。
- `approved_aliases` 不包含当前 `matched_alias` 时，不能支持 `rule_handled`。
- rule 要求的 role/context 不在 `confirmed_roles` 中时，不能支持该 rule。
- `merged` entity 不能直接支持 rule match；必须经治理确认后的 active entity / rule authority。
- `authority` 不能缺失来源；无 authority metadata 的 entity snapshot 不能支持 `rule_handled`。

Runtime-only vs durable references：

- snapshot 是 runtime-only view。
- snapshot 字段来自 durable `Entity Log`，但本节点不能写入或修正它。

### 3.6 `automation_policy_snapshot`

Purpose：说明当前 entity/context 是否允许 rule-based automation。

Source authority：`Entity Log.automation_policy` + 已生效 governance policy changes。

Required fields：

- `entity_id`
- `policy`；allowed values: `eligible`, `case_allowed_but_no_promotion`, `rule_required`, `review_required`, `disabled`。
- `policy_source`

Optional fields：

- `effective_from`
- `reason`
- `governance_ref`

Validation / rejection rules：

- `eligible` 允许 rule-based automation。
- `rule_required` 允许 approved active rule 自动处理；没有适用 rule 时必须离开 deterministic path。
- `case_allowed_but_no_promotion` 是否允许 rule-based automation 不是由名称本身完全冻结；本节点必须按 effective policy metadata 判断。如果 metadata 未明确允许 rule-based automation，不能输出 `rule_handled`。
- `review_required` 或 `disabled` 不能输出 `rule_handled`。
- policy upgrade / relaxation 只能来自 accountant-approved governance，不能由本节点推断。

Runtime-only vs durable references：

- snapshot 是 runtime-only。
- `policy_source` 和 `governance_ref` 是 durable authority references。

### 3.7 `rule_log_snapshot`

Purpose：提供当前 entity / role / context 下可能适用的 approved deterministic rules。

Source authority：`Rule Log` 中 accountant / governance 已批准的 rule records，以及已生效 rule governance state。

Required fields：

- `rules`：rule-facing records list；可以为空。
- `snapshot_source`

Each `rule_record` required fields：

- `rule_id`
- `entity_id`
- `rule_status`；node-facing allowed values: `active`, `inactive`, `pending_approval`, `rejected`, `governance_blocked`, `review_required`。
- `approval_status`；allowed values: `approved`, `pending`, `rejected`。
- `authority_source`
- `applicability`
- `approved_condition_set`
- `approved_accounting_treatment`

Each `rule_record` optional fields：

- `rule_name`
- `version`
- `effective_from`
- `effective_until`
- `governance_refs`
- `review_notes`

`applicability` required fields：

- `entity_id`

`applicability` optional fields：

- `required_aliases`
- `required_roles`
- `required_context_tags`

`approved_condition_set` optional fields：

- `direction`
- `amount_range`
- `currency`
- `required_evidence_types`
- `excluded_evidence_types`
- `approved_exception_conditions`

`approved_accounting_treatment` required meaning：

- approved rule-owned accounting outcome payload to be forwarded when the rule is matched.
- It must include enough approved accounting authority for downstream classification / JE workflow, but the exact JE line schema belongs to JE Generation Stage 3.

Validation / rejection rules：

- 只有 `rule_status = active` 且 `approval_status = approved` 的 rule 可以支持 `rule_handled`。
- `authority_source` 缺失时，不能执行 rule。
- `applicability.entity_id` 必须与当前 active entity 一致。
- `required_aliases` 若存在，当前 `matched_alias` 必须是 approved alias 且包含在 required aliases 内。
- `required_roles` 若存在，当前 context 必须由 confirmed role 满足。
- `approved_condition_set` 只能使用 rule 已批准条件和 objective transaction facts；不能由本节点临时扩展。
- `approved_accounting_treatment` 不能由本节点重写。

Runtime-only vs durable references：

- `rule_log_snapshot` 是 runtime read view。
- `rule_record` 来自 durable `Rule Log`。
- 本节点不能新增、修改、降级、删除或 approve rule。

### 3.8 `effective_governance_constraints`

Purpose：提供已经生效、会影响 rule eligibility 的 governance constraints。

Source authority：`Governance Log` 中已批准或已生效的 governance events。

Required fields when present：

- `constraint_id`
- `constraint_type`；allowed values: `alias_restriction`, `role_restriction`, `rule_restriction`, `automation_policy_restriction`, `entity_lifecycle_restriction`。
- `applies_to`
- `effect`；allowed values: `block_rule_match`, `require_review`, `limit_rule_scope`。
- `authority_ref`

Optional fields：

- `reason`
- `effective_from`
- `expires_at`

Validation / rejection rules：

- `effect = block_rule_match` 时不能输出 `rule_handled`。
- `effect = require_review` 时不能输出 automatic final handling；可以输出 review-required context。
- pending / rejected governance proposal 不能作为 effective constraint，除非它已经通过其他 authority 改变了 rule、entity 或 automation-policy status。

Runtime-only vs durable references：

- constraints 是 runtime view of durable governance authority。
- 本节点不能写入 `Governance Log`。

### 3.9 `effective_intervention_constraints`

Purpose：只承载已经转化为治理状态或 review-required constraint 的 accountant intervention context。

Source authority：`Intervention Log` + Review / Governance workflow 已确认的 effective constraint。

Required fields when present：

- `intervention_ref`
- `constraint_type`；allowed values: `review_required`, `rule_suspended`, `policy_changed`, `role_or_alias_disputed`。
- `authority_ref`

Optional fields：

- `reason`
- `related_rule_ids`
- `related_entity_ids`

Validation / rejection rules：

- raw recent intervention 或 lint warning 不能直接改变 rule eligibility。
- 只有已经转化为 `rule_status`、`automation_policy`、effective governance constraint 或 review-required constraint 的 intervention 才能影响本节点输出。

Runtime-only vs durable references：

- 该对象是 runtime view。
- intervention 原文不成为 rule source。

## 4. Output Contracts

### 4.1 `rule_match_result`

Purpose：本节点对当前交易的 deterministic rule path 结果。

Consumer / downstream authority：Case Judgment Node、Coordinator / Pending Node、Review Node、JE Generation Node、Transaction Logging Node。下游只能按本字段表达的 authority 使用结果，不能把 candidate signal 当作 approval。

Required fields：

- `transaction_id`
- `status`
- `authority_summary`
- `result_reason`

Allowed `status` values：

- `rule_handled`
- `rule_miss`
- `rule_blocked`
- `review_required`
- `governance_needed`
- `rule_conflict`
- `invalid_input`

Conditionally required fields：

- `matched_rule`：当 `status = rule_handled` 时 required。
- `rule_output_payload`：当 `status = rule_handled` 时 required。
- `miss_context`：当 `status = rule_miss` 时 required。
- `blocked_context`：当 `status = rule_blocked` 时 required。
- `review_context`：当 `status = review_required` 时 required。
- `governance_context`：当 `status = governance_needed` 时 required。
- `conflict_context`：当 `status = rule_conflict` 时 required。
- `invalid_input_errors`：当 `status = invalid_input` 时 required。

Optional fields：

- `candidate_signals`
- `downstream_handoff_hint`
- `runtime_trace`

Validation rules：

- `status = rule_handled` 时必须能追溯到 active approved rule、active entity、approved alias、confirmed required role/context 和允许 rule-based automation 的 policy。
- `status = rule_miss` 不能包含 authority block；如果存在 authority block，应使用 `rule_blocked`、`review_required` 或 `governance_needed`。
- `runtime_trace` 不能包含 raw prompt trace 或未授权内部实现细节；它也不能成为 durable authority。

Durable memory boundary：

- `rule_match_result` 是 runtime output。
- 它可以被 downstream Transaction Logging Node 作为 audit input 保存，但本节点不写 `Transaction Log`。
- `candidate_signals` 只提出候选，不写 durable memory。

### 4.2 `matched_rule`

Purpose：说明被确定性执行的 rule authority。

Required fields：

- `rule_id`
- `rule_version`
- `entity_id`
- `authority_source`
- `matched_conditions`

Optional fields：

- `rule_name`
- `governance_refs`

Validation rules：

- `rule_id` 必须来自 `Rule Log`。
- `authority_source` 必须表示 accountant / governance approved authority。
- `matched_conditions` 只能记录实际满足的 approved rule conditions。

Memory boundary：

- `matched_rule` 是对 durable rule 的 runtime reference。
- 本节点不改变 rule record。

### 4.3 `rule_output_payload`

Purpose：把 approved rule-owned accounting outcome 交给下游 classification / JE / review flow。

Required fields：

- `source_rule_id`
- `approved_accounting_treatment`
- `classification_authority`；allowed value for this node: `approved_rule`

Optional fields：

- `review_requirement`
- `accounting_notes`
- `evidence_refs_used`

Validation rules：

- `approved_accounting_treatment` 必须原样来自 matched approved rule，不能由本节点改写。
- 如果 matched rule 本身要求 review，本节点不能输出纯 automatic `rule_handled`；应输出 `review_required` 或在 `review_requirement` 中明确下游必须 review，具体 routing 见 Open Contract Boundaries。

Memory boundary：

- runtime-only handoff。
- 下游可将其用于 JE Generation、review context 或 Transaction Log audit input。

### 4.4 `miss_context`

Purpose：说明 deterministic rule path 正常未命中的原因，供 Case Judgment Node 继续处理。

Required fields：

- `miss_reason`；allowed values: `no_active_rule_for_entity_context`, `condition_not_satisfied`, `no_rule_after_policy_allowed_attempt`。
- `entity_id`

Optional fields：

- `evaluated_rule_ids`
- `condition_mismatch_summary`
- `case_judgment_allowed`：boolean

Validation rules：

- `miss_context` 不能用于 authority 不足的情况。
- `case_judgment_allowed` 不能覆盖 entity / policy / governance hard block；它只表示没有 rule hit 后是否可以进入 Case Judgment。

Memory boundary：

- runtime-only。
- 不能自动创建 rule candidate 或 rule promotion。

### 4.5 `blocked_context`

Purpose：说明 rule path 因 authority、policy 或 governance 限制不可用。

Required fields：

- `blocked_reason`；allowed values: `entity_not_active`, `new_entity_candidate`, `ambiguous_entity`, `unresolved_entity`, `alias_not_approved`, `alias_rejected`, `role_unconfirmed`, `automation_policy_block`, `rule_not_approved_or_not_active`, `governance_block`。

Optional fields：

- `entity_id`
- `matched_alias`
- `alias_status`
- `candidate_role`
- `related_rule_ids`
- `authority_refs`

Validation rules：

- blocked reason 是 hard authority limit，不能被 LLM 或 Case Judgment 自行解除。
- `candidate_role` 只能解释 block，不能写入 durable role。

Memory boundary：

- runtime-only。
- 可生成 candidate signal，但不写 durable memory。

### 4.6 `review_context`

Purpose：说明当前 rule path 需要 accountant review 才能继续或确认。

Required fields：

- `review_reason`；allowed values: `rule_requires_review`, `policy_requires_review`, `alias_or_role_dispute`, `condition_requires_accountant_confirmation`, `upstream_authority_issue`。

Optional fields：

- `question_focus`
- `related_entity_ids`
- `related_rule_ids`
- `evidence_refs`

Validation rules：

- review context 不能表达 approval。
- `question_focus` 只能帮助下游提问，不能替 accountant 作答。

Memory boundary：

- runtime-only。
- accountant 的回答若要成为 durable authority，必须走 Review / Governance authority path。

### 4.7 `governance_context`

Purpose：说明需要治理流程处理的长期 authority 问题。

Required fields：

- `governance_need_type`；allowed values: `rule_approval_needed`, `rule_conflict_resolution_needed`, `rule_lifecycle_review_needed`, `alias_approval_needed`, `role_confirmation_needed`, `automation_policy_decision_needed`, `entity_lifecycle_review_needed`。

Optional fields：

- `candidate_signal_refs`
- `related_entity_ids`
- `related_rule_ids`
- `reason`

Validation rules：

- governance context 不是 `Governance Log` write。
- 本节点不能批准、拒绝或应用 governance changes。

Memory boundary：

- candidate-only。
- 只有 Review / Governance Review / memory update workflow 可以把它转成 durable governance event。

### 4.8 `conflict_context`

Purpose：说明多条 rule 或 authority source 之间存在冲突，不能安全 deterministic handling。

Required fields：

- `conflict_type`；allowed values: `multiple_active_rules`, `rule_vs_policy`, `rule_vs_governance_constraint`, `entity_alias_role_conflict`, `rule_condition_overlap`。
- `conflicting_refs`
- `reason`

Optional fields：

- `recommended_downstream_review_scope`

Validation rules：

- 存在 unresolved conflict 时，不能输出 `rule_handled`。
- 本节点不能用 LLM、confidence 或 fallback preference 选择一个 rule 覆盖冲突。

Memory boundary：

- runtime-only conflict signal。
- 是否形成 durable governance event 由后续 workflow 决定。

### 4.9 `candidate_signals`

Purpose：把本节点发现的候选治理或后续评估信号交给下游。

Allowed `signal_type` values：

- `rule_candidate`
- `rule_condition_gap`
- `rule_conflict_review`
- `rule_stale_or_unstable`
- `alias_confirmation_needed`
- `role_confirmation_needed`
- `automation_policy_review`

Required fields per signal：

- `signal_type`
- `reason`
- `related_refs`

Optional fields：

- `evidence_refs`
- `suggested_review_focus`

Validation rules：

- signal 不能包含 `approval_status = approved`。
- signal 不能直接写入 `Rule Log`、`Entity Log` 或 `Governance Log`。
- signal 不能支持当前交易的 rule match。

Memory boundary：

- candidate-only。
- 长期化只能通过 accountant / governance approval。

## 5. Field Authority and Memory Boundary

### 5.1 Source of truth

- `transaction_id` 的 source of truth 是 Transaction Identity layer。
- `amount_abs`、`direction`、`transaction_date`、`bank_account`、evidence references 的 source of truth 是 Evidence Intake / Preprocessing 和 Evidence Log。
- `entity_id`、approved aliases、confirmed roles、entity status、automation policy 的 source of truth 是 `Entity Log` 加已生效 governance events。
- active approved rules、rule status、approved condition set、approved accounting treatment 的 source of truth 是 `Rule Log`。
- effective governance restrictions 的 source of truth 是 `Governance Log`。
- accountant intervention 只有在转化为 review-required constraint、policy change、rule status 或 governance event 后，才影响本节点 authority。

### 5.2 Fields that can never become durable memory by this node

本节点不能把以下字段直接写成 durable memory：

- `candidate_role`
- `candidate_signals`
- `miss_context`
- `blocked_context`
- `review_context`
- `governance_context`
- `conflict_context`
- `runtime_trace`
- rule miss / condition mismatch summary
- LLM-readable explanation

这些最多是 runtime context 或 candidate-only signal。

### 5.3 Fields that can become durable only after accountant / governance approval

以下内容只有经过 accountant / governance approval 才可能长期化：

- new rule / rule promotion
- rule condition change
- rule lifecycle change
- alias approval / rejection
- role confirmation
- automation policy upgrade or relaxation
- entity lifecycle change
- governance event resolution

本节点只能提供候选信号和引用，不能批准或应用这些变化。

### 5.4 Audit vs learning / logging boundary

`Transaction Log` 是 audit-facing final record，不参与 runtime rule decision。

本节点的 `rule_match_result` 可以被 downstream Transaction Logging Node 记录为“为什么本笔交易走 rule path 或未走 rule path”的审计输入，但该记录不会反过来成为本节点未来 rule source。

`Case Log`、`Knowledge Log / Summary Log` 和 repeated outcomes 不能替代 `Rule Log` authority。

## 6. Validation Rules

### 6.1 Contract-level validation rules

- Input 必须有稳定 `transaction_id`、objective transaction basis、completed entity-resolution handoff 和 rule authority snapshot。
- `rule_handled` 必须同时满足：active entity、approved alias、confirmed required role/context、policy 允许 rule-based automation、active approved rule、approved rule conditions satisfied。
- 所有 authority-bearing fields 必须有 source reference。
- Candidate-only fields 不能出现在 authority position。
- Runtime-only trace / explanation 不能成为 durable decision source。

### 6.2 Conditions that make input invalid

- 缺少 `transaction_id`。
- 缺少 `entity_resolution_output.status`。
- `entity_resolution_completed != true`。
- `structural_path_status = handled`。
- `transaction_identity_status` 不是 `assigned`。
- `amount_abs <= 0`。
- `direction` 不在 `inflow` / `outflow`。
- `evidence_refs` 为空。
- rule records 缺少 `rule_id`、`rule_status`、`approval_status` 或 `authority_source`，但请求要求本节点判断 rule match。

### 6.3 Conditions that make output invalid

- `status = rule_handled` 但没有 `matched_rule` 或 `rule_output_payload`。
- `status = rule_handled` 但 rule 不是 active approved。
- `status = rule_handled` 但 entity 不是 active。
- `status = rule_handled` 但 alias 是 candidate / rejected / missing required approved alias。
- `status = rule_handled` 但 required role/context 未 confirmed。
- `status = rule_handled` 但 automation policy 是 `review_required` 或 `disabled`。
- `status = rule_miss` 但实际原因是 authority block。
- `candidate_signals` 被标记为 approved 或 durable write。
- output 暗示本节点已经写入 `Transaction Log`、`Entity Log`、`Rule Log` 或 `Governance Log`。

### 6.4 Stop / ask conditions for unresolved contract authority

如果后续设计要求本节点直接决定以下事项，应停止并要求 product decision：

- `case_allowed_but_no_promotion` 是否一律允许 rule-based automation，而不是依赖 effective policy metadata。
- Rule Log 的完整 lifecycle enum 是否要在 Stage 3 全局冻结。
- `approved_accounting_treatment` 的 exact JE-ready schema 是否由 Rule Match Stage 3 定义，还是由 JE Generation / shared contract 定义。
- matched rule 自带 review requirement 时，`rule_handled + review_requirement` 与 `review_required` 的 routing 语义如何统一。
- 多条 active rules 同时满足时是否存在 deterministic priority，而不是一律 `rule_conflict`。

## 7. Examples

### 7.1 Valid minimal example

```yaml
rule_match_request:
  transaction_basis:
    transaction_id: txn_01HXABC
    amount_abs: 18.25
    direction: outflow
    transaction_date: 2026-04-30
    bank_account: operating_chequing
    evidence_refs: [ev_bank_001]
    raw_description: "TIMS COFFEE-1234"
  upstream_workflow_context:
    evidence_status: ready
    transaction_identity_status: assigned
    structural_path_status: not_structural
    entity_resolution_completed: true
  entity_resolution_output:
    status: resolved_entity
    entity_id: ent_tim_hortons
    confidence: high
    reason: "approved alias matched current bank description"
    matched_alias: "TIMS COFFEE-1234"
    alias_status: approved_alias
    evidence_used: [ev_bank_001]
  entity_authority_snapshot:
    entity_id: ent_tim_hortons
    entity_status: active
    approved_aliases: ["TIMS COFFEE-1234"]
    confirmed_roles: [meal_vendor]
    authority: accountant_approved
    automation_policy: eligible
  automation_policy_snapshot:
    entity_id: ent_tim_hortons
    policy: eligible
    policy_source: governance_event_approved
  rule_log_snapshot:
    snapshot_source: rule_log_current
    rules:
      - rule_id: rule_tim_meals
        entity_id: ent_tim_hortons
        rule_status: active
        approval_status: approved
        authority_source: accountant_approved
        applicability:
          entity_id: ent_tim_hortons
          required_aliases: ["TIMS COFFEE-1234"]
          required_roles: [meal_vendor]
        approved_condition_set:
          direction: outflow
        approved_accounting_treatment:
          treatment_ref: approved_rule_payload_tim_meals
```

Valid result：

```yaml
rule_match_result:
  transaction_id: txn_01HXABC
  status: rule_handled
  authority_summary: "active entity, approved alias, confirmed role, eligible policy, active approved rule"
  result_reason: "current transaction satisfies approved rule conditions"
  matched_rule:
    rule_id: rule_tim_meals
    rule_version: 1
    entity_id: ent_tim_hortons
    authority_source: accountant_approved
    matched_conditions:
      direction: outflow
  rule_output_payload:
    source_rule_id: rule_tim_meals
    classification_authority: approved_rule
    approved_accounting_treatment:
      treatment_ref: approved_rule_payload_tim_meals
```

### 7.2 Valid richer example

```yaml
rule_match_result:
  transaction_id: txn_01HXDEF
  status: rule_blocked
  authority_summary: "entity resolved but alias is candidate only"
  result_reason: "candidate alias cannot support rule match"
  blocked_context:
    blocked_reason: alias_not_approved
    entity_id: ent_home_depot
    matched_alias: "HD STORE 4521"
    alias_status: candidate_alias
    authority_refs: [entity_snapshot_2026_04_30]
  candidate_signals:
    - signal_type: alias_confirmation_needed
      reason: "candidate alias resembles active entity but lacks approval"
      related_refs: [ent_home_depot, ev_bank_101]
  downstream_handoff_hint: "Case Judgment may proceed only if automation policy and current evidence allow; alias signal requires review/governance before future rule use."
```

### 7.3 Invalid example

```yaml
rule_match_result:
  transaction_id: txn_01HXBAD
  status: rule_handled
  authority_summary: "new entity but likely SaaS vendor"
  matched_rule:
    rule_id: rule_generic_software
    entity_id: null
  rule_output_payload:
    classification_authority: inferred_rule
```

Invalid reason：

- `new_entity_candidate` 或无 stable active `entity_id` 不能支持 rule match。
- `classification_authority = inferred_rule` 不是 approved rule authority。
- rule match 不能使用 generic inference、case memory 或 LLM 判断替代 active approved rule。

## 8. Open Contract Boundaries

- `Rule Log` 的完整全局 lifecycle enum 仍未在 active docs 中冻结；本文件只定义 Rule Match Node 必须理解的 node-facing statuses。
- `approved_accounting_treatment` 的 exact shared accounting payload / JE-ready schema 需要与 JE Generation、Review、Transaction Logging 的 Stage 3 contracts 对齐。
- `case_allowed_but_no_promotion` 是否默认允许 rule-based automation 仍需更明确的 policy contract；本文件保守要求 effective metadata 明确允许。
- 多条 active approved rules 同时满足时，当前 contract 默认输出 `rule_conflict`；是否存在 deterministic priority / specificity resolution 留待 Stage 4 或 shared rule contract 决定。
- matched rule 自带 review requirement 时，`review_required` 与 `rule_handled` 加 downstream review flag 的关系未完全冻结。
- Accountant 补充确认 alias / role / rule 后是否自动 retrigger Rule Match，不在 Stage 3 冻结。

## 9. Self-Review

- 已阅读 required repo docs：`AGENTS.md`、`TASK_STATE.md`、`PLANS.md`、`CLAUDE.md`、`DECISIONS.md`、`supporting documents/communication_preferences.md`、`supporting documents/development_workflow.md`、`supporting documents/node_design_roadmap.md`、`new system/new_system.md`。
- 已阅读本节点 prior approved docs：Stage 1 functional intent 与 Stage 2 logic and boundaries。
- 已读取可用 Superpowers docs：`using-superpowers/SKILL.md`、`brainstorming/SKILL.md`；project workflow skill `ai-bookkeeper-node-design-facilitation` 在当前环境不存在，因此按 runner instruction 使用 repo `supporting documents/node_design_roadmap.md` 与本节点 Stage 1/2 docs 作为 workflow authority。
- 已确认 optional `supporting documents/node_design_roadmap_zh.md` 在 working tree 中缺失；未发明该文件内容。
- 本文件只写 Stage 3 data contract，没有进入 Stage 4 execution algorithm、Stage 5 technical implementation map、Stage 6 test matrix 或 Stage 7 coding-agent task contract。
- 未把 `Transaction Log`、`Case Log`、`Knowledge Log / Summary Log`、candidate alias、candidate role、new entity candidate、lint warning 或 recent intervention 当作 rule authority。
- 未创造 unsupported product authority；未修改 `new_system.md`、Stage 1/2 docs、governance docs 或其他 repo 文件。
