# Transaction Identity Node — Stage 3：Data Contract Spec

## 1. Stage 范围

本 Stage 3 只定义 `Transaction Identity Node` 的 implementation-facing data contracts。

前置依据：

- `new system/new_system.md`
- `new system/node_stage_designs/transaction_identity_node__stage_1__functional_intent.md`
- `new system/node_stage_designs/transaction_identity_node__stage_2__logic_and_boundaries.md`

本文件把 Stage 1/2 已批准的 permanent transaction identity、same-transaction handling、duplicate import discipline 和 identity issue boundary 转换成输入对象类别、输出对象类别、字段含义、字段 authority、runtime-only / durable-memory 边界、validation rules 和 compact examples。

本阶段不定义：

- step-by-step execution algorithm 或 branch sequence
- exact duplicate threshold、matching score、hash strategy 或 conflict-resolution procedure
- repo module path、class、API、storage engine、DB migration 或代码布局
- Stage 6 test matrix / fixture plan
- coding-agent task contract
- downstream evidence amendment、review trigger 或 reprocessing workflow 的完整规则
- entity、case、rule、accounting、JE 或 governance product authority
- legacy replacement mapping

## 2. Contract Position in Workflow

### 2.1 Upstream handoff consumed

本节点消费 `Evidence Intake / Preprocessing Node` 产出的 runtime evidence foundation：

- `EvidenceFoundationHandoff`
- `ObjectiveNormalizedTransactionBasis`
- `EvidenceAssociationResult`
- `EvidenceQualityIssueSignal`
- raw transaction source / supporting evidence references
- source / import / batch context

这些 upstream records 只提供客观交易结构、evidence references 和材料关联语境。它们不提供 permanent `transaction_id`、entity、rule、case、COA、HST/GST 或 JE authority。

### 2.2 Downstream handoff produced

本节点输出 `transaction_identity_handoff` 给：

- `Profile / Structural Match Node`：当当前交易拥有稳定 `transaction_id` 且没有被 duplicate / identity block 截断时。
- `Coordinator / Pending Node` / `Review Node`：当存在 same-transaction candidate、duplicate candidate、source ambiguity、registry conflict 或 unresolved identity issue 时。
- 后续 audit / memory workflow：仅通过 durable references 追溯 identity decision、evidence refs 和 source context。

本节点不直接触发 entity resolution、rule match、case judgment、JE generation 或 final transaction logging。它只提供这些节点能否继续的 identity-layer input。

### 2.3 Logs / memory stores read

本节点可以读取或消费：

- current runtime evidence foundation
- current batch identity context
- `Evidence Log` references / evidence metadata
- durable transaction identity / ingestion registry 中已存在的 identity records
- source / import context 和 objective association signals

本节点不得读取：

- `Transaction Log` 作为 runtime dedupe decision source
- `Entity Log`、`Case Log`、`Rule Log` 或 `Knowledge Log / Summary Log` 来判断是否同一笔交易
- entity / vendor / business semantics 来替代客观交易身份判断

### 2.4 Logs / memory stores written or candidate-only

本节点唯一允许的 durable write 属于 transaction identity / ingestion registry 语义：

- 新建永久 `transaction_id`
- 将既有 `transaction_id` 与新的 evidence / source context 建立可追溯关联
- 记录 duplicate import、identity candidate 或 identity issue 的 identity-layer outcome

这些写入不属于 `Transaction Log`，不形成 final audit result，也不创建 business memory authority。

本节点只能 candidate-only 输出：

- same-transaction candidate
- duplicate import candidate
- supplemental evidence candidate for existing transaction
- source ambiguity issue
- registry conflict issue
- identity review-needed signal

这些 candidate / issue 不得自动写入 `Entity Log`、`Case Log`、`Rule Log`、`Governance Log` 或 `Profile`。

## 3. Input Contracts

### 3.1 `transaction_identity_request`

**Purpose**

本节点的主 runtime input envelope，表示一组已经完成 evidence intake 的材料需要被分配、复用、阻断或标记为 identity candidate。

**Source authority**

由 workflow orchestrator 根据 `Evidence Intake / Preprocessing Node` 输出和当前 batch context 形成。该 request 不自行创造 transaction identity authority；identity authority 只能由本节点结合 durable identity registry 产生。

