# Entity Resolution Node — Stage 3：Data Contract Spec

## 1. Stage 范围

本 Stage 3 只定义 `Entity Resolution Node` 的 implementation-facing data contract。

前置依据是：

- `new system/new_system.md`
- `new system/node_stage_designs/entity_resolution_node__stage_1__functional_intent.md`
- `new system/node_stage_designs/entity_resolution_node__stage_2__logic_and_boundaries.md`

本阶段把 Stage 1/2 已批准的行为边界转换为输入对象、输出对象、字段语义、字段 authority、runtime / durable memory 边界、validation rules 和 compact examples。

本阶段不定义：

- step-by-step execution algorithm
- technical implementation map
- repo module path、class、API、storage engine 或 DB migration
- test matrix 或 fixture plan
- coding-agent task contract
- 新 product authority
- legacy replacement mapping

## 2. Contract Position in Workflow

### 2.1 Upstream Handoff Consumed

本节点消费 `Profile / Structural Match Node` 之后的 `non_structural_entity_resolution_handoff`。

该 handoff 表示：

- evidence intake 已形成可追溯 evidence foundation；
- transaction identity 已稳定；
- profile / structural path 未完成当前交易处理；
- 当前交易需要进入普通 `entity -> rule -> case` workflow。

如果上游尚未完成 evidence intake、transaction identity，或当前交易已经由 profile-backed structural path 完成，本节点输入无效。

### 2.2 Downstream Handoff Produced

本节点输出 `entity_resolution_output`，供以下 downstream nodes 消费：

- `Rule Match Node`：只在 stable entity、approved alias、confirmed role/context 和 automation policy 都允许时使用。
- `Case Judgment Node`：使用 entity basis、new entity candidate、role uncertainty、ambiguity reason 或 unresolved reason 作为当前交易上下文。
- `Coordinator / Pending Node`：使用 blocking / issue reason 生成 accountant question。
- `Review Node` / `Governance Review Node`：使用 candidate signals，但这些 signal 不是 approval。
- `Case Memory Update Node`：在交易完成后，可结合最终结果消费 candidate signals；本节点输出本身不等于 long-term memory mutation。

### 2.3 Logs / Memory Stores Read

本节点可以读取或消费：

- `Evidence Log` references：只作为 evidence source，不作为业务结论。
- `Entity Log`：known entities、aliases、roles、status、authority、risk_flags、automation_policy、evidence_links。
- `Governance Log` / governance context：已生效的 alias、role、merge/split、policy 限制。
- `Intervention Log`：与 identity correction、accountant confirmation、recent conflict 有关的语境。
- `Knowledge Log / Summary Log`：只作为辅助上下文，不能替代 `Entity Log` authority。
- `Profile / Structural Match Node` 的 runtime handoff：用于确认当前交易不是已完成结构性交易。

本节点不读取 `Transaction Log` 做 runtime decision。
本节点不能读取 `Case Log` 或 `Rule Log` 来绕过 entity / alias / role authority。

### 2.4 Logs / Memory Stores Written or Candidate-Only

本节点不直接写入：

- `Transaction Log`
- stable `Entity Log` authority
- `Case Log`
- `Rule Log`
- approved `Governance Log` event
- `Profile`

本节点可以输出 candidate-only signals：

- `new_entity_candidate`
- `alias_candidate`
- `role_confirmation_candidate`
- `merge_split_candidate`
- `identity_ambiguity_issue`
- `unresolved_identity_issue`
- `rejected_alias_conflict_issue`
- `automation_policy_governance_candidate`

这些 signal 可以被后续 workflow 评估，但不能由本节点直接变成 stable entity、approved alias、confirmed role、active rule、automation policy upgrade 或 accountant-approved governance result。

## 3. Input Contracts

### 3.1 `non_structural_entity_resolution_handoff`

Purpose：上游交给本节点的 runtime envelope，证明当前交易有资格进入 entity resolution。

Source authority：`Evidence Intake / Preprocessing Node`、`Transaction Identity Node`、`Profile / Structural Match Node`。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `transaction_id` | 稳定交易身份 | `Transaction Identity Node` | durable reference |
| `client_id` | 当前客户标识 | batch / client context | durable reference |
| `batch_id` | 当前处理批次 | workflow runtime | runtime |
| `objective_transaction_basis` | 客观交易基础，例如 date、amount、direction、bank_account | Evidence Intake / Preprocessing | runtime object with durable evidence references |
| `evidence_refs` | 可追溯 evidence IDs 或引用 | `Evidence Log` | durable references |
| `structural_match_status` | 上游结构性路径结果 | `Profile / Structural Match Node` | runtime |
| `structural_match_reason` | 为什么未由 profile / structural path 完成 | `Profile / Structural Match Node` | runtime |

