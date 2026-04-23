# 审核 Agent

---

## 1. 职责定义

在 accountant 审核 `report_draft` 时介入，接收 accountant 的自然语言修改指令，执行修改，并触发系统的长期学习更新。

审核 Agent 解决的核心问题是：**系统分类了但分错了。** 它处理的是已经完成分类、生成了 JE、出现在 `report_draft` 中的交易——系统当时认为是对的，但 accountant 在审核时发现了问题。

**审核 Agent 同时承担规则管理职责。** 除了修正当期交易，审核 Agent 还负责处理 observations 的升级审批、rules 的手动创建和删除、observations 的状态标记管理。这些操作都发生在 accountant 审核阶段，是审核工作的自然延伸。

**审核 Agent 是一个 Agent，不是代码 Pipeline。** 核心工作是与 accountant 交互，accountant 的修改指令可能是模糊的、批量的、附带额外意图的。例如 accountant 可能说"把所有 Rogers 的都改掉，以后这个 pattern 每次都问我"，一句话里同时包含修改当期 JE、删除 rule、在 observation 上标记 force_review 三个操作。

---

## 2. 触发条件

主 Workflow 生成 `report_draft` 后，accountant 开始审核时启动。

审核 Agent 处理的交易来自 `report_draft` 的所有 Section：

| Section | 来源 | 为什么会出现在审核阶段 |
| --- | --- | --- |
| Section A（CERTAIN） | Node 2 Rules 匹配 | Rule 本身可能有问题，或这笔交易是 rule 无法覆盖的例外 |
| Section B（PROBABLE） | Node 3 置信度分类器高置信度判断 | AI 判断可能有误 |
| Section C（CONFIRMED） | Coordinator Agent 阶段 accountant 确认 | Accountant 之前确认时可能犯错或改变想法 |

此外，审核 Agent 在审核阶段还处理以下非交易类任务：

- **Profile 变更处理**（处理 Coordinator 阶段记录的 profile_change_requests，验证后写入 profile.md）
- Observations 升级审批（满足升级条件的 observations 进入待升级队列）
- Rules 的手动创建和删除
- Observations 的 force_review / accountant_notes 标记管理

---

## 3. 输入

### report_draft

当前批次的 `report_draft`，包含所有交易的分类结果、JE、置信度标签、判断来源。它是供审核使用的草稿视图，不等于审核完成后的最终 `.xlsx` 导出。

### 客户文件

| 文件 | 用途 |
| --- | --- |
| Profile.md | 了解客户结构，辅助理解 accountant 的修改意图 |
| Rules.md | 查看被质疑的 rule 的详情（pattern, account, hst, match_count, rule_id, source） |
| Observations.md | 查看被质疑的 pattern 的历史分类记录（classification_history, accountant_notes） |
| COA.csv | 验证 accountant 指定的科目是否存在；在 accountant 给出模糊信息时辅助生成选项 |
| tax_reference.md | 了解 HST 规则，在 accountant 未指定 HST 处理方式时给出合理的默认建议 |
| Transaction Log | 通过 rule_id 或其他元数据查询历史交易明细 |

### 待升级队列

维护流程（代码脚本）扫描 observations 后生成的满足升级条件的候选列表。每条候选包含：

```yaml
{
    "pattern": "ROGERS WIRELESS",
    "count": 5,
    "months_seen": ["2024-03", "2024-04", "2024-05", "2024-06", "2024-07"],
    "classification_history": [
        {"account": "Telephone & Internet", "hst": "inclusive_13", "count": 5}
    ],
    "amount_range": [85.00, 92.00],
    "confirmed_by": "ai",
    "ai_summary": "该 pattern 连续 5 个月出现，金额稳定在 $85-92 之间，全部分类为 Telephone & Internet。Rogers Wireless 是加拿大主要电信运营商，分类结果与业务性质一致。建议升级为 rule。"
}
```

---

## 4. Agent Skill 结构