**Required fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `identity_request_id` | 本次 identity request 引用 | workflow runtime | runtime-only |
| `client_id` | 当前客户标识 | client / batch context | durable reference |
| `batch_id` | 当前处理批次 | workflow runtime | runtime-only |
| `evidence_handoff_ref` | 上游 `EvidenceFoundationHandoff` 引用 | Evidence Intake / Preprocessing | runtime ref with durable evidence refs |
| `objective_identity_basis` | 用于 identity 判断的客观交易 basis | Evidence Intake / Preprocessing | runtime object with durable evidence refs |
| `evidence_refs` | 支撑当前 identity 判断的 evidence references | `Evidence Log` / evidence foundation | durable references |
| `source_import_context` | source、batch、account、import attempt 等上下文 | importer / workflow runtime | mixed |
| `existing_identity_basis` | registry lookup 后可能相关的既有交易身份语境 | transaction identity / ingestion registry | durable refs |

**Optional fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `association_context` | 上游材料关联、候选关联或 duplicate-looking signal | Evidence Intake / Preprocessing | runtime / evidence context |
| `evidence_issue_context` | evidence quality、missing、conflict、source unclear 等问题 | Evidence Intake / Preprocessing | runtime / evidence context |
| `supplemental_context` | 当前材料可能是后补 evidence 的语境 | workflow / source context | runtime-only unless referenced |
| `request_trace` | runtime diagnostics | workflow runtime | runtime-only |

**Validation / rejection rules**

- `client_id`、`batch_id`、`objective_identity_basis`、`evidence_refs`、`source_import_context`、`existing_identity_basis` 缺失时 input invalid。
- `evidence_refs` 必须能回到 durable evidence source；不能只传自然语言摘要。
- `objective_identity_basis` 必须至少引用一个 usable `ObjectiveNormalizedTransactionBasis`。
- 如果上游 `handoff_status = rejected_invalid_input`，本节点不能伪造 identity decision。
- request 不得携带 asserted final `transaction_id`，除非该值来自 `existing_identity_basis` 中的 durable registry record。
- request 不得携带 entity、COA、HST/GST、rule、case、JE 或 final review conclusion 作为 identity 判断 authority。

**Runtime-only vs durable references**

`transaction_identity_request` 是 runtime-only envelope。它可以引用 durable evidence 和 registry records，但接收 request 不赋予本节点修改 evidence content、business memory 或 final audit records 的权力。

### 3.2 `objective_identity_basis`

**Purpose**

把当前材料中可用于交易身份判断的客观事实集中表达，避免用 vendor/entity 语义或 display description 代替 transaction identity。

**Source authority**

来自 `ObjectiveNormalizedTransactionBasis` 和 durable evidence references。字段 authority 是客观 evidence extraction，不是 accountant / entity / accounting conclusion。

**Required fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `objective_basis_id` | 对应上游 normalized basis | Evidence Intake / Preprocessing | runtime / evidence context |
| `source_material_id` | 当前主要 raw transaction material | Evidence Log / source material | durable evidence reference |
| `date` | 交易日期；必须带 source reference | objective evidence extraction | objective fact with evidence ref |
| `amount_abs` | 金额绝对值 | objective evidence extraction | objective fact |
| `direction` | 资金方向 | objective evidence extraction | objective fact |
| `source_account_ref` | 来源银行/支付账户引用；不是 COA | source evidence / Profile account context when available | durable or evidence reference |
| `raw_description_ref` | 原始描述 reference；可引用空描述状态 | Evidence Log | durable evidence reference |

**Allowed values**

`direction` 允许：

- `inflow`
- `outflow`
- `unknown`

`direction = unknown` 只能支持 blocked / candidate / issue output，不能支持 normal `assigned` identity handoff。

**Optional fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `posted_at` | posted date/time | source evidence | objective fact when present |
| `currency` | currency | source evidence | objective fact when present |
| `source_row_ref` | file、page、row、payload entry 等定位 | source evidence | durable evidence reference |
| `external_transaction_ref` | source system 提供的交易引用 | source system metadata | evidence/source metadata |
| `cheque_number_ref` | cheque number reference when present | evidence source | evidence reference |
| `counterparty_surface_text_refs` | 表面描述文本引用 | evidence signal only | durable evidence refs |
| `normalization_issue_ids` | 解析问题引用 | Evidence Intake / Preprocessing | runtime / evidence context |

**Validation / rejection rules**

- `amount_abs` 必须为正数；金额符号不得和 `direction` 重复表达。
- `date`、`amount_abs`、`source_account_ref` 缺失时，不能输出 normal `assigned` identity handoff。
- `direction = unknown` 时，不能输出 normal `assigned` identity handoff。
- `counterparty_surface_text_refs` 不得被解释为 entity identity、approved alias 或 same-transaction proof。
- `raw_description_ref` 可为空描述 reference；本节点不能要求 canonical `description` 存在。

**Runtime-only vs durable references**

该对象是 runtime handoff。客观字段可被 registry record 引用或 snapshot，但本节点不是原始 evidence source，也不能覆盖上游 objective extraction。