Optional fields：

- `upstream_issue_flags`：evidence quality、identity issue、profile issue、duplicate warning 等上游问题信号。
- `accountant_context_refs`：当前批次或当前交易可引用的 accountant-provided context。
- `profile_context_refs`：与本交易有关但未完成结构性处理的 profile context 引用。

Validation / rejection rules：

- `transaction_id`、`client_id`、`objective_transaction_basis`、`evidence_refs` 缺失时输入无效。
- `structural_match_status` 必须明确表示当前交易未被结构性路径完成；否则本节点必须拒绝该 handoff。
- `objective_transaction_basis.amount` 必须采用 absolute amount + explicit direction 的项目级语义；不得用正负号替代 `direction`。
- `evidence_refs` 必须能追溯到 evidence source；不能只传不可追溯摘要。

Runtime-only vs durable references：

- handoff envelope 是 runtime-only。
- `transaction_id`、`client_id`、`evidence_refs` 是 durable references。
- 本节点不能因为收到该 handoff 而创建 durable memory。

### 3.2 `current_evidence_identity_signals`

Purpose：列出当前 evidence 中可用于识别 counterparty / vendor / payee 的表面信号。

Source authority：`Evidence Log`、Evidence Intake / Preprocessing、accountant-provided current context。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `signals` | identity signal 列表 | current evidence | runtime list with durable evidence refs |

Each `signal` required fields：

| Field | Meaning | Authority |
| --- | --- | --- |
| `signal_type` | 信号类型 | Evidence Intake / Preprocessing |
| `surface_text` | evidence 中出现的原始或近原始名称文本 | Evidence Log |
| `evidence_ref` | 支撑该 signal 的 evidence reference | Evidence Log |
| `source_priority` | 当前设计允许的相对证据强度标签 | Evidence Intake / Preprocessing |

Allowed `signal_type` values：

- `raw_bank_text`
- `receipt_vendor`
- `cheque_payee`
- `invoice_party`
- `contract_party`
- `historical_ledger_name`
- `accountant_context`
- `other_current_evidence`

Allowed `source_priority` values：

- `primary`
- `supporting`
- `weak`
- `conflicting`

Optional fields per signal：

- `normalized_display_text`：仅用于 runtime comparison / display，不等于 approved alias。
- `language_or_script_note`：文本语言、缩写、拼写异常等说明。
- `extracted_role_hint`：当前 evidence 暗示的 role/context，只能是 candidate role hint。

Validation / rejection rules：

- `signals` 可以为空，但若为空，本节点只能输出 `unresolved` 或明确说明缺少 identity signal。
- `surface_text` 不能被替换成没有 evidence trace 的模型总结。
- `normalized_display_text` 不能作为 durable alias approval。
- `extracted_role_hint` 不能作为 confirmed role。

Runtime-only vs durable references：

- `signals` 是 runtime-only object。
- `evidence_ref` 是 durable reference。
- `surface_text` 可被后续 candidate signal 引用，但不能由本节点写入 approved alias。

### 3.3 `entity_authority_context`

Purpose：提供 `Entity Log` 与治理上下文中可用于识别的 known entity、alias、role、status、policy 和风险信息。

Source authority：`Entity Log`；已批准 governance changes 来自 `Governance Log`。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `candidate_entities` | 当前 evidence 可能相关的 entity context 列表 | `Entity Log` lookup / retrieval | runtime view over durable records |
| `governance_constraints` | 已生效治理限制 | `Governance Log` / Entity Log projection | runtime view over durable records |

Each `candidate_entity` required fields：

| Field | Meaning | Authority |
| --- | --- | --- |
| `entity_id` | entity unique identifier | `Entity Log` |
| `display_name` | entity display name | `Entity Log` |
| `entity_type` | entity type | `Entity Log` |
| `status` | lifecycle status | `Entity Log` |
| `authority` | entity / alias / role 的确认来源与可信级别 | `Entity Log` / Governance Log |
| `aliases` | relevant aliases with status | `Entity Log` |
| `roles` | accountant-confirmed roles only | `Entity Log` |
| `automation_policy` | entity-level automation policy | `Entity Log` / Governance Log |

