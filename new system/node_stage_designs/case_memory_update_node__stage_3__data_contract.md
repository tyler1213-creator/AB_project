# Case Memory Update Node — Stage 3：Data Contract Spec

## 1. Stage 范围

本 Stage 3 只定义 `Case Memory Update Node` 的 implementation-facing data contracts。

前置依据：

- `new system/node_stage_designs/case_memory_update_node__stage_1__functional_intent.md`
- `new system/node_stage_designs/case_memory_update_node__stage_2__logic_and_boundaries.md`
- active baseline：`new system/new_system.md`

本文件把 Stage 1/2 已确定的 completed-transaction case-learning、authority boundary、candidate-only handoff 和 memory/log 边界转换为输入对象、输出对象、字段含义、字段 authority、runtime-only / durable-memory 边界、validation rules 和紧凑示例。

本阶段不定义：

- step-by-step execution algorithm 或 branch sequence
- 技术实现路径、repo module、class、API、storage engine 或 DB migration
- test matrix、fixture plan 或 coding-agent task contract
- 新 product authority
- legacy replacement mapping
- `Case Log`、`Entity Log`、`Rule Log`、`Governance Log` 的全局完整 schema

## 2. Contract Position in Workflow

### 2.1 Upstream handoff consumed

本节点消费 `case_memory_update_request`。

该 request 必须由 workflow orchestration 在交易已经经过 finalization boundary 后形成，来源可以包括：

- completed structural / rule / case-supported outcome
- Review Node 的 accountant-approved 或 accountant-corrected current outcome handoff
- JE Generation completion context
- Transaction Logging Node 或等价 finalization handoff
- 与当前交易绑定的 Intervention Log / review / correction context
- 上游 entity、case、rule、governance candidate signals

本节点不接收仍处于 pending、review-required、not-approved、JE-blocked、identity unresolved、evidence conflicting 或 governance-blocked 状态的普通 runtime judgment。

### 2.2 Downstream handoff produced

本节点输出 `case_memory_update_result`。

下游消费者包括：

- `Case Judgment Node`：未来读取 `Case Log` 中的 case precedent；不读取本节点 runtime result 作为直接判断依据。
- `Governance Review Node`：消费 entity / alias / role / rule / automation-policy / governance candidate handoff。
- `Knowledge Compilation Node`：消费 knowledge compilation handoff，后续重新编译客户知识摘要。
- `Post-Batch Lint Node`：消费 consistency / rule-health / entity-risk signal。
- `Review Node` 或 `Coordinator / Pending Node`：在 blocked / invalid / unresolved authority 时接收回退信号。

### 2.3 Logs / memory stores read

本节点可以读取或消费引用：

- `Evidence Log`：原始证据和 evidence references。
- `Transaction Log` 或等价 finalization handoff：只用于确认当前交易已完成和审计 trace 可追溯；不作为未来 runtime decision source。
- `Intervention Log`：与当前交易绑定的 accountant question、answer、approval、correction、objection、review context。
- `Entity Log`：当前 entity / alias / role / automation policy 的 authority context。
- `Case Log`：用于 duplication、supersession、conflict risk 检查；不是让本节点重判当前交易。
- `Rule Log`：用于识别 rule conflict / rule candidate context；不执行 rule match。
- `Governance Log`：用于识别已生效 restriction 或 pending governance risk。
- `Knowledge Log / Summary Log`：仅作 case wording 或 candidate context 背景；不作为 deterministic rule source。

### 2.4 Logs / memory stores written or candidate-only

本节点唯一可直接 durable write 的语义目标是 `Case Log`：

- 写入真实 completed transaction case。
- 保留 final outcome、evidence、exception、review / correction、authority context。
- 明确该 case 只提供 future case precedent，不提供 deterministic rule authority。

本节点只能 candidate-only 输出：

- new entity / entity merge / entity split candidate
- alias approval / rejection candidate
- role confirmation candidate
- rule candidate / rule conflict / rule-health candidate
- automation-policy review candidate
- profile / tax config / account-mapping review candidate
- knowledge compilation handoff
- consistency issue signal

本节点不得写入或修改：

- `Transaction Log`
- `Profile`
- stable `Entity Log` authority
- `Rule Log`
- approved `Governance Log` mutation
- JE lines 或 accounting finalization record

## 3. Input Contracts

### 3.1 `case_memory_update_request`

Purpose：本节点的唯一 input envelope，表示一笔已完成交易正在进入 case-learning / candidate-handoff boundary。

Source authority：workflow orchestrator 汇总 finalization、review、JE、audit、evidence、entity、case、rule 和 governance context。该 envelope 不创造 product authority，只承载已由上游形成的 authority。

Required fields：

| Field | Meaning | Source authority | Runtime / durable |
| --- | --- | --- | --- |
| `request_id` | 本次 case memory update request 标识 | workflow runtime | runtime |
| `client_id` | 客户标识 | workflow / client context | durable reference |
| `batch_id` | 批次标识 | workflow runtime | runtime / durable batch ref |
| `transaction_id` | 稳定交易身份 | Transaction Identity Node | durable reference |
| `completed_transaction_basis` | 已完成交易基础 | finalization handoff | runtime view with durable refs |
| `learning_authority_context` | 是否允许写 Case Log 的 authority envelope | review / finalization / policy authority | runtime view over durable authority |
| `final_outcome_context` | 当前交易最终处理结果和 outcome source | structural / rule / case / review / correction path | runtime handoff with durable refs |
| `evidence_context` | 支撑 case 的 evidence refs 和 evidence sufficiency | Evidence Log / upstream nodes | durable refs + runtime summary |
| `entity_identity_context` | entity、alias、role、identity risk context | Entity Resolution / Entity Log / review context | runtime view with durable refs |
| `traceability_context` | outcome、evidence、review、JE、final logging 的绑定关系 | upstream workflow / logs | runtime validation envelope |

Optional fields：

| Field | Meaning | Source authority | Runtime / durable |
| --- | --- | --- | --- |
| `review_intervention_context` | accountant approval / correction / clarification / objection context | Review Node / Intervention Log | durable refs + runtime summary |
| `je_finalization_context` | JE 已生成或 finalization-ready 的证明 | JE Generation Node / finalization handoff | runtime view with durable refs |
| `transaction_logging_context` | final audit logging 或等价 finalization ref | Transaction Logging Node / Transaction Log | durable ref, audit-only |
| `prior_case_memory_context` | 既有 Case Log 中相关 case / duplicate / supersession context | Case Log | durable refs + runtime summary |
| `candidate_signal_inputs` | 上游已产生的 candidate signals | upstream nodes / review packaging | runtime / candidate refs |
| `governance_context` | 已生效或待处理 governance restriction / risk | Governance Log / governance workflow | durable refs + runtime view |
| `knowledge_summary_context` | 客户知识摘要背景 | Knowledge Log / Summary Log | durable ref / runtime summary |
| `request_trace` | 本次 request 的 packaging trace | workflow runtime | runtime-only |