```
review/
  SKILL.md                          ← 元数据层 + 指令层

  scripts/                          ← 资源层 — Script
    process_profile_changes.py      ← 处理 Coordinator 阶段记录的 profile_change_requests
    update_profile.py               ← 更新 profile.md 中的指定字段
    modify_je.py                    ← 修改 report_draft 中指定交易的 JE
    build_je_lines.py               ← 根据交易数据 + 分类结果构造 je_lines（共用脚本，定义见 je_generator_spec.md §1.5）
    create_rule.py                  ← 创建新 rule
    modify_rule.py                  ← 修改 rule 的 account / hst
    delete_rule.py                  ← 删除 rule + 对应 observation 标记 non_promotable
    promote_observation.py          ← 将 observation 升级为 rule
    update_observation.py           ← 更新 observation 的字段和状态标记
    write_observation.py            ← 将分类结果写入 observations
    write_intervention_log.py       ← 写入 intervention_log
    update_transaction_log.py       ← 更新 Transaction Log 中已有交易的分类结果和决策依据
    query_transaction_log.py        ← 从 Transaction Log 中查询历史交易
    merge_patterns.py               ← 合并多个 pattern 为一个（含 rebuild observations）
    rename_pattern.py               ← 重命名 pattern（含 rebuild observations）
    split_pattern.py                ← 拆分 pattern 为多个（含 rebuild observations）

  references/                       ← 资源层 — Reference
    current_rules.md                ← 当前客户的 rules（查看 rule 详情时加载）
    current_observations.md         ← 当前客户的 observations（查看历史分类时加载）
    output_report.md                ← 当前批次的 report_draft（审核对象，不是最终 .xlsx）
    upgrade_queue.md                ← 待升级 observations 列表（处理升级审批时加载）
    client_profile.md               ← 当前客户的 profile
    pending_profile_changes.md      ← Coordinator 阶段记录的待处理 profile 变更请求
    coa.csv                         ← 科目表（验证科目 + 模糊场景下生成选项）
    tax_reference.md           ← 加拿大税务事实性参考
```

### SKILL.md 内容结构

```markdown
---
name: review
description: 在 accountant 审核 `report_draft` 时介入。处理交易分类修正、rule 管理（创建/修改/删除）、
observation 升级审批、observation 状态标记管理。当 accountant 审核当期账目并提出修改意见时使用此 Skill。
---

# 审核 Agent 指令

## 核心原则
- 所有分类修改的最终决定权在 accountant
- accountant 给出明确分类指令时，验证科目存在后直接执行
- accountant 给出模糊信息时，结合 COA 生成选项请 accountant 选择
- 不自行决定是否删除 rule，必须先询问 accountant
- 发现 rule 匹配的交易有问题时，主动查询同 rule 的历史交易供 accountant 审查
- 在解析 accountant 的任何修改指令时，识别是否涉及 rule / observation 的连锁变更

## Profile 变更处理
[审核开始前，先处理 Coordinator 阶段记录的 profile_change_requests]

## 交易修正流程
[按交易来源分类的处理流程]

## 规则管理流程
[创建/修改/删除 rule 的流程]

## 升级审批流程
[如何呈现待升级 observations 并处理 accountant 的审批决定]

## Script 调用说明
[每个 Script 的用途、输入参数、何时调用]
```

---

## 5. 执行流程

### 5.0 Profile 变更处理（审核流程开头执行）

审核 Agent 在开始交易审核之前，先检查是否有 Coordinator 阶段记录的待处理 profile_change_requests。

```
→ 调用 process_profile_changes.py 读取 pending_profile_changes
→ 如果无待处理请求 → 跳过，直接进入 5.1
→ 如果有待处理请求：
  → 向 accountant 展示每条变更请求的内容（字段、新值、来源交易、accountant 原始表述）
  → Accountant 确认 → 调用 update_profile.py 写入 profile.md
  → Accountant 拒绝或修正 → 按 accountant 指令处理
  → 处理完成后清除已处理的请求
→ 继续进入交易审核流程
```

**设计原因：** Profile 是影响 Node 1/2/3 路由的系统上下文。变更信号通常在 Coordinator 阶段（处理 PENDING 交易时）由 accountant 提供，但 profile 的实际写入权集中在审核 Agent，确保：（1）写入口单一，不会出现批次中途状态变化；（2）变更经过审核阶段再次确认；（3）在下一批次运行前生效。

---

### 5.1 交易修正的通用模式

无论交易来自哪个 Section，accountant 提出修改后，agent 的分类辅助行为遵循统一模式：

**情况 A：Accountant 给出明确的分类指令**

