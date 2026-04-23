# Coordinator Agent

---

## 1. 职责定义

接收置信度分类器产出的所有 PENDING 交易，整理并呈现给 accountant，解析 accountant 的非结构化回复，将回复转化为系统可执行的操作，推动 PENDING 交易完成分类。

Coordinator Agent 解决的核心问题是：**系统不知道怎么分类。** 它是置信度分类器和 accountant 之间的桥梁——将系统的结构化疑问翻译成人能读懂的问题，将人的自然语言回复翻译成系统能执行的操作。

**Coordinator Agent 不做最终分类决定，但辅助 accountant 完成分类。** 当 accountant 给出明确的分类指令时，agent 验证科目后直接执行。当 accountant 给出模糊信息时，agent 结合 COA 生成选项请 accountant 选择。所有分类的最终决定权在 accountant 手里。

**Coordinator Agent 是一个 Agent，不是代码 Pipeline。** 核心工作是与人交互，而人的回复方式完全不可控：可能只回复部分交易、可能在回复中夹带无关信息（如客户结构变更）、可能引用之前的对话上下文、可能分多次回复。这些不确定性需要 LLM 的语义理解能力来处理。

---

## 2. 触发条件

置信度分类器处理完当前批次的所有交易后，如果存在 PENDING 交易，自动触发 Coordinator Agent。

如果当前批次没有 PENDING 交易，Coordinator Agent 不启动，主 Workflow 直接进入输出报告阶段。

---

## 3. 输入

### 来自置信度分类器的 PENDING 交易

每笔 PENDING 交易包含：

```yaml
{
    # 原始交易数据
    "date": "2024-07-15",
    "description": "HOME DEPOT",
    "pattern_source": "dictionary_hit",
    "amount": 2000.00,
    "direction": "debit",
    "raw_description": "HOME DEPOT 4521 TORONTO ON",
    "bank_account": "TD-5027013",
    "currency": "CAD",
    "supplementary_context": "",
    "receipt": null,
    "cheque_info": null,   # 支票交易时为 {"cheque_number": "00456", "payee": "John Smith Contracting", "memo": "Progress payment - Kitchen reno", "match_method": "cheque_number"}
    "bs_source": "TD_Chequing_Jul_2024.pdf",

    # 置信度分类器的输出
    "classifier_output": {
        "confidence": "pending",
        "options": [
            {"account": "Supplies & Materials", "hst": "inclusive_13", "reason": "建筑公司常见施工材料采购"},
            {"account": "Shareholder Loan", "hst": "exempt", "reason": "客户有个人消费记录，金额偏高"}
        ],
        "observation_context": "历史上 3 次 Supplies & Materials",
        "accountant_notes": "",
        "description_analysis": "",
        "suggested_questions": [],
        "policy_trace": {
            "activated_packs": ["retail_personal_use_risk"],
            "blocking_packs": [],
            "override_evidence": [],
            "unresolved_risks": ["retail_personal_use_risk"]
        }
    }
}
```

`policy_trace` 是 Coordinator 的正式输入之一，用来理解这笔交易为什么停在 PENDING。

- Coordinator 可以用它决定提问重点，例如优先追问结构性 profile 冲突还是业务用途
- Coordinator 不需要把 pack 名称原样展示给 accountant，而是应转译成 accountant 可读的问题和解释

### 客户文件

| 文件 | 用途 |
| --- | --- |
| Profile.md | 了解客户背景，辅助理解 accountant 回复中的隐含信息 |
| COA.csv | 验证 accountant 指定的科目是否存在；在 accountant 给出模糊信息时辅助生成选项 |
| tax_reference.md | 了解加拿大税务事实性规则（exempt/zero-rated 类别、ITC 限制等），在 accountant 未指定 HST 处理方式时给出合理的默认建议 |

---

## 4. Agent Skill 结构

