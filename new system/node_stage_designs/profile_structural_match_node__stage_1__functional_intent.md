# Profile / Structural Match Node — Stage 1：功能意图

## 1. Stage 范围

本 Stage 1 文档定义 `Profile / Structural Match Node` 的功能意图。

它只说明这个节点为什么存在、单一核心责任是什么、明确不负责什么、位于 workflow 的什么位置、哪些下游行为依赖它，以及哪些内容已知或未决定。

本阶段不定义 schema、字段契约、对象结构、存储路径、执行算法、测试矩阵、实现任务、旧系统替代映射或 legacy 约束迁移。

## 2. 节点为什么存在

新系统先认清“这是谁”和“过去类似情况怎么处理”，但并不是所有交易都应该先进入 entity resolution。

有些交易不是普通 vendor / payee / counterparty 交易，而是由客户结构事实直接决定含义的交易，例如：

- 内部账户之间的转账
- 已知贷款还款
- 其他由客户 `Profile` 中稳定结构事实可确定的交易

这些交易如果穿透到 `Entity Resolution Node`、`Rule Match Node` 或 `Case Judgment Node`，系统会把结构性事实误当成普通交易对象或历史先例问题，导致错误自动化、错误 pending 问题，甚至污染后续记忆。

`Profile / Structural Match Node` 存在的原因，是在 entity / rule / case 路径之前，先截住并处理可由客户结构事实确定的交易。

## 3. 核心责任

`Profile / Structural Match Node` 是一个 **profile-backed structural transaction gate**。

它的单一核心责任是：

> 基于已具备 authority 的客户结构事实，判断当前交易是否属于可确定的结构性交易；如果是，则给出结构性处理路径；如果不是，则把交易交给后续 entity-first workflow。

它处理的是结构性交易识别与结构性路径分流。

它不负责一般 vendor 识别，不负责历史案例判断，不负责把 profile 候选事实升级为稳定客户结构事实。

## 4. 明确不负责什么

`Profile / Structural Match Node` 不负责 evidence intake 或交易身份。

它不负责：

- 解析原始材料
- 保存 evidence
- 分配或复用 `transaction_id`
- 判断重复导入或同一交易

这些分别属于 `Evidence Intake / Preprocessing Node` 和 `Transaction Identity Node`。

它不负责非结构性对象识别。

它不负责：

- 识别普通 vendor、payee 或 counterparty 所属 entity
- 创建 stable entity
- 批准 alias、role 或 entity governance change
- 执行 entity merge / split

这些属于 `Entity Resolution Node` 或后续 governance workflow。

它不负责 rule、case 或 AI 分类判断。

它不负责：

- 执行 deterministic business rule match
- 使用 case memory 判断普通交易分类
- 判断历史先例是否适用
- 为非结构性交易选择 COA 科目或 HST/GST 处理

这些属于 `Rule Match Node`、`Case Judgment Node` 和后续 accounting workflow。

它不负责长期 profile governance。

它不能：

- 把 onboarding 或 runtime 中发现的 profile candidate 写成稳定 profile truth
- 自行批准新银行账户、内部转账关系、贷款关系或其他客户结构事实
- 放宽 automation policy
- 批准 governance-level change

它不写 `Transaction Log`。
`Transaction Log` 保存最终处理结果和审计轨迹，不参与 runtime decision，也不是本节点的运行时判断来源。

## 5. Workflow 位置

`Profile / Structural Match Node` 位于 `Transaction Identity Node` 之后，`Entity Resolution Node` 之前。

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

它消费上游已经整理的 objective transaction basis、evidence references、稳定交易身份，以及当前客户 `Profile` 中具备 authority 的结构事实。

它是 entity-first workflow 之前的结构性 gate。

如果当前交易可由稳定 profile facts 确定，本节点应阻止它继续被当作普通 vendor/entity 交易处理。
如果当前交易不能被结构性确定，本节点不应猜测，而应把交易交给后续 `Entity Resolution Node`。

## 6. 下游依赖

`Entity Resolution Node` 依赖本节点先排除结构性交易，否则内部转账、贷款还款或其他 profile-driven 交易可能被错误识别成普通 counterparty。

`Rule Match Node` 依赖本节点避免结构性交易进入普通 rule path。结构性交易不应靠普通 entity rule 来补救。

`Case Judgment Node` 依赖本节点提供结构性处理结果、未命中原因或结构性风险语境，以免把 profile 缺口误当成 case precedent 问题。

`Coordinator / Pending Node` 和 `Review Node` 依赖本节点暴露 profile 事实缺失、模糊或未确认的问题，向 accountant 请求聚焦确认。

`JE Generation Node` 依赖本节点区分结构性交易和普通收支交易，因为结构性交易的分录含义通常来自客户结构关系，而不是 vendor 分类。

`Case Memory Update Node` 和 `Governance Review Node` 可以消费本节点产生的候选信号，但不能把本节点 runtime 判断直接当成 profile mutation 或 governance approval。

## 7. 已确定内容

Stage 1 已确定以下内容：

- `Profile / Structural Match Node` 是 profile-backed structural transaction gate。
- 它位于 `Transaction Identity Node` 之后、`Entity Resolution Node` 之前。
- 它先处理内部转账、已知贷款还款和其他可由稳定客户结构事实确定的交易。
- 它只基于具备 authority 的 `Profile` 结构事实完成结构性处理。
- profile candidate、未确认关系或模糊结构信号不能被当成稳定 profile truth。
- 内部转账识别属于 bank-raw-signal 语义，不应被强行压成普通 canonical description / entity matching 问题。
- 它不做普通 entity resolution、rule match 或 case judgment。
- 它不做普通交易的 COA / HST / JE 业务判断。
- 它不写 `Transaction Log`。
- 它不直接修改 `Profile`、Entity / Case / Rule / Governance 等长期记忆。

## 8. Open Boundaries

以下问题留到后续阶段，不在 Stage 1 冻结：

- 哪些 profile facts 足以支持结构性确定处理。
- profile candidate 到 stable profile truth 的确认 workflow。
- 结构性未命中、结构性疑似、profile 缺失和 profile 冲突的精确下游路径。
- 结构性处理结果与后续 journal entry generation 的 exact contract。
- 本节点可以提出哪些 profile / governance candidate signals。
- 补充 evidence 或 accountant 回答后是否重新触发本节点，以及如何限制重跑边界。
- exact input / output schema、字段名、routing enum 和执行算法。
