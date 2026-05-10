# Knowledge Compilation Node — Stage 1：功能意图

## 1. Stage 范围

本 Stage 1 文档定义 `Knowledge Compilation Node` 的功能意图。

它只说明这个节点为什么存在、单一核心责任是什么、明确不负责什么、位于 workflow 的什么位置、哪些下游行为依赖它，以及哪些内容已知或未决定。

本阶段不定义 schema、字段契约、对象结构、存储路径、执行算法、测试矩阵、实现任务、旧系统替代映射或 legacy 约束迁移。

## 2. 节点为什么存在

新系统的长期知识分散在多层 durable stores 中：

- `Entity Log` 回答“这是谁、有哪些 alias / role / authority / automation policy”。
- `Case Log` 回答“过去真实完成案例怎样处理、当时证据和例外是什么”。
- `Rule Log` 回答“哪些 deterministic rules 已被批准并可执行”。
- `Governance Log` 回答“长期记忆和自动化权威为什么发生变化、哪些被批准 / 拒绝 / 暂缓”。
- `Transaction Log` 保存最终审计轨迹，但不参与 runtime decision，也不是学习层。

这些 stores 各自有清晰 authority，但人和 agent 不应每次都从原始记忆层重新拼接客户语境。

`Knowledge Compilation Node` 存在的原因，是把 entity、case、rule、governance 及必要审计背景编译成人和 agent 可读的客户知识摘要，使后续判断、review、治理和维护能快速理解客户常见模式、例外、风险和未解决边界。

它解决的是“如何让长期记忆可读、可解释、可导航”，不是“如何创造新的会计 authority”。

## 3. 核心责任

`Knowledge Compilation Node` 是一个 **durable-knowledge summarization node**。

它的单一核心责任是：

> 从已存在的 durable memory / log sources 中编译客户知识摘要，表达稳定事实、常见案例模式、已批准规则、治理历史、例外条件、风险提示和开放边界，供 humans 和 agents 读取；同时保持摘要不成为 deterministic rule source、accounting authority 或 governance approval。

它负责“把已存在的客户知识变得可读和可用”。

它不负责“决定当前交易怎样处理”，也不负责“把摘要反向写成权威记忆变化”。

## 4. 明确不负责什么

`Knowledge Compilation Node` 不替代 runtime workflow nodes。

它不负责：

- evidence intake 或客观结构标准化
- 分配或复用 `transaction_id`
- profile-backed structural match
- entity resolution
- deterministic rule match
- case-based runtime judgment
- pending clarification 提问
- accountant-facing current-transaction review decision
- journal entry generation
- final transaction logging
- completed-transaction case memory write
- governance approval
- post-batch lint 判断

它消费这些节点和 durable stores 的结果，而不是重做这些职责。

它不负责会计业务判断。

它不能自行：

- 选择或修正 COA 科目
- 判断 HST/GST treatment
- 判断业务用途
- 判断某个 case precedent 是否足以完成当前交易
- 判断某个 rule 是否命中当前交易
- 把自然语言摘要当作当前交易的 final outcome

它不负责长期 authority mutation。

它不能直接：

- 修改 `Profile`
- 修改 stable `Entity Log` authority
- 写入或修改 `Case Log`
- 写入或修改 `Rule Log`
- 批准或修改 `Governance Log`
- approve / reject alias
- confirm role
- create stable entity authority
- merge / split entity
- create / promote / modify / delete / downgrade active rule
- upgrade or relax automation policy
- 把 `new_entity_candidate` 升级成稳定实体

它不把 transient handoff、候选队列、review draft、report draft 或 lint finding 称为 `Log`。只有写入 durable `Knowledge Log / Summary Log` 的客户知识摘要才属于本节点的 durable 输出语义。

## 5. Workflow 位置

`Knowledge Compilation Node` 位于长期记忆形成或治理处理之后，面向后续 runtime、review、governance 和 maintenance 读取。

概念顺序是：

```text
Entity / Case / Rule / Governance / completed audit history changes
→ Knowledge Compilation Node
→ Knowledge Log / Summary Log
→ future Entity Resolution / Case Judgment / Review / Governance / Post-Batch Lint context
```

它可以在初始化阶段或批后阶段运行，也可以在相关 durable memory 发生变化后被触发；exact trigger 留到后续阶段冻结。

它不是 runtime decision gate。即使未来 runtime 节点读取客户知识摘要，摘要也只能作为可读背景，不能替代源 memory / logs 的 authority。

## 6. 下游依赖

`Entity Resolution Node` 可以读取客户知识摘要作为辅助语境，理解客户常见对象、别名风险或历史关系，但不能用摘要替代 `Entity Log` authority。

`Rule Match Node` 不能把客户知识摘要当作 active rule、rule condition 或 rule authority。

`Case Judgment Node` 可以读取客户知识摘要来理解历史案例模式、例外和风险，但仍必须回到 `Case Log`、current evidence 和 authority boundary 判断当前交易是否足够稳定。

`Review Node` 可以使用摘要帮助 accountant 快速理解客户背景、常见处理、例外、治理风险和未解决问题，但摘要不等于 accountant approval。

`Governance Review Node` 可以使用摘要理解候选的业务背景和历史变化，但正式治理仍依赖 source evidence、current memory state 和 accountant / governance authority。

`Post-Batch Lint Node` 可以读取摘要作为检查背景，但 lint finding、summary wording 或 repeated summary pattern 都不能直接变成 rule 或 authority change。

未来 humans 和 agents 可以用 `Knowledge Log / Summary Log` 快速恢复客户语境，但必须知道它是编译视图，不是源权威。

## 7. 已确定内容

Stage 1 已确定以下内容：

- `Knowledge Compilation Node` 是 durable-knowledge summarization node。
- 它把 entity、case、rule、governance 历史及必要审计背景编译成人和 agent 可读的客户知识摘要。
- 它的 durable 输出是 `Knowledge Log / Summary Log` 语义。
- 摘要帮助后续 humans 和 agents 理解常见模式、例外、风险和开放边界。
- 摘要不作为 deterministic rule source。
- 摘要不替代 `Entity Log`、`Case Log`、`Rule Log`、`Governance Log`、`Evidence Log` 或 `Transaction Log` 的 source authority。
- 它不处理当前交易分类、JE、pending、review approval 或 transaction logging。
- 它不执行 case memory write。
- 它不批准 entity、alias、role、rule、automation policy 或 governance 变化。
- `Transaction Log` 可以作为已完成交易审计背景来源，但不因此变成 runtime decision source 或学习层。

## 8. Open Boundaries

以下问题留到后续阶段，不在 Stage 1 冻结：

- Knowledge Compilation 的 exact trigger：onboarding seed、批后定期编译、durable memory mutation 后增量编译，或组合模式。
- `Knowledge Log / Summary Log` 的 exact scope：客户级总摘要、entity-level 摘要、case-pattern 摘要、governance summary 是否分层。
- 摘要 staleness、supersession、versioning 和 refresh 的 exact behavior。
- 摘要与 source logs 冲突时的 exact source-precedence 和 warning contract。
- rejected / deferred governance decision、unresolved risk、lint finding 是否以及如何进入摘要。
- Knowledge Compilation 与 `Post-Batch Lint Node` 对风险摘要、监控发现和候选提示的 exact split。
- downstream nodes 读取摘要时必须同时读取哪些 source authority。
- exact input / output schema、字段名、对象结构、routing enum、存储路径、执行算法、测试矩阵和 coding-agent task contract。
