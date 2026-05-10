# Evidence Intake / Preprocessing Node — Stage 3：Data Contract Spec

## 1. Stage 范围

本 Stage 3 只定义 `Evidence Intake / Preprocessing Node` 的 data contracts。

前置依据：

- `new system/new_system.md`
- `new system/node_stage_designs/evidence_intake_preprocessing_node__stage_1__functional_intent.md`
- `new system/node_stage_designs/evidence_intake_preprocessing_node__stage_2__logic_and_boundaries.md`

本阶段把 Stage 1/2 已批准的行为边界转换成 implementation-facing input / output object categories、字段含义、字段 authority、runtime-only 与 durable-memory 边界、validation rules 和 compact examples。

本阶段不定义：

- step-by-step execution algorithm
- technical implementation map、repo module path、class / API / storage engine
- DB migration 或 code file layout
- Stage 6 test matrix / fixture plan
- coding-agent task contract
- 新 product authority
- legacy replacement mapping

## 2. Contract Position in Workflow

### 2.1 Upstream handoff consumed

本节点消费主 workflow 入口侧的新交易材料：

- bank / payment account import line
- receipt、cheque、invoice、contract 等 supporting evidence
- client / accountant 对当前交易或当前 batch 的原始说明
- 当前 batch 内已存在的 intake context 或 evidence reference

这些 upstream materials 是 evidence source，不是 transaction identity、entity、rule、case 或 accounting authority。

### 2.2 Downstream handoff produced

本节点输出给：

- `Transaction Identity Node`：objective transaction basis、evidence refs、association / duplicate-looking signals
- `Profile / Structural Match Node`：客观交易字段与 evidence refs
- `Entity Resolution Node`：raw counterparty / vendor / payee signals、supporting evidence refs、quality context
- `Coordinator / Pending Node` / `Review Node`：missing、conflicting、unmatched、low-quality evidence issue signals
- 后续 audit / memory workflow：可回溯 evidence references

本节点不向下游输出 accounting conclusion、entity conclusion、rule result、case judgment 或 final routing decision。

### 2.3 Logs / memory stores read

本节点可以读取或消费：

- 当前 runtime raw materials
- 当前 batch intake context
- 已存在的 `Evidence Log` references，用于避免重复保存或保留 source relation
- 外部导入状态或材料来源说明

本节点不得读取 `Transaction Log` 做 runtime decision。
本节点不得读取 `Case Log`、`Rule Log`、`Knowledge Log / Summary Log` 来判断当前交易业务含义。

### 2.4 Logs / memory stores written or candidate-only

本节点可以写入或请求追加：

- `Evidence Log` record / evidence reference
- objective intake / normalization context
- evidence quality、source clarity、association status、parsing issue context

这些写入只能属于 evidence layer。

本节点只能 candidate-only 输出：

- evidence association candidate
- unmatched supporting evidence candidate
- duplicate-looking raw material candidate
- missing / conflicting / low-quality evidence issue

本节点绝不能写入或修改：

- `Transaction Log`
- `Entity Log`
- `Case Log`
- `Rule Log`
- `Governance Log`
- `Profile`

## 3. Input Contracts

### 3.1 `RuntimeMaterialIntakeEnvelope`

Purpose：把一次 runtime intake 的材料放在同一个处理边界中。

Source authority：workflow orchestrator / external importer / user upload context。它只说明材料进入系统的上下文，不提供业务结论。

Required fields：

| Field | Meaning | Runtime / Durable |
| --- | --- | --- |
| `intake_batch_id` | 本次 intake 批次或运行窗口的引用 | runtime-only，可被 durable records 引用 |
| `client_id` | 当前客户引用 | durable reference |
| `received_at` | 系统接收材料的时间 | durable evidence metadata |
| `source_channel` | 材料进入系统的渠道 | durable evidence metadata |
| `material_refs` | 本 envelope 包含的 raw material references | runtime handoff，material 本身可进入 Evidence Log |

Allowed `source_channel` values：

- `bank_import`
- `payment_account_import`
- `supporting_upload`
- `client_note`
- `accountant_note`
- `supplemental_evidence`
- `external_import_context`

Optional fields：