Accountant 直接指定了科目和/或 HST（如"改成 Subcontractor Expenses, exempt"，或从 agent 给出的选项中选择）。

```
→ Agent 验证 accountant 指定的科目是否存在于 COA.csv
  → 存在 → 调用 build_je_lines.py 构造 je_lines → validate_je 校验 → 调用 modify_je.py 更新 report_draft
  → 不存在 → 提示 accountant 科目不在 COA 中，请确认或指定其他科目
→ 调用 write_observation.py 写入分类结果（confirmed_by: accountant）
→ 后续处理 rule / observation 的连锁变更（见各场景具体步骤）
```

**情况 B：Accountant 给出模糊信息**

Accountant 提供了业务信息但未明确科目（如"这是新仓库的押金"）。

```
→ Agent 结合 COA.csv 和 tax_reference.md，生成 2-3 个选项
  例如："新仓库的押金"→ 可能是：
    A. Prepaid Rent (exempt) — 如果是预付租金
    B. Security Deposit (exempt) — 如果是可退还的押金
    C. Rent Expense (inclusive HST) — 如果是不可退还的首月租金
→ 请 accountant 选择
→ Accountant 选择后 → 走情况 A
```

**Agent 不自行做最终分类决定。** 情况 B 中 agent 生成选项是为了辅助 accountant 做决策，不是替 accountant 做决策。最终选哪个由 accountant 决定。

---

### 5.2 场景一：Accountant 发现 Rule 匹配的交易有问题（Section A）

```
Accountant 指出某笔 Section A 交易分类有误
  → Agent 查找该交易的判断来源 → 确认为 rule 匹配
  → Agent 加载该 rule 的详情（references: current_rules.md）
  → Agent 向 accountant 展示：pattern, account, hst, match_count, rule_id, source, created_date
  → Agent 询问 accountant："规则本身有问题，还是这笔是特殊情况？"
```

#### 路径 A：规则本身有问题

```
Step 1: 确定 rule 的处置方式（三选一，由 accountant 决定）

  方向 1 — 修改 rule：
    → Accountant 指定正确的 account / hst
    → 调用 modify_rule.py 修改 rule 的分类结果
    → Rule 继续使用，下次匹配时以新的分类结果生成 JE

  方向 2 — 删除 rule：
    → 调用 delete_rule.py 删除该 rule
    → 自动触发：对应 observation 标记 non_promotable: true
    → Agent 询问 accountant 是否需要在 observation 上留下判断理由
      → 是 → 调用 update_observation.py 写入 accountant_notes
    → Agent 询问 accountant 是否需要标记 force_review
      → 是 → 调用 update_observation.py 设置 force_review: true
    → 之后该 pattern 的交易由置信度分类器处理，
      参考 observation 中的 classification_history 和 accountant_notes

  方向 3 — 删除 rule 并确定标记 force_review：
    → 与方向 2 相同，但 force_review 确定设为 true
    → 之后该 pattern 的交易每次都走人工审核

Step 2: 修改当期交易的 JE
    → 按通用模式情况 A 或 B 处理
    → 调用 update_transaction_log.py 更新 Transaction Log（第二层：account/hst/je_lines + 第三层：classified_by 改为 accountant_confirmed，填入 accountant_id 和 confirmed_info，清空原 rule_id）

Step 3: 排查同 rule 的其他交易
    → 调用 query_transaction_log.py，用 rule_id 查询当期所有被该 rule 匹配的交易
    → 展示给 accountant，按金额和日期排列
    → Accountant 决定处理方式：
      → "全部改成 X" → Agent 批量执行修改
      → "逐笔看" → Agent 逐笔展示，accountant 逐笔确认
      → "前几笔没问题，最后一笔也要改" → Agent 按指令执行

Step 4: 记录
    → 调用 write_intervention_log.py
    → intervention_type: "rule_error"
    → 记录：交易信息、原始分类、修改后分类、accountant 判断理由、对 rule 的处置方式
```

#### 路径 B：这笔是例外，规则没问题

```
Step 1: Rule 不做任何改动

Step 2: 修改当期交易的 JE
    → 按通用模式情况 A 或 B 处理
    → 调用 update_transaction_log.py 更新 Transaction Log（第二层和第三层更新为修正后的值）

Step 3: 不排查其他交易（因为 rule 本身没问题）

Step 4: 例外不写入 observation
    → 避免污染 classification_history 的分布数据
    → 该 pattern 在 observation 中的记录保持不变

Step 5: 记录
    → 调用 write_intervention_log.py
    → intervention_type: "exception"
```

