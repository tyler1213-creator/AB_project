# 数据预处理 Agent

---

## 1. 职责定义

接收用户传入的所有原始财务文件（bank statement、小票、支票影像、其他附件），完成文件识别、分类、解析、配对，最终输出一套干净、结构化的交易数据集，交给主 Workflow 处理。

数据预处理 Agent 是整个系统的最上游入口。用户输入的文件来源多样（邮件、WhatsApp、Slack 等）、格式不统一、数量不确定、可能存在重复或缺失。Agent 通过 LLM 的推理能力处理不可控因素，将混乱的输入转化为标准化的输出。

**架构原则：Agent 负责决策，Script 负责执行，Reference 提供参考知识。** Agent 决定每个文件是什么、该调用什么工具处理、处理结果是否合理。确定性的解析、提取、配对操作封装为 Script（被执行但不被读取，零 token 消耗）。需要 Agent 参考的规范和格式定义封装为 Reference（条件触发时才加载）。

---

## 2. 触发条件

Accountant 或系统收到客户提交的一批财务文件后，手动或自动触发。每个客户每个处理周期运行一次。

---

## 3. 输入

### 必需输入

- **原始文件集合**：用户提交的所有文件（PDF、图片、Excel、CSV 等混合格式）
- **客户标识**：指明是哪个客户，用于加载该客户的 profile.md（获取银行账户列表等信息）

### 可选输入

- **任务说明**：accountant 提供的补充信息，如"这是 2024 年全年的 TD 账户 bank statement"。有则 Agent 用于做完整性校验，没有则 Agent 自行从文件内容中推断时间范围和账户范围

---

## 4. Agent Skill 结构

数据预处理 Agent 以 Claude Code 的 Agent Skill 标准组织，采用渐进式披露的三层架构：

```
data_preprocessing/
  SKILL.md                          ← 元数据层 + 指令层

  scripts/                          ← 资源层 — Script（被执行，不被读取，零 token 消耗）
    identify_pdf_type.py            ← 识别 PDF 文件类型（哪家银行的 BS / 小票 PDF / 其他）
    parse_td_bs.py                  ← 解析 Bank Statement PDF
    parse_excel_bs.py               ← 解析 Excel/CSV 格式的 BS
    extract_cheque_images.py        ← 从 BS PDF 中提取支票影像页
    match_receipts.py               ← 小票与交易数据配对
    generate_summary.py             ← 生成预处理摘要的结构化数据

  references/                       ← 资源层 — Reference（条件触发时才加载，消耗 token）
    output_schema.md                ← 标准交易数据输出格式定义
    supported_banks.md              ← 已支持银行列表及其 parser 对应关系
```

### SKILL.md 内容结构

```markdown
---
name: data_preprocessing
description: 接收原始财务文件（BS、小票、支票等），完成识别、分类、解析、配对，
输出标准化交易数据集。当用户传入需要处理的财务文件时使用此 Skill。
---

# 数据预处理 Skill 指令

## 核心原则
- 代码能做的不用 LLM，LLM 是兜底不是默认
- 不丢弃任何文件，无法处理的必须标记待人工确认
- 不确定的不猜，去问 accountant
- 所有输出必须遵循统一的交易数据格式（参考 output_schema.md）

## 处理流程
[详细的分步指令，见下方第 5 节]

## Script 调用说明
[每个 Script 的用途、输入参数、输出格式、何时调用]

## Reference 加载条件
- output_schema.md：在需要输出交易数据或验证输出格式时加载
- supported_banks.md：在判断 PDF 属于哪家银行时加载
```

### 渐进式披露的运作方式

1. **元数据层**（始终可见）：Agent 看到 name 和 description，判断当前任务是否需要使用此 Skill
2. **指令层**（按需加载）：Skill 被选中后，Agent 读取 SKILL.md 的完整指令，了解处理流程和规则
3. **资源层**（按需中的按需）：
   - Script：Agent 根据指令决定调用哪个脚本，脚本被执行后 Agent 只看到执行结果，不看脚本代码内容
   - Reference：Agent 在需要查阅格式定义或银行列表时加载对应文件

---

## 5. Agent 执行流程

Agent 的执行流程不是固定的 pipeline。Agent 根据收到的文件情况自行决定调用顺序和处理策略。以下是典型的执行流程，但 Agent 可以根据实际情况调整。

### Step 1: 接收文件与初步检查

```
→ 接收所有原始文件
→ 加载客户 profile.md（获取银行账户列表）
→ 如有任务说明，记录预期的账户范围和时间范围
```

