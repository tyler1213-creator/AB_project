# Transaction Logging Node — Stage 3：Data Contract Spec

## 1. Stage 范围

本 Stage 3 只定义 `Transaction Logging Node` 的 data contract。

前置依据是：

- `new system/node_stage_designs/transaction_logging_node__stage_1__functional_intent.md`
- `new system/node_stage_designs/transaction_logging_node__stage_2__logic_and_boundaries.md`

本文件把 Stage 1/2 已批准的 final audit-trail persistence 行为转换成 implementation-facing 的输入对象类别、输出对象类别、字段含义、字段 authority、runtime-only 与 durable-memory 边界、validation rules 和紧凑示例。

本阶段不定义：

- step-by-step execution algorithm
- technical implementation map、repo module path、class、API、DB、migration、storage engine 或代码布局
- test matrix、fixture plan 或 coding-agent task contract
- `Transaction Log` 的全局存储实现
- `JE Generation Node`、`Review Node`、`Case Memory Update Node` 或 `Governance Review Node` 的完整下游 schema
- 未由 active docs 支持的新 product authority
- legacy replacement mapping

## 2. Contract Position in Workflow

### 2.1 Upstream handoff consumed

`Transaction Logging Node` 消费 `transaction_logging_request`。

该 request 只应在当前交易具备 final logging authority 时由 workflow 传入。上游必须已经完成或明确阻断：

- `Evidence Intake / Preprocessing Node`
- `Transaction Identity Node`
- `Profile / Structural Match Node`
- `Entity Resolution Node`、`Rule Match Node`、`Case Judgment Node` 中适用的 classification path
- `Coordinator / Pending Node` 或 `Review Node` 中必要的 clarification / approval / correction
- `JE Generation Node` 的 journal entry result，除非后续阶段明确允许某类 terminal non-JE outcome 进入单独 audit record

本节点不能接收尚未绑定稳定 `transaction_id` 的普通 final logging request，也不能替上游重新做 entity resolution、classification、review decision 或 JE generation。

### 2.2 Downstream handoff produced

本节点可产生以下 output categories：

- `transaction_log_entry`：写入 audit-facing `Transaction Log` 的 durable final record。
- `transaction_log_write_receipt`：runtime-only 写入结果引用，供 workflow 继续交接。
- `final_logging_blocked_handoff`：runtime-only 安全停止 handoff，说明不能形成正常 final audit record。
- `logging_consistency_issue_signal`：runtime-only 一致性问题信号。
- `post_logging_handoff`：runtime-only 下游交接，引用已写入的 `transaction_log_entry` 和 candidate relationships。

### 2.3 Logs / memory stores read

本节点可以读取或消费：

- 当前交易的 objective transaction basis 和 `Evidence Log` references
- `Transaction Identity Node` 产生的稳定 `transaction_id`
- 上游 workflow path、classification result、authority trace 和 rationale references
- `JE Generation Node` 的 journal entry result、JE consistency status 和 calculation rationale reference
- `Intervention Log` / review context 中与当前交易绑定的 questions、answers、corrections、confirmations 和 approvals
- `Profile`、`Entity Log`、`Case Log`、`Rule Log`、`Governance Log` 的引用或摘要，但只能作为审计 trace、authority trace 或 candidate context
- 既有 `Transaction Log` 记录，但仅用于 duplicate-final-log prevention、audit continuity 或 historical display boundary

`Transaction Log` 不参与当前 runtime classification、rule match、case judgment、JE decision 或 learning。

### 2.4 Logs / memory stores written or candidate-only

本节点唯一允许的 durable write 是 audit-facing `Transaction Log` 语义下的 `transaction_log_entry`。

本节点只能 candidate-only 保留：

- case memory update candidate context
- entity / alias / role candidate context
- rule candidate、rule conflict 或 rule-health candidate context
- profile change / tax config / account-mapping review candidate context
- automation-policy / governance candidate context
- post-batch lint candidate context

这些 candidate relationships 只表示后续 workflow 应评估。它们不写 `Case Log`、`Rule Log`、stable `Entity Log`、`Governance Log` 或 `Profile`，也不代表 accountant / governance approval。

## 3. Input Contracts

### 3.1 `transaction_logging_request`

**Purpose**

`transaction_logging_request` 是本节点的主 runtime input envelope，表示当前交易需要形成最终 audit-facing transaction record，或需要被本节点明确阻止 final logging。

**Source authority**

由 workflow orchestrator 汇总上游节点输出形成。该 envelope 不自行创造 product authority；每个字段的 authority 来自对应上游节点、accountant decision 或 durable store reference。

**Required fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `logging_request_id` | 本次 logging request 引用 | workflow runtime | runtime |
| `client_id` | 当前客户标识 | client / batch context | durable reference |
| `batch_id` | 当前处理批次 | workflow runtime | runtime |
| `transaction_context` | 当前交易客观基础 | Evidence Intake / Transaction Identity | runtime object with durable refs |
| `final_outcome_context` | 当前交易最终处理结果 | upstream classification / review path | runtime object with durable refs |
| `journal_entry_context` | JE result 或 JE blocking context | `JE Generation Node` | runtime object with durable refs |
| `authority_context` | final logging authority 与限制 | upstream workflow / accountant / governance context | runtime projection |
| `audit_trace_context` | 需要保留的审计轨迹 | upstream workflow | runtime object with durable refs |

