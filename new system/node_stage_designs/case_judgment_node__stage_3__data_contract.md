# Case Judgment Node — Stage 3：Data Contract Spec

## 1. Stage 范围

本 Stage 3 只定义 `Case Judgment Node` 的 data contract。

它以前置已批准文档为基础：

- `new system/node_stage_designs/case_judgment_node__stage_1__functional_intent.md`
- `new system/node_stage_designs/case_judgment_node__stage_2__logic_and_boundaries.md`

本阶段把 Stage 1/2 中已经确定的 runtime judgment、authority boundary、memory/log boundary 转换成 implementation-facing 的输入/输出对象类别、字段含义、字段 authority、runtime-only 与 durable-memory 边界、validation rules 和紧凑示例。

本阶段不定义：

- step-by-step execution algorithm
- prompt structure
- technical module path、class、API、DB、migration 或 storage engine
- test matrix / fixture plan
- coding-agent task contract
- final router implementation
- 未由 active docs 支持的新 product authority

## 2. Contract Position in Workflow

### 2.1 Upstream handoff consumed

`Case Judgment Node` 消费的是 `deterministic path 未完成` 后的 runtime handoff。

上游必须已经完成或明确未完成：

- `Evidence Intake / Preprocessing Node`
- `Transaction Identity Node`
- `Profile / Structural Match Node`
- `Entity Resolution Node`
- `Rule Match Node`

该节点不能接收尚未分配 `transaction_id` 的交易，也不能替代上游重新执行 structural match、entity resolution 或 rule match。

### 2.2 Downstream handoff produced

`Case Judgment Node` 输出 `case_judgment_result`。

下游消费方向包括：

- `Coordinator / Pending Node`：消费 `pending` reason、missing information 和 focused question context。
- `Review Node`：消费 runtime recommendation、rationale、review reason 和 candidate signals。
- `JE Generation Node`：只能在后续 authority 允许且 classification outcome 已达到该节点要求时消费 accounting treatment，不直接把 Case Judgment 当成 final approval。
- `Transaction Logging Node`：后续可把结果和审计轨迹写入 `Transaction Log`，但 Case Judgment 本身不写。
- `Case Memory Update Node`：只可在后续确认后消费 candidate signals 或 final outcome；不能把 runtime judgment 直接当作 durable case。
- `Governance Review Node`：只可消费 governance candidate signal；不能把该节点输出当作 approval。

### 2.3 Logs / memory stores read

该节点可读取或消费以下 runtime context / durable references：

- `Evidence Log` references：原始证据、小票、支票、accountant context 等证据引用。
- `Profile` / structural context：客户结构事实和上游 structural result。
- `Entity Log` context：entity、alias、role、status、authority、automation_policy、identity risk。
- `Case Log` / case memory pack：历史案例、最终分类、证据、例外和 accountant correction。
- `Rule Log` / rule path context：rule miss、blocked rule、rule lifecycle、rule-required condition。
- `Intervention Log` references：近期 accountant 介入、回答、修正、确认。
- `Governance Log` references：未解决或已生效的 governance restriction。
- `Knowledge Log / Summary Log`：由 entity、case、rule、governance 历史编译出的客户知识摘要；不作为 deterministic rule source。

`Transaction Log` 是 audit-facing，按 active baseline 不参与 runtime decision；本节点不得把 `Transaction Log` 当作学习层或判断依据。

### 2.4 Logs / memory stores written or candidate-only

`Case Judgment Node` 不直接写入任何 durable log / memory store。

它只能输出 candidate-only signals：

- `case_memory_update_candidate`
- `entity_candidate_signal`
- `alias_candidate_signal`
- `role_candidate_signal`
- `rule_candidate_signal`
- `automation_policy_or_governance_candidate`

这些 signal 不是 durable memory operation，不改变 active entity、alias、role、rule、case、automation policy 或 governance state。

## 3. Input Contracts

### 3.1 `case_judgment_input`

**Purpose**

`case_judgment_input` 是本节点唯一入口 envelope，表示一笔非结构性交易在 deterministic path 未完成后进入 case-based runtime judgment。

**Source authority**

由 workflow orchestration 汇总上游节点输出形成。字段 authority 来自各上游节点和对应 durable store；本节点只消费，不重写来源事实。

**Required fields**

- `transaction_context`
- `deterministic_path_context`
- `entity_context`
- `case_memory_context`
- `current_evidence_context`
- `authority_context`

**Optional fields**

