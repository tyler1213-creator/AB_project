# Dry Run Pipeline — Orchestrator 参考疑点清单

本文件供 orchestrator 在汇总各 subagent 输出后做针对性追问使用。**不注入 subagent prompt。**

如果 subagent 自主发现了某个疑点，很好；如果没发现，orchestrator 可以做定向追问。

---

## JE Generator

### HST 科目名一致性
- §1.5 Step 6 写的是 `"HST/GST Receivable"`
- §2 的 je_input 示例写的是 `"HST Receivable"`
- §3.1 Step 5 的校验条件写的是 `"HST Receivable"`
- 三处名称是否一致？validate_je 的精确匹配会因名称不一致而失败

### inclusive 收入场景的 validate_je 校验
- §3.1 Step 5 写：`inclusive_13: 必须有一行 account = "HST Receivable"`
- 但 §3.2 模版 2 的收入示例用的是 `"HST Payable"`（credit 侧）
- 收入交易的 validate_je 校验条件是否应该允许 HST Payable？

### account 科目的 COA 校验职责归属
- validate_je 不检查 account 是否在 COA 中，由调用方在分类阶段校验
- 但 Node 3 spec 里 COA 验证是 LLM 输出后的格式检查
- 是否存在双方都没有检查的可能？

### hst = unknown 的 JE 修正路径
- 模版 3 结构与 exempt 相同（2 行），Transaction Log 靠 `hst: "unknown"` 标记区分
- unknown 的交易 JE 如何最终被修正？JE 是否需要在后续阶段重新生成？

### build_je_lines.py 各调用方的参数差异
- 5 个调用方（Node 1/2/3、Coordinator、审核 Agent）传入的参数格式是否一致？
- Node 1 处理 internal_transfer 时是否还需要提供 `classification.account`？

---

## Coordinator Agent

### 异步等待与状态管理
- Coordinator 是异步的——发出消息后等待 accountant 回复，可能数小时或数天
- "等待状态"如何存储？如果 Claude 进程退出，会话状态如何恢复？
- "Accountant 可以分多次回复，Agent 维护已处理/未处理状态"——状态存在哪里？

### 拆分交易后的原始交易状态
- split_transaction.py 拆分后，子交易调用 retrigger_workflow.py 从 Node 1 重新走
- 原始交易在 Transaction Log 中如何处理？是删除、标记为 superseded，还是保留？

### inject_context.py 的使用范围
- §6 说"仅在拆分交易后子交易需要重新走 workflow 时使用"
- 但 §4 执行流程提到：accountant 给出业务信息后，agent 有时会注入 supplementary_context 再让交易重走 workflow
- 这两个场景是否都应该用 inject_context.py？

### 非结构化 PENDING 的完整处理链
- "不带选项"的 PENDING：accountant 的回复可能再次触发情况 A 或 B
- 完整处理链是否与"带选项"最终汇归到同一个 Step 4？

### Coordinator 阶段的"例外不污染 observation"逻辑
- spec 只在审核 Agent 中明确了"例外不污染 observation"
- 如果 Coordinator 阶段 accountant 说"这只是这次的例外"——Coordinator 是否也应该跳过 write_observation？

### COA 验证失败时的 escalation 路径
- accountant 指定了不在 COA 中的科目，提示后 accountant 坚持用这个科目名
- spec 未描述这个 escalation 路径

---

## Output Report

### Pre-tax 列的提取规则
- 从 je_lines 中提取"费用/收入科目行的 amount"——但 je_lines 里没有标注"哪行是费用科目"
- 如何区分：银行科目行 vs 费用/收入科目行 vs HST 行？
- 如果一笔交易有 3 行（inclusive 模板），提取逻辑是否明确？

### internal_transfer 在报告中的展示
- internal_transfer 交易归属 Section A（classified_by = profile_match）
- 但无费用/收入科目，Pre-tax 和 HST Amount 列如何填？
- hst 列是 "internal_transfer" 还是 "exempt"？

### Amount 列正负号约定
- spec 写 Amount 正=收入，负=支出
- 但 Transaction Log 中 amount 字段可能是绝对值（direction 单独记录）
- 报告生成时谁负责加符号？

### hst = unknown 的报告展示
- HST Amount 列为 0 还是空？Pre-tax 等于 Amount 吗？
- 是否需要标注这些交易待确认？

### 跨 Section 的 classified_by 变更
- 某笔交易先通过 Node 2 分类（Section A），后被审核 Agent 改为 accountant_confirmed（Section C）——它在哪个 Section？

### 报告生成的"审核完成"判断标准
- 前提：accountant 完成审核——但审核是否"完成"如何判断？
- accountant 只审核了一部分就请求导出，如何处理？

---

## Review Agent

### intervention_type 判断冲突
- `exception` 和 `rule_error` 需要 Agent 显式传入；`classification_error` 和 `hst_correction` 自动判断
- 如果 accountant 说"这笔是例外"且同时改了 account——这既是 exception 又是 classification_error
- 自动判断会覆盖 agent 的显式传入吗？

### 删除 rule 时 observation 的 non_promotable 标记范围
- 如果该 pattern 有多条 rule（不同 amount_range），删除其中一条是否标记整个 observation 为 non_promotable？

### 审核 Agent vs Coordinator Agent 对 profile 变更信号的处理差异
- 审核 Agent 不修改 profile.md，只建议 accountant 在下次处理时更新
- Coordinator Agent 会直接更新 profile 并触发 retrigger
- 这个差异是否有意为之？是否会让 accountant 困惑？

### pattern 变更后的 rebuild 状态处理
- rebuild 重新聚合 observations 时，non_promotable 和 force_review 等状态标记是保留还是重置？
- 原 observation 有 accountant_notes，rebuild 后是否保留？

### write_intervention_log.py 的 date 取值
- date 从 `transaction_ids[0]` 的 Transaction Log 记录中获取
- 一次干预影响多笔跨月交易时，取 transaction_ids[0] 的 date 是否合理？
- 干预发生的时间应该是 audit timestamp 而非交易日期？

### Section A 排查"当期"的范围
- query_transaction_log.py 用 rule_id 查询"当期所有被该 rule 匹配的交易"
- "当期"是当前 period 还是历史全部？