**Optional fields**

- `candidate_context`：只保留候选关系，不执行 durable mutation。
- `existing_log_context`：既有 Transaction Log 状态，用于阻止重复 final logging。
- `runtime_notes`：runtime diagnostics；不能作为业务结论或 authority。

**Validation / rejection rules**

输入无效或必须被阻止 normal final logging，如果：

- 缺少 `transaction_context.transaction_id`
- `transaction_context.evidence_refs` 无法支持 audit traceability
- `final_outcome_context.outcome_status` 不是可 final logging 的状态
- `journal_entry_context.je_status != generated`
- `authority_context.final_logging_authority_status != authorized`
- 当前交易仍是 `pending`、`still_pending`、`review_required`、`not_approved`、`governance_blocked`、`conflicting` 或 `not_finalizable`
- `existing_log_context.existing_final_log_status = already_logged`
- request 试图把 candidate-only、review package、report draft、governance candidate 或 lint finding 当成 final audit record

**Runtime-only vs durable references**

`transaction_logging_request` 是 runtime-only envelope。它可以携带 durable references，但接收该 request 不授予本节点修改任何非 `Transaction Log` memory store 的权力。

### 3.2 `transaction_context`

**Purpose**

把 final audit record 绑定到稳定交易身份、客观金额方向、账户语境和证据引用。

**Source authority**

来自 `Evidence Intake / Preprocessing Node` 与 `Transaction Identity Node`。`transaction_id` authority 来自 transaction identity layer。

**Required fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `transaction_id` | 稳定交易 ID | `Transaction Identity Node` | durable reference |
| `transaction_date` | 交易日期 | evidence / preprocessing | durable transaction fact |
| `amount_abs` | 绝对金额 | evidence / preprocessing | durable transaction fact |
| `direction` | 资金方向 | evidence / preprocessing | durable transaction fact |
| `bank_account` | 客户侧银行账户引用 | evidence / Profile context | durable reference |
| `evidence_refs` | 支撑当前交易的证据引用 | `Evidence Log` | durable references |

**Allowed values**

`direction` 允许：

- `inflow`
- `outflow`

**Optional fields**

- `raw_description`
- `description`
- `pattern_source`
- `receipt_refs`
- `cheque_info_refs`
- `counterparty_surface_text`
- `currency`
- `import_batch_id`

**Validation / rejection rules**

- `amount_abs` 必须为正数；金额符号不能与 `direction` 重复表达。
- `direction` 必须属于允许值。
- `evidence_refs` 不能为空，除非后续阶段明确允许某类 terminal non-JE record 记录 evidence-limited outcome；当前 normal final logging 下不能为空。
- `description = null` 和 `pattern_source = null` 是有效状态；本节点不能要求 canonical description 存在。
- 本节点不能修改 `transaction_id`、原始 evidence 或客观交易事实。

**Runtime-only vs durable references**

该对象是 runtime handoff。字段来自 durable transaction / evidence foundation，但本节点只记录 snapshot / references，不成为客观交易事实来源。

### 3.3 `final_outcome_context`

**Purpose**

说明当前交易最终被怎样处理，以及该处理结果来自哪条 authority path。

**Source authority**

来自已完成的 structural / rule / case / pending / review workflow。accountant approval 或 correction 的 authority 来自 `Review Node` / intervention context，而不是本节点。

**Required fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `outcome_status` | 当前 outcome 是否可最终记录 | upstream workflow | runtime |
| `authority_path` | outcome 的来源路径 | upstream workflow | runtime |
| `accounting_outcome_summary` | 当前交易最终会计处理摘要 | upstream classification / review path | runtime snapshot |
| `outcome_rationale_refs` | 支持 outcome 的 rationale / evidence / memory refs | upstream workflow | durable refs |

**Allowed values**

`outcome_status` 允许：

- `finalizable_system_outcome`
- `accountant_approved_outcome`
- `accountant_corrected_outcome`
- `pending`
- `review_required`
- `not_approved`
- `governance_blocked`
- `conflicting`

`authority_path` 允许：

- `profile_structural`
- `rule_handled`
- `case_supported`
- `pending_resolved`
- `accountant_approved`
- `accountant_corrected`

**Required `accounting_outcome_summary` fields**

- `classification_result_ref`：上游最终分类结果引用，或 accountant-corrected outcome 引用。
- `account_refs`：最终 outcome 涉及的 COA / account references。
- `tax_treatment_refs`：最终 outcome 使用的 GST/HST / tax treatment references；如不适用，应由上游明确说明。

**Optional fields**

- `entity_ref`
- `rule_ref`
- `case_refs`
- `review_decision_ref`
- `intervention_refs`
- `policy_trace`
- `confidence_summary`
- `outcome_notes`

**Validation / rejection rules**

