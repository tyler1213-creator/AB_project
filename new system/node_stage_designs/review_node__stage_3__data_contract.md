# Review Node — Stage 3：Data Contract Spec

## 1. Stage 范围

本 Stage 3 只定义 `Review Node` 的 implementation-facing data contracts。

前置设计依据是：

- `new system/node_stage_designs/review_node__stage_1__functional_intent.md`
- `new system/node_stage_designs/review_node__stage_2__logic_and_boundaries.md`

本文件把 Stage 1/2 已批准的 Review Node 行为边界转换为输入对象、输出对象、字段含义、字段 authority、runtime-only / durable-memory 边界和 validation rules。

本文件不定义：

- step-by-step execution algorithm 或 branch sequence
- repo module path、class、API、storage engine、DB migration 或 code file layout
- test matrix、fixture plan 或 coding-agent task contract
- JE Generation、Transaction Logging、Case Memory Update 或 Governance Review 的完整下游 schema
- Review UI / prompt structure / display ordering
- 新 product authority 或 legacy replacement mapping

## 2. Contract Position in Workflow

`Review Node` 位于 accountant-facing review gate：

```text
upstream workflow results / pending returns / candidate signals
→ Review Node
→ accountant decision capture
→ JE Generation / Transaction Logging / Case Memory Update / Governance Review / Coordinator
```

### 2.1 Upstream handoff consumed

本节点消费 runtime `review_package_request`。

该 handoff 表示：

- upstream workflow 已形成可追溯 evidence、稳定 `transaction_id`、system result、pending clarification result、review-required context 或 governance / memory candidate；
- 当前事项需要 accountant 审核、批准、修正、拒绝或继续 pending；
- 当前事项尚未进入 JE finalization、final Transaction Log write 或 durable governance mutation execution。

### 2.2 Downstream handoff produced

本节点输出 `review_decision_package`，供下游 workflow 消费：

- `JE Generation Node`：只消费 accountant-approved 或 accountant-corrected current outcome handoff。
- `Transaction Logging Node`：消费 finalizable current outcome 与 review trace reference；本节点不写 `Transaction Log`。
- `Case Memory Update Node`：消费 accountant-confirmed outcome、correction context 和候选信号；本节点不写 `Case Log`。
- `Governance Review Node`：消费 entity / alias / role / rule / automation-policy / merge-split 等候选和 review context；本节点不批准或执行 governance mutation。
- `Coordinator / Pending Node`：消费 still-pending、clarification-needed 或 unresolved-review handoff。

### 2.3 Logs / memory stores read

本节点可以读取或消费：

- `Evidence Log` references 和 current evidence basis；
- stable transaction identity references；
- upstream outputs and rationale from Profile / Structural Match、Entity Resolution、Rule Match、Case Judgment、Coordinator / Pending、Post-Batch Lint；
- `Profile`、`Entity Log`、`Case Log`、`Rule Log`、`Governance Log` 中与当前 review item 有关的 authority limits、risk flags、policy constraints、candidate state 和已生效治理 context；
- `Intervention Log` 中与当前交易、批次或候选事项有关的 accountant questions、answers、corrections、confirmations、objections 和 prior review context；
- `Knowledge Log / Summary Log` 中可读摘要，但只能作为 review context；
- 既有 finalized `Transaction Log` history，但只能作为 audit-facing 历史参考，不能作为当前 runtime decision、rule source、case memory 或 learning authority。

### 2.4 Logs / memory stores written or candidate-only

本节点可以写入或形成等价 durable handoff 的唯一长期记录类别是 review / intervention 语义记录：

- accountant review action
- accountant approval / correction / rejection / confirmation / objection / still-pending explanation
- review package 被批准、修正、拒绝或退回的 reason / trace

这些记录属于 `Intervention Log` / review interaction 语义，不等于 final `Transaction Log`、`Case Log`、`Rule Log`、stable `Entity Log` 或 approved `Governance Log` mutation。

本节点只能 candidate-only 输出：

- supplemental evidence / reprocessing candidate
- profile change or profile confirmation candidate
- entity / alias / role candidate
- case memory update candidate
- rule candidate / rule conflict / rule-health candidate
- automation-policy / governance candidate
- merge / split candidate
- still-pending or unresolved-review signal

本节点绝不能直接写入或修改：

- `Transaction Log`
- `Profile`
- stable `Entity Log` authority
- `Case Log`
- `Rule Log`
- approved `Governance Log` mutation
- journal entry

## 3. Input Contracts

### 3.1 `review_package_request`

Purpose：Review Node 的 runtime input envelope，把一组需要 accountant-facing review 的交易结果、pending 回收结果、候选事项或批次语境放入同一审核边界。

Source authority：workflow orchestrator / upstream nodes。该对象只汇总上游已形成的 runtime facts、evidence references、authority limits 和 candidate signals，不创造 accountant approval。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `review_package_id` | 本次 review package 的 runtime 标识 | workflow runtime | runtime-only，可被 review record 引用 |
| `client_id` | 当前客户引用 | client / batch context | durable reference |
| `batch_id` | 当前处理批次引用 | workflow runtime | runtime reference |
| `review_scope` | package 覆盖范围 | workflow orchestrator | runtime |
| `trigger_reasons` | 为什么需要 Review Node | upstream nodes / orchestrator | runtime |
| `review_items` | 待审核 item 列表 | upstream handoff | runtime list with durable refs |
| `authority_limit_context` | 本 package 最多允许产生的后续结果 | policy / governance / upstream constraints | runtime view over durable authority |

Allowed `review_scope` values：

- `single_transaction`
- `transaction_batch`
- `governance_candidate_batch`
- `mixed_review_package`

Allowed `trigger_reasons` values：

- `current_outcome_requires_review`
- `pending_clarification_returned`
- `accountant_requested_review`
- `review_required_policy`
- `conflicting_evidence`
- `authority_risk`
- `governance_candidate_visibility`
- `post_batch_lint_candidate`
- `batch_review_policy`

Optional fields：

- `package_summary_context`：给 accountant 的 package-level 摘要 context；不是 approval。
- `related_intervention_refs`：与本 package 有关的 prior intervention references。
- `request_trace`：runtime diagnostics / orchestration trace。

Validation / rejection rules：

- `review_package_id`、`client_id`、`batch_id`、`review_scope`、`trigger_reasons`、`review_items`、`authority_limit_context` 必须存在。
- `review_items` 不能为空。
- `trigger_reasons` 必须至少有一个 allowed value。
- 如果 package 声称某 item 已经 final logged 或 governance mutation 已执行，本节点输入 invalid；Review Node 不能作为 runtime decision source 重开最终记录。
- `request_trace` 不能作为 accountant approval、accounting authority、rule authority 或 governance authority。

