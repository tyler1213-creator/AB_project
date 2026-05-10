# Governance Review Node — Stage 3：Data Contract Spec

## 1. Stage 范围

本 Stage 3 只定义 `Governance Review Node` 的 implementation-facing data contracts。

前置设计依据是：

- `new system/node_stage_designs/governance_review_node__stage_1__functional_intent.md`
- `new system/node_stage_designs/governance_review_node__stage_2__logic_and_boundaries.md`

本文件把 Stage 1/2 已批准的 durable-memory governance gate 行为边界转换为输入对象类别、输出对象类别、字段含义、字段 authority、runtime-only / durable-memory 边界、validation rules 和紧凑示例。

本文件不定义：

- step-by-step execution algorithm 或 branch sequence
- repo module path、class、API、storage engine、DB migration 或 code file layout
- test matrix、fixture plan 或 coding-agent task contract
- Review UI、prompt structure、queue ordering、dedup、expiry 或 retry 机制
- durable memory mutation 的技术执行者或存储实现
- 新 product authority 或 legacy replacement mapping

## 2. Contract Position in Workflow

`Governance Review Node` 位于普通交易处理结果、review / intervention 语境、case learning、lint findings 与长期记忆 authority 变化之间：

```text
runtime / review / logging / case-learning / lint governance candidates
→ Governance Review Node
→ governance decision record / authorized mutation handoff / blocked or deferred handoff
→ Entity Log / Rule Log / Governance Log / Knowledge Compilation / Post-Batch Lint / future runtime workflow
```

### 2.1 Upstream handoff consumed

本节点消费 `governance_review_request`。

该 request 表示：

- 上游 workflow 已提出可能影响长期 authority 的治理候选；
- 候选已绑定 evidence、transaction、case、review、intervention、memory state、lint finding 或 accountant instruction 中至少一种可追溯 basis；
- 候选事项不是当前交易分类、pending clarification、JE generation、final Transaction Log write 或 completed-case write；
- 候选尚未被正式批准、拒绝、暂缓、退回、阻断或记录为已处理治理结果。

典型上游来源包括：

- `Entity Resolution Node`
- `Rule Match Node`
- `Case Judgment Node`
- `Coordinator / Pending Node`
- `Review Node`
- `Transaction Logging Node`
- `Case Memory Update Node`
- `Post-Batch Lint Node`
- `Onboarding Node`
- accountant instruction / intervention context

### 2.2 Downstream handoff produced

本节点可产生以下 output categories：

- `governance_decision_record`：写入或推动写入 `Governance Log` 的 durable governance history。
- `authorized_memory_change_handoff`：在 approval authority 足够时，表达允许对应长期记忆或 automation authority 改变的授权 handoff。
- `governance_blocked_handoff`：runtime-only 安全停止，说明候选不能被批准。
- `candidate_refinement_handoff`：runtime-only 候选重组、补证据、拆分、合并或澄清 handoff。
- `knowledge_lint_handoff`：runtime-only 下游交接，供 `Knowledge Compilation Node` 或 `Post-Batch Lint Node` 使用。

### 2.3 Logs / memory stores read

本节点可以读取或消费：

- `Evidence Log` references 和 objective evidence context；
- `Entity Log` 中 entity、alias、role、status、authority、risk flags、automation_policy 和 evidence links；
- `Case Log` 中 completed-case precedent、exception、accountant correction 和 case authority context；
- `Rule Log` 中 active / historical rule authority、rule lifecycle、rule conflicts 和 rule-health context；
- `Transaction Log` finalized audit history，但只能作为 audit-facing historical context，不能参与 runtime decision、learning 或 rule source；
- `Intervention Log` 中 accountant questions、answers、corrections、confirmations、objections 和 review context；
- `Governance Log` 中 prior approvals、rejections、deferrals、restrictions、auto-applied downgrades 和 authority rationale；
- `Knowledge Log / Summary Log` 中可读摘要，但不能作为 deterministic rule source；
- `Profile` 中与候选影响有关的结构事实或限制。

### 2.4 Logs / memory stores written or candidate-only

本节点可以写入或推动写入的 durable 内容只限治理语义：

- `Governance Log` / governance event history；
- accountant / governance approval、rejection、deferral、restriction 或 auto-applied downgrade visibility；
- approved governance event 对应的 authorized durable memory change handoff。

本节点不能写入：

- `Transaction Log`
- `Case Log`
- journal entry
- current transaction accounting outcome
- report output

本节点是否直接执行已授权的 `Entity Log`、`Rule Log`、Profile、tax config 或 account-mapping mutation 尚未冻结。本 Stage 3 只定义授权 handoff 与 durable governance record 的数据 contract。

候选、queue item、review draft、lint finding、runtime trace 和 grouping helper 不是 `Log`。只有写入 active baseline 定义的 durable store 时，才能称为 `Log`。

## 3. Input Contracts

### 3.1 `governance_review_request`

Purpose：Governance Review Node 的主 runtime input envelope，承载一个或多个需要治理审查的长期 authority 候选。

Source authority：workflow orchestrator / upstream nodes。该 request 只汇总候选、证据、authority limits 和 memory state，不创造 accountant approval 或 governance approval。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `governance_review_request_id` | 本次治理审查 request 标识 | workflow runtime | runtime-only，可被治理记录引用 |
| `client_id` | 当前客户引用 | client / batch context | durable reference |
| `batch_id` | 当前批次引用；非批次触发时仍应有等价 workflow context | workflow runtime | runtime reference |
| `trigger_source` | 触发本 request 的上游 node 或语境 | upstream workflow | runtime |
| `trigger_reason` | 为什么进入 Governance Review | upstream workflow / accountant context | runtime |
| `candidate_items` | 待治理候选列表 | upstream handoff | runtime list with durable refs |
| `authority_limit_context` | 本 request 最多允许产生的治理结果 | durable policy / prior governance / upstream constraints | runtime view over durable authority |