- 只有 `finalizable_system_outcome`、`accountant_approved_outcome`、`accountant_corrected_outcome` 可以支持 normal final logging。
- `pending`、`review_required`、`not_approved`、`governance_blocked`、`conflicting` 必须阻止 normal final logging。
- `authority_path = accountant_approved` 或 `accountant_corrected` 时，必须提供 `review_decision_ref` 或可追溯 `intervention_refs`。
- `authority_path = rule_handled` 时，`rule_ref` 必须指向 approved active rule；candidate rule 不能支持 final logging。
- `authority_path = case_supported` 时，`case_refs` / rationale 必须说明为什么当前 authority 允许继续；case-supported 不等于 durable case write。
- `policy_trace` 如存在，只能记录上游 AI / risk-pack activation trace，不能给本节点新的 decision authority。

**Runtime-only vs durable references**

`final_outcome_context` 是 runtime projection。它可以被 `Transaction Log` 记录为 audit snapshot / references，但不能由本节点升级为 `Case Log`、`Rule Log`、Entity authority 或 Profile truth。

### 3.4 `journal_entry_context`

**Purpose**

说明当前交易是否已有可供审计、输出和 final logging 使用的 journal entry result。

**Source authority**

来自 `JE Generation Node`。本节点不能生成、修正、补齐或重算 JE。

**Required fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `je_status` | JE 是否已生成且可用于 final logging | `JE Generation Node` | runtime |
| `je_trace_refs` | JE 计算依据和结果引用 | `JE Generation Node` | durable / runtime refs |

**Allowed values**

`je_status` 允许：

- `generated`
- `blocked`
- `not_finalizable`
- `not_required_open_boundary`

**Conditionally required fields**

当 `je_status = generated` 时 required：

- `journal_entry_ref`
- `balanced`
- `je_total_debits`
- `je_total_credits`
- `je_result_summary`

当 `je_status = blocked` 或 `not_finalizable` 时 required：

- `je_blocked_reason`
- `blocked_by_node`
- `required_resolution_context`

**Optional fields**

- `tax_summary`
- `calculation_rationale_ref`
- `consistency_issue_refs`
- `je_notes`

**Validation / rejection rules**

- normal final logging 下，`je_status` 必须是 `generated`。
- `balanced` 必须为 `true`。
- `je_total_debits` 必须等于 `je_total_credits`。
- `journal_entry_ref` 必须能绑定到同一 `transaction_id`。
- `blocked`、`not_finalizable` 或 `not_required_open_boundary` 不能被写成普通 completed-transaction audit record。
- 本节点不能用 fallback account、默认 tax treatment 或自然语言说明补齐 JE 缺口。

**Runtime-only vs durable references**

`journal_entry_context` 是 runtime handoff with JE references。`Transaction Log` 可以记录 JE summary / references，但本节点不成为 JE authority。

### 3.5 `authority_context`

**Purpose**

说明当前交易为什么可以或不可以被最终记录。

**Source authority**

来自 upstream workflow gates、automation policy、rule lifecycle、review decision、accountant correction、pending resolution 和 governance restrictions。

**Required fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `final_logging_authority_status` | 当前是否具备 final logging authority | upstream workflow / accountant / governance context | runtime |
| `authority_basis_refs` | 支持该 authority status 的引用 | upstream workflow | durable refs |
| `blocked_reasons` | 阻断 normal final logging 的原因；authorized 时可为空 | upstream workflow / this node validation | runtime |

**Allowed values**

`final_logging_authority_status` 允许：

- `authorized`
- `pending`
- `review_required`
- `not_approved`
- `governance_blocked`
- `je_blocked`
- `traceability_blocked`
- `conflicting`

**Optional fields**

- `accountant_decision_ref`
- `review_decision_status`
- `automation_policy_snapshot`
- `rule_lifecycle_snapshot`
- `governance_restriction_refs`
- `authority_notes`

**Validation / rejection rules**

- 只有 `authorized` 可以支持 normal final logging。
- 如果 `review_decision_status` 表示未批准、仍 pending 或冲突，本节点不能将其解释为 approval。
- `accountant_decision_ref` 缺失时，不能声称 accountant-approved / corrected authority。
- governance restriction 未解决时，必须阻止 normal final logging。
- authority notes、confidence 或 LLM summary 不能覆盖 explicit block。

**Runtime-only vs durable references**

该对象是 runtime authority projection。`Transaction Log` 可以记录其 snapshot / refs，但本节点不能因记录 authority context 而批准长期 memory 或 governance change。

### 3.6 `audit_trace_context`

**Purpose**

定义最终 `Transaction Log` 需要保留的关键审计轨迹。

**Source authority**

来自上游 workflow、durable evidence references、review / intervention context、JE result 和相关 memory references。

**Required fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `workflow_path` | 本笔交易经过的主要 workflow path | workflow orchestrator | runtime |
| `evidence_refs` | 支撑当前处理结果的 evidence references | `Evidence Log` / upstream nodes | durable refs |
| `upstream_result_refs` | 上游 result / rationale references | upstream nodes | durable / runtime refs |
| `journal_entry_ref` | JE result 引用 | `JE Generation Node` | durable / runtime ref |

**Optional fields**

- `profile_structural_refs`
- `entity_refs`
- `rule_refs`
- `case_refs`
- `review_decision_refs`
- `intervention_refs`
- `governance_refs`
- `policy_trace`
- `audit_narrative`
- `trace_completeness_notes`

**Validation / rejection rules**