Runtime-only vs durable references：

- `review_package_request` 是 runtime-only。
- `client_id`、`batch_id`、`transaction_id`、`evidence_refs`、memory refs、governance refs 是 durable references。
- 收到该 package 不给 Review Node 任何长期 memory mutation authority。

### 3.2 `review_item`

Purpose：表达 package 内单个需要审核的交易、候选事项、批次风险或 mixed item。

Source authority：upstream workflow handoff。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `review_item_id` | package 内 item 标识 | workflow runtime | runtime-only，可被 review record 引用 |
| `item_type` | item 类型 | upstream handoff | runtime |
| `item_subject_refs` | item 绑定的交易、candidate、entity、rule、evidence 或 batch refs | upstream nodes / durable stores | durable refs |
| `review_need` | 为什么需要 accountant decision 或 visibility | upstream rationale | runtime |
| `review_question` | accountant 需要决定或确认的问题 | deterministic packaging / LLM summary within bounds | runtime |
| `source_context` | item 来自哪个 upstream node 或 workflow | upstream handoff | runtime |
| `authority_limits` | 该 item 允许输出的 decision 上限 | governance / policy / upstream constraints | runtime view over durable authority |

Allowed `item_type` values：

- `current_transaction_outcome`
- `transaction_correction_review`
- `still_pending_review`
- `evidence_conflict_review`
- `case_memory_candidate_review`
- `entity_candidate_review`
- `alias_candidate_review`
- `role_candidate_review`
- `rule_candidate_review`
- `automation_policy_candidate_review`
- `merge_split_candidate_review`
- `batch_review_summary`

Optional fields：

- `transaction_outcome_context`
- `evidence_review_context`
- `intervention_context`
- `candidate_governance_context`
- `batch_review_context`
- `risk_flags`
- `display_group_key`：review presentation grouping helper；不是 authority。

Validation / rejection rules：

- 每个 `review_item` 必须能绑定到具体 `transaction_id`、candidate id、entity/rule ref、evidence ref 或 batch ref；不能只有自然语言摘要。
- `review_question` 不能要求 accountant 批准一个 authority_limits 明确禁止的结果。
- `item_type` 与附带 context 必须匹配；例如 `current_transaction_outcome` 必须带 `transaction_outcome_context`。
- `display_group_key` 只能用于展示分组，不能作为去重、approval 或 governance authority。

Runtime-only vs durable references：

- `review_item` 是 runtime-only。
- `item_subject_refs` 中的 durable refs 只能被引用，不表示本节点拥有写入权。

### 3.3 `transaction_outcome_context`

Purpose：描述当前交易已经形成的 system result、accountant clarification result 或 review-required outcome claim，供 accountant 审核当前交易是否可进入 finalization。

Source authority：Profile / Structural Match、Rule Match、Case Judgment、Coordinator / Pending 或其他 approved upstream handoff。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `transaction_id` | 稳定交易身份 | Transaction Identity Node | durable reference |
| `outcome_context_id` | 当前 outcome context 标识 | upstream node / workflow runtime | runtime |
| `outcome_source_path` | 当前 outcome 来自哪条 workflow path | upstream node | runtime |
| `outcome_review_state` | outcome 进入 review 时的状态 | upstream node / orchestrator | runtime |
| `current_outcome_payload` | 当前交易处理结果 payload | upstream node | runtime object with durable refs |
| `upstream_rationale_refs` | 支撑该 outcome 的 rationale / trace refs | upstream nodes | runtime / durable refs |
| `evidence_refs` | accountant 审核必须能回溯的 evidence refs | Evidence Log / upstream nodes | durable references |

Allowed `outcome_source_path` values：

- `profile_structural_match`
- `rule_match`
- `case_judgment`
- `coordinator_pending_return`
- `manual_review_context`
- `post_batch_rework`

Allowed `outcome_review_state` values：

- `ready_for_accountant_review`
- `review_required_by_policy`
- `pending_clarification_returned`
- `conflict_requires_review`
- `not_approved_prior_result`
- `blocked_from_finalization`

Required fields inside `current_outcome_payload`：

- `accounting_outcome_type`：当前结果类型；allowed values: `classification_result`, `structural_result`, `correction_result`, `no_final_outcome_yet`。
- `accounting_outcome_summary`：给 accountant 和 downstream handoff 使用的简短结果摘要。
- `finalization_readiness`：该 outcome 在当前 authority 下是否理论上可被 accountant approval 推入下游；allowed values: `finalizable_if_approved`, `requires_correction`, `not_finalizable`, `governance_only`。
- `source_authority`：说明该 payload 来自哪个 upstream result、accountant clarification 或 policy context。

Optional fields inside `current_outcome_payload`：

- `coa_account_ref`
- `hst_gst_treatment`
- `amount_allocation`
- `business_context`
- `entity_ref`
- `rule_ref`
- `case_refs`
- `policy_or_risk_trace_refs`
- `unresolved_fields`

Validation / rejection rules：

- 缺少 `transaction_id`、`current_outcome_payload`、`upstream_rationale_refs` 或 `evidence_refs` 时，不能输出 `approved_current_outcome_handoff`。
- `current_outcome_payload.finalization_readiness != finalizable_if_approved` 时，不能输出 approved current outcome；只能 correction、still-pending、rejection 或 candidate handoff。
- `accounting_outcome_type = no_final_outcome_yet` 时，不能被 accountant approval 包装成 final outcome。
- `coa_account_ref`、`hst_gst_treatment` 等 accounting fields 如存在，其 authority 属于 upstream result 或 accountant correction；Review Node 只能捕捉 accountant 对其批准或修正。
- `Transaction Log` history 不得出现在 `source_authority` 中作为当前 runtime outcome authority。

Runtime-only vs durable references：

- `transaction_outcome_context` 是 runtime-only。
- `transaction_id`、`evidence_refs`、entity/rule/case refs 是 durable references。
- `current_outcome_payload` 经 accountant approval / correction 后可成为下游 JE 和 final logging 的输入，但不是由 Review Node 写成 `Transaction Log`。

### 3.4 `evidence_review_context`

Purpose：提供 accountant 审核 item 所需的 evidence foundation、objective transaction basis、risk reason、conflict reason 和 unresolved issue。

Source authority：Evidence Log、Evidence Intake / Preprocessing、Transaction Identity、upstream rationale。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `evidence_refs` | 支撑 review 的 evidence references | Evidence Log | durable references |
| `objective_transaction_basis_ref` | 客观交易基础引用或摘要 | Evidence Intake / Transaction Identity | runtime view with durable refs |
| `evidence_sufficiency_status` | 当前 evidence 是否足以审核 | upstream packaging / review validation | runtime |
| `evidence_explanation` | 给 accountant 的证据说明 | deterministic packaging / LLM summary within bounds | runtime |

