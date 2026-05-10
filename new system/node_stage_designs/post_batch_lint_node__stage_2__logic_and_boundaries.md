# Post-Batch Lint Node — Stage 2：功能逻辑与决策边界

## 1. Stage 范围

本 Stage 2 定义 `Post-Batch Lint Node` 的功能逻辑与决策边界。

它回答：

- 什么触发该节点
- 它消费哪些输入类别
- 它可以产生哪些输出类别
- 哪些责任属于 deterministic code
- 哪些责任可以使用 LLM semantic judgment
- accountant / governance authority 边界
- memory/log read、candidate-only、limited mutation、no-mutation 边界
- 证据不足、模糊、冲突时的行为边界

本阶段不定义 schema、字段契约、存储路径、执行算法、测试矩阵、implementation routing、threshold number 或冻结枚举值。

## 2. Trigger Boundary

`Post-Batch Lint Node` 在 batch-level boundary 下触发。

概念触发条件是：

- 一个批次已经形成足够的完成交易、review、intervention、case、rule、entity 或 governance 语境；并且
- 系统需要检查跨交易、跨记忆层或跨治理事项的自动化健康风险。

它不是单笔交易 runtime path 的一环。

典型触发语境包括：

- 批次处理结束后的常规健康检查。
- Review / intervention 中出现重复 correction、反复 pending、rule conflict 或 automation-risk signal。
- Case Memory Update 暴露 case-to-rule candidate、case conflict、entity / alias / role candidate 或 automation-policy concern。
- Governance Review 产生已批准、拒绝、暂缓、限制或 auto-applied downgrade 相关语境，需要未来监控。
- Knowledge Compilation 暴露 summary mismatch、stale knowledge 或 unresolved boundary，需要回到 source memory 检查。

如果输入只是单笔交易尚未 finalizable 的 runtime rationale、review draft、report draft、candidate-only note 或未绑定 evidence 的自然语言 warning，本节点不应把它当作 post-batch lint authority。

## 3. Input Categories

Stage 2 按判断作用组织 input categories。这里不是字段清单。

### 3.1 Completed batch / audit-history basis

说明本批次实际完成了哪些交易、哪些交易被 review / correction / intervention 影响、哪些候选信号随 finalization 被保留下来。

来源类别包括 final transaction processing context、audit-facing `Transaction Log` 查询语境、review / intervention trace、completed JE / output context。

边界：

- `Transaction Log` 只能作为已完成历史和 audit trace 被查询。
- 它不参与未来 runtime classification、rule match 或 case judgment。
- 它不是 learning layer，也不是 rule source。

### 3.2 Entity consistency basis

说明 entity memory 是否出现拆合、别名、角色、状态或自动化权限相关风险。

来源类别包括 `Entity Log`、entity resolution history、candidate alias / role context、merge / split candidates、new entity candidates、rejected alias context、entity lifecycle / automation policy context。

关键判断包括：

- 是否可能存在同一对象被拆成多个 entity。
- 是否可能存在一个 entity 混入不同业务角色或不同对象。
- alias / role candidate 是否反复出现但未治理。
- `new_entity_candidate` 是否积累出需要治理的 entity / alias / role 候选。

边界：

- Lint finding 不能自动 merge / split entity。
- Lint finding 不能把 candidate alias 或 candidate role 变成 approved / confirmed authority。
- `new_entity_candidate` 不因批次重复出现而自动变成 stable entity。

### 3.3 Rule health basis

说明 active rule 是否仍然安全、稳定、适用。

来源类别包括 `Rule Log`、rule match outcomes、rule blocked / ineligible reasons、review corrections、intervention history、governance restrictions 和 rule lifecycle context。

关键判断包括：

- active rule 是否反复被 accountant 修正。
- rule 条件是否过宽、过窄或与实际案例冲突。
- rule 是否依赖已经变化的 entity、alias、role 或 automation policy。
- rule miss / blocked pattern 是否暴露 rule candidate 或 rule review need。

边界：

- 本节点不能 create、promote、modify、delete 或 downgrade active rule。
- rule candidate、lint suggestion、repeated outcome、Case Log 或 Knowledge Summary 不能替代 `Rule Log` 中的 approved active rule。

### 3.4 Case-to-rule basis

说明一组 completed cases 是否表现出可能进入 rule governance 的稳定性。

来源类别包括 `Case Log`、completed transaction context、accountant corrections、case judgment rationale、customer knowledge summary 和 related evidence references。

关键判断包括：

- completed cases 是否在相同 entity / role / context 下表现出稳定处理。
- 是否存在明显例外条件，使 rule promotion 不安全。
- 是否存在 mixed-use、金额异常、tax treatment 差异、role ambiguity 或 review history，使规则化应被限制。

