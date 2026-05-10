# Coordinator / Pending Node — Stage 3：Data Contract Spec

## 1. Stage 范围

本 Stage 3 只定义 `Coordinator / Pending Node` 的 implementation-facing data contract。

前置依据是：

- `new system/new_system.md`
- `new system/node_stage_designs/coordinator_pending_node__stage_1__functional_intent.md`
- `new system/node_stage_designs/coordinator_pending_node__stage_2__logic_and_boundaries.md`

本阶段把 Stage 1/2 已批准的 pending clarification 行为转换为输入对象类别、输出对象类别、字段语义、字段 authority、runtime / durable boundary、validation rules 和 compact examples。

本阶段不定义：

- step-by-step execution algorithm
- accountant-facing UI / prompt structure
- technical implementation map、repo module path、class、API、storage engine 或 DB migration
- test matrix、fixture plan 或 coding-agent task contract
- exact reprocessing algorithm
- 新 product authority
- legacy replacement mapping

## 2. Contract Position in Workflow

### 2.1 Upstream Handoff Consumed

本节点消费 `pending_coordination_request`。

该 request 可由以下 upstream nodes 或 workflow context 触发：

- `Evidence Intake / Preprocessing Node`
- `Transaction Identity Node`
- `Profile / Structural Match Node`
- `Entity Resolution Node`
- `Rule Match Node`
- `Case Judgment Node`
- workflow runtime 中已经存在的 review-needed / clarification-needed context

该 handoff 必须说明：

- 当前 pending 绑定到哪笔稳定交易、哪个 batch、哪个 client；
- 上游哪个节点说明不能安全继续；
- 缺的是 evidence、identity、profile structure、entity / alias / role authority、rule authority、case judgment context、review context 还是 governance candidate context；
- 当前最多允许哪些后续动作。

如果上游没有稳定 `transaction_id`，或者问题不能绑定到具体交易 / evidence / issue，本节点不能生成普通 accountant clarification。

### 2.2 Downstream Handoff Produced

本节点可产生以下 output categories：

- `accountant_clarification_request`：面向 accountant 的聚焦问题。
- `intervention_log_record`：写入 `Intervention Log` 的问答 / 修正 / 确认语境。
- `supplemental_context_handoff`：交给后续 workflow 的补充 evidence 或 context。
- `runtime_continuation_handoff`：说明当前交易可以在受限边界内继续后续 judgment / review flow。
- `review_or_governance_candidate_handoff`：只表达后续应评估的候选信号。
- `still_pending_handoff`：说明回答缺失、不足、冲突或仍不能继续。

这些 output 都不等于 final accounting classification、JE、Transaction Log entry 或 governance approval。

### 2.3 Logs / Memory Stores Read

本节点可以读取或消费：

- runtime evidence foundation、objective transaction basis 和 `transaction_id`
- 上游节点带入的 pending / review / governance-needed context
- `Intervention Log` 中同一 transaction、batch、client 或相关 issue 的 prior questions / answers / corrections / confirmations
- `Profile`、`Entity Log`、`Case Log`、`Rule Log`、`Governance Log` 中由上游 handoff 带入的 effective authority limits 或 review-needed context
- `Knowledge Log / Summary Log` 的辅助摘要，但不能把它当作 deterministic rule source 或 accountant approval

本节点不得读取 `Transaction Log` 做 runtime pending decision。

### 2.4 Logs / Memory Stores Written or Candidate-Only

本节点唯一允许的 durable write 是 `Intervention Log` 语义下的 `intervention_log_record`。

该 write 只能记录：

- accountant-facing question
- accountant answer、clarification、correction、confirmation
- pending 为什么发生、回答解决了什么、仍缺什么
- 当前 interaction 与 transaction / evidence / upstream issue 的引用关系

本节点只能 candidate-only 输出：

- supplemental evidence / re-intake candidate
- profile change signal
- entity / alias / role confirmation candidate
- case memory update candidate
- rule candidate / rule conflict candidate
- automation-policy / governance candidate
- review-needed or unresolved-pending signal

本节点绝不能直接写入或修改：

- `Transaction Log`
- `Profile`
- `Entity Log`
- `Case Log`
- `Rule Log`
- approved `Governance Log`
- final JE / accounting result

## 3. Input Contracts

### 3.1 `pending_coordination_request`

Purpose：本节点的主 runtime input envelope，表示当前交易需要 pending clarification 或 intervention handling。

Source authority：workflow orchestrator + 上游触发节点。该 envelope 汇总上游已产生的 context，不自行创建 product authority。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `coordination_request_id` | 本次 pending coordination 的 runtime 引用 | workflow runtime | runtime |
| `client_id` | 当前客户标识 | client / batch context | durable reference |
| `batch_id` | 当前处理批次 | workflow runtime | runtime |
| `transaction_id` | 当前 pending 交易的稳定身份 | `Transaction Identity Node` | durable reference |
| `trigger_source_node` | 触发 pending 的上游节点 | upstream workflow | runtime |
| `pending_issue_context` | 一个或多个上游卡点 | upstream workflow | runtime object with durable refs |
| `authority_limit_context` | 当前允许 / 禁止的后续动作上限 | upstream authority / memory context | runtime projection |
| `transaction_context` | 当前交易客观基础与 evidence references | evidence / identity flow | runtime object with durable refs |