```
coordinator/
  SKILL.md                          ← 元数据层 + 指令层

  scripts/                          ← 资源层 — Script
    collect_pending.py              ← 收集并归组 PENDING 交易
    record_profile_change_request.py ← 记录待审核的 profile_change_request
    inject_context.py               ← 向交易写入 supplementary_context
    split_transaction.py            ← 拆分交易为多条标准格式
    retrigger_workflow.py           ← 触发指定交易重新进入 workflow
    build_je_lines.py               ← 根据交易数据 + 分类结果构造 je_lines（共用脚本，定义见 je_generator_spec.md §1.5）
    write_observation.py            ← 将分类结果写入 observations
    write_transaction_log.py        ← 将完成分类的交易写入 Transaction Log

  references/                       ← 资源层 — Reference
    pending_list.md                 ← 当前批次的 PENDING 交易清单（动态生成）
    client_profile.md               ← 当前客户的 profile
    coa.csv                         ← 科目表（验证科目 + 模糊场景下生成选项）
    tax_reference.md                ← 加拿大税务事实性参考
```

### SKILL.md 内容结构

```markdown
---
name: coordinator
description: 处理置信度分类器产出的 PENDING 交易。整理 PENDING 交易发送给 accountant，
解析 accountant 的非结构化回复，转化为系统操作，推动交易完成分类。
当有 PENDING 交易需要与 accountant 沟通时使用此 Skill。
---

# Coordinator Agent 指令

## 核心原则
- 所有分类的最终决定权在 accountant
- accountant 给出明确分类指令时，验证科目存在后直接生成 JE
- accountant 给出模糊信息时，结合 COA 生成选项请 accountant 选择
- 同 pattern 的交易归组展示，但明确列出每笔的金额和日期，不默认它们是同一业务目的
- 带选项的 PENDING 优先展示（accountant 可快速处理），不带选项的排在后面
- accountant 的回复可能是部分的、分次的、包含额外信息的，都要正确处理
- 在解析 accountant 的任何回复时，始终检查是否包含客户结构信息变更的信号
- 遇到无法解析的回复要追问，不猜测

## 消息组织规则
[如何将 PENDING 交易整理成 accountant 可读的消息]

## 回复解析规则
[如何将 accountant 的自然语言回复转化为操作]

## Script 调用说明
[每个 Script 的用途、输入参数、何时调用]
```

---

## 5. 执行流程

### Step 1：收集并组织 PENDING 交易

```
→ 调用 collect_pending.py 收集所有 PENDING 交易
→ 按 description 的标准化 pattern 归组
→ 在每组内按金额排序展示
→ 将"带选项"的 PENDING 和"不带选项"的 PENDING 分开排列
```

### Step 2：生成消息发送给 accountant

Agent 将归组后的 PENDING 交易生成可读消息。

**带选项的 PENDING（accountant 可快速处理）：**

```
本月有 4 笔 HOME DEPOT 交易需要确认分类：
  1. 07/03  $45.00   debit
  2. 07/11  $80.00   debit
  3. 07/18  $95.00   debit
  4. 07/25  $2,000.00  debit

系统参考：历史上 3 次分类为 Supplies & Materials。
系统建议：
  A. Supplies & Materials (inclusive HST) — 建筑公司常见施工材料采购
  B. Shareholder Loan (exempt) — 客户有个人消费记录，第 4 笔金额偏高

请确认每笔交易的分类。可以统一回复（如"前三笔选 A，第四笔选 B"），也可以逐笔说明。

---

07/20  CHQ#00456  $3,500.00  debit
   支票信息 — 收款人：John Smith Contracting，备注：Progress payment - Kitchen reno
系统建议：
  A. Subcontractor Expenses (inclusive HST) — 付款对象为承包商，备注为工程进度款
  B. Construction Labour (inclusive HST) — 如为直接劳务费用

请确认分类。
```

**不带选项的 PENDING（需要 accountant 提供信息）：**

```
以下交易系统无法判断，需要您提供信息：

1. 07/05  EMT E-TFR  $2,500.00  debit
   → 无法从描述判断业务目的。请问这笔转账是付给谁的？用途是什么？
```

### Step 3：等待并接收 accountant 回复

Agent 等待 accountant 回复。这是异步过程，可能需要数小时甚至数天。

**需要处理的回复类型：**