边界：

- case-to-rule 只能是 candidate。
- 它不等于 rule promotion。
- 它不能绕过 accountant / governance approval。

### 3.5 Review / intervention basis

说明 accountant 在本批次或近期介入中反复修正了什么、确认了什么、拒绝了什么、暂缓了什么。

来源类别包括 `Intervention Log`、Review Node context、pending answers、accountant corrections、unresolved review notes、governance handoff。

边界：

- Accountant response 可以解释 lint finding，但不自动变成 durable governance mutation。
- 模糊回答不能被 lint pass 升级成 stable entity、active rule 或放宽后的 automation policy。

### 3.6 Governance / automation-policy basis

说明现有 governance history、automation policy、rule lifecycle 或 entity authority 是否限制未来自动化。

来源类别包括 `Governance Log`、Entity Log automation policy、Rule Log lifecycle、prior approvals / rejections / deferrals / restrictions、auto-applied downgrade history。

关键判断包括：

- 是否需要把 automation policy 降到更保守状态。
- 是否需要把 automation policy 升级或放宽候选交给 accountant。
- 是否需要把 unresolved governance risk 继续保留为 review / lint / knowledge follow-up。

边界：

- 自动降级 automation policy 是 active baseline 允许的风险降低动作。
- 升级或放宽 automation policy 必须 accountant approval。
- rule lifecycle 变化必须 accountant / governance approval。

### 3.7 Knowledge / summary basis

说明客户知识摘要是否暴露 stale、conflicting 或 missing context。

来源类别包括 `Knowledge Log / Summary Log` 和 source memory references。

边界：

- Knowledge Summary 是可读背景，不是 deterministic rule source。
- 摘要与 source memory 冲突时，source memory / governance history 优先。
- 本节点不能通过修改摘要来改变 entity、case、rule 或 governance authority。

## 4. Output Categories

Stage 2 只定义 conceptual output categories，不冻结 routing enum。

### 4.1 No-material-finding result

含义：本批次没有发现需要 review、governance、knowledge follow-up 或 automation-policy action 的 material issue。

边界：

- 这不是对未来自动化永久安全的保证。
- 它不改变任何 durable authority。

### 4.2 Review-facing lint finding

含义：发现需要 accountant 可见的批次级风险、趋势或未解决问题。

可覆盖语境包括 entity consistency risk、rule instability、case conflict、repeated intervention、automation risk 或 stale knowledge。

边界：

- Finding 不是 `Log`。
- Finding 不是 accountant approval。
- Finding 不是 durable memory mutation。

### 4.3 Governance candidate handoff

含义：发现可能需要 `Governance Review Node` 处理的高权限事项。

可覆盖语境包括：

- entity merge / split candidate
- alias approval / rejection candidate
- role confirmation candidate
- rule candidate or rule-health candidate
- automation-policy review candidate
- unresolved governance risk candidate

边界：

- Candidate 只表示后续治理应评估。
- 它不批准治理变化。
- 它不改变 active rule、stable entity authority 或 automation policy，除受控自动降级例外外。

### 4.4 Case-to-rule candidate

含义：completed cases 可能已稳定到值得进入 rule governance review。

边界：

- 它不是 rule。
- 它不进入 rule match。
- 它不能作为 `Rule Log` authority。

### 4.5 Rule-health restriction candidate

含义：active rule、rule condition、rule applicability 或 rule lifecycle 暴露风险，需要 review / governance 评估。

边界：

- 本节点不能直接修改、删除或降级 active rule。
- 如果需要改变 active rule，必须进入 governance / accountant approval。

### 4.6 Limited auto-applied automation-policy downgrade

含义：在 active baseline 允许的受控边界内，系统可以对 entity automation policy 做风险降低方向的自动降级，并把该动作暴露给 Review / Governance visibility。

边界：

- 只能是更保守的自动化权限。
- 不能放宽权限。
- 不能升级权限。
- 不能改变 active rule。
- 不能批准 entity、alias、role、merge 或 split。
- 不能替 accountant 做会计判断。
- 必须保持后续 accountant visibility 和 governance traceability。

如果证据不足以支持自动降级，应输出 review / governance candidate，而不是静默 mutation。

### 4.7 Knowledge compilation follow-up

含义：lint finding、unresolved risk、stale summary 或 rejected / deferred governance context 需要进入未来客户知识摘要或监控背景。

边界：

- Knowledge follow-up 不能变成 deterministic rule source。
- Summary wording 不能把 candidate 写成 approved authority。

## 5. Deterministic Code vs LLM Semantic Judgment

Stage 2 的核心边界是：

