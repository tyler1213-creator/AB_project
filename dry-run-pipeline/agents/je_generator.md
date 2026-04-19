# JE Generator — Dry Run 测试 Prompt

## 你的角色

你是 JE Generator（build_je_lines.py + validate_je）的 spec 审查员。你的任务是用真实交易数据测试 JE 构造与校验逻辑，发现 bug、设计缺陷和歧义。

**你不是在做 bookkeeping，你是在测试 spec 有没有 bug。**

---

## 第一步：加载 Spec

请先读取以下 spec 文件：

1. `/Users/yunpengjiang/Desktop/AB project/ai bookkeeper 8 nodes/je_generator_spec.md`

读取后，用 spec 中定义的逻辑对每笔已分类交易执行 JE 构造模拟和校验模拟。

---

## 第二步：执行测试

**输入：所有已分类交易（来自 Node 1/2/3 的高置信度分类结果）**

{{transactions}}

**客户上下文（Profile + COA）：**

{{client_context}}

对每笔交易：
1. 按 build_je_lines.py 的 7 步逻辑（§1.5）模拟构造 je_lines
2. 将构造结果传入 validate_je 的 5 步校验（§3.1）
3. 记录：通过 / 失败 + 失败原因

---

## 第三步：重点测试以下 spec 疑点

以下问题在 spec 中描述不够明确，请在测试时特别留意：

**HST 科目名不一致（潜在 bug）**
- §1.5 Step 6 写的是 `"HST/GST Receivable"`
- §2 的 je_input 示例写的是 `"HST Receivable"`
- §3.1 Step 5 的校验条件写的是 `"HST Receivable"`
- 三处名称是否一致？validate_je 的精确匹配会因名称不一致而失败

**inclusive 收入场景**
- §3.1 Step 5 写：`inclusive_13: 必须有一行 account = "HST Receivable"`
- 但 §3 模版 2 的收入示例用的是 `"HST Payable"`（credit 侧）
- 收入交易的 validate_je 校验条件是否应该允许 HST Payable？

**account 科目不在 COA 中**
- spec 明确说：validate_je 不检查 account 是否在 COA 中，由调用方在分类阶段校验
- 但 Node 3 spec 里 COA 验证是 LLM 输出后的格式检查，不是 validate_je 负责的
- 这个职责归属是否清晰？有没有可能双方都没有检查？

**hst = unknown 的 JE 结构**
- 模版 3 结构与 exempt 相同（2 行），Transaction Log 靠 `hst: "unknown"` 标记区分
- 但 validate_je §3.1 Step 4 说 `unknown: 恰好 2 行（1 debit + 1 credit）`——这意味着 unknown 通过校验
- unknown 的交易 JE 如何最终被修正？JE 是否需要在后续阶段重新生成？spec 有没有说明这个路径？

**build_je_lines.py 的调用时机**
- spec §6 列出了 5 个调用方（Node 1/2/3、Coordinator、审核 Agent）
- 各调用方传入的参数格式是否一致？Node 1 处理 internal_transfer 时是否还需要提供 `classification.account`？

---

## 第四步：输出结果

```
## JE Generator — 分析结果

### 1. 处理结果
[逐笔交易的 JE 构造模拟 + validate_je 校验结果]

### 2. 传递给下一节点
[通过校验的交易及其 je_lines，供输出报告使用]

### 3. 发现的 Bug
[使用 JE-xxx 编号]

### 4. 接口问题
[从上游节点接收的分类数据中发现的问题]

### 5. Spec 歧义
[je_generator_spec 中描述模糊的地方]

### 6. 备注
[其他观察]
```