Allowed `entity_type` values：

- `vendor`
- `payee`
- `counterparty`
- `person`
- `organization`
- `unknown`

Allowed `status` values：

- `candidate`
- `active`
- `merged`
- `archived`

Allowed alias statuses：

- `candidate_alias`
- `approved_alias`
- `rejected_alias`

Allowed automation policy values：

- `eligible`
- `case_allowed_but_no_promotion`
- `rule_required`
- `review_required`
- `disabled`

Optional fields：

- `risk_flags`
- `evidence_links`
- `governance_notes`
- `merge_split_history_refs`
- `recent_identity_intervention_refs`
- `source_retrieval_reason`

Validation / rejection rules：

- `candidate_entities` may be empty; empty candidate set does not invalidate input.
- `active` entity status alone cannot be treated as rule eligibility.
- `candidate` entity status cannot support stable entity authority.
- `merged` or `archived` entity references must be treated as constrained context, not active identity target unless governance context explicitly provides the active target.
- `candidate_alias` cannot support rule match.
- `rejected_alias` is negative evidence and cannot be bypassed by semantic similarity.
- `roles` must contain only accountant-confirmed or allowed onboarding accountant-derived roles with authority metadata.

Runtime-only vs durable references：

- `entity_authority_context` is a runtime view.
- Entity, alias, role, status, policy, governance refs are durable authority records.
- 本节点不能 mutate these records.

### 3.4 `identity_governance_and_intervention_context`

Purpose：提供近期人工介入、identity correction、governance restriction 或 unresolved approval state，限制本节点输出 authority。

Source authority：`Intervention Log`、`Governance Log`、Review / Governance Review approved state。

Required fields：

| Field | Meaning | Authority |
| --- | --- | --- |
| `identity_constraints` | 当前交易或相关 entity 的限制列表 | Intervention / Governance context |

Optional fields：

- `recent_corrections`
- `pending_governance_events`
- `rejected_governance_events`
- `auto_applied_downgrades`
- `accountant_confirmation_refs`

Validation / rejection rules：

- pending governance event cannot be treated as approved authority.
- rejected governance event cannot be reused as positive evidence.
- auto-applied downgrade can restrict automation, but cannot upgrade or relax automation.
- accountant confirmation references must identify what was confirmed: alias、role、merge/split、policy 或 current transaction classification；不能泛化成所有 authority。

Runtime-only vs durable references：

- context envelope 是 runtime-only。
- intervention / governance references are durable records.
- 本节点只能 consume constraints or emit candidate signals.

### 3.5 `knowledge_summary_context`

Purpose：提供可读客户知识摘要，辅助解释 identity，但不提供 deterministic authority。

Source authority：`Knowledge Log / Summary Log`。

Required fields：

- None；该输入整体 optional。

Optional fields：

- `summary_refs`
- `entity_summary_text`
- `identity_risk_notes`
- `known_ambiguity_notes`

Validation / rejection rules：

- Knowledge Summary 与 `Entity Log` authority 冲突时，`Entity Log` / `Governance Log` authority wins。
- Summary text cannot create approved alias, confirmed role, stable entity, rule eligibility, or automation permission。

Runtime-only vs durable references：

- summary context 是 runtime read context。
- summary refs may be durable references。
- 本节点不能把 summary 内容写回 durable entity authority。

## 4. Output Contracts

### 4.1 `entity_resolution_output`

Purpose：表达当前交易的 entity identity state，以及该 state 对 rule、case、pending、review 和 governance 的 authority impact。

Consumer / downstream authority：

- `Rule Match Node` may consume only when output allows rule eligibility.
- `Case Judgment Node` may consume resolved, new candidate, role uncertainty, ambiguous or unresolved context within its own authority boundary.
- `Coordinator / Pending Node` consumes issue reasons.
- `Review Node` / `Governance Review Node` consumes candidate signals as proposals only.

Required fields：

