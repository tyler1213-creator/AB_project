# Knowledge Compilation Node — Stage 3：Data Contract Spec

## 1. Stage 范围

本 Stage 3 只定义 `Knowledge Compilation Node` 的 data contract。

前置依据是：

- `new system/node_stage_designs/knowledge_compilation_node__stage_1__functional_intent.md`
- `new system/node_stage_designs/knowledge_compilation_node__stage_2__logic_and_boundaries.md`

本文件把 Stage 1/2 已确定的 durable-knowledge summarization 行为转换为 implementation-facing 的输入对象类别、输出对象类别、字段语义、字段 authority、runtime-only / durable-memory 边界、validation rules 和 compact examples。

本阶段不定义：

- step-by-step execution algorithm
- exact refresh strategy、trigger scheduler 或 branch sequence
- technical module path、class、API、DB、migration、storage engine 或代码布局
- prompt structure、LLM tool interface 或 wording template
- test matrix、fixture plan 或 coding-agent task contract
- `Knowledge Log / Summary Log` 的全局存储实现
- 新 product authority、accounting decision、governance approval 或 legacy replacement mapping

## 2. Contract Position in Workflow

### 2.1 Upstream handoff consumed

`Knowledge Compilation Node` 消费 `knowledge_compilation_request`。

该 request 只应在客户长期记忆、治理历史、完成交易背景或 post-batch monitoring context 已经形成可追溯变化后传入。典型 upstream source 包括：

- `Onboarding Node`：初始 entity、historical case、rule / governance candidate 或 customer knowledge seed。
- `Case Memory Update Node`：已完成案例写入后，或产生需要刷新摘要的 handoff。
- `Governance Review Node`：已记录 approval、rejection、deferral、restriction 或 auto-applied downgrade 后。
- `Transaction Logging Node` / `Review Node` / `Intervention Log` context：已完成交易、accountant correction、confirmation 或解释性审计背景。
- `Post-Batch Lint Node`：风险、候选、unresolved issue 或 monitoring context 需要未来 humans / agents 看见。

本节点不能接收 current-transaction runtime judgment request 来替代 `Entity Resolution`、`Rule Match`、`Case Judgment`、`Coordinator`、`Review`、`JE Generation` 或 `Transaction Logging`。

### 2.2 Downstream handoff produced

本节点可产生以下 output categories：

- `knowledge_summary_record`：写入 durable `Knowledge Log / Summary Log` 的客户知识摘要。
- `knowledge_summary_write_receipt`：runtime-only 写入结果引用。
- `summary_warning_handoff`：source conflict、stale、supersession 或 review-needed warning。
- `knowledge_update_blocked_handoff`：当前输入不足以可靠编译摘要，或 source authority 不足。
- `knowledge_follow_up_signal`：candidate-only 后续处理信号。

下游可读取摘要作为可读背景，但不能把摘要当作 deterministic rule source、stable entity authority、case authority、governance approval、accounting outcome 或 current transaction decision。

### 2.3 Logs / memory stores read

本节点可以读取或消费：

- `Entity Log`：entity、alias、role、status、authority、risk flags、automation policy、evidence links。
- `Case Log`：completed cases、final classifications、evidence、exceptions、accountant corrections、review context。
- `Rule Log`：approved active rules、historical rule authority、rule lifecycle、governance status。
- `Governance Log`：approvals、rejections、deferrals、restrictions、auto-applied downgrades、authority rationale。
- `Evidence Log` references：仅用于 traceability，不用于覆盖 source memory authority。
- `Transaction Log`：finalized audit history only；它是 audit-facing，不参与 runtime decision，也不是学习层。
- `Intervention Log`：accountant questions、answers、corrections、confirmations、unresolved intervention context。
- `Profile`：客户结构、tax config 或 automation boundary 的稳定背景或待确认限制。
- `Post-Batch Lint Node` / monitoring handoff：需要进入摘要或后续关注的风险语境。
- 既有 `Knowledge Log / Summary Log`：用于 staleness、conflict、supersession 或 refresh context。

### 2.4 Logs / memory stores written or candidate-only

本节点唯一允许的 durable write 是 `Knowledge Log / Summary Log` 语义下的 `knowledge_summary_record`。

该 write 只能保存：

- source-grounded customer knowledge summary
- source references、authority labels、scope、version / supersession metadata
- unresolved boundary、risk、warning、stale / conflict / review-needed status

本节点只能 candidate-only 输出：

- entity / alias / role summary mismatch candidate
- case memory consistency issue
- rule-health / rule-summary mismatch signal
- unresolved governance risk
- automation-policy review candidate
- post-batch lint follow-up candidate
- review-facing clarification candidate

本节点绝不能直接写入或修改：

- `Transaction Log`
- `Case Log`
- `Rule Log`
- stable `Entity Log` authority
- approved `Governance Log`
- `Profile`
- journal entry
- stable entity、approved alias、confirmed role、active rule、automation policy 或 accountant approval

## 3. Input Contracts

### 3.1 `knowledge_compilation_request`

**Purpose**

`knowledge_compilation_request` 是本节点的主 input envelope，表示某个 client 的 durable source context 需要被编译、刷新、标记 stale / conflict，或被安全阻止更新。

**Source authority**

由 workflow orchestrator 或 upstream node handoff 汇总形成。该 envelope 不自行创造 authority；每个 source basis 的 authority 来自对应 durable store、upstream node 或 accountant / governance decision。

**Required fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `compilation_request_id` | 本次 compilation request 引用 | workflow runtime | runtime |
| `client_id` | 当前客户标识 | client context | durable reference |
| `trigger_context` | 为什么需要编译或刷新摘要 | upstream workflow | runtime object with durable refs |
| `source_basis_bundle` | 本次可用于编译的 source-grounded context | source logs / memory stores | runtime object with durable refs |
| `authority_filter_context` | 哪些 source 可写成稳定摘要，哪些只能 candidate / unresolved | upstream authority + source stores | runtime projection |