| Field | Meaning | Runtime / Durable |
| --- | --- | --- |
| `batch_context_note` | 与当前 batch 有关的原始说明 | evidence metadata；不是业务结论 |
| `related_runtime_refs` | 当前运行中可能相关的临时对象引用 | runtime-only |
| `source_system_name` | 外部系统名称，例如 bank portal 或 accounting export source | durable evidence metadata |

Validation / rejection rules：

- `intake_batch_id`、`client_id`、`received_at`、`source_channel`、`material_refs` 必须存在。
- `source_channel` 必须属于允许值。
- `material_refs` 不能为空。
- envelope 不能声称 `transaction_id`、`entity_id`、`rule_id`、COA、HST/GST 或 JE 结论。

### 3.2 `RawTransactionSourceMaterial`

Purpose：表达 bank / payment account 原始交易来源材料，以及可从来源中读取的客观事实。

Source authority：bank statement、payment account export、processor feed 或其他 source-provided transaction line。

Required fields：

| Field | Meaning | Runtime / Durable |
| --- | --- | --- |
| `source_material_id` | 原始交易材料引用 | durable evidence reference |
| `source_type` | 原始交易来源类型 | durable evidence metadata |
| `raw_evidence_pointer` | 可回到原始文件、行、页面或 payload 的引用 | durable evidence reference |
| `source_account_ref` | 来源账户或支付账户引用；未能确认时使用 source-provided account label | evidence metadata；不是 COA |
| `raw_amount_text` | 来源材料中的原始金额表示 | durable evidence content / reference |
| `raw_date_text` | 来源材料中的原始日期表示 | durable evidence content / reference |
| `raw_description` | 来源材料中的原始描述，允许为空但字段必须显式存在 | durable evidence content / reference |

Allowed `source_type` values：

- `bank_statement_line`
- `payment_account_export_line`
- `processor_feed_line`
- `manual_transaction_source`
- `other_transaction_source`

Optional fields：

| Field | Meaning | Runtime / Durable |
| --- | --- | --- |
| `currency` | source-provided currency | objective fact when present |
| `posted_at_text` | source-provided posted date/time text | evidence content / reference |
| `debit_credit_marker` | source-provided debit / credit label | evidence content / reference |
| `source_row_ref` | row number、page number、entry id 等来源定位 | durable evidence reference |
| `counterparty_surface_text` | 原始材料表面出现的 counterparty / vendor / payee signal | evidence signal；不是 entity conclusion |

Validation / rejection rules：

- `raw_evidence_pointer` 必须足以回到原始材料。
- `raw_amount_text` 和 `raw_date_text` 缺失时，材料仍可保存为 evidence，但不能产出 complete `ObjectiveNormalizedTransactionBasis`。
- `source_account_ref` 不得被解释为 COA account。
- `counterparty_surface_text` 不得被解释为稳定 `Entity`、approved alias 或 role。

### 3.3 `SupportingEvidenceMaterial`

Purpose：表达当前交易或当前 batch 相关的 supporting evidence。

Source authority：uploaded file、OCR/parser result、client/accountant note 原文、external attachment metadata。

Required fields：

| Field | Meaning | Runtime / Durable |
| --- | --- | --- |
| `supporting_material_id` | supporting material 引用 | durable evidence reference |
| `evidence_type` | supporting evidence 类型 | durable evidence metadata |
| `raw_evidence_pointer` | 可回到原始附件、页面、图片、文本或 note 的引用 | durable evidence reference |
| `received_at` | 系统接收 supporting evidence 的时间 | durable evidence metadata |
| `source_actor_type` | 提供材料的一方 | durable evidence metadata |

Allowed `evidence_type` values：

- `receipt`
- `cheque`
- `invoice`
- `contract`
- `client_note`
- `accountant_note`
- `historical_attachment`
- `other_supporting_material`

Allowed `source_actor_type` values：

- `client`
- `accountant`
- `system_import`
- `third_party_source`
- `unknown`

Optional fields：