### 3.3 `source_import_context`

**Purpose**

说明当前材料如何进入系统，帮助区分首次导入、重复导入、同源修正、跨来源补证据、historical onboarding 和 runtime processing。

**Source authority**

来自 importer、workflow runtime、upload context 或 onboarding/runtime batch context。

**Required fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `source_context_id` | source context 引用 | workflow runtime | runtime / source metadata |
| `source_channel` | 材料进入渠道 | importer / upload context | source metadata |
| `import_attempt_id` | 本次 import / upload / re-intake attempt | workflow runtime | runtime ref; may be retained |
| `received_at` | 系统接收时间 | workflow / importer | source metadata |
| `source_account_ref` | 来源账户或支付账户引用 | source material / client account context | evidence/profile reference |

**Allowed `source_channel` values**

- `bank_import`
- `payment_account_import`
- `supporting_upload`
- `supplemental_evidence`
- `historical_onboarding`
- `manual_reintake`
- `source_correction`
- `external_import_context`

**Optional fields**

- `source_system_name`
- `source_file_ref`
- `source_batch_ref`
- `prior_import_attempt_refs`
- `related_runtime_transaction_ref`
- `actor_type`; allowed values: `client`, `accountant`, `system_import`, `third_party_source`, `unknown`
- `source_context_note`

**Validation / rejection rules**

- `source_channel` 必须属于允许值。
- `source_context_note` 只能作为 source metadata / evidence context，不能作为 business conclusion。
- `related_runtime_transaction_ref` 只能表示 runtime hint，不能替代 durable `transaction_id`。
- `historical_onboarding` 与 runtime identity 可以使用同一 logical contract，但 exact migration / reconciliation order 不在本 Stage 冻结。

**Runtime-only vs durable references**

`import_attempt_id`、`source_batch_ref`、`prior_import_attempt_refs` 可被 registry record 引用以支持 auditability，但它们不是 transaction identity 本身。

### 3.4 `association_context`

**Purpose**

接收上游对多份材料之间关系的客观关联或候选信号，供本节点判断是否可能属于同一交易、重复材料或补充 evidence。

**Source authority**

来自 `EvidenceAssociationResult` 和 Evidence Intake / Preprocessing 的 objective association discipline。它不提供 confirmed transaction identity authority。

**Required fields when present**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `association_result_ids` | 上游 association result 引用 | Evidence Intake / Preprocessing | runtime / evidence refs |
| `association_statuses` | 上游关联状态列表 | Evidence Intake / Preprocessing | runtime / evidence context |
| `basis_refs` | 支撑关联状态的 evidence refs | Evidence Log | durable refs |

**Allowed `association_statuses` values**

- `confirmed_objective_association`
- `candidate_association`
- `unassociated`
- `conflicting_association`
- `duplicate_material_candidate`

**Optional fields**

- `candidate_strength`
- `conflict_issue_ids`
- `material_ref_ids`
- `association_reason`

**Validation / rejection rules**

- `confirmed_objective_association` 只能表示材料间客观配对成立，不能直接等同 same transaction identity confirmed。
- `candidate_association` 和 `duplicate_material_candidate` 不能支持 automatic duplicate discard。
- `conflicting_association` 必须保留 conflict refs；不能被包装成普通 low-confidence note 后继续 normal assignment。

**Runtime-only vs durable references**

association context 是 runtime handoff。后续可将其 refs 记录到 identity registry outcome，但本节点不能把它写成 business memory。

### 3.5 `existing_identity_basis`

**Purpose**

提供 durable transaction identity / ingestion registry 中可能与当前材料相关的既有身份，用于判断新建、复用、duplicate block、candidate 或 issue。

**Source authority**

来自 transaction identity / ingestion registry。它只提供 transaction identity authority，不提供 entity、rule、case、accounting 或 final logging authority。

**Required fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `lookup_status` | registry lookup 状态 | identity registry lookup | runtime |
| `candidate_identity_records` | 可能相关的既有 identity records | identity registry | durable refs |

**Allowed `lookup_status` values**

- `no_candidate_found`
- `single_candidate_found`
- `multiple_candidates_found`
- `registry_unavailable`
- `registry_inconsistent`

Each `candidate_identity_record` required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `transaction_id` | 既有永久交易 ID | identity registry | durable reference |
| `client_id` | 所属客户 | identity registry | durable reference |
| `registered_objective_basis` | 登记时的客观 identity basis snapshot / refs | identity registry / evidence refs | durable identity record |
| `registered_evidence_refs` | 已绑定 evidence refs | Evidence Log / identity registry | durable refs |
| `identity_record_status` | 该 identity record 当前状态 | identity registry | durable state |

