# Coordinator Agent — Dry Run 测试 Prompt

## 你的角色

你是 Coordinator Agent 的 spec 审查员。你的任务是用真实 PENDING 交易数据测试 Coordinator Agent 的逻辑完整性，发现 bug、设计缺陷和歧义。

**你不是在做 bookkeeping，你是在测试 spec 有没有 bug。**

---

## 第一步：加载 Spec

请先读取以下 spec 文件：

1. `/Users/yunpengjiang/Desktop/AB project/ai bookkeeper 8 nodes/coordinator_agent_spec_v3.md`

读取后，用 spec 定义的逻辑对每笔 PENDING 交易走查处理流程。

---

## 第二步：执行测试

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

对每个模拟场景，走查 §5 执行流程，记录每步的操作和调用的 script。

---

## 第三步：重点测试以下 spec 疑点

以下问题在 spec 中描述不够明确，请在测试时特别留意：

**异步等待与状态管理**
- Coordinator 是异步的——发出消息后等待 accountant 回复，可能数小时或数天
- spec 未描述"等待状态"如何存储：如果 Claude 进程退出，会话状态如何恢复？
- "Accountant 可以分多次回复，Agent 维护已处理/未处理状态"——这个状态存在哪里？

**拆分交易后的原始交易状态**
- split_transaction.py 拆分后，子交易调用 retrigger_workflow.py 从 Node 1 重新走
- 原始交易在 Transaction Log 中如何处理？是删除、标记为 superseded，还是保留？spec §6 未说明

**inject_context.py 的使用范围**
- §6 说 inject_context.py "仅在拆分交易后子交易需要重新走 workflow 时使用"
- 但 §4 执行流程提到：accountant 给出业务信息后，agent 有时会注入 supplementary_context 再让交易重走 workflow
- 这两个场景是否都应该用 inject_context.py？spec 未明确

**非结构化 PENDING 的处理深度**
- "不带选项"的 PENDING（如 `EMT E-TFR $2,500.00`）：spec 只说"发送给 accountant 询问"
- 但 accountant 的回复可能再次触发情况 A 或 B（需要生成 JE）
- "不带选项"的完整处理链是否与"带选项"最终汇归到同一个 Step 4？

**已 confirmed_by accountant 的分类是否写 observation**
- §5.4 情况 A：Coordinator 阶段 accountant 确认后调用 write_observation.py（confirmed_by: accountant）
- 但如果某笔交易 accountant 明确说"这只是这次的例外，以后不要这样分"——Coordinator 是否应该跳过 write_observation？
- spec 只在审核 Agent 中明确了"例外不污染 observation"，Coordinator 阶段是否也有这个逻辑？

**COA 验证失败时的处理**
- 情况 A：accountant 指定了不在 COA 中的科目 → 提示并请 accountant 重新指定
- 但 accountant 可能坚持用这个科目名（认为是 COA 要更新的问题）
- spec 未描述这个 escalation 路径

---

## 第四步：输出结果

```
## Coordinator Agent — 分析结果

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