Validation / rejection rules：

- `transaction_id`、`completed_transaction_basis`、`learning_authority_context`、`final_outcome_context`、`evidence_context`、`traceability_context` 缺失时，input invalid。
- `learning_authority_context.learning_authority_status != eligible_for_case_write` 时，不能写正常 `case_log_record`。
- 如果 `completed_transaction_basis.completion_status` 不是已完成状态，本节点必须输出 blocked / invalid result。
- `final_outcome_context` 不能只有 runtime suggestion、review draft、candidate signal 或 LLM rationale。
- `transaction_logging_context` 如存在，只能作为 audit/finalization proof，不得作为 future learning source 或 runtime decision basis。
- `request_trace` 不能替代 evidence refs、review refs、finalization refs 或 accountant authority。

Runtime-only vs durable references：

`case_memory_update_request` 是 runtime-only envelope。`transaction_id`、`evidence_refs`、`review/intervention refs`、`entity_id`、`case_id`、`rule_id`、`governance refs` 是 durable references，但本节点只拥有 `Case Log` write authority。

### 3.2 `completed_transaction_basis`

Purpose：证明当前 subject 是一笔已完成、可绑定、可沉淀的交易，而不是中间 judgment。

Source authority：Transaction Identity、JE / finalization、Review、Transaction Logging 或等价 finalization boundary。

Required fields：

| Field | Meaning | Source authority | Runtime / durable |
| --- | --- | --- | --- |
| `transaction_id` | 稳定交易 ID | Transaction Identity Node | durable reference |
| `completion_status` | 当前交易完成状态 | finalization workflow | runtime state |
| `completion_path` | 交易完成路径 | workflow orchestrator | runtime |
| `finalization_refs` | finalization / logging / JE / review refs | downstream finalization nodes | durable refs where applicable |
| `completed_at` | 完成时间 | finalization workflow | durable metadata if persisted |

Allowed `completion_status` values：

- `completed_finalized`
- `completed_logged`
- `completed_with_equivalent_finalization`
- `blocked_not_completed`
- `invalid_completion_claim`

Allowed `completion_path` values：

- `structural_path`
- `approved_rule_path`
- `case_supported_path`
- `accountant_approved_review_path`
- `accountant_corrected_review_path`
- `manual_finalization_path`

Optional fields：

- `final_transaction_log_ref`：final Transaction Log ref；audit-facing only。
- `je_ref`：相关 JE ref；本节点不读取 JE line 来重判会计处理。
- `review_decision_ref`：review decision / intervention ref。
- `reprocessing_context`：如果是 reprocess / correction 后完成，说明原交易与 supersession risk。

Validation / rejection rules：

- `completion_status` 为 `blocked_not_completed` 或 `invalid_completion_claim` 时，不能写 Case Log。
- `completion_path = approved_rule_path` 时，必须能追溯到 approved active rule authority，但本节点不重新执行 rule match。
- `completion_path = accountant_corrected_review_path` 时，必须有明确 accountant correction ref。
- `reprocessing_context` 存在时，必须进入 duplication / supersession validation；不得并列写出互相冲突 case。

Runtime-only vs durable references：

该对象是 runtime validation basis。它可以引用 durable finalization / audit records，但不把 Transaction Log 改造成 learning layer。

### 3.3 `learning_authority_context`

Purpose：明确当前 request 最多允许本节点做什么，防止把未批准或 candidate-only 内容写成 durable case。

Source authority：active product spec、Review / Intervention authority、finalization boundary、governance restriction、entity / rule policy 和 workflow orchestration 的 deterministic validation。

Required fields：

| Field | Meaning | Source authority | Runtime / durable |
| --- | --- | --- | --- |
| `learning_authority_status` | 是否允许写 completed case | workflow authority validation | runtime |
| `authority_source` | 为什么有或没有学习 authority | review / finalization / policy | runtime summary with durable refs |
| `authority_refs` | 支撑 authority 的 refs | Review / Intervention / Governance / finalization records | durable refs |
| `hard_blocks` | 阻止 case write 的 hard blocks | upstream / governance / validation | runtime list |
| `candidate_handoff_allowed` | 是否允许输出 candidate signals | workflow / policy authority | runtime |

Allowed `learning_authority_status` values：

- `eligible_for_case_write`
- `candidate_handoff_only`
- `blocked_pending_or_review_required`
- `blocked_not_finalized`
- `blocked_authority_conflict`
- `blocked_traceability_gap`
- `invalid_authority_claim`

Allowed `authority_source` values：

- `explicit_accountant_approval`
- `explicit_accountant_correction`
- `approved_rule_finalization`
- `structural_finalization`
- `case_supported_finalization`
- `manual_finalization`
- `equivalent_finalization_boundary`
- `none`

Optional fields：

- `accountant_actor_ref`：如果 authority 来自 accountant action。
- `review_decision_ref`：review package / decision item ref。
- `governance_refs`：影响学习 authority 的 governance refs。
- `authority_notes`：简短说明；不能替代 refs。

Validation / rejection rules：

- `learning_authority_status = eligible_for_case_write` 时，`authority_source` 不能是 `none`，`authority_refs` 不能为空。
- 有 `hard_blocks` 时不能写 Case Log，除非 block 只影响长期治理候选且不影响当前 completed outcome authority；这种区分必须在 `hard_blocks` 或 `authority_notes` 中明确。
- accountant silence、bulk acknowledgement、模糊自然语言、system confidence 或 runtime recommendation 不能成为 `explicit_accountant_approval`。
- `candidate_handoff_only` 可以输出 candidate signals，但不得输出 `case_log_record`。

Runtime-only vs durable references：

该对象是 runtime authority envelope。它引用 durable review/governance/finalization records，但本身不是 durable approval record。

### 3.4 `final_outcome_context`

Purpose：描述当前交易最终怎样处理，供 `Case Log` 保存未来 case precedent。

Source authority：Profile / Structural Match、Rule Match、Case Judgment 后续 finalization、Review Node、accountant correction 或 manual finalization handoff。

Required fields：

| Field | Meaning | Source authority | Runtime / durable |
| --- | --- | --- | --- |
| `transaction_id` | 稳定交易 ID | Transaction Identity Node | durable reference |
| `outcome_type` | 最终 outcome 类型 | upstream / review / finalization | runtime enum |
| `accounting_outcome` | 最终分类 / structural treatment / correction payload | upstream approved result / accountant correction | durable outcome candidate for case |
| `outcome_authority` | outcome 的 authority 来源 | upstream / review / rule / accountant | runtime with durable refs |
| `outcome_rationale_refs` | 支撑 outcome 的 rationale refs | upstream rationale / review / intervention | durable refs where persisted |

