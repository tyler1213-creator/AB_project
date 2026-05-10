# Post-Batch Lint Node — Stage 3：Data Contract Spec

## 1. Stage 范围

本 Stage 3 只定义 `Post-Batch Lint Node` 的 implementation-facing data contracts。

前置依据：

- `new system/node_stage_designs/post_batch_lint_node__stage_1__functional_intent.md`
- `new system/node_stage_designs/post_batch_lint_node__stage_2__logic_and_boundaries.md`
- active baseline：`new system/new_system.md`

本文件把 Stage 1/2 已确定的 post-batch automation-health、governance-signal、candidate-only、limited automation-policy downgrade 和 memory/log 边界转换为输入对象、输出对象、字段含义、字段 authority、runtime-only / durable-memory 边界、validation rules 和紧凑示例。

本阶段不定义：

- step-by-step execution algorithm 或 branch sequence
- 技术实现路径、repo module、class、API、storage engine、DB migration 或 code file layout
- test matrix、fixture plan 或 coding-agent task contract
- 新 product authority
- legacy replacement mapping
- `Entity Log`、`Case Log`、`Rule Log`、`Transaction Log`、`Intervention Log`、`Governance Log` 或 `Knowledge Log / Summary Log` 的全局完整 schema
- lint threshold numbers、batch scheduling、retry / timeout 行为

## 2. Contract Position in Workflow

### 2.1 Upstream handoff consumed

本节点消费 `post_batch_lint_request`。

该 request 必须由 workflow orchestration 在 batch-level boundary 形成，表示一个批次已经有足够的完成交易、review / intervention、case、rule、entity、governance 或 knowledge context 可供批后体检。

典型上游语境来自：

- completed batch / audit-history basis
- Case Memory Update Node 的 completed case、candidate signal 或 consistency signal
- Review Node / Intervention Log 的 accountant correction、confirmation、rejection、deferred 或 unresolved context
- Governance Review Node 的 approval、rejection、deferral、restriction、auto-applied downgrade 或 pending governance context
- Entity Log、Rule Log、Case Log、Knowledge Log / Summary Log 的 source-memory context
- Knowledge Compilation Node 暴露的 stale summary、summary mismatch 或 unresolved boundary

本节点不消费单笔交易尚未 finalizable 的 runtime rationale 作为 lint authority。单笔 pending、draft、queue item、candidate-only note、report draft 或未绑定 evidence 的自然语言 warning 不能单独触发 durable conclusion。

### 2.2 Downstream handoff produced

本节点输出 `post_batch_lint_result`。

下游消费者包括：

- `Review Node`：消费 accountant-facing lint finding、batch-level risk summary 和 auto-downgrade visibility item。
- `Governance Review Node`：消费 entity merge / split、alias / role、rule health、case-to-rule、automation-policy 或 unresolved governance candidate。
- `Knowledge Compilation Node`：消费 knowledge follow-up，后续把 unresolved risk、monitoring concern 或治理结果编译进客户知识摘要。
- 未来 `Entity Resolution Node`、`Rule Match Node` 和 `Case Judgment Node`：只能通过已经生效的 durable memory / governance changes 间接受影响，不能读取 raw lint finding 作为 runtime authority。

### 2.3 Logs / memory stores read

本节点可以读取或消费以下 source-memory context：

- `Transaction Log`：finalized audit history、final outcome trace、review / correction trace；只作批次级历史和审计参考，不参与 runtime decision，也不是 learning layer。
- `Intervention Log`：accountant questions、answers、corrections、confirmations、objections、unresolved intervention context。
- `Entity Log`：entity、alias、role、status、authority、risk flags、automation_policy、evidence links。
- `Case Log`：completed cases、final classifications、evidence、exceptions、accountant corrections、review context。
- `Rule Log`：approved active rules、rule lifecycle、rule authority、rule-health context。
- `Governance Log`：approvals、rejections、deferrals、restrictions、auto-applied downgrade history、pending governance context。
- `Knowledge Log / Summary Log`：人和 agent 可读摘要；只能作为辅助背景，不能作为 deterministic rule source。
- `Profile`：与 entity / rule / automation risk 有关的客户结构事实。

### 2.4 Logs / memory stores written or candidate-only

本节点默认输出 runtime handoff 和 candidate signals，不默认创建新的 durable `Log`。

本节点可以 candidate-only 输出：

- entity merge / split candidate
- alias approval / rejection candidate
- role confirmation candidate
- new entity governance candidate
- case-to-rule candidate
- rule conflict / rule instability / stale rule candidate
- automation-policy upgrade / relaxation review candidate
- knowledge compilation follow-up candidate
- unresolved governance risk candidate

本节点唯一在 active baseline 中已知的受限 durable action 是：

- 对 entity `automation_policy` 做风险降低方向的自动降级。

该动作必须通过 governance-event authority path 表达：

- 写出或触发 `entity_governance_event` 语义记录；
- `event_type = change_automation_policy`；
- `source = lint_pass`；
- `requires_accountant_approval = false`；
- `approval_status = auto_applied_downgrade`；
- accountant / governance review 保持可见。

除此之外，本节点不得写入或修改：

- `Transaction Log`
- `Case Log`
- `Rule Log`
- stable `Entity Log` authority
- approved alias / confirmed role / stable entity status
- entity merge / split outcome
- approved governance mutation
- current transaction accounting outcome 或 JE

## 3. Input Contracts

### 3.1 `post_batch_lint_request`

Purpose：本节点的唯一 input envelope，表示一个批次或等价 batch-level context 正在进入 post-batch automation-health check。

Source authority：workflow orchestrator 汇总 batch、audit、review / intervention、entity、case、rule、governance 和 knowledge context。该 envelope 不创造 accountant approval 或 governance authority。

Required fields：

| Field | Meaning | Source authority | Runtime / durable |
| --- | --- | --- | --- |
| `request_id` | 本次 lint request 标识 | workflow runtime | runtime |
| `client_id` | 客户标识 | client context | durable reference |
| `batch_id` | 批次标识 | workflow runtime | runtime / durable batch ref |
| `lint_scope` | 本次体检覆盖范围 | workflow orchestrator | runtime |
| `trigger_reasons` | 为什么触发 post-batch lint | workflow / review / governance / knowledge context | runtime |
| `completed_batch_basis` | completed batch / audit-history basis | finalization workflow / Transaction Log query context | runtime view with durable refs |
| `source_authority_context` | 各 input source 的 authority envelope | durable stores / workflow validation | runtime view over durable authority |

Allowed `lint_scope` values：

- `completed_batch`
- `recent_completed_batches`
- `governance_follow_up_scope`
- `knowledge_mismatch_scope`
- `targeted_entity_or_rule_scope`
- `mixed_batch_scope`

Allowed `trigger_reasons` values：

- `routine_post_batch_check`
- `repeated_review_correction`
- `repeated_intervention_pattern`
- `case_to_rule_signal`
- `entity_consistency_signal`
- `rule_health_signal`
- `automation_policy_risk_signal`
- `governance_follow_up`
- `knowledge_summary_mismatch`
- `accountant_requested_lint`

Optional fields：