| 回复类型 | 示例 | Agent 行为 |
| --- | --- | --- |
| 直接选择选项 | "前三笔选 A，第四笔选 B" | 明确的分类指令 → 走情况 A |
| 提供明确科目 | "那笔 EMT 是 Subcontractor Expenses, exempt" | 明确的分类指令 → 走情况 A |
| 提供业务信息但未指定科目 | "EMT 那笔是付给分包商的工程款" | 模糊信息 → 走情况 B |
| 部分回复 | "HOME DEPOT 的都是材料费，其他的我要问客户" | 处理已回复部分，其余继续等待 |
| 附带 profile 变更信息 | "对了这个客户上个月开始雇人了" | 记录 profile_change_request + 处理分类回复 |
| 引用上下文 | "这几笔和上个月那个一样处理" | 查阅上下文理解含义，无法确定则追问 |
| 模糊回复 | "应该是办公用品吧" | 追问确认 |
| 要求拆分 | "这笔 $5000 其中 $3000 是材料，$2000 是老板自己买的" | 调用 split_transaction.py 拆分 |
| 提供信息但未直接分类 | "这是我们新租的仓库的押金" | 模糊信息 → 走情况 B |

### Step 4：解析回复并执行操作

#### 情况 A：Accountant 给出明确的分类指令

Accountant 直接指定了科目和/或 HST（从选项中选择，或直接说明科目名称）。

```
→ Agent 验证 accountant 指定的科目是否存在于 COA.csv
  → 存在 → 调用 build_je_lines.py 构造 je_lines → 调用 validate_je 校验
  → 不存在 → 提示 accountant 科目不在 COA 中，请确认或指定其他科目
→ 调用 write_observation.py 写入分类结果（confirmed_by: accountant）
→ 调用 write_transaction_log.py 写入 Transaction Log（classified_by: accountant_confirmed，accountant_id，confirmed_info）
→ 交易完成分类，进入输出报告
```

#### 情况 B：Accountant 给出模糊信息

Accountant 提供了业务信息但未明确科目。

```
→ Agent 结合 COA.csv 和 tax_reference.md 生成 2-3 个选项
  例如："新仓库的押金" →
    A. Prepaid Rent (exempt) — 如果是预付租金
    B. Security Deposit (exempt) — 如果是可退还的押金
    C. Rent Expense (inclusive HST) — 如果是不可退还的首月租金
→ 请 accountant 选择
→ Accountant 选择后 → 走情况 A
```

#### 操作：捕获 profile 变更信号

Accountant 的回复中包含客户结构信息变更的信号。

**Coordinator Agent 不直接修改 profile.md。** 它负责捕获信号并记录为结构化的 `profile_change_request`，由审核 Agent 在审核阶段统一处理写入。

```
→ 调用 record_profile_change_request.py
  写入一条结构化变更请求，包含：
    - field: 需要变更的 profile 字段
    - new_value: 新值
    - effective_date: 生效日期（如 accountant 提及）
    - source_transaction: 触发此信号的交易 ID
    - accountant_statement: accountant 的原始表述
→ 当前 PENDING 交易照常按 accountant 的分类指令处理（走情况 A / B）
→ 继续处理其他回复
```

**可能触发 profile 变更信号的场景：**

- 银行账户变更（新开/关闭账户）→ bank_accounts / account_relationships
- 员工状态变更 → has_employees
- 老板个人消费习惯变更 → owner_uses_company_account
- 贷款变更 → loans
- HST 注册状态变更 → has_hst_registration

Agent 不主动询问这些信息，但在解析任何回复时始终检查是否包含变更信号。

#### 操作：拆分交易

```
→ 调用 split_transaction.py
  约束：splits 金额之和必须等于原始交易金额
→ 每条子交易带着 accountant 提供的业务信息
→ 如果 accountant 已给出每条子交易的明确分类 → 每条走情况 A
→ 如果 accountant 只给出了金额拆分和模糊描述 → 每条走情况 B
→ 如果 accountant 只给出了金额拆分未说明用途 → 每条子交易调用 retrigger_workflow.py 从 Node 1 重新走 workflow
```

### Step 5：确认全部 PENDING 已解决

```
→ 检查是否所有 PENDING 交易都已处理
→ 如有未处理的 → 继续等待 accountant 回复，或主动提醒 accountant
→ 全部处理完成 → Coordinator Agent 工作结束
→ 主 Workflow 继续执行 → Node 6 生成完整输出报告
```

---

## 6. Scripts 详细说明

### collect_pending.py

