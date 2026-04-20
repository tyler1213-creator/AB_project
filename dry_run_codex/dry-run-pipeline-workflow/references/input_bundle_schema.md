# Dry Run Pipeline Workflow — 输入包约定

本文件定义 orchestrator 传给每个 subagent 的输入包结构，目标是让节点只看到当前需要的信息，而不是整条 pipeline 的长上下文。

---

## 通用输入槽位

每个 subagent prompt 都由以下 4 个输入槽位组成：

### 1. `{{node_input}}`

当前节点必须处理的核心输入。只放本节点需要的数据。

示例：
- Data Preprocessing: `source_bundle`
- Node 1: 标准化交易 + profile_data
- Node 2: 未匹配交易 + rules_data
- Node 3: 未匹配交易 + observations_data + profile_data + coa_data
- Output Report: transaction_log_candidates

### 2. `{{client_context}}`

客户级上下文，通常包含：

```yaml
province: Ontario
hst_registered: true
hst_rate: 13%
business_type: Corporation
profile_data: {}
rules_data: []
observations_data: []
coa_data: []
```

### 3. `{{upstream_handoff}}`

上游节点的结构化输出。默认传最近一个相关节点的 `handoff_payload`。

目的：
- 追溯来源
- 检查接口问题
- 必要时复用上游 notes / issues

不要把多轮上游全文都塞给下游，只传与当前节点相关的最近 handoff。

### 4. `{{run_constraints}}`

本轮运行约束，例如：
- 只测试指定节点
- 要优先验证某个已知 bug
- 用户给出的额外业务背景

---

## `source_bundle` 建议结构

```yaml
source_bundle:
  files:
    - path: ""
      file_type: pdf
      notes: ""
  structured_candidates: []
  source_notes: []
  explicit_unknowns: []
```

`structured_candidates` 可为空。即使 orchestrator 没有先提取出交易，Data Preprocessing 也应继续验证其解析路径。

---

## 默认值原则

1. 能留空就留空，不猜
2. 默认值必须可见，不要隐式注入
3. 如果某节点关键输入缺失，应在 `interface_issues` 中明确指出