| Field | Meaning | Source authority | Runtime / durable |
| --- | --- | --- | --- |
| `entity_consistency_basis` | entity 拆合、alias、role、new entity、automation policy context | Entity Log / entity resolution / case update / review context | durable refs + runtime summary |
| `rule_health_basis` | rule stability、rule conflict、blocked / ineligible context | Rule Log / rule match / review corrections / governance restrictions | durable refs + runtime summary |
| `case_to_rule_basis` | completed cases 是否稳定到可提出 rule 候选 | Case Log / completed transaction context / review corrections | durable refs + runtime summary |
| `review_intervention_basis` | accountant correction、confirmation、rejection、unresolved notes | Intervention Log / Review Node context | durable refs + runtime summary |
| `governance_automation_basis` | governance history、automation policy、auto-downgrade history、pending restrictions | Governance Log / Entity Log / Rule Log | durable refs + runtime summary |
| `knowledge_summary_basis` | stale summary、summary mismatch、unresolved boundary | Knowledge Log / Summary Log + source refs | durable refs + runtime summary |
| `request_trace` | packaging / orchestration trace | workflow runtime | runtime-only |

Validation / rejection rules：

- `request_id`、`client_id`、`batch_id`、`lint_scope`、`trigger_reasons`、`completed_batch_basis`、`source_authority_context` 缺失时，input invalid。
- `trigger_reasons` 必须至少包含一个 allowed value。
- `completed_batch_basis` 必须证明存在 completed transaction、completed review / intervention context、durable memory context 或 governance follow-up context；只有未完成 runtime suggestion 时 input invalid。
- `Transaction Log` 只能作为 finalized audit history 查询语境，不得被声明为 learning source、rule source、runtime decision source 或 governance approval source。
- `request_trace`、draft、queue item、report draft 或自然语言 note 不能替代 source memory refs、evidence refs、review refs 或 governance refs。

Runtime-only vs durable references：

`post_batch_lint_request` 是 runtime-only envelope。它可以引用 durable transaction、entity、case、rule、intervention、governance、knowledge、profile refs，但不因此获得这些 store 的写入权。

### 3.2 `completed_batch_basis`

Purpose：说明本次 lint 分析的 batch-level 历史基础，防止把单笔未完成 runtime context 升级成批后体检。

Source authority：finalization workflow、Transaction Logging Node 的 audit-facing history query、Review / Intervention completion context 或等价 batch closure context。

Required fields：

| Field | Meaning | Source authority | Runtime / durable |
| --- | --- | --- | --- |
| `batch_id` | 批次标识 | workflow runtime | runtime / durable batch ref |
| `batch_completion_status` | 批次是否达到 lint boundary | workflow finalization | runtime |
| `completed_transaction_refs` | 本批次已完成交易 refs | finalization / Transaction Log query context | durable refs |
| `batch_time_window` | 批次或查询窗口 | workflow runtime | runtime metadata |
| `finalization_basis` | 为什么这些交易可作为 completed history | finalization / logging / review context | runtime summary with durable refs |

Allowed `batch_completion_status` values：

- `completed_batch_closed`
- `completed_partial_scope_closed`
- `governance_follow_up_scope_ready`
- `knowledge_mismatch_scope_ready`
- `invalid_not_completed`

Optional fields：

- `final_transaction_log_refs`：Transaction Log refs；audit-facing only。
- `review_decision_refs`：本批次相关 review decision / intervention refs。
- `je_refs`：completed JE refs；本节点不读取 JE line 来重判会计处理。
- `excluded_transaction_refs`：因未完成、pending、invalid 或 out-of-scope 被排除的交易 refs。
- `prior_batch_refs`：近期批次 ref，用于趋势分析；不是无限历史扫描授权。

Validation / rejection rules：

- `batch_completion_status = invalid_not_completed` 时，不得输出 material lint conclusion，只能输出 blocked / invalid result。
- `completed_transaction_refs` 不能为空，除非 `lint_scope` 是 `governance_follow_up_scope` 或 `knowledge_mismatch_scope` 且相关 durable source refs 足够。
- `final_transaction_log_refs` 不能作为 future runtime classification、rule promotion 或 learning authority。
- `excluded_transaction_refs` 中的 pending / not-finalized 交易不能被计入 rule instability、case-to-rule 或 auto-downgrade 依据。

Runtime-only vs durable references：

该对象是 runtime validation basis。它引用 durable audit / review records，但不让 `Transaction Log` 参与运行时决策。

### 3.3 `source_authority_context`

Purpose：明确每类 source memory 在本次 lint 中的 authority，防止 candidate、draft、summary 或 historical audit record 被误用。

Source authority：active product spec、durable memory metadata、governance state、workflow deterministic validation。

Required fields：

| Field | Meaning | Source authority | Runtime / durable |
| --- | --- | --- | --- |
| `source_authority_items` | 按 source category 列出的 authority item | workflow validation | runtime list |
| `candidate_only_sources` | 本次只能作为 candidate signal 的 source refs | source stores / workflow | runtime list with durable refs |
| `durable_authority_sources` | 本次可作为已批准 authority 读取的 source refs | Entity / Rule / Case / Governance / Intervention sources | durable refs |
| `hard_authority_blocks` | 阻止结论或 mutation 的 authority blocks | governance / validation | runtime list |

Required fields inside each `source_authority_item`：

| Field | Meaning | Source authority | Runtime / durable |
| --- | --- | --- | --- |
| `source_category` | source 类型 | workflow validation | runtime enum |
| `source_refs` | 绑定的 durable refs | durable stores | durable refs |
| `authority_state` | 该 source 在本次 lint 中的 authority | durable source metadata / governance | runtime |
| `allowed_use` | 本节点可如何使用该 source | policy / governance boundary | runtime |

Allowed `source_category` values：

- `transaction_audit_history`
- `intervention_history`
- `entity_memory`
- `case_memory`
- `rule_memory`
- `governance_history`
- `knowledge_summary`
- `profile_context`
- `runtime_candidate_signal`

Allowed `authority_state` values：

- `approved_authority`
- `completed_history`
- `accountant_confirmed`
- `candidate_only`
- `rejected`
- `deferred`
- `pending_governance`
- `auto_applied_downgrade`
- `unresolved`
- `conflicting`
- `summary_only`

Allowed `allowed_use` values：

- `audit_context_only`
- `risk_analysis_context`
- `candidate_generation_allowed`
- `governance_candidate_allowed`
- `knowledge_follow_up_allowed`
- `auto_downgrade_basis_allowed`
- `not_authoritative`

Optional fields：

- `authority_notes`：简短说明；不能替代 refs。
- `conflict_refs`：发生 source conflict 时的相关 refs。
- `source_freshness`：source 是否 stale；仅作 validation / risk context。

Validation / rejection rules：

- `source_category = transaction_audit_history` 时，`allowed_use` 不能是 `auto_downgrade_basis_allowed` 的唯一依据，也不能是 rule source / learning source。
- `authority_state = candidate_only`、`rejected`、`deferred`、`unresolved`、`summary_only` 时，不得作为 durable mutation authority。
- `Knowledge Summary` 与 source memory 冲突时，`source_category = knowledge_summary` 必须被标记为 `summary_only` 或 `conflicting`，并只能产生 knowledge follow-up。
- 若 `hard_authority_blocks` 影响 active rule、entity authority、merge/split、alias/role approval 或 automation-policy relaxation，输出必须保持 candidate / review-needed / governance-needed 语义。