Allowed `trigger_source_node` values：

- `evidence_intake_preprocessing`
- `transaction_identity`
- `profile_structural_match`
- `entity_resolution`
- `rule_match`
- `case_judgment`
- `review_context`
- `workflow_orchestrator`

Optional fields：

- `prior_intervention_context`：同一 transaction / batch / issue 相关的既有 intervention context。
- `suggested_question_targets`：上游建议本节点询问的事实类别；只能作为 question target，不能作为 authority。
- `request_trace`：runtime diagnostics；不得作为业务结论。

Validation / rejection rules：

- `transaction_id`、`client_id`、`batch_id`、`trigger_source_node`、`pending_issue_context`、`authority_limit_context` 缺失时 input invalid。
- `pending_issue_context` 为空时 input invalid；本节点不能主动创造 pending reason。
- 如果当前交易已经被 deterministic path、approved review path、JE generation 或 Transaction Logging 完成，input invalid。
- `trigger_source_node` 必须能与至少一个 `pending_issue_context.source_node` 对齐。
- `request_trace` 不能被用作 accountant question 的事实来源。

Runtime-only vs durable references：

- envelope 本身是 runtime-only。
- `transaction_id`、`client_id`、evidence refs、memory refs 是 durable references。
- 接收该 request 不授予本节点任何 long-term memory mutation authority。

### 3.2 `transaction_context`

Purpose：把 pending question 绑定到可追溯的当前交易和 evidence，而不是泛泛业务询问。

Source authority：`Evidence Intake / Preprocessing Node`、`Transaction Identity Node`、上游 handoff。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `transaction_id` | 稳定交易 ID | `Transaction Identity Node` | durable reference |
| `objective_transaction_basis` | 客观交易基础 | Evidence Intake / Preprocessing | runtime object with durable evidence refs |
| `evidence_refs` | 当前问题相关 evidence references | `Evidence Log` | durable references |
| `evidence_quality_status` | 当前 evidence 是否足以支持后续处理 | Evidence Intake / upstream issue context | runtime |

Required `objective_transaction_basis` fields：

- `transaction_date`
- `amount_abs`
- `direction`; allowed values: `inflow`, `outflow`
- `bank_account`

Optional fields：

- `raw_description`
- `description`
- `pattern_source`
- `receipt_refs`
- `cheque_info_refs`
- `invoice_refs`
- `contract_refs`
- `counterparty_surface_text`
- `currency`

Allowed `evidence_quality_status` values：

- `ready`
- `missing_evidence`
- `conflicting_evidence`
- `unmatched_evidence`
- `low_quality_evidence`
- `identity_or_attachment_unclear`

Validation / rejection rules：

- `amount_abs` 必须为正数；金额方向只能由 `direction` 表达，不能由 signed amount 暗示。
- `direction` 必须属于允许值。
- `evidence_refs` 不能为空，除非 pending issue 本身是 “missing evidence for known transaction”；这种情况必须在 `pending_issue_context` 中明确说明缺什么 evidence。
- `description = null` 和 `pattern_source = null` 都是有效状态；本节点不能要求 canonical description 存在。
- accountant-facing question 不能引用没有 `evidence_ref` 支撑的模型总结作为事实。

Runtime-only vs durable references：

- `transaction_context` 是 runtime handoff。
- 其中的 objective fields 来自 durable evidence / transaction identity。
- 本节点不能用自然语言 clarification 覆盖原始 evidence。

### 3.3 `pending_issue_context`

Purpose：表达上游为什么不能安全继续，以及 accountant clarification 需要修复哪个具体缺口。

Source authority：触发本节点的 upstream node。

Required fields per issue：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `issue_id` | 当前 pending issue 引用 | upstream workflow | runtime |
| `source_node` | 产生该 issue 的节点 | upstream workflow | runtime |
| `issue_type` | 卡点类别 | upstream node | runtime |
| `issue_summary` | 卡点简述 | upstream node | runtime |
| `blocking_reason` | 为什么不能安全继续 | upstream node | runtime |
| `question_target` | 需要 accountant 补充 / 确认的事实类别 | upstream node / Coordinator synthesis | runtime |
| `supporting_refs` | 支撑 issue 的 evidence / memory / prior intervention refs | upstream node | durable references |

Allowed `source_node` values：

- `evidence_intake_preprocessing`
- `transaction_identity`
- `profile_structural_match`
- `entity_resolution`
- `rule_match`
- `case_judgment`
- `review_context`
- `workflow_orchestrator`

Allowed `issue_type` values：

- `missing_evidence`
- `conflicting_evidence`
- `unmatched_evidence`
- `transaction_identity_unclear`
- `duplicate_or_same_transaction_unclear`
- `profile_structural_fact_missing`
- `profile_structural_conflict`
- `entity_ambiguous`
- `entity_unresolved`
- `new_entity_context_needed`
- `alias_authority_gap`
- `role_unconfirmed`
- `rule_blocked`
- `rule_conflict`
- `automation_policy_block`
- `case_precedent_uncertain`
- `case_evidence_insufficient`
- `review_required`
- `governance_candidate`
- `other_upstream_pending_issue`