- `profile_structural_context`
- `rule_context`
- `intervention_context`
- `governance_context`
- `knowledge_summary_context`
- `runtime_notes`

**Validation / rejection rules**

输入无效并应拒绝进入 judgment，如果：

- 缺少 `transaction_context.transaction_id`
- 交易仍处于 upstream identity / preprocessing 未完成状态
- `deterministic_path_context.path_completed = true`
- 缺少 `entity_context.status`
- 缺少 `authority_context.max_allowed_action`
- 引用的 evidence / case / entity / rule id 无法追溯到相应来源
- `Transaction Log` 被作为 runtime learning source 传入

**Runtime-only vs durable references**

`case_judgment_input` 是 runtime-only envelope。它可以携带 durable store references，但 envelope 自身不是 durable memory。

### 3.2 `transaction_context`

**Purpose**

说明当前交易的客观结构事实和证据入口。

**Source authority**

来自 `Evidence Intake / Preprocessing Node` 与 `Transaction Identity Node`。`transaction_id` authority 来自 transaction identity layer。

**Required fields**

- `transaction_id`：稳定交易 ID。
- `date`：交易日期。
- `amount`：绝对金额。
- `direction`：资金方向；必须沿用共享交易 contract 的 direction 语义。
- `bank_account`：客户侧银行账户引用。
- `evidence_refs`：本笔交易可追溯证据引用列表。

**Optional fields**

- `raw_description`
- `description`
- `receipt_ref`
- `cheque_ref`
- `counterparty_surface_text`
- `import_batch_id`

**Validation / rejection rules**

- `amount` 不得用正负号表达 direction。
- `direction` 缺失时无效。
- `evidence_refs` 为空时，只有当 upstream 明确标记为 evidence-limited runtime case 时才可继续；否则无效。
- `description = null` 合法，不得强行把缺失 description 当作 invalid。

**Runtime-only vs durable references**

交易结构字段属于当前 transaction record；`evidence_refs` 是 durable evidence references。该节点不能修改交易身份或原始证据。

### 3.3 `deterministic_path_context`

**Purpose**

说明为什么当前交易没有被 structural / rule deterministic path 完成。

**Source authority**

来自 `Profile / Structural Match Node` 与 `Rule Match Node`。

**Required fields**

- `path_completed`：必须为 `false` 才能进入本节点。
- `trigger_reason`
- `blocked_reasons`
- `structural_result_status`
- `rule_match_status`

**Optional fields**

- `matched_rule_id`
- `blocked_rule_ids`
- `rule_required_reason`
- `profile_structural_reason`
- `deterministic_trace_refs`

**Allowed values**

`trigger_reason` 允许：

- `no_applicable_rule`
- `rule_not_applicable`
- `rule_blocked_by_authority`
- `rule_required_but_missing`
- `review_required_by_policy`
- `deterministic_path_insufficient`

`rule_match_status` 允许：

- `not_attempted`
- `no_match`
- `matched_but_not_applicable`
- `blocked`
- `requires_review`

**Validation / rejection rules**

- `path_completed = true` 时无效；已完成交易不应进入本节点。
- 如果 `rule_match_status = blocked`，必须提供至少一个 `blocked_reasons`。
- 如果 `trigger_reason = rule_required_but_missing`，`authority_context.max_allowed_action` 不得允许直接 operational classification。

**Runtime-only vs durable references**

该对象是 runtime-only handoff。`matched_rule_id` 或 `blocked_rule_ids` 只是 durable `Rule Log` references，不代表本节点能修改 rule。

### 3.4 `entity_context`

**Purpose**

说明当前交易的 identity basis、alias / role 状态和自动化权限风险。

**Source authority**

来自 `Entity Resolution Node` 和 `Entity Log`。

**Required fields**

- `status`
- `confidence`
- `reason`
- `evidence_used`

**Optional fields**

- `entity_id`
- `display_name`
- `matched_alias`
- `alias_status`
- `candidate_role`
- `automation_policy`
- `entity_status`
- `blocking_reason`
- `candidate_entities`
- `risk_flags`

**Allowed values**

`status` 必须是 active baseline 已定义的 entity resolution status：

- `resolved_entity`
- `resolved_entity_with_unconfirmed_role`
- `new_entity_candidate`
- `ambiguous_entity_candidates`
- `unresolved`

`alias_status` 如存在，必须是：

- `candidate_alias`
- `approved_alias`
- `rejected_alias`