Allowed `identity_record_status` values：

- `active`
- `duplicate_import_recorded`
- `identity_issue_open`
- `superseded_by_registry_correction`

Optional fields：

- `prior_import_attempt_refs`
- `linked_duplicate_refs`
- `open_identity_issue_refs`
- `registry_correction_refs`
- `identity_decision_reason_refs`

**Validation / rejection rules**

- `registry_unavailable` 时，本节点不能输出 durable write pretending registry success。
- `registry_inconsistent` 时，必须输出 blocked / issue result，不能 normal assign or reuse。
- 多个 plausible candidates 存在且无法由客观 basis 安全区分时，不能强行复用其中一个 `transaction_id`。
- `candidate_identity_records.transaction_id` 不得被下游解释为 entity、case 或 accounting authority。

**Runtime-only vs durable references**

`existing_identity_basis` 是 runtime lookup projection。durable source of truth 仍是 identity / ingestion registry record。

### 3.6 `evidence_issue_context`

**Purpose**

把可能限制 identity decision 的 evidence / source / parsing issues 显式传入本节点。

**Source authority**

来自 `EvidenceQualityIssueSignal`、Evidence Intake / Preprocessing、source importer 或 workflow runtime。

**Required fields when present**

- `issue_ids`
- `issue_types`
- `severity`
- `affected_evidence_refs`
- `summary`

Allowed `severity` values：

- `blocks_objective_handoff`
- `allows_handoff_with_issue`
- `informational`

**Validation / rejection rules**

- `blocks_objective_handoff` 存在时，本节点不能输出 normal `assigned` handoff。
- evidence conflict 影响 date、amount、direction、source account 或 source authenticity 时，必须输出 candidate / issue / blocked result。
- issue context 不能自行生成 accountant-facing question；是否提问属于 Coordinator / Review boundary。

## 4. Output Contracts

### 4.1 `transaction_identity_handoff`

**Purpose**

本节点的主 runtime output envelope，向下游说明当前材料是否拥有稳定 transaction identity、是否被 duplicate block、或是否只能作为 identity candidate / issue 处理。

**Consumer / downstream authority**

`Profile / Structural Match Node`、`Coordinator / Pending Node`、`Review Node`、后续 audit / memory workflow。下游只能消费本 handoff 的 transaction identity / issue authority，不能从中推导 entity、rule、case 或 accounting authority。

**Required fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `identity_handoff_id` | 本次 handoff 引用 | Transaction Identity Node | runtime-only |
| `client_id` | 当前客户 | input context | durable reference |
| `batch_id` | 当前批次 | workflow runtime | runtime-only |
| `transaction_identity_status` | 当前 identity gate 状态 | Transaction Identity Node | runtime state |
| `identity_decision_type` | 具体 identity outcome 类型 | Transaction Identity Node | runtime state |
| `evidence_refs` | 支撑 identity outcome 的 evidence refs | Evidence Log / input handoff | durable refs |
| `identity_rationale` | 简短 identity-layer reason | Transaction Identity Node | runtime / registry context |

**Allowed `transaction_identity_status` values**

- `assigned`
- `duplicate_blocked`
- `candidate_only`
- `blocked`

**Allowed `identity_decision_type` values**

- `new_transaction_identity`
- `existing_transaction_identity_reuse`
- `duplicate_import_confirmed`
- `same_transaction_candidate`
- `duplicate_import_candidate`
- `supplemental_evidence_candidate`
- `identity_issue`
- `invalid_identity_input`

**Required conditional fields**

- `transaction_id` required when `transaction_identity_status = assigned`。
- `registry_write_receipt_ref` required when a durable registry write or registry association is completed。
- `duplicate_of_transaction_id` required when `identity_decision_type = duplicate_import_confirmed`。
- `candidate_identity_refs` required when `identity_decision_type` is `same_transaction_candidate` or `duplicate_import_candidate` and candidates exist。
- `identity_issue_signal_refs` required when `transaction_identity_status = candidate_only` or `blocked` due to issue。

**Optional fields**

- `objective_identity_snapshot`
- `source_import_context_ref`
- `association_context_refs`
- `evidence_issue_refs`
- `downstream_allowed_next_nodes`
- `runtime_notes`

Allowed `downstream_allowed_next_nodes` values：

- `profile_structural_match`
- `coordinator_pending`
- `review`
- `identity_issue_handling`
- `stop_no_downstream_processing`

**Validation rules**