Allowed `question_target` values：

- `evidence_attachment`
- `business_purpose`
- `counterparty_identity`
- `role_or_context`
- `profile_structural_fact`
- `rule_exception_or_conflict`
- `case_precedent_applicability`
- `review_confirmation`
- `governance_signal_context`
- `unresolved_issue_explanation`

Optional fields：

- `candidate_entity_refs`
- `candidate_alias_text`
- `candidate_role`
- `candidate_rule_refs`
- `case_memory_refs`
- `risk_or_policy_flags`
- `upstream_confidence`
- `upstream_policy_trace`

Validation / rejection rules：

- 每个 issue 必须有 `source_node`、`issue_type`、`blocking_reason` 和至少一个 `question_target`。
- `issue_type = new_entity_context_needed` 不得被解释为自动阻断 current operational classification；它只表示不能产生 durable entity / rule authority，且是否能继续分类取决于后续 evidence / judgment authority。
- `candidate_alias_text` 不能被当作 approved alias。
- `candidate_role` 不能被当作 confirmed role。
- `upstream_confidence` 不能替代 accountant clarification、review approval 或 governance approval。
- `review_required` 和 `governance_candidate` 不能被降级成普通 clarification completion。

Runtime-only vs durable references：

- issue object 是 runtime-only。
- `supporting_refs` 指向 durable evidence / memory / intervention records。
- issue 中的 candidate fields 永远不是 durable authority。

### 3.4 `authority_limit_context`

Purpose：定义本节点输出的上限，防止 pending question 绕过上游 hard blocks、review 或 governance boundary。

Source authority：upstream nodes、effective Profile / Entity / Rule / Governance context、Review / Governance boundary。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `allowed_next_actions` | 本节点最多可建议的后续动作 | upstream authority context | runtime |
| `hard_blocks` | 本节点不能通过提问解除的限制 | upstream / governance context | runtime projection |
| `memory_mutation_policy` | 当前回答是否可写长期记忆；对本节点必须为 no direct mutation | governance / project authority | runtime statement |

Allowed `allowed_next_actions` values：

- `ask_accountant`
- `record_intervention`
- `handoff_supplemental_context`
- `continue_runtime_judgment`
- `route_to_review`
- `propose_governance_candidate`
- `remain_pending`

Allowed `hard_blocks` values：

- `missing_stable_transaction_identity`
- `evidence_authenticity_or_attachment_conflict`
- `ambiguous_entity`
- `unresolved_entity`
- `unconfirmed_role`
- `candidate_or_rejected_alias`
- `rule_required_without_active_rule`
- `review_required_policy`
- `disabled_automation_policy`
- `governance_approval_required`
- `final_processing_already_completed`

Required `memory_mutation_policy` value for this node：

- `intervention_log_only_no_business_memory_mutation`

Optional fields：

- `effective_entity_policy`
- `effective_rule_lifecycle_status`
- `effective_review_requirement`
- `effective_governance_refs`
- `authority_notes`

Validation / rejection rules：

- 如果 `memory_mutation_policy` 允许本节点直接修改 Profile、Entity、Case、Rule、Governance 或 Transaction Log，则 input invalid。
- `allowed_next_actions` 不能包含本节点无权执行的 final accounting classification、JE generation、Transaction Log write 或 governance approval。
- `hard_blocks` 必须被 output 保留或升级，不能被 omission 消除。

Runtime-only vs durable references：

- 该对象是 runtime projection。
- governance / entity / rule references 可以指向 durable records，但本节点只有读取 / candidate handoff 权限。

### 3.5 `prior_intervention_context`

Purpose：避免重复提问、发现 accountant answer 冲突，并保留人机介入链条。

Source authority：`Intervention Log`。

Required fields when present：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `intervention_refs` | 相关 prior intervention records | `Intervention Log` | durable references |
| `relation_scope` | 与当前 request 的关系范围 | `Intervention Log` lookup / runtime selection | runtime |

Allowed `relation_scope` values：

- `same_transaction`
- `same_batch`
- `same_entity_or_candidate`
- `same_issue_type`
- `same_client_recent`

Optional fields：

- `prior_question_summary`
- `prior_answer_summary`
- `prior_resolution_status`
- `prior_conflict_flags`

Validation / rejection rules：

- prior intervention 可以提示重复或冲突，但不能替代 `Entity Log`、`Case Log`、`Rule Log`、`Governance Log` 或 `Profile` authority。
- 未经 review / governance 转化的 prior answer 不能作为 current durable business truth。
- 如果 prior answer 与 current evidence 或 memory authority 冲突，本节点必须保留 conflict signal。

Runtime-only vs durable references：

- summaries 是 runtime projection。
- `intervention_refs` 是 durable references。
- prior intervention 本身只属于 intervention history，不是 deterministic automation authority。

### 3.6 `accountant_response_payload`

Purpose：表达 accountant 对 clarification request 的回答、补充 evidence、修正或确认。

