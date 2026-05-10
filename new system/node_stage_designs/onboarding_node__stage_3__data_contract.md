# Onboarding Node — Stage 3：Data Contract Spec

## 1. Stage 范围

本 Stage 3 只定义 `Onboarding Node` 的 implementation-facing data contract。

前置依据是：

- `new system/new_system.md`
- `new system/node_stage_designs/onboarding_node__stage_1__functional_intent.md`
- `new system/node_stage_designs/onboarding_node__stage_2__logic_and_boundaries.md`

本文件把 Stage 1/2 已批准的 onboarding behavior boundary 转换为：

- input object / file / record categories
- output object / record categories
- required / optional fields
- allowed enum / state values
- field meaning 和 source authority
- runtime-only / durable-memory boundary
- validation rules
- compact valid / invalid examples
- non-blocking open contract boundaries

本阶段不定义：

- step-by-step execution algorithm 或 branch sequence
- technical implementation map、repo module path、class、API、storage engine、DB migration 或 code file layout
- test matrix、fixture plan 或 coding-agent task contract
- prompt structure、tool interface、threshold number 或 exact matching algorithm
- 新 product authority
- legacy replacement mapping
- legacy onboarding spec 迁移规则

## 2. Contract Position in Workflow

`Onboarding Node` 位于新客户主 workflow 之前。

它消费历史初始化材料，把这些材料转化为 evidence-first 的初始记忆基础和候选治理事项。它不是 runtime classification gate，也不是 accountant / governance approval gate。

### 2.1 Upstream handoff consumed

本节点消费 `onboarding_initialization_request`。

该 request 表示：

- 当前客户处于初始化、迁移、历史材料导入或等价 bootstrap context；
- 输入材料是历史材料，不是主 workflow 中的新交易 runtime handoff；
- 材料需要被保留为可追溯 evidence，并被解析为 profile、entity、case、knowledge、rule / governance candidate 的初始化基础；
- request 本身不创造 accountant approval、governance approval 或 durable accounting conclusion。

典型 upstream source 包括：

- client onboarding / migration workflow
- accountant 提供的历史账本、说明、确认或补充材料
- historical bank statement / receipt / cheque / contract package
- prior customer context import

### 2.2 Downstream handoff produced

本节点输出 `onboarding_initialization_result`，供后续 workflow 使用。

主要 downstream consumers：

- `Evidence Intake / Preprocessing Node`：读取初始化阶段形成的 evidence foundation 或 historical transaction basis；不把 Onboarding summary 当作 raw evidence。
- `Transaction Identity Node`：读取 historical transaction identity seed 或 dedupe context；不把 Onboarding 输出当作新交易的最终处理结果。
- `Profile / Structural Match Node`：读取已确认 profile facts 或 profile candidates 的 review status；未确认 candidate 不得作为稳定 structural truth。
- `Entity Resolution Node`：读取 initial entity foundation、candidate aliases、candidate roles 和 ambiguity notes；candidate alias / role 不能支持 rule match。
- `Rule Match Node`：只读取 accountant / governance approved active rules；不得消费 rule candidate 作为 deterministic rule。
- `Case Judgment Node`：读取 accountant-derived historical case foundation 和 customer knowledge summary；summary 不能替代 case evidence 或 rule authority。
- `Review Node` / `Governance Review Node`：消费 profile、entity、alias、role、rule、automation-policy、merge/split 和 conflict candidates。
- `Knowledge Compilation Node`：后续可重新编译或刷新 customer knowledge summary seed。

### 2.3 Logs / memory stores read

本节点可以读取或消费：

- historical raw evidence files / records：银行流水、小票、支票、合同、发票、历史账本原文、accountant 原话。
- existing `Evidence Log` references：如果客户迁移或补材料场景中已有 evidence records。
- existing `Profile` context：已知客户结构事实、tax config、bank accounts、loan / employee / owner-use context。
- existing `Entity Log` context：迁移已有 entity、alias、role、status、authority、automation_policy 和 risk flags。
- existing `Case Log` context：迁移已有 historical cases 或 prior accountant-corrected cases。
- existing `Rule Log` context：仅用于避免重复 rule candidate 或识别 authority conflict，不用于自行执行 rule match。
- existing `Governance Log` / `Intervention Log` context：已批准、已拒绝、待处理或近期 accountant 说明。
- `Knowledge Log / Summary Log`：只作为辅助背景，不能作为 deterministic authority。

本节点不得读取 `Transaction Log` 来生成 runtime decision、learning authority 或 rule source。若迁移材料中包含历史交易审计记录，只能作为 historical audit reference，不得把它混同为当前新交易处理日志。

### 2.4 Logs / memory stores written or candidate-only

本节点可以直接建立的 durable foundation 只限于 Stage 1/2 已允许的初始化语义：

- `Evidence Log` foundation：保存原始材料、source metadata 和 evidence references；不保存业务结论。
- historical transaction identity seed / basis：为历史材料中的交易提供稳定引用或 dedupe basis；不等于当前 runtime transaction finalization。
- accountant-derived historical `Case Log` foundation：只在历史处理结果来自 accountant-prepared books、accountant instruction 或等价高 authority source 时成立。
- sufficiently supported initial `Entity Log` foundation：只回答“是谁”和 role/context authority，不保存 COA / HST / JE 结论。
- `Knowledge Log / Summary Log` seed：可读客户知识摘要；不能作为 deterministic rule source。

本节点只能 candidate-only 输出：

- profile facts that require confirmation
- entity / alias / role governance candidates
- rule candidates 或 initial rule approval candidates
- automation policy candidates
- entity merge / split candidates
- conflict notes requiring accountant review
- evidence quality / traceability / authority issues

本节点不得直接写入或修改：

- 新交易的 `Transaction Log`
- active `Rule Log` authority
- approved alias / rejected alias authority
- stable role confirmation，除非 active docs 明确允许的 `accountant_derived_role` 且保留 source / authority metadata
- entity merge / split mutation
- automation policy upgrade or relaxation
- stable `Profile` truth，除非已有明确 accountant authority 或 active docs 已支持该 truth
- journal entry、review-facing report 或 final accounting output

## 3. Input Contracts

### 3.1 `onboarding_initialization_request`

Purpose：Onboarding Node 的主 input envelope，定义一次客户初始化 / 历史导入请求的边界。

Source authority：client onboarding workflow、migration workflow、accountant instruction 或等价 workflow orchestrator。该 request 只承载材料和 authority context，不创造 accountant approval。

Required fields：

| Field | Meaning | Source authority | Runtime / Durable |
| --- | --- | --- | --- |
| `onboarding_request_id` | 本次 onboarding request 标识 | workflow runtime | runtime-only，可被输出引用 |
| `client_id` | 当前客户标识 | client / onboarding context | durable reference |
| `onboarding_scope` | 初始化范围 | workflow / accountant instruction | runtime contract boundary |
| `material_package_refs` | 历史材料包引用列表 | uploader / accountant / migration workflow | durable evidence-source references |
| `source_authority_context` | 材料来源和 authority 分类 | accountant / workflow / imported records | runtime view over source authority |
| `requested_outputs` | 本次 request 期望建立或评估的 output categories | workflow / user instruction | runtime |

Allowed `onboarding_scope` values：

- `new_client_initialization`
- `client_migration`
- `historical_backfill`
- `re_onboarding_candidate`
- `incremental_historical_import_candidate`

`re_onboarding_candidate` 和 `incremental_historical_import_candidate` 只是 contract-level 标记；是否复用本节点完整 trigger boundary 仍是 Open Contract Boundary。

Allowed `requested_outputs` values：

- `evidence_foundation`
- `historical_transaction_basis`
- `profile_candidates`
- `entity_foundation`
- `historical_case_foundation`
- `knowledge_summary_seed`
- `rule_governance_candidates`
- `conflict_review_package`

Optional fields：

| Field | Meaning | Source authority | Runtime / Durable |
| --- | --- | --- | --- |
| `batch_id` | 初始化批次标识 | workflow runtime | runtime / batch reference |
| `accountant_id` | 提供或确认材料的 accountant | accountant / firm context | durable reference when persisted |
| `client_contact_refs` | 客户联系人或 client-provided note references | onboarding workflow | durable refs where applicable |
| `existing_memory_refs` | 迁移或补材料时可引用的既有 Profile / Entity / Case / Rule / Governance refs | existing durable stores | durable references |
| `authority_limits` | 本次 request 明确禁止或限制的 authority changes | accountant / governance / workflow policy | runtime view over durable policy |
| `request_notes` | 人类可读补充说明 | workflow runtime | runtime-only |

Validation / rejection rules：

