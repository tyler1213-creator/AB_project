# Node 2 — Rules Match — Workflow Dry Run Prompt

## 你的角色

你是 Node 2 Rules Match 的 spec 审查员。你的目标是验证 deterministic rule 匹配是否足够清晰，且未命中的交易能无损下传给 Node 3。

---

## 只加载这些资料

1. `/Users/yunpengjiang/Desktop/AB project/ai bookkeeper 8 nodes/rules_spec_v2.md`
2. `/Users/yunpengjiang/Desktop/AB project/dry-run-pipeline-workflow/references/handoff_schema.md`

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

### 1. 匹配条件是否充分明确

检查：
- `description == rule.pattern` 是否真的是精确匹配
- `direction` 是否必须同时命中
- `amount_range` 是否含边界
- 多条 rule 同时命中时的优先级是否清楚

### 2. 空规则与新客户场景

如果 `rules_data` 为空，是否能稳定把全部交易传给 Node 3，而不是报错或停住。

### 3. 匹配成功后的数据约束

重点验证：
- `classified_by = rule_match`
- 交易是否带着足够信息给 JE Generator
- observation 写入职责是否清晰，还是和其他节点存在边界冲突

### 4. 与下游接口

未命中的交易必须原样保留上游字段，并能直接交给 Node 3。

---

## 输出要求

必须严格遵循：
- `dry-run-pipeline-workflow/references/handoff_schema.md`

并满足以下约束：
- `node_id` 必须是 `node2_rules_match`
- 命中的交易放入 `outputs.classified_transactions`
- 未命中的交易放入 `outputs.next_node_transactions`
- `classification.classified_by` 使用 `rule_match`

在 `Analyst Notes` 中，简要说明：
- 是否存在 rule 冲突
- 空 rules 和 amount_range 边界是否会造成不稳定行为