Source authority：accountant input / accountant-provided material。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `response_id` | 本次回答引用 | workflow runtime / intervention capture | runtime before log write |
| `clarification_request_id` | 回答对应的问题 | `accountant_clarification_request` | runtime / intervention ref |
| `accountant_id` | 回答者标识 | accountant context | durable metadata |
| `responded_at` | 回答时间 | system capture | durable metadata if logged |
| `response_type` | 回答类别 | accountant input capture | runtime |
| `response_text` | accountant 原话或结构化回答文本 | accountant input | durable intervention content |

Allowed `response_type` values：

- `answer`
- `correction`
- `confirmation`
- `cannot_answer`
- `supplemental_evidence_provided`
- `needs_review`
- `governance_context_provided`

Optional fields：

- `attached_evidence_refs`
- `target_transaction_id`
- `target_issue_ids`
- `structured_response_claims`
- `accountant_confidence_note`
- `response_language`

Validation / rejection rules：

- `clarification_request_id` 必须能对应当前或 prior unresolved question。
- `target_transaction_id` 如存在，必须等于 request 的 `transaction_id`；否则必须作为 identity conflict 处理。
- `response_text` 不能为空，除非 `response_type = supplemental_evidence_provided` 且 `attached_evidence_refs` 非空。
- `structured_response_claims` 只能表示 accountant 说了什么，不能自动变成 Profile truth、approved alias、confirmed role、active rule 或 governance approval。
- `response_type = governance_context_provided` 只产生 governance candidate context，不等于 approved governance event。

Runtime-only vs durable references：

- payload 本身在写入前是 runtime input。
- 被接受后可写入 `Intervention Log`。
- attached raw evidence 若需要保存或重新处理，仍属于 Evidence Intake / Evidence Log 边界。

## 4. Output Contracts

### 4.1 `accountant_clarification_request`

Purpose：把上游卡点转化为 accountant 可以回答的聚焦问题。

Consumer / downstream authority：accountant-facing pending workflow、后续 `accountant_response_payload` capture、`Intervention Log`。

Required fields：

| Field | Meaning |
| --- | --- |
| `clarification_request_id` | 本次问题引用 |
| `coordination_request_id` | 来源 coordination request |
| `client_id` | 客户引用 |
| `batch_id` | 批次引用 |
| `transaction_id` | 绑定交易 |
| `question_status` | 当前问题状态 |
| `question_target` | 问题所询问的事实类别 |
| `question_text` | 面向 accountant 的问题文本 |
| `source_issue_ids` | 该问题覆盖的 pending issue |
| `why_needed` | 为什么这个回答会推进当前 workflow |
| `supporting_refs` | 支撑问题的 evidence / memory / intervention refs |
| `authority_warning` | 明确该回答不会自动形成哪些 authority |

Allowed `question_status` values：

- `drafted`
- `sent`
- `answered`
- `superseded`
- `cancelled`

`question_target` allowed values：同 `pending_issue_context.question_target`。

Optional fields：

- `answer_format_hint`：例如 yes/no、选择 candidate、补充一句业务用途、上传附件。
- `grouped_issue_ids`：多个 issue 被合并为一个问题时使用。
- `do_not_imply_facts`：列出不能包装成事实的 candidate / conflict。

Validation rules：

- `question_text` 必须绑定至少一个 `source_issue_id`。
- `question_text` 不得要求 accountant 批准内部系统流程。
- `question_text` 不得把 candidate entity、candidate alias、candidate role、candidate rule 包装为已确认事实。
- `authority_warning` 必须覆盖相关 issue 的 no-mutation / governance boundary。

Durable / candidate / runtime：

- question object 是 runtime output。
- 发送或记录后，其内容可以作为 `Intervention Log` record 的一部分 durable 保存。
- 它不写任何 business memory。

### 4.2 `intervention_log_record`

Purpose：在 `Intervention Log` 中保存 accountant 介入、提问、回答、修正和确认过程。

Consumer / downstream authority：Review Node、Case Judgment context、Governance Review candidate review、Case Memory Update Node、future Coordinator runs。

Required fields：

| Field | Meaning |
| --- | --- |
| `intervention_id` | Intervention Log record ID |
| `client_id` | 客户引用 |
| `batch_id` | 批次引用 |
| `transaction_id` | 绑定交易 |
| `coordination_request_id` | 来源 request |
| `intervention_type` | 介入记录类型 |
| `source_issue_ids` | 关联 pending issue |
| `question_text` | 若记录问题，保存问题文本 |
| `accountant_response_text` | 若记录回答，保存 accountant 原话 |
| `accountant_id` | accountant 标识 |
| `created_at` | 记录创建时间 |
| `authority_boundary` | 说明该记录不授予哪些 authority |
| `resolution_status` | 本次介入对 pending issue 的解决状态 |

Allowed `intervention_type` values：

- `question_asked`
- `answer_received`
- `correction_received`
- `confirmation_received`
- `supplemental_evidence_received`
- `unresolved_followup`
- `review_context_captured`
- `governance_candidate_context_captured`

Allowed `resolution_status` values：

- `open`
- `partially_answered`
- `answered_for_current_context`
- `needs_followup`
- `needs_review`
- `governance_candidate_only`
- `unresolved`
- `conflicting`