**Optional fields**

- `existing_summary_context`：既有 summary 的 current / stale / superseded / conflict 状态。
- `requested_summary_scope`：上游建议的摘要范围；不能越过 source authority。
- `lint_or_monitoring_context`：post-batch 风险或 unresolved issue。
- `runtime_notes`：runtime diagnostics；不得作为业务事实或 authority。

**Allowed `trigger_context.trigger_source` values**

- `onboarding`
- `case_memory_update`
- `governance_review`
- `transaction_logging`
- `review_node`
- `intervention_context`
- `post_batch_lint`
- `manual_refresh`
- `workflow_orchestrator`

**Validation / rejection rules**

输入无效或必须 blocked，如果：

- 缺少 `client_id`、`trigger_context`、`source_basis_bundle` 或 `authority_filter_context`。
- `source_basis_bundle` 中没有任何可追溯 source reference。
- 输入要求本节点处理 current transaction classification、rule match、case judgment、JE、review approval 或 governance approval。
- request 试图把 draft、queue item、unapproved candidate、runtime rationale 或 report draft 写成 stable customer knowledge。
- `Transaction Log` 被作为 runtime decision / learning source 传入，而不是 finalized audit-history reference。
- source conflicts 存在但 request 要求本节点静默选择其中一方作为稳定事实。

**Runtime-only vs durable references**

`knowledge_compilation_request` 是 runtime-only envelope。它可以携带 durable references；接收该 request 不授予本节点修改 source memory 的权力。

### 3.2 `trigger_context`

**Purpose**

说明本次 compilation 为什么发生、由哪个 upstream source 触发、是否绑定 batch / governance event / case / entity / rule / intervention。

**Source authority**

来自触发节点或 workflow runtime。

**Required fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `trigger_source` | 触发来源 | upstream workflow | runtime |
| `trigger_reason` | 触发原因 | upstream workflow | runtime |
| `changed_source_refs` | 发生变化或需要重读的 source refs | source logs / memory stores | durable references |

**Optional fields**

- `batch_id`
- `transaction_ids`
- `entity_ids`
- `case_ids`
- `rule_ids`
- `governance_event_ids`
- `intervention_ids`
- `lint_finding_ids`
- `requested_refresh_mode`

**Allowed `trigger_reason` values**

- `initial_knowledge_seed`
- `new_completed_case`
- `governance_decision_recorded`
- `governance_risk_unresolved`
- `finalized_audit_context_available`
- `accountant_correction_or_confirmation`
- `lint_or_monitoring_issue`
- `source_conflict_detected`
- `summary_stale_or_superseded`
- `manual_refresh_requested`

**Validation / rejection rules**

- `changed_source_refs` 不能为空。
- 如果 `trigger_reason = governance_decision_recorded`，必须提供 `governance_event_ids` 或等价 governance refs。
- 如果 `trigger_reason = new_completed_case`，必须提供 completed case refs；未完成交易不能作为 stable case basis。
- `requested_refresh_mode` 只能作为上游意图，不冻结 Stage 4 execution strategy。

**Runtime-only vs durable references**

`trigger_context` 是 runtime handoff；其中的 source ids / refs 指向 durable records。

### 3.3 `source_basis_bundle`

**Purpose**

把本次 compilation 可读取的 source categories 组织在同一个 input object 中，并明确哪些类别存在、缺失、candidate-only、conflicting 或 stale。

**Source authority**

来自各 durable stores、upstream handoff 和 authority filter。

**Required fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `basis_scope` | 本次 source bundle 覆盖的客户 / entity / case / rule / governance 范围 | workflow runtime + source refs | runtime |
| `entity_knowledge_basis` | entity / alias / role / automation policy context | `Entity Log` + `Governance Log` | runtime object with durable refs |
| `case_knowledge_basis` | completed case context | `Case Log` + completed workflow refs | runtime object with durable refs |
| `rule_knowledge_basis` | approved / historical rule context | `Rule Log` + governance refs | runtime object with durable refs |
| `governance_knowledge_basis` | authority change history and unresolved governance context | `Governance Log` | runtime object with durable refs |

**Optional fields**

- `completed_audit_basis`
- `intervention_basis`
- `profile_basis`
- `lint_monitoring_basis`
- `evidence_trace_basis`
- `existing_summary_refs`

**Validation / rejection rules**

- 每个非空 basis 必须携带 source refs 和 authority status。
- 如果某个 basis 只包含 candidate / pending / deferred 内容，必须由 `authority_filter_context` 标为 candidate-only 或 unresolved，不能进入 stable summary facts。
- source records 之间冲突时，必须保留 conflict metadata；不能只提供已“调和”的自然语言。
- `basis_scope` 不能暗示摘要粒度已冻结；它只说明本次输入覆盖范围。

**Runtime-only vs durable references**

该 bundle 是 runtime-only 汇总对象。内部 refs 指向 durable stores；本节点只能把其 source-grounded projection 编译成 `Knowledge Log / Summary Log`。

### 3.4 `entity_knowledge_basis`

**Purpose**

说明客户有哪些稳定或受限 entity、alias、role、status、authority、risk flags 和 automation-policy context。

**Source authority**

来自 `Entity Log`、已生效 `Governance Log`、approved alias / confirmed role history、merge / split / archived context 和 evidence references。

**Required fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `entity_refs` | 本次摘要相关 entity references | `Entity Log` | durable references |
| `entity_authority_status` | entity context 的 authority 状态 | `Entity Log` / governance | runtime projection |
| `source_refs` | 支撑 entity summary 的 source refs | source logs | durable references |

