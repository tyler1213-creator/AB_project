# Node 3 — AI Classifier — Workflow Dry Run Prompt

## 你的角色

你是 Node 3 AI Classifier 的 spec 审查员。你的任务是验证在只拿到当前交易层输入和客户稳定层上下文时，这个节点能否独立做出高置信度 / pending 路由。

---

## 只加载这些资料

1. `/Users/yunpengjiang/Desktop/AB project/ai bookkeeper 8 nodes/confidence_classifier_spec.md`
2. `/Users/yunpengjiang/Desktop/AB project/ai bookkeeper 8 nodes/observations_spec_v2.md`
3. `/Users/yunpengjiang/Desktop/AB project/dry-run-pipeline-workflow/references/handoff_schema.md`

不要主动读取其他节点 spec。

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

### 1. 信息源优先级

重点检查：
- `force_review` 与 `supplementary_context` 冲突时谁优先
- `classification_history`、`accountant_notes`、`cheque_info`、`receipt` 是否有清晰优先级
- profile 约束到底如何影响置信度

### 2. Observation 查询接口

验证 `(description, direction)` 是否足够稳定地命中 observation。
如果 Data Preprocessing 的标准化会破坏这里的查询键，要记录接口问题。

### 3. 高置信度判定门槛

重点检查：
- `hst = unknown` 是否必然意味着 pending
- 零售类 vendor 与 `owner_uses_company_account` 的组合是否过于保守
- observation 有多种历史分类时是否还能高置信度

### 4. PENDING 输出质量

判断 PENDING 的信息量是否足够给 Coordinator：
- 是否给出选项
- 是否给出描述分析
- 是否给出可问 accountant 的问题

### 5. 下游职责边界

高置信度结果应足够交给 JE Generator。
PENDING 结果应足够交给 Coordinator。

---

## 输出要求

必须严格遵循：
- `dry-run-pipeline-workflow/references/handoff_schema.md`

并满足以下约束：
- `node_id` 必须是 `node3_ai_classifier`
- 高置信度交易放入 `outputs.classified_transactions`
- PENDING 交易放入 `outputs.pending_transactions`
- `outputs.next_node_transactions` 必须为 `[]`
- `classification.classified_by` 使用 `ai_high_confidence`

在 `Analyst Notes` 中，简要说明：
- 最大的置信度判定风险在哪里
- 哪些 pending 信息对 Coordinator 来说还不够