Optional fields：

- `attached_evidence_refs`
- `resolved_issue_ids`
- `remaining_issue_ids`
- `conflict_refs`
- `candidate_signal_refs`
- `supersedes_intervention_id`
- `language_or_translation_note`

Validation rules：

- `intervention_id`、`transaction_id`、`source_issue_ids`、`intervention_type`、`authority_boundary` 必须存在。
- `question_asked` 必须有 `question_text`。
- `answer_received` / `correction_received` / `confirmation_received` 必须有 `accountant_response_text` 或可追溯 `attached_evidence_refs`。
- `resolution_status = answered_for_current_context` 只表示当前 context 已被回答，不表示 final classification、durable memory update 或 governance approval。
- `governance_candidate_only` 不能写成 approved governance result。

Durable / candidate / runtime：

- 该对象是本节点唯一允许 durable write 的类别。
- 它属于 `Intervention Log`，不是 `Transaction Log`、`Case Log`、`Rule Log`、`Entity Log` 或 `Governance Log`。
- 它可以成为后续 workflow 的 evidence/context reference，但不直接成为 deterministic authority。

### 4.3 `supplemental_context_handoff`

Purpose：把 accountant 新提供的 evidence、附件归属说明或当前交易 context 交给后续 workflow。

Consumer / downstream authority：Evidence Intake / Preprocessing、Transaction Identity、Entity Resolution、Case Judgment、Review Node。

Required fields：

| Field | Meaning |
| --- | --- |
| `handoff_id` | handoff 引用 |
| `transaction_id` | 绑定交易 |
| `source_intervention_id` | 来源 intervention |
| `handoff_type` | handoff 类别 |
| `target_issue_ids` | 要修复的 issue |
| `content_summary` | 补充内容摘要 |
| `source_refs` | accountant response / evidence refs |

Allowed `handoff_type` values：

- `supplemental_evidence`
- `evidence_attachment_clarification`
- `business_context`
- `identity_context`
- `profile_context`
- `case_context`
- `review_context`

Optional fields：

- `recommended_downstream_consumer`
- `requires_re_intake`：boolean
- `attached_evidence_refs`
- `remaining_authority_limits`

Validation rules：

- `source_intervention_id` 必须存在。
- `supplemental_evidence` 必须携带 `attached_evidence_refs` 或明确说明 evidence 缺失。
- `business_context` / `identity_context` / `profile_context` 不能覆盖 raw evidence。
- `requires_re_intake = true` 时，本 handoff 仍不等于 Evidence Log write；是否 intake 属于 Evidence Intake boundary。

Durable / candidate / runtime：

- 该 handoff 是 runtime-only。
- `source_intervention_id` 和 evidence refs 是 durable references。
- 它不写 long-term memory。

### 4.4 `runtime_continuation_handoff`

Purpose：说明 accountant clarification 可能已足以让当前交易进入受限后续 workflow。

Consumer / downstream authority：Case Judgment、Review Node、workflow orchestrator，以及必要时上游 reprocessing context。

Required fields：

| Field | Meaning |
| --- | --- |
| `handoff_id` | handoff 引用 |
| `transaction_id` | 绑定交易 |
| `source_intervention_ids` | 支撑 continuation 的 intervention refs |
| `continuation_status` | 当前 continuation contract label |
| `resolved_issue_ids` | 已解决的 issue |
| `remaining_issue_ids` | 仍未解决的 issue |
| `remaining_authority_limits` | 后续必须继续尊重的限制 |

Allowed `continuation_status` values：

- `context_ready_for_case_judgment`
- `context_ready_for_review`
- `context_ready_for_limited_reprocessing`
- `still_requires_review`

Optional fields：

- `suggested_reprocessing_scope`
- `supplemental_context_handoff_ids`
- `review_note`

Validation rules：

- `continuation_status` 不是最终 routing enum；它只说明 data contract 上的 handoff readiness。
- 若存在 hard block，例如 `governance_approval_required`、`review_required_policy`、`disabled_automation_policy`，不得输出会暗示自动 completion 的 status。
- `resolved_issue_ids` 不能包含实际未被 accountant 明确回答或 evidence 修复的 issue。

Durable / candidate / runtime：

- 该 handoff 是 runtime-only。
- 它不写 durable memory。
- 它不批准 classification、review outcome 或 governance event。

### 4.5 `review_or_governance_candidate_handoff`

Purpose：把 accountant response 中暴露的长期记忆、review 或治理相关信号交给后续 workflow 评估。

Consumer / downstream authority：Review Node、Governance Review Node、Case Memory Update Node、Post-Batch Lint Node。

Required fields：

| Field | Meaning |
| --- | --- |
| `candidate_handoff_id` | candidate handoff 引用 |
| `transaction_id` | 绑定交易 |
| `source_intervention_ids` | 来源 intervention |
| `candidate_type` | 候选类别 |
| `candidate_summary` | 候选信号说明 |
| `supporting_refs` | 支撑该候选的 refs |
| `required_authority_path` | 必须由哪个后续 authority path 处理 |

Allowed `candidate_type` values：