Allowed `outcome_type` values：

- `structural_result`
- `approved_rule_result`
- `case_supported_result`
- `accountant_approved_result`
- `accountant_corrected_result`
- `manual_result`

Optional fields：

- `classification_basis`：例如 structural、approved rule、case-supported、accountant correction。
- `coa_account_ref`：最终使用的 COA account reference；source authority 属于 upstream approved result / accountant correction。
- `hst_gst_treatment`：最终 tax treatment；source authority 属于 upstream approved result / accountant correction。
- `amount_allocation`：如有 split / allocation 的最终摘要；完整 JE schema 不在本节点定义。
- `case_refs_used`：如果 outcome 由 case-supported path 形成。
- `rule_ref_used`：如果 outcome 由 approved rule path 形成。
- `exception_summary`：与未来案例有关的例外语境。

Validation / rejection rules：

- `accounting_outcome` 不能为空；但本 Stage 不冻结共享 accounting schema。
- `coa_account_ref`、`hst_gst_treatment` 如存在，本节点只能复制为 case context，不能修正。
- `approved_rule_result` 必须引用 approved active rule；pending / rejected rule 不能支持 final outcome。
- `case_supported_result` 必须已越过后续 finalization / review boundary；不能把 Case Judgment runtime proposal 直接写成 final outcome。
- `accountant_corrected_result` 必须有明确 correction binding ref。

Runtime-only vs durable references：

`final_outcome_context` 是 case write source。写入 Case Log 后，final outcome 可成为 future case precedent；但它不能自动变成 Rule Log、Entity Log、Profile 或 Governance authority。

### 3.5 `evidence_context`

Purpose：绑定支撑 case precedent 的客观证据和证据强度，避免自然语言摘要脱离 evidence。

Source authority：Evidence Log、Evidence Intake / Preprocessing、receipt / cheque parser、upstream rationale、Review / Intervention context。

Required fields：

| Field | Meaning | Source authority | Runtime / durable |
| --- | --- | --- | --- |
| `evidence_refs` | 支撑当前 completed outcome 的 evidence references | Evidence Log | durable refs |
| `evidence_sufficiency_status` | evidence 是否足够支持 case write | upstream validation / review | runtime |
| `evidence_summary` | 对未来 case judgment 有用的证据摘要 | deterministic packaging / LLM summary within bounds | runtime summary |

Allowed `evidence_sufficiency_status` values：

- `sufficient_for_case_write`
- `limited_but_authorized`
- `insufficient_for_case_write`
- `conflicting_evidence`
- `unbound_evidence`

Optional fields：

- `raw_description_ref`
- `receipt_refs`
- `cheque_info_refs`
- `accountant_context_refs`
- `evidence_limitations`
- `evidence_exception_notes`

Validation / rejection rules：

- `evidence_refs` 不能为空，除非 `learning_authority_context` 明确允许 `limited_but_authorized` 且有 authority ref。
- `conflicting_evidence` 或 `unbound_evidence` 不能写正常 case。
- `evidence_summary` 不能只有“模型认为相似”；必须绑定 evidence refs 或明确 evidence limitations。

Runtime-only vs durable references：

Evidence 原文留在 Evidence Log；Case Log 应保存 evidence refs 和必要摘要，不复制或覆盖原始证据。

### 3.6 `entity_identity_context`

Purpose：记录当前 completed transaction 当时的 entity / alias / role / identity 状态，供未来 case judgment 理解 case 适用范围，同时保护 entity governance 边界。

Source authority：Entity Resolution Node、Entity Log、Review / Intervention correction、Governance Log。

Required fields：

| Field | Meaning | Source authority | Runtime / durable |
| --- | --- | --- | --- |
| `entity_resolution_status` | 当前交易完成时的 entity 状态 | Entity Resolution / review context | runtime state |
| `identity_case_binding_status` | 该 identity context 是否可作为 case context 保存 | workflow validation | runtime |
| `identity_summary` | 未来理解该 case 所需的身份说明 | upstream / review / LLM summary within bounds | runtime summary |

Allowed `entity_resolution_status` values：

- `resolved_entity`
- `resolved_entity_with_unconfirmed_role`
- `new_entity_candidate`
- `ambiguous_entity_candidates`
- `unresolved`

Allowed `identity_case_binding_status` values：

- `stable_entity_context`
- `candidate_entity_context`
- `identity_resolved_by_review`
- `identity_limited_case_context`
- `identity_conflict_blocks_case_write`

Optional fields：

- `entity_id`：仅在 stable entity 安全识别时填写。
- `display_name_snapshot`：case 当时显示名称快照。
- `matched_alias`
- `alias_status`；allowed values: `candidate_alias`, `approved_alias`, `rejected_alias`。
- `confirmed_role_refs`
- `candidate_role`
- `candidate_entities`
- `identity_risk_flags`
- `related_governance_refs`

Validation / rejection rules：

- `entity_resolution_status = resolved_entity` 时，`entity_id` 必须引用 stable entity authority。
- `new_entity_candidate` 可以写入 Case Log 的 candidate identity context，但不得携带 stable `entity_id` authority，也不得支持 rule promotion。
- `candidate_role` 只能作为当前 case context 或 candidate signal，不能写入 stable Entity Log role。
- `alias_status = candidate_alias` 可作为 case context，但不能被写成 approved alias。
- `alias_status = rejected_alias` 如仍影响当前 outcome safety，应 block case write 或输出 consistency issue。
- `identity_case_binding_status = identity_conflict_blocks_case_write` 时不能写正常 case。

Runtime-only vs durable references：

Stable `entity_id` / approved alias / confirmed role 的 source of truth 是 Entity Log / Governance-approved state。Case Log 可以记录当时引用和候选语境，但本节点不能修改 stable entity memory。

### 3.7 `traceability_context`

Purpose：证明 case record 中的 transaction、outcome、evidence、review/correction、JE/finalization 和 candidate signals 可以相互绑定。

Source authority：workflow orchestration、Evidence Log、Transaction Identity、Review / Intervention records、JE / finalization records、Transaction Log 或等价 finalization handoff。

Required fields：

| Field | Meaning | Source authority | Runtime / durable |
| --- | --- | --- | --- |
| `binding_status` | 关键 refs 是否绑定到同一 transaction / case subject | workflow validation | runtime |
| `required_ref_checks` | 必须通过的 ref 检查结果 | deterministic validation | runtime |
| `missing_or_conflicting_refs` | 缺失或冲突 refs | deterministic validation | runtime |

