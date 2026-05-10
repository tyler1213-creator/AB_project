# Entity Resolution Node — Stage 1：功能意图

## 1. Stage 范围

本 Stage 1 文档定义 `Entity Resolution Node` 的功能意图。

它只说明这个节点为什么存在、单一核心责任是什么、明确不负责什么、位于 workflow 的什么位置、哪些下游行为依赖它，以及哪些内容已知或未决定。

本阶段不定义 schema、字段契约、对象结构、存储路径、执行算法、测试矩阵、实现任务、旧系统替代映射或 legacy 约束迁移。

## 2. 节点为什么存在

新系统的核心链条是：

```text
raw evidence
→ entity
→ case memory
→ rule
```

因此，非结构性交易进入 rule match 或 case judgment 之前，系统必须先回答一个更基础的问题：

> 这笔交易的 evidence 最可能指向哪个 counterparty / vendor / payee？

如果没有这一层，后续 rule 会重新绑回脆弱的字符串模式，case judgment 也会在不知道“这是谁”的情况下使用历史先例，导致错误自动化、错误 pending 问题和长期记忆污染。

`Entity Resolution Node` 存在的原因，是在普通交易进入 deterministic rule 或 case-based judgment 之前，建立当前交易的实体识别基础，同时显露新对象、角色未确认、多实体歧义和无法识别等风险。

## 3. 核心责任

`Entity Resolution Node` 是一个 **runtime counterparty / vendor / payee identity gate**。

它的单一核心责任是：

> 基于当前交易 evidence、已知实体记忆、alias / role authority 和必要上下文，判断当前非结构性交易指向哪个实体识别状态，并把该状态交给后续 rule、case、pending、review 和治理流程。

它回答“这是谁，或者为什么现在不能安全确认是谁”。

它不回答“这笔该怎么分”、 “是否应生成 rule”、 “是否批准 alias / role”、或“是否可以改变长期治理状态”。

## 4. 明确不负责什么

`Entity Resolution Node` 不负责 evidence intake 或交易身份。

它不负责：

- 解析原始材料
- 保存原始 evidence
- 分配或复用 `transaction_id`
- 判断同一交易或重复导入

这些分别属于 `Evidence Intake / Preprocessing Node` 和 `Transaction Identity Node`。

它不负责结构性交易处理。

它不负责：

- 判断内部转账
- 判断已知贷款还款
- 基于 stable `Profile` 完成结构性交易
- 把 profile candidate 升级成 stable profile truth

这些属于 `Profile / Structural Match Node` 或后续 profile / governance workflow。

它不负责 rule、case 或会计分类判断。

它不负责：

- 执行 deterministic rule match
- 判断 historical case precedent 是否足以支持分类
- 选择 COA 科目
- 判断 HST/GST 处理
- 生成 journal entry
- 判断当前交易是否可 operational classification

这些属于 `Rule Match Node`、`Case Judgment Node`、`JE Generation Node` 和后续 accounting workflow。

它不负责人类确认或治理批准。

它不能直接：

- 批准或拒绝 alias
- 确认 role
- 创建 stable entity authority
- merge / split entity
- 放宽 automation policy
- promote、modify、delete 或 downgrade active rule
- 批准 governance event
- 把 runtime 候选身份变成 accountant-confirmed memory

它不写 `Transaction Log`。
`Transaction Log` 保存最终处理结果和审计轨迹，只写和查询，不参与 runtime decision，也不是实体识别的学习来源。

## 5. Workflow 位置

`Entity Resolution Node` 位于 `Profile / Structural Match Node` 之后，`Rule Match Node` 之前。

概念顺序是：

```text
new runtime materials
→ Evidence Intake / Preprocessing Node
→ Transaction Identity Node
→ Profile / Structural Match Node
→ Entity Resolution Node
→ Rule Match Node
→ Case Judgment Node / downstream review and logging flow
```

它只处理已经过上游 evidence intake、transaction identity 和 profile / structural gate 的非结构性交易。

如果当前交易已经被稳定 profile facts 结构性处理，本节点不应再把它当作普通 vendor / payee / counterparty 识别。

如果当前交易无法由 profile 结构性确定，本节点为后续普通交易 workflow 提供 entity basis。

## 6. 下游依赖

`Rule Match Node` 依赖本节点输出的实体识别状态、alias / role authority 和 automation-policy 语境。只有当实体、alias、role/context 和 automation policy 都允许时，rule match 才能成为确定性路径。

`Case Judgment Node` 依赖本节点提供 identity basis。`new_entity_candidate` 可以作为当前交易的上下文信号，但不支持 rule match，不创建 durable authority，也不能自动创建或升级 rule。

`Coordinator / Pending Node` 依赖本节点说明实体歧义、角色未确认、证据不足或无法识别的原因，以便向 accountant 提出聚焦问题。

`Review Node` 和 `Governance Review Node` 可以使用本节点产生的候选身份、alias、role、merge/split 或 automation-risk 信号，但这些信号不等于 approval。

`Case Memory Update Node` 可以在交易完成后消费已确认结果或候选信号，决定是否沉淀 case 或提出 entity / alias / role / rule 候选；本节点的 runtime 识别本身不是长期 memory mutation。

## 7. 已确定内容

Stage 1 已确定以下内容：

- `Entity Resolution Node` 是 runtime counterparty / vendor / payee identity gate。
- 它位于 `Profile / Structural Match Node` 之后、`Rule Match Node` 之前。
- 它只处理未被结构性路径完成的非结构性交易。
- 它使用当前 evidence、Entity Log、alias / role authority 和必要上下文识别对象。
- 它输出当前交易的实体识别状态，而不是会计分类结论。
- 它必须区分已安全识别、角色未确认、新实体候选、多实体歧义和无法识别等状态。
- `new_entity_candidate` 不天然阻断当前交易后续 case-based judgment，但不能支持 rule match，不能创建 stable entity authority，也不能自动创建或升级 rule。
- 它不执行 rule match、case judgment、COA / HST 判断或 journal entry generation。
- 它不写 `Transaction Log`。
- 它不批准 alias、role、entity merge/split、automation policy 或 rule / governance changes。

## 8. Open Boundaries

以下问题留到后续阶段，不在 Stage 1 冻结：

- 哪些 evidence categories 足以支持 stable entity resolution。
- alias status、role authority 和 automation policy 如何精确限制 downstream eligibility。
- `new_entity_candidate` 在 runtime 中只作为 handoff signal，还是可以创建待治理 candidate memory；exact write locus 尚未冻结。
- 多实体歧义、角色未确认、rejected alias、弱证据和冲突 evidence 的 precise downstream path。
- Entity Resolution 是否以及何时可触发补证据、人工确认或 governance candidate。
- entity resolution confidence 的语义边界和下游消费方式。
- exact input / output schema、字段名、routing enum 和执行算法。