| Field | Meaning | Runtime / Durable |
| --- | --- | --- |
| `captured_text` | OCR、parser 或手动录入的可读文本 | derived evidence content；不能覆盖 raw evidence |
| `visible_vendor_text` | 材料表面出现的 vendor / payee name | evidence signal；不是 entity conclusion |
| `visible_date_text` | 材料表面出现的日期 | evidence signal |
| `visible_amount_text` | 材料表面出现的金额 | evidence signal |
| `note_text` | client/accountant 原话 | durable evidence content |
| `author_id` | note 作者引用 | durable evidence metadata when present |

Validation / rejection rules：

- `raw_evidence_pointer` 必须存在。
- `source_actor_type = accountant` 不等于 accountant approval；除非下游 Review / Governance flow 明确批准，本节点只能保存原话。
- `captured_text`、`visible_vendor_text`、`visible_date_text`、`visible_amount_text` 都是 extracted evidence signals，不能覆盖原始材料。

### 3.4 `AssociationInputHint`

Purpose：表达 upstream 或 source system 提供的材料关联线索。

Source authority：importer metadata、file naming、upload grouping、client/accountant 原始说明、当前 batch runtime context。

Required fields：

| Field | Meaning | Runtime / Durable |
| --- | --- | --- |
| `hint_id` | 关联线索引用 | runtime-only unless preserved as evidence metadata |
| `hint_source` | 线索来源 | evidence metadata |
| `material_ref_ids` | 被线索关联的一组材料引用 | runtime handoff |
| `hint_type` | 线索类型 | runtime handoff / evidence metadata |

Allowed `hint_type` values：

- `same_upload_group`
- `same_source_file`
- `client_claimed_related`
- `accountant_claimed_related`
- `filename_or_folder_hint`
- `source_system_link`
- `possible_duplicate_material`

Optional fields：

| Field | Meaning | Runtime / Durable |
| --- | --- | --- |
| `hint_text` | 原始线索文本 | evidence metadata if preserved |
| `confidence_from_source` | source system 自带置信说明 | runtime-only unless source metadata requires retention |

Validation / rejection rules：

- hint 不能直接变成 confirmed association。
- `accountant_claimed_related` 表示 accountant 原话存在，不表示 review approval 已完成。
- `possible_duplicate_material` 只能交给下游 identity / review 评估，不能由本节点做 final dedupe。

### 3.5 `ExistingEvidenceReferenceContext`

Purpose：允许本节点识别已保存 evidence reference，避免重复保存或保留补交材料与既有 evidence 的关系。

Source authority：`Evidence Log` / current runtime intake registry。

Required fields：

| Field | Meaning | Runtime / Durable |
| --- | --- | --- |
| `evidence_ref_id` | 已存在 evidence reference | durable evidence reference |
| `client_id` | 所属客户引用 | durable reference |
| `evidence_type` | 已保存 evidence 类型 | durable evidence metadata |
| `preservation_status` | 已保存 evidence 的保留状态 | durable evidence metadata |

Allowed `preservation_status` values：

- `preserved`
- `reference_only`
- `superseded_by_clearer_copy`
- `rejected_untraceable`

Optional fields：

| Field | Meaning | Runtime / Durable |
| --- | --- | --- |
| `related_intake_batch_id` | 与既有 evidence 相关的 intake batch | durable reference |
| `content_fingerprint_ref` | 用于判断 material 是否重复的内容指纹引用 | evidence metadata；不定义 hash implementation |

Validation / rejection rules：

- 只能用于 evidence preservation / reference discipline。
- 不能从既有 evidence reference 推断业务结论。
- 不能读取 `Transaction Log` 来补足 runtime decision。

## 4. Output Contracts

### 4.1 `EvidenceLogRecord`

Purpose：保存原始 evidence 和 evidence reference，使后续 workflow 与 audit 能回到来源材料。

Consumer / downstream authority：`Evidence Log`、后续 workflow nodes、audit / review 查询。它只提供 evidence authority，不提供 business authority。

Required fields：

| Field | Meaning | Memory boundary |
| --- | --- | --- |
| `evidence_ref_id` | Evidence Log 内的 evidence reference | durable evidence |
| `client_id` | 客户引用 | durable reference |
| `source_material_id` | 来源 raw/supporting material reference | durable evidence |
| `evidence_type` | evidence 类型 | durable evidence metadata |
| `raw_evidence_pointer` | 可回到原始材料的引用 | durable evidence |
| `source_channel` | 材料进入渠道 | durable evidence metadata |
| `source_actor_type` | 材料提供方 | durable evidence metadata |
| `received_at` | 系统接收时间 | durable evidence metadata |
| `preservation_status` | evidence 保存状态 | durable evidence metadata |