| Field | Meaning | Authority / Source |
| --- | --- | --- |
| `transaction_id` | 对应交易身份 | input handoff |
| `status` | entity resolution status | Entity Resolution Node runtime judgment within authority checks |
| `confidence` | entity identity confidence only | Entity Resolution Node runtime judgment |
| `reason` | 简短识别理由 | Entity Resolution Node |
| `evidence_used` | 实际用于识别的 evidence signal references | input evidence signals |
| `rule_eligibility` | 是否可进入 deterministic rule match 的上限 | deterministic authority checks |
| `case_context_eligibility` | 是否可作为 Case Judgment context | deterministic authority checks |
| `memory_write_boundary` | 本输出对 durable memory 的权限边界 | Stage 3 contract |
| `candidate_signals` | candidate-only signals list, can be empty | Entity Resolution Node |

Allowed `status` values：

- `resolved_entity`
- `resolved_entity_with_unconfirmed_role`
- `new_entity_candidate`
- `ambiguous_entity_candidates`
- `unresolved`

Optional fields：

- `entity_id`
- `matched_alias`
- `alias_status`
- `candidate_role`
- `blocking_reason`
- `candidate_entities`
- `governance_issue_refs`
- `intervention_context_refs`
- `identity_risk_flags`

Allowed `confidence` values：

- `high`
- `medium`
- `low`
- `unknown`

`confidence` 只表示 identity confidence；具体 threshold number 未在本 Stage 3 冻结。

Allowed `rule_eligibility` values：

- `eligible_for_rule_match`
- `blocked_candidate_alias`
- `blocked_rejected_alias`
- `blocked_unconfirmed_role`
- `blocked_new_entity_candidate`
- `blocked_ambiguous_identity`
- `blocked_unresolved_identity`
- `blocked_entity_status`
- `blocked_automation_policy`
- `blocked_governance_constraint`

Allowed `case_context_eligibility` values：

- `eligible_for_case_context`
- `case_context_allowed_with_identity_caution`
- `case_context_allowed_but_no_rule_promotion`
- `case_context_requires_pending`
- `case_context_blocked_by_governance`

Allowed `memory_write_boundary` values：

- `runtime_only_no_memory_write`
- `candidate_signal_only`

Validation rules：

- If `status = resolved_entity`, `entity_id` is required and must refer to an active stable entity authority.
- If `status = resolved_entity`, `alias_status` must be `approved_alias` for `rule_eligibility = eligible_for_rule_match`.
- If `status = resolved_entity_with_unconfirmed_role`, `entity_id` is required and `candidate_role` or role issue context must be present.
- If `status = new_entity_candidate`, `entity_id` must be absent unless referring only to a candidate entity record whose authority is explicitly non-stable; `rule_eligibility` must be `blocked_new_entity_candidate`.
- If `status = ambiguous_entity_candidates`, `candidate_entities` must include at least two candidates or an explicit ambiguity reason.
- If `status = unresolved`, `blocking_reason` must explain missing or insufficient identity evidence.
- `confidence` cannot be interpreted as accounting classification confidence.
- `memory_write_boundary` cannot imply stable durable write.

Durable memory effect：

- This output does not write durable memory by itself.
- It can propose candidate signals.
- Any stable memory change requires accountant / governance authority through downstream workflow.

### 4.2 `candidate_signal`

Purpose：表达本节点发现的 identity / governance candidate issue，供 downstream review、pending、case-memory-update 或 governance workflow 处理。

Consumer / downstream authority：

- `Coordinator / Pending Node` may turn issue into accountant question.
- `Review Node` may display or collect confirmation.
- `Case Memory Update Node` may consider it after transaction completion.
- `Governance Review Node` may create or process governance event.

Required fields：

| Field | Meaning | Authority / Source |
| --- | --- | --- |
| `signal_type` | candidate or issue kind | Entity Resolution Node |
| `signal_status` | 本 signal 的 authority state | Entity Resolution Node contract |
| `reason` | 为什么提出该 signal | Entity Resolution Node |
| `supporting_evidence_refs` | 支撑该 signal 的 evidence references | Evidence Log |

Allowed `signal_type` values：

- `new_entity_candidate`
- `alias_candidate`
- `role_confirmation_candidate`
- `merge_split_candidate`
- `identity_ambiguity_issue`
- `unresolved_identity_issue`
- `rejected_alias_conflict_issue`
- `automation_policy_governance_candidate`

Allowed `signal_status` values：

- `candidate_only`
- `requires_accountant_confirmation`
- `requires_governance_review`

Optional fields：

- `proposed_display_name`
- `proposed_alias_surface_text`
- `related_entity_ids`
- `proposed_candidate_role`
- `conflicting_evidence_refs`
- `governance_constraint_refs`
- `suggested_accountant_question`