Allowed `trigger_source` values：

- `entity_resolution_node`
- `rule_match_node`
- `case_judgment_node`
- `coordinator_pending_node`
- `review_node`
- `transaction_logging_node`
- `case_memory_update_node`
- `post_batch_lint_node`
- `onboarding_node`
- `accountant_instruction`
- `workflow_orchestrator`

Allowed `trigger_reason` values：

- `entity_authority_candidate`
- `alias_authority_candidate`
- `role_authority_candidate`
- `entity_merge_split_candidate`
- `rule_lifecycle_candidate`
- `rule_conflict_or_health_issue`
- `automation_policy_candidate`
- `auto_applied_downgrade_visibility`
- `memory_consistency_issue`
- `accountant_governance_instruction`
- `post_batch_lint_governance_finding`
- `profile_tax_or_account_mapping_review_candidate`

Optional fields：

- `request_summary`：人类可读摘要；不是 authority。
- `related_review_package_refs`：相关 Review Node package / decision refs。
- `related_intervention_refs`：相关 accountant intervention refs。
- `related_transaction_log_refs`：相关 finalized audit history refs；只作 audit context。
- `runtime_trace`：orchestration diagnostics；不能作为 approval 或 evidence。

Validation / rejection rules：

- `governance_review_request_id`、`client_id`、`trigger_source`、`trigger_reason`、`candidate_items`、`authority_limit_context` 必须存在。
- `candidate_items` 不能为空。
- 每个 candidate 必须能绑定至少一种可追溯 durable reference：evidence、transaction、case、entity、rule、review、intervention、governance event、lint finding 或 onboarding source。
- 如果 request 要求本节点重新分类当前交易、生成 JE、写 Transaction Log 或写 completed Case Log，输入 invalid。
- 如果 request 声称 accountant silence、LLM explanation、frequency、similarity 或 lint warning 已经等于 governance approval，输入 invalid。
- `Transaction Log` refs 只能作为 audit-facing history，不能作为 runtime rule source 或 learning authority。

Runtime-only vs durable references：

- `governance_review_request` 是 runtime-only envelope。
- `client_id`、`transaction_id`、`evidence_refs`、`entity_ids`、`rule_ids`、`case_refs`、`review_refs`、`intervention_refs`、`governance_event_refs` 是 durable references。
- 接收该 request 不授予本节点未批准 mutation authority。

### 3.2 `governance_candidate_item`

Purpose：表达单个需要治理审查的长期 authority 候选。

Source authority：提出候选的 upstream node、accountant instruction、review / intervention context、case memory update context、post-batch lint context 或 onboarding context。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `candidate_id` | 候选标识 | upstream workflow | runtime or candidate reference |
| `candidate_type` | 候选事项类型 | upstream workflow | runtime |
| `candidate_status` | 候选进入本节点时的 authority 状态 | upstream workflow / prior governance | runtime |
| `subject_refs` | 候选影响的 entity、alias、role、rule、policy、transaction、case 或 profile/tax/account-mapping refs | durable stores / upstream context | durable refs |
| `proposed_change` | 候选想改变什么 | upstream workflow / accountant instruction | runtime proposal |
| `evidence_traceability_basis` | 支撑候选的证据和追溯 basis | Evidence / Case / Transaction / Intervention / Review / Lint context | runtime object with durable refs |
| `current_memory_state_basis` | 当前长期记忆状态 | Entity / Rule / Case / Governance / Profile context | runtime view over durable authority |
| `authority_basis` | 谁有权批准或限制该候选 | accountant / governance / policy / prior restriction | runtime view over durable authority |
| `impact_basis` | 批准后会影响哪些未来 workflow 或历史解释 | upstream analysis / deterministic impact summary | runtime |

Allowed `candidate_type` values：

- `approve_alias`
- `reject_alias`
- `confirm_role`
- `create_entity_from_candidate`
- `merge_entity`
- `split_entity`
- `archive_entity`
- `change_entity_status`
- `change_automation_policy`
- `record_auto_applied_downgrade`
- `create_rule`
- `promote_rule`
- `modify_rule`
- `downgrade_rule`
- `delete_rule`
- `rule_no_promotion_restriction`
- `profile_tax_or_account_mapping_review`
- `unresolved_governance_risk`

Allowed `candidate_status` values：

- `candidate_only`
- `requires_accountant_confirmation`
- `requires_governance_review`
- `pending_governance_decision`
- `previously_deferred`
- `previously_rejected`
- `auto_applied_downgrade_already_effective`

Optional fields：

- `candidate_summary`
- `conflict_basis`
- `risk_flags`
- `prior_governance_refs`
- `grouping_key`：展示或处理分组 helper；不是 evidence 或 approval。
- `supersedes_candidate_refs`
- `related_candidate_refs`

Validation / rejection rules：

- `candidate_status` 不能是 `approved`。已批准事项应作为 prior governance context 输入，而不是待批准 candidate。
- `candidate_type` 必须与 `proposed_change` 和 `subject_refs` 匹配。
- `approve_alias` / `reject_alias` 必须包含 affected alias surface text 和相关 `entity_id` 或 candidate entity ref。
- `confirm_role` 必须包含 proposed role/context 和相关 entity ref；runtime `candidate_role` 不能直接写入 stable role。
- `merge_entity` / `split_entity` 必须列出 affected entity ids 和影响范围；不能暗示 active rules、approved aliases 或 cases 会自动迁移。
- `create_rule` / `promote_rule` / `modify_rule` / `downgrade_rule` / `delete_rule` 必须绑定 rule candidate 或 existing rule ref、applicability basis 和 accountant / governance approval requirement。
- `change_automation_policy` 如果是 upgrade 或 relaxation，必须要求 accountant approval；系统不能自动放宽。
- `record_auto_applied_downgrade` 只能表示受控自动降级已生效并需要 governance history / Review visibility，不能表达 policy upgrade。
- `profile_tax_or_account_mapping_review` 当前只可作为 review candidate，除非后续 authority 明确纳入本节点治理 mutation scope。

