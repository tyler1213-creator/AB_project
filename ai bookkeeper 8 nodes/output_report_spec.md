# 输出报告（Output Report）

---

## 1. 职责定义

定义输出层产物的格式规范。该层有两种产物：

1. `report_draft`：供 Review Agent 使用的审核前快照，可为 markdown / 结构化表格形式
2. 最终输出报告：审核完成后按需导出的 `.xlsx` 工作簿

Accountant 的审核工作仍通过聊天与审核 Agent 交互完成，但审核 Agent 需要一份与最终报告列结构一致的 `report_draft` 作为 review 载体。

---

## 2. 数据格式

### 2.1 工作簿结构

最终导出产物是一个 Excel 文件（.xlsx），包含一个主工作表，按 Section 分区展示。

`report_draft` 复用相同的 Section 划分和列定义，但不要求已经落盘为最终 `.xlsx`。

### 2.2 Section 划分

| Section | 名称 | 交易来源 | 含义 |
|---------|------|----------|------|
| Section A | CERTAIN | `classified_by = profile_match` 或 `rule_match` | 确定性匹配，由代码逻辑完成分类 |
| Section B | PROBABLE | `classified_by = ai_high_confidence` | AI 高置信度判断 |
| Section C | CONFIRMED | `classified_by = accountant_confirmed` | Accountant 人工确认（含 Coordinator 阶段确认和审核阶段修正） |

每个 Section 内的交易按 date 升序排列。Section 之间有视觉分隔（空行 + Section 标题行）。

### 2.3 列定义

| 列 | 字段来源（Transaction Log） | 说明 |
|----|---------------------------|------|
| Date | date | 交易日期 |
| Description | description | 标准化后的交易描述 |
| Amount | amount + direction | 报告展示金额。底层存储为绝对值金额，报告层结合 direction 展示收入/支出方向 |
| Account | account | 分类科目 |
| HST | hst | HST 处理方式（exempt / inclusive_13 / unknown） |
| Pre-tax | je_lines 中费用/收入行的 amount | HST 拆分后的税前金额。exempt 和 unknown 时等于 amount |
| HST Amount | je_lines 中 HST/GST Receivable 或 HST/GST Payable 行的 amount | HST 金额。exempt 和 unknown 时为 0 或空 |
| Bank Account | bank_account | 所属银行账户 |
| Classified By | classified_by | 分类来源（profile_match / rule_match / ai_high_confidence / accountant_confirmed） |

### 2.4 汇总行

每个 Section 末尾一行汇总：

```
Section A 小计: [交易笔数] 笔, 总支出 $xxx, 总收入 $xxx
Section B 小计: [交易笔数] 笔, 总支出 $xxx, 总收入 $xxx
Section C 小计: [交易笔数] 笔, 总支出 $xxx, 总收入 $xxx
─────────────────────────────────
总计: [交易笔数] 笔, 总支出 $xxx, 总收入 $xxx
```

---

## 3. 数据来源

从 Transaction Log 拉取指定 period 的所有交易记录。

```
查询条件: period = 目标会计期间（如 "2024-07"）
数据范围: 该 period 下所有已写入 Transaction Log 的交易（即所有已完成分类的交易）
排序: 先按 classified_by 分组（对应 Section A/B/C），再按 date 升序
```

### 字段映射

| 报告列 | Transaction Log 字段 | 转换逻辑 |
|--------|---------------------|----------|
| Date | date | 原样 |
| Description | description | 原样 |
| Amount | amount + direction | 根据 `direction` 决定报告层显示为收入或支出；底层金额保持绝对值 |
| Account | account | 原样 |
| HST | hst | 原样 |
| Pre-tax | je_lines | 从 je_lines 中提取费用/收入科目行的 amount |
| HST Amount | je_lines | 从 je_lines 中提取 HST/GST Receivable 或 HST/GST Payable 行的 amount；无则为空 |
| Bank Account | bank_account | 原样 |
| Classified By | classified_by | 原样 |

---

## 4. 生成时机

分两种时机：

```
模式 A：生成 report_draft（审核前）
  前提条件:
    → 当期交易已形成可审核的 transaction log 数据集
    → Coordinator 阶段已处理完当前批次的 PENDING
  触发方式:
    → 主 Workflow 在 Review Agent 前生成
  输出:
    → 生成 `report_draft`
    → 供 Review Agent 使用，不视为最终交付物

模式 B：导出最终 .xlsx（审核后）
  前提条件:
    → 当期所有交易已完成分类（无 PENDING 交易）
    → Accountant 通过审核 Agent 完成审核
  触发方式:
    → Accountant 通过聊天请求导出（如"导出 7 月报告"）
    → 审核 Agent 调用报告导出功能
  输出:
    → 生成 .xlsx 文件
    → 文件名格式: {客户名}_{period}_bookkeeping_report.xlsx
    → 示例: AcmeCorp_2024-07_bookkeeping_report.xlsx
```

---

## 5. 被谁读取

| 读取者 | 用途 |
|--------|------|
| Accountant | 存档、客户交付、年终结账参考 |
| CRA 审计 | 审计时提供的交易分类明细（配合 Transaction Log 的完整审计追溯） |

---

## 6. 被谁修改

**不可修改。** 输出报告是只读的快照文件。

如果 accountant 发现需要修正：
1. 通过审核 Agent 在 Transaction Log 层面完成修正
2. 重新导出报告（生成新文件，不覆盖旧文件）

---

## 7. 与其他组件的关系

### 上游

| 组件 | 关系 |
|------|------|
| Transaction Log | 唯一数据来源。报告的所有字段从 Transaction Log 拉取 |

### 触发方

| 组件 | 关系 |
|------|------|
| 审核 Agent | 接收 accountant 的导出请求，调用报告生成功能 |

### 无关系的组件

| 组件 | 说明 |
|------|------|
| Node 1/2/3、Coordinator Agent | 主 Workflow 不直接写入报告。它们写入 Transaction Log，报告从 Transaction Log 拉取 |
| Profile / Rules / Observations | 报告不读取这些文件，所有需要的信息已在 Transaction Log 中 |
