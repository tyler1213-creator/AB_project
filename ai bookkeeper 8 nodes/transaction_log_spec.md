# Transaction Log

---

## 1. 职责定义

为每一笔完成处理的交易保留完整的审计追溯记录。Transaction Log 只回答一个问题：**从报表或税表上的任何一个数字，能否一路追溯回原始凭证和分类依据？**

Transaction Log 不承担分类决策、pattern 聚合、系统优化分析等职责。它是只写+查询的明细库，不参与主 Workflow 的任何判断逻辑。

---

## 2. 数据格式

采用结构化数据库存储（如 SQLite），每条记录对应一笔完成处理的交易。

```yaml
# --- 第一层：交易事实 ---
transaction_id: "txn_01JVF8Y7T6M3K2N9Q4R5S8W1XZ"
date: "2024-07-18"
description: "HOME DEPOT"
raw_description: "HOME DEPOT 4521 TORONTO ON"
pattern_source: "dictionary_hit"
amount: 156.78
direction: "debit"
balance: 11299.45
currency: "CAD"
bank_account: "TD-5027013"
bs_source: "TD_Chequing_Jul_2024.pdf"

# --- 第二层：分类结果 ---
account: "Supplies & Materials"
hst: "inclusive_13"
je_lines:
  - { type: "debit", account: "Supplies & Materials", amount: 138.71 }
  - { type: "debit", account: "HST/GST Receivable", amount: 18.07 }
  - { type: "credit", account: "Business Chequing", amount: 156.78 }

# --- 第三层：决策依据 ---
classified_by: "ai_high_confidence"
rule_id: null
profile_match_detail: null
ai_reasoning: "HOME DEPOT 是建材零售商。小票显示购买 Portland Cement x3 和 Rebar 10mm x10，均为施工材料。客户行业为 Construction，分类为 Supplies & Materials。Observation 中该 pattern 历史 4 次均为相同分类。小票含 HST $18.07，与 inclusive_13 拆分结果一致。"
policy_trace:
  activated_packs: ["retail_personal_use_risk"]
  blocking_packs: []
  override_evidence: ["receipt_business_use", "stable_single_observation"]
  unresolved_risks: []
accountant_id: null
confirmed_info: null

# --- 第四层：补充证据 ---
receipt:
  source_file: "homedepot_receipt_0718.jpg"
  vendor_name: "The Home Depot #4521"
  items: ["Portland Cement x3", "Rebar 10mm x10"]
  tax_amount: 18.07
  match_confidence: "high"
cheque_info: null
supplementary_context: ""

# --- 第五层：元数据 ---
processing_date: "2024-08-02"
period: "2024-07"
parent_transaction_id: null
child_transaction_ids: null
```

### 字段说明

**第一层：交易事实**

- **transaction_id**：交易的永久唯一标识，由共享模块 `transaction_identity_and_dedup` 在 ingest 时分配，格式 `txn_<ULID>`。重复导入同一笔交易时必须复用同一 ID。它是 split / review / intervention / audit chain 的统一关联键
- **date**：交易日期，来自 BS 原始数据
- **description**：canonical pattern，来自数据预处理 Agent 的输出，是下游节点默认消费的交易描述字段；当交易不存在可识别 identity signal 时可为 null
- **raw_description**：银行原始描述原文，来自 BS 原始数据，主要用于审计留痕和 AI 参考，不作为默认的确定性匹配字段
- **pattern_source**：通过标准化工具生成 pattern 时的来源，取值 `dictionary_hit` / `llm_extraction` / `fallback`；若交易未经过标准化工具（如 cheque `payee` 直写或 `description = null`）则为 null
- **amount**：交易金额的绝对值，`Decimal > 0`。银行原始正负号由数据预处理 Agent 统一转换，不在下游继续传递符号语义
- **direction**：交易方向，严格取值 `debit` / `credit`。无法判断方向的记录不得进入主 Workflow，应在数据预处理阶段拦截并标记待人工确认
- **balance**：交易后余额，来自 BS 原始数据
- **currency**：币种，来自 BS 原始数据
- **bank_account**：所属银行账户标识，必须精确等于 `profile.bank_accounts[].id`，由数据预处理 Agent 从 BS 原始账户信息映射得到
- **bs_source**：来源 BS 文件名，来自数据预处理 Agent 输出

**第二层：分类结果**

- **account**：最终科目名称，来自完成分类的节点（Node 1 / Node 2 / 置信度分类器 / Coordinator Agent）的输出。如果审核阶段被修改，更新为修改后的值
- **hst**：HST 处理方式（exempt / inclusive_13 / unknown），来源同 account
- **je_lines**：完整的 JE 借贷分录，来自 build_je_lines.py 构造 + validate_je 校验的输出。如果审核阶段被修改，更新为重新构造的 JE

**第三层：决策依据**