- `transaction_identity_status = assigned` 必须有 exactly one `transaction_id`。
- `assigned` handoff 不得同时包含 `duplicate_of_transaction_id`。
- `duplicate_blocked` 不得让 `profile_structural_match` 作为 allowed next node。
- `candidate_only` 不得被下游当作 confirmed identity 或 confirmed duplicate。
- `blocked` 必须说明 blocking issue，且不得输出 usable downstream `transaction_id`。
- handoff 不得包含 entity、COA、HST/GST、rule result、case judgment、JE 或 final audit conclusion。

**Memory boundary**

`transaction_identity_handoff` 是 runtime-only envelope。`transaction_id` 和 registry refs 是 durable references，但 handoff 本身不是 `Transaction Log`，也不是 business memory。

### 4.2 `transaction_identity_registry_record`

**Purpose**

表达本节点允许写入的 durable identity / ingestion registry record 的 logical contract。

**Consumer / downstream authority**

未来 identity lookup、dedupe discipline、evidence amendment / reprocessing boundary 和 audit traceability 可以引用该 record。它只提供 transaction identity authority。

**Required fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `transaction_id` | 永久交易 ID；新建时采用 `txn_<ULID>` 语义 | Transaction Identity Node | durable primary identity |
| `client_id` | 所属客户 | input context | durable reference |
| `identity_record_status` | identity record 状态 | Transaction Identity Node / registry | durable state |
| `registered_at` | 登记时间 | system time | durable metadata |
| `registered_from_request_id` | 来源 identity request | workflow runtime | durable trace ref |
| `objective_identity_basis_refs` | 支撑 identity 的 objective basis refs | Evidence Intake / Preprocessing | durable refs |
| `evidence_refs` | 绑定到该 identity 的 evidence refs | Evidence Log | durable refs |
| `source_import_context_refs` | source / import context refs | importer / workflow | durable refs |
| `identity_reason` | 简短 identity-layer reason | Transaction Identity Node | durable identity metadata |

**Allowed `identity_record_status` values**

- `active`
- `duplicate_import_recorded`
- `identity_issue_open`
- `superseded_by_registry_correction`

**Optional fields**

- `duplicate_of_transaction_id`
- `linked_duplicate_import_refs`
- `supplemental_evidence_refs`
- `open_identity_issue_refs`
- `prior_identity_record_refs`
- `registry_correction_refs`
- `objective_identity_snapshot`
- `source_fingerprint_refs`

**Validation rules**

- 新建 normal transaction identity 时，`transaction_id` 必须存在且稳定；不得用 date-seq ID。
- `transaction_id` 不能由 downstream node、LLM、accountant note 或 source display text 分配。
- `evidence_refs` 不能为空。
- `duplicate_import_recorded` 必须引用 `duplicate_of_transaction_id` 或明确说明为什么只能记录 unresolved duplicate issue。
- `identity_issue_open` 必须引用 issue refs。
- registry record 不得保存 entity、COA、HST/GST、rule、case、JE 或 final classification conclusion。
- registry record 不能重写或覆盖 raw evidence；只能引用 evidence。

**Memory boundary**

这是本节点允许的 durable write boundary。它属于 transaction identity / ingestion registry，不属于 `Transaction Log`，也不能被 `Case Log`、`Rule Log` 或 `Knowledge Log` 当作 learning source。

### 4.3 `identity_registry_write_receipt`

**Purpose**

给 workflow 一个 runtime-only receipt，说明 identity registry mutation / association 是否完成。

**Consumer / downstream authority**

workflow orchestrator 和 downstream nodes。receipt 只证明 identity-layer write status，不提供 business authority。

**Required fields**

- `registry_write_receipt_id`
- `write_status`
- `transaction_id` when applicable
- `registry_record_ref`
- `written_at`
- `write_summary`

Allowed `write_status` values：

- `created_new_identity`
- `reused_existing_identity`
- `recorded_duplicate_import`
- `recorded_identity_issue`
- `write_blocked`

Optional fields：

- `blocked_reason`
- `candidate_identity_refs`
- `issue_signal_refs`

**Validation rules**

- `write_status = write_blocked` 必须说明 `blocked_reason`，且不得被下游当作 assigned identity。
- receipt 不得作为 replacement source of truth；durable source of truth 是 registry record。

**Memory boundary**

该 receipt 是 runtime-only。可被后续 audit context 引用，但不是 final audit log。

### 4.4 `identity_issue_signal`

**Purpose**

表达 identity layer 发现的 candidate、冲突、来源不清、registry inconsistency 或 evidence amendment uncertainty，供 Coordinator / Review / identity issue handling 使用。

**Consumer / downstream authority**

`Coordinator / Pending Node`、`Review Node`、可能的 identity issue handling workflow。该 signal 不是 accountant question、governance event 或 final audit record。