Runtime-only vs durable references：

该对象是 runtime authority envelope。它引用 durable source records，但本身不是 durable approval record。

### 3.4 `entity_consistency_basis`

Purpose：提供 entity merge / split、alias、role、new entity、lifecycle status 和 automation policy 风险分析的输入基础。

Source authority：Entity Log、entity resolution history、Case Log、Review / Intervention context、Governance Log。

Required fields when present：

| Field | Meaning | Source authority | Runtime / durable |
| --- | --- | --- | --- |
| `entity_refs` | 被检查的 entity refs | Entity Log | durable refs |
| `entity_status_context` | lifecycle status 和 authority context | Entity Log / Governance Log | runtime view over durable authority |
| `alias_role_context` | approved / candidate / rejected alias 和 confirmed / candidate role context | Entity Log / entity resolution / review context | durable refs + runtime summary |
| `entity_evidence_refs` | 支撑 entity 判断的 evidence refs | Evidence Log / Entity Log | durable refs |
| `related_case_refs` | 与 entity 相关的 completed case refs | Case Log | durable refs |

Optional fields：

- `new_entity_candidate_refs`
- `candidate_alias_refs`
- `candidate_role_context`
- `merge_candidate_inputs`
- `split_candidate_inputs`
- `recent_correction_refs`
- `automation_policy_context`
- `prior_governance_refs`

Validation / rejection rules：

- 没有 `entity_refs` 或 candidate refs 时，不能输出 entity-specific finding。
- `new_entity_candidate_refs` 不能被视为 stable entity authority，不能支持 rule match 或 rule promotion。
- `candidate_alias_refs`、`candidate_role_context` 不能被写成 approved alias 或 confirmed role。
- merge / split 风险只能输出 candidate；不得改变 entity lifecycle status 或历史 case 归属。
- automation-policy downgrade 必须引用 stable active entity；不能对 unresolved、candidate-only 或 ambiguous entity 静默降级。

Runtime-only vs durable references：

该对象是 runtime analysis basis。`entity_refs`、`alias refs`、`case_refs`、`governance_refs` 是 durable references；candidate role 仍是 runtime / candidate context，不是 durable role authority。

### 3.5 `rule_health_basis`

Purpose：提供 active rule 稳定性、适用性、过宽 / 过窄、rule conflict 和 rule review need 的输入基础。

Source authority：Rule Log、rule match outcomes、Review / Intervention corrections、Governance Log、Entity Log automation policy context。

Required fields when present：

| Field | Meaning | Source authority | Runtime / durable |
| --- | --- | --- | --- |
| `rule_refs` | 被检查的 approved rule refs | Rule Log | durable refs |
| `rule_lifecycle_context` | active / restricted / deprecated / pending context | Rule Log / Governance Log | durable refs + runtime summary |
| `rule_outcome_refs` | 本批次或近期 rule match outcome refs | workflow / audit context | durable refs / runtime summary |
| `rule_correction_refs` | accountant correction / objection refs | Review / Intervention Log | durable refs |
| `rule_entity_context` | rule 依赖的 entity、alias、role、automation policy context | Entity Log / Rule Log | durable refs + runtime summary |

Optional fields：

- `rule_blocked_or_ineligible_refs`
- `rule_miss_pattern_context`
- `conflicting_case_refs`
- `prior_rule_health_candidate_refs`
- `governance_restriction_refs`

Validation / rejection rules：

- `rule_refs` 必须引用 approved / durable rule context；candidate rule 只能进入 `case_to_rule_basis` 或 governance candidate context。
- 本节点不能 create、promote、modify、delete 或 downgrade active rule。
- `rule_correction_refs` 可支持 rule-health finding，但不能自动改变 rule lifecycle。
- rule instability 如果只来自 unfinalized transaction、summary wording 或 unsupported natural language note，不能形成 material rule-health conclusion。

Runtime-only vs durable references：

该对象是 runtime analysis basis。`Rule Log` refs 是 durable authority refs，但本节点只读取，不写入或修改。

### 3.6 `case_to_rule_basis`

Purpose：提供 completed cases 是否稳定到值得进入 rule governance review 的输入基础。

Source authority：Case Log、completed transaction context、Review / Intervention corrections、Entity Log role / automation policy context、Knowledge Summary 辅助背景。

Required fields when present：

| Field | Meaning | Source authority | Runtime / durable |
| --- | --- | --- | --- |
| `case_refs` | 被聚合评估的 completed case refs | Case Log | durable refs |
| `case_grouping_basis` | 为什么这些 case 可被同组比较 | Case Log / Entity Log / workflow analysis | runtime summary with durable refs |
| `final_outcome_pattern` | 同组 case 中稳定或冲突的 final outcome pattern | Case Log / review corrections | runtime summary over durable refs |
| `exception_context` | 例外、mixed-use、tax treatment、amount anomaly、role ambiguity 等风险 | Case Log / evidence / review context | runtime summary with durable refs |
| `promotion_authority_boundary` | 为什么只能 candidate，不能直接 rule promotion | active baseline / governance boundary | runtime |

Optional fields：

- `entity_ref`
- `confirmed_role_refs`
- `candidate_role_context`
- `supporting_evidence_refs`
- `conflicting_case_refs`
- `review_correction_refs`
- `automation_policy_context`
- `knowledge_summary_refs`

Validation / rejection rules：

- `case_refs` 必须是 completed cases；pending、draft 或 not-finalized cases 不能计入 promotion candidate。
- `new_entity_candidate`、candidate alias 或 candidate role 可以作为 risk/context，但不能支持 rule promotion authority。
- `case_to_rule_basis` 只能输出 candidate；不得写 `Rule Log` 或创建 active rule。
- `Knowledge Summary` 只能帮助 wording / context，不得替代 `Case Log` refs。

Runtime-only vs durable references：

该对象是 runtime aggregation basis。`case_refs` 是 durable case refs，但 repeated cases 不自动成为 rule。

### 3.7 `review_intervention_basis`

Purpose：提供 accountant 在本批次或近期介入中反复修正、确认、拒绝、暂缓或未解决事项的输入基础。

Source authority：Intervention Log、Review Node context、pending answers、accountant corrections、governance handoff。

Required fields when present：

| Field | Meaning | Source authority | Runtime / durable |
| --- | --- | --- | --- |
| `intervention_refs` | 相关 accountant interaction refs | Intervention Log / review record | durable refs |
| `intervention_types` | correction / confirmation / rejection / pending / objection 类型 | Review / Intervention context | runtime enum list |
| `subject_refs` | 介入绑定的 transaction、entity、case、rule、candidate 或 batch refs | workflow / durable stores | durable refs |
| `accountant_action_state` | accountant action 是否明确、模糊、拒绝、暂缓或未解决 | Intervention Log / Review Node | runtime |

Allowed `accountant_action_state` values：

- `explicit_correction`
- `explicit_confirmation`
- `explicit_rejection`
- `explicit_deferral`
- `still_pending`
- `ambiguous_response`
- `unresolved_objection`

Optional fields：