---

### 5.3 场景二：Accountant 发现 AI 高置信度判断的交易有问题（Section B）

```
Accountant 指出某笔 Section B 交易分类有误
  → Agent 查找该交易的判断来源 → 确认为 AI 高置信度判断
  → Agent 必要时按 transaction_id 从 Transaction Log 读取该笔的 ai_reasoning / policy_trace
  → Agent 理解当时触发了哪些 risk packs、哪些 override evidence 让系统放行
  → Agent 加载该 pattern 的 observation 记录（references: current_observations.md）
  → Agent 向 accountant 展示 classification_history
  → Agent 询问："之前的分类记录是否也需要更改？"
```

#### 之前的也需要更改

```
Step 1: 修改当期交易 JE → 按通用模式情况 A 或 B 处理
    → 调用 update_transaction_log.py 更新 Transaction Log（第二层和第三层更新为修正后的值）

Step 2: 修正 observation
    → 调用 update_observation.py 修正 classification_history

Step 3: 排查同 pattern 的其他交易
    → 调用 query_transaction_log.py 查询当期同 pattern 交易
    → 展示给 accountant，支持批量修改或逐笔确认
    → 每笔被修改的交易同步调用 update_transaction_log.py

Step 4: 记录
    → 调用 write_intervention_log.py
    → intervention_type: "classification_error"
```

#### 之前的没问题，这笔是例外

```
Step 1: 修改当期交易 JE → 按通用模式处理
    → 调用 update_transaction_log.py 更新 Transaction Log

Step 2: 例外不写入 observation（避免污染 classification_history）

Step 3: 记录
    → intervention_type: "exception"
```

#### 之前的没问题，但之后需要特殊处理

```
Step 1: 修改当期交易 JE → 按通用模式处理
    → 调用 update_transaction_log.py 更新 Transaction Log

Step 2: 例外不写入 observation

Step 3: 按 accountant 指令设置 observation 标记
    → force_review: true（如 accountant 要求）
    → accountant_notes（如 accountant 要求留下说明）
    → 调用 update_observation.py

Step 4: 记录
    → intervention_type: "classification_error"
```

---

### 5.4 场景三：Accountant 发现 Coordinator 阶段确认的交易有问题（Section C）

```
处理逻辑与场景二完全相同。
唯一区别：intervention_log 中 original_source 记录为 "accountant_confirmed_via_coordinator"。
```

---

### 5.5 场景四：Observations 升级审批

```
→ Agent 加载 upgrade_queue.md
→ 逐条或批量展示给 accountant，每条包含：
    - Pattern 名称
    - 出现次数和月份分布
    - 金额范围
    - classification_history
    - 每次的确认来源（vendor_library / ai / accountant）
    - AI 生成的升级建议摘要

→ Accountant 对每条做出决定：

  批准升级：
    → 调用 promote_observation.py
    → 写入 rules.md，source: "promoted_from_observation, approved_by_accountant, {date}"
    → Observation 记录保留

  拒绝 — 不可升级：
    → 调用 update_observation.py 标记 non_promotable: true

  拒绝 — 再观察：
    → 不做任何标记，下次满足条件时再次进入队列

→ Accountant 可以批量审批或逐条处理
```

---

### 5.6 场景五：Accountant 主动管理规则

#### 手动创建 rule

```
→ Agent 确认：pattern, account, hst, direction, amount_range（如需要）
→ 调用 create_rule.py
→ source: "manually_created_by_accountant, {date}"
```

#### 手动删除 rule

```
→ Agent 展示 rule 详情和 match_count
→ Accountant 确认删除
→ 调用 delete_rule.py（自动标记对应 observation 为 non_promotable）
→ Agent 询问是否需要 accountant_notes 和 force_review
```

#### 手动设置 observation 的 force_review

```
→ 调用 update_observation.py 设置 force_review: true
→ Agent 询问是否需要 accountant_notes
```

---

### 5.7 场景六：Accountant 请求 Pattern 变更

Accountant 在审核中发现 pattern 标准化有问题（如同一商户被拆成多个 pattern，或不同服务被合并为一个 pattern），可通过审核 Agent 发起 pattern 变更。