- **classified_by**：当前分类的决策来源，记录谁对该交易的现行分类负责。四种取值：
  - `profile_match`：Node 1 通过 profile 中的 account_relationships 匹配（内部转账等）
  - `rule_match`：Node 2 通过 rules.md 中的 rule 匹配
  - `ai_high_confidence`：置信度分类器判断为高置信度并直接分类
  - `accountant_confirmed`：accountant 做出的分类决定（包括 Coordinator 阶段确认 PENDING 交易、审核阶段修正分类）
- **rule_id**：命中的 rule 编码，仅 classified_by = rule_match 时有值。来自 Node 2 匹配结果
- **profile_match_detail**：命中的 account_relationship 信息，仅 classified_by = profile_match 时有值。来自 Node 1 匹配结果。记录匹配到的 account_relationship 条目内容（pattern、from、to、type），用于审计追溯 Node 1 的原始信号匹配依据
- **ai_reasoning**：AI 的判断逻辑说明，仅 classified_by = ai_high_confidence 时有值。来自置信度分类器输出。内容需让不同水平的 accountant 都能看懂分类依据，包括：识别到的 vendor 类型、参考了哪些历史数据、小票/附件信息如何支持判断、HST 处理的依据
- **policy_trace**：Node 3 的结构化策略轨迹，仅 classified_by = ai_high_confidence 时有值。记录激活了哪些 risk packs、哪些属于 blocking、哪些 override evidence 使交易仍可高置信度，以及是否存在 unresolved_risks。它服务于审计追溯和审核排错，不作为主 Workflow 的输入
- **accountant_id**：做出分类确认的 accountant 姓名，仅 classified_by = accountant_confirmed 时有值。来自 Coordinator Agent 记录
- **confirmed_info**：accountant 提供的业务信息或判断依据，仅 classified_by = accountant_confirmed 时有值。来自 Coordinator Agent 记录的 accountant 原话或摘要

**第四层：补充证据**

- **receipt**：配对的小票信息，来自数据预处理 Agent 的小票配对结果。包含：
  - source_file：小票原始文件名
  - vendor_name：小票上的商家名称
  - items：购买项目列表
  - tax_amount：小票上的税额
  - match_confidence：小票与交易的配对置信度
- **cheque_info**：支票影像提取信息，来自数据预处理 Agent 的支票处理结果。无支票影像或关联失败时为 null。包含以下子字段：
  - cheque_number：支票号码
  - payee：收款人
  - memo：支票备注
  - match_method：关联方式，`cheque_number`（通过支票号精确关联）或 `amount_date`（通过金额+日期模糊关联）
- **supplementary_context**：Coordinator Agent 在处理拆分交易后子交易需要重新走 workflow 时注入的额外说明；其他情况为空字符串

**第五层：元数据**

- **processing_date**：该交易被系统处理的日期，系统自动记录
- **period**：所属会计期间（如 2024-07），由交易日期推算或 BS 覆盖期间确定
- **parent_transaction_id**：如果该交易是拆分后的子交易，指向原始交易的 transaction_id
- **child_transaction_ids**：如果该交易被拆分，指向所有子交易的 transaction_id 列表

---

## 3. 数据来源

**每笔交易在完成分类并生成 JE 后，由当前处理节点将信息写入 Transaction Log。**

### 写入时机与来源

| 写入节点 | 触发条件 | 写入的关键字段 |
| --- | --- | --- |
| Node 1（Profile 匹配） | 交易命中 profile 中的 account_relationships | classified_by = profile_match，profile_match_detail |
| Node 2（Rules 匹配） | 交易命中 rules.md 中的 rule | classified_by = rule_match，rule_id |
| 置信度分类器 | AI 判断为高置信度 | classified_by = ai_high_confidence，ai_reasoning，policy_trace |
| Coordinator Agent | Accountant 确认 PENDING 交易 | classified_by = accountant_confirmed，accountant_id，confirmed_info |

### 各层字段的写入来源

| 字段层 | 写入来源 |
| --- | --- |
| 第一层（交易事实） | 数据预处理 Agent 的标准化输出，所有路径共用。其中 `transaction_id` 由上游 ingestion layer 分配，不在 Transaction Log 内重算 |
| 第二层（分类结果） | 完成分类的节点 + build_je_lines.py + validate_je |
| 第三层（决策依据） | 完成分类的节点各自填入对应字段 |
| 第四层（补充证据） | 数据预处理 Agent（receipt / cheque_info），Coordinator Agent（supplementary_context） |
| 第五层（元数据） | 系统自动生成 |

### 不写入 Transaction Log 的情况

- PENDING 状态尚未被 accountant 确认的交易（没有最终分类结果）

---

## 4. 状态与生命周期

**Transaction Log 记录没有状态流转。一旦写入，记录永久保留。**