### Step 2: 文件分类与解析

对每个文件判断类型并完成解析。核心原则：**代码优先识别和解析，失败后 LLM 兜底。**

#### PDF 文件处理

```
→ 调用 identify_pdf_type.py 识别 PDF 类型
  → 识别为已支持银行的 BS（如 TD、BMO）
    → 调用对应银行的 parser（如 parse_td_bs.py）
      → 解析成功 → 交易数据进入交易池
      → 解析失败 → LLM 直接解析 PDF 内容，输出统一格式交易数据
    → parser 执行中如提取到支票影像页 → 影像进入支票待处理队列

  → 识别为小票 PDF
    → LLM 直接解析，提取 vendor、金额、日期、税额、商品明细
    → 结果进入小票数据池

  → 识别为未支持银行的 BS
    → LLM 直接解析 PDF 内容，输出统一格式交易数据
    → 交易数据进入交易池

  → 代码无法识别
    → LLM 判断文件类型
      → 判断为已支持银行的 BS → 调用对应 parser → 成功则完成，失败则 LLM 直接解析
      → 判断为未支持银行的 BS → LLM 直接解析
      → 判断为小票 → LLM 直接解析提取小票信息
      → 判断为其他 → Agent 评估是否有用，或标记待人工确认
```

#### 图片文件处理

```
→ 全部交给 LLM 处理（一次调用完成分类 + 内容提取）
→ LLM 识别为小票 → 提取 vendor、金额、日期、税额、商品明细 → 进入小票数据池
→ LLM 识别为支票 → 提取 payee、金额、日期、memo → 进入支票待处理队列
→ LLM 识别为其他 → Agent 评估是否有用，或标记待人工确认
```

#### Excel/CSV 文件处理

```
→ 代码分析表头和数据结构，判断是否为银行导出的交易数据
  → 是 → 调用 parse_excel_bs.py 解析 → 交易数据进入交易池
  → 否或无法判断 → LLM 分析文件内容
    → LLM 判断为交易数据 → LLM 直接解析为统一格式 → 进入交易池
    → LLM 判断为其他 → Agent 评估或标记待人工确认
```

#### 其他格式文件

```
→ 全部交给 LLM 处理
→ LLM 分析内容，提取有价值的信息
→ 能转化为交易数据 → 按统一格式输出 → 进入交易池
→ 不确定 → 不猜测，标记待人工确认
```

**所有 LLM 解析的核心约束：输出的交易数据字段必须统一，遇到不清楚的字段不猜测，标记为空或 unknown，由 accountant 后续确认。**

### Step 3: 支票影像处理

```
→ 对所有支票影像（来自 parser 提取 + 用户直接传入的支票图片）
→ LLM 多模态识别，提取 cheque_number、payee、金额、日期、memo
→ 通过支票号关联到交易池中对应的 CHQ# 交易
  → 关联成功 → 将 cheque_info（cheque_number, payee, memo, match_method: "cheque_number"）写入对应交易
  → 无法通过支票号关联 → LLM 尝试通过金额 + 日期匹配
    → 匹配成功 → 将 cheque_info（cheque_number, payee, memo, match_method: "amount_date"）写入对应交易
    → 匹配失败 → 标记待人工确认，记录到预处理摘要的待确认清单（含支票号、金额、payee、memo）
```

### Step 4: 小票与交易配对

```
→ 所有 BS 解析和所有小票提取完成后，执行统一配对
→ 调用 match_receipts.py 进行代码配对（金额 + 日期 + 商家名模糊匹配）
  → 高确信配对 → 自动将小票数据写入交易的 receipt 字段
  → 低确信配对 → LLM 进一步判断（如 BS 上 "AMZN MKTP CA" vs 小票上 "Amazon.ca"）
    → LLM 判断为同一交易 → 写入 receipt 字段
    → LLM 无法确定 → 标记待人工确认
  → 未配对小票 → 标记待人工确认
```

### Step 5: Description 标准化

```
→ 所有交易数据经过 Step 2-4 进入交易池后，统一执行 description 标准化
→ 对每笔交易调用共享模块 standardize_description(raw_description, client_id)
  → 返回 canonical pattern → 写入交易的 description 字段
  → 原始描述保留在 raw_description 字段
  → 同时记录 cleaned_fragment 和 source（dictionary_hit / llm_extraction / fallback）
→ 字典未命中的新 description 由共享模块自动调用 LLM 提取并缓存到 Pattern Dictionary
→ 详细设计见 tools/pattern_standardization_spec.md
```

### Step 6: 完整性校验与去重