- `profile_change_signal`
- `entity_candidate_context`
- `alias_confirmation_candidate`
- `role_confirmation_candidate`
- `case_memory_update_candidate`
- `rule_candidate`
- `rule_conflict_candidate`
- `automation_policy_candidate`
- `governance_review_candidate`
- `review_required_signal`

Allowed `required_authority_path` values：

- `review_node`
- `case_memory_update_node`
- `governance_review_node`
- `evidence_intake_reprocessing`
- `post_batch_lint_node`

Optional fields：

- `affected_entity_refs`
- `affected_alias_text`
- `affected_role`
- `affected_rule_refs`
- `affected_profile_field_hint`
- `risk_flags`
- `conflict_refs`

Validation rules：

- candidate handoff 必须写明 `required_authority_path`。
- `alias_confirmation_candidate` 不能写成 `approved_alias`。
- `role_confirmation_candidate` 不能写成 confirmed role。
- `rule_candidate` 不能写成 active rule。
- `automation_policy_candidate` 不能放宽或升级 automation policy。
- `governance_review_candidate` 不能包含 `approval_status = approved`。

Durable / candidate / runtime：

- 该 handoff 是 candidate-only runtime output。
- 只有后续 Review / Governance / Case Memory workflow 才能把它转化为 durable memory 或 approved governance event。

### 4.6 `still_pending_handoff`

Purpose：在 accountant 未答、回答不足、回答冲突或仍缺关键 evidence 时，保留 pending / unresolved 语义。

Consumer / downstream authority：workflow orchestrator、Coordinator future run、Review Node。

Required fields：

| Field | Meaning |
| --- | --- |
| `handoff_id` | handoff 引用 |
| `transaction_id` | 绑定交易 |
| `pending_status` | 未解决状态 |
| `remaining_issue_ids` | 仍未解决的 issue |
| `unresolved_reason` | 为什么仍不能继续 |
| `next_clarification_target` | 下一步最小可回答问题类别 |

Allowed `pending_status` values：

- `awaiting_accountant_response`
- `answer_incomplete`
- `answer_ambiguous`
- `answer_conflicting`
- `evidence_still_missing`
- `authority_still_blocked`
- `requires_review_instead_of_pending`
- `requires_governance_instead_of_pending`

Optional fields：

- `conflict_refs`
- `prior_intervention_refs`
- `suggested_followup_question`
- `review_note`

Validation rules：

- `remaining_issue_ids` 不能为空。
- `unresolved_reason` 必须具体说明缺什么或冲突在哪里。
- 如果问题实际需要 review / governance，必须使用对应 status，不能伪装成普通 missing answer。
- 不能使用 confidence 语言掩盖 unresolved state。

Durable / candidate / runtime：

- handoff 是 runtime-only。
- 相关 unanswered / conflicting interaction 可以另行写入 `Intervention Log`。

## 5. Field Authority and Memory Boundary

`transaction_id` 的 source of truth 是 `Transaction Identity Node`。本节点只能引用，不能分配、合并、重写或去重。

客观交易字段的 source of truth 是 Evidence Intake / Preprocessing 和 durable evidence references。Accountant 自然语言回答可以补充 context，但不能覆盖 raw evidence。

`pending_issue_context` 的 source of truth 是触发本节点的 upstream node。本节点可以合并、转写成 accountant-facing question，但不能发明上游卡点。

`authority_limit_context` 的 source of truth 是上游 effective authority、Profile、Entity / Rule / Governance context 和 Review / Governance boundary。本节点不能扩大 authority。

`Intervention Log` 是本节点唯一可写 durable store。它保存 accountant 介入过程，不保存 final accounting result，也不作为 deterministic runtime decision source。

以下字段或对象永远不能由本节点变成 durable memory authority：

- `candidate_alias_text`
- `candidate_role`
- `candidate_entity_refs`
- `candidate_rule_refs`
- `structured_response_claims`
- `suggested_question_targets`
- `request_trace`
- `upstream_confidence`
- `upstream_policy_trace`
- `accountant_confidence_note`

以下内容只能在后续 authority path 批准后成为 durable memory：

- profile structural fact：只能经 Review / profile authority path 确认后写入 `Profile`。
- entity / alias / role：只能经 Review / Governance Review 后写入 `Entity Log` 或 effective governance projection。
- case memory：只能经交易完成后的 `Case Memory Update Node` 形成，不由本节点直接写入。
- active rule：只能经 accountant / governance approval 后写入 `Rule Log`。
- automation policy change：放宽或升级必须 accountant / governance approval；自动降级若由 lint pass 触发，也不属于本节点。
- governance event：只能由 `Governance Review Node` 批准或记录。

Audit vs learning / logging boundary：

- `Transaction Log` 是 audit-facing final processing record，只写和查询，不参与本节点 runtime decision。
- `Intervention Log` 保存 pending intervention 过程，可供 review / governance / future coordinator context 使用，但不是 learning layer 本身。
- `Log` 在本设计中表示 durable long-term meaningful information storage；临时 question queue、candidate queue、runtime handoff、report draft 不能因为是列表就称为 `Log`。

## 6. Validation Rules

Contract-level validation rules：