Allowed `evidence_sufficiency_status` values：

- `sufficient_for_review`
- `missing_key_evidence`
- `conflicting_evidence`
- `low_quality_evidence`
- `unbound_evidence`

Optional fields：

- `missing_evidence_types`
- `conflict_descriptions`
- `supporting_document_refs`
- `identity_or_dedupe_issue_refs`
- `evidence_authenticity_flags`

Validation / rejection rules：

- `evidence_refs` 不能为空。
- `evidence_sufficiency_status != sufficient_for_review` 时，不能输出 approved current outcome。
- `unbound_evidence` 表示 evidence 未绑定到明确交易或候选事项，不能被 review summary 语言绕过。
- `evidence_explanation` 不能替代 evidence refs，也不能覆盖 raw evidence。

Runtime-only vs durable references：

- context object 是 runtime-only。
- evidence references 是 durable refs。
- 本节点不能因 evidence review 而修改 `Evidence Log`；只能输出 supplemental evidence / reprocessing candidate。

### 3.5 `intervention_context`

Purpose：表达 prior pending、current review interaction 或 accountant-provided context 中与该 item 有关的 clarification、correction、confirmation、objection 或 unresolved answer。

Source authority：`Intervention Log`、Coordinator / Pending Node handoff、current accountant review interaction。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `intervention_refs` | 相关 intervention / review refs | Intervention Log / runtime review | durable refs or runtime refs |
| `actor_context` | accountant / user / system actor context | intervention source | runtime / durable actor ref |
| `interaction_summary` | 与当前 item 有关的交互摘要 | review packaging / LLM summary within bounds | runtime |
| `binding_status` | 该 interaction 是否明确绑定到 item | deterministic validation | runtime |

Allowed `binding_status` values：

- `bound_to_item`
- `partially_bound`
- `unbound`
- `ambiguous_reference`

Optional fields：

- `raw_response_refs`
- `clarification_payload`
- `correction_payload`
- `confirmation_payload`
- `objection_payload`
- `unresolved_questions`

Validation / rejection rules：

- `binding_status != bound_to_item` 时，不能把 accountant response 当作 approval 或 correction authority。
- `actor_context` 必须能区分 accountant action、client note、system-generated summary 和 imported context。
- accountant 自然语言如果指代不明，必须保留为 ambiguous / still-pending；LLM 不能替 accountant 选择含义。
- `correction_payload` 只可影响 current transaction handoff 或生成 candidate；不能直接变成 durable profile/entity/rule/governance mutation。

Runtime-only vs durable references：

- prior `intervention_refs` 是 durable references。
- current review interaction 在输出 `review_intervention_record` 后可成为 durable intervention / review record。
- 本节点写入的 review/intervention 记录不等于 `Transaction Log`、`Case Log`、`Rule Log`、`Entity Log` 或 `Governance Log` mutation。

### 3.6 `candidate_governance_context`

Purpose：描述 Review Node 需要展示、整理或转交的长期 memory / governance candidate、risk 或 visibility item。

Source authority：Entity Resolution、Rule Match、Case Judgment、Coordinator / Pending、Post-Batch Lint、Review packaging，或 accountant current correction 中暴露的 candidate signal。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `candidate_context_id` | candidate context 标识 | upstream workflow | runtime / candidate ref |
| `candidate_type` | candidate 类型 | upstream workflow | runtime |
| `candidate_subject_refs` | 涉及的 transaction、entity、alias、role、rule、case、evidence 或 policy refs | upstream / durable stores | durable refs where applicable |
| `candidate_reason` | 为什么形成候选 | upstream rationale / review packaging | runtime |
| `approval_requirement` | 是否需要 accountant / governance approval | active policy / governance boundary | runtime view over durable authority |
| `current_authority_status` | 当前是否已有 durable authority | memory / governance context | runtime view over durable records |

Allowed `candidate_type` values：

- `supplemental_evidence_candidate`
- `profile_change_candidate`
- `profile_confirmation_candidate`
- `new_entity_candidate`
- `alias_candidate`
- `role_confirmation_candidate`
- `case_memory_update_candidate`
- `rule_candidate`
- `rule_conflict_candidate`
- `rule_health_candidate`
- `automation_policy_candidate`
- `merge_candidate`
- `split_candidate`
- `auto_applied_downgrade_visibility`

Allowed `approval_requirement` values：

- `current_transaction_only`
- `candidate_only`
- `accountant_approval_required`
- `governance_review_required`
- `auto_applied_visibility_only`
- `not_eligible_for_approval`

Allowed `current_authority_status` values：

- `no_durable_authority`
- `candidate_exists`
- `approved_authority_exists`
- `rejected_or_disabled`
- `conflicting_authority`
- `unknown_authority`

Optional fields：

- `suggested_downstream_workflow`；allowed values: `coordinator_pending`, `case_memory_update`, `governance_review`, `post_batch_lint`, `evidence_reprocessing`, `no_downstream_action`。
- `risk_flags`
- `affected_transactions`
- `related_intervention_refs`
- `related_governance_refs`
- `accountant_visibility_note`

Validation / rejection rules：

- `candidate_subject_refs` 不能为空。
- candidate context 不能声称 approved alias、confirmed role、stable entity、active rule 或 automation-policy upgrade 已经由 Review Node 生效。
- `auto_applied_downgrade_visibility` 可以说明 downgrade 已按系统 lint policy 生效并需要展示，但 Review Node 不能把它包装成 accountant-approved upgrade / relaxation。
- `approval_requirement = governance_review_required` 的 item 不能输出为普通 current transaction approval 后绕过 governance。

Runtime-only vs durable references：

- 该 context 在 Review Node 内是 runtime-only / candidate-only。
- 后续是否写入 `Governance Log`、`Entity Log`、`Rule Log`、`Case Log` 或 `Profile`，由下游 workflow 和 accountant/governance approval 决定。

### 3.7 `authority_limit_context`

Purpose：明确 Review Node 对 package 或 item 最多能产生什么 downstream handoff，防止 review summary、LLM interpretation 或 candidate signal 越权。

Source authority：active product spec、entity automation policy、rule lifecycle、governance restrictions、upstream hard blocks、accountant authority boundary。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `allowed_decision_types` | Review Node 可输出的 decision type 上限 | policy / upstream / governance | runtime |
| `finalization_blocks` | 阻止 JE / final logging 的 hard blocks | upstream / governance / evidence validation | runtime |
| `memory_mutation_blocks` | 阻止长期 memory mutation 的边界 | governance / product authority | runtime |
| `requires_explicit_accountant_action` | 是否必须有明确 accountant action | accountant authority policy | runtime |