- `onboarding_request_id`、`client_id`、`onboarding_scope`、`material_package_refs`、`source_authority_context` 缺失时，input invalid。
- `material_package_refs` 不能为空；空材料不能生成初始化记忆，只能返回 invalid / blocked result。
- `onboarding_scope` 不能表示普通 runtime transaction classification；若输入是新交易 runtime handoff，应拒绝并交由主 workflow。
- `source_authority_context` 必须能区分 raw evidence、accountant-processed historical basis、accountant instruction、client statement、system inference 和 migrated context。
- `requested_outputs` 不能要求 Onboarding 直接批准 active rule、automation policy upgrade、entity merge/split、unconfirmed profile truth 或 final journal entry。

Runtime-only vs durable references：

- request envelope 是 runtime-only。
- `client_id`、material refs、existing memory refs 和 accountant refs 是 durable references。
- 本节点不能仅凭 request metadata 产生 durable business conclusion；所有 durable output 必须绑定 material evidence 和 source authority。

### 3.2 `historical_material_package`

Purpose：描述 Onboarding 可消费的历史材料文件 / 记录类别，并保留 source、traceability 和 material quality。

Source authority：上传材料、accountant-provided package、client migration export、historical data import。

Required fields：

| Field | Meaning | Source authority | Runtime / Durable |
| --- | --- | --- | --- |
| `material_ref` | 原始材料引用 | evidence ingestion / upload workflow | durable evidence-source reference |
| `material_type` | 材料类型 | uploader / parser / workflow | runtime classification with durable ref |
| `source_actor_type` | 谁提供该材料 | onboarding workflow | runtime authority input |
| `source_authority_category` | 材料 authority 分类 | workflow / accountant context | runtime authority input |
| `received_at` | 材料接收时间 | workflow runtime | durable metadata if persisted |
| `traceability_status` | 是否可追溯到原始材料 | evidence intake / workflow | runtime validation |

Allowed `material_type` values：

- `bank_statement`
- `historical_ledger`
- `receipt`
- `cheque`
- `invoice`
- `contract`
- `accountant_note`
- `client_note`
- `prior_system_export`
- `other_historical_evidence`

Allowed `source_actor_type` values：

- `accountant`
- `client`
- `firm_staff`
- `system_migration`
- `unknown`

Allowed `source_authority_category` values：

- `raw_evidence`
- `accountant_processed_books`
- `accountant_instruction`
- `client_statement`
- `system_migrated_context`
- `system_inferred`
- `unknown_authority`

Allowed `traceability_status` values：

- `traceable_to_original`
- `traceable_to_accountant_source`
- `derived_with_source_refs`
- `summary_only_insufficient_trace`
- `missing_source`

Optional fields：

| Field | Meaning | Source authority | Runtime / Durable |
| --- | --- | --- | --- |
| `covered_period` | 材料覆盖日期范围 | parser / accountant / file metadata | runtime / durable metadata |
| `currency` | 材料币种 | parser / statement metadata | runtime |
| `account_refs` | 材料关联银行账户、ledger account 或 profile account ref | material metadata / accountant | durable refs where available |
| `file_hash_or_import_fingerprint` | 去重或追溯指纹 | deterministic intake | durable technical metadata if persisted |
| `parse_quality_flags` | 解析质量或缺页、OCR、格式问题 | parser / intake workflow | runtime |
| `linked_material_refs` | 同一历史交易相关的 receipt、cheque、ledger、bank refs | evidence intake / workflow | durable refs |

Validation / rejection rules：

- `material_ref` 必须可回到原始材料或 accountant source；summary-only 材料不能支持 stable entity、confirmed case 或 rule candidate authority。
- `source_authority_category = system_inferred` 的材料不能单独支持 accountant-derived case、stable role 或 active rule candidate。
- `source_actor_type = unknown` 或 `source_authority_category = unknown_authority` 时，只能作为 weak evidence 或 review context。
- `traceability_status = missing_source` 时，不得产生 durable memory write；最多产生 invalid / evidence gap issue。

Runtime-only vs durable references：

- `historical_material_package` 的分类 envelope 是 runtime-only。
- `material_ref`、linked refs、hash / fingerprint 和 persisted source metadata 可以成为 durable evidence references。

### 3.3 `historical_transaction_basis`

Purpose：把历史材料中可识别的交易整理为客观交易基础和可追溯 evidence set，供 identity、entity、case 和 candidate evaluation 使用。

Source authority：historical bank statements、historical ledger、receipts、cheques、invoices、contracts、accountant-prepared books。

Required fields：

| Field | Meaning | Source authority | Runtime / Durable |
| --- | --- | --- | --- |
| `historical_transaction_ref` | 历史交易临时引用或既有导入引用 | onboarding workflow | runtime, may be linked to durable identity |
| `client_id` | 客户标识 | onboarding request | durable reference |
| `objective_transaction_basis` | 客观交易字段集合 | historical materials / parser | runtime object with durable evidence refs |
| `evidence_refs` | 支撑该历史交易的 evidence refs | Evidence Log / material package | durable references |
| `source_authority_category` | 本历史交易处理结果的 authority 分类 | source context | runtime authority input |
| `traceability_status` | 交易记录是否可追溯 | evidence intake / workflow | runtime validation |

`objective_transaction_basis` required fields：

| Field | Meaning | Source authority |
| --- | --- | --- |
| `transaction_date` | 交易日期或历史记录日期 | bank / ledger / evidence |
| `amount` | 绝对值金额 | bank / ledger / evidence |
| `direction` | 资金方向 | bank / ledger / evidence |
| `currency` | 币种 | bank / ledger / evidence |
| `bank_account_ref` | 银行账户或历史账户引用 | bank / profile / ledger |

Allowed `direction` values：

- `inflow`
- `outflow`
- `transfer_unknown_direction`
- `unknown`

Optional fields：

| Field | Meaning | Source authority | Runtime / Durable |
| --- | --- | --- | --- |
| `historical_transaction_id_seed` | 可用于稳定 identity 的 seed / dedupe basis | Transaction Identity / onboarding workflow | durable identity basis if accepted |
| `raw_description` | 银行原始描述 | bank statement | durable evidence text/ref |
| `ledger_description` | 历史账本描述 | accountant-prepared books / ledger | durable evidence text/ref |
| `receipt_vendor_text` | receipt vendor 表面文本 | receipt evidence | durable evidence text/ref |
| `cheque_payee_text` | cheque payee 表面文本 | cheque evidence | durable evidence text/ref |
| `accountant_classification_context` | 历史会计处理结果摘要和 refs | accountant-processed books / instruction | durable refs + runtime summary |
| `linked_transaction_refs` | 可能重复、拆分、配对或内部转账相关历史交易 | identity / onboarding workflow | runtime with durable refs |
| `quality_flags` | 缺字段、冲突、低质量解析、方向不明等 | deterministic intake / parser | runtime |

Validation / rejection rules：

- `amount` 必须采用 absolute amount + explicit `direction`；不得用正负号隐含方向。
- `transaction_date`、`amount`、`currency`、`bank_account_ref` 缺失时，不能形成正常 historical transaction basis；可以保留 evidence issue。
- `direction = unknown` 时不能支持 structural profile truth、stable case conclusion 或 rule candidate，除非 accountant source 明确补足。
- `accountant_classification_context` 只有在 source authority 是 `accountant_processed_books` 或 `accountant_instruction` 时，才能支持 historical case foundation。
- historical transaction basis 不得写入新交易 `Transaction Log`。

Runtime-only vs durable references：

- historical transaction basis envelope 是 runtime-only。
- accepted evidence refs 和 identity seed 可以成为 durable references。
- 本节点不能把历史交易 basis 变成 final current transaction processing record。

### 3.4 `accountant_processed_historical_basis`

Purpose：表达哪些历史分类、ledger treatment、accountant note 或 accountant-prepared books 可支持 accountant-derived historical case foundation。

Source authority：accountant-prepared historical books、accountant instruction、firm-approved historical ledgers、accountant correction notes。

Required fields：

| Field | Meaning | Source authority | Runtime / Durable |
| --- | --- | --- | --- |
| `basis_ref` | accountant-processed basis 引用 | historical ledger / accountant note | durable evidence/source reference |
| `related_historical_transaction_refs` | 该 basis 涉及的历史交易 | onboarding workflow | durable refs where available |
| `accounting_treatment_summary` | 历史处理结果摘要 | accountant-prepared books / accountant instruction | runtime summary with durable source |
| `authority_category` | authority 类型 | accountant / workflow | runtime authority input |
| `evidence_refs` | 支撑该处理结果的 source refs | Evidence Log / material package | durable references |
| `traceability_status` | 是否可追溯 | evidence / accountant source | runtime validation |

Allowed `authority_category` values：

- `accountant_prepared_books`
- `explicit_accountant_instruction`
- `accountant_correction`
- `firm_migration_approved`
- `uncertain_accountant_source`

Optional fields：