- **用途**：收集当前批次所有 PENDING 交易，按 pattern 归组
- **输入**：当前批次交易数据
- **执行逻辑**：筛选 confidence = "pending" 的交易，按 description 标准化后归组，组内按金额排序
- **输出**：归组后的 PENDING 交易列表，区分"带选项"和"不带选项"

### record_profile_change_request.py

- **用途**：将 accountant 提供的 profile 变更信号记录为结构化请求，供审核 Agent 后续处理
- **输入**：client_id, field, new_value, effective_date（可选）, source_transaction, accountant_statement
- **输出**：写入成功/失败状态
- **说明**：不直接修改 profile.md。变更请求存储在 pending_profile_changes 中，审核 Agent 在审核流程开头统一处理

### inject_context.py

- **用途**：向指定交易的 supplementary_context 字段写入信息
- **输入**：transaction_id, context 文本
- **输出**：更新后的交易数据
- **说明**：仅在拆分交易后子交易需要重新走 workflow 时使用

### split_transaction.py

- **用途**：将一笔交易拆分为多条标准格式交易数据
- **输入**：original_transaction, splits（每条包含 amount 和 context）
- **执行逻辑**：验证 splits 金额之和 = 原始金额 → 生成多条标准格式交易数据
- **约束**：金额之和必须等于原始交易金额，不等则报错拒绝执行

### retrigger_workflow.py

- **用途**：触发指定交易重新进入主 Workflow
- **输入**：transaction_ids, start_node（从哪个节点开始）
- **start_node 选择**：
  - 拆分交易后 accountant 未给出分类 → Node 1
- **输出**：触发成功/失败状态

### build_je_lines.py

- **用途**：根据交易数据 + 分类结果构造完整的 je_lines
- **输入**：transaction（amount, direction, bank_account）, classification（account, hst）, client_id
- **执行逻辑**：共用脚本，完整定义见 je_generator_spec.md §1.5。读取 Profile（bank_accounts, tax_config）和 COA（Type 列），确定性计算借贷方向、金额拆分、HST 科目选择
- **输出**：je_input（hst_type + je_lines），传给 validate_je 校验
- **说明**：纯确定性计算，不做会计判断。Account 和 hst 由 accountant 决定后传入

### write_observation.py

- **用途**：将交易分类结果写入 observations
- **输入**：pattern, account, hst, transaction_date
- **执行逻辑**：如 pattern 已存在 → 更新 count, months_seen, amount_range, classification_history；如不存在 → 创建新记录
- **说明**：confirmed_by 固定为 accountant（Coordinator 阶段所有分类都经过 accountant 确认）

### write_transaction_log.py

- **用途**：将完成分类的交易写入 Transaction Log
- **输入**：transaction（完整交易数据）, je_lines, classified_by, accountant_id, confirmed_info
- **执行逻辑**：组装五层字段，写入 Transaction Log 数据库。第一层和第四层从 transaction 对象中提取，第二层从 je_lines 传入，第三层从 classified_by 等参数传入，第五层由脚本自动生成（processing_date, period）
- **说明**：与其他节点（Node 1/2、置信度分类器）共用同一个脚本，各节点传入不同的 classified_by 和对应字段

---

## 7. 权限边界

### 允许

- ✅ 读取 profile.md（了解客户背景）
- ✅ 读取 COA.csv（验证科目 + 模糊场景下生成选项）
- ✅ 读取 tax_reference.md（加拿大税务事实性参考）
- ✅ 记录 profile_change_request（当 accountant 提供客户结构信息变更时，记录结构化变更请求供审核 Agent 处理）
- ✅ 向交易注入 supplementary_context
- ✅ 拆分交易为多条标准格式
- ✅ 触发 workflow 重处理
- ✅ 调用 build_je_lines.py 构造 je_lines + validate_je 校验（account + hst 由 accountant 决定）
- ✅ 将分类结果写入 observations（confirmed_by: accountant）
- ✅ 将完成分类的交易写入 Transaction Log（classified_by: accountant_confirmed）
- ✅ 在 accountant 给出模糊信息时，结合 COA 生成选项请 accountant 选择
- ✅ 与 accountant 多轮对话（追问、澄清、确认）

### 不允许