- `correction_pattern_summary`
- `related_rule_refs`
- `related_entity_refs`
- `related_case_refs`
- `prior_pending_question_refs`
- `governance_candidate_refs`

Validation / rejection rules：

- Accountant 模糊回答不能被解释成 stable entity、active rule、alias approval、role confirmation、merge/split approval 或 automation-policy relaxation。
- Explicit correction 可以支持 review-facing finding、rule-health candidate、case conflict context 或 automation-policy risk context，但不能自动写 active rule。
- `still_pending` 或 `unresolved_objection` 只能支持 review / governance needed 语义，不能支持 auto-downgrade，除非还有独立 durable evidence 满足降级边界。

Runtime-only vs durable references：

该对象引用 durable intervention / review records，但不把 accountant interaction 自动转化为 governance approval。

### 3.8 `governance_automation_basis`

Purpose：提供 governance history、automation policy、rule lifecycle、entity authority 和 auto-downgrade history 的输入基础。

Source authority：Governance Log、Entity Log、Rule Log、Review / Intervention context。

Required fields when present：

| Field | Meaning | Source authority | Runtime / durable |
| --- | --- | --- | --- |
| `governance_refs` | 相关 governance event refs | Governance Log | durable refs |
| `automation_policy_context` | 当前和历史 automation policy context | Entity Log / Governance Log | durable refs + runtime summary |
| `entity_or_rule_refs` | 被 governance / policy 影响的 entity 或 rule refs | Entity Log / Rule Log | durable refs |
| `approval_status_context` | approved / rejected / deferred / pending / auto-applied downgrade context | Governance Log | runtime view over durable authority |

Allowed `automation_policy` values：

- `eligible`
- `case_allowed_but_no_promotion`
- `rule_required`
- `review_required`
- `disabled`

Allowed `approval_status_context` values：

- `pending`
- `approved`
- `rejected`
- `deferred`
- `auto_applied_downgrade`
- `unresolved`
- `conflicting`

Optional fields：

- `prior_auto_downgrade_event_refs`
- `restriction_refs`
- `contested_downgrade_refs`
- `relaxation_or_upgrade_candidate_refs`
- `governance_notes`

Validation / rejection rules：

- automation-policy downgrade 只能从较宽松状态转向更保守状态。
- automation-policy upgrade / relaxation 必须输出 review / governance candidate，不能自动生效。
- rule lifecycle 变化必须 accountant / governance approval；本节点不能直接改变 active rule。
- rejected / deferred governance decision 不得被 lint 重新包装成 approved authority。

Runtime-only vs durable references：

该对象是 runtime authority view。只有 auto-applied downgrade output 可以触发 durable governance-event path；其他 governance changes 均 candidate-only。

### 3.9 `knowledge_summary_basis`

Purpose：提供 stale summary、summary mismatch、missing context 或 unresolved boundary 的输入基础。

Source authority：Knowledge Log / Summary Log 和对应 source memory refs。

Required fields when present：

| Field | Meaning | Source authority | Runtime / durable |
| --- | --- | --- | --- |
| `knowledge_summary_refs` | 被检查的 summary refs | Knowledge Log / Summary Log | durable refs |
| `source_memory_refs` | summary 对应的 entity / case / rule / governance refs | source memory stores | durable refs |
| `summary_issue_type` | stale、conflict、missing、overstated authority 等问题类型 | workflow / lint analysis | runtime |
| `source_priority_context` | source memory / governance history 是否优先于 summary | active baseline / source stores | runtime |

Allowed `summary_issue_type` values：

- `stale_summary`
- `summary_source_conflict`
- `missing_unresolved_boundary`
- `overstated_candidate_as_authority`
- `missing_governance_result`
- `insufficient_source_refs`

Optional fields：

- `affected_entity_refs`
- `affected_rule_refs`
- `affected_case_refs`
- `affected_governance_refs`
- `suggested_follow_up_scope`

Validation / rejection rules：

- Knowledge Summary 不能作为 deterministic rule source。
- Summary 与 source memory 冲突时，source memory / governance history 优先，输出应为 knowledge follow-up，不得直接改 entity、case、rule 或 governance authority。
- 如果 summary 缺少 source refs，不能用 summary wording 支持 material lint conclusion。

Runtime-only vs durable references：

该对象引用 durable knowledge records，但本节点不能通过修改摘要改变 memory authority。

## 4. Output Contracts

### 4.1 `post_batch_lint_result`

Purpose：本节点的唯一 output envelope，汇总 no-material result、review-facing finding、governance candidates、knowledge follow-up 和 limited auto-downgrade outputs。

Consumer / downstream authority：Review Node、Governance Review Node、Knowledge Compilation Node 和 workflow orchestrator。该 envelope 本身不是 accountant approval、Rule Log authority、stable Entity Log authority 或 Transaction Log record。

Required fields：

| Field | Meaning | Consumer / authority | Runtime / durable |
| --- | --- | --- | --- |
| `result_id` | 本次 lint result 标识 | workflow runtime | runtime |
| `request_id` | 对应 lint request | workflow runtime | runtime ref |
| `client_id` | 客户标识 | downstream routing | durable reference |
| `batch_id` | 批次标识 | downstream routing | runtime / durable batch ref |
| `lint_result_status` | 本次结果总体状态 | downstream routing | runtime enum |
| `source_refs_used` | 本次结果实际引用的 source refs | audit / review / governance visibility | durable refs |
| `authority_boundary_summary` | 本结果的 authority 边界摘要 | downstream validation | runtime summary |

Allowed `lint_result_status` values：

- `no_material_finding`
- `findings_emitted`
- `candidates_emitted`
- `auto_downgrade_applied`
- `mixed_result`
- `blocked_invalid_input`
- `blocked_unresolved_authority`

Optional fields：

- `review_facing_findings`
- `governance_candidate_handoffs`
- `case_to_rule_candidates`
- `rule_health_restriction_candidates`
- `auto_applied_automation_policy_downgrades`
- `knowledge_compilation_follow_ups`
- `blocked_reason`
- `result_trace`

Validation rules：

- `lint_result_status = no_material_finding` 时，不得同时包含 material findings、governance candidates 或 auto-applied downgrades。
- `lint_result_status = auto_downgrade_applied` 或 `mixed_result` 且包含 downgrade 时，必须包含对应 `auto_applied_automation_policy_downgrades`。
- `blocked_invalid_input` 或 `blocked_unresolved_authority` 时，不得输出 durable mutation payload。
- `authority_boundary_summary` 必须明确 raw lint finding 不可作为 runtime classification、rule source 或 governance approval。

Durable / candidate / runtime boundary：

`post_batch_lint_result` 是 runtime handoff envelope。除 `auto_applied_automation_policy_downgrade` 通过 governance-event path 形成 durable effect 外，其余 output 默认是 candidate-only 或 runtime handoff。

### 4.2 `review_facing_lint_finding`

Purpose：给 Review Node / accountant 可见的批次级风险、趋势或未解决事项。

Consumer / downstream authority：Review Node。该 finding 只提供 accountant visibility 和 review context，不是 durable memory mutation。

Required fields：