**Optional fields**

- `display_names`
- `approved_aliases`
- `candidate_aliases`
- `rejected_aliases`
- `confirmed_roles`
- `candidate_roles`
- `entity_lifecycle_statuses`
- `automation_policies`
- `risk_flags`
- `merge_split_context`
- `governance_notes_refs`
- `new_entity_candidate_refs`

**Allowed authority / status values**

`entity_authority_status` 允许：

- `stable_authority`
- `candidate_only`
- `mixed_authority`
- `conflicting`
- `stale`
- `unresolved`

`entity_lifecycle_statuses` 如提供，必须沿用 active baseline：`candidate`、`active`、`merged`、`archived`。

`automation_policies` 如提供，必须沿用 active baseline：`eligible`、`case_allowed_but_no_promotion`、`rule_required`、`review_required`、`disabled`。

**Validation / rejection rules**

- `candidate_aliases`、`candidate_roles`、`new_entity_candidate_refs` 只能写成 candidate / unresolved boundary，不能写成 approved alias、confirmed role 或 stable entity fact。
- merge / split 只能按已记录 governance history 解释；本节点不能生成 merge / split decision。
- `automation_policy` 升级或放宽必须 accountant approval；摘要不能把未批准建议写成已生效 policy。

**Runtime-only vs durable references**

该对象是 runtime projection。`Entity Log` 是 source of truth；summary 只能引用和解释，不能替代 entity authority。

### 3.5 `case_knowledge_basis`

**Purpose**

说明过去真实完成案例如何处理、有哪些条件、例外、correction、review context 或风险模式。

**Source authority**

来自 `Case Log`、completed transaction context、Review correction / approval、case judgment rationale 和必要 evidence references。

**Required fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `case_refs` | 本次摘要相关 completed case refs | `Case Log` | durable references |
| `case_authority_status` | case context 是否可作为已完成历史先例 | `Case Log` / Review | runtime projection |
| `source_refs` | supporting evidence / review / case refs | source logs | durable references |

**Optional fields**

- `entity_refs`
- `final_classification_refs`
- `evidence_condition_refs`
- `exception_markers`
- `accountant_correction_refs`
- `review_context_refs`
- `case_pattern_candidates`
- `case_conflict_notes`

**Allowed `case_authority_status` values**

- `completed_authority`
- `candidate_only`
- `mixed_authority`
- `conflicting`
- `stale`
- `unresolved`

**Validation / rejection rules**

- 只有 completed / approved / finalized case context 可写成稳定 historical case summary。
- 当前交易 pending、not approved、review-required、JE-blocked、conflicting 或未完成时，不能作为 stable case knowledge。
- 多个相似 completed cases 不能被本节点升级为 deterministic rule。
- case summary 必须保留例外和条件；不能把“通常如此”写成“必须如此”。

**Runtime-only vs durable references**

该对象是 runtime projection。`Case Log` 是 case authority；summary 不是 case memory write。

### 3.6 `rule_knowledge_basis`

**Purpose**

说明哪些 deterministic rules 已被批准、处于 active / historical / restricted / rejected / deferred / review-needed 状态，以及 rule authority 如何影响客户知识摘要。

**Source authority**

来自 `Rule Log`、rule lifecycle context、governance decisions、rule-health context 和 approved rule authority。

**Required fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `rule_refs` | 本次摘要相关 rule refs | `Rule Log` | durable references |
| `rule_authority_status` | rule context 的 authority 状态 | `Rule Log` / governance | runtime projection |
| `source_refs` | rule / governance supporting refs | source logs | durable references |

**Optional fields**

- `active_rule_refs`
- `historical_rule_refs`
- `restricted_rule_refs`
- `rejected_rule_candidate_refs`
- `deferred_rule_candidate_refs`
- `rule_health_notes`
- `rule_conflict_refs`
- `related_entity_refs`

**Allowed `rule_authority_status` values**

- `approved_active`
- `historical_or_superseded`
- `restricted`
- `candidate_only`
- `rejected`
- `deferred`
- `conflicting`
- `stale`

**Validation / rejection rules**

- Summary wording 不能变成 rule condition。
- candidate、lint suggestion、repeated completed outcome 或 review draft 不能写成 approved active rule。
- 本节点不能 create、promote、modify、delete、downgrade active rule。
- `Rule Match Node` 未来必须读取 `Rule Log`，不能读取 summary 来执行 rule。

**Runtime-only vs durable references**

该对象是 runtime projection。`Rule Log` 是 deterministic rule source；summary 只是可读解释。

### 3.7 `governance_knowledge_basis`

**Purpose**

说明长期记忆和自动化权威为什么变化，哪些事项被 approved、rejected、deferred、restricted、auto-applied downgrade 或仍 unresolved。

**Source authority**

来自 `Governance Log`、Governance Review decisions、accountant / governance rationale、auto-applied downgrade visibility 和 prior governance history。

**Required fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `governance_event_refs` | 本次摘要相关 governance events | `Governance Log` | durable references |
| `governance_authority_status` | governance context 的 authority 状态 | `Governance Log` | runtime projection |
| `source_refs` | supporting governance / evidence refs | source logs | durable references |

**Optional fields**

- `approved_event_refs`
- `rejected_event_refs`
- `deferred_event_refs`
- `auto_applied_downgrade_refs`
- `pending_event_refs`
- `restriction_refs`
- `affected_entity_refs`
- `affected_rule_refs`
- `authority_rationale_refs`

**Allowed `governance_authority_status` values**

- `approved_or_applied`
- `rejected`
- `deferred`
- `pending`
- `auto_applied_downgrade`
- `mixed_authority`
- `conflicting`
- `unresolved`

**Validation / rejection rules**