Allowed `allowed_decision_types` values：

- `approve_current_outcome`
- `correct_current_outcome`
- `reject_current_outcome`
- `keep_still_pending`
- `return_for_clarification`
- `forward_candidate_only`
- `acknowledge_visibility_only`
- `block_finalization`

Optional fields：

- `policy_refs`
- `governance_refs`
- `automation_policy_refs`
- `rule_lifecycle_refs`
- `entity_authority_refs`
- `review_required_reasons`

Validation / rejection rules：

- Output `decision_type` 必须属于 `allowed_decision_types`。
- `finalization_blocks` 非空时，不能输出 finalizable approved handoff，除非 block 被 accountant correction 明确解决且 evidence/context 可追溯。
- `memory_mutation_blocks` 不能被 Review Node 输出覆盖；只能产生 candidate handoff。
- 如果 `requires_explicit_accountant_action = true`，accountant silence、bulk acknowledgement、模糊自然语言或系统建议不能算 approval。

Runtime-only vs durable references：

- `authority_limit_context` 是 runtime view。
- policy/governance/entity/rule refs 是 durable references。
- 本节点不得修改这些 authority refs。

### 3.8 `batch_review_context`

Purpose：描述多交易、多候选或批次风险的聚合审核 context。

Source authority：workflow orchestrator、Post-Batch Lint、upstream candidate signals、review packaging。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `batch_id` | 当前批次引用 | workflow runtime | runtime reference |
| `grouped_item_refs` | 被聚合的 review item refs | review package | runtime refs |
| `batch_review_reason` | 为什么需要批次级审核 | upstream / lint / policy | runtime |
| `aggregation_basis` | 聚合依据 | deterministic grouping / LLM summary within bounds | runtime |

Allowed `batch_review_reason` values：

- `batch_policy_review`
- `repeated_correction_pattern`
- `rule_health_concern`
- `entity_merge_split_concern`
- `automation_risk_trend`
- `unresolved_item_summary`
- `accountant_requested_batch_view`

Optional fields：

- `affected_transaction_ids`
- `candidate_context_ids`
- `risk_summary`
- `partial_decision_allowed`：boolean。

Validation / rejection rules：

- `batch_review_context` 不能直接成为 future runtime authority。
- repeated correction 或 trend 不能自动升级为 rule、entity authority 或 automation-policy change。
- 批次级 acknowledgement 不能替代 item-level explicit approval，除非 `authority_limit_context` 明确允许且每个 item 绑定清楚。

Runtime-only vs durable references：

- batch context 是 runtime-only review aid。
- 其中的 transaction、candidate、intervention refs 可以被下游引用。
- 不属于 `Knowledge Log / Summary Log`，也不替代 Knowledge Compilation。

## 4. Output Contracts

### 4.1 `review_decision_package`

Purpose：Review Node 的 top-level output envelope，表达 accountant 已对哪些 item 做出什么 decision，以及哪些 item 仍需下游处理或候选转交。

Consumer / downstream authority：JE Generation、Transaction Logging、Case Memory Update、Governance Review、Coordinator / Pending、workflow orchestrator。下游只能按本 output 的 authority boundary 消费，不得把 candidate-only output 当 durable authority。

Required fields：

| Field | Meaning | Durable write status |
| --- | --- | --- |
| `review_package_id` | 对应 input package | runtime reference |
| `review_decision_package_id` | 本次 output 标识 | runtime / durable review ref |
| `client_id` | 当前客户引用 | durable reference |
| `batch_id` | 当前批次引用 | runtime reference |
| `review_actor` | 执行 review action 的 accountant / authorized actor | durable review metadata |
| `decision_items` | 每个 item 的 decision | runtime output; decision record may become intervention record |
| `package_status` | package-level status | runtime |
| `created_at` | decision package 创建时间 | durable review metadata if persisted |

Allowed `package_status` values：

- `all_items_decided`
- `partially_decided`
- `still_pending`
- `blocked_by_invalid_review`
- `candidate_only_forwarded`
- `no_finalization_allowed`

Optional fields：

- `package_level_summary`
- `review_intervention_record_refs`
- `downstream_handoff_refs`
- `unresolved_item_refs`

Validation rules：

- `decision_items` 不能为空。
- `review_actor` 必须能证明是 accountant 或被允许的 review actor；system actor 不能批准 accountant-only decision。
- `package_status` 必须由 item statuses 支撑；不能全部 item still-pending 但 package 标为 all_items_decided。
- output 不能包含 JE lines、Transaction Log entries、Case Log records、Rule Log records、stable Entity mutation 或 approved Governance mutation。

Durable boundary：

- package envelope 本身可以作为 review/intervention trace 被引用。
- 它不是 final audit log，不是 learning layer，不是 governance approval record。

### 4.2 `review_decision_item`

Purpose：表达 accountant 对单个 review item 的 decision。

Consumer / downstream authority：workflow orchestrator 和相应 downstream node。

Required fields：

| Field | Meaning | Durable write status |
| --- | --- | --- |
| `review_item_id` | 对应 input item | runtime reference |
| `decision_type` | accountant / review decision 类型 | review/intervention record |
| `decision_authority` | decision 的 authority 来源 | review/intervention metadata |
| `decision_rationale` | 为什么如此决定 | review/intervention metadata |
| `decision_binding_refs` | decision 绑定的 transaction/candidate/evidence refs | durable refs |
| `downstream_route` | downstream 应如何消费 | runtime handoff |

Allowed `decision_type` values：

- `approved_current_outcome`
- `corrected_current_outcome`
- `rejected_current_outcome`
- `still_pending`
- `returned_for_clarification`
- `candidate_forwarded`
- `visibility_acknowledged`
- `finalization_blocked`

Allowed `decision_authority` values：

- `explicit_accountant_approval`
- `explicit_accountant_correction`
- `explicit_accountant_rejection`
- `explicit_accountant_pending_decision`
- `accountant_visibility_acknowledgement`
- `system_validation_block`

Allowed `downstream_route` values：

- `je_generation`
- `transaction_logging_after_finalization`
- `case_memory_update_candidate`
- `governance_review`
- `coordinator_pending`
- `evidence_reprocessing`
- `upstream_rework`
- `no_downstream_action`

Optional fields：

- `approved_current_outcome_handoff`
- `corrected_current_outcome_handoff`
- `rejected_or_pending_handoff`
- `memory_governance_candidate_handoff`
- `review_intervention_record`
- `conflict_preservation_note`

Validation rules：