Validation rules：

- `candidate_signal` cannot have `approved`, `confirmed`, `active`, or `auto_applied` as status.
- `supporting_evidence_refs` required unless `signal_type = unresolved_identity_issue` and the reason is explicitly no identity signal exists.
- `proposed_candidate_role` cannot be written as stable role by this node.
- `related_entity_ids` for merge/split candidate must not imply merge/split approval.

Durable memory effect：

- Candidate signal is not durable authority.
- Whether candidate signals are persisted immediately or only carried in runtime handoff is not frozen in this Stage 3; see Open Contract Boundaries.

### 4.3 `downstream_authority_summary`

Purpose：给 downstream nodes 一个 compact authority summary，防止下游误用 identity result。

Consumer / downstream authority：`Rule Match Node`、`Case Judgment Node`、`Coordinator / Pending Node`。

Required fields：

| Field | Meaning |
| --- | --- |
| `can_enter_rule_match` | deterministic rule path 是否允许被尝试 |
| `can_enter_case_judgment` | case judgment 是否可把该 identity state 作为上下文 |
| `can_support_rule_promotion` | 本 identity state 是否可支持 rule promotion candidate |
| `requires_pending_or_review` | 是否需要 pending / review before completion |
| `authority_limit_reason` | authority 上限说明 |

Allowed boolean field values：`true` / `false`。

Validation rules：

- `can_enter_rule_match = true` requires `status = resolved_entity`, `entity_id` present, `alias_status = approved_alias`, confirmed role/context where required, and automation policy allowing rule-based automation.
- `new_entity_candidate` may have `can_enter_case_judgment = true` when current evidence is strong and authority permits, but must have `can_enter_rule_match = false` and `can_support_rule_promotion = false`.
- `resolved_entity_with_unconfirmed_role` must have `can_enter_rule_match = false` unless a future approved contract defines a narrow exception.
- `ambiguous_entity_candidates` and `unresolved` must not support rule match or rule promotion.

Durable memory effect：

- Runtime-only summary.
- Cannot become durable memory by itself.

## 5. Field Authority and Memory Boundary

### 5.1 Source of Truth for Important Fields

| Field / Concept | Source of Truth |
| --- | --- |
| `transaction_id` | `Transaction Identity Node` / transaction identity layer |
| objective transaction basis | Evidence Intake / Preprocessing output with Evidence Log trace |
| raw evidence / receipt / cheque / invoice references | `Evidence Log` |
| stable entity fields | `Entity Log` |
| approved / rejected alias | `Entity Log` as governed by accountant / governance approval |
| confirmed role/context | `Entity Log` with accountant-confirmed or allowed onboarding authority metadata |
| entity lifecycle status | `Entity Log` / approved governance projection |
| automation policy | `Entity Log` / `Governance Log`; upgrades or relaxations require accountant approval |
| governance event state | `Governance Log` |
| accountant intervention / confirmation process | `Intervention Log` |
| final transaction processing audit | `Transaction Log`, written downstream only |

### 5.2 Fields That Can Never Become Durable Memory by This Node

本节点不能把以下字段或判断直接写成 durable memory：

- `confidence`
- `reason`
- `blocking_reason`
- `candidate_role`
- `normalized_display_text`
- `suggested_accountant_question`
- `rule_eligibility`
- `case_context_eligibility`
- LLM semantic comparison rationale
- raw model prompt trace
- rejected candidate list not exposed in contract
- accounting classification implication

这些字段只能作为 runtime handoff、review context 或 candidate explanation。

### 5.3 Fields That Can Become Durable Only After Accountant / Governance Approval

以下内容可以成为 long-term memory，但只能通过 accountant / governance-approved authority path：

- new stable entity
- approved alias
- rejected alias
- confirmed role/context
- entity merge / split result
- entity archive / reactivate result
- automation policy upgrade or relaxation
- active rule creation / modification / deletion / downgrade / promotion

本节点最多提出 candidate signal。

### 5.4 Audit vs Learning / Logging Boundary

`Transaction Log` 是 audit-facing final record：

- 记录最终处理结果和审计轨迹；
- 不参与本节点 runtime decision；
- 不作为 Entity Resolution 的学习来源；
- 不由本节点写入。

`Entity Log`、`Case Log`、`Rule Log`、`Governance Log` 和 `Knowledge Log / Summary Log` 各自有单一职责。
本节点的输出不能把 runtime guess 伪装成这些 logs 的 durable authority。