Allowed `evidence_type` values：

- `bank_statement_line`
- `payment_account_export_line`
- `processor_feed_line`
- `manual_transaction_source`
- `receipt`
- `cheque`
- `invoice`
- `contract`
- `client_note`
- `accountant_note`
- `historical_attachment`
- `other_supporting_material`
- `other_transaction_source`

Allowed `source_actor_type` values：

- `client`
- `accountant`
- `system_import`
- `third_party_source`
- `unknown`

Allowed `preservation_status` values：

- `preserved`
- `reference_only`
- `superseded_by_clearer_copy`
- `rejected_untraceable`

Optional fields：

| Field | Meaning | Memory boundary |
| --- | --- | --- |
| `captured_text_ref` | OCR/parser/text extraction 的引用 | durable derived evidence reference |
| `content_fingerprint_ref` | 重复材料识别用内容指纹引用 | durable evidence metadata |
| `source_location` | file、page、row、payload path 等来源定位 | durable evidence metadata |
| `intake_batch_id` | 产生该 record 的 intake batch | durable reference |
| `quality_issue_ids` | 相关 evidence quality issues | durable evidence context |

Validation rules：

- 必须能回到 raw evidence；只有模型摘要而无 `raw_evidence_pointer` 的输出无效。
- 不得包含 `transaction_id` assignment、`entity_id` conclusion、COA、HST/GST、JE、rule result 或 case judgment。
- `rejected_untraceable` 可以记录 rejection metadata，但不能作为后续自动化 evidence basis。

### 4.2 `ObjectiveNormalizedTransactionBasis`

Purpose：把可客观解析的交易结构统一成下游可消费的 basis。

Consumer / downstream authority：`Transaction Identity Node`、`Profile / Structural Match Node`、后续 entity / case workflow。它是 objective fact basis，不是 permanent transaction identity。

Required fields：

| Field | Meaning | Memory boundary |
| --- | --- | --- |
| `objective_basis_id` | 当前 normalized basis 引用 | runtime handoff；可被 evidence context 引用 |
| `source_material_id` | 来源 raw transaction material | durable evidence reference |
| `parse_status` | 客观结构解析状态 | runtime handoff / evidence context |
| `date_basis` | 解析出的交易日期及其 source reference；可为 null | objective fact when present |
| `amount_absolute_basis` | 解析出的绝对金额及其 source reference；可为 null | objective fact when present |
| `direction_basis` | 解析出的 money direction 及其 source reference；可为 null | objective fact when present |
| `source_account_basis` | 来源账户 basis；不是 COA | objective fact when present |
| `raw_description_ref` | 原始描述 evidence reference | durable evidence reference |

Allowed `parse_status` values：

- `parsed`
- `partially_parsed`
- `unparseable`

Allowed `direction_basis.value` values when known：

- `money_in`
- `money_out`
- `unknown`

Optional fields：

| Field | Meaning | Memory boundary |
| --- | --- | --- |
| `currency_basis` | currency 及其 source reference | objective fact when present |
| `posted_at_basis` | posted date/time 及其 source reference | objective fact when present |
| `counterparty_surface_text_refs` | raw description / receipt / cheque 等表面文本引用 | evidence signal；不是 entity |
| `normalization_issue_ids` | 解析或标准化问题 | evidence context |

Validation rules：

- `parsed` 必须至少有 `date_basis`、`amount_absolute_basis`、`direction_basis`、`source_account_basis`。
- `partially_parsed` 必须显式说明缺失或冲突的 basis。
- `unparseable` 不得伪造客观字段；只能携带 source reference 和 issue。
- 本节点不得在此对象中分配 `transaction_id`。
- `amount_absolute_basis` 不得携带方向符号；direction 必须由 `direction_basis` 表达。

### 4.3 `EvidenceAssociationResult`

Purpose：表达多份材料之间的客观关联、候选关联、无法关联或冲突状态。