- `decision_type = approved_current_outcome` 必须使用 `decision_authority = explicit_accountant_approval`，且不得存在 unresolved finalization block。
- `decision_type = corrected_current_outcome` 必须使用 `decision_authority = explicit_accountant_correction`，并带 `corrected_current_outcome_handoff`。
- `candidate_forwarded` 不能被 downstream 当作 approved governance event。
- `visibility_acknowledged` 只能说明 accountant 已看到事项；不能变成 approval、correction、rule change 或 policy change。
- `system_validation_block` 只能产生 blocked / pending / clarification route，不能产生 accountant approval。

Durable boundary：

- decision item 可以写成 review/intervention record。
- 它不直接写入最终 transaction audit、case memory、rule memory、entity authority 或 governance mutation。

### 4.3 `approved_current_outcome_handoff`

Purpose：将 accountant 已明确批准的当前交易 outcome 交给 JE Generation / finalization flow。

Consumer / downstream authority：`JE Generation Node`、后续 `Transaction Logging Node`、`Case Memory Update Node`。

Required fields：

| Field | Meaning | Durable write status |
| --- | --- | --- |
| `transaction_id` | 被批准的交易 | durable reference |
| `approved_outcome_payload` | accountant 批准的当前交易结果 payload | downstream runtime input |
| `approval_actor` | accountant / authorized actor | review/intervention metadata |
| `approval_timestamp` | 批准时间 | review/intervention metadata |
| `approval_evidence_refs` | 支撑 approval 的 evidence refs | durable refs |
| `approval_rationale` | approval reason / accountant note | review/intervention metadata |
| `review_trace_ref` | 可回到 review decision 的引用 | durable review/intervention ref |

Optional fields：

- `upstream_outcome_context_id`
- `approved_with_conditions`
- `condition_notes`
- `case_memory_candidate_hint`

Validation rules：

- 必须有 explicit accountant approval。
- `approved_outcome_payload.finalization_readiness` 必须为 `finalizable_if_approved` 或等价的 accountant-corrected finalizable state。
- `approval_evidence_refs` 不能为空。
- 如果存在 unresolved evidence conflict、identity conflict、governance block 或 review-required policy block，output invalid。
- 该 handoff 不等于 case memory write、rule promotion、entity / alias / role approval 或 automation-policy approval。

Durable boundary：

- runtime handoff can feed JE / final logging。
- Review Node 不写 JE，不写 Transaction Log。
- `case_memory_candidate_hint` 只是 candidate，不是 `Case Log` write。

### 4.4 `corrected_current_outcome_handoff`

Purpose：表达 accountant 对当前交易 outcome 的明确修正，供 downstream workflow 基于修正继续 finalization、rework 或 candidate generation。

Consumer / downstream authority：JE Generation、Coordinator / Pending、upstream rework、Case Memory Update、Governance Review。

Required fields：

| Field | Meaning | Durable write status |
| --- | --- | --- |
| `transaction_id` | 被修正的交易 | durable reference |
| `original_outcome_context_id` | 被修正的上游 outcome | runtime / review ref |
| `correction_payload` | accountant 明确修正内容 | review/intervention metadata; downstream runtime input |
| `correction_actor` | accountant / authorized actor | review metadata |
| `correction_timestamp` | 修正时间 | review metadata |
| `correction_evidence_refs` | 支撑 correction 的 evidence refs | durable refs |
| `correction_rationale` | accountant 修正说明 | review/intervention metadata |
| `correction_scope` | correction 影响范围 | review validation |

Allowed `correction_scope` values：

- `current_transaction_only`
- `current_transaction_plus_candidate_signal`
- `requires_upstream_rework`
- `requires_governance_review`
- `not_finalizable_yet`

Optional fields：

- `corrected_outcome_payload`
- `unresolved_followup_questions`
- `memory_governance_candidate_handoff`
- `review_trace_ref`

Validation rules：

- 必须有 explicit accountant correction。
- `correction_payload` 必须绑定到明确 `transaction_id` 和原始 review item。
- 如果 correction 仍缺关键 COA / HST / evidence / identity 信息，不能 route 到 `je_generation`，应 route 到 pending、upstream rework 或 governance review。
- `correction_scope` 不能被扩大为 durable memory mutation。
- 如果 correction 暗示 Profile、Entity、Rule、Case 或 automation policy 需要变化，只能输出 candidate handoff。

Durable boundary：

- correction 可成为 current transaction downstream authority。
- correction 不自动写长期 memory，不自动创建 active rule，不自动批准 alias / role / entity / automation policy。

### 4.5 `rejected_or_pending_handoff`

Purpose：表达 accountant 未批准当前 outcome、仍需澄清、或系统 validation 阻止 finalization。

Consumer / downstream authority：Coordinator / Pending、Evidence Intake / reprocessing、upstream rework、workflow orchestrator。

Required fields：

| Field | Meaning | Durable write status |
| --- | --- | --- |
| `subject_refs` | 被拒绝或 pending 的 transaction / candidate refs | durable refs |
| `pending_or_rejection_reason` | 为什么不能 finalization | review/intervention metadata |
| `blocking_category` | 阻断类别 | runtime routing |
| `required_next_information` | 还缺什么信息或决定 | runtime handoff |
| `review_trace_ref` | review decision 引用 | durable review/intervention ref |

Allowed `blocking_category` values：

- `missing_evidence`
- `ambiguous_accountant_response`
- `unresolved_identity`
- `conflicting_evidence`
- `authority_block`
- `governance_needed`
- `accounting_outcome_rejected`
- `insufficient_review_context`

Optional fields：

- `suggested_downstream_route`
- `related_intervention_refs`
- `candidate_handoff_refs`

Validation rules：

- rejected / still-pending item 不能进入 JE generation。
- `ambiguous_accountant_response` 不能被 LLM 解释成 approval。
- `governance_needed` 不能被降级为普通 current transaction approval。

Durable boundary：

- 可写 review/intervention trace。
- 不写 Transaction Log final outcome。

### 4.6 `review_intervention_record`

Purpose：保存 accountant 在 Review Node 中的 review action、decision、rationale、correction、objection、confirmation 或 still-pending explanation。

Consumer / downstream authority：Intervention history、Transaction Logging trace reference、Case Memory Update context、Governance Review context、Coordinator / Pending。

Required fields：

| Field | Meaning | Durable write status |
| --- | --- | --- |
| `review_intervention_id` | review/intervention record 标识 | durable review/intervention record |
| `review_package_id` | 来源 package | durable review/intervention metadata |
| `review_item_id` | 来源 item | durable review/intervention metadata |
| `client_id` | 客户引用 | durable reference |
| `batch_id` | 批次引用 | runtime / durable ref |
| `actor_id` | accountant / authorized actor | durable review metadata |
| `actor_role` | actor role | durable review metadata |
| `action_type` | review action 类型 | durable review metadata |
| `raw_action_ref` | accountant 原始操作或回答引用 | durable evidence / intervention ref |
| `normalized_action_summary` | 规范化摘要 | durable review metadata |
| `bound_subject_refs` | action 绑定的交易、candidate、evidence refs | durable refs |
| `created_at` | 记录时间 | durable review metadata |