`automation_policy` 如存在，必须是：

- `eligible`
- `case_allowed_but_no_promotion`
- `rule_required`
- `review_required`
- `disabled`

**Validation / rejection rules**

- `resolved_entity` 必须提供 `entity_id`。
- `new_entity_candidate` 不得提供 stable `entity_id` 作为 durable authority；如有 candidate id，只能在 candidate signal 中表达。
- `ambiguous_entity_candidates` 应提供 `candidate_entities` 或 `blocking_reason`。
- `rejected_alias` 不能支持 operational classification。
- `automation_policy = disabled` 或 `review_required` 时，输出不得为 operational classification。
- `automation_policy = rule_required` 且无 approved active rule 时，输出不得为 operational classification。

**Runtime-only vs durable references**

`candidate_role`、`new_entity_candidate`、`candidate_alias` 是 runtime-only 或 candidate-only，不得由本节点写入 stable Entity Log。`entity_id`、`approved_alias`、confirmed role、automation policy 的 source of truth 是 `Entity Log` / governance-approved state。

### 3.5 `case_memory_context`

**Purpose**

提供历史先例和例外条件，供本节点判断当前交易是否有 case-supported basis。

**Source authority**

来自 `Case Log` 和由 `Knowledge Compilation Node` 编译出的 customer knowledge summary。`Case Log` 保存真实历史案例、最终分类、证据、例外和 accountant correction。

**Required fields**

- `case_refs`
- `case_summary`
- `precedent_fit_basis`

**Optional fields**

- `similar_case_count`
- `exception_patterns`
- `accountant_corrections`
- `negative_cases`
- `case_freshness`
- `source_summary_ref`

**Validation / rejection rules**

- `case_refs` 可以为空，但必须明确 `case_summary` 表示无可用先例；不得把无案例伪装成稳定模式。
- `case_summary` 不能只有计数；必须表达适用条件或说明条件未知。
- accountant correction 必须保留来源 reference，不能被压缩成无来源的“系统知识”。

**Runtime-only vs durable references**

本对象是 runtime case pack。`case_refs` 指向 durable `Case Log`，但本节点不能 append、update、promote 或 invalidate case memory。

### 3.6 `current_evidence_context`

**Purpose**

说明本次交易有哪些证据支持、削弱或推翻历史先例。

**Source authority**

来自 `Evidence Log`、当前 transaction evidence、receipt、cheque、accountant-provided context。

**Required fields**

- `available_evidence`
- `evidence_strength_summary`

**Optional fields**

- `receipt_details_summary`
- `cheque_details_summary`
- `accountant_context_refs`
- `missing_evidence`
- `conflicting_evidence`
- `mixed_use_indicators`
- `amount_or_context_anomaly`

**Validation / rejection rules**

- 如果存在 `conflicting_evidence`，输出必须体现 pending 或 review caution；不得隐藏冲突。
- 如果 `evidence_strength_summary` 只说明“模型觉得像”，缺少证据 reference，则不能支持 operational classification。
- accountant-provided context 必须作为 evidence reference，不得被本节点改写成 durable policy。

**Runtime-only vs durable references**

证据本身由 `Evidence Log` 保存。本节点只读取引用并生成 runtime rationale。

### 3.7 `authority_context`

**Purpose**

定义本节点当前最多允许输出什么 runtime action，防止 LLM 或 case reasoning 扩大 automation authority。

**Source authority**

来自 entity automation policy、rule lifecycle、profile / governance restrictions、review requirements 和 workflow orchestration 的 deterministic eligibility 判断。

**Required fields**

- `max_allowed_action`
- `hard_blocks`
- `candidate_signal_allowed`

**Optional fields**

- `requires_accountant_confirmation`
- `requires_governance_review`
- `authority_reason`
- `policy_refs`

**Allowed values**

`max_allowed_action` 允许：

- `operational_classification_allowed`
- `pending_only`
- `review_required_only`
- `candidate_signal_only`

**Validation / rejection rules**

- `hard_blocks` 非空时，必须解释是否限制 `operational_classification`。
- `max_allowed_action != operational_classification_allowed` 时，输出不得为 `operational_classification`。
- `candidate_signal_allowed = false` 时，输出不得包含 candidate signals。

**Runtime-only vs durable references**

`authority_context` 是 runtime authority envelope。它引用 durable policy / governance state，但本节点不能修改这些 state。

## 4. Output Contracts

### 4.1 `case_judgment_result`

**Purpose**