**Required fields**

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `identity_issue_id` | issue signal 引用 | Transaction Identity Node | runtime / possible registry ref |
| `issue_type` | issue 类型 | Transaction Identity Node | runtime state |
| `severity` | 对 downstream identity safety 的影响 | Transaction Identity Node | runtime state |
| `affected_evidence_refs` | 涉及 evidence refs | Evidence Log | durable refs |
| `summary` | 简短说明 | Transaction Identity Node | runtime / review context |

Allowed `issue_type` values：

- `same_transaction_candidate`
- `duplicate_import_candidate`
- `supplemental_evidence_candidate`
- `source_ambiguity`
- `objective_fact_conflict`
- `registry_inconsistency`
- `registry_unavailable`
- `overmerge_risk`
- `invalid_identity_input`

Allowed `severity` values：

- `blocks_downstream_processing`
- `requires_identity_review`
- `allows_downstream_with_identity_caution`
- `informational`

Optional fields：

- `candidate_identity_refs`
- `conflicting_values`
- `source_context_refs`
- `recommended_downstream_owner`; allowed values: `coordinator_pending`, `review`, `identity_issue_handling`, `workflow_orchestrator`
- `human_readable_explanation`

**Validation rules**

- `objective_fact_conflict` 必须列出 conflicting values / refs。
- `registry_inconsistency` 必须阻止 normal assigned handoff。
- `same_transaction_candidate`、`duplicate_import_candidate` 和 `supplemental_evidence_candidate` 不得包含 confirmed reuse / confirmed duplicate language。
- signal 不得写入 `Governance Log`，不得批准 registry correction，且不得自行形成 accountant-facing question。

**Memory boundary**

`identity_issue_signal` 可以被 registry record 或 review package 引用，但它本身不改变 durable business memory。

## 5. Field Authority and Memory Boundary

### 5.1 Source of truth for important fields

- `transaction_id` 的 source of truth 是 Transaction Identity / ingestion registry。新建永久 ID 采用 `txn_<ULID>` 语义。
- `client_id` 来自 client / batch context。
- `date`、`amount_abs`、`direction`、`source_account_ref` 来自 Evidence Intake / Preprocessing 的 objective extraction 和 source evidence。
- `evidence_refs` 的 source of truth 是 `Evidence Log` / evidence preservation layer。
- `source_import_context` 的 authority 来自 importer、upload context、batch runtime 或 onboarding/runtime context。
- `existing_identity_basis` 的 authority 来自 durable identity registry lookup。
- `identity_decision_type` 和 `transaction_identity_status` 的 authority 只限于 transaction identity / dedupe layer。

### 5.2 Fields that can never become durable business memory by this node

本节点不能把以下字段或结论写成 Entity / Case / Rule / Governance / Profile memory：

- counterparty / vendor / payee entity conclusion
- approved alias
- confirmed role/context
- COA account
- HST/GST treatment
- classification confidence
- case judgment rationale
- deterministic rule result
- JE result
- accountant approval / correction
- automation policy change
- governance approval

### 5.3 Fields that can become durable only through accountant/governance approval

如果 identity issue 暴露了可能的长期业务记忆变化，下列变化只能通过后续 accountant / governance authority path：

- entity merge / split
- alias approval / rejection
- role confirmation
- rule promotion / modification / deletion / downgrade
- automation policy upgrade / relaxation
- profile structural fact confirmation
- case memory write based on completed final outcome

`Transaction Identity Node` 最多输出 issue / candidate context，不能执行这些变化。

### 5.4 Audit vs learning/logging boundary

- `Transaction Log` 是 final audit-facing record，不参与本节点 runtime dedupe。
- identity registry 是 runtime identity / ingestion discipline 的 source of truth，不是 final audit log。
- identity registry 可以支持 audit traceability，但不能替代 Transaction Logging Node 的 final processing record。
- duplicate import handling 防止重复交易对象，不等于删除、丢弃或覆盖 raw evidence。
- identity candidate / issue 可以进入 review context，但不能作为 learning layer 或 rule promotion evidence。

## 6. Validation Rules

### 6.1 Contract-level validation rules

- 每个 normal downstream transaction item 必须绑定 stable `transaction_id`，或者被明确标记为 `duplicate_blocked` / `candidate_only` / `blocked`。
- `amount_abs` 必须是正数；direction 必须显式表达。
- `evidence_refs` 必须非空且可追溯。
- `Transaction Log`、`Entity Log`、`Case Log`、`Rule Log`、`Governance Log`、`Knowledge Log / Summary Log` 不能作为 identity decision source。
- LLM output、natural-language summary、vendor similarity 或 business semantics 不能创建 confirmed transaction identity。
- candidate-only signal 不能被当作 confirmed identity decision。