- `workflow_path` 不能缺失到无法解释 outcome 来源。
- `evidence_refs`、`upstream_result_refs`、`journal_entry_ref` 必须与同一 `transaction_id` 绑定。
- `audit_narrative` 只能总结已存在 refs / rationale，不能补充新事实。
- `Transaction Log` 中的 trace 是 audit support，不是 future runtime decision source。

**Runtime-only vs durable references**

该对象是 runtime audit projection。被写入 `Transaction Log` 后形成 durable audit record 的一部分，但不成为 learning layer。

### 3.7 `candidate_context`

**Purpose**

保留本笔 completed transaction 与后续 memory / governance / lint 候选的关系。

**Source authority**

来自上游 candidate signals、review context、JE issue context 或本节点发现的 logging consistency boundary。候选本身不具备 approval authority。

**Optional fields**

- `case_memory_candidate_refs`
- `entity_candidate_refs`
- `alias_candidate_refs`
- `role_candidate_refs`
- `rule_candidate_refs`
- `profile_change_candidate_refs`
- `tax_config_review_candidate_refs`
- `account_mapping_review_candidate_refs`
- `automation_policy_candidate_refs`
- `governance_candidate_refs`
- `post_batch_lint_candidate_refs`

**Validation / rejection rules**

- candidate refs 不得作为 final outcome authority。
- candidate refs 不得被写入 active Rule / Entity / Case / Governance memory by this node。
- 如果 candidate 与 current outcome 冲突到影响 finalization，应转为 blocked handoff 或 consistency issue，而不是保留为普通候选。

**Runtime-only vs durable references**

`candidate_context` 本身是 runtime-only。被 `Transaction Log` 保留时，只是 durable audit relation / candidate relation，不是 durable memory mutation。

### 3.8 `existing_log_context`

**Purpose**

说明当前交易是否已经有 completed final transaction log，防止重复正常落盘。

**Source authority**

来自 `Transaction Log` 查询结果，只能用于 duplicate-final-log prevention、audit continuity 或 historical display boundary。

**Required fields when provided**

- `existing_final_log_status`

**Allowed values**

- `not_logged`
- `already_logged`
- `possible_duplicate_log`

**Optional fields**

- `existing_transaction_log_entry_refs`
- `prior_logging_notes`

**Validation / rejection rules**

- `already_logged` 或 `possible_duplicate_log` 必须阻止 normal duplicate final logging，除非后续阶段定义 correction / reversal / supersession contract。
- 既有 `Transaction Log` 不得作为当前 classification、rule match、case judgment 或 JE authority。

**Runtime-only vs durable references**

该对象是 runtime query projection。它不授权本节点重写历史日志。

## 4. Output Contracts

### 4.1 `transaction_log_entry`

**Purpose**

`transaction_log_entry` 是写入 audit-facing `Transaction Log` 的 durable final record，保存当前交易最终处理结果和关键审计轨迹。

**Consumer / downstream authority**

下游可以查询它用于审计、review history、output flow、Case Memory Update、Governance Review、Knowledge Compilation 和 Post-Batch Lint。它不参与 future runtime decision，也不是 learning layer、rule source 或 governance approval。

**Required fields**

| Field | Meaning | Authority | Durable / Runtime |
| --- | --- | --- | --- |
| `transaction_log_entry_id` | 本条 Transaction Log 记录引用 | Transaction Log write boundary | durable audit reference |
| `client_id` | 客户标识 | input request | durable reference |
| `batch_id` | 批次引用 | input request | durable / runtime reference |
| `transaction_id` | 稳定交易 ID | `Transaction Identity Node` | durable reference |
| `logged_at` | 写入时间 | Transaction Logging write event | durable audit metadata |
| `entry_status` | 本条记录状态 | Transaction Logging contract | durable audit field |
| `transaction_snapshot` | 当前交易客观事实快照 | `transaction_context` | durable audit snapshot |
| `final_outcome_snapshot` | 最终处理结果快照 | `final_outcome_context` | durable audit snapshot |
| `journal_entry_snapshot` | JE result summary / refs | `journal_entry_context` | durable audit snapshot |
| `authority_trace` | final logging authority refs | `authority_context` | durable audit snapshot |
| `audit_trace_refs` | evidence / workflow / review / intervention refs | `audit_trace_context` | durable references |

**Allowed values**

`entry_status` 当前只允许：

- `final_logged`

Stage 3 不把 blocked、pending、review-required 或 not-finalizable 伪装成 `transaction_log_entry.entry_status`。terminal non-JE audit record 是否存在，是 Open Contract Boundary。

**Optional fields**

- `policy_trace`
- `candidate_relationships`
- `audit_narrative`
- `trace_completeness_notes`
- `source_node_versions`

**Validation rules**

- 必须绑定单一稳定 `transaction_id`。
- `entry_status` 必须是 `final_logged`。
- `journal_entry_snapshot.je_status` 必须是 `generated`。
- `authority_trace.final_logging_authority_status` 必须是 `authorized`。
- `final_outcome_snapshot.outcome_status` 必须是可 final logging 状态。
- `audit_trace_refs` 必须足以追溯 evidence、workflow path、JE result 和任何 accountant approval / correction。
- `candidate_relationships` 如存在，必须标记为 candidate-only，不得表示 approval。
- 不得包含本节点生成的新 COA、tax treatment、classification、JE line、entity authority、rule authority 或 governance approval。