Allowed `binding_status` values：

- `all_required_refs_bound`
- `non_blocking_refs_missing`
- `blocking_refs_missing`
- `conflicting_refs`

Optional fields：

- `transaction_log_ref_check`
- `review_ref_check`
- `intervention_ref_check`
- `evidence_ref_check`
- `je_ref_check`
- `prior_case_duplication_check`
- `governance_ref_check`

Validation / rejection rules：

- `binding_status = blocking_refs_missing` 或 `conflicting_refs` 时不能写 normal case。
- `non_blocking_refs_missing` 只有在缺失项不影响 completed outcome authority 和 evidence traceability 时才可继续，并必须记录 limitation。
- prior duplicate / reprocessing / correction risk 不能被自然语言摘要绕过。

Runtime-only vs durable references：

该对象是 runtime validation envelope。通过验证不等于批准任何长期 governance change。

### 3.8 `candidate_signal_inputs`

Purpose：承接上游已经产生的 memory / governance / lint 候选信号，供本节点决定是否随 completed case 一起转交。

Source authority：Entity Resolution、Rule Match、Case Judgment、Coordinator / Pending、Review Node、Post-Batch Lint context 或 accountant correction 中暴露的 candidate signal。

Required fields for each signal：

| Field | Meaning | Source authority | Runtime / durable |
| --- | --- | --- | --- |
| `signal_id` | 候选信号标识 | upstream workflow | runtime / candidate ref |
| `signal_type` | 候选类型 | upstream workflow | runtime enum |
| `subject_refs` | 相关 transaction、entity、alias、role、rule、case、evidence refs | upstream / durable stores | refs |
| `signal_reason` | 为什么形成候选 | upstream rationale / review context | runtime summary |
| `required_authority_path` | 后续需要哪个 authority path | active policy / governance boundary | runtime |

Allowed `signal_type` values：

- `new_entity_candidate`
- `entity_merge_candidate`
- `entity_split_candidate`
- `alias_approval_candidate`
- `alias_rejection_candidate`
- `role_confirmation_candidate`
- `rule_candidate`
- `rule_conflict_candidate`
- `rule_health_candidate`
- `automation_policy_review_candidate`
- `profile_or_tax_config_review_candidate`
- `knowledge_compilation_candidate`
- `post_batch_lint_candidate`
- `case_consistency_issue`

Allowed `required_authority_path` values：

- `case_memory_update_only`
- `review_node`
- `governance_review`
- `post_batch_lint`
- `knowledge_compilation`
- `coordinator_pending`
- `not_eligible`

Optional fields：

- `proposed_candidate_payload`
- `source_node`
- `source_result_ref`
- `related_case_refs`
- `risk_level`

Validation / rejection rules：

- `subject_refs` 不能为空。
- candidate signal 不得声称 approved alias、confirmed role、stable entity、active rule、automation-policy upgrade 或 governance event 已生效。
- `new_entity_candidate` 不得输出 `rule_candidate` / rule promotion support；如有 repeated case signal，只能是治理/体检风险或 future review item。
- `case_allowed_but_no_promotion` context 不得生成 rule promotion candidate，除非 signal 明确表达 no-promotion restriction / risk。

Runtime-only vs durable references：

这些 inputs 是 candidate-only。是否写入 governance queue、lint queue 或其他 durable candidate store 留给下游 owner，不由本节点批准。

## 4. Output Contracts

### 4.1 `case_memory_update_result`

Purpose：表达本节点对 completed transaction 的 case-learning 和 candidate-handoff 结果。

Consumer / downstream authority：workflow orchestrator、Case Judgment future read path、Governance Review、Knowledge Compilation、Post-Batch Lint、Review / Coordinator fallback。下游只能按 output status 和 authority boundary 消费。

Required fields：

| Field | Meaning | Authority |
| --- | --- | --- |
| `request_id` | 对应 input request | runtime reference |
| `transaction_id` | 对应交易 ID | Transaction Identity |
| `result_status` | 本节点结果状态 | Case Memory Update validation |
| `case_write_status` | Case Log 写入状态 | Case Memory Update validation |
| `candidate_handoff_status` | 候选转交状态 | Case Memory Update validation |
| `authority_summary` | 使用的 learning authority 摘要 | input authority context |
| `created_at` | 本节点结果时间 | workflow runtime |

Allowed `result_status` values：

- `case_written`
- `case_written_with_candidate_handoffs`
- `candidate_handoff_only`
- `skipped_duplicate_or_superseded`
- `blocked_not_completed`
- `blocked_authority_gap`
- `blocked_traceability_gap`
- `blocked_conflict`
- `invalid_input`

Allowed `case_write_status` values：

- `written`
- `not_written_candidate_only`
- `not_written_duplicate`
- `not_written_blocked`
- `not_written_invalid`

Allowed `candidate_handoff_status` values：

- `none`
- `candidate_signals_forwarded`
- `candidate_signals_blocked`
- `candidate_signals_not_allowed`

Optional fields：

- `case_log_record`：当 `case_write_status = written` 时 required。
- `candidate_handoffs`：当 candidate signals 被转交时 required。
- `knowledge_compilation_handoff`
- `consistency_issue_signal`
- `blocked_context`
- `runtime_trace`

Validation rules：

- `result_status = case_written` 或 `case_written_with_candidate_handoffs` 时，必须有 `case_log_record`。
- `case_write_status = written` 时，input `learning_authority_status` 必须是 `eligible_for_case_write`。
- output 不能包含 Transaction Log write、Rule Log write、stable Entity Log mutation、Governance approval 或 JE write。
- `candidate_handoff_only` 不能被 downstream 当作 Case Log write。

Memory boundary：

`case_memory_update_result` 本身是 runtime output。只有 `case_log_record` 属于 Case Log durable write payload；candidate handoffs 是 candidate-only。

### 4.2 `case_log_record`

Purpose：写入 `Case Log` 的 completed transaction case，作为未来 Case Judgment 的 case precedent。

Consumer / downstream authority：未来 `Case Judgment Node`、Knowledge Compilation、Post-Batch Lint、Governance Review 可读取。它不支持 deterministic Rule Match。

Required fields：

| Field | Meaning | Authority |
| --- | --- | --- |
| `case_id` | Case Log record ID | Case Log write |
| `client_id` | 客户标识 | input |
| `transaction_id` | 交易 ID | Transaction Identity |
| `case_status` | case 生命周期 / 可用状态 | Case Log |
| `case_authority` | 为什么可作为 case precedent | learning authority context |
| `final_outcome_snapshot` | 完成交易 outcome 快照 | final outcome context |
| `evidence_refs` | 支撑 case 的证据 refs | Evidence Log |
| `evidence_summary` | 对未来判断有用的证据摘要 | evidence context |
| `entity_identity_snapshot` | 当时 entity / identity context | entity_identity_context |
| `review_correction_refs` | approval / correction refs；没有则为空列表 | Review / Intervention |
| `case_precedent_scope` | 未来如何使用该 case 的边界 | Case Memory Update |
| `created_from_transaction_id` | 来源交易 ID | Transaction Identity |
| `created_at` | 写入时间 | Case Log |

