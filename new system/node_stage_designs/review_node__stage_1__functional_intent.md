# Review Node — Stage 1：功能意图

## 1. Stage 范围

本 Stage 1 文档定义 `Review Node` 的功能意图。

它只说明这个节点为什么存在、单一核心责任是什么、明确不负责什么、位于 workflow 的什么位置、哪些下游行为依赖它，以及哪些内容已知或未决定。

本阶段不定义 schema、字段契约、对象结构、存储路径、执行算法、测试矩阵、实现任务、旧系统替代映射或 legacy 约束迁移。

## 2. 节点为什么存在

新系统会在上游节点中形成多种系统结果：

- 结构性处理结果
- deterministic rule-handled result
- case-supported runtime judgment
- pending 后回收的 accountant clarification
- review-required context
- entity / alias / role / rule / automation-policy 等治理候选

这些结果不能都被系统直接落成最终会计输出或长期治理变化。

`Review Node` 存在的原因，是把系统已经形成的处理结果、人工介入语境、风险说明和候选事项放到 accountant authority 面前，让 accountant 审核、批准、修正或拒绝，而不是让上游 runtime 节点自行承担最终会计权威或 durable governance authority。

它是 accountant-facing final review gate，不是新的分类推理节点。

## 3. 核心责任

`Review Node` 是一个 **accountant-facing review and decision-capture gate**。

它的单一核心责任是：

> 将当前交易或批次中需要 accountant authority 的系统结果、人工澄清结果、风险说明和治理候选组织成可审核语境，并捕捉 accountant 的批准、修正、拒绝或继续待处理决定，交给后续 JE、logging、memory update 或 governance workflow。

它负责“把什么交给 accountant 审、accountant 决定了什么、这个决定应交给哪个后续 workflow”。

它不负责替 accountant 作业务决定，也不负责直接执行长期治理变化。

## 4. 明确不负责什么

`Review Node` 不替代上游 workflow nodes。

它不负责：

- evidence intake 或客观结构标准化
- 分配或复用 `transaction_id`
- profile-backed structural match
- entity resolution
- deterministic rule match
- case-based runtime judgment
- pending clarification 提问

它消费这些节点的结果、rationale、pending / review context 和候选信号，而不是重做它们的职责。

它不负责原始会计推理。

它不能自行：

- 选择 COA 科目
- 判断 HST/GST 处理
- 判断 case precedent 是否足以自动分类
- 把模糊 accountant response 解释成明确业务决定
- 把系统建议包装成 accountant approval

它不负责 journal entry 或最终审计落盘。

它不负责：

- 生成 journal entries
- 写入 `Transaction Log`
- 把 review package 本身当成最终审计记录
- 把 transient review queue、handoff、draft 或候选事项称为 `Log`

它不直接修改长期业务记忆或治理状态。

它不能直接：

- 修改 `Profile`
- 写入或修改 stable `Entity Log` authority
- 写入或修改 `Case Log`
- 写入或修改 `Rule Log`
- 直接批准或执行 `Governance Log` mutation
- approve / reject alias
- confirm role
- create stable entity authority
- merge / split entity
- create / promote / modify / delete / downgrade active rule
- upgrade or relax automation policy

高权限长期记忆变化属于 `Governance Review Node`、相关 memory update workflow 和 accountant / governance approval 边界。

## 5. Workflow 位置

`Review Node` 位于 accountant-facing review 位置，概念上在上游分类 / pending / candidate 形成之后、JE generation 和 final transaction logging 之前。

概念顺序是：

```text
upstream workflow results and candidates
→ Review Node
→ accountant approval / correction / rejection / still-pending decision
→ JE Generation Node / Transaction Logging Node / Case Memory Update Node / Governance Review Node
```

它可以消费来自以下节点的 review context：

- `Profile / Structural Match Node`
- `Entity Resolution Node`
- `Rule Match Node`
- `Case Judgment Node`
- `Coordinator / Pending Node`
- `Post-Batch Lint Node`
- 后续形成的 memory / governance candidate workflow

它不回头改变这些节点已经拥有或不拥有的 authority。

## 6. 下游依赖

`JE Generation Node` 依赖 `Review Node` 输出的 accountant-approved 或 accountant-corrected 当前交易处理语境，避免把未经确认或仍有争议的系统结果转换成 journal entry。

`Transaction Logging Node` 依赖后续完成的最终处理结果和 review / correction trace，写入 audit-facing `Transaction Log`。`Review Node` 本身不写 `Transaction Log`。

`Case Memory Update Node` 依赖 accountant-confirmed outcome、correction context 和 review rationale，判断哪些 completed transaction 可以沉淀为 case，哪些只能形成候选。

`Governance Review Node` 依赖 `Review Node` 暴露或整理的 entity、alias、role、rule、automation-policy 等治理候选和 accountant-facing review context。候选和 review context 不等于 durable governance mutation。

`Coordinator / Pending Node` 或相关上游节点可能依赖 `Review Node` 的 still-pending / insufficient-review decision，重新获取缺失信息或修正上游 context。

## 7. 已确定内容

Stage 1 已确定以下内容：

- `Review Node` 是 accountant-facing review and decision-capture gate。
- 它面向当前交易或批次中需要 accountant authority 的系统结果、人工澄清结果、风险说明和治理候选。
- 它捕捉 accountant 的批准、修正、拒绝或继续待处理决定。
- 它不重新执行 evidence intake、transaction identity、structural match、entity resolution、rule match、case judgment 或 pending question generation。
- 它不替 accountant 作最终业务决定。
- 它不生成 journal entries。
- 它不写 `Transaction Log`。
- 它不直接修改 `Profile`、Entity / Case / Rule / Governance 等长期业务记忆。
- 它可以把长期记忆或治理相关事项作为候选或 accountant-facing review context 交给后续 workflow。
- 高权限长期 memory / governance mutation 必须由 accountant / governance approval 和后续治理 workflow 处理。

## 8. Open Boundaries

以下问题留到后续阶段，不在 Stage 1 冻结：

- Review Node 是否覆盖每一笔交易的批次审核，还是只覆盖 review-required / sampled / governance-candidate items。
- accountant approval、correction、rejection 和 still-pending 的 exact routing contract。
- Review Node 与 `Governance Review Node` 对治理候选的精确分工：哪些只展示和捕捉意向，哪些进入正式治理审批。
- Review decision 如何影响 JE Generation 的触发边界。
- Review decision 与 `Intervention Log`、`Transaction Log`、`Governance Log` 的 exact persistence boundary。
- 多笔交易和多个治理候选如何聚合、排序、去重和展示。
- exact input / output schema、字段名、对象结构、routing enum 和执行算法。