- approved / applied governance events 可以进入摘要作为已生效语境。
- rejected / deferred / pending events 只能作为限制、风险或开放边界，不能写成已生效 authority。
- `auto_applied_downgrade` 可被摘要为已生效限制，但不能被本节点扩展成升级或放宽。
- 本节点不能 approve governance event，也不能修改 source memory 来匹配摘要写法。

**Runtime-only vs durable references**

该对象是 runtime projection。`Governance Log` 是 governance authority；summary 只是解释层。

### 3.8 `completed_audit_basis`

**Purpose**

提供 finalized transaction audit history、review correction、accountant confirmation 或 intervention context 中对客户知识有解释价值的背景。

**Source authority**

来自 audit-facing `Transaction Log`、`Intervention Log`、Review Node context 和 finalization history。

**Required fields when present**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `completed_transaction_refs` | 已完成交易引用 | `Transaction Log` / final workflow | durable references |
| `audit_context_status` | audit context 是否 finalized / usable as background | Transaction Logging / Review | runtime projection |
| `source_refs` | supporting audit / intervention refs | source logs | durable references |

**Optional fields**

- `review_decision_refs`
- `intervention_refs`
- `accountant_confirmation_refs`
- `accountant_correction_refs`
- `final_outcome_refs`
- `audit_trace_notes`

**Allowed `audit_context_status` values**

- `finalized_background`
- `intervention_confirmed`
- `correction_recorded`
- `candidate_only`
- `conflicting`
- `unresolved`

**Validation / rejection rules**

- `Transaction Log` 只能作为 finalized audit background，不参与 runtime decision，也不是 learning layer。
- 本节点不能从 Transaction Log 直接推导 active rule、stable entity、case authority 或 accounting authority。
- 未完成、未批准或冲突交易不能作为 stable summary fact。

**Runtime-only vs durable references**

该对象是 runtime projection。摘要可以引用 finalized audit context，但不能重写审计历史。

### 3.9 `lint_monitoring_basis`

**Purpose**

提供 post-batch lint / monitoring 中值得 humans 或 agents 看见的风险、候选、unresolved issue 或 follow-up context。

**Source authority**

来自 `Post-Batch Lint Node` finding、monitoring handoff、governance unresolved risk 和 review / memory consistency issue。

**Required fields when present**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `finding_refs` | lint / monitoring finding refs | Post-Batch Lint / monitoring workflow | durable or runtime refs |
| `finding_authority_status` | finding 是否已治理、candidate-only 或 unresolved | lint / governance context | runtime projection |
| `source_refs` | supporting source refs | source logs / lint context | durable references |

**Optional fields**

- `entity_merge_candidate_refs`
- `entity_split_candidate_refs`
- `rule_instability_refs`
- `case_to_rule_candidate_refs`
- `automation_risk_refs`
- `memory_consistency_issue_refs`
- `review_follow_up_refs`

**Allowed `finding_authority_status` values**

- `candidate_only`
- `governance_needed`
- `review_needed`
- `approved_or_applied`
- `auto_applied_downgrade`
- `rejected`
- `deferred`
- `unresolved`

**Validation / rejection rules**

- lint finding 可以进入 summary as warning / unresolved boundary / follow-up context。
- lint finding 本身不是 governance approval，不能改变 entity authority、rule authority 或 automation policy，除 active baseline 允许的 auto-applied downgrade 已经由 source context 明确记录。
- 本节点不能把 repeated lint wording 变成 rule 或 stable policy。

**Runtime-only vs durable references**

该对象是 runtime projection。candidate finding 只能作为 candidate-only context。

### 3.10 `authority_filter_context`

**Purpose**

明确每类 source 在本次 compilation 中的可用边界，防止 candidate、draft、pending、conflicting 或 stale context 被写成稳定客户知识。

**Source authority**

来自 source logs、upstream handoff、accountant / governance authority 和 deterministic validation。

**Required fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `stable_summary_allowed_refs` | 可写成稳定摘要事实的 source refs | source authority | runtime projection |
| `candidate_only_refs` | 只能作为 candidate / follow-up 的 refs | source authority | runtime projection |
| `unresolved_boundary_refs` | 必须保留 unresolved / review-needed / governance-needed 的 refs | source authority | runtime projection |
| `excluded_refs` | 不可进入摘要的 refs 及原因 | source authority / validation | runtime projection |

**Optional fields**

- `conflict_refs`
- `stale_refs`
- `superseded_refs`
- `source_precedence_notes`
- `authority_warnings`

**Validation / rejection rules**

- 所有 `source_basis_bundle` 中的 source refs 必须至少落入 stable、candidate-only、unresolved、excluded、conflict、stale 或 superseded 之一。
- 同一 ref 不能同时被标为 stable fact 和 unresolved / excluded，除非对象中明确说明不同字段的 authority split。
- `source_precedence_notes` 不能改写 active authority order；source logs / memory stores 仍是 summary 的上游 authority。

**Runtime-only vs durable references**

该对象是 runtime-only authority projection。它可以被摘要记录为 authority metadata，但不成为 source memory。

### 3.11 `existing_summary_context`

**Purpose**

说明既有 `Knowledge Log / Summary Log` 记录是否 current、stale、superseded、conflicting 或需要 refresh。

**Source authority**

来自既有 `Knowledge Log / Summary Log` 和 source-change comparison context。

**Required fields when present**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `summary_refs` | 既有摘要引用 | `Knowledge Log / Summary Log` | durable references |
| `existing_summary_status` | 既有摘要状态 | Knowledge Log + source comparison | runtime projection |

**Optional fields**

- `superseded_by_refs`
- `stale_reason`
- `conflict_reason`
- `source_snapshot_refs`
- `last_compiled_at`

**Allowed `existing_summary_status` values**