表达本节点对当前交易的 runtime judgment：进入 operational classification path、pending path，或 review-required path，并提供 rationale 和 candidate-only signals。

**Consumer / downstream authority**

由 `Coordinator / Pending Node`、`Review Node`、`JE Generation Node`、`Transaction Logging Node`、`Case Memory Update Node`、`Governance Review Node` 后续消费。下游各自拥有自己的 approval、logging、JE 或 governance authority。

**Required fields**

- `transaction_id`
- `judgment_status`
- `authority_used`
- `rationale`
- `evidence_refs_used`
- `case_refs_used`
- `memory_write_effect`

**Optional fields**

- `accounting_treatment_proposal`
- `pending_request_context`
- `review_required_context`
- `candidate_signals`
- `confidence_label`
- `risk_flags`
- `blocked_reasons`
- `trace_summary`

**Allowed statuses**

`judgment_status` 允许：

- `operational_classification`
- `pending`
- `review_required`

这些是 Stage 3 data contract status，不冻结最终 router enum 或 UI label。

**Validation rules**

- `transaction_id` 必须与 input 一致。
- `memory_write_effect` 必须为 `none`。
- `judgment_status = operational_classification` 时，必须有 `accounting_treatment_proposal`、足够 `rationale`、`evidence_refs_used`，且 `authority_used.max_allowed_action = operational_classification_allowed`。
- `judgment_status = pending` 时，必须有 `pending_request_context`。
- `judgment_status = review_required` 时，必须有 `review_required_context` 或 blocking authority explanation。
- 输出不得包含任何表示 durable write succeeded、rule promoted、entity approved、alias approved、role confirmed 或 governance approved 的字段。

**Durable memory effect**

本对象是 runtime-only result。它不写 durable memory。后续节点可以把它作为 audit trail source、review context 或 candidate signal source，但不能把它直接当作 durable approval。

### 4.2 `accounting_treatment_proposal`

**Purpose**

当 `judgment_status = operational_classification` 时，表达当前交易的 operational accounting proposal。它是 runtime recommendation，不是 final accountant approval。

**Consumer / downstream authority**

主要供 `Review Node`、后续 eligible 的 `JE Generation Node` 和 audit formation 使用。最终是否可落账由下游 authority 和 review boundary 决定。

**Required fields**

- `classification_basis`
- `proposed_accounting_treatment`
- `case_support_summary`
- `current_evidence_support_summary`

**Optional fields**

- `coa_account_ref`
- `hst_gst_treatment_ref`
- `business_use_context`
- `exception_handling_note`
- `confidence_label`

**Allowed values**

`classification_basis` 允许：

- `case_supported`
- `current_evidence_supported_new_entity`
- `case_supported_with_current_evidence_override`

`confidence_label` 如存在，允许：

- `high`
- `medium`
- `low`

`low` 不得与 `judgment_status = operational_classification` 同时出现。

**Validation rules**

- 必须说明 case precedent 与 current evidence 如何共同支持 proposal。
- `new_entity_candidate` 场景只能使用 `current_evidence_supported_new_entity` 或更保守路径；不得暗示已有 stable entity / rule authority。
- `coa_account_ref`、`hst_gst_treatment_ref` 的具体共享 schema 未在本 Stage 冻结；如填写，只能作为 reference / proposal，不得被解释为 JE line。

**Durable memory effect**

runtime-only proposal。不能创建 Case Log、Rule Log、Entity Log 或 Governance Log 记录。

### 4.3 `pending_request_context`

**Purpose**

当证据可补、上下文可问清时，为 `Coordinator / Pending Node` 提供聚焦问题上下文。

**Consumer / downstream authority**

`Coordinator / Pending Node` 负责生成和发送 accountant-facing question。本节点不直接提问。

**Required fields**

- `pending_reason`
- `missing_or_unclear_information`
- `question_focus`
- `why_not_auto_classified`

**Optional fields**

- `suggested_evidence_to_request`
- `candidate_answer_options`
- `case_context_for_question`
- `review_caution`

**Allowed values**

`pending_reason` 允许：

- `missing_receipt_or_support`
- `unclear_business_purpose`
- `insufficient_current_evidence`
- `needs_accountant_context`
- `new_entity_needs_context`
- `case_precedent_fit_unclear`

**Validation rules**

- pending 必须是可通过补信息解决的问题。
- 如果问题本质是 authority / governance block，不得输出为 pending-only；应使用 `review_required`。
- `question_focus` 应指向最小必要信息，不得要求 accountant 重新审核整条 pipeline。