- ❌ 自行做最终分类决定——明确指令时直接执行，模糊信息时生成选项请 accountant 选择，最终决定权在 accountant
- ❌ 直接修改 profile.md（只记录 profile_change_request，实际写入由审核 Agent 处理）
- ❌ 修改 rules.md（规则变更是审核 Agent 的职责）
- ❌ 修改 observations.md 的状态标记（non_promotable / force_review 是审核 Agent 的职责）
- ❌ 修改 workflow 逻辑
- ❌ 对 accountant 的模糊回复做猜测性解读（应追问确认）

---

## 8. 与人的交互

| 交互对象 | 交互内容 | 交互时机 |
| --- | --- | --- |
| Accountant | 发送整理后的 PENDING 交易清单 | 置信度分类完成后 |
| Accountant | 接收并解析 accountant 的回复 | Accountant 回复时 |
| Accountant | 在 accountant 给出模糊信息时生成选项供选择 | Accountant 未明确指定科目时 |
| Accountant | 追问模糊或不完整的回复 | 回复无法明确解析时 |
| Accountant | 提醒未处理的 PENDING 交易 | 长时间未收到回复时 |
| Accountant | 确认拆分交易的金额明细 | Accountant 要求拆分但未给出精确金额时 |

**交互原则：**

- Agent 不主动向客户交互，所有沟通通过 accountant
- 每次发送消息时，带选项的 PENDING 排在前面，不带选项的排在后面
- 同 pattern 的交易归组展示，但明确列出每笔明细，不假设它们分类相同
- Accountant 可以分多次回复，Agent 维护已处理/未处理状态
- 在解析任何回复时，始终检查是否包含客户结构信息变更的信号（捕获后记录 profile_change_request，不直接修改 profile）
- 所有通过 Coordinator Agent 完成的分类，confirmed_by 记录为 accountant

---

## 9. 与其他组件的关系

### 上游（数据来源）

| 组件 | 关系 |
| --- | --- |
| 置信度分类器（Node 3） | 提供所有 PENDING 交易及其分类器输出（含 `policy_trace`） |
| Profile.md | 提供客户背景信息 |
| COA.csv | 提供科目表用于验证和生成选项 |
| tax_reference.md | 提供加拿大税务事实性参考 |

### 下游（输出去向）

| 操作 | 下游组件 | 说明 |
| --- | --- | --- |
| Accountant 给出明确分类 | build_je_lines.py + validate_je | 构造并校验 JE，不经过置信度分类器 |
| Accountant 给出明确分类 | Node 5（写入 Observations，通过 write_observation.py） | 分类结果写入 observations，confirmed_by: accountant |
| Profile 变更信号记录 | pending_profile_changes | 结构化变更请求，审核 Agent 在审核阶段统一处理写入 profile |
| 拆分交易后 accountant 未给出分类 | Node 1（Profile 匹配） | 每条子交易从 Node 1 走完整 workflow |
| 所有 PENDING 解决后 | Node 6（输出报告） | 主 Workflow 继续生成完整输出报告 |

### 可修改的文件

| 文件 | 操作 | 触发条件 |
| --- | --- | --- |
| pending_profile_changes | 写入变更请求 | Accountant 在回复中提供客户结构信息变更（不直接修改 profile.md） |
| Observations.md | 写入分类结果 | Accountant 确认分类后通过 write_observation.py 写入 |
| Transaction Log | 写入交易记录 | Accountant 确认分类后通过 write_transaction_log.py 写入 |
| 交易数据 | 写入 supplementary_context | 拆分交易后子交易需要重新走 workflow 时 |
| 交易数据 | 拆分为多条 | Accountant 要求拆分 |
| 输出报告 | 新增已完成分类的交易和 JE | Accountant 确认分类后直接生成 JE 写入报告 |

### 不直接交互

| 组件 | 关系 |
| --- | --- |
| Rules.md | Coordinator Agent 不读取也不修改 |
| Observations.md 状态标记 | Coordinator Agent 不修改 non_promotable / force_review（这是审核 Agent 的职责） |
| Knowledge Base | Coordinator Agent 不读取行业规则等会计知识 |
| 审核 Agent | Coordinator Agent 完成后由主 Workflow 生成输出报告，之后才进入审核阶段 |