- `current`
- `stale`
- `superseded`
- `conflicting`
- `review_needed`
- `unknown`

**Validation / rejection rules**

- 如果 source context 已显示 stale 或 conflict，本节点不能继续输出看似 current 的无 warning 摘要。
- 本阶段不冻结 exact lifecycle；status 只定义 contract-level state semantics。

**Runtime-only vs durable references**

该对象是 runtime projection over durable summary records。

## 4. Output Contracts

### 4.1 `knowledge_summary_record`

**Purpose**

写入 durable `Knowledge Log / Summary Log` 的客户知识摘要。它是 source-grounded 编译视图，用于 humans 和 agents 快速理解客户常见模式、例外、风险、治理历史和开放边界。

**Consumer / downstream authority**

下游 `Entity Resolution`、`Case Judgment`、`Review`、`Governance Review`、`Post-Batch Lint`、humans 和 future agents 可读取它作为辅助语境。任何 deterministic 或 authority-bearing decision 必须回查 source logs / memory stores。

**Required fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `summary_id` | 摘要记录唯一引用 | Knowledge Log write | durable |
| `client_id` | 当前客户标识 | client context | durable reference |
| `summary_scope` | 摘要覆盖范围 | compilation request + source refs | durable metadata |
| `summary_status` | 摘要当前可用状态 | compilation validation | durable metadata |
| `summary_sections` | 结构化可读摘要内容 | source-grounded compilation | durable compiled view |
| `source_refs` | 支撑摘要的 source refs | source logs / memory stores | durable references |
| `authority_labels` | 每段摘要的 authority / candidate / unresolved 标记 | authority filter | durable metadata |
| `compiled_from_request_id` | 来源 request 引用 | workflow runtime | durable metadata |
| `compiled_at` | 编译时间 | workflow runtime | durable metadata |

**Optional fields**

- `supersedes_summary_refs`
- `superseded_by_summary_ref`
- `stale_reason`
- `conflict_notes`
- `open_boundaries`
- `risk_warnings`
- `downstream_usage_limits`
- `follow_up_signal_refs`
- `review_needed_reason`

**Allowed `summary_scope.scope_type` values**

- `client_level`
- `entity_level`
- `case_pattern_level`
- `rule_level`
- `governance_level`
- `mixed_scope`

这些 scope values 只定义 contract semantics，不冻结 exact storage granularity 或 refresh strategy。

**Allowed `summary_status` values**

- `current`
- `current_with_open_boundaries`
- `stale`
- `superseded`
- `conflicting`
- `review_needed`
- `blocked_not_written`

`blocked_not_written` 不能用于已成功 durable write 的 normal record；它只可出现在 blocked handoff 或 attempted-output context 中。

**Required `summary_sections` categories**

至少一类 section 必须存在：

- `entity_context`
- `case_patterns`
- `approved_rule_context`
- `governance_history`
- `automation_boundaries`
- `risk_and_exception_notes`
- `open_boundaries`
- `source_conflict_notes`

**Validation rules**

- 每个 `summary_sections` item 必须有对应 `source_refs` 和 `authority_labels`。
- `authority_labels = stable_fact` 的内容必须来自 durable approved / completed / applied source authority。
- candidate、pending、deferred、rejected、unresolved 或 lint-only 内容必须明确标成 `candidate_only`、`unresolved`、`review_needed`、`governance_needed`、`rejected_context` 或 `deferred_context`。
- 摘要不能包含 source logs 中不存在的客户事实。
- 摘要不能输出 COA / HST / JE decision 作为本节点新判断；只能引用 source-approved historical outcome 或 approved rule context。
- 摘要不能把 `new_entity_candidate` 写成 stable entity、approved alias、confirmed role 或 rule authority。

**Durable memory boundary**

`knowledge_summary_record` 是 durable summary memory，但不是 source authority。它不会改变 `Entity Log`、`Case Log`、`Rule Log`、`Governance Log`、`Transaction Log`、`Profile` 或 JE。

### 4.2 `knowledge_summary_write_receipt`

**Purpose**

runtime-only 写入结果引用，说明本节点是否成功写入或刷新 `Knowledge Log / Summary Log`。

**Consumer / downstream authority**

由 workflow orchestrator 或 downstream handoff 使用；它不提供 product authority。

**Required fields**

- `compilation_request_id`
- `write_status`
- `summary_refs`
- `written_at`

**Optional fields**

- `warning_refs`
- `blocked_handoff_ref`
- `follow_up_signal_refs`
- `runtime_notes`

**Allowed `write_status` values**

- `written`
- `refreshed`
- `superseded_previous`
- `warning_only`
- `blocked`
- `no_write_needed`

**Validation rules**

- `write_status = written / refreshed / superseded_previous` 时，必须提供至少一个 `summary_refs`。
- `write_status = blocked` 时，必须提供 `blocked_handoff_ref` 或 equivalent blocked reason。
- receipt 本身是 runtime-only，不是 durable authority。

### 4.3 `summary_warning_handoff`

**Purpose**

表达 source conflict、stale summary、supersession、review-needed 或 memory consistency warning。

**Consumer / downstream authority**

可供 Review、Governance Review、Post-Batch Lint、workflow orchestrator 或 future compilation 读取。它是 warning，不是 source correction。

**Required fields**

- `warning_id`
- `client_id`
- `warning_type`
- `affected_summary_refs`
- `affected_source_refs`
- `warning_reason`

**Optional fields**

- `suggested_follow_up_target`
- `severity`
- `related_entity_refs`
- `related_case_refs`
- `related_rule_refs`
- `related_governance_event_refs`

**Allowed `warning_type` values**

- `source_conflict`
- `summary_stale`
- `summary_superseded`
- `authority_gap`
- `traceability_gap`
- `memory_consistency_issue`
- `review_needed`
- `governance_needed`