## 6. Validation Rules

### 6.1 Contract-Level Validation Rules

- Every output must preserve `transaction_id`.
- Every output must identify one and only one `status`.
- `confidence` must be scoped to identity confidence only.
- Every positive identity result must cite `evidence_used`.
- Every blocked or limited result must include `blocking_reason` or `authority_limit_reason`.
- Candidate-only fields must stay candidate-only unless downstream accountant / governance approval changes authority.
- `Transaction Log` must not appear as runtime input.
- Knowledge Summary cannot override Entity Log / Governance Log authority.

### 6.2 Conditions That Make Input Invalid

Input is invalid when:

- `transaction_id` is missing or unstable.
- `evidence_refs` are missing or non-traceable.
- objective transaction basis is missing.
- `direction` is absent or amount sign is used as direction authority.
- profile / structural status says current transaction was already completed structurally.
- candidate alias, pending governance event, or knowledge summary is labeled as approved authority.
- rejected alias conflict is omitted from authority context when known.

### 6.3 Conditions That Make Output Invalid

Output is invalid when:

- `resolved_entity` has no `entity_id`.
- `resolved_entity` uses a `candidate_alias` or `rejected_alias` while claiming `eligible_for_rule_match`.
- `new_entity_candidate` claims rule eligibility or rule promotion support.
- `resolved_entity_with_unconfirmed_role` writes or implies confirmed role.
- `ambiguous_entity_candidates` selects a single winner without resolving authority.
- `unresolved` lacks reason.
- output claims to write stable Entity Log, Rule Log, Case Log, Governance Log, Transaction Log, or Profile.
- output treats `confidence` as accounting classification confidence.

### 6.4 Stop / Ask Conditions for Unresolved Contract Authority

Future Stage 3 revisions or later stages must stop and ask if they need to decide:

- whether candidate entity / alias / role signals are persisted by this node or by downstream memory-update / governance workflow;
- exact threshold for sufficient evidence categories to support stable resolution;
- whether accountant confirmation should retrigger Entity Resolution in the same batch;
- exact rule/case routing for unconfirmed role exceptions;
- how to resolve direct conflict between Knowledge Summary text and current Entity Log authority beyond the rule that Entity Log / Governance Log wins.

## 7. Examples

### 7.1 Valid Minimal Example

```json
{
  "transaction_id": "txn_01HABCEXAMPLE001",
  "status": "resolved_entity",
  "entity_id": "ent_tim_hortons",
  "confidence": "high",
  "reason": "receipt vendor and approved alias both identify Tim Hortons.",
  "matched_alias": "TIMS COFFEE-1234",
  "alias_status": "approved_alias",
  "evidence_used": [
    {
      "signal_type": "receipt_vendor",
      "surface_text": "Tim Hortons",
      "evidence_ref": "ev_receipt_001"
    }
  ],
  "rule_eligibility": "eligible_for_rule_match",
  "case_context_eligibility": "eligible_for_case_context",
  "memory_write_boundary": "runtime_only_no_memory_write",
  "candidate_signals": [],
  "downstream_authority_summary": {
    "can_enter_rule_match": true,
    "can_enter_case_judgment": true,
    "can_support_rule_promotion": true,
    "requires_pending_or_review": false,
    "authority_limit_reason": "Stable entity with approved alias and allowed automation policy."
  }
}
```

### 7.2 Valid Richer Example