**Durable memory effect**

runtime-only handoff。accountant 后续回答应由 `Intervention Log` / review workflow 记录，不由本节点写入。

### 4.4 `review_required_context`

**Purpose**

当问题不是简单补信息，而是 authority、policy、identity、role、rule 或 governance risk 要求人审或治理时，提供 review-required explanation。

**Consumer / downstream authority**

`Review Node`、必要时 `Governance Review Node` 或 pending-review flow 消费。具体 routing 留给后续阶段。

**Required fields**

- `review_reason`
- `blocking_basis`
- `why_case_judgment_cannot_override`

**Optional fields**

- `governance_candidate_hint`
- `identity_risk_summary`
- `policy_refs`
- `conflict_summary`
- `suggested_review_focus`

**Allowed values**

`review_reason` 允许：

- `automation_policy_review_required`
- `automation_disabled`
- `rule_required_without_rule`
- `unconfirmed_required_role`
- `rejected_or_unsafe_alias`
- `ambiguous_or_unresolved_identity`
- `governance_block`
- `conflicting_evidence_requires_business_judgment`

**Validation rules**

- 必须保留 blocked reason，不得将 hard block 改写成 soft caution。
- 如果 `automation_policy = disabled`、`review_required` 或 `rule_required` without approved rule，输出必须为 `review_required`。
- 如果 identity 是 `ambiguous_entity_candidates` 或 `unresolved` 且不能安全归属，输出必须为 `review_required` 或 pending；不得 operational classification。

**Durable memory effect**

runtime-only review handoff。不能 approve / reject governance event。

### 4.5 `candidate_signals`

**Purpose**

表达本节点观察到的后续 memory update 或 governance review 候选信号。

**Consumer / downstream authority**

`Case Memory Update Node`、`Review Node`、`Governance Review Node`、`Post-Batch Lint Node` 可评估这些 signal。它们不是 approval。

**Required fields per signal**

- `signal_type`
- `signal_reason`
- `source_evidence_refs`
- `requires_authority`

**Optional fields per signal**

- `related_entity_refs`
- `related_case_refs`
- `related_rule_refs`
- `proposed_candidate_payload`
- `risk_note`

**Allowed signal types**

- `case_memory_update_candidate`
- `entity_candidate_signal`
- `alias_candidate_signal`
- `role_candidate_signal`
- `rule_candidate_signal`
- `automation_policy_or_governance_candidate`

**Allowed `requires_authority` values**

- `case_memory_update_node`
- `accountant_review`
- `governance_review`

**Validation rules**

- 每个 signal 必须有 source evidence reference。
- `rule_candidate_signal` 不得出现在 `automation_policy = case_allowed_but_no_promotion` 的上下文中，除非 signal 明确表示“禁止 promotion 的风险说明”，而不是 promotion candidate。
- `entity_candidate_signal` 不得包含 stable entity approval。
- `alias_candidate_signal` 不得把 alias 标记为 approved。
- `role_candidate_signal` 不得把 role 标记为 confirmed。
- `automation_policy_or_governance_candidate` 不得改变当前 automation policy。

**Durable memory effect**

candidate-only。所有长期变化必须经后续 owner node 和 accountant/governance authority。

## 5. Field Authority and Memory Boundary

### 5.1 Source of truth

- `transaction_id`：`Transaction Identity Node` / transaction identity layer。
- `amount`、`direction`、`date`、`bank_account`：preprocessing 后的 transaction record；`direction` 是资金方向 source of truth，金额保持 absolute value。
- `evidence_refs`：`Evidence Log`。
- `entity_id`、approved alias、confirmed role、entity status、automation policy：`Entity Log` 与对应 governance-approved state。
- `case_refs`、historical outcome、accountant correction：`Case Log`。
- active rule、rule lifecycle、rule-required condition：`Rule Log`。
- accountant intervention / answer / correction：`Intervention Log`。
- governance restriction / approval status：`Governance Log`。
- runtime judgment、rationale、pending reason、review reason：`Case Judgment Node` 本次运行输出，仅为 runtime authority。

### 5.2 Fields that can never become durable memory by this node

以下字段或对象不能由本节点直接成为 durable memory：

- `case_judgment_result`
- `accounting_treatment_proposal`
- `rationale`
- `confidence_label`
- `pending_request_context`
- `review_required_context`
- `candidate_signals`
- `candidate_role`
- `new_entity_candidate`
- `alias_candidate_signal`
- `rule_candidate_signal`
- 任何 LLM semantic explanation