**Durable memory boundary**

这是 durable audit record，只属于 `Transaction Log`。它不能被后续 runtime classifier、Rule Match 或 Case Judgment 当作 authority source。后续 governance 变化不重写历史 `transaction_log_entry`。

### 4.2 `transaction_log_write_receipt`

**Purpose**

runtime-only 写入结果引用，用于让 workflow 明确本节点已完成或未完成 durable write。

**Consumer / downstream authority**

workflow orchestrator、output flow、Case Memory Update、Governance Review、Knowledge Compilation、Post-Batch Lint 可读取该 receipt 来定位 `transaction_log_entry`。

**Required fields**

- `logging_request_id`
- `write_status`
- `transaction_id`

**Allowed values**

`write_status` 允许：

- `written`
- `blocked`
- `consistency_issue`

**Conditionally required fields**

- `transaction_log_entry_id`：当 `write_status = written` 时 required。
- `blocked_handoff_ref`：当 `write_status = blocked` 时 required。
- `consistency_issue_ref`：当 `write_status = consistency_issue` 时 required。

**Optional fields**

- `post_logging_handoff_ref`
- `runtime_notes`

**Validation rules**

- `written` 必须对应一个有效 `transaction_log_entry_id`。
- `blocked` 或 `consistency_issue` 不得同时声称 durable final log 已写入。

**Memory boundary**

该 receipt 是 runtime-only handoff，不是 `Transaction Log` durable content，也不是 review / governance approval。

### 4.3 `final_logging_blocked_handoff`

**Purpose**

当 normal final logging 条件不满足时，安全停止并把问题交回合适的上游 / review / governance workflow。

**Consumer / downstream authority**

可由 workflow orchestrator、Coordinator、Review、JE Generation、上游 node 或 Governance Review 消费。具体 routing 留给后续 Stage 4，不在本阶段定义。

**Required fields**

- `blocked_handoff_id`
- `logging_request_id`
- `transaction_id`
- `blocked_reason_type`
- `blocked_reason_summary`
- `required_resolution_context`
- `source_refs`

**Allowed `blocked_reason_type` values**

- `missing_transaction_identity`
- `missing_evidence_trace`
- `outcome_not_finalizable`
- `review_or_approval_missing`
- `journal_entry_missing`
- `journal_entry_not_finalizable`
- `authority_block`
- `governance_block`
- `conflicting_context`
- `duplicate_final_log`

**Optional fields**

- `suggested_return_node`
- `affected_candidate_refs`
- `accountant_facing_summary`
- `runtime_notes`

**Validation rules**

- Must not write `transaction_log_entry` for the same request as a normal final record.
- Must not change final outcome, JE, review decision or governance state.
- `accountant_facing_summary` 只能解释 block，不能替 accountant 作决定。

**Memory boundary**

runtime-only。它不是 durable final audit record，除非后续阶段单独定义 terminal non-JE / blocked audit record contract。

### 4.4 `logging_consistency_issue_signal`

**Purpose**

表达 final outcome、JE context、authority trace、evidence refs、review / intervention trace 或 existing Transaction Log 之间存在不一致。

**Consumer / downstream authority**

workflow orchestrator、Review、Coordinator、JE Generation、Governance Review 或 post-batch analysis 可消费该 signal。它不自行修复问题。

**Required fields**

- `consistency_issue_id`
- `logging_request_id`
- `transaction_id`
- `issue_type`
- `issue_summary`
- `conflicting_refs`
- `safe_next_boundary`

**Allowed `issue_type` values**

- `transaction_id_mismatch`
- `evidence_ref_missing_or_mismatched`
- `outcome_je_mismatch`
- `authority_trace_conflict`
- `review_intervention_conflict`
- `duplicate_or_prior_log_conflict`
- `candidate_conflicts_with_finalization`

**Optional fields**

- `severity`
- `accountant_facing_summary`
- `governance_candidate_refs`
- `runtime_notes`

**Validation rules**

- 该 signal 不能与 normal `transaction_log_entry` write 同时代表同一 unresolved issue 已被忽略。
- `conflicting_refs` 必须指出至少两个不一致来源或一个缺失的 required authority source。

**Memory boundary**

runtime-only issue signal。它不创建 governance event、不修改 memory、不重写历史 Transaction Log。

### 4.5 `post_logging_handoff`

**Purpose**

在 `transaction_log_entry` 成功写入后，把已完成交易的审计引用和 candidate relationships 交给后续 workflow。

**Consumer / downstream authority**

- `Case Memory Update Node`：可读取 completed transaction audit context，但是否写入 Case Log 属于它的 authority。
- `Governance Review Node`：可读取 candidate / governance context，但 approval 属于 governance workflow。
- `Knowledge Compilation Node`：可读取审计历史作摘要背景，但 summary 不成为 deterministic rule source。
- `Post-Batch Lint Node`：可读取已完成交易和 candidate relationships 做批后体检。
- output flow：可读取 final result 和 audit refs 供展示 / export。

**Required fields**

- `transaction_log_entry_id`
- `transaction_id`
- `client_id`
- `batch_id`
- `available_audit_refs`