#### 合并 pattern

```
→ Accountant 指出多个 pattern 应为同一商户（如 ROGERS WIRELESS + ROGERS CABLE → ROGERS）
→ Agent 展示各 pattern 的 observation 记录和 Transaction Log 中的交易数
→ Accountant 确认合并
→ 调用 merge_patterns.py（自动完成：Pattern Dictionary 更新 → Transaction Log 更新 → observations rebuild → rules 更新）
→ 调用 write_intervention_log.py，actions_taken 记录合并操作详情
```

#### 重命名 pattern

```
→ Accountant 指出某 pattern 名称需要修正（如 AMZN MKTP → AMAZON）
→ 调用 rename_pattern.py
→ 调用 write_intervention_log.py
```

#### 拆分 pattern

```
→ Accountant 指出某 pattern 实际包含不同商户或服务
→ Agent 从 Pattern Dictionary 查询该 pattern 下的所有 cleaned_fragment
→ 展示给 accountant，请其指定每个 cleaned_fragment 的归属
→ 调用 split_pattern.py(source_pattern, split_mapping)
→ 调用 write_intervention_log.py
```

**所有 pattern 变更的下游处理均以 Transaction Log 为 source of truth 执行 rebuild。** 详细设计见 `tools/pattern_standardization_spec.md` 第 6 节。

---

## 6. Scripts 详细说明

### process_profile_changes.py

- **用途**：读取 Coordinator 阶段记录的待处理 profile_change_requests
- **输入**：client_id
- **输出**：待处理的变更请求列表（每条包含 field, new_value, effective_date, source_transaction, accountant_statement）
- **说明**：只读取，不执行写入。审核 Agent 展示给 accountant 确认后，调用 update_profile.py 执行实际写入

### update_profile.py

- **用途**：更新客户 profile.md 中的指定字段
- **输入**：client_id, field, value
- **输出**：更新成功/失败状态
- **说明**：Profile 的唯一运行期写入点（Onboarding Agent 创建初始版本除外）

### modify_je.py

- **用途**：修改 `report_draft` 中指定交易的 JE
- **输入**：transaction_id, new_je_data
- **输出**：更新后的 `report_draft`

### build_je_lines.py

- **用途**：根据交易数据 + 分类结果构造完整的 je_lines
- **输入**：transaction（amount, direction, bank_account）, classification（account, hst）, client_id
- **执行逻辑**：共用脚本，完整定义见 je_generator_spec.md §1.5。读取 Profile（bank_accounts, tax_config）和 COA（Type 列），确定性计算借贷方向、金额拆分、HST 科目选择
- **输出**：je_input（hst_type + je_lines），传给 validate_je 校验
- **说明**：纯确定性计算，不做会计判断。Account 和 hst 由 accountant 决定后传入

### create_rule.py

- **用途**：创建新 rule
- **输入**：pattern, direction, account, hst, amount_range（可选）
- **输出**：新 rule 数据，source 标记为 "manually_created_by_accountant, {date}"，match_count = 0

### modify_rule.py

- **用途**：修改 rule 的 account / hst
- **输入**：rule_id, new_account, new_hst
- **输出**：更新后的 rule 数据

### delete_rule.py

- **用途**：删除 rule 并联动更新 observation
- **输入**：rule_id
- **执行逻辑**：从 rules.md 删除该 rule → 在 observations.md 中标记对应 pattern 为 non_promotable: true
- **说明**：accountant_notes 和 force_review 由 agent 单独调用 update_observation.py，因为需要先询问 accountant

### promote_observation.py

- **用途**：将 observation 升级为 rule
- **输入**：observation_pattern
- **执行逻辑**：从 observations 取 classification_history 中唯一的分类结果 → 构建 rule → 写入 rules.md → observation 记录保留
- **输出**：新 rule 数据，source: "promoted_from_observation, approved_by_accountant, {date}"

### update_observation.py

- **用途**：更新 observation 的字段或状态标记
- **输入**：pattern, 要更新的字段和值
- **可更新的字段**：non_promotable, force_review, accountant_notes, classification_history

### write_observation.py