| Field | Meaning | Source authority | Runtime / Durable |
| --- | --- | --- | --- |
| `coa_account_ref` | 历史 COA 科目或等价账本科目引用 | accountant-prepared books | durable ref / runtime mapping context |
| `tax_treatment_context` | GST/HST 或 tax treatment 历史语境 | accountant-prepared books / instruction | runtime summary with source refs |
| `business_context_note` | accountant 对用途、例外、客户背景的说明 | accountant | durable evidence/source ref |
| `exception_context` | 该历史处理为何是例外或特殊处理 | accountant / ledger | runtime summary |
| `confidence_note` | 迁移或解析过程对 source 的信心说明 | workflow / migration | runtime |

Validation / rejection rules：

- `authority_category = uncertain_accountant_source` 不能支持 confirmed historical case write；只能进入 candidate / review package。
- `accounting_treatment_summary` 不能只有 LLM 总结，必须绑定 ledger / accountant source refs。
- `coa_account_ref` 或 tax treatment context 如来自旧 COA / historical books，只是 historical case context，不自动创建 active rule 或 current COA mapping authority。
- 如果 accountant-processed result 与 raw evidence 冲突，必须保留 conflict issue；不得隐藏在 summary 中。

Runtime-only vs durable references：

- basis envelope 是 runtime-only。
- `basis_ref`、source docs、ledger refs、accountant note refs 可以作为 durable evidence / case references。

### 3.5 `customer_structural_basis`

Purpose：表达历史材料中暗示或支持的客户结构事实，例如 bank accounts、internal transfers、loans、employees、tax config 或 owner personal use pattern。

Source authority：historical materials、accountant notes、client-provided context、existing Profile、migration context。

Required fields：

| Field | Meaning | Source authority | Runtime / Durable |
| --- | --- | --- | --- |
| `structural_basis_ref` | 结构事实 basis 引用 | onboarding workflow | runtime / durable ref |
| `structural_fact_type` | 结构事实类型 | material / accountant / profile context | runtime |
| `proposed_fact_summary` | 候选事实摘要 | onboarding extraction / accountant source | runtime summary |
| `source_authority_category` | authority 分类 | source context | runtime authority input |
| `evidence_refs` | 支撑该结构事实的 evidence refs | Evidence Log / materials | durable references |
| `confirmation_status` | 是否已具备 stable Profile authority | accountant / Profile / governance context | runtime authority state |

Allowed `structural_fact_type` values：

- `bank_account`
- `internal_transfer_relationship`
- `loan`
- `employee_presence`
- `payroll_context`
- `tax_config`
- `owner_uses_company_account`
- `related_party_context`
- `other_profile_fact`

Allowed `confirmation_status` values：

- `already_confirmed_profile_truth`
- `accountant_confirmed_in_onboarding_source`
- `candidate_requires_confirmation`
- `conflicting_requires_review`
- `insufficient_evidence`

Optional fields：

| Field | Meaning | Source authority | Runtime / Durable |
| --- | --- | --- | --- |
| `existing_profile_ref` | 已有 Profile fact 引用 | Profile | durable reference |
| `affected_account_refs` | 涉及的银行账户、loan account 或 payroll account | Profile / evidence | durable refs |
| `effective_period` | 结构事实适用期间 | accountant / historical evidence | runtime / durable metadata |
| `risk_flags` | 混用、关联方、payroll、tax risk 等 | evidence / accountant / governance context | runtime |
| `review_question_hint` | 给 Review / accountant 的澄清提示 | onboarding workflow | runtime-only |

Validation / rejection rules：

- `confirmation_status = candidate_requires_confirmation`、`conflicting_requires_review` 或 `insufficient_evidence` 时，不得写成 stable Profile truth。
- client statement 可以支持 candidate 或 review question，但不能单独支持高 authority profile mutation，除非 accountant 后续确认。
- profile candidate 不得支持 current structural match，直到被确认为 stable Profile truth。
- `tax_config`、loan、employee、owner personal use 等高影响事实必须保留 source / authority 和 risk context。

Runtime-only vs durable references：

- structural basis envelope 是 runtime-only。
- confirmed Profile refs 和 evidence refs 是 durable references。
- candidate profile fact 不是 durable Profile truth；它可以作为 review / governance candidate 被持久追踪，但不能被 Profile / Structural Match 当作已确认事实。

### 3.6 `entity_onboarding_basis`

Purpose：表达历史材料中出现的 counterparty / vendor / payee、aliases、surface texts 和 role/context hints，供 initial entity foundation 或 entity candidates 使用。

Source authority：bank statement raw text、historical ledger names、receipts、cheques、contracts、invoices、accountant context、existing Entity Log。

Required fields：

| Field | Meaning | Source authority | Runtime / Durable |
| --- | --- | --- | --- |
| `entity_basis_ref` | entity basis 引用 | onboarding workflow | runtime / durable ref |
| `surface_signals` | 表面身份信号列表 | historical evidence | runtime list with durable refs |
| `candidate_display_name` | 候选展示名称 | onboarding extraction / accountant source | runtime proposal |
| `source_authority_category` | authority 分类 | material source context | runtime authority input |
| `evidence_refs` | 支撑该 entity basis 的 evidence refs | Evidence Log / material package | durable references |
| `entity_initialization_status` | 本 basis 的初始化状态 | onboarding authority evaluation | runtime state |

Each `surface_signal` required fields：

| Field | Meaning | Source authority |
| --- | --- | --- |
| `signal_type` | identity signal 类型 | evidence source |
| `surface_text` | 原始或近原始文本 | evidence source |
| `evidence_ref` | 支撑该 signal 的 evidence ref | Evidence Log |
| `source_priority` | 信号相对强度 | evidence / accountant context |

Allowed `signal_type` values：

- `raw_bank_text`
- `historical_ledger_name`
- `receipt_vendor`
- `cheque_payee`
- `invoice_party`
- `contract_party`
- `accountant_context`
- `existing_alias`
- `other_historical_identity_signal`

Allowed `source_priority` values：

- `primary`
- `supporting`
- `weak`
- `conflicting`

Allowed `entity_initialization_status` values：

- `stable_initial_entity_supported`
- `entity_candidate_only`
- `ambiguous_entity_group`
- `merge_split_candidate_only`
- `insufficient_identity_evidence`
- `conflicting_identity_evidence`

Optional fields：

| Field | Meaning | Source authority | Runtime / Durable |
| --- | --- | --- | --- |
| `existing_entity_refs` | 可能匹配的既有 entities | Entity Log / migration context | durable refs |
| `proposed_aliases` | 候选 aliases / 表面写法 | evidence / onboarding extraction | candidate-only |
| `proposed_role_context` | 当前客户关系下的 role/context 候选 | accountant source / historical evidence / LLM extraction | candidate or accountant-derived |
| `role_authority_category` | role authority 来源 | source context | runtime authority input |
| `risk_flags` | mixed-use、name ambiguity、related-party 等风险 | evidence / accountant / governance context | runtime / candidate context |
| `automation_policy_candidate` | 建议的 automation policy change 或 restriction | onboarding candidate | candidate-only |
| `entity_reason` | 为什么选择该 entity status | onboarding extraction / evaluation | runtime explanation |

Validation / rejection rules：

- `surface_signals` 不能为空；没有 identity signal 时不能生成 entity foundation。
- `stable_initial_entity_supported` 必须有足够 traceable evidence，且不得依赖不可追溯 summary。
- `proposed_aliases` 默认是 candidate alias；不得支持 rule match，除非后续 governance / accountant approval 使其成为 approved alias。
- `proposed_role_context` 默认是 candidate role；只有 `role_authority_category = accountant_derived_from_processed_books` 或等价 explicit accountant authority，并保留 source metadata，才可作为受控例外进入 stable entity role context。
- entity basis 不得保存 COA、HST、JE、classification conclusion 或 deterministic rule authority。
- merge / split 只能输出 candidate；不得由 Onboarding 执行。

Allowed `role_authority_category` values：

- `accountant_derived_from_processed_books`
- `explicit_accountant_instruction`
- `system_inferred_candidate`
- `client_statement_candidate`
- `unknown_role_authority`

Runtime-only vs durable references：

- entity basis envelope 和 explanation 是 runtime-only。
- stable entity foundation 如被写入 `Entity Log`，必须只持有 identity / alias / role authority metadata 和 evidence links。
- candidate aliases、candidate roles、merge/split candidates 可以进入 governance review package，但不等于 durable approval。

### 3.7 `case_precedent_basis`

Purpose：表达哪些历史交易可作为 `Case Log` 的 accountant-derived historical case foundation。

Source authority：accountant-processed historical records、accountant-prepared books、accountant instruction、accountant correction notes。

Required fields：