### 5.3 Fields that can become durable only after approval / owner-node handling

以下信息只有通过后续 authority path 才可能进入长期记忆：

- final accountant-confirmed classification：经 review / confirmed workflow 后，才可由 `Case Memory Update Node` 写入 `Case Log`。
- new entity / alias / role：必须经 `Review Node` / `Governance Review Node` / approved entity governance path。
- rule candidate：必须经 accountant / governance approval 后才可写入 `Rule Log`。
- automation policy change：降级可由 lint pass 触发并记录，升级或放宽必须 accountant approval；Case Judgment 只能提出 signal。
- governance event：必须由 governance workflow 创建、审批、记录。

### 5.4 Audit vs learning / logging boundary

`Transaction Log` 保存最终处理结果和审计轨迹；它只写和查询，不参与 runtime decision，也不是 learning layer。

Case Judgment 的 runtime result 后续可以作为 Transaction Log 的 audit trace 输入，但不能反向成为本节点的 runtime evidence source。

Case Judgment 可以帮助形成 audit explanation，但不能把 audit record、runtime rationale 或单次 outcome 直接转成 case memory、rule 或 governance authority。

## 6. Validation Rules

### 6.1 Contract-level validation rules

- 每个输入必须有稳定 `transaction_id`。
- 只有 `deterministic_path_context.path_completed = false` 的交易可以进入本节点。
- `authority_context.max_allowed_action` 是输出上限；LLM rationale 不能扩大它。
- `new_entity_candidate` 可以支持当前 operational classification，但只能在 authority 允许且 current evidence 足够强时；它不能支持 rule match、rule promotion 或 stable entity write。
- `Transaction Log` 不得出现在 runtime decision source 中。
- 所有 durable store references 必须可追溯；不能传入无来源的“历史通常如此”。
- 输出的 `memory_write_effect` 必须为 `none`。

### 6.2 Conditions that make the input invalid

- 缺少 `transaction_id`。
- preprocessing / identity 尚未完成。
- deterministic path 已完成。
- 缺少 entity resolution status。
- 缺少 authority context。
- 把 audit-only `Transaction Log` 当作 case memory 或 learning source。
- blocked rule / policy 状态缺少 blocked reason。
- 引用的 evidence、case、entity、rule、intervention 或 governance record 不可追溯。

### 6.3 Conditions that make the output invalid

- `operational_classification` 绕过 `review_required`、`disabled`、`rule_required` without rule、governance block、rejected alias 或 unsafe identity。
- `pending` 用于本质上需要 review / governance 的 authority block。
- `review_required` 缺少 blocking basis。
- `accounting_treatment_proposal` 没有 evidence / case support。
- 输出声称已写入 `Entity Log`、`Case Log`、`Rule Log`、`Governance Log` 或 `Transaction Log`。
- candidate signal 声称已 approved / confirmed / promoted / applied。
- `confidence_label = high` 但同时存在 unresolved material conflict 且未进入 review-required。

### 6.4 Stop / ask conditions for unresolved contract authority

后续 Stage 或实现中如遇到以下情况，应 stop and ask，不得自行补 product authority：

- 需要冻结全局 router enum 或跨节点状态机。
- 需要定义共享 accounting classification schema / JE-ready schema。
- 需要决定 `operational_classification` 是否可在无 accountant review 下直接进入 JE。
- 需要决定 candidate signal 的 durable queue schema。
- 需要改变 `Transaction Log` 是否参与 runtime decision。
- 需要允许 Case Judgment 直接写 Case Log、Rule Log、Entity Log 或 Governance Log。

## 7. Examples

### 7.1 Valid minimal example