**Allowed `severity` values**

- `info`
- `caution`
- `blocks_summary_write`
- `blocks_downstream_use`

**Validation rules**

- warning 必须指向 affected source or summary refs。
- warning 不能修正 source logs，也不能自行选择冲突版本。
- `blocks_summary_write` 时，本节点不得同时输出无 warning 的 `current` summary。

**Durable / candidate boundary**

warning 可随 summary 保存为 Knowledge Log metadata 或 runtime handoff；它不改变 source memory。

### 4.4 `knowledge_update_blocked_handoff`

**Purpose**

说明本次 input 不能被安全编译为可靠摘要，或只能等待 source memory / review / governance / lint workflow 处理后再刷新。

**Consumer / downstream authority**

workflow orchestrator、Review、Governance Review、Post-Batch Lint 或相关 source-memory workflow。

**Required fields**

- `blocked_handoff_id`
- `compilation_request_id`
- `client_id`
- `blocked_reason`
- `blocking_refs`
- `required_resolution_owner`

**Optional fields**

- `safe_partial_summary_allowed`
- `warning_refs`
- `follow_up_signal_refs`
- `runtime_notes`

**Allowed `blocked_reason` values**

- `no_traceable_source_refs`
- `source_authority_insufficient`
- `source_conflict_unresolved`
- `candidate_only_input`
- `current_transaction_not_final`
- `governance_approval_missing`
- `review_approval_missing`
- `transaction_log_misused_as_learning_source`
- `requested_authority_out_of_scope`

**Allowed `required_resolution_owner` values**

- `source_memory_workflow`
- `review_node`
- `governance_review_node`
- `post_batch_lint_node`
- `case_memory_update_node`
- `workflow_orchestrator`
- `human_product_decision`

**Validation rules**

- blocked handoff 必须说明具体 blocking refs 或说明为何 refs 缺失。
- 如果 `safe_partial_summary_allowed = true`，partial summary 必须排除 blocked facts，并保留 open boundary / warning。
- blocked handoff 不能伪装成 successful summary write。

**Runtime / durable boundary**

blocked handoff 是 runtime-only 或 workflow handoff；它不是 source memory mutation。

### 4.5 `knowledge_follow_up_signal`

**Purpose**

表达编译过程中发现的后续处理候选或问题，供其他 workflow 评估。

**Consumer / downstream authority**

Review、Governance Review、Post-Batch Lint、Case Memory Update 或 source memory workflow。该 signal 不是 approval。

**Required fields**

- `signal_id`
- `client_id`
- `signal_type`
- `signal_summary`
- `supporting_refs`
- `target_workflow`
- `authority_status`

**Optional fields**

- `related_summary_refs`
- `related_entity_refs`
- `related_case_refs`
- `related_rule_refs`
- `related_governance_event_refs`
- `priority_hint`

**Allowed `signal_type` values**

- `entity_summary_mismatch`
- `alias_or_role_review_candidate`
- `case_memory_consistency_issue`
- `rule_health_or_summary_mismatch`
- `unresolved_governance_risk`
- `automation_policy_review_candidate`
- `post_batch_lint_follow_up`
- `review_clarification_candidate`

**Allowed `target_workflow` values**

- `review_node`
- `governance_review_node`
- `post_batch_lint_node`
- `case_memory_update_node`
- `entity_memory_workflow`
- `rule_memory_workflow`
- `workflow_orchestrator`

**Allowed `authority_status` values**

- `candidate_only`
- `review_needed`
- `governance_needed`
- `unresolved`

**Validation rules**

- follow-up signal 必须有 supporting refs；没有 refs 时只能成为 blocked / traceability warning。
- signal 不能修改 entity、case、rule、governance、Profile、Transaction Log 或 JE。
- signal 不能扩大 automation permission 或 approve rule / alias / role。

**Runtime / durable boundary**

signal 是 candidate-only。它可以作为 summary metadata 或 handoff 保存，但只有后续 accountant / governance authority path 才能让相关内容变成 source memory。

## 5. Field Authority and Memory Boundary

### 5.1 Source of truth

- `client_id`：client / batch context 是引用 authority；本节点不创建客户身份。
- `entity_id`、alias、role、entity status、automation policy：`Entity Log` + approved / applied `Governance Log` 是 source of truth。
- completed cases、final classification history、case exceptions、accountant correction context：`Case Log`、Review context 和 completed workflow refs 是 source of truth。
- active / historical / restricted rules：`Rule Log` + governance decisions 是 source of truth。
- approval、rejection、deferral、restriction、auto-applied downgrade：`Governance Log` 是 source of truth。
- finalized audit history：`Transaction Log` 是 audit-facing source of truth，但不参与 runtime decision，也不是 learning layer。
- accountant questions / answers / confirmations / corrections：`Intervention Log` / Review context 是 intervention source。
- raw evidence and evidence references：`Evidence Log` 是 source of truth。
- compiled customer knowledge wording：`Knowledge Log / Summary Log` 是 compiled-view source for the summary text only，不是 upstream facts 的 authority。

### 5.2 Fields that can never become durable memory by this node

本节点绝不能把以下内容写成 source memory 或 authority mutation：

- stable entity creation
- approved alias
- confirmed role
- entity merge / split / archive / reactivate
- automation policy upgrade or relaxation
- active rule create / promote / modify / delete / downgrade
- stable case memory write
- Transaction Log final record
- Profile update
- COA / HST / JE decision
- accountant approval or governance approval
- current transaction final classification

### 5.3 Fields that can become durable only through accountant / governance approval

以下字段或信号如果需要成为长期 authority，必须经对应 accountant / governance path，而不是本节点：