| Field | Meaning | Consumer / authority | Runtime / durable |
| --- | --- | --- | --- |
| `finding_id` | finding 标识 | workflow runtime | runtime |
| `finding_type` | finding 类型 | Review / Governance routing | runtime enum |
| `severity` | 风险级别 | review packaging | runtime enum |
| `subject_refs` | 绑定的 batch、transaction、entity、case、rule、governance 或 knowledge refs | downstream traceability | durable refs |
| `finding_summary` | accountant-facing 简短说明 | Review Node | runtime wording |
| `evidence_refs` | 支撑 finding 的 evidence/source refs | review traceability | durable refs |
| `recommended_review_action` | 建议 accountant 看什么或决定什么 | Review Node | runtime guidance |
| `authority_limit` | finding 不能做什么 | downstream validation | runtime |

Allowed `finding_type` values：

- `entity_merge_risk`
- `entity_split_risk`
- `alias_role_governance_need`
- `new_entity_governance_need`
- `rule_instability`
- `case_to_rule_opportunity`
- `rule_health_restriction_need`
- `automation_policy_risk`
- `stale_knowledge_or_summary_conflict`
- `repeated_intervention_pattern`
- `unresolved_governance_risk`
- `insufficient_evidence_monitoring`

Allowed `severity` values：

- `info`
- `monitor`
- `review_needed`
- `governance_needed`
- `high_risk`

Optional fields：

- `related_candidate_ids`
- `related_auto_downgrade_event_id`
- `source_conflict_summary`
- `llm_semantic_summary`

Validation rules：

- `subject_refs` 和 `evidence_refs` 不能同时为空。
- `finding_summary` 不能把 candidate 写成 approved authority。
- `recommended_review_action` 不能要求 accountant 批准 `authority_limit` 禁止的结果。
- `llm_semantic_summary` 只能解释风险，不能成为 mutation authority。

Durable / candidate / runtime boundary：

Review-facing finding 是 runtime / review handoff。是否有后续 durable review / intervention record 由 Review Node 管理；本对象不写 durable memory。

### 4.3 `governance_candidate_handoff`

Purpose：把需要 Governance Review Node 评估的高权限事项组织成 candidate。

Consumer / downstream authority：Governance Review Node。该 handoff 不批准治理变化。

Required fields：

| Field | Meaning | Consumer / authority | Runtime / durable |
| --- | --- | --- | --- |
| `candidate_id` | governance candidate 标识 | governance workflow | runtime / candidate ref |
| `candidate_type` | candidate 类型 | Governance Review routing | runtime enum |
| `subject_refs` | 相关 entity、alias、role、rule、case、transaction、batch 或 knowledge refs | governance traceability | durable refs |
| `candidate_basis` | 为什么需要 governance review | lint analysis over source refs | runtime summary |
| `evidence_refs` | 支撑 candidate 的 source refs | governance traceability | durable refs |
| `required_authority` | 谁必须批准或处理 | active baseline / governance boundary | runtime |
| `candidate_status` | candidate 当前状态 | workflow runtime | runtime enum |

Allowed `candidate_type` values：

- `entity_merge_candidate`
- `entity_split_candidate`
- `alias_approval_candidate`
- `alias_rejection_candidate`
- `role_confirmation_candidate`
- `new_entity_governance_candidate`
- `rule_candidate`
- `rule_conflict_candidate`
- `rule_instability_candidate`
- `automation_policy_review_candidate`
- `automation_policy_upgrade_or_relaxation_candidate`
- `unresolved_governance_risk_candidate`
- `knowledge_authority_cleanup_candidate`

Allowed `required_authority` values：

- `accountant_approval_required`
- `governance_review_required`
- `review_visibility_required`
- `knowledge_compilation_required`

Allowed `candidate_status` values：

- `candidate_open`
- `candidate_deferred`
- `candidate_blocked_insufficient_evidence`
- `candidate_superseded`

Optional fields：

- `risk_flags`
- `conflict_refs`
- `related_review_finding_id`
- `proposed_event_preview`

Validation rules：

- Candidate 必须绑定具体 `subject_refs`；不能只有自然语言建议。
- `proposed_event_preview` 只能作为 preview，不是 executed governance event。
- `automation_policy_upgrade_or_relaxation_candidate` 永远不能自动生效。
- merge / split、alias approval / rejection、role confirmation、new entity stabilization、rule lifecycle change 都必须保持 candidate 语义。

Durable / candidate / runtime boundary：

该 handoff 是 candidate-only。后续 durable governance event 必须由 Governance Review Node / accountant authority path 形成。

### 4.4 `case_to_rule_candidate`

Purpose：表达一组 completed cases 可能稳定到值得进入 rule governance review。

Consumer / downstream authority：Governance Review Node / Review Node。该对象不是 rule，不进入 Rule Match。

Required fields：

| Field | Meaning | Consumer / authority | Runtime / durable |
| --- | --- | --- | --- |
| `candidate_id` | candidate 标识 | governance workflow | runtime / candidate ref |
| `entity_ref` | 相关 stable entity ref | Entity Log | durable ref |
| `case_refs` | 支撑 candidate 的 completed cases | Case Log | durable refs |
| `proposed_rule_scope_summary` | 可能规则化的业务范围摘要 | governance review | runtime wording |
| `stability_basis` | 为什么看起来稳定 | lint analysis over Case Log | runtime summary |
| `exception_risk_context` | 为什么仍需治理评估 | Case Log / evidence / review context | runtime summary with durable refs |
| `promotion_boundary` | 明确本对象不等于 rule promotion | active baseline | runtime |

Optional fields：

- `confirmed_role_refs`
- `candidate_role_context`
- `supporting_evidence_refs`
- `conflicting_case_refs`
- `review_correction_refs`
- `automation_policy_context`
- `related_governance_candidate_id`

Validation rules：

- `case_refs` 必须全部为 completed cases。
- `entity_ref` 必须引用 stable entity；如果只有 `new_entity_candidate`，只能输出 governance candidate，不得输出 case-to-rule candidate。
- 有 candidate alias / candidate role 时，必须放入 `exception_risk_context`，不得把它们当作 approved rule precondition。
- `promotion_boundary` 必须说明 accountant / governance approval 是 rule promotion 的唯一 authority path。

Durable / candidate / runtime boundary：

该对象是 rule-governance candidate。它不能写 `Rule Log`，不能支持 Rule Match，也不能成为 deterministic rule source。

### 4.5 `rule_health_restriction_candidate`

Purpose：表达 active rule、rule condition、applicability 或 lifecycle 暴露风险，需要 review / governance 评估。

Consumer / downstream authority：Governance Review Node / Review Node。该对象不能修改 active rule。

Required fields：

| Field | Meaning | Consumer / authority | Runtime / durable |
| --- | --- | --- | --- |
| `candidate_id` | candidate 标识 | governance workflow | runtime / candidate ref |
| `rule_ref` | 被检查的 active rule | Rule Log | durable ref |
| `rule_health_issue_type` | rule 风险类型 | governance routing | runtime enum |
| `supporting_source_refs` | 支撑风险判断的 correction / case / entity / governance refs | downstream traceability | durable refs |
| `risk_summary` | rule 为什么可能不安全 | review / governance wording | runtime summary |
| `required_follow_up` | 下游应 review 还是 governance | downstream routing | runtime enum |
| `no_mutation_boundary` | 明确本节点不能改变 active rule | active baseline | runtime |

