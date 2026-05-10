# Evidence Intake / Preprocessing Node — Stage 1：功能意图

## 1. Stage 范围

本 Stage 1 文档定义 `Evidence Intake / Preprocessing Node` 的功能意图。

它只说明这个节点为什么存在、单一核心责任是什么、明确不负责什么、位于 workflow 的什么位置、哪些下游行为依赖它，以及哪些内容已知或未决定。

本阶段不定义 schema、字段契约、对象结构、存储路径、执行算法、测试矩阵、实现任务、旧系统替代映射或 legacy 约束迁移。

## 2. 节点为什么存在

新系统是 evidence-first baseline。后续 entity resolution、rule match、case judgment、review 和 audit 都必须能回到原始证据，而不是只依赖被压缩后的交易描述或模型摘要。

`Evidence Intake / Preprocessing Node` 存在的原因，是把新交易进入系统时的原始材料先整理成可追溯、可传递、只含客观结构的 evidence foundation。

它解决的是入口层问题：

- 原始材料必须被保留和引用。
- 客观交易结构必须被统一到下游可消费的形式。
- 证据质量、缺失、冲突和配对状态必须在早期显露。
- 业务结论、身份结论和会计分类不能在入口层被提前伪造。

如果这一层混入业务判断，后续节点会把入口猜测误当成 evidence authority。
如果这一层没有整理客观结构，后续节点又会被迫重复解析、重复猜测和重复处理缺证据问题。

## 3. 核心责任

`Evidence Intake / Preprocessing Node` 是一个 **runtime evidence normalization and evidence foundation node**。

它的单一核心责任是：

> 接收主 workflow 中的新交易原始材料，保留可追溯 evidence，并统一客观结构，使后续节点可以基于同一组 evidence references 和 objective facts 继续处理。

它负责“证据进入系统时如何被整理”。

它不负责“这是谁”、 “这笔该怎么分”、 “是否可以自动落账”、或“哪些长期记忆应该被批准”。

## 4. 明确不负责什么

`Evidence Intake / Preprocessing Node` 不负责交易永久身份。

它不负责：

- 分配 `transaction_id`
- 判断是否为同一交易
- 处理重复导入的最终去重决策

这些属于 `Transaction Identity Node`。

它不负责结构性或语义性业务判断。

它不负责：

- 判断内部转账、贷款还款或其他 profile-driven 结构性交易
- 识别 counterparty / vendor / payee 所属的稳定 entity
- 判断 alias、role 或 entity status
- 执行 deterministic rule match
- 使用 case memory 形成分类建议
- 决定是否进入 pending、review 或 operational classification

它不负责会计结论。

它不能：

- 选择 COA 科目
- 判断 HST/GST 处理
- 生成 journal entry
- 批准 accountant review outcome

它不负责长期治理。

它不能：

- 写入或修改 `Entity Log`
- 写入或修改 `Case Log`
- 写入或修改 `Rule Log`
- 写入或批准 `Governance Log` 变化
- promote、modify、delete 或 downgrade active rule
- 批准 alias、role、entity merge / split 或 automation policy 变化

它不写 `Transaction Log`。
`Transaction Log` 是最终处理结果和审计轨迹，不参与 runtime decision，也不是 evidence intake 的写入目标。

## 5. Workflow 位置

`Evidence Intake / Preprocessing Node` 位于主 workflow 的入口侧。

它处理运行中新交易材料，发生在 `Transaction Identity Node` 之前，并为后续 workflow nodes 准备统一的 evidence foundation。

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

`Onboarding Node` 是初始化节点，不是本节点的常规 runtime 替代。
Onboarding 可以建立历史 evidence 和初始 memory context；本节点处理主 workflow 中新交易的常规 evidence intake。

## 6. 下游依赖

`Transaction Identity Node` 依赖本节点整理出的客观交易结构和原始 evidence references，用于分配稳定交易身份、识别同一交易和处理导入重复问题。

`Profile / Structural Match Node` 依赖本节点提供的客观交易事实和证据引用，判断是否存在结构性确定路径。

`Entity Resolution Node` 依赖本节点保留的原始 counterparty / vendor / payee 信号、相关附件证据和证据质量语境，判断当前交易可能指向哪个对象。

`Rule Match Node` 间接依赖本节点，因为 deterministic rule 只有在上游 identity、entity、alias、role 和 objective transaction basis 清楚时才可能安全执行。

`Case Judgment Node` 依赖本节点提供的 current evidence basis，用来判断历史案例是否适用、当前证据是否足够、风险是否被覆盖。

`Coordinator / Pending Node` 和 `Review Node` 依赖本节点暴露的缺失、模糊、冲突或低质量 evidence context，向 accountant 提出聚焦问题或支持人工审核。

后续审计和 memory update workflow 依赖本节点保留的 evidence traceability，但不能把本节点的入口整理视为会计结论或治理批准。

## 7. 已确定内容

Stage 1 已确定以下内容：

- `Evidence Intake / Preprocessing Node` 是主 workflow 的 runtime evidence 入口节点。
- 它的核心职责是保留可追溯 evidence，并统一客观结构。
- 它可以建立 evidence foundation，但不能保存业务结论。
- 它不分配 `transaction_id`，不处理最终去重决策。
- 它不做 profile / structural match、entity resolution、rule match 或 case judgment。
- 它不做会计分类、HST/GST 判断或 journal entry generation。
- 它不写 `Transaction Log`。
- 它不修改 Entity / Case / Rule / Governance 等长期业务记忆。
- 它不把 transient handoff、临时配对候选、解析草稿或 review draft 称为 `Log`。

## 8. Open Boundaries

以下问题留到后续阶段，不在 Stage 1 冻结：

- 原始 evidence 在本节点内何时被持久化，何时只作为待确认 intake result 传递。
- 新交易 evidence 与历史 onboarding evidence 的 exact linkage boundary。
- 支票、小票、合同或其他附件与交易的配对结果，哪些可以由本节点确定，哪些只能作为候选。
- 解析失败、部分解析、重复材料和补交材料的 precise workflow boundary。
- Evidence quality、conflict 和 missing evidence 由本节点表达到什么精度。
- 下游节点如何引用本节点产生的 evidence foundation。