Runtime-only vs durable references：

- `governance_candidate_item` 本身是 runtime / candidate handoff。
- `subject_refs` 和 evidence refs 指向 durable sources。
- 候选只有在 `governance_decision_record` 记录为 approved 或 auto-applied downgrade visibility 后，才可能影响长期 authority。

### 3.3 `evidence_traceability_basis`

Purpose：说明候选依据来自哪些可追溯 source，防止治理决定建立在摘要、相似性或频率上。

Source authority：`Evidence Log`、completed transaction context、`Case Log`、`Transaction Log` audit history、`Intervention Log`、Review Node decision context、Case Memory Update candidate context、Post-Batch Lint context、Onboarding source metadata。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `supporting_source_refs` | 支持候选的 source refs | durable stores / upstream context | durable refs |
| `source_categories` | source 类型列表 | upstream packaging | runtime |
| `traceability_status` | evidence 是否足够可追溯 | deterministic validation | runtime |
| `evidence_summary` | 支撑关系的人类可读摘要 | deterministic packaging / LLM summary within bounds | runtime |

Allowed `source_categories` values：

- `evidence_log_ref`
- `transaction_log_ref`
- `case_log_ref`
- `intervention_log_ref`
- `review_decision_ref`
- `entity_log_ref`
- `rule_log_ref`
- `governance_log_ref`
- `post_batch_lint_finding_ref`
- `onboarding_source_ref`
- `accountant_instruction_ref`

Allowed `traceability_status` values：

- `sufficient`
- `insufficient`
- `conflicting`
- `missing`

Optional fields：

- `contradicting_source_refs`
- `accountant_quote_refs`
- `transaction_ids`
- `case_refs`
- `lint_finding_refs`
- `source_quality_notes`

Validation / rejection rules：

- `supporting_source_refs` 不能为空，除非候选被明确输出为 blocked due to missing traceability。
- `evidence_summary` 不能替代 `supporting_source_refs`。
- `Transaction Log` refs 只能说明历史 audit context，不能作为 runtime decision source 或 rule source。
- `traceability_status != sufficient` 时不得输出 approved durable memory change。

Runtime-only vs durable references：

- 该对象是 runtime evidence packaging。
- refs 指向 durable records；summary 不成为 durable authority。

### 3.4 `current_memory_state_basis`

Purpose：说明当前长期记忆状态、prior governance 限制和候选可能触碰的 authority 边界。

Source authority：`Entity Log`、`Rule Log`、`Case Log`、`Governance Log`、`Knowledge Log / Summary Log`、Profile。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `memory_state_refs` | 当前相关 memory refs | durable stores | durable refs |
| `memory_state_summary` | 当前状态摘要 | durable stores / deterministic packaging | runtime |
| `effective_authority_constraints` | 已生效 authority 限制 | Entity / Rule / Governance / Profile context | runtime view over durable authority |
| `memory_conflict_status` | 当前 memory 是否存在冲突 | deterministic validation / upstream context | runtime |

Allowed `memory_conflict_status` values：

- `none`
- `potential_conflict`
- `confirmed_conflict`
- `unknown`

Optional fields：

- `entity_state_snapshot`
- `alias_state_snapshot`
- `role_state_snapshot`
- `rule_state_snapshot`
- `automation_policy_snapshot`
- `profile_constraint_snapshot`
- `knowledge_summary_refs`
- `prior_governance_refs`

Validation / rejection rules：

- Knowledge Summary 与 source memory / Governance Log 冲突时，source memory / Governance Log authority wins。
- pending governance event 不能被当作 approved authority。
- rejected governance event 不能作为正向 approval basis 重用。
- 如果 current memory state 缺失到无法判断影响范围，应输出 blocked 或 refinement handoff，不得批准。

Runtime-only vs durable references：

- snapshot 和 summary 是 runtime packaging。
- Entity / Rule / Case / Governance / Profile refs 是 durable authority source。

### 3.5 `authority_basis`

Purpose：说明当前候选最多允许什么治理结果，以及 accountant / governance authority 是否已足够。

Source authority：accountant decision、Review Node decision context、Intervention Log、prior Governance Log restrictions、entity authority、rule lifecycle policy、automation policy boundary、active docs authority。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `required_authority_level` | 候选需要的 authority 层级 | product authority / governance policy | runtime |
| `available_authority_refs` | 当前可用的 approval / instruction / restriction refs | Intervention / Review / Governance context | durable refs |
| `authority_status` | 当前 authority 是否足够 | deterministic validation | runtime |
| `approval_actor_requirement` | 需要谁批准 | governance policy / candidate type | runtime |

Allowed `required_authority_level` values：

- `accountant_confirmation`
- `governance_approval`
- `system_controlled_downgrade_visibility`
- `owner_workflow_review`
- `not_approvable_from_current_context`

Allowed `authority_status` values：

- `sufficient_for_approval`
- `sufficient_for_rejection`
- `sufficient_for_auto_applied_downgrade_record`
- `insufficient`
- `ambiguous`
- `blocked_by_prior_governance`

Allowed `approval_actor_requirement` values：

- `accountant`
- `governance_owner`
- `system_controlled_downgrade`
- `profile_or_tax_or_account_mapping_owner`
- `none_candidate_only`

Optional fields：

