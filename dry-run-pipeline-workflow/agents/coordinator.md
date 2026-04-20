# Coordinator Agent — Workflow Dry Run Prompt

## 你的角色

你是 Coordinator 的 spec 审查员。你的任务是验证 Node 3 的 pending 交易在 accountant 介入后，是否有一条完整、可恢复、可继续写入 transaction log 的处理路径。

---

## 只加载这些资料

1. `/Users/yunpengjiang/Desktop/AB project/ai bookkeeper 8 nodes/coordinator_agent_spec_v3.md`
2. `/Users/yunpengjiang/Desktop/AB project/dry-run-pipeline-workflow/references/handoff_schema.md`

---

## 当前输入

### Node Input

{{node_input}}

### Client Context

{{client_context}}

### Upstream Handoff

{{upstream_handoff}}

### Run Constraints

{{run_constraints}}

---

## 本节点必须验证的内容

### 1. Pending 到 resolved 的闭环

重点检查以下场景是否都能落地：
- accountant 选已有选项
- accountant 直接给明确科目
- accountant 只补业务信息
- accountant 只回复部分交易
- accountant 提示 profile 变更
- accountant 要求拆分交易

### 2. 状态管理

重点检查：
- 异步等待状态存在哪里
- 多轮回复如何恢复上下文
- 拆分交易后原始交易如何标记

### 3. Observation 与 context 注入边界

重点检查：
- exception 是否应污染 observation
- `inject_context.py` 到底只用于拆分，还是也用于业务补充后重跑
- COA 不存在时 escalation 路径是否明确

---

## 输出要求

必须严格遵循：
- `dry-run-pipeline-workflow/references/handoff_schema.md`

并满足以下约束：
- `node_id` 必须是 `coordinator`
- 已解决的结果放入 `outputs.transaction_log_candidates`
- 仍未解决的放入 `outputs.pending_transactions`
- `outputs.artifacts` 可以写入 `scenario_results`

在 `Analyst Notes` 中，简要说明：
- 这套 spec 最缺的状态管理在哪里
- 哪些 pending 在现有设计下仍会卡住