- **用途**：将交易分类结果写入 observations
- **输入**：pattern, account, hst, transaction_date
- **执行逻辑**：如 pattern 已存在 → 更新 count, months_seen, amount_range, classification_history；如不存在 → 创建新记录
- **说明**：confirmed_by 固定为 accountant（审核阶段所有分类都经过 accountant 确认）

### update_transaction_log.py

- **用途**：更新 Transaction Log 中已有交易的分类结果和决策依据
- **输入**：transaction_id, 更新字段（account, hst, je_lines, classified_by, accountant_id, confirmed_info）
- **执行逻辑**：根据 transaction_id 找到记录，更新第二层（account/hst/je_lines）和第三层（classified_by 改为 accountant_confirmed，填入 accountant_id 和 confirmed_info，清空不再适用的原字段如 rule_id / ai_reasoning / policy_trace）
- **说明**：仅审核 Agent 调用。第一层（交易事实）和第四层（补充证据）不可修改

### write_intervention_log.py

- **用途**：记录 accountant 的每次审核干预，写入客户的 Intervention Log 数据库
- **输入**：transaction_ids（list）, accountant_id, reason, actions_taken, intervention_type（可选，exception / rule_error 时显式传入）
- **执行逻辑**：
  - intervention_id 由脚本自动生成（格式 `int_{YYYYMMDD}_{seq}`）
  - date 和 period 从 Transaction Log 中根据 transaction_ids[0] 获取
  - intervention_type 未传入时，脚本从 Transaction Log 读取修正前后分类，自动判断：account 不同 → classification_error，account 相同但 hst 不同 → hst_correction
- **完整字段定义**：见第 7 节

### query_transaction_log.py

- **用途**：从 Transaction Log 中查询历史交易，必要时读取 AI 高置信度记录里的 `ai_reasoning` / `policy_trace`
- **输入**：查询条件（rule_id / pattern / 时间范围 / 金额范围 等）
- **输出**：匹配的交易列表（含完整处理记录）
- **说明**：替代之前从 `report_draft` 中扫描的方式，支持跨期查询

### merge_patterns.py

- **用途**：将多个 pattern 合并为一个
- **输入**：source_patterns（list）, target_pattern
- **执行逻辑**：
  1. 更新 Pattern Dictionary：将所有 source_patterns 对应的条目的 canonical_pattern 改为 target_pattern
  2. 更新 Transaction Log：将 description 为 source_patterns 的交易记录改为 target_pattern
  3. 删除受影响的 observation 记录
  4. 从 Transaction Log rebuild observations（按 description + direction 重新聚合）
  5. 更新 Rules 中引用旧 pattern 的 rule（合并为 target_pattern 的 rule，或删除重复）
- **说明**：rebuild 复用已有的 observation 聚合逻辑，以 Transaction Log 为 source of truth

### rename_pattern.py

- **用途**：重命名一个 pattern
- **输入**：old_pattern, new_pattern
- **执行逻辑**：与 merge_patterns.py 相同的 5 步流程（本质是单源合并）
- **说明**：rename 是 merge 的特例，可复用同一底层逻辑

### split_pattern.py

- **用途**：将一个 pattern 拆分为多个
- **输入**：source_pattern, split_mapping（dict，cleaned_fragment → new_pattern）
- **执行逻辑**：
  1. 更新 Pattern Dictionary：按 split_mapping 修改各条目的 canonical_pattern
  2. 更新 Transaction Log：按 cleaned_fragment 匹配，将 description 改为对应的 new_pattern
  3. 删除受影响的 observation 记录
  4. 从 Transaction Log rebuild observations
  5. 创建/更新对应的 Rules
- **说明**：拆分需要 accountant 指定哪些 cleaned_fragment 归属哪个新 pattern

---

## 7. Intervention Log

### 7.1 定位

Intervention Log 记录 accountant 在审核阶段对系统分类结果的每次人工干预。

**核心职责：** 只记录 Transaction Log 里没有的信息——accountant 为什么做人工介入，过程中对 rule/observation 做了什么连锁操作。交易本身的详情（pattern、原始分类、修正后分类、original_source 等）通过 `transaction_ids` 关联 Transaction Log 查询。一次干预事件可能影响多笔交易（如批量修正同 rule/同 pattern 的交易），因此 Intervention Log 的分析单位是"干预事件"，不是"交易"。

**读取者：** 产品负责人及未来可能的其他角色（合伙人、高级 accountant）。

**与 Observations 的区别：**