| Field | Meaning | Source authority | Runtime / Durable |
| --- | --- | --- | --- |
| `case_basis_ref` | case basis 引用 | onboarding workflow | runtime / durable ref |
| `historical_transaction_ref` | 对应历史交易 | historical transaction basis | durable ref if accepted |
| `case_authority_category` | 支持 case 的 authority 类型 | accountant source context | runtime authority input |
| `final_historical_treatment` | 历史处理结果摘要 | accountant-processed basis | runtime summary with durable refs |
| `evidence_refs` | 支撑该 case 的 evidence refs | Evidence Log / material package | durable references |
| `entity_context_ref` | 相关 entity basis / entity ref | Entity Log / entity basis | durable or candidate ref |
| `case_write_eligibility` | 是否允许写入 confirmed historical case foundation | authority evaluation | runtime state |

Allowed `case_authority_category` values：

- `accountant_prepared_books`
- `explicit_accountant_instruction`
- `accountant_correction`
- `firm_migration_approved`
- `insufficient_accounting_authority`

Allowed `case_write_eligibility` values：

- `eligible_for_accountant_derived_case`
- `candidate_case_requires_review`
- `blocked_by_missing_authority`
- `blocked_by_traceability_gap`
- `blocked_by_conflict`

Optional fields：

| Field | Meaning | Source authority | Runtime / Durable |
| --- | --- | --- | --- |
| `coa_account_ref` | 历史分类科目或 ledger account ref | accountant-prepared books | durable ref / runtime context |
| `tax_treatment_context` | GST/HST 或 tax context | accountant source | runtime summary with refs |
| `exception_conditions` | 该 case 的例外条件 | accountant source / evidence | runtime summary |
| `receipt_or_supporting_evidence_context` | receipt、cheque、contract 等支持材料 | evidence package | durable refs + runtime summary |
| `accountant_note_refs` | accountant 说明或修正 refs | accountant source | durable refs |
| `case_conflict_flags` | case 与 evidence、entity、profile 或其他 cases 的冲突 | onboarding evaluation | runtime |

Validation / rejection rules：

- `case_write_eligibility = eligible_for_accountant_derived_case` 必须绑定 accountant authority 和 traceable evidence。
- 缺少 accountant authority 的 historical transaction 不能写入 confirmed Case Log；只能作为 candidate case 或 evidence context。
- entity unresolved 不必自动阻止 case candidate，但会限制 confirmed case memory 的 entity binding；不得伪装成 resolved entity case。
- historical case 是 precedent，不是 deterministic rule；不能支持 Rule Match。
- Transaction Log 不参与 case write authority。

Runtime-only vs durable references：

- case precedent basis envelope 是 runtime-only。
- accepted `case_log_record` 可以成为 durable `Case Log` memory。
- candidate case 或 conflict package 只是 review / governance input，不是 confirmed case memory。

### 3.8 `rule_stability_basis`

Purpose：表达少量稳定对象是否值得进入 initial rule candidate / governance approval path。

Source authority：accountant-derived historical cases、stable entity foundation、existing Rule Log / Governance Log context、accountant instruction。

Required fields：

| Field | Meaning | Source authority | Runtime / Durable |
| --- | --- | --- | --- |
| `rule_basis_ref` | rule stability basis 引用 | onboarding workflow | runtime ref |
| `entity_ref` | 相关 entity 或 entity candidate | Entity Log / entity basis | durable or candidate ref |
| `supporting_case_refs` | 支持 rule candidate 的 historical case refs | Case Log / case basis | durable refs if confirmed |
| `proposed_rule_summary` | 候选 rule 的业务含义摘要 | onboarding evaluation | runtime proposal |
| `rule_candidate_status` | rule candidate 状态 | onboarding authority evaluation | runtime state |
| `evidence_refs` | 支撑 rule candidate 的 evidence refs | Evidence Log / Case Log | durable references |

Allowed `rule_candidate_status` values：

- `initial_rule_candidate`
- `rule_candidate_requires_accountant_review`
- `blocked_by_entity_authority`
- `blocked_by_alias_or_role_authority`
- `blocked_by_case_instability`
- `blocked_by_conflict_or_exception`
- `not_rule_candidate`

Optional fields：

| Field | Meaning | Source authority | Runtime / Durable |
| --- | --- | --- | --- |
| `existing_rule_refs` | 相关既有 rules | Rule Log | durable refs |
| `proposed_conditions` | direction、amount range、role/context、exception boundary 等候选条件 | onboarding evaluation / accountant source | candidate-only |
| `automation_policy_candidate` | 是否建议限制或改变 automation policy | onboarding evaluation | candidate-only |
| `conflict_summary` | 为什么不适合 rule 或需要 review | onboarding evaluation | runtime |
| `governance_candidate_reason` | 进入 Governance Review 的理由 | onboarding evaluation | runtime |

Validation / rejection rules：

- 本 input 只能支持 rule candidate；不能产生 active Rule Log authority。
- `supporting_case_refs` 如不是 confirmed accountant-derived cases，只能支持 weak candidate 或 review question。
- `entity_ref` 若只是 candidate entity、alias 未 approved 或 role 未 confirmed，必须阻断 active rule path。
- automation policy upgrade / relaxation 只能作为 candidate，不能由 Onboarding 直接生效。
- rule candidate 必须保留 exception / conflict boundary；不得把 mixed-use 或近期修正隐藏为稳定 rule。

Runtime-only vs durable references：

- rule stability basis 是 runtime-only candidate evaluation。
- rule candidate 可进入 governance package；active rule 只能由 accountant / governance approval 后产生。

### 3.9 `onboarding_authority_context`

Purpose：统一表达本次 Onboarding 能做什么、不能做什么，以及哪些 output 必须被降级为 candidate / review-needed。

Source authority：active docs、accountant instruction、Governance Log、Profile / Entity / Rule / Case authority metadata、workflow policy。

Required fields：

| Field | Meaning | Source authority | Runtime / Durable |
| --- | --- | --- | --- |
| `authority_context_ref` | authority context 引用 | workflow / governance context | runtime / durable refs |
| `client_id` | 客户标识 | onboarding request | durable reference |
| `allowed_direct_write_categories` | 本次允许的 direct durable foundation categories | active docs / governance / accountant context | runtime policy view |
| `candidate_only_categories` | 只能作为 candidate 输出的 categories | active docs / governance / accountant context | runtime policy view |
| `blocked_categories` | 本次明确禁止输出或写入的 categories | active docs / governance / accountant context | runtime policy view |

Allowed `allowed_direct_write_categories` values：

- `evidence_foundation`
- `historical_transaction_identity_seed`
- `accountant_derived_historical_case`
- `sufficiently_supported_initial_entity`
- `knowledge_summary_seed`

Allowed `candidate_only_categories` values：

- `profile_fact_candidate`
- `alias_candidate`
- `role_confirmation_candidate`
- `entity_merge_split_candidate`
- `rule_candidate`
- `automation_policy_candidate`
- `conflict_review_candidate`
- `case_requires_review_candidate`

Allowed `blocked_categories` values：

- `current_transaction_log_write`
- `journal_entry_generation`
- `active_rule_creation_without_approval`
- `approved_alias_without_approval`
- `stable_role_without_authority`
- `entity_merge_split_without_governance`
- `automation_policy_relaxation_without_approval`
- `unconfirmed_profile_truth_write`
- `classification_conclusion_from_raw_evidence_only`

Optional fields：

- `governance_restriction_refs`：已生效或 pending governance restriction。
- `accountant_instruction_refs`：明确 accountant instruction refs。
- `authority_notes`：用于 explainability 的人类可读 authority 说明。

Validation / rejection rules：

- `allowed_direct_write_categories` 不得包含 active rule、current Transaction Log、JE、automation relaxation、merge/split approval 或 unconfirmed Profile truth。
- 若 `authority_context_ref` 缺失或与 input source authority 冲突，必须按更保守的 candidate-only / blocked path 输出。
- candidate-only category 不得被下游解释为 approval。

Runtime-only vs durable references：

- authority context envelope 是 runtime-only。
- governance / accountant instruction refs 是 durable references。

## 4. Output Contracts

### 4.1 `onboarding_initialization_result`

Purpose：Onboarding Node 的主 output envelope，汇总本次初始化完成状态、durable foundation writes、candidate packages、blocked issues 和 downstream handoff refs。

Consumer / downstream authority：workflow orchestrator、Evidence Intake / Preprocessing、Transaction Identity、Profile / Structural Match、Entity Resolution、Case Judgment、Review、Governance Review、Knowledge Compilation。该 result 本身不创造 accountant approval。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `onboarding_result_id` | 本次 onboarding result 标识 | workflow runtime | runtime, may be referenced |
| `onboarding_request_id` | 对应 request | input request | runtime reference |
| `client_id` | 客户标识 | input request | durable reference |
| `result_status` | 初始化结果状态 | Onboarding Node within contract limits | runtime state |
| `durable_foundation_refs` | 本次建立的 durable foundation refs | allowed direct write categories | durable refs |
| `candidate_package_refs` | 本次产生的 candidate package refs | candidate-only outputs | runtime / durable refs if persisted for review |
| `blocked_or_invalid_items` | 无法处理或被 authority 阻断的 items | validation / authority evaluation | runtime issue list |
| `downstream_handoff_summary` | 给后续 workflow 的可读摘要 | Onboarding Node | runtime summary |
| `authority_boundary_summary` | 本次 direct write / candidate-only / blocked 边界摘要 | authority context | runtime summary |