- `accountant_id`
- `accountant_decision_ref`
- `approval_timestamp`
- `authority_notes`
- `prior_restriction_refs`

Validation / rejection rules：

- Accountant silence 不能成为 approval。
- 模糊 accountant natural-language response 不能被解释成 durable approval。
- 当前交易 correction 不自动等于长期治理 instruction。
- Rule creation / promotion / modification / deletion / downgrade 必须有 accountant / governance approval。
- Automation policy upgrade 或 relaxation 必须有 accountant approval。
- `authority_status != sufficient_for_approval` 时不得输出 approved durable memory change。

Runtime-only vs durable references：

- `authority_basis` 是 runtime authority projection。
- approval / restriction refs 指向 durable review、intervention 或 governance records。

### 3.6 `impact_and_conflict_basis`

Purpose：说明候选若被批准会影响哪些 downstream behavior，并保留冲突，不让 LLM 或 grouping 把冲突抹平。

Source authority：upstream impact analysis、Entity / Rule / Case / Governance / Transaction history context、Post-Batch Lint context。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `affected_workflow_areas` | 候选可能影响的 workflow 区域 | upstream analysis / deterministic packaging | runtime |
| `affected_memory_refs` | 可能被影响的 memory refs | durable stores | durable refs |
| `impact_clarity_status` | 影响范围是否清楚 | deterministic validation / semantic summary within bounds | runtime |
| `conflict_status` | 是否存在未解决冲突 | deterministic validation / upstream context | runtime |

Allowed `affected_workflow_areas` values：

- `future_entity_resolution`
- `future_rule_match`
- `future_case_judgment`
- `case_to_rule_eligibility`
- `automation_policy`
- `knowledge_compilation`
- `post_batch_lint_monitoring`
- `review_display`
- `audit_explanation`
- `profile_tax_or_account_mapping_review`

Allowed `impact_clarity_status` values：

- `clear`
- `partial`
- `unclear`

Allowed `conflict_status` values：

- `none`
- `potential_conflict`
- `unresolved_conflict`
- `resolved_by_accountant_decision`
- `blocked_by_conflict`

Optional fields：

- `conflicting_evidence_refs`
- `conflicting_case_refs`
- `conflicting_rule_refs`
- `conflicting_transaction_log_refs`
- `conflicting_governance_refs`
- `suggested_refinement_focus`

Validation / rejection rules：

- `impact_clarity_status != clear` 时不得批准 entity merge/split、rule lifecycle change 或 automation policy relaxation。
- `conflict_status` 为 `unresolved_conflict` 或 `blocked_by_conflict` 时不得批准 durable memory change。
- 冲突影响 historical audit explanation 时，不得重写 historical `Transaction Log`，只能通过 governance history 解释后续变化。

Runtime-only vs durable references：

- 该对象是 runtime impact / conflict packaging。
- conflict refs 指向 durable records，但不改变这些 records。

## 4. Output Contracts

### 4.1 `governance_decision_record`

Purpose：记录治理候选被批准、拒绝、暂缓、退回、阻断、限制，或记录受控系统自动降级已生效的 durable governance history。

Consumer / downstream authority：`Governance Log`、Knowledge Compilation、Post-Batch Lint、Review display、future Entity Resolution / Rule Match / Case Judgment authority context。

Required fields：

| Field | Meaning | Authority | Durable effect |
| --- | --- | --- | --- |
| `event_id` | 单次治理动作主键 | Governance Review Node / governance workflow | durable governance record id |
| `event_type` | 治理事件类型 | candidate type + approved decision | durable governance classification |
| `client_id` | 客户引用 | request context | durable reference |
| `source_candidate_id` | 来源候选 | upstream candidate | durable reference if persisted |
| `source` | 事件来源 | upstream request | durable metadata |
| `decision_status` | 本节点对候选的正式处理结果 | accountant / governance / system downgrade boundary | durable governance state |
| `requires_accountant_approval` | 是否需要 accountant approval | candidate type / governance policy | durable metadata |
| `authority_refs` | 支撑该 decision 的 approval / restriction refs | Review / Intervention / Governance context | durable references |
| `reason` | 决定原因 | accountant / governance decision or bounded summary | durable explanation |
| `evidence_links` | 支撑或解释该治理事件的 evidence refs | Evidence / Case / Transaction / Intervention / Review context | durable references |
| `created_at` | 事件创建时间 | workflow clock | durable metadata |

Allowed `event_type` values：

- `approve_alias`
- `reject_alias`
- `confirm_role`
- `create_entity_from_candidate`
- `merge_entity`
- `split_entity`
- `archive_entity`
- `change_entity_status`
- `change_automation_policy`
- `record_auto_applied_downgrade`
- `create_rule`
- `promote_rule`
- `modify_rule`
- `downgrade_rule`
- `delete_rule`
- `rule_no_promotion_restriction`
- `profile_tax_or_account_mapping_review`
- `unresolved_governance_risk`

Allowed `decision_status` values：

- `approved`
- `rejected`
- `deferred`
- `returned_for_clarification`
- `blocked`
- `auto_applied_downgrade_recorded`

Allowed `approval_status` values：

- `pending`
- `approved`
- `rejected`
- `auto_applied_downgrade`

Optional fields：

- `approval_status`：active `entity_governance_event` 使用的审批状态；entity-related event 必填。
- `resolved_at`
- `accountant_id`
- `entity_ids`
- `rule_ids`
- `case_refs`
- `transaction_ids`
- `affected_aliases`
- `affected_roles`
- `old_value`
- `new_value`
- `policy_change_direction`
- `restriction_scope`
- `supersedes_event_refs`
- `related_event_refs`
- `downstream_visibility`

Allowed `policy_change_direction` values：

- `downgrade`
- `upgrade`
- `relaxation`
- `restriction`
- `no_change_visibility_only`