Allowed `actor_role` values：

- `accountant`
- `authorized_reviewer`
- `system_validation`

Allowed `action_type` values：

- `approve_current_outcome`
- `correct_current_outcome`
- `reject_current_outcome`
- `keep_still_pending`
- `request_clarification`
- `confirm_context_for_current_transaction`
- `object_to_system_result`
- `acknowledge_candidate_visibility`
- `system_blocked_invalid_review`

Optional fields：

- `rationale_text`
- `correction_payload`
- `visibility_candidate_refs`
- `conflict_notes`
- `downstream_handoff_refs`

Validation rules：

- `system_validation` actor_role 不能产生 accountant approval 或 correction。
- `raw_action_ref` 必须保留或能追溯 accountant 原话 / 操作；不能只保存 LLM paraphrase。
- `normalized_action_summary` 不能比 raw action 拥有更高 authority。
- record 不能包含 final Transaction Log entry、JE lines、Case Log write、Rule Log write、Entity authority mutation 或 Governance approval mutation。

Durable boundary：

- 这是 Review Node 唯一允许写入或形成 durable-equivalent handoff 的记录类别。
- 它是 intervention / review interaction record，不是 audit-facing final transaction log，不是 learning layer。

### 4.7 `memory_governance_candidate_handoff`

Purpose：把 review 中暴露的长期 memory 或 governance 事项转交给后续 workflow。

Consumer / downstream authority：Case Memory Update、Governance Review、Post-Batch Lint、Coordinator / Pending、Evidence reprocessing。

Required fields：

| Field | Meaning | Durable write status |
| --- | --- | --- |
| `candidate_handoff_id` | candidate handoff 标识 | runtime / candidate ref |
| `candidate_type` | 候选类型 | runtime / candidate |
| `subject_refs` | candidate 绑定对象 | durable refs |
| `candidate_basis` | candidate 为什么存在 | review/intervention metadata |
| `source_review_trace_ref` | 来源 review decision | durable review/intervention ref |
| `required_authority_path` | 后续必须经过的 authority path | runtime view over governance policy |

Allowed `required_authority_path` values：

- `case_memory_update_review`
- `governance_review_required`
- `accountant_approval_required_downstream`
- `evidence_reprocessing_required`
- `coordinator_clarification_required`
- `post_batch_lint_followup`
- `candidate_rejected_no_action`

Optional fields：

- `suggested_event_type`
- `affected_transactions`
- `proposed_value`
- `old_value_context`
- `risk_flags`
- `blocking_reasons`

Validation rules：

- `candidate_handoff_id` 不能被当成 durable memory id。
- handoff 不能声明 alias approved、role confirmed、entity stable、rule active、automation policy upgraded / relaxed 或 governance event approved。
- `proposed_value` 只是 proposal；不能直接执行。
- `required_authority_path = governance_review_required` 时，consumer 必须进入 Governance Review 或等价 governance workflow。

Durable boundary：

- candidate-only。
- 不写长期 memory，不批准治理，不改变 automation behavior。

### 4.8 `batch_review_summary_handoff`

Purpose：汇总一组 review items 的已处理、未处理、风险、candidate 和下游 handoff 状态。

Consumer / downstream authority：workflow orchestrator、Coordinator、Governance Review、Post-Batch Lint、human review surface。

Required fields：

| Field | Meaning | Durable write status |
| --- | --- | --- |
| `batch_id` | 批次引用 | runtime reference |
| `review_package_id` | package 引用 | runtime / review ref |
| `decided_item_refs` | 已有 decision 的 item refs | runtime refs |
| `undecided_item_refs` | 未完成 review 的 item refs | runtime refs |
| `blocked_item_refs` | 被 validation 或 authority block 的 item refs | runtime refs |
| `candidate_handoff_refs` | 已转出的 candidate refs | runtime / candidate refs |
| `summary_status` | 批次 review 状态 | runtime |

Allowed `summary_status` values：

- `batch_review_complete`
- `batch_review_partial`
- `batch_review_blocked`
- `governance_candidates_forwarded`
- `still_pending_items_exist`

Optional fields：

- `accountant_visible_summary`
- `risk_summary`
- `next_review_focus`

Validation rules：

- summary 不能替代 item-level review decision。
- summary 不能作为 deterministic rule source。
- summary 不属于 `Knowledge Log / Summary Log`，不能直接作为 future runtime memory。

Durable boundary：

- 可作为 review trace 被保存或引用。
- 不写 final Transaction Log，不写长期 memory。

## 5. Field Authority and Memory Boundary

### 5.1 Source of truth for important fields

- `transaction_id`：source of truth 是 Transaction Identity Node / transaction identity layer。
- `client_id`、`batch_id`：source of truth 是 client / workflow runtime context。
- `evidence_refs`：source of truth 是 `Evidence Log`；Review Node 只能引用。
- `current_outcome_payload`：source of truth 是 upstream result 或 accountant correction；Review Node 只捕捉 accountant 对其 approval / correction。
- `review_actor`、`actor_id`、`raw_action_ref`：source of truth 是 accountant review interaction capture。
- `authority_limit_context`：source of truth 是 active policy、Profile / Entity / Rule / Governance authority、upstream hard blocks。
- `candidate_governance_context`：source of truth 是 upstream candidate signal、review correction 中暴露的 candidate，或 Post-Batch Lint context；不是 approved authority。
- `review_intervention_record`：source of truth 是 Review Node 捕捉到的 review action，但 authority 仅限 intervention / review interaction。

### 5.2 Fields that can never become durable memory by this node

Review Node 永远不能把以下字段直接写成长久业务记忆或治理状态：

- `display_group_key`
- `package_summary_context`
- `review_question`
- `evidence_explanation`
- `interaction_summary`
- `normalized_action_summary`
- `package_level_summary`
- `batch_review_summary_handoff.accountant_visible_summary`
- `candidate_reason`
- `proposed_value`
- `risk_summary`
- LLM-generated explanation / paraphrase
- accountant silence、ambiguous response、bulk acknowledgement

这些字段可以帮助 review、trace 或 downstream routing，但不能成为 `Profile`、stable `Entity Log`、`Case Log`、`Rule Log`、approved `Governance Log` 或 `Transaction Log` final outcome 的直接写入依据。