Consumer / downstream authority：`Transaction Identity Node`、Coordinator / Review、audit context。它不替代 transaction identity / dedupe authority。

Required fields：

| Field | Meaning | Memory boundary |
| --- | --- | --- |
| `association_result_id` | association result 引用 | runtime handoff；可被 evidence context 引用 |
| `material_ref_ids` | 被评估的一组材料 | evidence references |
| `association_status` | 关联状态 | runtime handoff / evidence context |
| `basis_refs` | 支持该状态的来源引用 | evidence references |
| `reason` | 简短客观说明 | evidence context |

Allowed `association_status` values：

- `confirmed_objective_association`
- `candidate_association`
- `unassociated`
- `conflicting_association`
- `duplicate_material_candidate`

Optional fields：

| Field | Meaning | Memory boundary |
| --- | --- | --- |
| `conflict_issue_ids` | 对应 conflict issue | evidence context |
| `candidate_strength` | 粗粒度候选强度 | runtime-only unless retained as evidence context |

Allowed `candidate_strength` values when present：

- `strong`
- `weak`
- `unknown`

Validation rules：

- `confirmed_objective_association` 只能表示材料间客观配对成立，不能表示 same transaction identity 已确认。
- `candidate_association`、`duplicate_material_candidate` 不能支持 rule match、case promotion 或 durable business memory。
- `conflicting_association` 必须引用具体冲突来源。

### 4.4 `EvidenceQualityIssueSignal`

Purpose：把 missing、ambiguous、conflicting、unreadable、source-unclear 等 evidence issue 显露给下游。

Consumer / downstream authority：`Coordinator / Pending Node`、`Review Node`、`Transaction Identity Node`、audit context。它不是 accountant question、pending decision 或 classification result。

Required fields：

| Field | Meaning | Memory boundary |
| --- | --- | --- |
| `issue_id` | issue 引用 | runtime handoff；可进入 evidence context |
| `issue_type` | issue 类型 | evidence context |
| `affected_material_refs` | 受影响材料 | evidence references |
| `severity` | 对 objective handoff 的影响 | evidence context |
| `summary` | 简短客观说明 | evidence context |

Allowed `issue_type` values：

- `missing_core_transaction_fact`
- `unreadable_material`
- `unsupported_format`
- `source_unclear`
- `parsing_failed`
- `partial_parse`
- `evidence_conflict`
- `unmatched_supporting_evidence`
- `candidate_association_only`
- `duplicate_material_candidate`

Allowed `severity` values：

- `blocks_objective_handoff`
- `allows_handoff_with_issue`
- `informational`

Optional fields：

| Field | Meaning | Memory boundary |
| --- | --- | --- |
| `needed_followup_subject` | 下游可能需要追问的主题 | runtime handoff |
| `conflicting_values` | 冲突值及来源引用 | evidence context |
| `source_excerpt_refs` | 支持 issue 的短摘录引用 | evidence references |

Validation rules：

- issue signal 不得自行生成 accountant-facing question。
- issue signal 不得决定 PENDING、review_required 或 classification path。
- `evidence_conflict` 必须列出冲突来源，不能只写“conflict”。

### 4.5 `EvidenceFoundationHandoff`

Purpose：把本节点整理后的 evidence foundation 交给下游 workflow nodes。

Consumer / downstream authority：直接下游 workflow。它是 runtime handoff，不是 durable business memory。

Required fields：

| Field | Meaning | Memory boundary |
| --- | --- | --- |
| `handoff_id` | 本次下游交接引用 | runtime-only |
| `intake_batch_id` | 来源 intake batch | runtime reference |
| `client_id` | 当前客户 | durable reference |
| `handoff_status` | 交接状态 | runtime handoff |
| `evidence_ref_ids` | 本次 handoff 可用 evidence references | durable evidence references |
| `objective_basis_ids` | 可用 objective normalized basis references | runtime / evidence context |
| `association_result_ids` | association result references | runtime / evidence context |
| `quality_issue_ids` | issue signal references | runtime / evidence context |

Allowed `handoff_status` values：

- `ready`
- `ready_with_issues`
- `rejected_invalid_input`

Optional fields：