**Optional fields**

- `case_memory_candidate_refs`
- `governance_candidate_refs`
- `knowledge_compilation_refs`
- `post_batch_lint_refs`
- `output_flow_refs`

**Validation rules**

- 必须引用已成功写入的 `transaction_log_entry`。
- candidate refs 不得表示 durable approval。
- 不得要求下游把 `Transaction Log` 当作 runtime decision source。

**Memory boundary**

runtime-only handoff。它可以携带 durable references，但不执行任何 durable mutation。

## 5. Field Authority and Memory Boundary

### 5.1 Source of truth for important fields

- `transaction_id` 的 source of truth 是 `Transaction Identity Node` / transaction identity layer。
- `amount_abs`、`direction`、`transaction_date`、`bank_account` 和 raw evidence references 的 source of truth 是 evidence / preprocessing flow 和 `Evidence Log`。
- classification / accounting outcome 的 source of truth 是完成该 outcome 的 upstream workflow path 或 accountant review / correction。
- `journal_entry_ref`、balanced status、JE totals 和 JE rationale 的 source of truth 是 `JE Generation Node`。
- accountant approval / correction 的 source of truth 是 `Review Node` / `Intervention Log` 中可追溯 decision context。
- entity、alias、role、rule、automation policy、governance restriction 的 source of truth 分别是对应 durable store 和 approved governance context。
- `transaction_log_entry` 的 source of truth 仅限已写入的 audit-facing `Transaction Log` record。

### 5.2 Fields that can never become durable memory by this node

本节点永远不能把以下字段或对象写成长期业务 memory：

- `candidate_context` 中的任何 candidate refs
- `policy_trace` 中的 runtime AI activation / risk-pack trace
- `confidence_summary`
- `audit_narrative`
- `runtime_notes`
- `accountant_facing_summary`
- `logging_consistency_issue_signal`
- `final_logging_blocked_handoff`
- `post_logging_handoff`

这些内容可以作为 audit context 或 runtime handoff 被保留，但不能成为 stable entity、approved alias、confirmed role、active rule、case memory、Profile truth 或 governance approval。

### 5.3 Fields that can become durable only after accountant / governance approval

以下内容如果要进入长期 authority，必须经后续 accountant / governance approval path：

- new entity、alias、role、merge / split、entity status 或 automation policy 变化
- rule creation、promotion、modification、deletion、downgrade 或 conflict resolution
- profile change、tax config change、account mapping change
- case memory update 是否可沉淀为 `Case Log`
- repeated correction 是否支持 rule candidate 或 automation-policy change

`Transaction Logging Node` 最多记录它们与当前 completed transaction 的 candidate relationship。

### 5.4 Audit vs learning / logging boundary

`Transaction Log` 是 audit-facing durable record。它保存“当时为什么这样处理”和“结果如何形成”的 trace。

它不是：

- runtime classification source
- deterministic rule source
- Case Log memory
- Rule Log memory
- stable Entity Log authority
- Governance Log approval
- Profile truth
- report draft 或 review package

后续节点可以查询 `Transaction Log` 理解历史和做审计 / lint / knowledge summary，但不能直接把它当作当前交易自动化依据。

## 6. Validation Rules

### 6.1 Contract-level validation rules

- 每个 normal `transaction_log_entry` 必须绑定一个稳定 `transaction_id`。
- `transaction_log_entry` 必须有可追溯 evidence refs、final outcome refs、JE refs 和 authority refs。
- `amount_abs` 必须为正数；direction 只能由 `direction` 字段表达。
- `journal_entry_context.je_status` 必须是 `generated`，且 JE 必须 balanced，才可 normal final logging。
- `authority_context.final_logging_authority_status` 必须是 `authorized`，才可 normal final logging。
- candidate-only 内容必须显式保留 candidate boundary。
- `Transaction Log` 历史记录不得被用于当前 runtime classification / learning authority。

### 6.2 Conditions that make the input invalid

输入 invalid 或必须停止，如果：

- 缺少 `transaction_id`
- 缺少足够 evidence refs 支持 audit traceability
- final outcome 仍 pending、review-required、not-approved、conflicting 或 governance-blocked
- JE 缺失、blocked、not-finalizable、unbalanced 或无法绑定同一 transaction
- accountant approval / correction 缺失但 request 声称 accountant authority
- candidate-only signal 被包装成 final outcome
- 既有 `Transaction Log` 表明该交易已 final logged，且后续 correction / supersession contract 未定义

### 6.3 Conditions that make the output invalid

输出 invalid，如果：

- `transaction_log_entry.entry_status` 不是 `final_logged`
- durable entry 中缺少 transaction / outcome / JE / authority / evidence trace 任一核心绑定
- durable entry 包含本节点新创造的 COA、tax treatment、classification 或 JE result
- durable entry 把 candidate relationship 表示为 approved memory
- blocked handoff 同时声称 normal final log 已写入
- consistency issue 被忽略并仍写入 normal final record
- post logging handoff 要求下游把 `Transaction Log` 当作 runtime decision source

### 6.4 Stop / ask conditions for unresolved contract authority

后续阶段或实现前必须 stop / ask，如果需要决定：