Allowed `rule_health_issue_type` values：

- `frequent_accountant_correction`
- `overbroad_rule_condition`
- `overnarrow_rule_condition`
- `entity_or_alias_authority_changed`
- `role_context_conflict`
- `automation_policy_conflict`
- `case_conflict_with_rule`
- `stale_rule_context`
- `insufficient_evidence_for_action`

Allowed `required_follow_up` values：

- `review_visibility_only`
- `governance_review_required`
- `monitor_next_batch`
- `blocked_insufficient_evidence`

Optional fields：

- `related_case_refs`
- `related_intervention_refs`
- `related_entity_refs`
- `related_governance_refs`
- `suggested_rule_review_question`

Validation rules：

- `rule_ref` 必须引用 durable Rule Log 中的 rule；candidate rule 不适用本对象。
- `no_mutation_boundary` 必须存在。
- `supporting_source_refs` 不能只包含 Knowledge Summary 或 unbound natural language note。
- 输出该 candidate 不得改变 rule lifecycle、rule condition 或 active status。

Durable / candidate / runtime boundary：

该对象是 candidate-only。active rule 的任何创建、修改、删除、降级或 lifecycle 变化都必须经 accountant / governance approval。

### 4.6 `auto_applied_automation_policy_downgrade`

Purpose：表达本节点在 active baseline 允许的受控边界内，对 entity `automation_policy` 执行了风险降低方向的自动降级。

Consumer / downstream authority：Entity memory / governance event workflow、Review Node、Governance Review Node。该对象是本节点唯一可产生 durable effect 的 output category。

Required fields：

| Field | Meaning | Consumer / authority | Runtime / durable |
| --- | --- | --- | --- |
| `downgrade_id` | 本次 auto-downgrade 标识 | workflow / governance trace | runtime / durable event ref if persisted |
| `entity_id` | 被降级的 stable entity | Entity Log | durable ref |
| `old_automation_policy` | 降级前 policy | Entity Log | durable state |
| `new_automation_policy` | 降级后 policy | lint conservative authority | durable state after event |
| `downgrade_reason` | 为什么需要风险降低 | lint analysis | runtime summary, review-visible |
| `supporting_source_refs` | 支撑降级的 durable refs | Case / Review / Governance / Entity / Rule sources | durable refs |
| `entity_governance_event_payload` | 必须记录的 governance-event 语义 payload | governance-event authority path | durable record payload |
| `review_visibility_ref` | 给 Review Node 的可见性绑定 | workflow runtime | runtime / durable review ref later |

Required fields inside `entity_governance_event_payload`：

| Field | Required value / meaning |
| --- | --- |
| `event_id` | governance event 唯一标识 |
| `event_type` | `change_automation_policy` |
| `entity_ids` | 必须包含 `entity_id` |
| `old_value` | `old_automation_policy` |
| `new_value` | `new_automation_policy` |
| `source` | `lint_pass` |
| `requires_accountant_approval` | `false` |
| `approval_status` | `auto_applied_downgrade` |
| `reason` | 与 `downgrade_reason` 一致或更详细 |
| `evidence_links` | `supporting_source_refs` 中的 evidence/source refs |
| `created_at` | event 创建时间 |

Allowed downgrade direction：

- `eligible` → `case_allowed_but_no_promotion`
- `eligible` → `rule_required`
- `eligible` → `review_required`
- `eligible` → `disabled`
- `case_allowed_but_no_promotion` → `rule_required`
- `case_allowed_but_no_promotion` → `review_required`
- `case_allowed_but_no_promotion` → `disabled`
- `rule_required` → `review_required`
- `rule_required` → `disabled`
- `review_required` → `disabled`

Optional fields：

- `related_review_finding_id`
- `related_rule_health_candidate_id`
- `prior_policy_history_refs`
- `contest_or_reversal_guidance`

Validation rules：

- `entity_id` 必须引用 stable entity；candidate、ambiguous、merged-away 或 unresolved entity 不得静默降级。
- `new_automation_policy` 必须比 `old_automation_policy` 更保守；任何 upgrade / relaxation invalid。
- `supporting_source_refs` 不能只包含 Transaction Log refs、Knowledge Summary refs、draft、queue item 或 unbound note。
- 降级不能改变 active rule、alias approval、role confirmation、entity merge/split、current transaction accounting outcome 或 historical Transaction Log。
- 必须有 Review / Governance visibility；不能静默 durable mutation。

Durable / candidate / runtime boundary：

该对象通过 governance-event path 产生 durable effect。它不是 accountant approval，不批准任何 rule / alias / role / merge / split，也不阻断历史交易解释；未来 runtime 只通过更新后的 entity `automation_policy` 间接受影响。

### 4.7 `knowledge_compilation_follow_up`

Purpose：把 stale summary、source conflict、unresolved risk、monitoring concern 或治理结果交给 Knowledge Compilation Node。

Consumer / downstream authority：Knowledge Compilation Node。该对象不能改变 source memory authority。

Required fields：

| Field | Meaning | Consumer / authority | Runtime / durable |
| --- | --- | --- | --- |
| `follow_up_id` | follow-up 标识 | knowledge workflow | runtime / candidate ref |
| `follow_up_type` | follow-up 类型 | Knowledge Compilation routing | runtime enum |
| `affected_summary_refs` | 受影响 summary refs | Knowledge Log / Summary Log | durable refs |
| `source_memory_refs` | 应回看或优先的 source refs | Entity / Case / Rule / Governance stores | durable refs |
| `summary_boundary_note` | 摘要应怎样表达 unresolved / candidate / approved 边界 | lint / source authority | runtime wording |
| `authority_limit` | Knowledge Summary 不能成为 rule source | active baseline | runtime |

Allowed `follow_up_type` values：

- `stale_summary_refresh`
- `summary_source_conflict_review`
- `candidate_authority_wording_cleanup`
- `unresolved_risk_monitoring_note`
- `governance_result_summary_update`

Optional fields：

- `related_review_finding_id`
- `related_governance_candidate_id`
- `suggested_compilation_scope`

Validation rules：

- `source_memory_refs` 不能为空。
- `summary_boundary_note` 不能把 candidate 或 lint finding 写成 approved authority。
- 该 follow-up 不得改变 entity、case、rule、governance 或 Transaction Log authority。

Durable / candidate / runtime boundary：

该对象是 knowledge workflow handoff。后续摘要可以被 durable 保存，但摘要仍不是 deterministic rule source。

### 4.8 `no_material_finding_result`

Purpose：表达本次 scope 下没有发现需要 review、governance、knowledge follow-up 或 automation-policy action 的 material issue。

Consumer / downstream authority：workflow orchestrator / Review Node optional visibility。

Required fields：

| Field | Meaning | Consumer / authority | Runtime / durable |
| --- | --- | --- | --- |
| `scope_checked` | 实际检查的 scope | workflow | runtime |
| `source_refs_checked` | 实际读取或汇总的 source refs | traceability | durable refs |
| `no_finding_statement` | 无 material finding 的限定说明 | downstream visibility | runtime wording |
| `limitations` | 本结论的范围限制 | downstream validation | runtime |

Optional fields：