Validation rules：

- `event_id` 是治理动作主键；`entity_ids`、`rule_ids` 或 `transaction_ids` 只能作为查询索引或 affected refs。
- Entity-related `governance_decision_record` 必须包含 `approval_status`，以对齐 active baseline 的 `entity_governance_event` 最小字段。
- `approved` 必须有 `authority_refs` 且 `authority_status = sufficient_for_approval`。
- `rejected` / `deferred` / `returned_for_clarification` / `blocked` 必须保留 reason。
- `auto_applied_downgrade_recorded` 只能用于系统受控降级已生效的 visibility / history；不能用于 upgrade 或 relaxation。
- Entity-related event 至少应能按 `event_id`、`entity_id`、`decision_status`、`event_type` 查询；若关联 transaction / case，也应能按对应引用查询。
- `merge_entity` / `split_entity` 的 record 不能声明 active rules、approved aliases 或 historical cases 已自动迁移，除非对应迁移也有明确 accountant / governance authority。
- `decision_status = approved` 不等于当前交易 accounting approval，也不重写 historical `Transaction Log`。

Durable memory effect：

- durable governance history。
- 只有 `approved` 或 `auto_applied_downgrade_recorded` 可以影响 future authority，但具体 memory mutation execution locus 尚未冻结。
- `rejected`、`deferred`、`returned_for_clarification` 和 `blocked` 只能作为治理历史、future warning、knowledge / lint context 或再审 context。

### 4.2 `authorized_memory_change_handoff`

Purpose：在治理 decision 已足够授权时，表达哪些长期记忆或 automation authority 可以被改变。

Consumer / downstream authority：负责 durable memory mutation 的 owner workflow / memory update layer、Entity Log / Rule Log / Profile owner context、future runtime authority projection。

Required fields：

| Field | Meaning | Authority |
| --- | --- | --- |
| `handoff_id` | 授权 mutation handoff 标识 | Governance Review runtime |
| `governance_event_id` | 对应 approved governance event | `governance_decision_record` |
| `mutation_target` | 允许改变的 durable target 类别 | approved governance decision |
| `authorized_change_type` | 允许改变的动作 | approved governance decision |
| `target_refs` | 受影响 memory refs | durable stores |
| `authorized_old_value` | 授权前值或 expected current value | current memory state basis |
| `authorized_new_value` | 授权后值 | approved governance decision |
| `authority_refs` | 支撑授权的 refs | governance decision / accountant approval |

Allowed `mutation_target` values：

- `entity_log`
- `rule_log`
- `governance_log_projection`
- `profile_or_tax_or_account_mapping_owner_workflow`

Allowed `authorized_change_type` values：

- `approve_alias`
- `reject_alias`
- `confirm_role`
- `create_stable_entity`
- `merge_entity`
- `split_entity`
- `archive_entity`
- `change_entity_status`
- `change_automation_policy`
- `create_rule`
- `promote_rule`
- `modify_rule`
- `downgrade_rule`
- `delete_rule`
- `record_restriction`

Optional fields：

- `effective_at`
- `migration_constraints`
- `do_not_migrate_refs`
- `post_change_review_visibility`
- `knowledge_compilation_hint`
- `post_batch_lint_monitoring_hint`

Validation rules：

- 必须引用 `decision_status = approved` 的 `governance_event_id`，除非是 `record_auto_applied_downgrade` 对应的已生效降级记录。
- `change_automation_policy` 如果方向是 `upgrade` 或 `relaxation`，必须有 accountant approval refs。
- Rule lifecycle change 必须有 accountant / governance approval refs。
- `new_entity_candidate` 只有通过 `create_stable_entity` 授权后，才可能成为 stable entity authority。
- `candidate_alias` 只有通过 `approve_alias` 授权后，才可能支持 future rule match。
- `candidate_role` 只有通过 `confirm_role` 授权后，才可能成为 stable role。
- `merge_entity` 不得删除旧 `entity_id`；旧 entity 应进入 governed lifecycle state，并通过治理事件解释后续关系。
- `split_entity` 不得自动全量迁移 historical cases；只能迁移 accountant 明确确认的案例。

Durable memory effect：

- 这是 authorized durable-memory change handoff。
- 本 Stage 3 不冻结本节点是直接执行 mutation，还是把该 handoff 交给专门 memory update workflow。

### 4.3 `governance_blocked_handoff`

Purpose：安全阻止候选被批准，说明阻断原因和需要返回的 resolution path。

Consumer / downstream authority：Review Node、Coordinator / Pending Node、Case Memory Update Node、Post-Batch Lint Node、upstream owner workflow、human governance review。

Required fields：

- `blocked_handoff_id`
- `source_candidate_id`
- `block_reason`
- `blocked_refs`
- `required_resolution_path`

Allowed `block_reason` values：

- `missing_evidence_traceability`
- `insufficient_authority`
- `ambiguous_accountant_instruction`
- `current_transaction_not_finalized`
- `impact_scope_unclear`
- `unresolved_conflict`
- `blocked_by_prior_governance`
- `candidate_type_out_of_scope`
- `profile_tax_or_account_mapping_owner_required`

Allowed `required_resolution_path` values：

- `return_to_review_node`
- `return_to_coordinator_pending_node`
- `return_to_case_memory_update_node`
- `return_to_post_batch_lint_node`
- `return_to_upstream_owner_workflow`
- `request_accountant_governance_decision`
- `defer_until_more_evidence`

Optional fields：

- `suggested_clarification_question`
- `missing_refs`
- `conflict_summary`
- `risk_flags`

Validation rules：

- Blocked handoff 不能包含 approved event、authorized mutation 或 durable memory write claim。
- 如果原因是 authority / governance，不得伪装成 ordinary missing field。
- `suggested_clarification_question` 只能聚焦问题，不能替 accountant 作答。