- 每次 coordination 必须绑定 `client_id`、`batch_id`、`transaction_id` 和至少一个 upstream issue。
- 每个 accountant question 必须能追溯到具体 issue 和 supporting refs。
- 每个 output 必须保留相关 authority boundary，尤其是 no direct business memory mutation。
- 本节点只能写 `Intervention Log`；所有其他 output 都是 runtime-only 或 candidate-only。
- `new_entity_candidate` 可以支持当前交易后续 case judgment context，但不能支持 rule match、stable entity authority 或 rule promotion。
- Case Judgment 的 candidate signals 可以作为 input context，但不能被本节点写成 long-term memory 或 governance approval。

Input invalid conditions：

- 缺少 stable `transaction_id`。
- 缺少 `pending_issue_context` 或上游卡点不能绑定具体 transaction / evidence / issue。
- 当前交易已经 final processed、JE generated 或 written to `Transaction Log`。
- request 要求本节点执行 final classification、JE、Transaction Log write、Profile / Entity / Case / Rule / Governance mutation。
- `authority_limit_context.memory_mutation_policy` 不是 `intervention_log_only_no_business_memory_mutation`。

Output invalid conditions：

- question 把候选对象包装为 confirmed fact。
- output 将 accountant answer 直接写成 Profile truth、approved alias、confirmed role、stable entity、case memory、active rule 或 approved governance event。
- output 使用 `Transaction Log` 作为 runtime pending decision source。
- still-unresolved / conflicting state 被标成可以自动 completion。
- review-required 或 governance-needed 被降级为 ordinary pending completion。
- `intervention_log_record` 缺少 authority boundary 或 source issue references。

Stop / ask conditions for unresolved contract authority：

- 如果后续设计要求本节点直接接收并保存 raw supplemental evidence，而不经过 Evidence Intake / Evidence Log 边界，应停止并确认 evidence re-intake contract。
- 如果 workflow 需要把 accountant clarification 直接作为 current-batch final classification approval，应停止并确认 Review Node 边界。
- 如果产品想让本节点创建 / approve durable entity、alias、role、rule、profile 或 governance changes，应停止并确认治理 authority 是否改变。
- 如果 exact routing enum 要统一 across Coordinator、Review、Case Judgment、Governance Review，应在跨节点 contract freeze 中决定，不应由本节点单独发明。

## 7. Examples

### 7.1 Valid minimal example

```json
{
  "pending_coordination_request": {
    "coordination_request_id": "coordreq_01",
    "client_id": "client_abc",
    "batch_id": "batch_2026_05",
    "transaction_id": "txn_01HY",
    "trigger_source_node": "case_judgment",
    "pending_issue_context": [
      {
        "issue_id": "issue_01",
        "source_node": "case_judgment",
        "issue_type": "case_evidence_insufficient",
        "issue_summary": "Home Depot 历史案例有 business / personal mixed-use，本笔缺 receipt。",
        "blocking_reason": "当前 evidence 不足以判断业务用途。",
        "question_target": "business_purpose",
        "supporting_refs": ["evidence_bank_01", "case_ref_home_depot_mixed_use"]
      }
    ],
    "authority_limit_context": {
      "allowed_next_actions": ["ask_accountant", "record_intervention", "route_to_review", "remain_pending"],
      "hard_blocks": [],
      "memory_mutation_policy": "intervention_log_only_no_business_memory_mutation"
    },
    "transaction_context": {
      "transaction_id": "txn_01HY",
      "objective_transaction_basis": {
        "transaction_date": "2026-05-02",
        "amount_abs": 184.22,
        "direction": "outflow",
        "bank_account": "bank_main"
      },
      "evidence_refs": ["evidence_bank_01"],
      "evidence_quality_status": "missing_evidence",
      "raw_description": "HOME DEPOT #4521"
    }
  },
  "accountant_clarification_request": {
    "clarification_request_id": "clarq_01",
    "coordination_request_id": "coordreq_01",
    "client_id": "client_abc",
    "batch_id": "batch_2026_05",
    "transaction_id": "txn_01HY",
    "question_status": "drafted",
    "question_target": "business_purpose",
    "question_text": "这笔 Home Depot 支出是业务材料、私人用途，还是需要补 receipt 才能判断？",
    "source_issue_ids": ["issue_01"],
    "why_needed": "历史案例存在 mixed-use，当前缺少能支持分类的用途证据。",
    "supporting_refs": ["evidence_bank_01", "case_ref_home_depot_mixed_use"],
    "authority_warning": "回答只作为当前交易 intervention context，不会自动创建 rule 或修改 entity / case memory。"
  }
}
```

### 7.2 Valid richer example

