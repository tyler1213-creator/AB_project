# Case Judgment Node — Stage 1：功能意图

## 1. Stage 范围

本 Stage 1 文档定义 `Case Judgment Node` 的功能意图。

它只说明这个节点为什么存在、单一核心责任是什么、明确不负责什么、位于 workflow 的什么位置、哪些下游行为依赖它，以及哪些问题留到 Stage 2。

本阶段不定义 schema、字段契约、存储路径、执行算法、测试矩阵或实现任务。

## 2. 节点为什么存在

新系统不能把 rule miss 当成可以直接裸猜的许可，但也不应该把所有 rule miss 交易都直接推给人工。

`Case Judgment Node` 存在于这两者之间。

当结构性匹配和 deterministic rule 都不能完成当前交易时，系统仍然可能拥有有价值的当前证据、entity/profile context、历史案例和客户专属知识。这个节点使用这些 context 判断当前交易是否可以进入 operational classification 路径，还是必须进入 pending / review。

它的目的，是在 runtime 层面平衡自动化能力和会计审慎性。

## 3. 核心责任

`Case Judgment Node` 是一个 **case-based runtime judgment gate**。

它的单一核心责任是：

> 在结构性确定处理和 rule match 都不能直接完成交易后，判断当前交易是否有足够的 case-supported 和 evidence-supported 基础进入 operational classification，还是必须进入 pending / review。

它只对当前交易做 runtime judgment。

它不创造 durable authority。它不批准治理变化。它不把一次 runtime outcome 直接变成长期记忆或 deterministic rule。

## 4. 明确不负责什么

`Case Judgment Node` 不替代上游确定性或身份识别工作。

它不负责：

- `Profile / Structural Match`
- `Entity Resolution`
- `Rule Match`

它消费这些上游结果，而不是吸收这些上游职责。

它不负责人类交互或最终审核 authority。

它不负责：

- 直接向 accountant 提问
- 批准或修正最终 review outcome
- 执行 `Review Node` 的职责
- 执行 `Governance Review Node` 的职责

它不负责后续执行或审计落盘。

它不负责：

- 生成 journal entries
- 写入 `Transaction Log`
- 直接把本次 runtime judgment 固化成长期案例

它不直接修改长期记忆或治理 authority。

它不能直接：

- 向 `Entity Log`、`Case Log`、`Rule Log` 或 `Governance Log` 写入 durable changes
- 批准 alias、role、entity 或 rule 变化
- promote、modify、delete 或 downgrade rules
- 放宽 automation policy
- 执行 entity merge / split
- 做 governance-level authority changes

它可以产生 runtime rationale 或 candidate signals，但任何 durable memory update 或 governance action 都属于后续 review、memory update 或 governance workflow nodes。

## 5. Workflow 位置

`Case Judgment Node` 位于 `Rule Match Node` 之后。

它只在以下条件下进入：

- 结构性确定处理没有已经完成当前交易；并且
- deterministic rule matching 没有产生适用结果。

它消费上游 workflow nodes 已经准备好的 context，包括当前 evidence、profile/structural context、entity resolution context、rule-match outcome、case memory 和 customer knowledge。

它是 runtime decision gate，不是 governance gate。

它不能回头重做上游节点的职责。

## 6. 下游依赖

如果 judgment 足够稳定，交易可以继续进入 operational classification 方向，并在后续确认后支持 review、journal entry generation、transaction logging 和 case-memory handling。

如果 judgment 不够稳定，`Coordinator / Pending Node` 依赖这个节点给出的 pending reason 和 context summary，向 accountant 提出更聚焦的问题。

`Review Node` 可以使用这个节点的 rationale 来审核、批准或修正系统结果。

`Case Memory Update Node` 和 `Governance Review Node` 可以消费后续已确认结果或 candidate signals，但不能把这个节点的 runtime judgment 直接当成长期 memory mutation 或 governance approval。

## 7. 已确定内容

Stage 1 已确定以下内容：

- 这个节点是 `case-based runtime judgment gate`。
- 它在结构性确定处理和 rule matching 都不能完成交易之后运行。
- 它使用当前 evidence、entity/profile context、case memory 和 customer knowledge 做 runtime judgment。
- 它判断交易可以进入 operational classification，还是必须进入 pending / review。
- 它不替代上游 matching、identity 或 rule responsibilities。
- 它不直接向 accountant 提问。
- 它不生成 journal entries。
- 它不写 `Transaction Log`。
- 它不直接修改长期 entity、case、rule 或 governance memory。
- 它不批准 governance-level changes。
- 它的下游影响是支持 operational classification、pending handling、review、audit trail formation 和后续 memory/governance workflows，但不拥有这些下游职责。

## 8. 留到 Stage 2 的问题

以下问题有意不在 Stage 1 解决：

- 哪些 evidence categories 可以支持 operational classification。
- 哪些情况必须进入 pending。
- runtime rationale 与 candidate signals 的边界。
- 这个节点可以读取哪些 logs / memory stores。
- 它可以把哪些 memory 或 governance changes 作为 candidates 提出。
- 哪些 memory 或 governance changes 它绝不能直接写入。
- accountant authority 的具体交接边界。
- governance authority 的具体交接边界。
- insufficient evidence、ambiguous evidence 或 conflicting evidence 下的行为。
