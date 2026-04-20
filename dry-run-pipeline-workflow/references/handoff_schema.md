# Dry Run Pipeline Workflow — 结构化 Handoff Schema

每个 subagent 的输出都必须同时满足两件事：

1. 有简短的人类可读总结
2. 有一个严格结构化的 `handoff_payload`，供 orchestrator 提取和路由

---

## 必须输出的外层格式

````md
## [节点名称] — 分析结果

```yaml
handoff_payload:
  node_id: ""
  status: completed
  summary:
    processed_count: 0
    classified_count: 0
    forwarded_count: 0
    pending_count: 0
  outputs:
    next_node_transactions: []
    classified_transactions: []
    pending_transactions: []
    transaction_log_candidates: []
    artifacts: {}
  issues:
    bugs: []
    interface_issues: []
    spec_ambiguities: []
  notes: []
```

### Analyst Notes
- 用 3-8 条要点总结本节点的关键发现
````

---

## 字段说明

### 1. `node_id`

固定使用以下值之一：
- `data_preprocessing`
- `node1_profile_match`
- `node2_rules_match`
- `node3_ai_classifier`
- `je_generator`
- `coordinator`
- `output_report`
- `review_agent`

### 2. `status`

允许值：
- `completed`
- `completed_with_issues`
- `blocked`

### 3. `summary`

- `processed_count`: 本节点实际检查的交易数或场景数
- `classified_count`: 本节点完成分类的交易数
- `forwarded_count`: 传给下一功能节点的交易数
- `pending_count`: 本节点输出为 pending / unresolved 的数量

### 4. `outputs`

#### `next_node_transactions`

传递给下一个功能节点的交易列表。必须保留所有上游附加字段。

#### `classified_transactions`

本节点已给出明确分类结果的交易。每笔至少包含：
- `transaction`
- `classification`
- `evidence`

#### `pending_transactions`

本节点决定暂不自动完成的交易。每笔至少包含：
- `transaction`
- `pending_reason`
- `questions_or_options`

#### `transaction_log_candidates`

已经足够接近 Transaction Log 结构的数据，通常由 JE Generator 或 Coordinator 产出。

#### `artifacts`

用于非交易类输出，例如：
- `report_draft`
- `review_summary`
- `scenario_results`

### 5. `issues`

#### `bugs`

每项使用以下字段：
- `id`
- `severity`
- `title`
- `description`
- `trigger`
- `impact`
- `spec_refs`
- `suggestion`

#### `interface_issues`

每项使用以下字段：
- `id`
- `description`
- `upstream_provided`
- `expected`
- `impact`

#### `spec_ambiguities`

每项使用以下字段：
- `id`
- `description`
- `spec_text`
- `interpretation_a`
- `interpretation_b`
- `recommendation`

### 6. `notes`

字符串数组。写补充观察、下游注意事项、默认值说明。

---

## 交易对象最小契约

如果某个数组里放的是交易对象，尽量包含以下字段：

```yaml
transaction_id: ""
date: ""
description: ""
raw_description: ""
amount: 0
direction: debit
account: ""
currency: CAD
balance: null
bs_source: ""
receipt: null
cheque_info: null
supplementary_context: null
```

如果字段未知，写 `null` 或空字符串，不要自行省略关键字段。

---

## 分类对象最小契约

```yaml
classification:
  account: ""
  hst: ""
  classified_by: ""
  reasoning: ""
```

---

## 使用规则

1. 没有内容的数组写 `[]`，不要写“无”
2. `artifacts` 没有内容时写 `{}`
3. 不要把上游交易改写成摘要文字后再传递
4. 人类可读说明要短，结构化 payload 才是正式 handoff
5. Bug 编号建议沿用节点前缀，如 `DP-001`、`N1-001`