Durable memory effect：

- runtime-only handoff。
- 可被下游记录为 intervention / review / governance context，但本对象本身不是 approval。

### 4.4 `candidate_refinement_handoff`

Purpose：表达候选需要合并、拆分、去重、补证据、澄清业务含义或重新绑定 subject refs 后才能正式批准或拒绝。

Consumer / downstream authority：Review Node、Post-Batch Lint Node、Case Memory Update Node、workflow orchestrator、human governance review。

Required fields：

- `refinement_handoff_id`
- `source_candidate_ids`
- `refinement_need`
- `affected_refs`
- `required_next_review_scope`

Allowed `refinement_need` values：

- `group_candidates_by_business_meaning`
- `split_candidate_into_separate_events`
- `deduplicate_candidate_refs`
- `attach_missing_evidence_refs`
- `clarify_accountant_intent`
- `clarify_impact_scope`
- `resolve_memory_conflict`

Optional fields：

- `suggested_grouping_key`
- `candidate_relationship_summary`
- `proposed_refinement_notes`

Validation rules：

- Grouping、dedup 或 LLM semantic summary 不能把多个弱信号自动变成 strong authority。
- `suggested_grouping_key` 不能作为 evidence、approval 或 mutation key。
- refinement handoff 不能包含 `decision_status = approved`。

Durable memory effect：

- runtime-only / candidate-only。
- 是否持久保存为 candidate queue item 尚未冻结；即使持久保存，也不是 `Governance Log` approval。

### 4.5 `knowledge_lint_handoff`

Purpose：把治理结果、未解决风险、rejected / deferred context 或 auto-applied downgrade visibility 交给知识摘要和批后监控。

Consumer / downstream authority：`Knowledge Compilation Node`、`Post-Batch Lint Node`、Review display。

Required fields：

- `handoff_id`
- `handoff_type`
- `source_governance_event_refs`
- `summary_for_downstream`
- `authority_effect`

Allowed `handoff_type` values：

- `approved_governance_summary`
- `rejected_governance_summary`
- `deferred_governance_summary`
- `unresolved_governance_risk`
- `auto_applied_downgrade_visibility`
- `post_change_monitoring_hint`

Allowed `authority_effect` values：

- `future_runtime_authority_changed`
- `history_only_no_runtime_authority`
- `candidate_only_no_authority`
- `monitoring_required`

Optional fields：

- `affected_entity_ids`
- `affected_rule_ids`
- `affected_case_refs`
- `review_visibility_note`
- `lint_monitoring_focus`

Validation rules：

- Knowledge handoff 不是 Knowledge Summary 本身。
- Lint handoff 不是 governance approval。
- Knowledge Summary 和 lint finding 不能成为 deterministic rule source。
- `authority_effect = future_runtime_authority_changed` 必须引用 approved governance event 或 auto-applied downgrade record。

Durable memory effect：

- runtime-only downstream handoff。
- 下游是否写 `Knowledge Log / Summary Log` 或 lint follow-up 由对应节点 contract 决定。

## 5. Field Authority and Memory Boundary

### 5.1 Source of truth for important fields

- `transaction_id`：Transaction Identity Node / transaction identity layer。
- `evidence_refs`：`Evidence Log`。
- `entity_id`、alias state、role state、entity lifecycle status、automation_policy：`Entity Log` as governed by approved `Governance Log` events。
- `case_refs`、completed-case precedent、accountant correction context：`Case Log` / review-confirmed case memory authority。
- `rule_id`、active rule、rule lifecycle、rule conditions：`Rule Log` as governed by accountant / governance approval。
- `Transaction Log` refs：audit-facing finalized history only，不参与 runtime decision 或 learning。
- `Intervention Log` / Review refs：accountant question、answer、correction、confirmation、approval 或 objection 的 source。
- `Governance Log` / `governance_decision_record`：高权限长期记忆变化及审批状态的 source。
- `Knowledge Log / Summary Log`：可读摘要 source，不是 deterministic rule source。
- Profile / tax config / account-mapping context：对应 owner workflow / Profile / tax config authority；本节点是否可直接治理 mutation 尚未冻结。

### 5.2 Fields that can never become durable memory by this node

以下内容不能由本节点直接变成 stable Entity / Case / Rule / Profile memory：

- `governance_review_request`
- `governance_candidate_item`
- `request_summary`
- `candidate_summary`
- `evidence_summary`
- `memory_state_summary`
- `impact_basis` summary
- `conflict_basis` summary
- `grouping_key`
- `suggested_grouping_key`
- `runtime_trace`
- LLM-generated explanation
- lint finding
- review draft
- current transaction correction without explicit long-term governance instruction

这些内容最多可作为治理审查 context、review / intervention context、candidate-only handoff 或 durable governance record 的 explanation。

### 5.3 Fields that can become durable only after accountant / governance approval

以下内容可以成为 long-term authority，但只能通过 accountant / governance-approved path：

- `new_entity_candidate` → stable entity。
- `candidate_alias` → approved alias。
- `candidate_role` → confirmed stable role。
- merge / split candidate → governed entity merge / split event。
- rule candidate → active rule。
- rule modification / downgrade / deletion → changed rule lifecycle。
- automation policy upgrade / relaxation → changed automation authority。
- no-promotion restriction or automation restriction → durable governance restriction。

系统受控 automation policy downgrade 可以立即生效，但必须写入 governance history，状态为 auto-applied downgrade visibility / record，不得被包装成 accountant-approved upgrade。

### 5.4 Audit vs learning / logging boundary

`Transaction Log` 是 audit-facing final history，只写和查询，不参与本节点 runtime decision，也不是 learning layer 或 rule source。

