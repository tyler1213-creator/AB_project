# JE Generation Node — Stage 1：功能意图

## 1. Stage 范围

本 Stage 1 文档定义 `JE Generation Node` 的功能意图。

它只说明这个节点为什么存在、单一核心责任是什么、明确不负责什么、位于 workflow 的什么位置、哪些下游行为依赖它，以及哪些内容已知或未决定。

本阶段不定义 schema、字段契约、对象结构、存储路径、执行算法、测试矩阵、实现任务、旧系统替代映射或 legacy 约束迁移。

## 2. 节点为什么存在

新系统的上游节点负责形成当前交易的处理结果：结构性确定结果、deterministic rule result、case-supported runtime result、pending 后回收的 accountant clarification，或 review 中 accountant 批准 / 修正后的结果。

这些结果仍然不是 journal entry。

`JE Generation Node` 存在的原因，是把已经具备当前交易落账 authority 的分类 / 税务处理结果，转换成可审计、可入账、借贷平衡的 double-entry journal entry。

它把“这笔交易应该如何分类”的会计判断，与“如何把该判断机械转换为借贷分录”的计算职责分开。

没有这个节点，下游 `Transaction Logging Node` 和最终输出只能看到分类结论，而不能看到可验证的会计分录结果。

## 3. 核心责任

`JE Generation Node` 是一个 **pure journal-entry computation node**。

它的单一核心责任是：

> 将当前交易已经 finalizable 的 accounting outcome 转换为借贷平衡、税务处理一致、可供后续 audit logging 和输出使用的 journal entry；如果输入尚不能 finalization，则暴露不能生成 JE 的原因，而不是自行补业务判断。

它只做当前交易的分录计算与一致性检查。

它不创造分类 authority，不创造 tax authority，不创造 accountant approval，不创造长期记忆。

## 4. 明确不负责什么

`JE Generation Node` 不替代上游 workflow nodes。

它不负责：

- evidence intake 或客观结构标准化
- 分配或复用 `transaction_id`
- profile-backed structural match
- entity resolution
- deterministic rule match
- case-based runtime judgment
- pending clarification 提问
- accountant-facing review decision capture

它消费上游已经形成并具备相应 authority 的 current outcome，而不是重做这些职责。

它不负责会计业务判断。

它不能自行：

- 选择 COA 科目
- 判断业务用途
- 判断 HST/GST 是否适用
- 判断 tax treatment
- 判断 case precedent 是否足以支持自动分类
- 把模糊 accountant response 解释成明确分类
- 把未确认系统建议包装成 finalizable outcome

它不负责审计日志或长期记忆。

它不负责：

- 写入 `Transaction Log`
- 写入 `Case Log`
- 写入或修改 `Entity Log`
- 写入或修改 `Rule Log`
- 写入或批准 `Governance Log` mutation
- 修改 `Profile`
- 批准、执行或写入 rule / entity / alias / role / automation-policy candidate
- 把本次分录结果沉淀为长期客户知识

它不负责最终报告展示。

它可以为输出层提供 journal entry 结果，但不负责 report layout、accountant-facing review package 或最终 export。

## 5. Workflow 位置

`JE Generation Node` 位于当前交易 outcome 已具备 finalization 条件之后、final transaction logging 之前。

概念顺序是：

```text
finalizable current transaction outcome
→ JE Generation Node
→ journal entry result or JE-blocked reason
→ Transaction Logging Node / output flow / downstream completion workflow
```

它通常消费来自以下路径的 finalizable outcome：

- `Profile / Structural Match Node` 形成的结构性确定结果
- `Rule Match Node` 形成的 deterministic rule-handled result
- `Case Judgment Node` 形成且被当前 authority 允许继续的 case-supported result
- `Coordinator / Pending Node` 回收 clarification 后形成的可继续处理语境
- `Review Node` 捕捉的 accountant-approved 或 accountant-corrected current outcome

但 Stage 1 不冻结 exact handoff：哪些高可信系统结果可以无需逐笔 review 直接进入 JE，哪些必须先经 `Review Node`，留到后续阶段定义。

本节点不能在 pending、review-required、authority-blocked、conflicting evidence 或 not-approved 状态下自行生成 journal entry。

## 6. 下游依赖

`Transaction Logging Node` 依赖本节点产出的 journal entry result，把最终处理结果和审计轨迹写入 audit-facing `Transaction Log`。`JE Generation Node` 本身不写 `Transaction Log`。

最终输出 / report flow 依赖本节点产出的 journal entry，使 accountant 或客户交付物可以看到可入账的借贷结果，而不只是分类标签。

`Review Node`、`Coordinator / Pending Node` 或相关上游 workflow 可能依赖本节点暴露的 JE-blocked reason，处理分类、税务、金额、authority 或配置不一致的问题。

`Case Memory Update Node` 可以依赖已完成交易的 final outcome 和 JE completion context，但本节点不决定哪些结果应沉淀为 case memory。

## 7. 已确定内容

Stage 1 已确定以下内容：

- `JE Generation Node` 是 pure journal-entry computation node。
- 它位于 finalizable current outcome 之后、`Transaction Logging Node` 之前。
- 它把已具备当前交易落账 authority 的 accounting outcome 转换为 double-entry journal entry。
- 它必须保持借贷平衡和 tax treatment 一致性。
- 它不选择 COA 科目。
- 它不判断 HST/GST 是否适用。
- 它不替 accountant 作最终业务决定。
- 它不生成 accountant approval。
- 它不写 `Transaction Log`。
- 它不写或修改 Entity / Case / Rule / Governance memory。
- 它不执行 rule promotion、entity governance、profile update 或长期客户知识沉淀。
- 如果当前交易尚不能 finalization，它应暴露不能生成 JE 的原因，而不是自行猜测。

## 8. Open Boundaries

以下问题留到后续阶段，不在 Stage 1 冻结：

- 哪些 upstream outcome 可以被视为 `finalizable current transaction outcome`。
- `Review Node` 是否覆盖所有 JE 前交易，还是只覆盖 review-required / sampled / governance-candidate items。
- 高可信 structural / rule / case-supported result 是否可以不经逐笔 accountant review 直接触发 JE。
- accountant approval、correction、rejection、still-pending 与 JE Generation 的 exact handoff contract。
- JE-blocked reason 应返回哪个上游 workflow，或进入哪个 review / pending flow。
- split、refund、reversal、multi-line、tax-included / tax-excluded、zero-tax、partial-tax 等复杂分录类别的精确边界。
- exact input / output schema、字段名、对象结构、routing enum、执行算法、测试矩阵和 coding-agent task contract。
