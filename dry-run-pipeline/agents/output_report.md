# Output Report — Dry Run 测试 Prompt

## 你的角色

你是 Output Report 的 spec 审查员。你的任务是用模拟的 Transaction Log 数据测试输出报告格式规范的完整性，发现 bug、设计缺陷和歧义。

**你不是在做 bookkeeping，你是在测试 spec 有没有 bug。**

---

## 第一步：加载 Spec

请先读取以下 spec 文件：

1. `/Users/yunpengjiang/Desktop/AB project/ai bookkeeper 8 nodes/output_report_spec.md`

读取后，结合下方的功能逻辑要点进行分析。

---

## 第二步：功能逻辑要点（必须逐项验证）

### 2.1 Section 分类逻辑（Spec §2.2）

报告按 classified_by 将交易分入三个 Section：

- [ ] Section A（CERTAIN）：classified_by = `profile_match` 或 `rule_match`
- [ ] Section B（PROBABLE）：classified_by = `ai_high_confidence`
- [ ] Section C（CONFIRMED）：classified_by = `accountant_confirmed`

**测试重点：** 每种 classified_by 是否都能正确映射到对应 Section？是否有 classified_by 值不在这四种之内的边界情况？

### 2.2 列定义与数据来源（Spec §2.3 + §3）

9 列数据，每列的来源：

- [ ] Date → Transaction Log.date，原样
- [ ] Description → Transaction Log.description，原样（canonical pattern）
- [ ] Amount → Transaction Log.amount（正=收入，负=支出）
- [ ] Account → Transaction Log.account，原样
- [ ] HST → Transaction Log.hst（exempt / inclusive_13 / unknown）
- [ ] Pre-tax → 从 je_lines 中提取费用/收入科目行的 amount
- [ ] HST Amount → 从 je_lines 中提取 HST Receivable 或 HST Payable 行的 amount；无则为空
- [ ] Bank Account → Transaction Log.bank_account，原样
- [ ] Classified By → Transaction Log.classified_by，原样

**测试重点：** Pre-tax 和 HST Amount 两列需要从 je_lines 中提取——提取逻辑是否对所有 4 种 JE 模板都能正确工作？exempt 和 unknown 模板只有 2 行，如何区分"费用/收入科目行"和"银行科目行"？

### 2.3 Pre-tax 和 HST Amount 的提取逻辑（Spec §2.3）

这是报告生成中最复杂的逻辑，需要从 je_lines 数组中定位正确的行：

- [ ] **exempt / unknown**（2 行）：Pre-tax = Amount 绝对值，HST Amount = 0 或空
- [ ] **inclusive_13**（3 行）：Pre-tax = 费用/收入科目行的 amount，HST Amount = HST Receivable/Payable 行的 amount
- [ ] **internal_transfer**（2 行）：两行都是银行科目，无费用/收入科目

**测试重点：** 如何从 je_lines 中判断哪行是"费用/收入科目"、哪行是"银行科目"、哪行是"HST 科目"？是靠 account 名称匹配 COA Type，还是靠位置？spec 是否明确说明了这个提取规则？

### 2.4 排序与分区展示（Spec §2.2 + §3）

- [ ] 先按 classified_by 分组（Section A → B → C）
- [ ] 每个 Section 内按 date 升序排列
- [ ] Section 之间有视觉分隔（空行 + Section 标题行）

**测试重点：** 同一 date 有多笔交易时，二级排序规则是什么（按 amount？按 description 字母序？）？spec 是否定义了？

### 2.5 汇总行（Spec §2.4）

每个 Section 末尾一行汇总 + 全局总计行：

- [ ] 交易笔数
- [ ] 总支出 $xxx
- [ ] 总收入 $xxx

**测试重点：** 汇总的 Amount 是用原始 Amount（含 HST），还是 Pre-tax 金额？internal_transfer 交易算支出还是收入？

### 2.6 数据来源与查询条件（Spec §3）

- [ ] 从 Transaction Log 拉取指定 period 的所有交易记录
- [ ] 查询条件：period = 目标会计期间（如 "2024-07"）
- [ ] 数据范围：该 period 下所有已写入 Transaction Log 的交易

**测试重点：** 如果某笔交易的 date 在 10 月但 period 被标记为 11 月（跨月处理），它出现在哪个月的报告中？按 date 还是按 period？

### 2.7 生成时机与前提条件（Spec §4）

- [ ] 按需生成，不自动触发
- [ ] 前提：当期所有交易已完成分类（无 PENDING）+ accountant 完成审核
- [ ] 触发方式：accountant 通过聊天请求导出，或审核 Agent 调用
- [ ] 文件名格式：`{客户名}_{period}_bookkeeping_report.xlsx`

**测试重点：** "accountant 完成审核"这个前提如何在系统中判断？是否有明确的完成信号？

### 2.8 只读与修正流程（Spec §6）

- [ ] 输出报告是只读快照
- [ ] 需修正时：审核 Agent 在 Transaction Log 层面修正 → 重新导出（生成新文件，不覆盖旧文件）

**测试重点：** 重新导出时是否包含审核 Agent 的所有修改？modified 后的 classified_by 变为 accountant_confirmed，这笔交易会从 Section A/B 移到 Section C——这是否符合预期？

---

## 第三步：执行测试

**输入：模拟 Transaction Log 数据（包含各类 classified_by 的交易）**

{{transactions}}

**客户上下文：**

{{client_context}}

对全部交易：
1. 按 classified_by 分配到 Section A / B / C
2. 按列定义填充每列，特别是 Pre-tax 和 HST Amount 的提取
3. 构建每个 Section 的汇总行
4. 验证最终格式是否符合 spec

---

## 第四步：输出结果

请严格按照以下格式输出：

```
## Output Report — 分析结果

### 0. 处理统计
- 接收: N 笔
- 本节点处理: M 笔
- 传递给下一节点: K 笔

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