### 6.2 Conditions that make the input invalid

Input invalid if：

- 缺少 `client_id`、`batch_id`、`objective_identity_basis`、`evidence_refs`、`source_import_context` 或 `existing_identity_basis`。
- 上游 evidence handoff 已经 `rejected_invalid_input`。
- date、amount、direction 或 source account 的 objective basis 缺失到无法支持 identity assignment，且 request 仍要求 normal assignment。
- `existing_identity_basis.lookup_status = registry_inconsistent` 但 request 要求 normal reuse / new assignment。
- request 声称 entity、COA、rule、case、JE 或 accountant conclusion 是 identity authority。
- `evidence_refs` 只是不可追溯摘要。

### 6.3 Conditions that make the output invalid

Output invalid if：

- `transaction_identity_status = assigned` 但缺少 exactly one `transaction_id`。
- `assigned` 同时声明 `duplicate_of_transaction_id`。
- `duplicate_blocked` 仍允许普通 downstream classification path。
- `candidate_only` 输出被写成 confirmed reuse、confirmed duplicate 或 final discard。
- output 写入或修改 Entity / Case / Rule / Governance / Profile / Transaction Log。
- registry record 保存 business classification、HST/GST、JE 或 final review result。
- `blocked` / `identity_issue` 没有 reason 或 issue refs。

### 6.4 Stop / ask conditions for unresolved contract authority

后续 Stage 或 implementation 如果遇到以下情况，不能自行填补为产品结论：

- 需要冻结 exact same-transaction / duplicate threshold。
- 需要决定 supplemental evidence 对既有 transaction 的 amendment、reprocessing 或 review trigger。
- 需要决定 registry correction / merge / split transaction identity 的 authority path。
- 需要决定 historical onboarding identity 与 runtime identity 的 reconciliation order。
- 需要让 candidate-only identity 继续进入 operational classification 的条件。
- 需要改变 `Transaction Log` 不参与 runtime decision 的边界。

## 7. Examples

### 7.1 Valid minimal example

```yaml
transaction_identity_request:
  identity_request_id: ident_req_001
  client_id: client_abc
  batch_id: batch_2026_05_06
  evidence_handoff_ref: handoff_ev_001
  objective_identity_basis:
    objective_basis_id: obj_001
    source_material_id: raw_bank_001
    date: "2026-04-30"
    amount_abs: "42.15"
    direction: outflow
    source_account_ref: bank_account_main
    raw_description_ref: ev_desc_001
  evidence_refs: [ev_bank_001]
  source_import_context:
    source_context_id: src_ctx_001
    source_channel: bank_import
    import_attempt_id: import_001
    received_at: "2026-05-06T10:00:00Z"
    source_account_ref: bank_account_main
  existing_identity_basis:
    lookup_status: no_candidate_found
    candidate_identity_records: []

transaction_identity_handoff:
  identity_handoff_id: ident_handoff_001
  client_id: client_abc
  batch_id: batch_2026_05_06
  transaction_identity_status: assigned
  identity_decision_type: new_transaction_identity
  transaction_id: txn_01JTXN0001
  evidence_refs: [ev_bank_001]
  registry_write_receipt_ref: reg_receipt_001
  identity_rationale: "No existing identity candidate found for the objective transaction basis."
  downstream_allowed_next_nodes: [profile_structural_match]
```

Why valid：客观交易 basis 完整，registry 未找到候选，本节点只分配 transaction identity，没有产生 entity、rule、case 或 accounting conclusion。

### 7.2 Valid richer example

```yaml
transaction_identity_request:
  identity_request_id: ident_req_010
  client_id: client_abc
  batch_id: batch_2026_05_06
  evidence_handoff_ref: handoff_ev_010
  objective_identity_basis:
    objective_basis_id: obj_010
    source_material_id: raw_bank_010_reimport
    date: "2026-04-30"
    amount_abs: "250.00"
    direction: outflow
    source_account_ref: bank_account_main
    raw_description_ref: ev_desc_010b
    source_row_ref: bank_csv_row_88
  evidence_refs: [ev_bank_010b]
  source_import_context:
    source_context_id: src_ctx_010
    source_channel: manual_reintake
    import_attempt_id: import_003
    received_at: "2026-05-06T11:15:00Z"
    source_account_ref: bank_account_main
    prior_import_attempt_refs: [import_001]
  association_context:
    association_result_ids: [assoc_010]
    association_statuses: [duplicate_material_candidate]
    basis_refs: [ev_bank_010, ev_bank_010b]
  existing_identity_basis:
    lookup_status: single_candidate_found
    candidate_identity_records:
      - transaction_id: txn_01JTXN0100
        client_id: client_abc
        registered_objective_basis: obj_010_original
        registered_evidence_refs: [ev_bank_010]
        identity_record_status: active

transaction_identity_handoff:
  identity_handoff_id: ident_handoff_010
  client_id: client_abc
  batch_id: batch_2026_05_06
  transaction_identity_status: duplicate_blocked
  identity_decision_type: duplicate_import_confirmed
  duplicate_of_transaction_id: txn_01JTXN0100
  evidence_refs: [ev_bank_010b]
  registry_write_receipt_ref: reg_receipt_010
  identity_rationale: "Re-intake material matches an existing registered transaction identity."
  downstream_allowed_next_nodes: [stop_no_downstream_processing]
```

