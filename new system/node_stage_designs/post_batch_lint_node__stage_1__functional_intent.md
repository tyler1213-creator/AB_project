# Post-Batch Lint Node — Stage 1：功能意图

## 1. Stage 范围

本 Stage 1 文档定义 `Post-Batch Lint Node` 的功能意图。

它只说明这个节点为什么存在、单一核心责任是什么、明确不负责什么、位于 workflow 的什么位置、哪些下游行为依赖它，以及哪些内容仍未决定。

本阶段不定义 schema、字段契约、存储路径、执行算法、测试矩阵、implementation routing、阈值或编码任务。

## 2. 节点为什么存在

单笔交易 workflow 只能判断“这一笔是否能处理”。它很难可靠回答批次结束后才显现的问题：

- 两个 entity 是否可能其实是同一个对象。
- 一个 entity 是否被过度合并，需要拆分。
- 某条 active rule 是否最近频繁被 accountant 修正。
- 多个 completed cases 是否已经稳定到值得提出 rule 候选。
- 某个 entity 是否已经不适合继续保持当前自动化权限。

`Post-Batch Lint Node` 存在，是为了在批次结束后做系统健康检查，把单笔交易节点无法安全处理的跨交易、跨记忆层风险暴露出来。

它不是 runtime classification 节点。它是 batch-level monitoring / governance preparation 节点。

## 3. 核心责任

`Post-Batch Lint Node` 是一个 **post-batch automation-health and governance-signal gate**。

它的单一核心责任是：

> 在一个批次完成后，检查 entity、case、rule、review / intervention 和 governance 相关历史，识别需要 accountant / governance 关注的自动化健康风险、memory consistency 风险和 rule promotion / restriction 候选。

它关心的是未来自动化是否仍然安全，而不是重新决定已经完成交易的会计结果。

## 4. 明确不负责什么

`Post-Batch Lint Node` 不参与单笔交易 runtime decision。

它不负责：

- 识别当前交易 identity。
- 执行结构性匹配。
- 执行 rule match。
- 做 case-based runtime judgment。
- 生成 pending question。
- 审核或修正当前交易结果。
- 生成 journal entry。
- 写入单笔交易的 final `Transaction Log`。

它不拥有 accountant authority。

它不能：

- 替 accountant 批准 accounting decision。
- 把 lint finding 变成 accountant-confirmed fact。
- 把 review draft、handoff、queue、candidate 或 report draft 称为 `Log`。

它不拥有 rule governance authority。

它不能：

- create、promote、modify、delete 或 downgrade active rule。
- 把 repeated cases 自动升级为 active rule。
- 把 rule candidate 当作 deterministic rule source。
- 用 lint finding 直接改变 `Rule Log` authority。

它不拥有 entity merge / split authority。

它不能：

- 自动 merge entity。
- 自动 split entity。
- 自动批准 alias。
- 自动确认 role。
- 把 `new_entity_candidate` 变成 stable entity。

它不拥有放宽自动化权限的 authority。

它不能：

- upgrade automation policy。
- relax automation policy。
- 把 risk warning 解释成未来自动化放宽依据。

Active baseline 允许 lint pass 在受控边界内自动降低 entity `automation_policy`。这只是风险降低动作，不是 accountant approval、rule mutation 或 accounting decision。

## 5. Workflow 位置

`Post-Batch Lint Node` 位于批次结束后。

它依赖前序 workflow 已经形成足够的完成交易语境、review / intervention 语境、case memory 语境、rule / entity / governance 语境或候选信号。

它不在单笔交易主路径中阻塞当前交易处理。它也不回头重写已经完成交易的历史审计记录。

它的典型上游语境来自：

- 已完成交易的 audit history。
- Review / intervention 中暴露的 correction、confirmation 或 unresolved risk。
- Case Memory Update 提出的 case、entity、rule 或 automation-policy 候选。
- Governance Review 的已批准、拒绝、暂缓、限制或 auto-applied downgrade 语境。
- Knowledge Compilation 暴露的 summary mismatch、stale knowledge 或 unresolved boundary。

## 6. 下游依赖

`Review Node` 可以使用 lint finding，把跨交易风险或候选事项组织给 accountant 审核。

`Governance Review Node` 可以消费 lint finding 中的治理候选，例如 entity merge / split risk、alias / role issue、rule instability、case-to-rule candidate 或 automation-policy review need。

`Knowledge Compilation Node` 可以消费 lint finding，把 unresolved risk、monitoring concern 或已处理治理结果编译进客户知识摘要；但摘要不能因此成为 deterministic rule source。

未来的 `Entity Resolution Node`、`Rule Match Node` 和 `Case Judgment Node` 只会通过已经生效的 durable memory / governance changes 间接受影响。它们不能把 raw lint warning 当作 runtime authority。

Accountant 依赖这个节点获得批次级别的风险视图，而不是在每笔交易中反复发现同类问题。

## 7. 已确定内容

Stage 1 已确定以下内容：

- 这个节点是 batch-level health check，不是 runtime classification。
- 它在批次结束后运行，检查跨交易和跨记忆层风险。
- 它识别 entity merge / split risk、rule instability、case-to-rule candidate 和 automation risk。
- 它可以产生 review / governance / knowledge follow-up 语境。
- 它不能重写 `Transaction Log`。
- 它不能把 `Transaction Log` 变成 runtime decision source 或 learning layer。
- 它不能自动改变 active rule。
- 它不能自动批准 entity、alias、role、merge 或 split。
- 它不能 upgrade 或 relax automation policy。
- Active baseline 允许它在受控边界内自动降低 entity automation policy，并把该风险降低动作暴露给 review / governance。

## 8. 留到 Stage 2 的问题

以下问题有意不在 Stage 1 解决：

- 哪些条件触发 post-batch lint。
- 它消费哪些 input categories。
- 它输出哪些 conceptual categories。
- 哪些检查属于 deterministic code。
- 哪些比较或解释可以使用 LLM semantic judgment。
- 自动降级 automation policy 的 authority 边界。
- governance candidate 与 review-facing finding 的边界。
- memory/log read、candidate-only、limited mutation 和 no-mutation 边界。
- evidence insufficient、ambiguous 或 conflicting 时如何处理。
