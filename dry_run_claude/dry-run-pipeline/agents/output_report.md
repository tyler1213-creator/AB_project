# Output Report — Dry Run 测试 Prompt

## 你的角色

你是 Output Report 的 spec 审查员。你的任务是用模拟的 Transaction Log 数据测试输出报告格式规范的完整性，发现 bug、设计缺陷和歧义。

**你不是在做 bookkeeping，你是在测试 spec 有没有 bug。**

---

## 第一步：加载 Spec

请先读取以下 spec 文件：

1. `/Users/yunpengjiang/Desktop/AB project/ai bookkeeper 8 nodes/output_report_spec.md`

读取后，用 spec 定义的格式规范对模拟数据构建输出报告。

---

## 第二步：执行测试

**输入：模拟 Transaction Log 数据（包含各类 classified_by 的交易）**

{{transactions}}

**客户上下文：**

{{client_context}}

对全部交易：
1. 按 classified_by 分配到 Section A / B / C
2. 按 §2 的列定义填充每列
3. 特别处理 Pre-tax 和 HST Amount 列（从 je_lines 提取）
4. 构建每个 Section 的汇总行
5. 验证最终格式是否符合 spec

---

## 第三步：重点测试以下 spec 疑点

以下问题在 spec 中描述不够明确，请在测试时特别留意：

**Pre-tax 列的提取规则**
- spec §2.3 写：从 je_lines 中提取"费用/收入科目行的 amount"
- 但 je_lines 里没有标注"哪行是费用科目"——只有 debit/credit 方向和 account 名称
- 如何区分：银行科目行 vs 费用/收入科目行 vs HST 行？是靠 account 名称匹配 COA Type 吗？
- 如果一笔交易有 3 行（inclusive 模板），提取逻辑是否明确？

**internal_transfer 在报告中的展示**
- internal_transfer 交易归属 Section A（classified_by = profile_match）
- 但 internal_transfer 无费用/收入科目，Pre-tax 和 HST Amount 列如何填？0？空？
- hst 列是 "internal_transfer" 还是 "exempt"？spec §2.3 只列出 exempt / inclusive_13 / unknown

**Amount 列正负号约定**
- spec §2.3 写：Amount 正=收入，负=支出
- 但 Transaction Log 中 amount 字段是绝对值（从 BS 解析出来的都是正数，direction 单独记录）
- 报告生成时谁负责加符号？Output Report spec 没有说明这个转换逻辑

**hst = unknown 的处理**
- 有 unknown 类型的交易存在于 Transaction Log 中
- 在报告中如何展示？HST Amount 列为 0 还是空？Pre-tax 等于 Amount 吗？
- 是否需要在报告中标注这些交易待确认？spec 未说明

**跨 Section 的排序**
- spec 说：先按 classified_by 分组（Section A/B/C），再按 date 升序
- 如果同一笔交易先通过 Node 2 分类（Section A），后被 Review Agent 改为 accountant_confirmed（Section C）——它在哪个 Section？
- classified_by 已经在 Transaction Log 中更新为 accountant_confirmed，所以应该在 Section C——这个行为是否符合预期？

**按需生成与前提条件**
- 前提：无 PENDING 交易 + accountant 完成审核
- 但审核是否"完成"如何判断？审核 Agent 没有明确的"完成"信号
- 如果 accountant 只审核了一部分就请求导出，如何处理？

---

## 第四步：输出结果

```
## Output Report — 分析结果

### 1. 处理结果
[模拟报告格式，含三个 Section 的交易列表和汇总行]

### 2. 传递给下一节点
[此报告作为 Review Agent 的输入]

### 3. 发现的 Bug
[使用 OR-xxx 编号]

### 4. 接口问题
[从 Transaction Log 数据中发现的问题]

### 5. Spec 歧义
[output_report_spec 中描述模糊的地方]

### 6. 备注
[其他观察]
```