```json
{
  "input": {
    "transaction_context": {
      "transaction_id": "txn_01HZXCASE0001",
      "date": "2026-04-30",
      "amount": "42.10",
      "direction": "outflow",
      "bank_account": "operating_chequing",
      "evidence_refs": ["ev_bank_001", "ev_receipt_001"],
      "raw_description": "HOME DEPOT #4521"
    },
    "deterministic_path_context": {
      "path_completed": false,
      "trigger_reason": "no_applicable_rule",
      "blocked_reasons": [],
      "structural_result_status": "not_structural",
      "rule_match_status": "no_match"
    },
    "entity_context": {
      "status": "resolved_entity",
      "entity_id": "ent_home_depot",
      "confidence": "high",
      "reason": "approved alias matched current bank text",
      "matched_alias": "HOME DEPOT",
      "alias_status": "approved_alias",
      "automation_policy": "eligible",
      "evidence_used": ["ev_bank_001"]
    },
    "case_memory_context": {
      "case_refs": ["case_hd_001", "case_hd_002"],
      "case_summary": "Home Depot 通常为材料费；mixed-use 例外需要 receipt 支持。",
      "precedent_fit_basis": "receipt items match prior business-material cases"
    },
    "current_evidence_context": {
      "available_evidence": ["receipt"],
      "evidence_strength_summary": "receipt shows cement and steel supplies"
    },
    "authority_context": {
      "max_allowed_action": "operational_classification_allowed",
      "hard_blocks": [],
      "candidate_signal_allowed": true
    }
  },
  "output": {
    "transaction_id": "txn_01HZXCASE0001",
    "judgment_status": "operational_classification",
    "authority_used": {
      "max_allowed_action": "operational_classification_allowed"
    },
    "accounting_treatment_proposal": {
      "classification_basis": "case_supported",
      "proposed_accounting_treatment": "materials expense treatment",
      "case_support_summary": "prior matching cases classify business materials this way",
      "current_evidence_support_summary": "receipt supports business materials"
    },
    "rationale": "当前 receipt 覆盖 mixed-use 风险，且与历史 business-material case 条件一致。",
    "evidence_refs_used": ["ev_bank_001", "ev_receipt_001"],
    "case_refs_used": ["case_hd_001", "case_hd_002"],
    "memory_write_effect": "none",
    "candidate_signals": [
      {
        "signal_type": "case_memory_update_candidate",
        "signal_reason": "receipt-backed mixed-use clarification may be useful after final confirmation",
        "source_evidence_refs": ["ev_receipt_001"],
        "requires_authority": "case_memory_update_node"
      }
    ]
  }
}
```

### 7.2 Valid richer example

```json
{
  "input": {
    "transaction_context": {
      "transaction_id": "txn_01HZXCASE0002",
      "date": "2026-04-30",
      "amount": "300.00",
      "direction": "outflow",
      "bank_account": "operating_chequing",
      "evidence_refs": ["ev_bank_010", "ev_contract_010"],
      "raw_description": "TIMS BUTTON SAAS"
    },
    "deterministic_path_context": {
      "path_completed": false,
      "trigger_reason": "no_applicable_rule",
      "blocked_reasons": [],
      "structural_result_status": "not_structural",
      "rule_match_status": "not_attempted"
    },
    "entity_context": {
      "status": "new_entity_candidate",
      "confidence": "medium",
      "reason": "new vendor surface text with supporting contract evidence",
      "matched_alias": "TIMS BUTTON SAAS",
      "alias_status": "candidate_alias",
      "evidence_used": ["ev_bank_010", "ev_contract_010"]
    },
    "case_memory_context": {
      "case_refs": [],
      "case_summary": "no prior cases for this entity",
      "precedent_fit_basis": "no precedent; current evidence only"
    },
    "current_evidence_context": {
      "available_evidence": ["contract"],
      "evidence_strength_summary": "contract clearly identifies SaaS subscription for business operations"
    },
    "authority_context": {
      "max_allowed_action": "operational_classification_allowed",
      "hard_blocks": [],
      "candidate_signal_allowed": true
    }
  },
  "output": {
    "transaction_id": "txn_01HZXCASE0002",
    "judgment_status": "operational_classification",
    "authority_used": {
      "max_allowed_action": "operational_classification_allowed"
    },
    "accounting_treatment_proposal": {
      "classification_basis": "current_evidence_supported_new_entity",
      "proposed_accounting_treatment": "software subscription treatment",
      "case_support_summary": "no durable precedent used",
      "current_evidence_support_summary": "contract supports business SaaS subscription"
    },
    "rationale": "new_entity_candidate 不提供 durable authority，但当前合同证据足够支持本笔 runtime proposal。",
    "evidence_refs_used": ["ev_bank_010", "ev_contract_010"],
    "case_refs_used": [],
    "memory_write_effect": "none",
    "candidate_signals": [
      {
        "signal_type": "entity_candidate_signal",
        "signal_reason": "new vendor may need stable entity review after transaction confirmation",
        "source_evidence_refs": ["ev_bank_010", "ev_contract_010"],
        "requires_authority": "accountant_review"
      },
      {
        "signal_type": "case_memory_update_candidate",
        "signal_reason": "first confirmed treatment may become initial case after review",
        "source_evidence_refs": ["ev_contract_010"],
        "requires_authority": "case_memory_update_node"
      }
    ]
  }
}
```