```
→ 根据 profile.md 中的银行账户列表，检查每个账户是否都有对应的 BS
→ 根据任务说明（如有）或 BS 自身的日期范围，检查月份覆盖是否完整
→ 检测重复 BS（同一账户同一月份出现多个文件）
  → 内容相同 → 自动去重，在摘要中记录
  → 内容不同 → 标记待人工确认（可能是修正版 vs 原始版）
→ 发现缺失或异常 → 记录在摘要中
```

### Step 7: 生成预处理摘要与输出

```
→ 调用 generate_summary.py 收集处理过程中的所有元数据，生成结构化摘要数据
→ Agent 基于结构化数据生成可读的摘要文本
→ Agent 将摘要发送给 accountant，负责后续交互（回答疑问、处理待确认项）
→ 将交易数据按 BS 来源分组，逐组传入主 Workflow
```

---

## 6. Scripts 详细说明

每个 Script 是一个独立的可执行脚本。Agent 只关心 Script 的输入参数和返回结果，不读取代码内容。

### identify_pdf_type.py

- **用途**：识别 PDF 文件属于什么类型
- **输入**：PDF 文件路径
- **执行逻辑**：读取 PDF 前几页文字内容，匹配已知银行的特征模式（header 格式、银行名称、账号格式等）
- **输出**：`{ "type": "bs" | "receipt" | "unknown", "bank": "td" | "bmo" | null, "confidence": "high" | "low" }`
- **扩展方式**：新增银行支持时，在脚本中添加对应银行的特征匹配规则

### parse_bs.py

- **用途**：解析 Bank Statement PDF 为结构化交易数据
- **输入**：PDF 文件路径
- **执行逻辑**：已有实现（693 行，v2.0），针对 TD BS 格式定制的确定性解析逻辑
- **输出**：标准交易数据格式数组（格式见第 7 节）
- **附加行为**：如果 PDF 中包含支票影像页，将其截取为图片文件并在输出中标记

### parse_excel_bs.py

- **用途**：解析 Excel/CSV 格式的银行交易数据
- **输入**：文件路径 + 银行标识
- **执行逻辑**：根据银行标识选择对应的列映射规则，将表格数据转为标准交易数据格式
- **输出**：标准交易数据格式数组

### extract_cheque_images.py

- **用途**：从 BS PDF 中识别和提取支票影像页
- **输入**：PDF 文件路径
- **执行逻辑**：识别 PDF 中的支票影像页（通过页面布局特征），截取为独立图片文件
- **输出**：`{ "cheque_images": [{ "file_path": "...", "cheque_number": "00456", "page_number": 3 }] }`
- **说明**：可以集成在各银行 parser 中，也可以作为独立脚本在 parser 未提取时调用

### match_receipts.py

- **用途**：将小票数据与交易数据做自动配对
- **输入**：交易数据池（JSON 数组）+ 小票数据池（JSON 数组）
- **执行逻辑**：
  - 金额匹配：小票 total_amount 与交易 amount 完全一致或差额 ≤ $0.05
  - 日期匹配：小票日期与交易日期相差 0-3 天
  - 商家名模糊匹配：小票 vendor_name 与交易 description 的相似度评分
  - 三项综合评分决定配对确信度
- **输出**：`{ "high_confidence": [...], "low_confidence": [...], "unmatched_receipts": [...] }`
- **说明**：低确信配对由 Agent 调用 LLM 进一步判断，不直接介入人工

### generate_summary.py

- **用途**：收集预处理过程中的所有元数据，生成结构化摘要数据
- **输入**：处理日志（文件分类结果、解析结果、配对结果、异常记录）
- **执行逻辑**：汇总统计信息，生成结构化 JSON
- **输出**：结构化摘要数据（文件清单、BS 覆盖情况、重复检测结果、配对结果、交易总数、待确认事项列表）
- **说明**：Agent 拿到结构化数据后，自行生成可读的摘要文本与 accountant 交互

---

## 7. 输出

### 主要输出：标准交易数据集

按 BS 来源分组的结构化交易数据，每笔交易格式如下：

```yaml
{
    "transaction_id": "txn_2024071502",
    "date": "2024-07-15",
    "description": "HOME DEPOT",
    "amount": -156.78,
    "balance": 12345.67,
    "direction": "debit",
    "raw_description": "HOME DEPOT 4521 TORONTO ON",
    "account": "TD-CAD-5027013",
    "currency": "CAD",
    "supplementary_context": "",
    "receipt": {
        "vendor_name": "The Home Depot #4521",
        "items": ["Portland Cement x3", "Rebar 10mm x10"],
        "tax_amount": 18.07,
        "match_confidence": "high"
    },
    "cheque_info": null,
    "bs_source": "TD_Chequing_Jul_2024.pdf"
}
```