Allowed `case_status` values：

- `active_case`
- `limited_authority_case`
- `superseded_case`
- `blocked_from_automation_use`

Allowed `case_authority.authority_type` values：

- `accountant_approved_case`
- `accountant_corrected_case`
- `approved_rule_finalized_case`
- `structural_finalized_case`
- `case_supported_finalized_case`
- `manual_finalized_case`

Allowed `case_precedent_scope.use_level` values：

- `case_judgment_context_only`
- `case_supported_classification_context`
- `exception_context_only`
- `negative_or_conflict_context`

Optional fields：

- `rule_ref_used`
- `case_refs_used`
- `exception_context`
- `risk_flags`
- `amount_context`
- `direction`
- `bank_account_ref`
- `receipt_refs`
- `cheque_info_refs`
- `accountant_notes_summary`
- `candidate_signal_refs`
- `supersedes_case_ids`
- `superseded_by_case_id`
- `limitations`

Validation rules：

- `case_id` 必须唯一。
- `transaction_id` 必须与 input 一致。
- `final_outcome_snapshot` 必须来自 approved / finalized source，不能来自 runtime suggestion。
- `evidence_refs` 必须可追溯到 Evidence Log。
- `review_correction_refs` 中的 accountant action 必须绑定当前 transaction / review item。
- `case_precedent_scope` 不得声称该 case 可支持 deterministic rule match。
- `new_entity_candidate` case 必须设置 `use_level` 为 `case_judgment_context_only`、`exception_context_only` 或更保守语义，且 `limitations` 必须说明不能支持 rule promotion / stable entity authority。

Memory boundary：

这是本节点唯一 durable write payload。它写入 Case Log，但不写入 Transaction Log、Entity Log、Rule Log、Governance Log 或 Profile。

### 4.3 `entity_identity_snapshot`

Purpose：作为 `case_log_record` 子对象，记录 case 当时指向谁或候选谁，而不是批准 entity memory。

Required fields：

| Field | Meaning | Authority |
| --- | --- | --- |
| `entity_resolution_status` | 当时识别状态 | Entity Resolution / review |
| `identity_case_binding_status` | case 对身份的绑定质量 | validation |
| `identity_summary` | 可读身份说明 | bounded summary |

Optional fields：

- `entity_id`
- `display_name_snapshot`
- `matched_alias`
- `alias_status`
- `confirmed_role_refs`
- `candidate_role`
- `candidate_entities`
- `identity_risk_flags`
- `related_governance_refs`

Validation rules：

- `entity_id` 只能在 stable entity authority 存在时出现。
- `alias_status = candidate_alias` 不得被重写为 approved。
- `candidate_role` 不得进入 stable roles。
- `new_entity_candidate` 不得声称 `entity_id` 是 stable authority。

Memory boundary：

该 snapshot 是 case context，不是 Entity Log mutation。

### 4.4 `candidate_handoff`

Purpose：把完成交易暴露出的长期 memory / governance / lint 信号转交给 owner workflow。

Consumer / downstream authority：Governance Review、Post-Batch Lint、Knowledge Compilation、Review、Coordinator。candidate handoff 不是 approval。

Required fields：

| Field | Meaning | Authority |
| --- | --- | --- |
| `handoff_id` | candidate handoff 标识 | workflow runtime |
| `transaction_id` | 来源交易 | Transaction Identity |
| `candidate_type` | 候选类型 | Case Memory Update packaging |
| `subject_refs` | 相关 transaction/entity/alias/role/rule/case/evidence refs | upstream / durable refs |
| `candidate_reason` | 为什么转交 | upstream + Case Memory Update summary |
| `required_authority_path` | 后续 owner / authority path | active policy boundary |
| `candidate_status` | 当前候选状态 | Case Memory Update output |

Allowed `candidate_type` values：

- `new_entity_candidate`
- `entity_merge_candidate`
- `entity_split_candidate`
- `alias_approval_candidate`
- `alias_rejection_candidate`
- `role_confirmation_candidate`
- `rule_candidate`
- `rule_conflict_candidate`
- `rule_health_candidate`
- `automation_policy_review_candidate`
- `profile_or_tax_config_review_candidate`
- `knowledge_compilation_candidate`
- `post_batch_lint_candidate`
- `case_consistency_issue`

Allowed `required_authority_path` values：

- `governance_review`
- `post_batch_lint`
- `knowledge_compilation`
- `review_node`
- `coordinator_pending`
- `not_eligible`

Allowed `candidate_status` values：

- `proposed_candidate`
- `forwarded_candidate`
- `blocked_candidate`
- `not_eligible_candidate`

Optional fields：

- `case_id`
- `source_signal_ids`
- `proposed_candidate_payload`
- `risk_level`
- `blocking_reason`
- `related_governance_refs`

Validation rules：

- `subject_refs` 不能为空。
- `required_authority_path = governance_review` 的 candidate 不得被标记为 approved / applied。
- `candidate_type = rule_candidate` 时不得来自 `new_entity_candidate` 或 `case_allowed_but_no_promotion` context，除非明确是 no-promotion / rule-risk signal。
- `automation_policy_review_candidate` 不得改变 automation policy；升级或放宽必须 accountant / governance approval。

Memory boundary：

Candidate handoff 是 candidate-only output。它不写 stable memory，不创建 active rule，不批准 governance event。

### 4.5 `knowledge_compilation_handoff`

Purpose：提示 `Knowledge Compilation Node` 后续可以基于新 case 或候选变化重新编译客户知识摘要。

Required fields：

| Field | Meaning | Authority |
| --- | --- | --- |
| `handoff_id` | handoff 标识 | workflow runtime |
| `trigger_refs` | 触发编译的 case / candidate refs | Case Log / candidate handoffs |
| `compilation_reason` | 为什么需要更新摘要 | Case Memory Update |

Allowed `compilation_reason` values：

- `new_case_added`
- `case_exception_added`
- `case_correction_added`
- `entity_or_rule_candidate_added`
- `consistency_issue_detected`

Optional fields：

- `suggested_summary_focus`
- `affected_entity_ids`
- `affected_case_ids`

Validation rules：

- 该 handoff 不能包含已编译 knowledge summary。
- 不能声明 summary 已成为 deterministic rule source。

