# Coordinator Agent — Dry Run 测试 Prompt

## 你的角色

你是 Coordinator Agent 的 spec 审查员。你的任务是用真实 PENDING 交易数据测试 Coordinator Agent 的逻辑完整性，发现 bug、设计缺陷和歧义。

**你不是在做 bookkeeping，你是在测试 spec 有没有 bug。**

---

## 第一步：加载 Spec

请先读取以下 spec 文件：

1. `/Users/yunpengjiang/Desktop/AB project/ai bookkeeper 8 nodes/coordinator_agent_spec_v3.md`

读取后，结合下方的功能逻辑要点进行分析。

---

## 第二步：功能逻辑要点（必须逐项验证）

### 2.1 Coordinator 的核心职责

Coordinator Agent 是置信度分类器和 accountant 之间的桥梁。它不做最终分类决定，但辅助 accountant 完成分类。

- [ ] 触发条件：置信度分类器处理完所有交易后，存在 PENDING 交易时自动触发
- [ ] 无 PENDING 交易 → 不启动，直接进入输出报告阶段
- [ ] Coordinator 是 Agent（需要 LLM 语义理解），不是代码 Pipeline

**测试重点：** 当所有交易都被 Node 1/2/3 消化（0 笔 PENDING）时，Coordinator 是否被正确跳过？

### 2.2 PENDING 交易接收与分组（Spec §5 Step 1）

- [ ] 调用 collect_pending.py 收集所有 PENDING 交易
- [ ] 按 description 的标准化 pattern 归组
- [ ] 组内按金额排序
- [ ] "带选项"和"不带选项"的 PENDING 分开排列

**测试重点：** 同一 pattern 不同金额的多笔交易是否正确归组？带选项和不带选项的分组逻辑是否与 Node 3 输出中的 options 字段对应？

### 2.3 沟通消息生成（Spec §5 Step 2）

**带选项的 PENDING：**
- [ ] 同 pattern 归组展示，列出每笔的日期、金额、direction
- [ ] 展示系统参考（observation_context）
- [ ] 展示系统建议选项（来自 classifier_output.options）
- [ ] 允许 accountant 统一回复或逐笔说明

**不带选项的 PENDING：**
- [ ] 展示交易明细
- [ ] 展示 AI 分析（description_analysis）和建议提问（suggested_questions）
- [ ] 请 accountant 提供信息

**cheque_info 交易：**
- [ ] 展示支票信息（收款人、备注、支票号）
- [ ] cheque_info 作为分类的关键线索呈现

**测试重点：** 消息格式是否对 accountant 友好？同组内交易数量很多时（如 10+ 笔同 pattern）展示方式是否合理？

### 2.4 Accountant 回复解析（Spec §5 Step 3-4）

**9 种回复类型及对应处理：**

- [ ] 直接选择选项 → 情况 A（明确分类指令）
- [ ] 提供明确科目 → 情况 A
- [ ] 提供业务信息但未指定科目 → 情况 B（模糊信息 → 生成选项）
- [ ] 部分回复 → 处理已回复部分，其余继续等待
- [ ] 附带 profile 变更信息 → 调用 update_profile.py + 处理分类回复
- [ ] 引用上下文 → 查阅上下文理解，无法确定则追问
- [ ] 模糊回复 → 追问确认
- [ ] 要求拆分 → 调用 split_transaction.py
- [ ] 提供信息但未直接分类 → 情况 B

**测试重点：** 每种回复类型的处理路径是否完整？是否有遗漏的回复类型？

### 2.5 情况 A：明确分类指令后的操作链（Spec §5 Step 4）

- [ ] 验证科目存在于 COA.csv → 存在 → 继续 / 不存在 → 提示重新指定
- [ ] 调用 build_je_lines.py 构造 → validate_je 校验
- [ ] 调用 write_observation.py 写入分类结果（confirmed_by: accountant）
- [ ] 调用 write_transaction_log.py 写入 Transaction Log（classified_by: accountant_confirmed）
- [ ] 交易完成分类，进入输出报告