- `candidate_aliases` → 只能经 alias approval path 变成 approved alias。
- `candidate_roles` → 只能经 role confirmation path 变成 confirmed role。
- `new_entity_candidate_refs` → 只能经 entity governance / approved memory path 变成 stable entity。
- `case_pattern_candidates` → 只能经 completed case write 或 rule governance path 影响 source memory。
- `rule_health_or_summary_mismatch` / `case_to_rule_candidate_refs` → 只能经 rule governance path 影响 Rule Log。
- `automation_policy_review_candidate` → 降级必须符合 active baseline；升级或放宽必须 accountant approval。
- `governance_needed` signals → 只能经 Governance Review 形成 approved / rejected / deferred governance events。

### 5.4 Audit vs learning / summary boundary

- `Transaction Log` 保存最终处理结果和审计轨迹；本节点只能把 finalized audit context 当作解释背景引用。
- `Knowledge Log / Summary Log` 保存 compiled view；它帮助 humans / agents 理解客户语境，但不直接学习、执行 rule、批准 governance 或处理当前交易。
- `Log` 在本节点语境中仍表示 durable long-term meaningful information storage；candidate queues、transient handoffs、review draft、report draft 或 runtime notes 不能被称为 Log。

## 6. Validation Rules

### 6.1 Contract-level validation rules

- Every stable summary fact must have traceable `source_refs`.
- Every source ref must have an authority label: stable, candidate-only, unresolved, rejected, deferred, stale, superseded, conflicting, or excluded.
- Summary text must preserve source authority distinctions; candidate / unresolved content must not be phrased as settled fact.
- Conflicts must be explicit. The node cannot use LLM judgment to silently choose a source version.
- If existing summary is stale or conflicting, new output must mark staleness / conflict / supersession.
- Summary output must include downstream usage limits when there is any risk it may be mistaken for rule or authority.
- The node may write only `Knowledge Log / Summary Log` semantics.

### 6.2 Conditions that make the input invalid

Input is invalid or blocked when:

- required envelope fields are missing;
- no traceable source refs exist;
- current transaction is not completed but is presented as stable case / audit basis;
- governance-required change lacks approval but is presented as authority;
- candidate alias / role / entity / rule is presented as approved;
- source conflicts are present but conflict metadata is omitted;
- `Transaction Log` is presented as runtime decision or learning source;
- request asks this node to classify a transaction, generate JE, approve governance, mutate Profile, or modify source logs.

### 6.3 Conditions that make the output invalid

Output is invalid when:

- `knowledge_summary_record.summary_sections` contains facts without source refs;
- `summary_status = current` while known conflicts or stale source refs are unresolved;
- candidate-only content is written under `authority_labels = stable_fact`;
- summary text creates new accounting treatment, COA, HST, JE, rule condition, entity authority, alias approval, role confirmation, or automation permission;
- `knowledge_follow_up_signal.authority_status` is anything stronger than candidate / review-needed / governance-needed / unresolved;
- `knowledge_summary_write_receipt.write_status = written` without summary refs;
- warning or blocked handoff lacks affected / blocking refs and reason.

### 6.4 Stop / ask conditions for unresolved contract authority

Stop and ask for product decision before freezing a narrower contract if:

- downstream design requires summary to become a runtime decision source;
- exact `Knowledge Log / Summary Log` granularity must be frozen as one canonical storage shape;
- source precedence between source logs and summaries is proposed to change;
- unresolved governance or lint findings are proposed to become stable policy by summary wording;
- Transaction Log is proposed as direct learning input for runtime nodes;
- summary lifecycle rules would mutate source memory or authority automatically.

## 7. Examples

### 7.1 Valid minimal example

```yaml
knowledge_compilation_request:
  compilation_request_id: kcr_001
  client_id: client_abc
  trigger_context:
    trigger_source: case_memory_update
    trigger_reason: new_completed_case
    changed_source_refs: [case_101]
    case_ids: [case_101]
  source_basis_bundle:
    basis_scope:
      scope_type: entity_level
      entity_ids: [ent_tim_hortons]
    entity_knowledge_basis:
      entity_refs: [ent_tim_hortons]
      entity_authority_status: stable_authority
      source_refs: [ent_tim_hortons, gov_alias_12]
      approved_aliases: ["TIM HORTONS #1234"]
      automation_policies:
        ent_tim_hortons: eligible
    case_knowledge_basis:
      case_refs: [case_101]
      case_authority_status: completed_authority
      source_refs: [case_101, evidence_receipt_88]
    rule_knowledge_basis:
      rule_refs: []
      rule_authority_status: historical_or_superseded
      source_refs: []
    governance_knowledge_basis:
      governance_event_refs: [gov_alias_12]
      governance_authority_status: approved_or_applied
      source_refs: [gov_alias_12]
  authority_filter_context:
    stable_summary_allowed_refs: [ent_tim_hortons, gov_alias_12, case_101]
    candidate_only_refs: []
    unresolved_boundary_refs: []
    excluded_refs: []

knowledge_summary_record:
  summary_id: ks_001
  client_id: client_abc
  summary_scope:
    scope_type: entity_level
    entity_ids: [ent_tim_hortons]
  summary_status: current
  summary_sections:
    entity_context:
      text: "Tim Hortons 是已识别实体，已批准 alias 包括 TIM HORTONS #1234。"
      source_refs: [ent_tim_hortons, gov_alias_12]
      authority_label: stable_fact
    case_patterns:
      text: "已完成案例 case_101 可作为历史先例背景；未来自动化仍需读取 source case / rule authority。"
      source_refs: [case_101]
      authority_label: stable_fact
  source_refs: [ent_tim_hortons, gov_alias_12, case_101]
  authority_labels:
    ent_tim_hortons: stable_fact
    gov_alias_12: stable_fact
    case_101: stable_fact
  compiled_from_request_id: kcr_001
  compiled_at: "2026-05-06T10:00:00Z"
```