- `transaction_id` 字段：数据预处理 Agent 为每笔交易生成的唯一标识，格式 `txn_{YYYYMMDD}{序号}`，贯穿整个 Workflow 直至写入 Transaction Log

- `receipt` 字段：无小票配对时为 null
- `cheque_info` 字段：支票影像成功关联到该交易时填入，包含 cheque_number、payee、memo、match_method；无支票影像或关联失败时为 null
- `supplementary_context` 字段：预处理阶段不写入；仅由 Coordinator Agent 在拆分交易后子交易重新走 workflow 时注入额外说明

### 附属输出：预处理摘要

Agent 生成的可读摘要，示例：

```
客户：2830448 Ontario Ltd.

接收文件：15 个
  - BS PDF：12 个（TD Chequing x6, TD Savings x6）
  - 小票：2 个（图片 x1, PDF x1）
  - 无法识别：1 个（filename.jpg，待人工确认）

BS 覆盖情况：
  - TD Chequing (5027013)：2024-01 ✓ ... 2024-12 ✓
  - TD Savings (6337546)：2024-01 ✓ ... 2024-12 ✓

重复检测：
  - TD_Chequing_Jul.pdf 与 TD_July_Statement.pdf 内容相同，已去重

支票影像：
  - 4 张支票影像从 BS PDF 中提取，3 张已关联到对应交易，1 张无法自动关联

小票配对：
  - 2 张小票中 1 张已配对，1 张未配对（待人工确认）

交易总数：276 笔（TD Chequing 189 笔，TD Savings 87 笔）

待人工确认事项：
  - 1 个无法识别的文件
  - 1 张未配对的小票
  - 1 张无法关联到交易的支票（CHQ#00789，$2,500，收款人 ABC Corp，memo: Consulting fee）

输出状态：就绪（有 2 项待人工确认，不阻塞后续处理）
```

---

## 8. 权限边界

### 允许

- ✅ 读取客户 profile.md（获取银行账户列表用于校验）
- ✅ 调用所有已注册的 Script
- ✅ 自主决定文件分类和处理顺序
- ✅ 自动去重内容完全相同的重复 BS
- ✅ 将支票提取信息写入交易的 cheque_info
- ✅ 将小票数据写入交易的 receipt 字段
- ✅ 对低确信配对调用 LLM 进一步判断
- ✅ 生成预处理摘要并与 accountant 交互
- ✅ 标记无法处理的事项为待人工确认

### 不允许

- ❌ 修改 profile.md / rules.md / observations.md
- ❌ 进行交易分类判断（不判断科目、不判断 HST）
- ❌ 生成 JE
- ❌ 丢弃任何文件（无法处理的必须标记待人工确认，不能静默跳过）
- ❌ 对不确定的内容做猜测性解析（标记 unknown，交给 accountant）

---

## 9. 与人的交互

| 交互对象 | 交互内容 | 交互时机 |
| --- | --- | --- |
| Accountant | 发送预处理摘要供校验 | 所有文件处理完成后 |
| Accountant | 回答 accountant 对摘要的疑问 | Accountant 有问题时 |
| Accountant | 发送待人工确认清单并处理回复 | 有无法自动处理的事项时 |

Agent 不主动向客户交互，所有沟通通过 accountant。

---

## 10. 与其他组件的关系

### 上游（数据来源）

| 组件 | 关系 |
| --- | --- |
| 用户 / Accountant | 提供原始文件集合和任务说明 |
| Profile.md | 提供客户银行账户列表，用于完整性校验和 BS 识别辅助 |
| Pattern Dictionary | R/W：查找已知 pattern + 缓存 LLM 提取的新条目（通过共享模块 standardize_description） |

### 下游（输出去向）

| 组件 | 关系 |
| --- | --- |
| 主 Workflow | 接收标准交易数据集，按 BS 来源分组逐组处理 |
| Accountant | 接收预处理摘要和待人工确认清单 |

### 不直接交互

| 组件 | 关系 |
| --- | --- |
| Rules.md | 预处理 Agent 不读取也不写入 |
| Observations.md | 预处理 Agent 不读取也不写入 |
| Knowledge Base | 预处理 Agent 不需要会计知识 |
| Coordinator Agent | 预处理 Agent 完成后不再参与 |
| 审核 Agent | 预处理 Agent 不参与审核流程 |