`Governance Log` 解释后续长期 authority 为什么变化，但不重写 historical `Transaction Log`。

`Case Judgment Node`、`Case Memory Update Node`、`Review Node`、`Post-Batch Lint Node` 和 `Transaction Logging Node` 都可以产生治理候选信号，但候选信号本身不创造 durable authority。

## 6. Validation Rules

### 6.1 Contract-level validation rules

- 每个 governance candidate 必须有 `candidate_type`、`subject_refs`、`proposed_change`、`evidence_traceability_basis`、`current_memory_state_basis`、`authority_basis` 和 `impact_basis`。
- Candidate 不得用 `Log` 命名，除非它已经写入 active baseline 定义的 durable `Governance Log`。
- `authority_basis` 必须先于 durable change validation；authority 不足时不得批准。
- `traceability_status` 必须足够；不能用 confidence、frequency、similarity 或 natural-language summary 填补证据链。
- `impact_clarity_status` 必须足够；影响范围不明时不能批准会影响 future runtime authority 的变化。
- conflict 必须保留；LLM 不得替 accountant 在冲突中选择 durable authority。
- 所有 approved rule lifecycle change 必须引用 accountant / governance approval。
- 所有 automation policy upgrade / relaxation 必须引用 accountant approval。
- 所有 entity merge / split 必须通过治理流程，并保留 governance event。

### 6.2 Conditions that make the input invalid

输入 invalid，如果：

- 请求本节点执行当前交易分类、COA 选择、HST/GST treatment 判断、JE generation 或 Transaction Log final write。
- 候选没有 subject refs 或 evidence / review / intervention / memory refs。
- accountant response 模糊、沉默或只表达当前交易 correction，却被标为 long-term approval。
- `candidate_status = approved` 却作为待审 candidate 输入。
- request 把 Transaction Log history 当成 runtime decision source、learning source 或 rule source。
- request 把 `new_entity_candidate`、candidate alias、candidate role、candidate rule 或 lint finding 当成 durable authority。

### 6.3 Conditions that make the output invalid

输出 invalid，如果：

- `governance_decision_record.decision_status = approved` 但缺少 authority refs。
- approved event 缺少 evidence links 或 reason。
- `authorized_memory_change_handoff` 未引用 approved governance event。
- `authorized_memory_change_handoff` 尝试改变 target 外的 durable store，或把 profile / tax / account-mapping change 当作本节点已冻结 mutation scope。
- merge / split 输出声称自动迁移 active rules、approved aliases 或 all historical cases。
- output 声称重写 historical `Transaction Log`。
- output 声称 governance approval 已批准当前交易 accounting outcome。
- candidate refinement 或 blocked handoff 包含 approved mutation。

### 6.4 Stop / ask conditions for unresolved contract authority

必须 stop / ask，而不是写成 final contract，如果当前任务要求：

- 冻结 Governance Review 是否直接执行 durable memory mutation。
- 冻结 Review Node 与 Governance Review Node 在 accountant approval capture 上的 exact split。
- 冻结 profile / tax config / account-mapping change 是否属于本节点直接治理 mutation scope。
- 冻结 rule promotion eligibility threshold、queue ranking、dedup、expiry、reopen 或 supersession behavior。
- 冻结 entity merge / split 后 cases、aliases、roles、rules 的完整 migration algorithm。

## 7. Examples

### 7.1 Valid minimal example

```json
{
  "governance_review_request_id": "gov_req_001",
  "client_id": "client_abc",
  "batch_id": "batch_2026_05",
  "trigger_source": "review_node",
  "trigger_reason": "alias_authority_candidate",
  "candidate_items": [
    {
      "candidate_id": "cand_alias_001",
      "candidate_type": "approve_alias",
      "candidate_status": "requires_accountant_confirmation",
      "subject_refs": {
        "entity_ids": ["ent_tim_hortons"],
        "affected_aliases": ["TIMS COFFEE-1234"]
      },
      "proposed_change": {
        "alias_status": "approved_alias"
      },
      "evidence_traceability_basis": {
        "supporting_source_refs": ["ev_001", "review_decision_001"],
        "source_categories": ["evidence_log_ref", "review_decision_ref"],
        "traceability_status": "sufficient",
        "evidence_summary": "Accountant confirmed this bank surface text refers to Tim Hortons."
      },
      "current_memory_state_basis": {
        "memory_state_refs": ["ent_tim_hortons"],
        "memory_state_summary": "Alias is currently candidate-only.",
        "effective_authority_constraints": [],
        "memory_conflict_status": "none"
      },
      "authority_basis": {
        "required_authority_level": "accountant_confirmation",
        "available_authority_refs": ["review_decision_001"],
        "authority_status": "sufficient_for_approval",
        "approval_actor_requirement": "accountant"
      },
      "impact_basis": {
        "affected_workflow_areas": ["future_entity_resolution", "future_rule_match"],
        "affected_memory_refs": ["ent_tim_hortons"],
        "impact_clarity_status": "clear",
        "conflict_status": "none"
      }
    }
  ],
  "authority_limit_context": {
    "max_result": "approve_alias_or_reject_alias"
  }
}
```

Valid output：