**code owns batch eligibility, authority enforcement, durable-action limits, and conservative gating; LLM may help interpret cross-case meaning and explain risk inside those limits.**

### 5.1 Deterministic code responsibility

Deterministic code 负责：

- 判断 Post-Batch Lint 是否可触发：是否存在完成批次或等价的 batch-level review / memory / governance context。
- 区分 source categories：Transaction audit history、Entity、Case、Rule、Intervention、Governance、Knowledge。
- 检查 source authority：approved、completed、candidate-only、rejected、deferred、auto-applied downgrade、unresolved、conflicting。
- 防止 transient handoff、queue、draft、candidate 或 report artifact 被称为 `Log`。
- 防止 `Transaction Log` 被用于 runtime decision、learning、rule source 或 governance approval。
- 判断哪些 finding 只能 review-facing，哪些可以进入 governance candidate，哪些可以进入 knowledge follow-up。
- 执行 active rule no-mutation boundary。
- 执行 entity merge / split no-mutation boundary。
- 执行 automation policy boundary：只能在允许范围内风险降低；升级或放宽必须 accountant approval。
- 防止 `new_entity_candidate`、candidate alias、candidate role 或 repeated cases 获得 stable authority。
- 防止 Knowledge Summary 或 lint finding 替代 source memory authority。

### 5.2 LLM semantic judgment responsibility

LLM 可以负责：

- 比较多个 cases 是否语义上属于同一业务场景。
- 解释 rule instability、case conflict、entity split / merge risk 或 automation-risk trend。
- 帮助识别候选事项的业务含义和 accountant-facing wording。
- 总结为什么某个 rule candidate 仍有例外风险。
- 总结为什么某个 entity 可能需要 merge、split、role confirmation 或 automation-policy restriction。

### 5.3 Hard boundary

LLM 不能：

- 扩大 automation authority。
- 放宽 automation policy。
- create / promote / modify / delete / downgrade active rule。
- merge / split entity。
- approve alias or role。
- 把 `new_entity_candidate` 变成 stable entity。
- 把 repeated cases 变成 active rule。
- 把 lint finding 写成 durable governance approval。
- 重写 historical `Transaction Log`。

## 6. Accountant Authority Boundary

Accountant 仍然拥有最终 accounting decision 和 durable governance authority。

`Post-Batch Lint Node` 不能：

- 替 accountant 批准会计分类。
- 替 accountant 批准 rule promotion。
- 替 accountant 批准 entity merge / split。
- 替 accountant 批准 alias、role 或 stable entity authority。
- 替 accountant 放宽 automation policy。
- 把 accountant 模糊回答解释成长期 governance approval。

当 lint finding 暗示 future automation、entity authority、rule authority 或 customer knowledge 需要变化时，本节点应输出 review / governance / knowledge follow-up 语境，而不是自行批准。

自动降低 automation policy 是风险降低动作。它不等于 accountant approval，必须保留 accountant visibility 和可治理性。

## 7. Governance Authority Boundary

Governance-level changes 不属于本节点的自由裁量。

本节点可以提出治理候选，或在 active baseline 允许下执行受限的 automation-policy downgrade。

除此之外，它不能：

- approve / reject alias
- confirm role
- create stable entity from candidate
- merge / split entity
- create / promote / modify / delete / downgrade active rule
- upgrade or relax automation policy
- approve governance event
- invalidate durable memory
- rewrite historical audit history

如果 finding 会影响 future entity resolution、rule match、case judgment、automation policy 或 historical explanation，但影响范围不清，本节点应保持 candidate / review-needed / governance-needed 语义。

## 8. Memory / Log Boundary

Stage 2 采用四层边界：read / consume、candidate-only、limited mutation、no unauthorized mutation。

### 8.1 Read / consume boundary

`Post-Batch Lint Node` 可以读取或消费以下 conceptual context：

- `Transaction Log` 中的 finalized audit history，只作 batch-level historical context、traceability 和 risk analysis。
- `Intervention Log` 中的 accountant questions、answers、corrections、confirmations 和 unresolved intervention context。
- `Entity Log` 中的 entity、alias、role、status、authority、risk flags、automation policy 和 evidence links。
- `Case Log` 中的 completed cases、final classifications、evidence、exceptions、accountant corrections 和 review context。
- `Rule Log` 中的 approved active rules、rule lifecycle、historical rule authority 和 rule-health context。
- `Governance Log` 中的 approvals、rejections、deferrals、restrictions 和 auto-applied downgrade history。
- `Knowledge Log / Summary Log` 中的人类和 agent 可读摘要，但只能作为辅助背景。
- Profile context 中与 entity / rule / automation risk 有关的结构事实。