Allowed `result_status` values：

- `completed_with_foundation`
- `completed_with_candidates_only`
- `partial_foundation_with_review_needed`
- `blocked_invalid_input`
- `blocked_by_authority_gap`
- `blocked_by_traceability_gap`
- `blocked_by_conflict`

Optional fields：

- `evidence_foundation_refs`
- `historical_transaction_identity_refs`
- `initial_entity_refs`
- `historical_case_refs`
- `knowledge_summary_refs`
- `profile_candidate_refs`
- `governance_review_request_refs`
- `quality_warnings`
- `open_issue_summary`
- `created_at`

Validation rules：

- `result_status = completed_with_foundation` 必须至少包含一个 allowed direct durable foundation ref。
- candidate-only run 不得伪装为 foundation write；`completed_with_candidates_only` 必须明确没有 stable durable authority change。
- `blocked_invalid_input`、`blocked_by_authority_gap`、`blocked_by_traceability_gap`、`blocked_by_conflict` 必须列出 `blocked_or_invalid_items`。
- `durable_foundation_refs` 不得包含 active rule、current Transaction Log、JE、automation upgrade、merge/split approval 或 unconfirmed Profile truth。

Durable / candidate / runtime：

- result envelope 是 runtime-only。
- listed durable refs 指向各自 memory store 中已允许的 foundation records。
- candidate package refs 指向 review / governance candidate tracking，不等于 approval。

### 4.2 `initial_evidence_record`

Purpose：把历史原始材料保存为可追溯 evidence foundation。

Consumer / downstream authority：Evidence Log、Evidence Intake / Preprocessing、Entity Resolution、Case Judgment、Review / Governance context。它只提供 evidence source，不提供业务结论。

Required fields：

| Field | Meaning | Authority | Durable Boundary |
| --- | --- | --- | --- |
| `evidence_id` | evidence record 标识 | Evidence Log / onboarding foundation | durable |
| `client_id` | 客户标识 | onboarding request | durable reference |
| `source_material_ref` | 原始材料引用 | material package | durable reference |
| `evidence_type` | evidence 类型 | material package / intake classification | durable metadata |
| `source_authority_category` | source authority 分类 | source context | durable metadata |
| `traceability_status` | 追溯状态 | evidence intake / onboarding validation | durable metadata |
| `content_ref_or_excerpt` | 原始内容引用或受控摘录 | source material | durable evidence ref / bounded excerpt |
| `created_from` | 创建来源，应为 `onboarding_node` | workflow | durable metadata |

Allowed `evidence_type` values：

- `bank_statement_line`
- `historical_ledger_entry`
- `receipt_record`
- `cheque_record`
- `invoice_record`
- `contract_record`
- `accountant_note`
- `client_note`
- `migration_record`
- `other_evidence`

Optional fields：

- `covered_period`
- `linked_evidence_ids`
- `parse_quality_flags`
- `account_refs`
- `hash_or_fingerprint`
- `language_or_format_note`

Validation rules：

- evidence record 不得保存 COA conclusion、HST conclusion、rule result 或 JE。
- `content_ref_or_excerpt` 必须可追溯；不能只有 LLM paraphrase。
- `source_authority_category` 必须保留，不得把 accountant source 和 raw evidence source 抹平。

Durable / candidate / runtime：

- 这是 durable evidence foundation。
- 它不能单独成为 classification authority。

### 4.3 `historical_transaction_identity_seed`

Purpose：为历史材料中的交易建立稳定引用、去重 basis 或 future identity alignment context。

Consumer / downstream authority：Transaction Identity Node、Evidence Intake / Preprocessing、Case Log write validation。它不代表当前新交易 finalization。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `historical_transaction_seed_id` | 历史交易 seed 标识 | onboarding / identity workflow | durable ref if persisted |
| `client_id` | 客户标识 | onboarding request | durable reference |
| `objective_transaction_basis` | 日期、金额、direction、currency、bank account | historical transaction basis | durable refs + runtime values |
| `evidence_refs` | 支撑历史交易的 evidence refs | Evidence Log | durable references |
| `dedupe_basis` | 去重依据 | deterministic identity discipline | runtime / durable metadata |
| `identity_status` | identity seed 状态 | onboarding / identity evaluation | runtime state |

Allowed `identity_status` values：

- `stable_historical_identity_seed`
- `possible_duplicate`
- `split_or_combined_transaction_candidate`
- `insufficient_identity_basis`
- `conflicting_identity_basis`

Optional fields：

- `linked_historical_transaction_refs`
- `source_file_refs`
- `bank_account_ref`
- `ledger_entry_refs`
- `quality_flags`

Validation rules：

- identity seed 不得包含会计分类结论。
- identity seed 不得写入 `Transaction Log`。
- duplicate / split / combined candidates 必须保持候选状态，不能强制合并历史 cases。

Durable / candidate / runtime：

- accepted identity seed 可以成为 durable identity / dedupe reference。
- ambiguous identity signals 是 candidate / issue context。

### 4.4 `profile_candidate_record`

Purpose：表达待 accountant / review / governance 确认的客户结构事实。

Consumer / downstream authority：Review Node、Governance Review Node、Profile / Structural Match Node after confirmation。未确认前不得作为 stable Profile truth。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `profile_candidate_id` | profile candidate 标识 | onboarding workflow | candidate tracking ref |
| `client_id` | 客户标识 | onboarding request | durable reference |
| `structural_fact_type` | 结构事实类型 | customer structural basis | candidate |
| `proposed_fact_summary` | 候选事实摘要 | evidence / accountant source / extraction | candidate |
| `source_authority_category` | 来源 authority | source context | candidate metadata |
| `evidence_refs` | 支撑候选事实的 evidence refs | Evidence Log / materials | durable refs |
| `confirmation_status` | 确认状态 | onboarding authority evaluation | candidate state |
| `review_need_reason` | 为什么需要确认或为何已支持 | onboarding validation | runtime / candidate explanation |

Allowed `confirmation_status` values：

- `candidate_requires_confirmation`
- `accountant_confirmed_in_source`
- `already_confirmed_profile_truth`
- `conflicting_requires_review`
- `insufficient_evidence`

Optional fields：

- `existing_profile_ref`
- `affected_account_refs`
- `effective_period`
- `risk_flags`
- `suggested_review_question`
- `governance_candidate_ref`

Validation rules：

- 只有 `already_confirmed_profile_truth` 或 `accountant_confirmed_in_source` 可被后续流程评估为 stable Profile write；其具体 confirmation workflow 未在本 Stage 冻结。
- `candidate_requires_confirmation`、`conflicting_requires_review`、`insufficient_evidence` 不得被 Profile / Structural Match Node 当作 confirmed structural fact。
- `suggested_review_question` 只是 runtime helper，不是 evidence 或 authority。

Durable / candidate / runtime：

- profile candidate 可被持久追踪为 candidate package。
- 它不是 stable Profile truth，除非后续 accountant / governance authority 完成确认。

### 4.5 `initial_entity_record_or_candidate`

Purpose：建立初始 entity foundation，或保留 entity / alias / role / merge-split candidate。

Consumer / downstream authority：Entity Log、Entity Resolution Node、Governance Review Node、Review Node、Case Judgment Node。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `entity_output_id` | 本次 entity output 标识 | onboarding workflow | runtime / candidate ref |
| `client_id` | 客户标识 | onboarding request | durable reference |
| `entity_initialization_status` | entity 初始化状态 | onboarding authority evaluation | runtime state |
| `display_name` | 展示名称 | evidence / accountant source / onboarding extraction | durable if stable, candidate otherwise |
| `entity_type` | entity 类型 | evidence / accountant source / onboarding extraction | durable if stable, candidate otherwise |
| `surface_signals` | 支撑 identity 的表面信号 | Evidence Log / materials | durable refs + runtime list |
| `evidence_refs` | 支撑 entity output 的 evidence refs | Evidence Log | durable references |
| `authority` | source / authority metadata | source context / accountant source | durable metadata if stable |
| `created_from` | 创建来源，应为 `onboarding_node` | workflow | durable metadata if stable |

Allowed `entity_initialization_status` values：

- `stable_initial_entity_supported`
- `entity_candidate_only`
- `ambiguous_entity_group`
- `merge_split_candidate_only`
- `insufficient_identity_evidence`
- `conflicting_identity_evidence`