- `monitor_next_batch_subject_refs`
- `insufficient_data_notes`

Validation rules：

- `no_finding_statement` 不能写成未来自动化永久安全保证。
- 如果存在 unresolved authority conflict、invalid input 或 blocked mutation claim，不能输出 no-material result。

Durable / candidate / runtime boundary：

该对象是 runtime result。它不改变任何 durable authority。

## 5. Field Authority and Memory Boundary

### 5.1 Source of truth for important fields

| Field / concept | Source of truth |
| --- | --- |
| `client_id`、`batch_id`、`request_id`、`result_id` | workflow runtime / orchestration context |
| `transaction_id` | Transaction Identity Node / durable transaction identity layer |
| completed transaction history | finalization context and audit-facing `Transaction Log` query; audit-only |
| `entity_id`、entity lifecycle、approved alias、confirmed role、automation_policy | `Entity Log` plus governance-event history |
| completed case precedent | `Case Log` |
| active deterministic rule | `Rule Log` only |
| accountant correction / approval / objection / pending answer | `Intervention Log` / Review Node durable interaction record |
| governance approval / rejection / deferral / restriction / auto-applied downgrade | `Governance Log` / governance-event semantics |
| knowledge summary wording | `Knowledge Log / Summary Log`; never deterministic rule source |
| profile structural facts | `Profile` |

### 5.2 Fields that can never become durable memory by this node

本节点不能把以下字段或对象直接写成 durable authority：

- `review_facing_lint_finding`
- `governance_candidate_handoff`
- `case_to_rule_candidate`
- `rule_health_restriction_candidate`
- `knowledge_compilation_follow_up`
- `llm_semantic_summary`
- `finding_summary`
- `recommended_review_action`
- `candidate_role_context`
- `new_entity_candidate_refs`
- `candidate_alias_refs`
- `request_trace` / `result_trace`
- draft、queue、report draft、unbound natural language note

这些对象最多是 runtime handoff、candidate signal、review visibility 或 knowledge follow-up，不是 `Log` authority。

### 5.3 Fields that can become durable only after accountant / governance approval

以下事项必须经 accountant / governance approval 才能成为 durable authority：

- entity merge / split outcome
- stable entity creation from candidate
- approved alias / rejected alias
- confirmed role
- rule creation / promotion / modification / deletion / downgrade
- automation-policy upgrade or relaxation
- governance approval / rejection / deferral decision
- source-memory cleanup that changes entity、case、rule 或 governance authority

本节点可以提出候选，但不能批准这些变化。

### 5.4 Limited durable action: automation-policy downgrade

本节点唯一可直接触发的 durable action 是更保守方向的 entity `automation_policy` downgrade。

该动作必须同时满足：

- stable entity 可识别；
- `new_automation_policy` 比 `old_automation_policy` 更保守；
- 支撑依据来自 durable source refs，而不是 draft / summary-only / unbound note；
- 写入 `entity_governance_event` 语义记录，`approval_status = auto_applied_downgrade`；
- 对 Review / Governance 可见；
- 不改变 active rule、alias、role、merge/split、current accounting outcome 或 historical `Transaction Log`。

### 5.5 Audit vs learning / logging boundary

`Transaction Log` 是 audit-facing history。它可以被查询来理解完成交易和 review/correction trace，但：

- 不参与 runtime decision；
- 不是 learning layer；
- 不是 rule source；
- 不是 governance approval source；
- 不被本节点重写。

`Log` 一词只用于 durable long-term meaningful information storage。`finding`、`candidate`、`handoff`、`queue`、`review draft`、`report draft` 或 runtime trace 不应被命名为 `Log`。

## 6. Validation Rules

### 6.1 Contract-level validation rules

- 所有 output 必须能追溯到 `post_batch_lint_request.request_id`、`client_id` 和 `batch_id`。
- 所有 material finding / candidate / downgrade 必须有 `subject_refs` 或等价 durable refs。
- Candidate、finding、summary 和 LLM wording 不能替代 source memory refs。
- `Transaction Log` refs 必须标记为 audit-facing / completed history，不得作为 runtime decision、rule source、learning authority 或 governance approval。
- Knowledge Summary 与 source memory 冲突时，source memory / governance history 优先。
- 本节点不能输出任何会导致 active rule 直接变化的 payload。
- 本节点不能输出任何 entity merge / split、alias approval、role confirmation 或 stable entity creation 的 executed payload。
- automation-policy downgrade 之外的 durable mutation claim invalid。

### 6.2 Conditions that make the input invalid

Input invalid when：

- `post_batch_lint_request` required fields 缺失。
- `trigger_reasons` 不在 allowed values。
- `completed_batch_basis` 不能证明 batch-level lint boundary 已达到。
- 输入只有单笔未完成 runtime rationale、pending、draft、queue item、candidate note 或 unbound natural language warning。
- source authority 把 candidate-only、rejected、deferred、unresolved 或 summary-only source 标成 approved authority。
- Transaction Log 被声明为 learning source、rule source、runtime decision source 或 governance approval source。
- active source memory 与 summary 冲突但未标记 conflict / source priority。

### 6.3 Conditions that make the output invalid

Output invalid when：

- `post_batch_lint_result` required fields 缺失。
- `no_material_finding` 与 material finding / candidate / downgrade 同时出现。
- finding / candidate 没有 durable subject refs 或 source refs。
- candidate wording 把 proposed / repeated / likely 写成 approved / active / confirmed。
- case-to-rule candidate 被写成 active rule 或 Rule Match source。
- rule-health candidate 直接修改 active rule lifecycle 或 condition。
- merge / split、alias、role、new entity candidate 被写成 executed governance outcome。
- automation-policy output 放宽权限、升级权限，或对 non-stable entity 降级。
- auto-downgrade 没有 governance-event payload、supporting refs 或 review visibility。
- output 声称重写或修正 historical `Transaction Log`。

### 6.4 Stop / ask conditions for unresolved contract authority

后续 Stage 或实现前必须 stop / ask 的情况：

- 需要把 lint findings 持久保存为新的 durable monitoring artifact / `Log`。
- 需要冻结 auto-downgrade exact eligibility threshold、contest / reversal contract 或 persistence mechanics。
- 需要让 Post-Batch Lint 直接改变 active rule、alias、role、merge/split 或 stable entity status。
- 需要把 Knowledge Summary 或 Transaction Log 作为 future runtime classification / rule source。
- 需要决定 Post-Batch Lint 与 Knowledge Compilation 的 exact ordering。

## 7. Examples

### 7.1 Valid minimal example