```json
{
  "accountant_response_payload": {
    "response_id": "resp_01",
    "clarification_request_id": "clarq_01",
    "accountant_id": "acct_01",
    "responded_at": "2026-05-06T10:30:00-07:00",
    "response_type": "supplemental_evidence_provided",
    "response_text": "这是业务材料，receipt 已补上传，都是水泥和钢筋。",
    "attached_evidence_refs": ["upload_receipt_77"],
    "target_transaction_id": "txn_01HY",
    "target_issue_ids": ["issue_01"],
    "structured_response_claims": {
      "business_purpose_claim": "business_materials",
      "receipt_mentions": ["cement", "rebar"]
    }
  },
  "intervention_log_record": {
    "intervention_id": "int_01",
    "client_id": "client_abc",
    "batch_id": "batch_2026_05",
    "transaction_id": "txn_01HY",
    "coordination_request_id": "coordreq_01",
    "intervention_type": "supplemental_evidence_received",
    "source_issue_ids": ["issue_01"],
    "question_text": "这笔 Home Depot 支出是业务材料、私人用途，还是需要补 receipt 才能判断？",
    "accountant_response_text": "这是业务材料，receipt 已补上传，都是水泥和钢筋。",
    "accountant_id": "acct_01",
    "created_at": "2026-05-06T10:31:00-07:00",
    "authority_boundary": "Intervention only; no Profile, Entity, Case, Rule, Governance, Transaction Log, JE, or final classification write.",
    "resolution_status": "answered_for_current_context",
    "attached_evidence_refs": ["upload_receipt_77"],
    "resolved_issue_ids": ["issue_01"]
  },
  "supplemental_context_handoff": {
    "handoff_id": "suppctx_01",
    "transaction_id": "txn_01HY",
    "source_intervention_id": "int_01",
    "handoff_type": "supplemental_evidence",
    "target_issue_ids": ["issue_01"],
    "content_summary": "Accountant provided receipt and business-purpose context for current transaction.",
    "source_refs": ["int_01", "upload_receipt_77"],
    "requires_re_intake": true,
    "attached_evidence_refs": ["upload_receipt_77"],
    "remaining_authority_limits": ["no_direct_rule_creation", "no_direct_case_memory_write"]
  }
}
```

### 7.3 Invalid example with reason

```json
{
  "review_or_governance_candidate_handoff": {
    "candidate_handoff_id": "cand_01",
    "transaction_id": "txn_02",
    "source_intervention_ids": ["int_02"],
    "candidate_type": "alias_confirmation_candidate",
    "candidate_summary": "Accountant said TIMS COFFEE is Tim Hortons.",
    "supporting_refs": ["int_02"],
    "required_authority_path": "governance_review_node",
    "affected_alias_text": "TIMS COFFEE",
    "approval_status": "approved"
  }
}
```

Invalid reason：

- `Coordinator / Pending Node` 可以提出 `alias_confirmation_candidate`，但不能设置 `approval_status = approved`。
- alias approval 属于 Review / Governance authority，不属于 pending clarification write authority。
- 该回答最多可进入 candidate handoff 和 `Intervention Log`，不能直接变成 approved alias 或 rule-match authority。

## 8. Open Contract Boundaries

- `Intervention Log` 的全局 schema 尚未在 active docs 中完整冻结；本文件只定义本节点最小可写 record category。
- accountant 补交 raw evidence 后，是由本节点先捕捉再转交，还是必须由 Evidence Intake 重新接收，仍需跨节点 contract 决定；本文件用 `requires_re_intake` 保留边界。
- accountant 回答后 exact reprocessing target 和 rerun boundary 尚未冻结；本文件只定义 handoff readiness，不定义执行算法。
- ordinary pending、review-required、governance-needed、still-unresolved 的全局 routing enum 尚未跨节点冻结；本文件中的 status 是 Coordinator data-contract labels，不是最终 workflow routing enum。
- 多笔 pending 交易的问题聚合、去重、排序和展示方式仍未冻结；本文件只允许 `grouped_issue_ids` 表示问题合并，不定义 UI 或 batching algorithm。
- accountant response 何时足以支持 current operational classification、何时必须进入 Review Node，还需要 Case Judgment / Review Node Stage 3 共同收敛。

## 9. Self-Review

- 已按要求阅读 `AGENTS.md`、`TASK_STATE.md`、`PLANS.md`、`CLAUDE.md`、`DECISIONS.md`、`supporting documents/communication_preferences.md`、`supporting documents/development_workflow.md`、`supporting documents/node_design_roadmap.md`、`new system/new_system.md`、本节点 Stage 1/2，以及可用 Superpowers docs：`using-superpowers/SKILL.md`、`brainstorming/SKILL.md`；project workflow skill `ai-bookkeeper-node-design-facilitation` 在当前环境不存在，因此使用 repo roadmap 与本节点 Stage 1/2 docs 作为 workflow authority。
- 已确认 `supporting documents/node_design_roadmap_zh.md` 在工作树中缺失；未 invent 该文件内容。
- 本文件只写 Stage 3 data contract，没有进入 Stage 4 execution algorithm、Stage 5 technical implementation、Stage 6 test matrix 或 Stage 7 coding-agent task contract。
- 未把 `Transaction Log` 作为 runtime decision source。
- 未给本节点新增 Profile、Entity Log、Case Log、Rule Log、Governance Log 或 Transaction Log 写权限。
- 未把 accountant response、Case Judgment candidate、new_entity_candidate、candidate alias、candidate role 或 candidate rule 包装成 durable authority。
- Target file written only because live docs answered the gating question：本节点可以 durable 写入的边界仅限 `Intervention Log`，业务长期记忆变化只能 candidate-only 或交由 Review / Governance authority。