### 5.3 Fields that can become durable only after accountant / governance approval

以下内容最多由 Review Node 输出为 candidate 或 current-transaction correction context；只有经过相应 downstream authority path 后才可能变成 durable memory：

- profile change / profile confirmation
- new entity / entity merge / split
- alias approval / rejection
- role confirmation
- case memory update
- rule creation / promotion / modification / deletion / downgrade
- automation policy upgrade / relaxation / governance change
- accountant correction that implies long-term client policy

Current transaction approval / correction 可以成为本笔交易 downstream finalization 的依据，但不自动成为长期 memory 或 rule authority。

### 5.4 Audit vs learning / logging boundary

- `Transaction Log` 是 audit-facing final log，不参与 runtime review decision；Review Node 不写它。
- `review_intervention_record` 是 accountant interaction / review rationale record，不是 final audit log。
- `Case Log` 是 completed transaction 的 case memory；Review Node 不写它。
- `Rule Log` 只保存 accountant / governance approved deterministic rules；Review Node 不写 active rule。
- `Governance Log` 保存高权限长期记忆变化及审批状态；Review Node 只能转交 candidate，不批准或执行 mutation。
- `Knowledge Log / Summary Log` 是编译摘要；Review Node 的 batch summary 不等于 customer knowledge summary。

## 6. Validation Rules

### 6.1 Contract-level validation rules

- 每个 review decision 必须绑定到明确 `review_item_id` 和 subject refs。
- Accountant approval / correction 必须有明确 actor、raw action ref、timestamp、evidence refs 和 item binding。
- Runtime summary、LLM explanation、display grouping、candidate signal 不能提升 authority。
- Output decision 必须尊重 input `authority_limit_context.allowed_decision_types`、`finalization_blocks` 和 `memory_mutation_blocks`。
- Current transaction finalization 与 long-term memory / governance candidate 必须分开输出。
- Review Node output 不能包含 JE lines、final Transaction Log entries、Case Log records、Rule Log records、stable Entity mutation、Profile mutation 或 approved Governance mutation。

### 6.2 Conditions that make the input invalid

Input invalid when：

- 缺少 `review_package_id`、`client_id`、`batch_id`、`review_items` 或 `authority_limit_context`。
- `review_items` 为空。
- item 没有明确 subject refs。
- current transaction item 缺少 `transaction_id`、`current_outcome_payload`、`upstream_rationale_refs` 或 `evidence_refs`。
- evidence refs 不可追溯，或 evidence 未绑定到 item。
- pending / intervention context 没有绑定到明确交易、问题或候选事项。
- package 声称 item 已 final logged 或 governance mutation 已执行。
- input 把 `Transaction Log` history 当成当前 runtime decision authority。
- input 把 candidate alias / role / entity / rule / policy 当成 approved durable authority。

### 6.3 Conditions that make the output invalid

Output invalid when：

- `approved_current_outcome` 缺少 explicit accountant approval。
- `corrected_current_outcome` 缺少 explicit accountant correction 或 correction payload。
- ambiguous accountant response、silence、bulk acknowledgement 或 LLM interpretation 被当作 approval。
- unresolved evidence、identity、authority 或 governance block 仍存在，却 route 到 JE generation。
- rejected / still-pending item 被 route 到 JE generation。
- governance-needed item 被输出为普通 approved current outcome 以绕过 Governance Review。
- candidate handoff 声称已经写入 long-term memory 或 approved governance event。
- review intervention record 包含 final Transaction Log write、JE lines、Case Log write、Rule Log write、Entity authority mutation 或 Profile mutation。
- batch summary 被当作 item-level approval 或 deterministic rule source。

### 6.4 Stop / ask conditions for unresolved contract authority

后续阶段或实现前必须 stop / ask when：

- Review Node 与 Governance Review Node 的 split 被要求承担 durable governance approval / execution，而 live docs 未冻结该 authority。
- 下游要求 Review Node 直接写 `Transaction Log`、`Case Log`、`Rule Log`、stable `Entity Log`、`Profile` 或 approved `Governance Log`。
- 需要决定 Review Node 是否审核所有交易、只审核 review-required items、还是支持 sampling / policy-based batch review 的产品范围。
- exact accounting payload schema 被要求冻结为 Review Node authority，而 upstream / JE contract 尚未定义。
- accountant bulk approval 是否能覆盖多个 item 缺少明确 item binding 或 authority policy。

## 7. Examples

### 7.1 Valid minimal example

```json
{
  "review_package_request": {
    "review_package_id": "revpkg_001",
    "client_id": "client_abc",
    "batch_id": "batch_2026_05",
    "review_scope": "single_transaction",
    "trigger_reasons": ["current_outcome_requires_review"],
    "review_items": [
      {
        "review_item_id": "revitem_001",
        "item_type": "current_transaction_outcome",
        "item_subject_refs": { "transaction_id": "txn_01HZX" },
        "review_need": "Accountant approval required before JE generation.",
        "review_question": "Approve current classification for this transaction?",
        "source_context": { "source_node": "case_judgment" },
        "authority_limits": {
          "allowed_decision_types": ["approve_current_outcome", "reject_current_outcome", "keep_still_pending"],
          "finalization_blocks": [],
          "memory_mutation_blocks": ["no_case_write_by_review_node", "no_rule_promotion_by_review_node"],
          "requires_explicit_accountant_action": true
        },
        "transaction_outcome_context": {
          "transaction_id": "txn_01HZX",
          "outcome_context_id": "outctx_001",
          "outcome_source_path": "case_judgment",
          "outcome_review_state": "ready_for_accountant_review",
          "current_outcome_payload": {
            "accounting_outcome_type": "classification_result",
            "accounting_outcome_summary": "Office supplies expense, GST/HST input tax credit applicable.",
            "finalization_readiness": "finalizable_if_approved",
            "source_authority": "case_judgment_result"
          },
          "upstream_rationale_refs": ["rationale_case_001"],
          "evidence_refs": ["ev_bank_001", "ev_receipt_001"]
        }
      }
    ],
    "authority_limit_context": {
      "allowed_decision_types": ["approve_current_outcome", "reject_current_outcome", "keep_still_pending"],
      "finalization_blocks": [],
      "memory_mutation_blocks": ["no_durable_memory_mutation_by_review_node"],
      "requires_explicit_accountant_action": true
    }
  },
  "review_decision_package": {
    "review_package_id": "revpkg_001",
    "review_decision_package_id": "revdec_001",
    "client_id": "client_abc",
    "batch_id": "batch_2026_05",
    "review_actor": { "actor_id": "acct_001", "actor_role": "accountant" },
    "package_status": "all_items_decided",
    "created_at": "2026-05-06T10:00:00Z",
    "decision_items": [
      {
        "review_item_id": "revitem_001",
        "decision_type": "approved_current_outcome",
        "decision_authority": "explicit_accountant_approval",
        "decision_rationale": "Accountant approved current outcome.",
        "decision_binding_refs": { "transaction_id": "txn_01HZX", "evidence_refs": ["ev_bank_001", "ev_receipt_001"] },
        "downstream_route": "je_generation"
      }
    ]
  }
}
```