Memory boundary：

Runtime/candidate handoff only。Knowledge Log / Summary Log 的写入属于 Knowledge Compilation Node。

### 4.6 `blocked_context`

Purpose：当本节点不能写 case 或不能转交 candidate 时，说明阻断原因和安全回退方向。

Required fields：

| Field | Meaning | Authority |
| --- | --- | --- |
| `blocked_reason` | 阻断原因 | validation |
| `blocking_refs` | 相关 refs | upstream / durable refs |
| `suggested_return_path` | 建议回到哪个 workflow | Case Memory Update validation |

Allowed `blocked_reason` values：

- `transaction_not_completed`
- `learning_authority_missing`
- `accountant_approval_missing`
- `accountant_correction_ambiguous`
- `traceability_gap`
- `evidence_insufficient_or_conflicting`
- `identity_conflict`
- `governance_block`
- `duplicate_or_supersession_unresolved`
- `invalid_input_contract`
- `candidate_handoff_not_allowed`

Allowed `suggested_return_path` values：

- `review_node`
- `coordinator_pending`
- `transaction_logging_or_finalization`
- `evidence_reprocessing`
- `governance_review`
- `post_batch_lint`
- `manual_investigation`

Optional fields：

- `blocking_summary`
- `missing_fields`
- `conflicting_field_refs`
- `candidate_preservation_note`

Validation rules：

- blocked output must not include `case_log_record`.
- blocked output must not silently drop candidate signals if preserving them is authority-safe; if dropped, explain why.

Memory boundary：

Runtime-only. It does not write Case Log or durable governance memory.

## 5. Field Authority and Memory Boundary

### 5.1 Source of truth for important fields

- `transaction_id`：Transaction Identity Node / transaction identity layer。
- raw evidence、receipt、cheque、accountant context refs：Evidence Log / Intervention Log。
- final accounting outcome：upstream finalized result、explicit accountant approval / correction、approved rule finalization、structural finalization 或 equivalent finalization boundary。
- `coa_account_ref`、`hst_gst_treatment`、amount allocation：上游 approved result / accountant correction / finalization authority；本节点只保存快照。
- `entity_id`、approved alias、confirmed role、entity status、automation policy：Entity Log + approved Governance authority。
- approved active rule：Rule Log + accountant / governance approval。
- governance restriction / event status：Governance Log。
- case precedent：Case Log，由本节点在 authority 合格时写入。
- Transaction Log：audit-facing final log，只写和查询，不参与 runtime decision，也不是 learning layer。

### 5.2 Fields that can never become durable memory by this node

本节点绝不能把以下内容写成长期 authority：

- stable entity creation / approval
- alias approval or rejection
- role confirmation
- entity merge / split / archive / reactivate
- active rule creation / promotion / modification / deletion / downgrade
- automation policy upgrade / relaxation / durable change
- Profile / tax config / account mapping mutation
- JE lines or final accounting computation
- Transaction Log entry
- Governance approval event
- LLM prompt trace、model confidence、candidate-only rationale

### 5.3 Fields that can become durable only after accountant / governance approval

以下内容可以由本节点提出候选，但必须经后续 authority path 才能成为长期 memory：

- `new_entity_candidate` → stable entity：Governance Review / approved entity governance。
- `alias_approval_candidate` / `alias_rejection_candidate` → approved / rejected alias：Governance Review / accountant approval。
- `role_confirmation_candidate` → confirmed role：Governance Review / accountant approval。
- `rule_candidate` / `rule_conflict_candidate` → active rule or rule change：Governance Review / accountant approval。
- `automation_policy_review_candidate` → automation policy change：governance workflow；升级或放宽必须 accountant approval。
- profile / tax config / account mapping review candidate → Profile durable change：appropriate review/governance owner。

### 5.4 Audit vs learning / logging boundary

`Transaction Log` 记录 final处理结果和审计轨迹；本节点可以读取它或等价 finalization handoff 来验证完成状态，但不能把 Transaction Log 当作未来 runtime learning source。

`Case Log` 是学习层，保存 completed transaction case precedent。它可被未来 Case Judgment 读取，但不能被 Rule Match 当作 deterministic rule source。

Candidate handoff 是治理/体检/编译输入，不是 durable approval。

## 6. Validation Rules

### 6.1 Contract-level validation rules

- 每个 request 必须绑定一个稳定 `transaction_id`。
- Case write 必须同时满足 completed transaction、learning authority、final outcome、evidence traceability、identity binding 和 duplication/supersession safety。
- 本节点只能写 `Case Log`；任何 Entity / Rule / Governance / Profile / Transaction Log mutation 字段都使 output invalid。
- `new_entity_candidate` 可以形成 case context 和 candidate handoff，但不能支持 rule match、rule promotion 或 stable entity authority。
- `candidate_alias`、`candidate_role` 只能作为 candidate/context，不能变成 approved alias / confirmed role。
- `Transaction Log` refs 只能用于 audit/finalization proof，不能作为 future runtime decision source。

### 6.2 Conditions that make input invalid

- 缺少 `transaction_id`、`learning_authority_context`、`final_outcome_context`、`evidence_context` 或 `traceability_context`。
- 当前交易仍 pending、review-required、not-approved、JE-blocked、not-finalized、identity unresolved in a blocking way、evidence conflicting 或 governance-blocked。
- outcome 只是 Case Judgment / LLM runtime proposal，没有 finalization authority。
- accountant response 未绑定当前交易或语义模糊，却被包装成 approval / correction。
- evidence refs 缺失、不可追溯或与 outcome 冲突。
- reprocessing / correction / duplicate risk 未解决。
- input 声称本节点应写 Rule Log、Entity Log、Governance Log、Profile、Transaction Log 或 JE。

### 6.3 Conditions that make output invalid

- `case_write_status = written` 但没有 `case_log_record`。
- `case_log_record.final_outcome_snapshot` 来自 runtime suggestion 或 candidate signal。
- `case_log_record.case_precedent_scope` 声称可以支持 deterministic rule match。
- candidate handoff 声称 approved / confirmed / promoted / applied。
- `new_entity_candidate` case 或 candidate 声称有 stable entity authority 或 rule promotion support。
- output 包含 Transaction Log write、Rule Log write、stable Entity Log mutation、Governance approval、Profile mutation 或 JE generation result。
- blocked output 同时包含正常 `case_log_record`。

### 6.4 Stop / ask conditions for unresolved contract authority

后续 Stage 或实现中如遇到以下问题，应 stop and ask，不得自行补 product authority：