| Field | Meaning | Memory boundary |
| --- | --- | --- |
| `downstream_notes` | 给下游的客观上下文摘要 | runtime-only |
| `supplemental_to_runtime_ref` | 补交材料可能对应的 runtime transaction candidate | runtime-only；不是 transaction identity |

Validation rules：

- `ready` 至少需要一个 usable `ObjectiveNormalizedTransactionBasis`。
- `ready_with_issues` 必须引用至少一个 `EvidenceQualityIssueSignal` 或 non-confirmed `EvidenceAssociationResult`。
- `rejected_invalid_input` 必须说明 rejection issue，且不得输出伪造 objective basis。
- handoff 不得包含 final routing、classification、entity conclusion、rule result 或 JE。

## 5. Field Authority and Memory Boundary

### 5.1 Source of truth for important fields

- Raw material content 的 source of truth 是原始 file、row、payload、image、note 或 external source record。
- `raw_evidence_pointer` / `source_location` 的 authority 来自 importer、upload context 或 evidence preservation layer。
- `date_basis`、`amount_absolute_basis`、`direction_basis`、`currency_basis` 的 authority 来自原始材料加本节点 objective extraction；它们不是业务判断。
- `counterparty_surface_text_refs`、`visible_vendor_text`、`visible_amount_text` 是 evidence signals，不是 stable entity、alias approval 或 role confirmation。
- `association_status` 的 authority 只限于 evidence association discipline，不延伸为 transaction identity / dedupe authority。
- `quality_issue` 的 authority 只说明 evidence condition，不说明 accounting treatment。

### 5.2 Fields that can never become durable memory by this node

本节点不能把以下字段或结论写成 durable business memory：

- `transaction_id` assignment
- stable `entity_id`
- approved alias
- confirmed role/context
- COA account
- HST/GST treatment
- journal entry
- deterministic rule result
- case judgment / precedent applicability
- accountant approval
- governance approval
- automation policy change

其中 `transaction_id` 可以由 `Transaction Identity Node` 产生，但不能由本节点产生。

### 5.3 Fields that can become durable only after accountant / governance approval

以下内容即使从本节点材料中出现，也只能作为 evidence 或 candidate signal 传递；只有经过下游 accountant / governance authority path 后，才可能成为长期 authority：

- client/accountant note 中包含的客户结构事实
- alias、entity、role/context 候选
- rule candidate 或 automation policy candidate
- 对 evidence conflict 的业务解释
- 对 supporting evidence 与交易用途关系的确认

本节点可以保存“某人说过什么”和“材料表面显示什么”，不能批准其长期业务含义。

### 5.4 Audit vs learning / logging boundary

- `Evidence Log` 保存原始证据和证据引用，不保存业务结论。
- `Transaction Log` 保存最终处理结果和审计轨迹；本节点不写，也不把它作为 runtime decision source。
- Evidence quality / association issue 可以成为 audit context，但不能成为 learning layer 的 business conclusion。
- Candidate association、duplicate-looking signal、unmatched evidence 不是 durable learning。

## 6. Validation Rules

### 6.1 Contract-level validation rules

- 所有 output 必须能追溯到 input material 或 existing evidence reference。
- 所有 extracted fields 必须保留 source reference；不能只有模型总结。
- Objective facts、evidence signals、candidate signals、business authority 必须分层表达。
- `Log` 只能指 durable long-term meaningful information storage；runtime handoff、candidate queue、temporary parse result 不能命名为 `Log`。
- `Transaction Log` 不参与本节点 runtime decision。

### 6.2 Conditions that make input invalid

Input invalid if：

- 没有 `client_id`。
- 没有任何可追溯 raw material reference。
- `source_channel`、`source_type`、`evidence_type` 或 `source_actor_type` 不属于允许值。
- 材料只提供摘要，没有 raw evidence pointer。
- 输入把 COA、HST/GST、entity、rule、case 或 transaction identity 当作本节点应接受的 asserted fact。
- accountant/client note 缺少 source actor metadata，却要求作为 authority 使用。

### 6.3 Conditions that make output invalid

Output invalid if：