```
交易完成分类 + JE 生成
  → 写入 Transaction Log（一次写入）

审核阶段 accountant 修正分类：
  → 更新第二层：account / hst / je_lines 为修正后的值
  → 更新第三层：classified_by 改为 accountant_confirmed，填入 accountant_id 和 confirmed_info，清空不再适用的字段（rule_id / ai_reasoning / policy_trace 等）
  → 修正详情（改前→改后、原因）记录在 Intervention Log

交易被拆分：
  → 原始交易记录更新 child_transaction_ids
  → 为每个子交易创建独立的 Transaction Log 记录，parent_transaction_id 指向原始交易

保留期限：
  → 最低 7 年（加拿大 engagement documentation 保留要求）
  → 7 年后可按 processing_date 归档或清理
```

---

## 5. 被谁读取

| 读取者 | 时机 | 目的 |
| --- | --- | --- |
| 审核 Agent | 审核阶段 accountant 质疑某条 rule 或某笔交易时 | 按 rule_id 查询该 rule 匹配过的所有交易；按 transaction_id 查看单笔交易的完整信息 |
| 审核 Agent | 审核阶段 accountant 要求按科目或 vendor 查询时 | 优先按 account / description / period 查询；对 `description = null` 的交易需支持回退按 `raw_description` 查询 |
| Accountant（通过审核 Agent） | Year-end 结账、CRA 审计应对、客户询问 | 从报表数字追溯到具体交易，从交易追溯到原始凭证和分类依据 |

**Transaction Log 不被主 Workflow 的任何判断节点读取。** Node 1-4 和置信度分类器在处理交易时不查询 Transaction Log。Transaction Log 是纯输出端，不参与分类决策。

---

## 6. 被谁修改

### 主 Workflow 各节点（写入）

| 操作 | 触发条件 |
| --- | --- |
| 新增记录 | 交易完成分类并生成 JE |

### 审核 Agent（更新）

| 操作 | 触发条件 |
| --- | --- |
| 更新第二层（account / hst / je_lines）+ 第三层（classified_by 改为 accountant_confirmed、填入 accountant_id 和 confirmed_info、清空原 rule_id / ai_reasoning / policy_trace 等不再适用的字段） | Accountant 在审核阶段修正了交易分类 |
| 更新 child_transaction_ids | 交易被拆分 |
| 新增子交易记录 | 拆分交易时为每个子交易创建记录 |


---

## 7. 与其他组件的关系

### 上游（数据来源）

| 组件 | 关系 |
| --- | --- |
| 数据预处理 Agent | 提供第一层（交易事实）和第四层（receipt / cheque_info）的数据 |
| Node 1（Profile 匹配） | 提供 classified_by = profile_match 及 profile_match_detail |
| Node 2（Rules 匹配） | 提供 classified_by = rule_match 及 rule_id |
| 置信度分类器 | 提供 classified_by = ai_high_confidence 及 ai_reasoning、policy_trace |
| Coordinator Agent | 提供 classified_by = accountant_confirmed 及 accountant_id、confirmed_info |
| build_je_lines.py + validate_je | 提供 je_lines |

### 消费者（谁读取 Transaction Log）

| 组件 | 关系 |
| --- | --- |
| 审核 Agent | 按 rule_id / account / description / raw_description / period / transaction_id 查询交易明细 |

### 与 Intervention Log 的关系

| 关系 | 说明 |
| --- | --- |
| 关联方式 | 通过 transaction_id 关联。Intervention Log 中每条干预记录包含 affected_transaction_ids 字段 |
| 职责划分 | Transaction Log 存储交易的最终状态和首次分类依据；Intervention Log 存储每次人工干预的变更详情（改前→改后、原因、操作人） |
| 查询方向 | 从 Transaction Log 出发：需要了解某笔交易是否被修改过时，用 transaction_id 去 Intervention Log 查询。从 Intervention Log 出发：需要了解被干预交易的完整信息时，用 affected_transaction_ids 去 Transaction Log 查询 |

### 与 Observations 的关系

| 关系 | 说明 |
| --- | --- |
| 粒度区别 | Transaction Log 存储单笔交易级别的明细记录；Observations 存储 pattern 级别的聚合统计 |
| 职责不重叠 | Transaction Log 回答"这笔交易为什么这么分"；Observations 回答"这个 pattern 历史上被怎么分" |
| 无读写依赖 | Transaction Log 和 Observations 之间没有直接的读写关系，各自独立由不同节点写入 |

### 与 Rules 的关系

| 关系 | 说明 |
| --- | --- |
| 通过 rule_id 关联 | Transaction Log 中 classified_by = rule_match 的记录包含 rule_id，可追溯到 rules.md 中的具体规则 |
| 反向查询 | 审核 Agent 可通过 rule_id 在 Transaction Log 中查询该 rule 匹配过的所有交易 |