- 需要决定哪些 high-confidence non-review outcomes 可直接获得 `eligible_for_case_write`。
- 需要冻结 shared `accounting_outcome` / JE-ready schema。
- 需要定义 durable candidate queue / governance event storage schema。
- 需要决定 duplicate / reprocessed / corrected / reversed / split transaction 的 exact supersession behavior。
- 需要允许本节点修改 Entity Log、Rule Log、Governance Log、Profile 或 Transaction Log。
- 需要改变 `Transaction Log` 不参与 runtime decision / learning 的边界。

## 7. Examples

### 7.1 Valid minimal example

```json
{
  "case_memory_update_request": {
    "request_id": "cmu_req_001",
    "client_id": "client_acme",
    "batch_id": "batch_2026_05",
    "transaction_id": "txn_01HZXCMU0001",
    "completed_transaction_basis": {
      "transaction_id": "txn_01HZXCMU0001",
      "completion_status": "completed_logged",
      "completion_path": "accountant_approved_review_path",
      "finalization_refs": ["txnlog_001", "review_decision_001"],
      "completed_at": "2026-05-06T09:10:00Z"
    },
    "learning_authority_context": {
      "learning_authority_status": "eligible_for_case_write",
      "authority_source": "explicit_accountant_approval",
      "authority_refs": ["review_decision_001"],
      "hard_blocks": [],
      "candidate_handoff_allowed": true
    },
    "final_outcome_context": {
      "transaction_id": "txn_01HZXCMU0001",
      "outcome_type": "accountant_approved_result",
      "accounting_outcome": {
        "coa_account_ref": "coa_meals",
        "hst_gst_treatment": "itc_eligible"
      },
      "outcome_authority": "explicit_accountant_approval",
      "outcome_rationale_refs": ["review_decision_001"]
    },
    "evidence_context": {
      "evidence_refs": ["ev_bank_001", "ev_receipt_001"],
      "evidence_sufficiency_status": "sufficient_for_case_write",
      "evidence_summary": "receipt supports business meal context"
    },
    "entity_identity_context": {
      "entity_resolution_status": "resolved_entity",
      "identity_case_binding_status": "stable_entity_context",
      "entity_id": "ent_tim_hortons",
      "matched_alias": "TIM HORTONS #1234",
      "alias_status": "approved_alias",
      "identity_summary": "approved alias bound to active Tim Hortons entity"
    },
    "traceability_context": {
      "binding_status": "all_required_refs_bound",
      "required_ref_checks": ["transaction", "evidence", "review", "final_log"],
      "missing_or_conflicting_refs": []
    }
  },
  "case_memory_update_result": {
    "request_id": "cmu_req_001",
    "transaction_id": "txn_01HZXCMU0001",
    "result_status": "case_written",
    "case_write_status": "written",
    "candidate_handoff_status": "none",
    "authority_summary": "explicit accountant approval after review",
    "case_log_record": {
      "case_id": "case_001",
      "client_id": "client_acme",
      "transaction_id": "txn_01HZXCMU0001",
      "case_status": "active_case",
      "case_authority": {
        "authority_type": "accountant_approved_case",
        "authority_refs": ["review_decision_001"]
      },
      "final_outcome_snapshot": {
        "coa_account_ref": "coa_meals",
        "hst_gst_treatment": "itc_eligible"
      },
      "evidence_refs": ["ev_bank_001", "ev_receipt_001"],
      "evidence_summary": "receipt supports business meal context",
      "entity_identity_snapshot": {
        "entity_resolution_status": "resolved_entity",
        "identity_case_binding_status": "stable_entity_context",
        "entity_id": "ent_tim_hortons",
        "matched_alias": "TIM HORTONS #1234",
        "alias_status": "approved_alias",
        "identity_summary": "approved alias bound to active entity"
      },
      "review_correction_refs": ["review_decision_001"],
      "case_precedent_scope": {
        "use_level": "case_supported_classification_context"
      },
      "created_from_transaction_id": "txn_01HZXCMU0001",
      "created_at": "2026-05-06T09:11:00Z"
    },
    "created_at": "2026-05-06T09:11:00Z"
  }
}
```

### 7.2 Valid richer example with new entity candidate

```json
{
  "case_memory_update_request": {
    "request_id": "cmu_req_002",
    "client_id": "client_acme",
    "batch_id": "batch_2026_05",
    "transaction_id": "txn_01HZXCMU0002",
    "completed_transaction_basis": {
      "transaction_id": "txn_01HZXCMU0002",
      "completion_status": "completed_with_equivalent_finalization",
      "completion_path": "accountant_corrected_review_path",
      "finalization_refs": ["review_decision_002", "je_002"],
      "completed_at": "2026-05-06T10:00:00Z"
    },
    "learning_authority_context": {
      "learning_authority_status": "eligible_for_case_write",
      "authority_source": "explicit_accountant_correction",
      "authority_refs": ["review_decision_002"],
      "hard_blocks": [],
      "candidate_handoff_allowed": true
    },
    "final_outcome_context": {
      "transaction_id": "txn_01HZXCMU0002",
      "outcome_type": "accountant_corrected_result",
      "accounting_outcome": {
        "coa_account_ref": "coa_software",
        "hst_gst_treatment": "itc_eligible"
      },
      "outcome_authority": "explicit_accountant_correction",
      "outcome_rationale_refs": ["review_decision_002"]
    },
    "evidence_context": {
      "evidence_refs": ["ev_bank_002", "ev_invoice_002"],
      "evidence_sufficiency_status": "sufficient_for_case_write",
      "evidence_summary": "invoice identifies a new SaaS vendor and business subscription"
    },
    "entity_identity_context": {
      "entity_resolution_status": "new_entity_candidate",
      "identity_case_binding_status": "candidate_entity_context",
      "matched_alias": "NEW SAAS INC",
      "alias_status": "candidate_alias",
      "candidate_role": "software_vendor",
      "identity_summary": "current evidence supports a new vendor candidate, not stable entity authority"
    },
    "traceability_context": {
      "binding_status": "all_required_refs_bound",
      "required_ref_checks": ["transaction", "evidence", "review", "je"],
      "missing_or_conflicting_refs": []
    },
    "candidate_signal_inputs": [
      {
        "signal_id": "sig_new_entity_002",
        "signal_type": "new_entity_candidate",
        "subject_refs": ["txn_01HZXCMU0002", "ev_invoice_002"],
        "signal_reason": "new vendor identified by invoice and accountant correction",
        "required_authority_path": "governance_review"
      }
    ]
  },
  "case_memory_update_result": {
    "request_id": "cmu_req_002",
    "transaction_id": "txn_01HZXCMU0002",
    "result_status": "case_written_with_candidate_handoffs",
    "case_write_status": "written",
    "candidate_handoff_status": "candidate_signals_forwarded",
    "authority_summary": "explicit accountant correction allows case write; entity remains candidate-only",
    "case_log_record": {
      "case_id": "case_002",
      "client_id": "client_acme",
      "transaction_id": "txn_01HZXCMU0002",
      "case_status": "limited_authority_case",
      "case_authority": {
        "authority_type": "accountant_corrected_case",
        "authority_refs": ["review_decision_002"]
      },
      "final_outcome_snapshot": {
        "coa_account_ref": "coa_software",
        "hst_gst_treatment": "itc_eligible"
      },
      "evidence_refs": ["ev_bank_002", "ev_invoice_002"],
      "evidence_summary": "invoice identifies business SaaS subscription",
      "entity_identity_snapshot": {
        "entity_resolution_status": "new_entity_candidate",
        "identity_case_binding_status": "candidate_entity_context",
        "matched_alias": "NEW SAAS INC",
        "alias_status": "candidate_alias",
        "candidate_role": "software_vendor",
        "identity_summary": "candidate entity only"
      },
      "review_correction_refs": ["review_decision_002"],
      "case_precedent_scope": {
        "use_level": "case_judgment_context_only"
      },
      "limitations": [
        "does not create stable entity",
        "does not support rule promotion"
      ],
      "created_from_transaction_id": "txn_01HZXCMU0002",
      "created_at": "2026-05-06T10:01:00Z"
    },
    "candidate_handoffs": [
      {
        "handoff_id": "handoff_new_entity_002",
        "transaction_id": "txn_01HZXCMU0002",
        "candidate_type": "new_entity_candidate",
        "subject_refs": ["txn_01HZXCMU0002", "case_002", "ev_invoice_002"],
        "candidate_reason": "completed case contains a new vendor candidate",
        "required_authority_path": "governance_review",
        "candidate_status": "forwarded_candidate"
      }
    ],
    "created_at": "2026-05-06T10:01:00Z"
  }
}
```