- output 无法追溯到 raw evidence。
- output 用 OCR/parser/LLM extraction 覆盖原始 evidence。
- output 分配 `transaction_id`。
- output 生成 stable entity、approved alias、confirmed role、rule result、case judgment、COA、HST/GST 或 JE。
- candidate association 被写成 confirmed transaction identity。
- issue signal 被写成 accountant decision、PENDING decision 或 final routing。
- handoff 读取或引用 `Transaction Log` 作为 runtime decision authority。

### 6.4 Stop / ask conditions for unresolved contract authority

后续 Stage 如果遇到以下情况，应 stop / ask，而不是自行冻结：

- 需要决定 Evidence Log 写入是在 identity 前、identity 后，还是分为 pre-identity reference 与 post-identity attachment。
- 需要决定 supplemental evidence 对既有 transaction 的 re-intake / amendment 覆盖规则。
- 需要把 evidence association candidate 升级为 confirmed transaction association 的 authority。
- 需要让本节点读取 `Profile`、`Entity Log`、`Case Log`、`Rule Log` 或 `Transaction Log` 参与判断。
- 需要改变本节点不写 `Transaction Log` / business memory 的边界。

## 7. Examples

### 7.1 Valid minimal example

```yaml
input:
  intake_envelope:
    intake_batch_id: intake_2026_05_06_001
    client_id: client_abc
    received_at: "2026-05-06T10:15:00-07:00"
    source_channel: bank_import
    material_refs: [mat_bank_001]
  raw_transaction_material:
    source_material_id: mat_bank_001
    source_type: bank_statement_line
    raw_evidence_pointer: bank_file_01.csv:row:12
    source_account_ref: RBC chequing ending 1234
    raw_amount_text: "45.20"
    raw_date_text: "2026-05-05"
    raw_description: "TIMS COFFEE-1234"

output:
  evidence_log_record:
    evidence_ref_id: ev_001
    client_id: client_abc
    source_material_id: mat_bank_001
    evidence_type: bank_statement_line
    raw_evidence_pointer: bank_file_01.csv:row:12
    source_channel: bank_import
    source_actor_type: system_import
    received_at: "2026-05-06T10:15:00-07:00"
    preservation_status: preserved
  objective_basis:
    objective_basis_id: obj_001
    source_material_id: mat_bank_001
    parse_status: parsed
    date_basis: { value: "2026-05-05", source_ref: ev_001 }
    amount_absolute_basis: { value: "45.20", source_ref: ev_001 }
    direction_basis: { value: money_out, source_ref: ev_001 }
    source_account_basis: { value: "RBC chequing ending 1234", source_ref: ev_001 }
    raw_description_ref: ev_001
  handoff:
    handoff_id: handoff_001
    intake_batch_id: intake_2026_05_06_001
    client_id: client_abc
    handoff_status: ready
    evidence_ref_ids: [ev_001]
    objective_basis_ids: [obj_001]
    association_result_ids: []
    quality_issue_ids: []
```

Why valid：输出只包含 evidence reference 与 objective basis，没有 transaction identity、entity、rule、case 或 accounting conclusion。

### 7.2 Valid richer example

```yaml
input:
  intake_envelope:
    intake_batch_id: intake_2026_05_06_002
    client_id: client_abc
    received_at: "2026-05-06T11:00:00-07:00"
    source_channel: supplemental_evidence
    material_refs: [mat_bank_010, mat_receipt_010]
  raw_transaction_material:
    source_material_id: mat_bank_010
    source_type: bank_statement_line
    raw_evidence_pointer: bank_file_01.csv:row:44
    source_account_ref: RBC visa ending 5555
    raw_amount_text: "1,284.77"
    raw_date_text: "2026-05-03"
    raw_description: "HOME DEPOT #4521"
  supporting_evidence_material:
    supporting_material_id: mat_receipt_010
    evidence_type: receipt
    raw_evidence_pointer: receipts/home_depot_4521.jpg
    received_at: "2026-05-06T11:00:00-07:00"
    source_actor_type: client
    captured_text: "HOME DEPOT ... cement ... rebar ... total 1284.77"
    visible_vendor_text: "HOME DEPOT"
    visible_amount_text: "1284.77"

output:
  association_result:
    association_result_id: assoc_010
    material_ref_ids: [mat_bank_010, mat_receipt_010]
    association_status: candidate_association
    basis_refs: [ev_bank_010, ev_receipt_010]
    reason: "Amount and visible vendor align; date source still needs downstream confirmation."
    candidate_strength: strong
  quality_issue:
    issue_id: issue_010
    issue_type: candidate_association_only
    affected_material_refs: [mat_bank_010, mat_receipt_010]
    severity: allows_handoff_with_issue
    summary: "Receipt appears related but association is not final transaction identity."
  handoff:
    handoff_id: handoff_010
    intake_batch_id: intake_2026_05_06_002
    client_id: client_abc
    handoff_status: ready_with_issues
    evidence_ref_ids: [ev_bank_010, ev_receipt_010]
    objective_basis_ids: [obj_010]
    association_result_ids: [assoc_010]
    quality_issue_ids: [issue_010]
```