Allowed `entity_type` values：

- `vendor`
- `payee`
- `customer`
- `financial_institution`
- `government_agency`
- `employee_or_contractor`
- `related_party`
- `unknown_or_other`

Optional fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `entity_id` | stable entity id；仅 stable write 时存在 | Entity Log / onboarding foundation | durable |
| `existing_entity_refs` | 可能匹配或冲突的既有 entities | Entity Log | durable refs |
| `aliases` | aliases with status | evidence / governance authority | durable/candidate depending status |
| `roles` | confirmed 或 accountant-derived roles | accountant authority | durable only when authority supports |
| `candidate_role` | 系统推断或 client statement role | onboarding extraction | candidate-only |
| `status` | stable entity lifecycle status | Entity Log | durable when stable |
| `risk_flags` | identity / mixed-use / role risk | evidence / accountant / governance context | runtime or durable metadata |
| `automation_policy_candidate` | automation policy 候选 | onboarding evaluation | candidate-only |
| `governance_candidate_refs` | alias / role / merge / split / policy candidates | onboarding / governance workflow | candidate refs |
| `entity_reason` | entity output 理由 | onboarding evaluation | runtime explanation |

Allowed stable `status` values：

- `candidate`
- `active`
- `merged`
- `archived`

Allowed alias statuses in this output：

- `candidate_alias`
- `approved_alias`
- `rejected_alias`

Validation rules：

- `stable_initial_entity_supported` 不等于可以自动分类；automation 仍由 rule / case / policy authority 控制。
- `candidate_alias` 不得支持 rule match。
- `candidate_role` 不得写成 stable role。
- `approved_alias` 或 `rejected_alias` 必须来自 existing governance / accountant authority，不得由 Onboarding 直接发明。
- `roles` 只有在 accountant-confirmed、existing Entity Log 或受控 `accountant_derived_from_processed_books` source metadata 支持时，才能成为 durable role。
- entity record 不得包含 COA、HST、JE 或 final classification conclusion。
- merge / split candidate 不得执行 mutation。

Durable / candidate / runtime：

- stable entity foundation 可写入 `Entity Log`，但只在 entity memory 职责内有效。
- candidate alias、candidate role、merge/split、automation policy candidate 只能进入 review / governance path。

### 4.6 `historical_case_record_or_candidate`

Purpose：把 accountant-processed historical transaction 转化为 historical case foundation，或在 authority 不足时保留 case candidate / issue。

Consumer / downstream authority：Case Log、Case Judgment Node、Review Node、Governance Review Node、Knowledge Compilation Node。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `case_output_id` | case output 标识 | onboarding workflow | runtime / candidate ref |
| `client_id` | 客户标识 | onboarding request | durable reference |
| `case_write_status` | case 输出状态 | onboarding authority evaluation | runtime state |
| `historical_transaction_ref` | 对应历史交易 | historical transaction basis | durable ref if accepted |
| `final_historical_treatment` | accountant-derived 历史处理结果 | accountant-processed basis | durable case context if accepted |
| `case_authority_category` | case authority 来源 | accountant source context | durable metadata if accepted |
| `evidence_refs` | 支撑 case 的 evidence refs | Evidence Log / materials | durable references |
| `entity_context_ref` | 相关 entity 或 candidate context | Entity Log / entity output | durable/candidate ref |
| `created_from` | 创建来源，应为 `onboarding_node` | workflow | durable metadata if accepted |

Allowed `case_write_status` values：

- `written_accountant_derived_case`
- `candidate_case_requires_review`
- `blocked_by_missing_accountant_authority`
- `blocked_by_traceability_gap`
- `blocked_by_identity_or_entity_conflict`
- `blocked_by_accounting_conflict`

Optional fields：

- `case_id`
- `coa_account_ref`
- `tax_treatment_context`
- `exception_conditions`
- `receipt_or_supporting_evidence_refs`
- `accountant_note_refs`
- `review_candidate_ref`
- `case_reason`

Validation rules：

- `written_accountant_derived_case` 必须有 accountant authority 和 traceable evidence。
- raw bank evidence、receipt、cheque 或 LLM inference 不能单独支持 confirmed historical case。
- historical case 不等于 deterministic rule。
- unresolved entity 可允许 candidate case，但 confirmed case 的 entity binding 必须如实标注 unresolved / candidate / stable context。
- case record 不得写入 `Transaction Log`，不得生成 JE。

Durable / candidate / runtime：

- `written_accountant_derived_case` 是 durable `Case Log` foundation。
- candidate / blocked statuses 是 review or issue context，不是 confirmed case memory。

### 4.7 `customer_knowledge_summary_seed`

Purpose：从 initialized evidence、entity、case、risk 和 conflict context 中生成客户知识摘要种子，供 humans 和 agents 后续理解客户语境。

Consumer / downstream authority：Knowledge Log / Summary Log、Knowledge Compilation Node、Case Judgment Node as context only、Review Node。它不是 deterministic rule source。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `summary_seed_id` | summary seed 标识 | onboarding / knowledge workflow | durable if persisted |
| `client_id` | 客户标识 | onboarding request | durable reference |
| `summary_scope` | 摘要覆盖范围 | onboarding workflow | durable metadata |
| `source_refs` | 摘要来源 refs | Entity / Case / Evidence / Governance refs | durable references |
| `summary_text` | 人和 agent 可读摘要 | Onboarding synthesis | durable summary if persisted |
| `authority_disclaimer` | 摘要 authority 边界说明 | active docs / onboarding authority | durable metadata |
| `created_from` | 创建来源，应为 `onboarding_node` | workflow | durable metadata |

Allowed `summary_scope` values：

- `client_initial_knowledge`
- `entity_patterns_overview`
- `case_precedent_overview`
- `risk_and_exception_overview`
- `conflict_and_review_needed_overview`

Optional fields：

- `related_entity_refs`
- `related_case_refs`
- `related_profile_candidate_refs`
- `related_governance_candidate_refs`
- `summary_quality_flags`
- `expires_or_refresh_reason`

Validation rules：

- `summary_text` 必须绑定 source refs；不能是不可追溯的自由发挥。
- summary 不能包含“已批准 rule”“已确认 Profile fact”“已合并 entity”等超出 source authority 的结论。
- summary 不能替代 Evidence Log、Case Log、Rule Log 或 accountant approval。

Durable / candidate / runtime：

- 可以作为 durable Knowledge / Summary seed。
- 只能作为 context，不得参与 deterministic rule match。

### 4.8 `rule_and_governance_candidate_package`

Purpose：把 Onboarding 发现的 rule、alias、role、merge/split、automation policy、profile confirmation 或 conflict review candidates 交给 Review / Governance Review。

Consumer / downstream authority：Governance Review Node、Review Node、Post-Batch Lint / Knowledge Compilation as context。该 package 不批准任何长期 authority change。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `candidate_package_id` | candidate package 标识 | onboarding workflow | candidate tracking ref |
| `client_id` | 客户标识 | onboarding request | durable reference |
| `candidate_items` | 候选事项列表 | onboarding evaluation | candidate-only |
| `evidence_refs` | package-level evidence refs | Evidence Log / source material | durable references |
| `trigger_source` | 固定为 `onboarding_node` | workflow | runtime/candidate metadata |
| `authority_limit_context` | package 最多允许的 approval path | onboarding authority context | runtime policy view |
| `package_status` | package 状态 | onboarding workflow | runtime/candidate state |

Allowed `package_status` values：

- `ready_for_review`
- `needs_evidence_refinement`
- `blocked_by_authority_gap`
- `blocked_by_conflict`
- `deferred_open_boundary`

Each `candidate_item` required fields：

| Field | Meaning | Authority |
| --- | --- | --- |
| `candidate_item_id` | 候选 item 标识 | onboarding workflow |
| `candidate_type` | 候选类型 | onboarding evaluation |
| `candidate_summary` | 候选事项摘要 | onboarding evaluation |
| `source_refs` | 支撑候选的 refs | Evidence / Entity / Case / Profile context |
| `requires_accountant_approval` | 是否需要 accountant approval | active docs / governance boundary |
| `approval_status` | 当前批准状态 | governance/review workflow |

Allowed `candidate_type` values：

- `profile_fact_confirmation`
- `alias_approval`
- `alias_rejection`
- `role_confirmation`
- `entity_merge_candidate`
- `entity_split_candidate`
- `rule_candidate`
- `automation_policy_candidate`
- `case_review_candidate`
- `conflict_review_candidate`
- `traceability_issue`

Allowed `approval_status` values：

- `not_submitted`
- `pending_review`
- `approved`
- `rejected`
- `deferred`
- `blocked`

Optional fields：