- JE-blocked / not-finalizable 是否需要 terminal audit-facing durable record。
- correction、reversal、superseded transaction、split transaction 或 reprocessing 如何影响既有 `Transaction Log`。
- 哪些 high-confidence system outcome 可以不经逐笔 review 直接进入 JE / final logging。
- Review Node 是否覆盖所有 final logging 前交易，还是只覆盖 review-required / sampled / governance-candidate items。
- `Transaction Log` 与 final output artifact 的 exact field-level boundary。

## 7. Examples

### 7.1 Valid minimal example

```json
{
  "transaction_logging_request": {
    "logging_request_id": "tl_req_001",
    "client_id": "client_001",
    "batch_id": "batch_2026_05",
    "transaction_context": {
      "transaction_id": "txn_01HZXAMPLE0001",
      "transaction_date": "2026-05-01",
      "amount_abs": "45.20",
      "direction": "outflow",
      "bank_account": "bank_operating_cad",
      "evidence_refs": ["ev_bank_001"]
    },
    "final_outcome_context": {
      "outcome_status": "finalizable_system_outcome",
      "authority_path": "rule_handled",
      "accounting_outcome_summary": {
        "classification_result_ref": "cls_001",
        "account_refs": ["coa_meals"],
        "tax_treatment_refs": ["tax_hst_itc_partial"]
      },
      "outcome_rationale_refs": ["rule_approved_001"],
      "rule_ref": "rule_approved_001"
    },
    "journal_entry_context": {
      "je_status": "generated",
      "journal_entry_ref": "je_001",
      "balanced": true,
      "je_total_debits": "45.20",
      "je_total_credits": "45.20",
      "je_result_summary": "balanced expense entry",
      "je_trace_refs": ["je_calc_001"]
    },
    "authority_context": {
      "final_logging_authority_status": "authorized",
      "authority_basis_refs": ["rule_approved_001"],
      "blocked_reasons": []
    },
    "audit_trace_context": {
      "workflow_path": ["evidence_intake", "transaction_identity", "entity_resolution", "rule_match", "je_generation"],
      "evidence_refs": ["ev_bank_001"],
      "upstream_result_refs": ["entity_res_001", "rule_match_001", "cls_001"],
      "journal_entry_ref": "je_001"
    }
  }
}
```

Expected contract result：可写 `transaction_log_entry`，entry status 为 `final_logged`。该 entry 记录 rule / JE / evidence refs，但不让 `Transaction Log` 成为 future rule source。

### 7.2 Valid richer example

```json
{
  "transaction_logging_request": {
    "logging_request_id": "tl_req_002",
    "client_id": "client_001",
    "batch_id": "batch_2026_05",
    "transaction_context": {
      "transaction_id": "txn_01HZXAMPLE0002",
      "transaction_date": "2026-05-02",
      "amount_abs": "1280.00",
      "direction": "outflow",
      "bank_account": "bank_operating_cad",
      "evidence_refs": ["ev_bank_002", "ev_receipt_010"],
      "raw_description": "HOME DEPOT #4521",
      "receipt_refs": ["ev_receipt_010"]
    },
    "final_outcome_context": {
      "outcome_status": "accountant_corrected_outcome",
      "authority_path": "accountant_corrected",
      "accounting_outcome_summary": {
        "classification_result_ref": "review_correction_004",
        "account_refs": ["coa_materials"],
        "tax_treatment_refs": ["tax_hst_itc_supported"]
      },
      "outcome_rationale_refs": ["case_judgment_017", "review_decision_004"],
      "entity_ref": "entity_home_depot",
      "case_refs": ["case_112", "case_145"],
      "review_decision_ref": "review_decision_004",
      "intervention_refs": ["intervention_021"],
      "policy_trace": {
        "activated_packs": ["mixed_use_risk"],
        "override_evidence_refs": ["ev_receipt_010"]
      }
    },
    "journal_entry_context": {
      "je_status": "generated",
      "journal_entry_ref": "je_002",
      "balanced": true,
      "je_total_debits": "1280.00",
      "je_total_credits": "1280.00",
      "je_result_summary": "balanced materials expense and HST entry",
      "tax_summary": "HST/GST Receivable based on approved correction",
      "je_trace_refs": ["je_calc_002"]
    },
    "authority_context": {
      "final_logging_authority_status": "authorized",
      "authority_basis_refs": ["review_decision_004"],
      "accountant_decision_ref": "review_decision_004",
      "review_decision_status": "corrected",
      "blocked_reasons": []
    },
    "audit_trace_context": {
      "workflow_path": ["evidence_intake", "transaction_identity", "entity_resolution", "case_judgment", "review", "je_generation"],
      "evidence_refs": ["ev_bank_002", "ev_receipt_010"],
      "upstream_result_refs": ["entity_res_044", "case_judgment_017", "review_decision_004"],
      "review_decision_refs": ["review_decision_004"],
      "intervention_refs": ["intervention_021"],
      "journal_entry_ref": "je_002",
      "policy_trace": {
        "activated_packs": ["mixed_use_risk"],
        "override_evidence_refs": ["ev_receipt_010"]
      }
    },
    "candidate_context": {
      "case_memory_candidate_refs": ["case_candidate_009"],
      "rule_candidate_refs": ["rule_candidate_003"]
    }
  }
}
```

