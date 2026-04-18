# 输出报告（Output Report）

---

## 1. 职责定义

定义系统最终交付物的格式规范。输出报告是一份 Excel 工作簿，包含当期所有已完成交易的分类结果和 JE 明细，供 accountant 存档和审计使用。

**输出报告不是审核载体。** Accountant 的审核工作通过聊天（WhatsApp/Slack）与审核 Agent 交互完成。输出报告在审核完毕后按需生成，是只读的最终交付物。

---

## 2. 数据格式

### 2.1 工作簿结构

一个 Excel 文件（.xlsx），包含一个主工作表，按 Section 分区展示。

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
| Amount | amount | 交易金额（正=收入，负=支出） |
| Account | account | 分类科目 |
| HST | hst | HST 处理方式（exempt / inclusive_13 / unknown） |
| Pre-tax | je_lines 中费用/收入行的 amount | HST 拆分后的税前金额。exempt 和 unknown 时等于 Amount 绝对值 |
| HST Amount | je_lines 中 HST Receivable/Payable 行的 amount | HST 金额。exempt 和 unknown 时为 0 或空 |
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
| Amount | amount | 原样 |
| Account | account | 原样 |
| HST | hst | 原样 |
| Pre-tax | je_lines | 从 je_lines 中提取费用/收入科目行的 amount |
| HST Amount | je_lines | 从 je_lines 中提取 HST Receivable 或 HST Payable 行的 amount；无则为空 |
| Bank Account | bank_account | 原样 |
| Classified By | classified_by | 原样 |

---

## 4. 生成时机

**按需生成，不自动触发。**

```
前提条件:
  → 当期所有交易已完成分类（无 PENDING 交易）
  → Accountant 通过审核 Agent 完成审核

触发方式:
  → Accountant 通过聊天请求导出（如"导出 7 月报告"）
  → 审核 Agent 调用报告生成功能

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