**测试重点：** 操作链中每步的输入来源和输出去向是否明确？write_observation 和 write_transaction_log 的调用顺序是否有依赖？

### 2.6 情况 B：模糊信息后的操作链（Spec §5 Step 4）

- [ ] Agent 结合 COA.csv + tax_reference.md 生成 2-3 个选项
- [ ] 请 accountant 选择 → 走情况 A

**测试重点：** 生成选项时 agent 依据什么信息源？选项格式是否与 Node 3 输出的 options 格式一致？

### 2.7 拆分交易流程（Spec §5 Step 4 + §6）

- [ ] 调用 split_transaction.py：金额之和必须等于原始金额
- [ ] 子交易三种后续路径：
  - accountant 已给每条明确分类 → 每条走情况 A
  - accountant 只给金额拆分和模糊描述 → 每条走情况 B
  - accountant 只给金额拆分未说明用途 → 每条 retrigger_workflow.py 从 Node 1 重新走

**测试重点：** 拆分后原始交易的状态如何处理？子交易重走 workflow 时是否携带 supplementary_context？

### 2.8 Profile 变更信号捕获（Spec §5 Step 4）

- [ ] Agent 在解析任何回复时始终检查是否包含 profile 变更信号
- [ ] 可能触发的场景：银行账户变更、员工状态、贷款变更、HST 注册状态等
- [ ] 调用 update_profile.py → 如变更影响当前 PENDING 交易 → retrigger_workflow.py
- [ ] Agent 不主动询问这些信息

**测试重点：** profile 变更信号的检测是否依赖 LLM 语义理解？如果 accountant 的回复中隐含变更信号但不明确，agent 是否追问确认？

### 2.9 全部 PENDING 解决确认（Spec §5 Step 5）

- [ ] 检查所有 PENDING 是否都已处理
- [ ] 未处理的 → 继续等待或提醒 accountant
- [ ] 全部完成 → 主 Workflow 继续 → 生成输出报告

**测试重点：** 如果 accountant 长期不回复某些交易，系统的行为是什么？是否有超时机制？

### 2.10 权限边界（Spec §7）

- [ ] 允许：读 Profile/COA/tax_reference、更新 profile、注入 supplementary_context、拆分交易、触发 workflow 重处理、构造 JE、写 observation（confirmed_by: accountant）、写 Transaction Log
- [ ] 不允许：自行做最终分类决定、修改 rules.md、修改 observation 状态标记（non_promotable/force_review）

**测试重点：** Coordinator 的权限边界与审核 Agent 是否有重叠或冲突？两者的职责分界是否清晰？

---

## 第三步：执行测试

**输入：来自 Node 3 的 PENDING 交易列表**

{{transactions}}

**客户上下文（Profile + COA）：**

{{client_context}}

**模拟 Accountant 回复场景（覆盖以下类型）：**

1. 选择带选项 PENDING 的选项 A 或 B
2. 直接提供明确科目名称（不通过选项）
3. 提供业务信息但未指定科目（模糊回复）
4. 只回复部分交易（未全覆盖）
5. 回复中包含 profile 变更信号（如"这个客户上个月开始雇人了"）
6. 要求拆分某笔交易（指定金额拆分）

对每个模拟场景，走查执行流程，记录每步的操作和调用的 script。

---

## 第四步：输出结果

请严格按照以下格式输出：

```
## Coordinator Agent — 分析结果

### 0. 处理统计
- 接收: N 笔 PENDING 交易
- 本节点处理: M 笔（已完成分类）
- 传递给下一节点: K 笔（含拆分后重走 workflow 的子交易）

### 1. 处理结果
[每个模拟场景的处理流程和操作记录，含调用的 script]

### 2. 传递给下一节点
[完成分类的交易列表（已生成 JE），供输出报告使用]

### 3. 发现的 Bug
[使用 CO-xxx 编号]

### 4. 接口问题
[从 Node 3 接收的 PENDING 数据中发现的问题]

### 5. Spec 歧义
[coordinator_agent_spec 中描述模糊的地方]

### 6. 备注
[其他观察]
```
