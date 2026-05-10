# Transaction Logging Node — Stage 1：功能意图

## 1. Stage 范围

本 Stage 1 文档定义 `Transaction Logging Node` 的功能意图。

它只说明这个节点为什么存在、单一核心责任是什么、明确不负责什么、位于 workflow 的什么位置、哪些下游行为依赖它，以及哪些内容已知或未决定。

本阶段不定义 schema、字段契约、对象结构、存储路径、执行算法、测试矩阵、实现任务、旧系统替代映射或 legacy 约束迁移。

## 2. 节点为什么存在

新系统的上游 workflow 会形成当前交易的处理路径、会计结果、review / intervention 语境、journal entry result 和治理候选。

这些内容如果只停留在 runtime handoff、review package、report draft 或节点输出里，就不能形成长期可追溯的审计记录。

`Transaction Logging Node` 存在的原因，是在当前交易完成 finalization 后，把本笔交易最终处理结果和关键审计轨迹写入 audit-facing `Transaction Log`。

它让系统以后能够回答：

- 这笔交易最终如何处理。
- 该结果来自哪条 workflow path。
- 哪些 evidence、rule、case、review、intervention 或 JE context 支持该结果。
- 之后即使 entity / rule / governance 状态变化，历史交易当时的处理依据仍可被追溯。

`Transaction Log` 是长期审计记录，不是学习层、运行时判断源、队列、草稿或候选池。

## 3. 核心责任

`Transaction Logging Node` 是一个 **final audit-trail persistence node**。

它的单一核心责任是：

> 在当前交易已经具备 final logging authority 后，把最终交易处理结果、journal entry completion context、上游 authority trace、evidence / review / intervention 引用和必要审计说明写入 audit-facing `Transaction Log`；同时拒绝把未完成、未批准、候选-only 或 governance-needed 内容伪装成最终审计记录。

它只负责当前交易的最终审计落盘。

它不重新做会计判断，不重新生成 JE，不创造长期业务记忆，不参与未来 runtime decision。

## 4. 明确不负责什么

`Transaction Logging Node` 不替代上游 workflow nodes。

它不负责：

- evidence intake 或客观结构标准化
- 分配或复用 `transaction_id`
- profile-backed structural match
- entity resolution
- deterministic rule match
- case-based runtime judgment
- pending clarification 提问
- accountant-facing review decision capture
- journal entry generation

它消费上游已经完成且具备 final logging authority 的 outcome、JE result、review / intervention trace 和 audit-support context，而不是重做这些职责。

它不负责会计业务判断。

它不能自行：

- 选择或修正 COA 科目
- 判断业务用途
- 判断 HST/GST tax treatment
- 判断 case precedent 是否适用
- 判断 rule 是否应命中
- 把模糊 accountant response 解释成 approval
- 把 JE-blocked reason 改写成可落账结果

它不负责 durable memory 或 governance mutation。

它不能直接：

- 修改 `Profile`
- 写入或修改 stable `Entity Log` authority
- 写入或修改 `Case Log`
- 写入或修改 `Rule Log`
- 写入或批准 `Governance Log` mutation
- approve / reject alias
- confirm role
- create stable entity authority
- merge / split entity
- create / promote / modify / delete / downgrade active rule
- upgrade or relax automation policy
- 把当前交易 outcome 直接变成长期客户知识

它不负责 output report。

它可以为最终输出提供已落盘或可追溯的审计语境，但不负责 report layout、review package、spreadsheet export 或客户交付物格式。

## 5. Workflow 位置

`Transaction Logging Node` 位于 `JE Generation Node` 和 final completion / output flow 之后，位于 `Case Memory Update Node`、后续 governance / knowledge compilation 语境之前或并行交接处。

概念顺序是：

```text
finalizable current transaction outcome
→ Review / JE Generation as required
→ journal entry result and audit-support context
→ Transaction Logging Node
→ audit-facing Transaction Log entry
→ Case Memory Update / Governance Review / output flow / post-batch workflows
```

正常情况下，它只在当前交易已经完成必要 review、具备 journal entry result，并且不再处于 pending、review-required、not-approved、conflicting 或 governance-blocked 状态时运行。

Stage 1 不冻结 exact handoff：哪些高可信系统结果可以直接进入 JE 和 final logging，哪些必须先经 `Review Node`，留到后续阶段定义。

## 6. 下游依赖

`Case Memory Update Node` 依赖已完成交易的 final outcome、review / correction trace 和审计语境，判断哪些内容可以沉淀为 case memory 或候选信号。`Transaction Logging Node` 本身不决定 case memory 是否写入。

`Governance Review Node` 可以依赖 `Transaction Log` 中的历史审计轨迹理解某笔交易当时为何这样处理，但治理变化必须由 governance workflow 执行。历史 `Transaction Log` 不因后续 entity merge/split、rule change 或 automation-policy change 被重写。

`Knowledge Compilation Node` 可以把已完成交易的审计历史作为可读摘要的背景来源，但摘要不能反过来成为 deterministic rule source。

`Post-Batch Lint Node` 可以查询 `Transaction Log` 发现 repeated corrections、rule instability、automation risk 或 case-to-rule 候选，但 lint / governance 结果不等于修改既有交易日志。

最终 output flow 可以使用 `Transaction Log` 或其审计语境展示最终结果，但 report draft、review package 或 export artifact 不是 `Transaction Log` 本身。

## 7. 已确定内容

Stage 1 已确定以下内容：

- `Transaction Logging Node` 是 final audit-trail persistence node。
- 它写入 audit-facing `Transaction Log`。
- `Transaction Log` 保存每笔交易最终处理结果和审计轨迹。
- `Transaction Log` 只写和查询，不参与 runtime decision，也不是学习层。
- 它位于 finalizable outcome、必要 review 和 JE generation 之后。
- 它依赖稳定 `transaction_id`、final outcome、journal entry result、evidence references、review / intervention trace 和 upstream authority context。
- 它不做 evidence intake、identity、structural match、entity resolution、rule match、case judgment、pending clarification、review decision capture 或 JE generation。
- 它不替 accountant 作会计判断。
- 它不修改 Entity / Case / Rule / Governance memory。
- 它不执行 rule promotion、entity governance、profile update 或 automation-policy change。
- 它不把 transient handoff、queue、draft、candidate 或 report artifact 称为 `Log`。
- 它不重写历史日志来追随后续治理变化；后续解释应通过 governance event 或后续审计语境完成。

## 8. Open Boundaries

以下问题留到后续阶段，不在 Stage 1 冻结：

- 哪些 upstream outcome 可被视为具备 final logging authority。
- `Review Node` 是否覆盖所有 final logging 前交易，还是只覆盖 review-required / sampled / governance-candidate items。
- high-confidence structural / rule / case-supported result 是否可以不经逐笔 accountant review 直接进入 JE 和 final logging。
- JE-blocked / not-finalizable handoff 是否能形成某种 terminal audit record，还是只能保留在 intervention / review / blocked workflow 语境中。
- accountant approval、correction、rejection、still-pending 与 final logging 的 exact handoff contract。
- review / intervention trace 与 `Transaction Log` 的 exact persistence boundary。
- final `Transaction Log` 与 `Case Memory Update Node`、`Governance Review Node`、`Knowledge Compilation Node`、`Post-Batch Lint Node` 的 exact handoff contract。
- exact input / output schema、字段名、对象结构、routing enum、存储路径、执行算法、测试矩阵和 coding-agent task contract。