```json
{
  "governance_decision_record": {
    "event_id": "gov_evt_001",
    "event_type": "approve_alias",
    "client_id": "client_abc",
    "source_candidate_id": "cand_alias_001",
    "source": "review_node",
    "decision_status": "approved",
    "approval_status": "approved",
    "requires_accountant_approval": true,
    "authority_refs": ["review_decision_001"],
    "reason": "Accountant confirmed the alias belongs to the existing entity.",
    "evidence_links": ["ev_001", "review_decision_001"],
    "created_at": "2026-05-06T10:00:00Z",
    "entity_ids": ["ent_tim_hortons"],
    "affected_aliases": ["TIMS COFFEE-1234"],
    "old_value": "candidate_alias",
    "new_value": "approved_alias"
  },
  "authorized_memory_change_handoff": {
    "handoff_id": "auth_mut_001",
    "governance_event_id": "gov_evt_001",
    "mutation_target": "entity_log",
    "authorized_change_type": "approve_alias",
    "target_refs": ["ent_tim_hortons"],
    "authorized_old_value": "candidate_alias",
    "authorized_new_value": "approved_alias",
    "authority_refs": ["review_decision_001"]
  }
}
```

### 7.2 Valid richer example

```json
{
  "candidate_id": "cand_policy_007",
  "candidate_type": "record_auto_applied_downgrade",
  "candidate_status": "auto_applied_downgrade_already_effective",
  "subject_refs": {
    "entity_ids": ["ent_home_depot"],
    "policy": "automation_policy"
  },
  "proposed_change": {
    "old_value": "eligible",
    "new_value": "case_allowed_but_no_promotion",
    "policy_change_direction": "downgrade"
  },
  "evidence_traceability_basis": {
    "supporting_source_refs": ["lint_finding_044", "case_101", "case_118"],
    "source_categories": ["post_batch_lint_finding_ref", "case_log_ref"],
    "traceability_status": "sufficient",
    "evidence_summary": "Post-batch lint found repeated mixed-use corrections."
  },
  "authority_basis": {
    "required_authority_level": "system_controlled_downgrade_visibility",
    "available_authority_refs": ["lint_finding_044"],
    "authority_status": "sufficient_for_auto_applied_downgrade_record",
    "approval_actor_requirement": "system_controlled_downgrade"
  },
  "impact_basis": {
    "affected_workflow_areas": ["future_case_judgment", "case_to_rule_eligibility", "post_batch_lint_monitoring"],
    "affected_memory_refs": ["ent_home_depot"],
    "impact_clarity_status": "clear",
    "conflict_status": "none"
  }
}
```

Reason valid：这是受控自动降级 visibility，不是 automation policy upgrade / relaxation；它需要治理历史和 Review visibility，但不需要伪装成 accountant approval。

### 7.3 Invalid example

```json
{
  "candidate_id": "cand_rule_009",
  "candidate_type": "promote_rule",
  "candidate_status": "requires_governance_review",
  "subject_refs": {
    "entity_ids": ["ent_new_vendor"],
    "candidate_rule_id": "rule_cand_009"
  },
  "proposed_change": {
    "rule_status": "active"
  },
  "evidence_traceability_basis": {
    "supporting_source_refs": ["case_301", "case_302"],
    "source_categories": ["case_log_ref"],
    "traceability_status": "sufficient",
    "evidence_summary": "Two similar cases had same classification."
  },
  "authority_basis": {
    "required_authority_level": "governance_approval",
    "available_authority_refs": [],
    "authority_status": "insufficient",
    "approval_actor_requirement": "accountant"
  }
}
```

Invalid reason：repeated cases 不等于 rule promotion approval；active rule change 必须有 accountant / governance approval。该候选最多输出 `governance_blocked_handoff` 或 `candidate_refinement_handoff`，不能输出 approved rule mutation。

## 8. Open Contract Boundaries

- Governance Review 与 Review Node 对 accountant approval capture、formal governance approval 和 durable mutation execution 的 exact split 仍未冻结。
- Approved governance change 是由本节点直接执行 durable mutation，还是由专门 memory update workflow 执行，仍未冻结。
- Governance candidate queue、grouping、dedup、expiry、reopen、supersession 和 retry behavior 仍未冻结。
- Profile / tax config / account-mapping candidate 是否属于本节点直接治理 mutation scope 仍未冻结；当前 contract 只允许 candidate / owner workflow review handoff。
- Rule promotion / modification / downgrade 的 exact eligibility threshold、condition schema 和 rule-health contract 仍未冻结。
- Entity merge / split 后 cases、aliases、roles、rules 和 future matching 的完整 migration algorithm 仍未冻结。
- Rejected / deferred governance decision 对 future runtime warning、Knowledge Summary 和 Post-Batch Lint 的 exact expression 仍未冻结。

## 9. Self-Review

- 已阅读 required docs：`AGENTS.md`、`TASK_STATE.md`、`PLANS.md`、`CLAUDE.md`、`DECISIONS.md`、`supporting documents/communication_preferences.md`、`supporting documents/development_workflow.md`、`supporting documents/node_design_roadmap.md`、`new system/new_system.md`。
- 已阅读本节点 prior approved docs：Stage 1 functional intent、Stage 2 logic and boundaries。
- 已读取可用 Superpowers docs：`using-superpowers/SKILL.md`、`brainstorming/SKILL.md`；project workflow skill `ai-bookkeeper-node-design-facilitation` 在当前环境不存在，因此按 runner instruction 使用 repo `supporting documents/node_design_roadmap.md` 与本节点 Stage 1/2 docs 作为 workflow authority。
- 已确认 optional `supporting documents/node_design_roadmap_zh.md` 在 working tree 中缺失；未发明或引用该文件内容。
- 本文件保持 Stage 3 data contract 范围：定义 input / output contracts、field authority、memory boundary、validation rules 和 compact examples。
- 未定义 Stage 4 execution algorithm、Stage 5 implementation map、Stage 6 test matrix、Stage 7 coding-agent task contract。
- 未把 candidate、review draft、lint finding、queue 或 runtime trace 称为 `Log`。
- 未把 `Transaction Log` 变成 runtime decision、learning 或 rule source。
- 未发明 unsupported product authority；未修改 `new_system.md`、Stage 1/2 docs、governance docs 或其他 repo 文件。