Why valid：receipt 内容被保留为 evidence signal；材料关联保持 candidate，不被提升为交易身份、business purpose、COA 或 HST/GST 判断。

### 7.3 Invalid example

```yaml
output:
  objective_basis:
    objective_basis_id: obj_bad_001
    transaction_id: txn_01HZX...
    date_basis: { value: "2026-05-03", source_ref: ev_010 }
    amount_absolute_basis: { value: "-1284.77", source_ref: ev_010 }
    direction_basis: { value: money_out, source_ref: ev_010 }
    entity_id: ent_home_depot
    coa_account: Materials
    hst_treatment: ITC_claimable
  association_result:
    association_status: confirmed_objective_association
    reason: "The receipt proves this is a business purchase."
```

Invalid reasons：

- 本节点不能分配 `transaction_id`。
- `amount_absolute_basis` 不能带方向符号。
- 本节点不能输出 stable entity、COA 或 HST/GST treatment。
- receipt 不能由本节点解释成 final business purpose。
- association reason 把 evidence association 混成了 accounting conclusion。

## 8. Open Contract Boundaries

- Evidence Log 写入的 exact timing 未冻结：当前 contract 定义 logical `EvidenceLogRecord` 与 handoff reference，不决定是 pre-identity 立即持久化、identity 后绑定，还是两阶段引用。
- Supplemental evidence 的 re-intake / amendment workflow 未冻结：本节点可以表达 `supplemental_to_runtime_ref`，但不能决定覆盖既有 transaction 或重写 downstream outcome。
- `confirmed_objective_association` 的精确 authority threshold 未冻结：本 Stage 只要求它不得等同 transaction identity / dedupe。
- Evidence issue 如何转化为 accountant-facing question，属于 `Coordinator / Pending Node` 或 `Review Node` 后续 contract。
- `content_fingerprint_ref` 只作为 contract-level duplicate-material reference，不定义 hash / storage implementation。

## 9. Self-Review

- 已按要求读取 `AGENTS.md`、`TASK_STATE.md`、`PLANS.md`、`CLAUDE.md`、`DECISIONS.md`、`supporting documents/communication_preferences.md`、`supporting documents/development_workflow.md`、`supporting documents/node_design_roadmap.md`、`new system/new_system.md`。
- 已读取本节点 Stage 1 / Stage 2 approved docs。
- 已读取可用 Superpowers docs：`using-superpowers/SKILL.md`、`brainstorming/SKILL.md`；project workflow skill `ai-bookkeeper-node-design-facilitation` 在当前环境不存在，因此按 runner instruction 使用 repo `supporting documents/node_design_roadmap.md` 与本节点 Stage 1/2 docs 作为 workflow authority。
- 已确认 `supporting documents/node_design_roadmap_zh.md` 在 working tree 中缺失，未虚构该文件内容。
- 未引入 Stage 4 execution algorithm、Stage 5 technical implementation map、Stage 6 fixture/test matrix、Stage 7 coding-agent task contract。
- 未把 `Transaction Log` 作为 runtime decision source。
- 未赋予本节点 transaction identity、entity、rule、case、accounting 或 governance authority。
- 未使用 legacy specs 作为 active design source。
- 本次目标是仅写入本 Stage 3 文件；未要求也未修改 active baseline、Stage 1/2、governance 或 handoff docs。