- Observations 记录"分类事实"，用于升级 rules 和提供 AI 层参考
- Intervention Log 记录"人为什么要改"，用于改进系统

**写入节点：** 只有审核 Agent。只有审核阶段 accountant 的人工介入才写入 Intervention Log。

**长期价值：**

- 发现某类交易需要行业特定规则 → 创建对应的 industry reference 文件
- 发现某条 rule 的出错率高 → 审视 observation 升级条件是否需要调整
- 统计各类 intervention_type 的分布 → 了解系统薄弱环节

---

### 7.2 存储

数据库（SQLite），支持按 intervention_type / period / pattern 聚合查询。每客户独立数据库文件。

---

### 7.3 字段定义

| 字段 | 类型 | 说明 |
|------|------|------|
| `intervention_id` | string | 唯一标识，系统生成，格式 `int_{YYYYMMDD}_{seq}` |
| `transaction_ids` | list | 本次干预影响的所有交易 ID 列表。交易详情（pattern、原始/修正后分类、original_source 等）通过这些 ID 查询 Transaction Log 获取 |
| `intervention_type` | enum | 见 7.4 节 |
| `date` | string | 干预发生日期，`YYYY-MM-DD` |
| `period` | string | 交易所属处理期间，`YYYY-MM` |
| `accountant_id` | string | 做出决定的 accountant |
| `reason` | string | 为什么做人工介入（accountant 的判断理由，自然语言）。Transaction Log 不记录这个 |
| `actions_taken` | string | 连锁操作摘要——对 rule / observation 做了什么（如"删除 rule_012，observation 标记 non_promotable + force_review"）。Transaction Log 也不记录这个 |

---

### 7.4 intervention_type 取值与判断规则

| 类型 | 含义 | 判断方式 |
|------|------|----------|
| `rule_error` | Rule 匹配的交易被修正，且 accountant 判定 rule 本身有问题 | 审核 Agent 根据 accountant 判断传入 |
| `classification_error` | 系统分类被修正，科目发生变化 | 自动判断：修正前后 account 不同 |
| `hst_correction` | 系统分类被修正，科目不变但 HST 处理变化 | 自动判断：修正前后 account 相同、hst 不同 |
| `exception` | 这笔交易是例外，系统对该 pattern 的分类逻辑没问题 | 审核 Agent 根据 accountant 判断传入 |
| `accrual_adjustment` | 会计调整（预留） | 待设计 |

**自动判断逻辑：** `write_intervention_log.py` 从 Transaction Log 读取修正前后的分类结果，比较 account 和 hst 字段差异，自动区分 classification_error 和 hst_correction。exception 和 rule_error 由审核 Agent 显式传入。

---

### 7.5 写入逻辑

写入时机对应第 5 节各场景的最后一步，由 `write_intervention_log.py` 执行。审核 Agent 传入 transaction_id、accountant_id、reason、actions_taken，以及 intervention_type（exception / rule_error 时显式传入，其他情况由脚本自动判断）。

---

### 7.6 读取逻辑

通过数据库查询，支持的聚合维度：

- 按 `intervention_type` 统计分布
- 按 `period` 观察趋势
- 按 `transaction_id` join Transaction Log 获取交易详情（pattern、分类来源、修正前后分类等）
- 按客户按月 review：查询指定 period 的所有记录

---

## 8. 权限边界

### 允许

- ✅ 读取 profile.md, rules.md, observations.md, COA.csv, tax_reference.md, `report_draft`, Transaction Log, pending_profile_changes
- ✅ 更新 profile.md（处理 Coordinator 阶段记录的 profile_change_requests，经 accountant 确认后写入）
- ✅ 修改 `report_draft` 中的 JE（基于 accountant 指令）
- ✅ 调用 build_je_lines.py 构造 je_lines + validate_je 校验（account + hst 由 accountant 决定）
- ✅ 在 accountant 给出模糊信息时，结合 COA 生成选项请 accountant 选择
- ✅ 创建新 rule（基于 accountant 指令）
- ✅ 修改 rule 的 account / hst（基于 accountant 指令）
- ✅ 删除 rule（基于 accountant 指令）
- ✅ 升级 observation 为 rule（基于 accountant 批准）
- ✅ 更新 observation 的 non_promotable / force_review / accountant_notes / classification_history
- ✅ 将分类结果写入 observations（confirmed_by: accountant）
- ✅ 写入 intervention_log
- ✅ 查询 Transaction Log 中的历史交易
- ✅ 更新 Transaction Log 中已有交易的分类结果和决策依据（基于 accountant 修正指令）
- ✅ 支持 accountant 的批量修改指令
- ✅ 与 accountant 多轮对话
- ✅ 管理 Pattern Dictionary：合并/重命名/拆分 pattern（基于 accountant 指令），含自动 rebuild observations