- `related_entity_refs`
- `related_case_refs`
- `related_profile_refs`
- `related_rule_refs`
- `proposed_old_value`
- `proposed_new_value`
- `risk_flags`
- `review_question_hint`
- `candidate_reason`

Validation rules：

- Onboarding-created candidate item cannot start as `approved` unless it references an existing prior approval; otherwise `approval_status` must be `not_submitted` or `pending_review`.
- `rule_candidate` cannot be consumed by Rule Match Node until governance / accountant approval creates active Rule Log authority.
- `automation_policy_candidate` cannot relax automation policy without approval; restrictive suggestions also need proper governance visibility if persisted.
- merge/split candidate cannot mutate Entity Log.
- candidate package is not a durable Log unless and until represented as a proper Governance Log event or approved memory mutation record.

Durable / candidate / runtime：

- package is candidate-only.
- It may create Governance Review request refs, but approval belongs downstream.

### 4.9 `onboarding_blocked_issue`

Purpose：记录无法安全形成 foundation 或 candidate 的 invalid / blocked condition。

Consumer / downstream authority：workflow orchestrator、Review Node、Governance Review Node、human operator。它是 safety output，不是 memory authority。

Required fields：

| Field | Meaning | Authority | Runtime / Durable |
| --- | --- | --- | --- |
| `issue_id` | issue 标识 | onboarding workflow | runtime / issue tracking ref |
| `client_id` | 客户标识 | onboarding request | durable reference |
| `issue_type` | issue 类型 | validation / authority evaluation | runtime state |
| `affected_refs` | 受影响材料、交易、entity、case 或 candidate refs | onboarding workflow | durable refs where applicable |
| `reason` | 阻断原因 | onboarding validation | runtime explanation |
| `required_resolution_path` | 需要什么后续处理 | active docs / onboarding boundary | runtime |

Allowed `issue_type` values：

- `invalid_onboarding_scope`
- `missing_required_material`
- `missing_traceable_source`
- `missing_accountant_authority`
- `objective_transaction_basis_invalid`
- `identity_conflict`
- `entity_ambiguity`
- `accounting_treatment_conflict`
- `profile_authority_gap`
- `rule_authority_gap`
- `governance_boundary_block`

Allowed `required_resolution_path` values：

- `request_correct_material`
- `request_accountant_confirmation`
- `send_to_review_node`
- `send_to_governance_review_node`
- `defer_until_open_boundary_resolved`
- `exclude_from_durable_memory`

Optional fields：

- `suggested_question`
- `conflicting_refs`
- `severity`
- `created_at`

Validation rules：

- blocked issue must not be hidden only inside knowledge summary.
- `exclude_from_durable_memory` must not delete evidence; it only means no durable business memory write.
- issue reason must distinguish traceability gap, accountant authority gap, identity ambiguity, entity ambiguity, and accounting conflict when known.

Durable / candidate / runtime：

- issue is runtime / review handoff.
- It can be persisted as review/governance context if downstream workflow chooses, but is not itself `Log` authority.

## 5. Field Authority and Memory Boundary

### 5.1 Source of truth for important fields

| Field / Concept | Source of truth | Onboarding authority |
| --- | --- | --- |
| `client_id` | client / onboarding workflow | reference only |
| source material content | original material / Evidence Log | preserve and reference |
| objective transaction fields | bank / ledger / evidence source, normalized by deterministic intake | normalize within evidence bounds |
| `direction` | explicit evidence-derived direction | must be explicit; no sign-based ambiguity |
| accountant historical classification | accountant-prepared books / instruction / correction | may support accountant-derived case |
| Profile truth | Profile + accountant / governance confirmation | candidate unless authority already supports truth |
| entity identity | Entity Log / traceable evidence / accountant source | may create sufficiently supported initial entity |
| alias approval / rejection | Governance / accountant approval | candidate only unless pre-approved source exists |
| stable role | accountant-confirmed role or controlled accountant-derived role | no system-inferred stable role |
| historical case memory | accountant-derived historical treatment with evidence refs | may write only when eligible |
| active rule | Rule Log after accountant / governance approval | candidate only |
| automation policy relaxation | accountant / governance approval | candidate only |
| automation policy downgrade | governed policy / lint / governance rules | Onboarding may propose; direct downgrade authority not settled here |
| customer knowledge summary | source-bound synthesis over evidence/entity/case/governance refs | context only |
| Transaction Log | Transaction Logging Node final audit write | no write, no runtime learning |

### 5.2 Fields that can never become durable memory by this node

以下字段或信息不得由 Onboarding 直接变成 durable authority：

- LLM-only inference without source refs
- raw evidence interpreted as accounting conclusion
- candidate profile fact as stable Profile truth
- candidate alias as approved alias
- candidate role as stable role
- rule candidate as active Rule Log record
- automation policy upgrade / relaxation
- entity merge / split execution
- current transaction final outcome
- journal entry
- current transaction `Transaction Log` entry
- review-facing report output
- prompt trace、temporary candidate queue、debug trace

### 5.3 Fields that can become durable only after accountant / governance approval

以下字段可以由 Onboarding 提出 candidate，但必须经 accountant / governance authority：

- profile facts requiring confirmation
- alias approval / rejection
- role confirmation，除 active docs 允许的 accountant-derived role 受控例外外
- entity merge / split
- rule promotion / initial rule creation
- rule modification / deletion / downgrade
- automation policy upgrade or relaxation
- profile tax config、loan、payroll、owner-use 等高影响结构事实
- unresolved conflict resolution

### 5.4 Audit vs learning / logging boundary

- `Evidence Log` 保存原始证据和证据引用，不保存业务结论。
- `Case Log` 可以保存 accountant-derived historical case，供 future case precedent 使用；它不是 deterministic rule。
- `Rule Log` 只保存 accountant / governance approved deterministic rules；Onboarding 只能提出 rule candidate。
- `Transaction Log` 只保存每笔交易最终处理结果和审计轨迹；它不参与 runtime decision，也不是 learning layer。Onboarding 不写新交易 `Transaction Log`。
- `Knowledge Log / Summary Log` 是可读摘要，不是 rule source。
- Candidate package、review queue、runtime handoff、trace、summary draft 不能被命名或处理成 durable `Log`，除非它们进入 active baseline 定义的 durable store。

## 6. Validation Rules

### 6.1 Contract-level validation rules

- 所有 durable outputs 必须绑定 `client_id`、source authority metadata 和 evidence/source refs。
- 所有 accounting treatment、case precedent、role、rule、profile fact、automation policy 相关字段必须携带 authority category。
- evidence、candidate、case、rule、governance、summary 语义必须分层，不能用一个 summary 字段混装。
- amount 必须是 absolute amount，direction 必须显式。
- `Transaction Log` 不能被用作 Onboarding learning layer。
- candidate-only output 必须明确 candidate type、approval status 和 downstream authority path。
- conflicting evidence 必须作为 issue / conflict candidate 暴露，不能被 summary 掩盖。
- `Knowledge Summary` 不能缺少 source refs，不能表达超出 source authority 的结论。

### 6.2 Conditions that make the input invalid

输入在以下情况下 invalid 或必须被阻断：

- `onboarding_initialization_request` 缺少 `client_id`、scope、material refs 或 authority context。
- scope 是普通 runtime transaction classification。
- material package 为空。
- material 无法追溯到原始 source 或 accountant source，却请求 durable memory write。
- historical transaction 缺少日期、金额、currency、bank account 或 explicit direction，且没有 accountant source 补足。
- source authority 无法区分 raw evidence、accountant-processed basis、accountant instruction、client statement 和 system inference。
- requested output 要求 Onboarding 直接写 active rule、Transaction Log、JE、automation relaxation、merge/split approval 或 unconfirmed Profile truth。

### 6.3 Conditions that make the output invalid

输出在以下情况下 invalid：

- durable foundation ref 指向 active rule、current Transaction Log、JE 或 review-facing report。
- profile candidate 被标记为 stable Profile truth 但没有 accountant / governance authority。
- candidate alias 被标记为 approved alias 但没有 prior approval reference。
- system-inferred role 被写入 stable role。
- historical case 缺少 accountant authority 或 traceable evidence。
- rule candidate 被输出为 active deterministic rule。
- automation policy candidate 被输出为已放宽或已升级。
- merge/split candidate 执行了 Entity Log mutation。
- knowledge summary 缺少 source refs 或替代了 evidence/case/rule authority。
- blocked conflict 只出现在 summary 中，没有结构化 issue record。

### 6.4 Stop / ask conditions for unresolved contract authority

后续 Stage 或 implementation task 遇到以下情况必须 stop / ask，不得自行补产品 authority：