### 7.3 Invalid example with reason

```json
{
  "case_memory_update_request": {
    "request_id": "cmu_req_bad_001",
    "client_id": "client_acme",
    "batch_id": "batch_2026_05",
    "transaction_id": "txn_01HZXCMU_BAD",
    "completed_transaction_basis": {
      "transaction_id": "txn_01HZXCMU_BAD",
      "completion_status": "blocked_not_completed",
      "completion_path": "case_supported_path",
      "finalization_refs": [],
      "completed_at": null
    },
    "learning_authority_context": {
      "learning_authority_status": "eligible_for_case_write",
      "authority_source": "none",
      "authority_refs": [],
      "hard_blocks": ["review_required"],
      "candidate_handoff_allowed": true
    },
    "final_outcome_context": {
      "transaction_id": "txn_01HZXCMU_BAD",
      "outcome_type": "case_supported_result",
      "accounting_outcome": {
        "coa_account_ref": "coa_materials"
      },
      "outcome_authority": "runtime_llm_recommendation",
      "outcome_rationale_refs": []
    },
    "evidence_context": {
      "evidence_refs": [],
      "evidence_sufficiency_status": "insufficient_for_case_write",
      "evidence_summary": "model thinks this looks like prior cases"
    },
    "entity_identity_context": {
      "entity_resolution_status": "new_entity_candidate",
      "identity_case_binding_status": "candidate_entity_context",
      "entity_id": "ent_auto_created_bad",
      "alias_status": "candidate_alias",
      "identity_summary": "new entity auto-created"
    },
    "traceability_context": {
      "binding_status": "blocking_refs_missing",
      "required_ref_checks": ["transaction"],
      "missing_or_conflicting_refs": ["evidence", "review", "finalization"]
    }
  }
}
```

Invalid reasons：

- `completion_status = blocked_not_completed`，不能写 Case Log。
- `learning_authority_status` 声称 eligible，但 `authority_source = none`、`authority_refs` 为空且存在 hard block。
- `outcome_authority` 是 runtime recommendation，不是 final outcome authority。
- evidence refs 缺失且 evidence insufficient。
- `new_entity_candidate` 错误携带 stable-looking `entity_id`。
- traceability 有 blocking refs missing。

## 8. Open Contract Boundaries

以下问题未被 live docs 完全冻结，但不阻塞本 Stage 3，因为本文件用 conservative authority envelope 把它们隔离为上游/后续决策：

- `completed-transaction learning authority` 的 exact upstream granting rule：哪些 high-confidence structural / rule / case-supported outcomes 可不经逐笔 accountant review 直接 `eligible_for_case_write`。
- Case Memory Update 与 final `Transaction Log` 的 exact trigger order：必须严格后置于 Transaction Logging Node，还是可以消费等价 finalization handoff。
- shared `accounting_outcome` / `final_outcome_snapshot` 的全局字段结构，尤其 COA、HST/GST、split、allocation 与 JE-ready payload 的边界。
- duplicate / reprocessed / corrected / reversed / split transaction 的 exact Case Log supersession behavior。
- candidate handoff 是否写入独立 durable queue、Governance Log pending event、Review package，或只作为 workflow handoff。
- case-to-rule candidate 的 primary owner：本节点可以提出保守候选，但 Post-Batch Lint / Governance Review 的分工还未完全冻结。
- `case_allowed_but_no_promotion` 下 rule-related signal 的 exact allowed shape：本文件只允许 no-promotion / risk signal，不允许 promotion candidate。

## 9. Self-Review

- 已读取 required repo docs：`AGENTS.md`、`TASK_STATE.md`、`PLANS.md`、`CLAUDE.md`、`DECISIONS.md`、`supporting documents/communication_preferences.md`、`supporting documents/development_workflow.md`、`supporting documents/node_design_roadmap.md`、`new system/new_system.md`。
- 已读取本节点 prior approved docs：Stage 1 functional intent 与 Stage 2 logic and boundaries。
- 已读取可用 Superpowers docs：`using-superpowers/SKILL.md`、`brainstorming/SKILL.md`；project workflow skill `ai-bookkeeper-node-design-facilitation` 在当前环境不存在，因此按 runner instruction 使用 repo `supporting documents/node_design_roadmap.md` 与本节点 Stage 1/2 docs 作为 workflow authority。
- 已注意 optional reading absence：`supporting documents/node_design_roadmap_zh.md` 不存在，未臆造。
- 本文件保持 Stage 3 data contract 范围，没有进入 Stage 4 execution algorithm、Stage 5 implementation map、Stage 6 test matrix、Stage 7 coding-agent task contract。
- 未引入 unsupported product authority；未把 `Transaction Log` 改成 learning/runtime decision source。
- 未把 candidate entity / alias / role / rule / automation-policy 写成 durable authority。
- 只写入目标文件：`new system/node_stage_designs/case_memory_update_node__stage_3__data_contract.md`。