### 7.3 Invalid example

```json
{
  "input": {
    "transaction_context": {
      "transaction_id": "txn_01HZXCASE0003",
      "amount": "-95.00",
      "direction": "outflow",
      "bank_account": "operating_chequing",
      "evidence_refs": ["ev_bank_020"]
    },
    "deterministic_path_context": {
      "path_completed": false,
      "trigger_reason": "rule_required_but_missing",
      "blocked_reasons": ["automation_policy_rule_required"],
      "structural_result_status": "not_structural",
      "rule_match_status": "no_match"
    },
    "entity_context": {
      "status": "resolved_entity",
      "entity_id": "ent_sensitive_vendor",
      "confidence": "high",
      "reason": "approved alias matched",
      "alias_status": "approved_alias",
      "automation_policy": "rule_required",
      "evidence_used": ["ev_bank_020"]
    },
    "authority_context": {
      "max_allowed_action": "review_required_only",
      "hard_blocks": ["rule_required_without_rule"],
      "candidate_signal_allowed": true
    }
  },
  "output": {
    "transaction_id": "txn_01HZXCASE0003",
    "judgment_status": "operational_classification",
    "rationale": "历史上通常这样分类，所以直接自动处理。",
    "memory_write_effect": "none"
  }
}
```

Invalid reasons：

- `amount` 使用了负号表达方向，违反 amount-as-absolute-value contract。
- `automation_policy = rule_required` 且无 approved rule，authority 上限是 `review_required_only`。
- 输出 `operational_classification` 绕过 hard block。
- 输出缺少 `accounting_treatment_proposal`、`evidence_refs_used`、`case_refs_used` 和 valid `authority_used`。

## 8. Open Contract Boundaries

- Final router enum / downstream state-machine 名称尚未由 active docs 冻结；本 Stage 3 只冻结 `judgment_status` 的 data contract 类别。
- 共享 `accounting_treatment_proposal` 与未来 JE-ready classification schema 的精确字段尚未冻结；本节点只能输出 proposal / reference，不定义 JE line contract。
- `confidence_label` 是否应成为全局共享枚举，还是仅作为本节点 runtime output，尚未最终决定。
- candidate signals 是否进入独立 durable queue、由哪个后续 node 先归集、以及 queue schema 如何设计，留给后续 Stage / node contract。
- `operational_classification` 在哪些客户或批次设置下可跳过 accountant review 直接进入 JE，未由当前 Stage 冻结；本文件只表达 Case Judgment 的 runtime recommendation authority。
- Timeout、retry、partial-result behavior 仍是 repo active risk，本 Stage 不定义。

## 9. Self-Review

- 已按要求读取 `AGENTS.md`、`TASK_STATE.md`、`PLANS.md`、`CLAUDE.md`、`DECISIONS.md`、`supporting documents/communication_preferences.md`、`supporting documents/development_workflow.md`、`supporting documents/node_design_roadmap.md`、`new system/new_system.md`。
- 已读取 prior approved Stage 1/2 docs：`case_judgment_node__stage_1__functional_intent.md`、`case_judgment_node__stage_2__logic_and_boundaries.md`。
- 已读取可用 Superpowers docs：`using-superpowers/SKILL.md`、`brainstorming/SKILL.md`；project workflow skill `ai-bookkeeper-node-design-facilitation` 在当前环境不存在，因此按 runner instruction 使用 repo `supporting documents/node_design_roadmap.md` 与本节点 Stage 1/2 docs 作为 workflow authority。
- 已确认 optional `supporting documents/node_design_roadmap_zh.md` 在工作树中不存在，未虚构该文件。
- 本文件保持 Stage 3 data contract 范围；未定义 Stage 4 execution algorithm、Stage 5 technical implementation map、Stage 6 test matrix 或 Stage 7 coding-agent task contract。
- 未把 `Transaction Log` 作为 runtime decision / learning source。
- 未赋予 Case Judgment durable memory write、rule promotion、entity approval、alias approval、role confirmation 或 governance approval authority。
- 未使用 legacy specs 作为 active authority。
- 若写入成功，本次只应新增/修改目标文件：`new system/node_stage_designs/case_judgment_node__stage_3__data_contract.md`。
