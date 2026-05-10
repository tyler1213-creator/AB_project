# Coordinator / Pending Node — Stage 1：功能意图

## 1. Stage 范围

本 Stage 1 文档定义 `Coordinator / Pending Node` 的功能意图。

它只说明这个节点为什么存在、单一核心责任是什么、明确不负责什么、位于 workflow 的什么位置、哪些下游行为依赖它，以及哪些内容已知或未决定。

本阶段不定义 schema、字段契约、对象结构、存储路径、执行算法、测试矩阵、实现任务、旧系统替代映射或 legacy 约束迁移。

## 2. 节点为什么存在

新系统的上游节点会尽量在各自边界内完成确定性处理、entity resolution、rule match 和 case judgment。

但有些交易并不是系统完全无法理解，而是缺少一个关键 accountant clarification：

- 当前 evidence 缺失、低质量、无法配对或互相冲突。
- transaction identity、profile structure、entity、alias、role 或 rule authority 存在未确认问题。
- Case Judgment 认为当前证据不足以支持 operational classification。
- 当前问题需要 accountant 提供业务用途、对象身份、角色、结构事实或例外说明。

如果没有 `Coordinator / Pending Node`，系统会出现两种坏结果：

- 上游节点为了继续自动化而猜测。
- accountant 收到泛泛问题，无法看出系统到底卡在哪里。

`Coordinator / Pending Node` 存在的原因，是把上游已经定位出的不确定性转化为最小必要、可回答、可追溯的 accountant clarification，并把回答交回后续 workflow。

它不是新的分类节点。它是 pending 状态下的人机澄清桥。

## 3. 核心责任

`Coordinator / Pending Node` 是一个 **runtime clarification and intervention bridge**。

它的单一核心责任是：

> 在当前交易因证据不足、身份/结构/规则/案例判断不稳或需要 accountant 信息而不能继续安全处理时，向 accountant 获取聚焦确认，并把问答与补充 context 作为受限 intervention / handoff 交给后续 workflow。

它负责“问什么、为什么问、如何保留回答语境”。

它不负责“最终怎么分”、 “长期记忆是否改变”、 “规则是否升级”、或“治理事件是否批准”。

## 4. 明确不负责什么

`Coordinator / Pending Node` 不替代上游判断节点。

它不负责：

- evidence intake 或客观结构标准化
- 分配或复用 `transaction_id`
- profile-backed structural match
- entity resolution
- deterministic rule match
- case precedent judgment

它消费这些节点给出的 pending / review context，而不是重做它们的职责。

它不负责会计分类或分录生成。

它不能：

- 选择 COA 科目
- 判断 HST/GST 处理
- 生成 journal entries
- 把 accountant 的回答直接变成最终 review outcome

它不负责 durable memory 或 governance approval。

它不能直接：

- 修改 `Profile`
- 写入或修改 `Entity Log`
- 写入或修改 `Case Log`
- 写入或修改 `Rule Log`
- 写入或批准 `Governance Log`
- approve / reject alias
- confirm role
- create stable entity authority
- merge / split entity
- promote、modify、delete 或 downgrade active rule
- upgrade or relax automation policy

它不写 `Transaction Log`。
`Transaction Log` 保存每笔交易最终处理结果和审计轨迹，只写和查询，不参与 runtime decision，也不是 pending 澄清的运行时学习层。

它不把 transient handoff、问题队列、回答草稿、report draft 或候选变更称为 `Log`。只有进入 durable store 的 accountant 介入、提问、回答、修正和确认过程，才属于 `Intervention Log` 语境。

## 5. Workflow 位置

`Coordinator / Pending Node` 位于上游判断节点和 accountant-facing review / downstream completion flow 之间。

概念顺序是：

```text
upstream workflow context
→ pending / review-needed / clarification-needed handoff
→ Coordinator / Pending Node
→ accountant clarification
→ downstream review, reprocessing, completion, memory-update or governance workflow
```

在主交易路径中，它最典型地发生在 `Case Judgment Node` 判断不够稳定之后。

它也可以消费更早节点显露出的 pending context，例如：

- Evidence Intake 暴露的 missing / conflicting evidence。
- Transaction Identity 暴露的 same-transaction / duplicate uncertainty。
- Profile / Structural Match 暴露的 profile fact 缺失或结构事实冲突。
- Entity Resolution 暴露的 ambiguous entity、unresolved identity、unconfirmed role 或 alias authority 问题。
- Rule Match 暴露的 rule blocked、authority gap 或 review/governance-needed context。

本节点的定位不是替代这些上游节点，而是把它们已经表达清楚的卡点转化为 accountant 可以回答的问题。

## 6. 下游依赖

上游节点依赖 `Coordinator / Pending Node` 回收 accountant clarification 后，才能在受限边界内继续处理或保持 pending / review-required 状态。

`Case Judgment Node` 依赖本节点取得的补充业务语境、证据说明或 accountant clarification，判断当前交易是否仍需要 pending / review，或是否可以继续 operational classification path。

`Review Node` 依赖本节点保留的 accountant 介入语境，审核系统结果、人工修正和治理候选。

`Governance Review Node` 可以消费本节点捕捉到的 profile、entity、alias、role、rule 或 automation-policy 候选信号，但这些信号不等于 approval。

`Case Memory Update Node` 可以在交易完成后消费已确认结果和 intervention context，判断是否值得形成 case memory 或候选信号；本节点的问答本身不是 case memory approval。

`JE Generation Node` 和 `Transaction Logging Node` 只应依赖后续已确认或足够可信的处理结果，而不是把 pending 问答本身当作最终会计结论。

## 7. 已确定内容

Stage 1 已确定以下内容：

- `Coordinator / Pending Node` 是 runtime clarification and intervention bridge。
- 它在交易因证据、身份、结构、rule、case 或 authority 问题不能安全继续时介入。
- 它的核心职责是向 accountant 提出聚焦问题，并保留回答语境。
- 它不重新执行 evidence intake、transaction identity、structural match、entity resolution、rule match 或 case judgment。
- 它不做最终会计分类、HST/GST 判断或 journal entry generation。
- 它不写 `Transaction Log`。
- 它不直接修改 `Profile`、Entity / Case / Rule / Governance 等长期业务记忆。
- 它可以捕捉 profile、entity、alias、role、rule、case 或 governance 相关候选信号，但不能批准或落地这些变化。
- Accountant authority 和 durable governance changes 必须留给 Review / Governance Review / memory update workflow。

## 8. Open Boundaries

以下问题留到后续阶段，不在 Stage 1 冻结：

- accountant 回答后是否重新触发哪个上游节点，以及如何限制重跑边界。
- 哪些 accountant clarification 足以支持当前交易继续处理，哪些必须进入 Review Node。
- `Intervention Log` 的 exact contract 和与 Evidence Log 的边界。
- 补交 evidence 应由本节点直接接收、还是重新进入 Evidence Intake / Preprocessing Node。
- 多笔 pending 交易的问题聚合、去重和展示边界。
- review-required、governance-needed 和 ordinary pending 的 exact routing contract。
- exact input / output schema、字段名、routing enum 和执行算法。