Expected contract result：可写 `transaction_log_entry`。`case_candidate_009` 和 `rule_candidate_003` 只能作为 candidate relationships 保留，不能由本节点写入 Case Log 或 Rule Log。

### 7.3 Invalid example

```json
{
  "transaction_logging_request": {
    "logging_request_id": "tl_req_bad_001",
    "client_id": "client_001",
    "batch_id": "batch_2026_05",
    "transaction_context": {
      "transaction_id": "txn_01HZXAMPLE0999",
      "transaction_date": "2026-05-03",
      "amount_abs": "-300.00",
      "direction": "outflow",
      "bank_account": "bank_operating_cad",
      "evidence_refs": []
    },
    "final_outcome_context": {
      "outcome_status": "review_required",
      "authority_path": "case_supported",
      "accounting_outcome_summary": {
        "classification_result_ref": "case_guess_999",
        "account_refs": ["coa_repairs"],
        "tax_treatment_refs": ["tax_unknown"]
      },
      "outcome_rationale_refs": ["case_judgment_999"]
    },
    "journal_entry_context": {
      "je_status": "not_finalizable",
      "je_blocked_reason": "tax treatment unresolved",
      "blocked_by_node": "je_generation",
      "required_resolution_context": "review tax treatment",
      "je_trace_refs": []
    },
    "authority_context": {
      "final_logging_authority_status": "review_required",
      "authority_basis_refs": ["case_judgment_999"],
      "blocked_reasons": ["review required", "JE not finalizable"]
    },
    "audit_trace_context": {
      "workflow_path": ["case_judgment"],
      "evidence_refs": [],
      "upstream_result_refs": ["case_judgment_999"],
      "journal_entry_ref": null
    }
  }
}
```

Invalid reasons：

- `amount_abs` 使用了负号，违反 amount-as-absolute-value contract。
- `evidence_refs` 为空，不能支持 normal final audit traceability。
- outcome 仍是 `review_required`。
- JE 是 `not_finalizable`，没有 generated balanced JE。
- authority 不是 `authorized`。

正确 contract behavior 是输出 `final_logging_blocked_handoff` 或 `logging_consistency_issue_signal`，不得写普通 `transaction_log_entry`。

## 8. Open Contract Boundaries

- JE-blocked / not-finalizable 是否需要单独 terminal audit-facing durable record，仍未由 active docs 决定。本 Stage 3 只允许它阻止 normal final logging。
- correction、reversal、superseded transaction、split transaction 和 reprocessing 如何影响既有 `Transaction Log`，仍未冻结。
- 哪些 high-confidence structural / rule / case-supported result 可以不经逐笔 accountant review 直接进入 JE / final logging，仍属于跨节点 authority boundary。
- Review Node 是否覆盖所有 final logging 前交易，还是只覆盖 review-required / sampled / governance-candidate items，仍未冻结。
- `Transaction Log` 与 final output report / export artifact 的 exact field-level boundary 仍未冻结。
- `journal_entry_context.je_result_summary` 的完整字段结构应由 JE Generation 的 Stage 3 / shared contract 冻结；本文件只要求可追溯引用和 minimum audit summary。
- duplicate final logging prevention 已定义为 contract boundary，但 idempotency key、correction flow 和 historical supersession behavior 留给后续阶段。

## 9. Self-Review

- 已阅读 required governance docs：`AGENTS.md`、`TASK_STATE.md`、`PLANS.md`、`CLAUDE.md`、`DECISIONS.md`、`supporting documents/communication_preferences.md`、`supporting documents/development_workflow.md`、`supporting documents/node_design_roadmap.md`。
- 已阅读 active baseline：`new system/new_system.md`，包括 `当前系统由哪些 Workflow Nodes 与 Logs 组成`。
- 已阅读 prior approved Stage 1/2 docs：`transaction_logging_node__stage_1__functional_intent.md`、`transaction_logging_node__stage_2__logic_and_boundaries.md`。
- 已读取可用 Superpowers docs：`using-superpowers/SKILL.md`、`brainstorming/SKILL.md`；project workflow skill `ai-bookkeeper-node-design-facilitation` 在当前环境不存在，因此按 runner instruction 使用 repo `supporting documents/node_design_roadmap.md` 与本节点 Stage 1/2 docs 作为 workflow authority。
- 已按 prompt 记录 optional-reading absence：`supporting documents/node_design_roadmap_zh.md` 在工作树中缺失，未编造该文件。
- 本文只定义 Stage 3 data contracts；未进入 Stage 4 execution algorithm、Stage 5 technical implementation map、Stage 6 test matrix、Stage 7 coding-agent task contract。
- 本文未把 `Transaction Log` 设计成 runtime decision source 或 learning layer。
- 本文未赋予本节点修改 `Profile`、`Entity Log`、`Case Log`、`Rule Log` 或 `Governance Log` 的权限。
- 本文未把 candidate-only signal、Case Judgment output、review package、report draft 或 JE-blocked handoff 伪装成 durable final audit record。
- 本文未发明 unsupported product authority；未决产品边界已列入 `Open Contract Boundaries`。
- 若未 blocked，本次只写入目标文件：`new system/node_stage_designs/transaction_logging_node__stage_3__data_contract.md`。