Why valid：重复导入被 identity layer 阻断，避免产生第二个交易对象；但 evidence ref 仍保留为可追溯材料，不删除 raw evidence，也不写 Transaction Log。

### 7.3 Invalid example

```yaml
transaction_identity_handoff:
  identity_handoff_id: ident_handoff_bad
  client_id: client_abc
  batch_id: batch_2026_05_06
  transaction_identity_status: assigned
  identity_decision_type: existing_transaction_identity_reuse
  transaction_id: txn_20260430_001
  evidence_refs: [ev_bank_bad]
  identity_rationale: "Looks like the same vendor, so reuse the old transaction."
  entity_id: ent_tim_hortons
  coa_account: Meals and Entertainment
  downstream_allowed_next_nodes: [profile_structural_match]
```

Invalid reasons：

- `transaction_id` 使用 date-seq style，不符合永久 `txn_<ULID>` 语义。
- 用 vendor/entity 相似性确认 transaction identity，越过 identity authority。
- output 混入 `entity_id` 和 COA conclusion。
- rationale 不是客观交易身份依据。

## 8. Open Contract Boundaries

- Exact same-transaction / duplicate threshold 未冻结：本 Stage 只定义 contract states，不定义匹配算法、score 或阈值。
- Evidence amendment timing 未冻结：既有 `transaction_id` 收到 supplemental evidence 时，是 identity association、evidence amendment、review trigger 还是 reprocessing trigger，仍需后续阶段定义。
- Identity registry storage shape 未冻结：本文件定义 logical record，不定义 DB、index、migration 或 file layout。
- Historical onboarding identity 与 runtime identity 的 reconciliation order 未冻结。
- Registry correction / transaction identity merge-split authority path 未完整定义；当前只要求不能由本节点用 candidate signal 自动修正。
- `candidate_only` 是否允许某些受限下游继续处理未冻结；当前 contract 只要求不得当作 confirmed identity 或 duplicate。
- Evidence Log 写入时点与 identity registry 绑定时点未冻结；当前 contract 只要求所有 identity output 必须保留可追溯 evidence refs。

## 9. Self-Review

- 已阅读 required docs：`AGENTS.md`、`TASK_STATE.md`、`PLANS.md`、`CLAUDE.md`、`DECISIONS.md`、`supporting documents/communication_preferences.md`、`supporting documents/development_workflow.md`、`supporting documents/node_design_roadmap.md`、`new system/new_system.md`。
- 已阅读本节点 prior approved docs：Stage 1 functional intent 与 Stage 2 logic and boundaries。
- 已读取可用 Superpowers docs：`using-superpowers/SKILL.md`、`brainstorming/SKILL.md`；project workflow skill `ai-bookkeeper-node-design-facilitation` 在当前环境不存在，因此按 runner instruction 使用 repo `supporting documents/node_design_roadmap.md` 与本节点 Stage 1/2 docs 作为 workflow authority。
- 已确认 optional `supporting documents/node_design_roadmap_zh.md` 在 working tree 中缺失；未发明该文件内容。
- 本文件只做 Stage 3 data contract，没有进入 Stage 4 execution algorithm、Stage 5 technical map、Stage 6 fixtures/tests 或 Stage 7 coding-agent task contract。
- 未定义 repo module path、storage engine、DB migration、class、API 或 implementation layout。
- 未把 `Transaction Log` 作为 runtime decision source。
- 未赋予本节点 Entity / Case / Rule / Governance / Profile / Transaction Log 写入权。
- 未发明 unsupported product authority；未把 open contract boundary 伪装成 finalized decision。
- 未读取或迁移 legacy specs；未使用 historical drafts 作为 active baseline。
- 若未 blocked，本次只写入目标文件：`new system/node_stage_designs/transaction_identity_node__stage_3__data_contract.md`。