### 8.2 Candidate-only boundary

本节点可以提出候选信号，但不能执行对应高权限变化：

- entity merge / split candidate
- alias approval / rejection candidate
- role confirmation candidate
- new entity governance candidate
- case-to-rule candidate
- rule conflict / instability / stale rule candidate
- automation-policy upgrade / relaxation review candidate
- knowledge compilation follow-up candidate
- unresolved governance risk candidate

Candidate-only 表示后续 Review、Governance Review、Knowledge Compilation、Case Memory Update 或相关 memory workflow 应评估该信号。

### 8.3 Limited mutation boundary

本节点唯一在 active baseline 中已知的受限 durable action 是：

- 对 entity automation policy 做风险降低方向的自动降级。

该边界必须同时满足：

- 只降低自动化权限，不放宽。
- 不改变 active rule。
- 不批准 entity / alias / role / merge / split。
- 不改变当前交易 accounting outcome。
- 不重写 historical `Transaction Log`。
- 对 accountant / governance review 保持可见。

Stage 2 不冻结 exact contract、持久化形态或触发阈值。

### 8.4 No unauthorized mutation boundary

本节点绝不能：

- 写入或修改 `Transaction Log`
- 把 `Transaction Log` 变成 learning layer 或 runtime decision source
- 写入或修改 `Case Log`
- 写入或修改 `Rule Log`
- 修改 active rule
- 写入或修改 stable `Entity Log` authority，除受控 automation-policy downgrade 外
- approve alias、role、entity、merge 或 split
- upgrade or relax automation policy
- 写入或批准 governance approval
- 把 candidate、queue、review draft、lint finding 或 report draft 称为 `Log`
- 把 Knowledge Summary 当作 source authority

## 9. Insufficient / Ambiguous / Conflicting Evidence Behavior

Stage 2 采用优先级边界：authority first、source sufficiency second、conflict caution third。

### 9.1 Authority first

如果事项涉及 active rule、entity authority、alias / role approval、merge / split、automation-policy upgrade / relaxation 或 governance approval，本节点不能自行批准。

这些情况应保持 candidate、review-needed 或 governance-needed 语义。

自动降低 automation policy 只在 active baseline 允许的风险降低边界内成立；如果 evidence 或 authority 不足，应退回 candidate。

### 9.2 Source sufficiency second

如果 finding 只来自未绑定 evidence 的自然语言说明、draft、queue item、单笔 runtime rationale 或未完成交易，本节点不能把它升级成 lint conclusion。

如果 completed cases、review corrections、intervention history 或 source memory 不足以支持 batch-level 判断，应输出 insufficient-evidence finding、review candidate 或 no-action result。

### 9.3 Conflict caution third

如果 source memory、Transaction Log audit history、Case Log、Rule Log、Entity Log、Governance history、Knowledge Summary 或 accountant correction 互相冲突，本节点应保守处理。

典型边界：

- Transaction Log 与后续 governance state 不一致：不重写历史，通过治理历史解释时点差异。
- Case Log 与 Rule Log 表达不同处理边界：区分 case precedent 与 active rule，不能用 case 直接覆盖 rule。
- Knowledge Summary 与 source memory 冲突：source memory / governance history 优先，摘要进入 follow-up。
- Lint finding 与 approved authority 冲突：保持 warning / candidate，不直接改变 authority。
- Automation-policy downgrade evidence ambiguous：不要静默降级，进入 review / governance candidate。

### 9.4 Hard boundary

- 批次级趋势不等于 governance approval。
- 重复案例不等于 active rule。
- Lint warning 不等于 runtime rule override。
- `new_entity_candidate` 不天然阻断当前交易分类，但不创造 stable entity、approved alias、confirmed role 或 rule authority。
- `Transaction Log` 是 audit-facing，不参与 runtime decision，也不是 learning layer。
- 风险降低可以保守；权限放宽必须审批。

## 10. Stage 2 Open Boundaries

以下内容仍留到后续 stage 或用户决策：

- Post-Batch Lint 与 Knowledge Compilation 的 exact ordering。
- lint finding、review package、governance candidate queue 的 exact handoff contract。
- automation-policy auto-downgrade 的 exact eligibility、persistence、visibility 和 contest / reversal contract。
- case-to-rule candidate 的 exact eligibility contract。
- rule instability、frequent correction、entity split / merge risk 的 exact thresholds。
- rejected / deferred governance decision 对未来 lint monitoring 和 Knowledge Summary 的 exact expression。
- Post-Batch Lint 是否生成可持久保存的 monitoring artifact；若需要，必须先决定它是否是 durable `Log`，不能默认把 handoff / queue 称为 `Log`。