```json
{
  "transaction_id": "txn_01HABCEXAMPLE002",
  "status": "new_entity_candidate",
  "confidence": "medium",
  "reason": "Bank text and invoice party identify a vendor not present in Entity Log; evidence is strong enough for case context but not durable authority.",
  "matched_alias": "CLOUD LEDGER SYSTEMS",
  "alias_status": "candidate_alias",
  "candidate_role": "software_vendor",
  "evidence_used": [
    {
      "signal_type": "raw_bank_text",
      "surface_text": "CLOUD LEDGER SYSTEMS",
      "evidence_ref": "ev_bankline_204"
    },
    {
      "signal_type": "invoice_party",
      "surface_text": "Cloud Ledger Systems Inc.",
      "evidence_ref": "ev_invoice_204"
    }
  ],
  "blocking_reason": "New entity candidate cannot support rule match or rule promotion before governance.",
  "rule_eligibility": "blocked_new_entity_candidate",
  "case_context_eligibility": "eligible_for_case_context",
  "memory_write_boundary": "candidate_signal_only",
  "candidate_signals": [
    {
      "signal_type": "new_entity_candidate",
      "signal_status": "requires_accountant_confirmation",
      "proposed_display_name": "Cloud Ledger Systems Inc.",
      "proposed_alias_surface_text": "CLOUD LEDGER SYSTEMS",
      "proposed_candidate_role": "software_vendor",
      "supporting_evidence_refs": ["ev_bankline_204", "ev_invoice_204"],
      "reason": "Current evidence points to a previously unseen vendor."
    }
  ],
  "downstream_authority_summary": {
    "can_enter_rule_match": false,
    "can_enter_case_judgment": true,
    "can_support_rule_promotion": false,
    "requires_pending_or_review": false,
    "authority_limit_reason": "Current evidence may support case judgment, but no stable entity or approved alias exists."
  }
}
```

### 7.3 Invalid Example

```json
{
  "transaction_id": "txn_01HABCEXAMPLE003",
  "status": "new_entity_candidate",
  "entity_id": "ent_new_auto_created",
  "confidence": "high",
  "reason": "LLM says this is probably a new vendor.",
  "alias_status": "candidate_alias",
  "rule_eligibility": "eligible_for_rule_match",
  "memory_write_boundary": "created_stable_entity",
  "candidate_signals": []
}
```

Invalid reasons：

- `new_entity_candidate` cannot support `eligible_for_rule_match`。
- 本节点不能 create stable entity authority。
- `memory_write_boundary = created_stable_entity` is not allowed。
- no traceable `evidence_used`。
- LLM probability alone cannot become durable authority。

## 8. Open Contract Boundaries

- Candidate entity / alias / role / merge-split signals 的 exact persistence locus 尚未冻结：本节点直接写 candidate queue，还是只在 runtime handoff 中返回并由 `Case Memory Update Node` / `Governance Review Node` 落盘。
- stable entity resolution 所需 evidence category threshold 尚未冻结；本 Stage 3 只要求 evidence traceability 和 authority consistency。
- accountant 回答 identity question 后是否 same-batch retrigger Entity Resolution 尚未冻结。
- `resolved_entity_with_unconfirmed_role` 在哪些窄场景可以进入 Case Judgment、Pending 或 Review 的 precise routing 仍属 downstream contract。
- Knowledge Summary 与 Entity Log / Governance Log 冲突时，当前 contract 只冻结 authority order，不冻结修复流程。
- `confidence` 的 exact threshold / calibration 尚未冻结；本 contract 只冻结 compact labels 和语义边界：identity confidence only, not accounting confidence。

## 9. Self-Review

- 已阅读 required repo docs：`AGENTS.md`、`TASK_STATE.md`、`PLANS.md`、`CLAUDE.md`、`DECISIONS.md`、`supporting documents/communication_preferences.md`、`supporting documents/development_workflow.md`、`supporting documents/node_design_roadmap.md`、`new system/new_system.md`。
- 已阅读 prior approved stage docs：`entity_resolution_node__stage_1__functional_intent.md`、`entity_resolution_node__stage_2__logic_and_boundaries.md`。
- 已读取可用 Superpowers docs：`using-superpowers/SKILL.md`、`brainstorming/SKILL.md`；project workflow skill `ai-bookkeeper-node-design-facilitation` 在当前环境不存在，因此按 runner instruction 使用 repo `supporting documents/node_design_roadmap.md` 与本节点 Stage 1/2 docs 作为 workflow authority。
- 已确认 optional `supporting documents/node_design_roadmap_zh.md` 在当前 working tree 中 absent，未虚构该文件内容。
- 已识别本节点 Stage 3 的 gating question：candidate signals 是否由本节点直接持久化。live docs 足以冻结“不创建 durable authority”，但 exact persistence locus 未冻结；因此作为 non-blocking open contract boundary 记录。
- 未定义 Stage 4 execution algorithm、Stage 5 technical implementation map、Stage 6 test matrix、Stage 7 coding-agent task contract。
- 未引入 unsupported product authority。
- 未使用 legacy specs 作为 active baseline。
- 本文件声明本节点不写 `Transaction Log`，且 `Transaction Log` 不参与 runtime decision。
- 除本 Stage 3 target file 外，不应修改任何 repo 文件。