Why valid：

- transaction、evidence、rationale、authority limits 和 explicit accountant approval 都可追溯。
- output 只把 current outcome 交给 JE flow，不写 Transaction Log 或长期 memory。

### 7.2 Valid richer example

```json
{
  "review_item_id": "revitem_010",
  "item_type": "transaction_correction_review",
  "item_subject_refs": { "transaction_id": "txn_01HY2", "entity_id": "ent_home_depot" },
  "transaction_outcome_context": {
    "transaction_id": "txn_01HY2",
    "outcome_context_id": "outctx_010",
    "outcome_source_path": "case_judgment",
    "outcome_review_state": "conflict_requires_review",
    "current_outcome_payload": {
      "accounting_outcome_type": "classification_result",
      "accounting_outcome_summary": "Materials expense suggested from receipt.",
      "finalization_readiness": "requires_correction",
      "source_authority": "case_judgment_result",
      "entity_ref": "ent_home_depot"
    },
    "upstream_rationale_refs": ["rationale_case_010"],
    "evidence_refs": ["ev_bank_010", "ev_receipt_010"]
  },
  "intervention_context": {
    "intervention_refs": ["int_pending_010"],
    "actor_context": { "actor_id": "acct_001", "actor_role": "accountant" },
    "interaction_summary": "Accountant clarified this receipt includes owner personal renovation items.",
    "binding_status": "bound_to_item",
    "raw_response_refs": ["raw_review_response_010"]
  },
  "decision_output": {
    "decision_type": "corrected_current_outcome",
    "decision_authority": "explicit_accountant_correction",
    "downstream_route": "je_generation",
    "corrected_current_outcome_handoff": {
      "transaction_id": "txn_01HY2",
      "original_outcome_context_id": "outctx_010",
      "correction_scope": "current_transaction_plus_candidate_signal",
      "correction_payload": {
        "accounting_outcome_summary": "Treat personal portion as shareholder loan / owner draw context for current transaction."
      },
      "correction_actor": "acct_001",
      "correction_timestamp": "2026-05-06T10:05:00Z",
      "correction_evidence_refs": ["ev_receipt_010", "raw_review_response_010"],
      "correction_rationale": "Accountant explicitly corrected mixed-use handling."
    },
    "memory_governance_candidate_handoff": {
      "candidate_handoff_id": "cand_review_010",
      "candidate_type": "case_memory_update_candidate",
      "subject_refs": { "transaction_id": "txn_01HY2", "entity_id": "ent_home_depot" },
      "candidate_basis": "Current correction may be useful as a mixed-use case.",
      "source_review_trace_ref": "review_intervention_010",
      "required_authority_path": "case_memory_update_review"
    }
  }
}
```

Why valid：

- correction 明确绑定当前交易。
- current transaction handoff 与 case-memory candidate handoff 被分开。
- candidate 不声称已经写入 `Case Log` 或生成 rule。

### 7.3 Invalid example

```json
{
  "review_item_id": "revitem_bad",
  "decision_type": "approved_current_outcome",
  "decision_authority": "accountant_visibility_acknowledgement",
  "decision_rationale": "Accountant saw the batch summary and did not object.",
  "downstream_route": "je_generation",
  "memory_governance_candidate_handoff": {
    "candidate_type": "alias_candidate",
    "subject_refs": { "entity_id": "ent_123", "alias": "TIMS COFFEE" },
    "required_authority_path": "governance_review_required",
    "proposed_value": { "alias_status": "approved_alias" }
  }
}
```

Why invalid：

- visibility acknowledgement / silence 不是 explicit accountant approval。
- batch summary 不能替代 item-level approval。
- alias candidate 不能由 Review Node 变成 approved alias。
- governance-required candidate 不能绕过 Governance Review。

## 8. Open Contract Boundaries

以下问题仍未由 live docs 完全冻结，但不阻塞本 Stage 3 contract：

- Review Node 是否覆盖所有交易、只覆盖 review-required items、还是支持 sampling / policy-based batch review 的 exact product scope。
- Review Node 与 `Governance Review Node` 在 accountant governance approval capture、governance event approval 和 durable mutation execution 上的 exact split。
- `review_intervention_record` 与未来 `Intervention Log` implementation schema 的 exact persistence contract。
- `review_trace_ref` 如何被 `Transaction Logging Node` 纳入 final audit trail 的 exact downstream schema。
- 多交易、多候选 package 的 aggregation、dedup、sorting、partial approval 和 bulk action 规则。
- `current_outcome_payload` 中 COA / HST / amount allocation 的完整 accounting schema；本文件只规定 Review Node 如何消费和转交，不把 accounting payload source of truth 放到 Review Node。

## 9. Self-Review

- 已读取 required live repo docs：`AGENTS.md`、`TASK_STATE.md`、`PLANS.md`、`CLAUDE.md`、`DECISIONS.md`、`supporting documents/communication_preferences.md`、`supporting documents/development_workflow.md`、`supporting documents/node_design_roadmap.md`、`new system/new_system.md`。
- 已读取 prior approved Review Node Stage 1/2 docs。
- 已读取可用 Superpowers docs：`using-superpowers/SKILL.md`、`brainstorming/SKILL.md`；project workflow skill `ai-bookkeeper-node-design-facilitation` 在当前环境不存在，因此按 runner instruction 使用 repo `supporting documents/node_design_roadmap.md` 与本节点 Stage 1/2 docs 作为 workflow authority。
- 已注意 `supporting documents/node_design_roadmap_zh.md` 在工作树中不存在；本文件未引用或发明该文档。
- 本文件只写 Stage 3 data contract：没有定义 Stage 4 execution algorithm、Stage 5 technical implementation map、Stage 6 test matrix / fixtures、Stage 7 coding-agent task contract。
- 未把 `Transaction Log` 当作 runtime decision source。
- 未把 `Log` 用作 transient handoff / temporary candidate queue。
- 未让 `new_entity_candidate`、candidate alias / role / rule / governance signal 获得 durable authority。
- 未让 Case Judgment 或 Review Node 写 long-term memory 或批准 governance。
- 已保持 Accountant / Governance approval 作为长期 authority change 边界。
- 本次只应写入目标文件：`new system/node_stage_designs/review_node__stage_3__data_contract.md`。