### 7.2 Valid richer example

```yaml
knowledge_summary_record:
  summary_id: ks_020
  client_id: client_abc
  summary_scope:
    scope_type: mixed_scope
    entity_ids: [ent_home_depot]
  summary_status: current_with_open_boundaries
  summary_sections:
    entity_context:
      text: "Home Depot 是 active entity；automation_policy 为 case_allowed_but_no_promotion。"
      source_refs: [ent_home_depot, gov_auto_44]
      authority_label: stable_fact
    case_patterns:
      text: "历史 completed cases 多数支持材料费语境，但存在 owner personal-use exception。"
      source_refs: [case_210, case_217, case_231]
      authority_label: stable_fact
    approved_rule_context:
      text: "当前没有可直接执行的 active rule；任何 rule promotion 都需要 governance approval。"
      source_refs: [rule_health_09]
      authority_label: unresolved
    risk_and_exception_notes:
      text: "mixed-use risk 未消失；runtime Case Judgment 必须回查 current evidence 和 Case Log。"
      source_refs: [case_217, lint_332]
      authority_label: review_needed
  open_boundaries:
    - "是否应为 Home Depot 设立更窄规则仍是 governance-needed candidate。"
  risk_warnings:
    - "摘要不可作为 Rule Match 条件。"
  source_refs: [ent_home_depot, gov_auto_44, case_210, case_217, case_231, lint_332]
  authority_labels:
    ent_home_depot: stable_fact
    gov_auto_44: stable_fact
    lint_332: review_needed
  follow_up_signal_refs: [kfus_007]
  compiled_from_request_id: kcr_020
  compiled_at: "2026-05-06T10:15:00Z"

knowledge_follow_up_signal:
  signal_id: kfus_007
  client_id: client_abc
  signal_type: automation_policy_review_candidate
  signal_summary: "Home Depot mixed-use pattern may need governance review before rule promotion."
  supporting_refs: [case_217, lint_332]
  target_workflow: governance_review_node
  authority_status: governance_needed
```

### 7.3 Invalid example with reason

```yaml
knowledge_summary_record:
  summary_id: ks_bad_001
  client_id: client_abc
  summary_scope:
    scope_type: entity_level
    entity_ids: [new_entity_candidate_55]
  summary_status: current
  summary_sections:
    entity_context:
      text: "Tims Button is an approved vendor and should be categorized as software subscriptions."
      source_refs: [runtime_entity_guess_55]
      authority_label: stable_fact
```

Invalid reasons：

- `new_entity_candidate` / runtime guess 被写成 approved vendor，越过 entity governance。
- `software subscriptions` 是 accounting classification / COA-style conclusion，本节点不能创造。
- `source_refs` 不是 durable approved / completed source authority。
- `summary_status = current` 和 `authority_label = stable_fact` 掩盖了 candidate-only 状态。

## 8. Open Contract Boundaries

- Exact `Knowledge Log / Summary Log` granularity 仍未冻结：client-level、entity-level、case-pattern-level、rule-level、governance-level 是否作为独立 durable record，还是以 `summary_scope` 区分，留到后续阶段。
- Exact lifecycle 仍未冻结：full-refresh、incremental-refresh、batch-refresh、governance-triggered refresh、supersession behavior 和 retention policy 留到后续阶段。
- `summary_status` 与 source log conflict 的 repair workflow 未冻结；本 Stage 3 只要求显式 warning / blocked / stale / conflict。
- Downstream runtime nodes 读取 summary 时必须同步读取哪些 source memory 的 exact contract 未冻结；当前只冻结“summary 不可替代 source authority”。
- Knowledge Compilation 与 `Post-Batch Lint Node` 对 risk summary、monitoring finding、candidate follow-up 的 exact split 仍未完全冻结。
- rejected / deferred governance decision、unresolved lint finding 和 monitoring issue 的 exact human-readable wording style 未冻结；当前只冻结 authority label 和 boundary。
- Onboarding seed summary 与后续 runtime / batch summary 的 merge or replacement behavior 未冻结。

## 9. Self-Review

- 已按要求读取 live repo docs：`AGENTS.md`、`TASK_STATE.md`、`PLANS.md`、`CLAUDE.md`、`DECISIONS.md`、`supporting documents/communication_preferences.md`、`supporting documents/development_workflow.md`、`supporting documents/node_design_roadmap.md`、`new system/new_system.md`。
- 已读取 prior approved stage docs：`knowledge_compilation_node__stage_1__functional_intent.md`、`knowledge_compilation_node__stage_2__logic_and_boundaries.md`。
- 已读取可用 Superpowers docs：`using-superpowers/SKILL.md`、`brainstorming/SKILL.md`；project workflow skill `ai-bookkeeper-node-design-facilitation` 在当前环境不存在，因此按 runner instruction 使用 repo `supporting documents/node_design_roadmap.md` 与本节点 Stage 1/2 docs 作为 workflow authority。
- 已确认 optional `supporting documents/node_design_roadmap_zh.md` 在 working tree 中缺失；未 invent 该文件内容。
- 本文件只定义 Stage 3 data contracts，没有进入 Stage 4 execution algorithm、Stage 5 technical map、Stage 6 test matrix 或 Stage 7 coding-agent task contract。
- 未把 summary 写成 deterministic rule source、runtime decision source、accounting authority、case memory write、entity authority 或 governance approval。
- 未从 historical drafts 或 legacy specs 引入 active product authority。
- 本次不修改 `new_system.md`、Stage 1/2 docs、governance docs 或其他 repo 文件；若未 blocked，只写目标 Stage 3 文件。