```json
{
  "post_batch_lint_request": {
    "request_id": "pbl_req_001",
    "client_id": "client_001",
    "batch_id": "batch_2026_05_001",
    "lint_scope": "completed_batch",
    "trigger_reasons": ["routine_post_batch_check"],
    "completed_batch_basis": {
      "batch_id": "batch_2026_05_001",
      "batch_completion_status": "completed_batch_closed",
      "completed_transaction_refs": ["txn_01HAA", "txn_01HAB"],
      "batch_time_window": "2026-05",
      "finalization_basis": "completed transactions have finalization refs"
    },
    "source_authority_context": {
      "source_authority_items": [
        {
          "source_category": "transaction_audit_history",
          "source_refs": ["txn_log_ref_01"],
          "authority_state": "completed_history",
          "allowed_use": "audit_context_only"
        }
      ],
      "candidate_only_sources": [],
      "durable_authority_sources": ["txn_log_ref_01"],
      "hard_authority_blocks": []
    }
  },
  "post_batch_lint_result": {
    "result_id": "pbl_result_001",
    "request_id": "pbl_req_001",
    "client_id": "client_001",
    "batch_id": "batch_2026_05_001",
    "lint_result_status": "no_material_finding",
    "source_refs_used": ["txn_log_ref_01"],
    "authority_boundary_summary": "No durable authority changed; Transaction Log used as audit context only.",
    "no_material_finding_result": {
      "scope_checked": "completed_batch",
      "source_refs_checked": ["txn_log_ref_01"],
      "no_finding_statement": "No material post-batch automation-health issue found in this scope.",
      "limitations": "This is not a permanent guarantee of future automation safety."
    }
  }
}
```

Reason：valid，因为 input 达到 batch-level boundary，Transaction Log 只作 audit context，output 不改变 durable authority。

### 7.2 Valid richer example

```json
{
  "post_batch_lint_result": {
    "result_id": "pbl_result_014",
    "request_id": "pbl_req_014",
    "client_id": "client_001",
    "batch_id": "batch_2026_05_001",
    "lint_result_status": "mixed_result",
    "source_refs_used": ["entity_home_depot", "case_101", "case_122", "int_044", "gov_017"],
    "authority_boundary_summary": "Findings are candidate/review handoff only except the conservative automation-policy downgrade.",
    "review_facing_findings": [
      {
        "finding_id": "finding_014_a",
        "finding_type": "automation_policy_risk",
        "severity": "governance_needed",
        "subject_refs": ["entity_home_depot"],
        "finding_summary": "Recent corrected cases show mixed-use risk for this entity.",
        "evidence_refs": ["case_101", "case_122", "int_044"],
        "recommended_review_action": "Review whether this entity should remain eligible for case-based automation.",
        "authority_limit": "Finding is not accountant approval and does not change active rules."
      }
    ],
    "auto_applied_automation_policy_downgrades": [
      {
        "downgrade_id": "downgrade_014_a",
        "entity_id": "entity_home_depot",
        "old_automation_policy": "eligible",
        "new_automation_policy": "case_allowed_but_no_promotion",
        "downgrade_reason": "Mixed-use corrections make rule promotion unsafe until governance review.",
        "supporting_source_refs": ["case_101", "case_122", "int_044"],
        "entity_governance_event_payload": {
          "event_id": "gov_event_055",
          "event_type": "change_automation_policy",
          "entity_ids": ["entity_home_depot"],
          "old_value": "eligible",
          "new_value": "case_allowed_but_no_promotion",
          "source": "lint_pass",
          "requires_accountant_approval": false,
          "approval_status": "auto_applied_downgrade",
          "reason": "Mixed-use corrections make promotion unsafe.",
          "evidence_links": ["case_101", "case_122", "int_044"],
          "created_at": "2026-05-06T18:10:00Z"
        },
        "review_visibility_ref": "finding_014_a"
      }
    ],
    "rule_health_restriction_candidates": [
      {
        "candidate_id": "rule_health_014_a",
        "rule_ref": "rule_089",
        "rule_health_issue_type": "case_conflict_with_rule",
        "supporting_source_refs": ["case_101", "case_122", "int_044"],
        "risk_summary": "The active rule may be too broad for mixed-use purchases.",
        "required_follow_up": "governance_review_required",
        "no_mutation_boundary": "Post-Batch Lint cannot modify active rules."
      }
    ]
  }
}
```

Reason：valid，因为唯一 durable effect 是更保守的 automation-policy downgrade，并通过 governance-event payload 暴露；rule-health 仍是 candidate。

### 7.3 Invalid example

```json
{
  "post_batch_lint_result": {
    "result_id": "pbl_result_bad",
    "request_id": "pbl_req_bad",
    "client_id": "client_001",
    "batch_id": "batch_2026_05_001",
    "lint_result_status": "candidates_emitted",
    "source_refs_used": ["knowledge_summary_07"],
    "authority_boundary_summary": "Summary says Home Depot is usually materials.",
    "case_to_rule_candidates": [
      {
        "candidate_id": "ctr_bad",
        "entity_ref": "new_entity_candidate_12",
        "case_refs": ["draft_case_1"],
        "proposed_rule_scope_summary": "Create active rule for Home Depot materials.",
        "stability_basis": "Knowledge summary says usually materials.",
        "exception_risk_context": "None.",
        "promotion_boundary": "Rule can be used next batch."
      }
    ]
  }
}
```

Reason：invalid：

- `entity_ref` 不是 stable entity；
- `case_refs` 不是 completed Case Log refs；
- Knowledge Summary 被当成 rule source；
- candidate 被写成 next-batch usable rule；
- 该 output 绕过 accountant / governance approval。

## 8. Open Contract Boundaries

- Post-Batch Lint 是否需要生成可持久保存的 monitoring artifact 仍未冻结；本 Stage 3 不把 finding / candidate / handoff 默认命名为新的 `Log`。
- Post-Batch Lint 与 Knowledge Compilation 的 exact ordering 未冻结。
- automation-policy auto-downgrade 的 exact eligibility threshold、contest / reversal contract、dedupe / idempotency contract 和 persistence mechanics 未冻结。
- case-to-rule candidate 的 exact eligibility threshold 未冻结。
- rule instability、frequent correction、entity split / merge risk 的 exact thresholds 未冻结。
- rejected / deferred governance decision 对未来 lint monitoring 和 Knowledge Summary 的 exact expression 未冻结。

## 9. Self-Review

- 已阅读 required repo docs：`AGENTS.md`、`TASK_STATE.md`、`PLANS.md`、`CLAUDE.md`、`DECISIONS.md`、`supporting documents/communication_preferences.md`、`supporting documents/development_workflow.md`、`supporting documents/node_design_roadmap.md`、`new system/new_system.md`。
- 已阅读本节点 prior approved docs：`post_batch_lint_node__stage_1__functional_intent.md`、`post_batch_lint_node__stage_2__logic_and_boundaries.md`。
- 已读取可用 Superpowers docs：`using-superpowers/SKILL.md`、`brainstorming/SKILL.md`；project workflow skill `ai-bookkeeper-node-design-facilitation` 在当前环境不存在，因此按 runner instruction 使用 repo `supporting documents/node_design_roadmap.md` 与本节点 Stage 1/2 docs 作为 workflow authority。
- 已注意 optional reading absence：`supporting documents/node_design_roadmap_zh.md` 不在 working tree；本文件未发明该文件内容。
- 未做 Stage 4/5/6/7 creep：没有定义执行算法、技术实现地图、测试矩阵或 coding-agent task contract。
- 未发明 unsupported product authority：auto-downgrade 只按 active baseline 的风险降低边界表达；其他高权限变化均保持 candidate / review / governance 语义。
- 本次未修改 `new_system.md`、Stage 1/2 docs、governance docs 或其他 repo 文件；仅在未 blocked 的情况下写入目标 Stage 3 文件。