### 不允许

- ❌ 自己做最终分类决定——明确指令时直接执行，模糊信息时生成选项请 accountant 选择，但最终决定权在 accountant
- ❌ 自己决定是否删除 rule——必须询问 accountant
- ❌ 自己决定 observation 的 force_review / accountant_notes 内容——必须来自 accountant
- ❌ 修改 workflow 逻辑
- ❌ 自行发起 profile 变更——只处理 Coordinator 阶段记录的 profile_change_requests，或在审核对话中 accountant 主动提出的变更

---

## 9. 与人的交互

| 交互对象 | 交互内容 | 交互时机 |
| --- | --- | --- |
| Accountant | 接收交易修改指令 | 审核 `report_draft` 时 |
| Accountant | 展示 rule 详情并询问处置方向 | 发现 rule 匹配的交易有问题时 |
| Accountant | 查询并展示同 rule / 同 pattern 的历史交易 | Rule 被判定有问题时 |
| Accountant | 展示 observation 历史并询问是否需要更改 | 发现 AI 判断的交易有问题时 |
| Accountant | 在 accountant 给出模糊信息时生成选项供选择 | Accountant 未明确指定科目时 |
| Accountant | 展示待升级 observations 并接收审批决定 | 审核阶段末尾 |
| Accountant | 接收手动创建/删除 rule 的指令 | Accountant 主动要求时 |
| Accountant | 追问模糊的修改指令 | 无法明确解析意图时 |

**交互原则：**

- 每次修改操作前，Agent 向 accountant 确认操作内容和影响范围
- 涉及 rule 变更时，展示 match_count 让 accountant 了解使用频率
- 涉及 observation 标记变更时，说明对未来交易处理的影响
- 批量操作时，列出所有受影响的交易让 accountant 批量确认或逐笔确认
- 所有通过审核 Agent 完成的分类修正，confirmed_by 记录为 accountant

---

## 10. 与其他组件的关系

### 上游（数据来源）

| 组件 | 关系 |
| --- | --- |
| Node 6（输出报告） | 产出 `report_draft` 供审核 Agent 审核；审核完成后才可进一步导出最终 `.xlsx` |
| 维护流程（代码） | 提供待升级 observations 列表 |
| Transaction Log | 提供历史交易查询能力 |
| Accountant | 提供修改指令和审批决定 |

### 可读取的文件

| 文件 | 用途 |
| --- | --- |
| Profile.md | 了解客户结构 |
| Rules.md | 查看 rule 详情 |
| Observations.md | 查看 pattern 历史分类记录 |
| COA.csv | 验证科目 + 模糊场景下生成选项 |
| tax_reference.md | 加拿大税务事实性参考 |
| `report_draft` | 审核对象 |
| Transaction Log | 查询历史交易明细 |

### 可修改的文件

| 文件 | 操作 |
| --- | --- |
| Rules.md | 创建 / 修改 / 删除 rule |
| Observations.md | 标记 non_promotable / force_review / 写入 accountant_notes / 修正 classification_history / 写入新分类结果 |
| Transaction Log | 更新已有交易的分类结果和决策依据（第二层 + 第三层） |
| Intervention_log.md | 追加干预记录 |
| Pattern Dictionary | 合并/重命名/拆分 pattern（基于 accountant 指令） |
| `report_draft` | 修改 JE |

### 不直接交互

| 组件 | 关系 |
| --- | --- |
| 置信度分类器（Node 3） | 审核 Agent 不调用置信度分类器。JE 构造由 build_je_lines.py 完成 |
| Coordinator Agent | 两者不同时工作，审核 Agent 在 Coordinator 之后运行 |
| 数据预处理 Agent | 审核 Agent 不参与文件预处理 |
| Profile.md（写入） | 审核 Agent 不修改 profile |