- 需要决定 re-onboarding / incremental historical import 是否完整复用本节点 trigger boundary。
- 需要决定 profile candidate 到 stable Profile truth 的 exact approval workflow。
- 需要决定 initial rule candidate 到 active Rule Log 的 exact approval workflow。
- 需要决定初始化部分失败时主 workflow 是否可启动及启动限制。
- 需要为 stable entity、accountant-derived role、historical case write 设置 threshold number。
- 需要决定 Onboarding 是否可直接执行任何 automation policy downgrade。
- 需要把 candidate package 技术持久化为某种 queue / store / log。

## 7. Examples

### 7.1 Valid minimal example

```json
{
  "onboarding_initialization_request": {
    "onboarding_request_id": "onb_req_001",
    "client_id": "client_abc",
    "onboarding_scope": "new_client_initialization",
    "material_package_refs": ["mat_bank_2025_01", "mat_ledger_2025"],
    "source_authority_context": {
      "mat_bank_2025_01": "raw_evidence",
      "mat_ledger_2025": "accountant_processed_books"
    },
    "requested_outputs": [
      "evidence_foundation",
      "historical_case_foundation",
      "entity_foundation"
    ]
  },
  "onboarding_initialization_result": {
    "onboarding_result_id": "onb_res_001",
    "onboarding_request_id": "onb_req_001",
    "client_id": "client_abc",
    "result_status": "partial_foundation_with_review_needed",
    "durable_foundation_refs": {
      "evidence_foundation_refs": ["ev_001", "ev_002"],
      "historical_case_refs": ["case_hist_001"]
    },
    "candidate_package_refs": ["cand_pkg_001"],
    "blocked_or_invalid_items": [],
    "downstream_handoff_summary": "historical cases available; profile facts require confirmation",
    "authority_boundary_summary": "no active rules or profile truth approved by onboarding"
  }
}
```

Why valid：

- 材料有 source authority。
- historical case 来自 accountant-processed books。
- profile / governance items 保持 candidate。
- 没有写 `Transaction Log`、active rule 或 JE。

### 7.2 Valid richer example

```json
{
  "initial_entity_record_or_candidate": {
    "entity_output_id": "ent_out_014",
    "client_id": "client_abc",
    "entity_initialization_status": "stable_initial_entity_supported",
    "entity_id": "ent_tim_hortons",
    "display_name": "Tim Hortons",
    "entity_type": "vendor",
    "surface_signals": [
      {
        "signal_type": "historical_ledger_name",
        "surface_text": "Tims",
        "evidence_ref": "ev_ledger_041",
        "source_priority": "primary"
      },
      {
        "signal_type": "raw_bank_text",
        "surface_text": "TIM HORTONS #1234",
        "evidence_ref": "ev_bank_088",
        "source_priority": "supporting"
      }
    ],
    "evidence_refs": ["ev_ledger_041", "ev_bank_088"],
    "authority": {
      "source_authority_category": "accountant_processed_books",
      "role_authority_category": "accountant_derived_from_processed_books"
    },
    "aliases": [
      {
        "surface_text": "TIM HORTONS #1234",
        "alias_status": "candidate_alias",
        "evidence_ref": "ev_bank_088"
      }
    ],
    "roles": [
      {
        "role": "restaurant_vendor",
        "authority": "accountant_derived_from_processed_books",
        "source_ref": "ev_ledger_041"
      }
    ],
    "status": "active",
    "created_from": "onboarding_node",
    "governance_candidate_refs": ["cand_alias_approval_014"],
    "entity_reason": "ledger and bank evidence support same vendor; bank alias still requires approval before rule match"
  },
  "rule_and_governance_candidate_package": {
    "candidate_package_id": "cand_pkg_014",
    "client_id": "client_abc",
    "package_status": "ready_for_review",
    "trigger_source": "onboarding_node",
    "authority_limit_context": "candidate_only_for_rule_and_alias",
    "evidence_refs": ["ev_ledger_041", "ev_bank_088"],
    "candidate_items": [
      {
        "candidate_item_id": "cand_alias_approval_014",
        "candidate_type": "alias_approval",
        "candidate_summary": "Consider approving TIM HORTONS #1234 as alias for Tim Hortons",
        "source_refs": ["ev_bank_088"],
        "requires_accountant_approval": true,
        "approval_status": "not_submitted"
      },
      {
        "candidate_item_id": "cand_rule_014",
        "candidate_type": "rule_candidate",
        "candidate_summary": "Repeated accountant-treated Tim Hortons cases may support an initial rule",
        "source_refs": ["case_hist_011", "case_hist_012"],
        "requires_accountant_approval": true,
        "approval_status": "not_submitted"
      }
    ]
  }
}
```

Why valid：

- entity foundation 只回答 identity / role context。
- bank alias 仍是 `candidate_alias`，不能支持 rule match。
- rule remains candidate-only。
- role 的 durable authority 来自 accountant-processed books，并保留 source。

### 7.3 Invalid example

```json
{
  "historical_case_record_or_candidate": {
    "case_output_id": "case_out_bad_001",
    "client_id": "client_abc",
    "case_write_status": "written_accountant_derived_case",
    "historical_transaction_ref": "hist_txn_009",
    "final_historical_treatment": {
      "coa_account_ref": "Meals and Entertainment",
      "tax_treatment_context": "HST included"
    },
    "case_authority_category": "insufficient_accounting_authority",
    "evidence_refs": ["ev_bank_009"],
    "entity_context_ref": "ent_candidate_009",
    "created_from": "onboarding_node"
  },
  "rule_and_governance_candidate_package": {
    "candidate_package_id": "cand_pkg_bad_001",
    "client_id": "client_abc",
    "package_status": "ready_for_review",
    "candidate_items": [
      {
        "candidate_item_id": "rule_bad_001",
        "candidate_type": "rule_candidate",
        "candidate_summary": "Automatically classify future matching bank text as Meals and Entertainment",
        "source_refs": ["ev_bank_009"],
        "requires_accountant_approval": false,
        "approval_status": "approved"
      }
    ]
  }
}
```

Why invalid：

- raw bank evidence alone cannot support `written_accountant_derived_case`。
- `case_authority_category = insufficient_accounting_authority` contradicts confirmed case write。
- entity is only candidate but the output implies future deterministic automation。
- rule candidate is incorrectly marked approved and does not require accountant approval。

## 8. Open Contract Boundaries

以下问题未被 live docs 冻结，但不阻塞本 Stage 3 contract：

- `re_onboarding_candidate` 和 `incremental_historical_import_candidate` 是否完整复用本节点，还是需要独立 trigger / authority boundary。
- profile candidate 到 stable Profile truth 的 exact confirmation workflow。
- initial rule candidate 到 active Rule Log 的 exact approval workflow。
- 初始化部分失败时，主 workflow 是否允许启动，以及以什么 restrictions 启动。
- `stable_initial_entity_supported`、`accountant_derived_role`、`eligible_for_accountant_derived_case` 的具体 evidence threshold / scoring。
- Onboarding 是否可直接执行任何 automation policy downgrade，还是只能提出 candidate。
- historical transaction identity seed 的全局 registry owner 与 Transaction Identity Node 的 exact handoff。
- candidate package 是否需要独立持久化 store；若持久化，不能误称为 `Log`，除非 active baseline 明确定义。
- historical COA / tax treatment 与当前客户 COA / tax config 的 mapping contract 尚未冻结；Onboarding 只能保留 historical context 和 candidate。

## 9. Self-Review

- 已按要求读取 `AGENTS.md`、`TASK_STATE.md`、`PLANS.md`、`CLAUDE.md`、`DECISIONS.md`、`supporting documents/communication_preferences.md`、`supporting documents/development_workflow.md`、`supporting documents/node_design_roadmap.md`、`new system/new_system.md`。
- 已读取 prior approved docs：`onboarding_node__stage_1__functional_intent.md`、`onboarding_node__stage_2__logic_and_boundaries.md`。
- 已读取可用 Superpowers docs：`using-superpowers/SKILL.md`、`brainstorming/SKILL.md`；project workflow skill `ai-bookkeeper-node-design-facilitation` 在当前环境不存在，因此按 runner instruction 使用 repo `supporting documents/node_design_roadmap.md` 与本节点 Stage 1/2 docs 作为 workflow authority。
- 已注意 optional `supporting documents/node_design_roadmap_zh.md` 在 working tree 中缺失；未引用或发明该文件。
- 本文件只定义 Stage 3 data contracts；未写 Stage 4 execution algorithm、Stage 5 technical map、Stage 6 test matrix、Stage 7 coding-agent task contract。
- 未把 `Transaction Log` 当作 runtime decision、learning layer 或 onboarding write target。
- 未把 candidate queue、runtime handoff、summary draft 或 review package 命名为 durable `Log`。
- 未发明 accountant / governance approval authority；profile、rule、automation、alias / role governance、merge/split 均保持 approval boundary。
- 本次只写入目标文件：`new system/node_stage_designs/onboarding_node__stage_3__data_contract.md`。
