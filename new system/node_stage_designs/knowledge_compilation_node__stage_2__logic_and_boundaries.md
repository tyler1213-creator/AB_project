# Knowledge Compilation Node — Stage 2：功能逻辑与决策边界

## 1. Stage 范围

本 Stage 2 定义 `Knowledge Compilation Node` 的功能逻辑与决策边界。

它回答：

- 什么触发该节点
- 它消费哪些输入类别
- 它可以产生哪些输出类别
- 哪些责任属于 deterministic code
- 哪些责任可以使用 LLM semantic judgment
- accountant / governance authority 边界
- memory/log read、write、candidate-only、no-mutation 边界
- 证据不足、模糊、冲突时的行为边界

本阶段不定义 schema、字段契约、对象结构、存储路径、执行算法、测试矩阵、implementation routing、threshold number、冻结枚举值或 coding-agent task contract。

## 2. Trigger Boundary

`Knowledge Compilation Node` 在客户长期记忆、治理历史或完成交易背景发生足以影响客户知识摘要的变化时触发。

概念触发条件是：

- `Entity Log`、`Case Log`、`Rule Log`、`Governance Log` 或相关 completed audit history 已有可追溯变化；并且
- 这些变化可能影响 humans 或 agents 对客户常见模式、例外、风险、自动化边界或未解决问题的理解；并且
- 上游变化已经进入各自 durable source 或 formal candidate / handoff 语境；并且
- 当前任务是更新可读知识摘要，而不是处理当前交易、批准治理或执行 rule。

典型触发来源包括：

- onboarding 形成初始 entity、historical case、rule / governance candidates 或 customer knowledge seed。
- `Case Memory Update Node` 写入新完成案例或产生 knowledge-compilation handoff。
- `Governance Review Node` 记录批准、拒绝、暂缓、限制或 auto-applied downgrade 相关治理结果。
- `Transaction Logging Node`、Review、Intervention 或 audit history 暴露出对客户知识有解释价值的完成交易背景。
- `Post-Batch Lint Node` 暴露需要进入未来摘要或监控背景的风险、候选或 unresolved issue。

以下情况不能触发本节点去生成权威结论：

- 当前交易仍 pending、review-required、not-approved、JE-blocked、unresolved、conflicting 或 governance-blocked。
- 输入只是 runtime rationale、review draft、report draft、unapproved candidate、queue item 或未绑定 evidence 的自然语言说明。
- 需要 accountant / governance approval 的事项尚未获得相应 authority，却被要求写成稳定客户知识。

Stage 2 不冻结 exact refresh strategy：全量重编译、增量更新、批后编译、治理后编译或版本策略留到后续阶段定义。

## 3. Input Categories

Stage 2 按判断作用组织 input categories，不列字段清单。

### 3.1 Entity knowledge basis

说明客户有哪些稳定或受限 entity、alias、role、status、authority、risk flags 和 automation-policy context。

来源类别包括 `Entity Log`、已生效 `Governance Log` context、approved alias / confirmed role history、merge / split / archived 语境和相关 evidence references。

边界：

- Entity summary 只能概括 `Entity Log` 和已授权治理结果。
- candidate alias、candidate role、`new_entity_candidate` 或 merge / split candidate 可以作为未解决边界描述，但不能被写成 stable authority。
- 摘要不能替代未来 Entity Resolution 对 `Entity Log` 的读取。

### 3.2 Case knowledge basis

说明过去真实完成案例如何处理、有哪些条件、例外、correction、review context 或风险模式。

来源类别包括 `Case Log`、completed transaction context、review / correction rationale、case judgment rationale 和必要 evidence references。

边界：

- Case summary 是历史先例的可读压缩。
- 它不是 simple majority rule。
- 它不能把多个相似案例自动升级成 deterministic rule。
- 它不能把未完成、未批准或冲突交易写成稳定案例知识。

### 3.3 Rule knowledge basis

说明哪些 deterministic rules 已被 accountant / governance 批准，哪些 rule 处于限制、冲突、拒绝、暂缓或需要 review 的状态。

来源类别包括 `Rule Log`、rule lifecycle context、governance decisions、rule-health context 和 approved rule authority。

边界：

- Rule summary 只能解释 active / historical rule authority。
- 它不能创建、修改、删除、降级或 promote rule。
- 它不能把 summary wording 变成 rule condition。
- Rule Match 仍必须读取 `Rule Log`，不能读取摘要来执行 rule。

### 3.4 Governance knowledge basis

说明长期记忆和自动化权威为什么发生变化，以及哪些事项被批准、拒绝、暂缓、限制或自动降级。

来源类别包括 `Governance Log`、Governance Review decisions、auto-applied downgrade visibility、accountant / governance rationale 和 prior governance history。

边界：

- Governance summary 是解释层，不是 approval。
- rejected / deferred decisions 可以作为风险或限制背景，但不能变成 future authority。
- 未解决治理风险应被表达为开放边界，不应被总结成稳定事实。

### 3.5 Completed audit and intervention basis

说明哪些已完成交易审计轨迹、intervention、review correction 或 accountant confirmation 对客户知识摘要有解释价值。

来源类别包括 audit-facing `Transaction Log`、`Intervention Log`、Review Node context 和 finalization history。

边界：

- `Transaction Log` 只作历史审计背景和 traceability 来源。
- 它不参与 runtime decision，也不是学习层。
- Knowledge Compilation 不能用 Transaction Log 直接推导 active rule、stable entity 或 accounting authority。

### 3.6 Lint / monitoring basis

说明批后检查或监控语境中有哪些 entity 拆合风险、rule instability、case-to-rule 候选、automation risk 或 unresolved issue 值得 humans / agents 后续看见。

来源类别包括 `Post-Batch Lint Node` finding、lint handoff、governance unresolved risk 和 review / memory consistency issue。

边界：

- lint / monitoring finding 可以进入摘要作为风险或待处理背景。
- 它不是 governance approval。
- 它不能直接改变 active memory 或 automation authority。

## 4. Output Categories

Stage 2 只定义 conceptual output categories，不冻结 routing enum 或对象形状。

### 4.1 Customer knowledge summary write

含义：把可追溯的客户长期语境编译成 durable `Knowledge Log / Summary Log` 摘要。

摘要可覆盖：

- 常见 entity / vendor / payee 语境
- 历史 case patterns 与例外条件
- 已批准 rules 的人类可读解释
- governance history 和 authority changes 的解释
- automation-policy 风险和限制
- unresolved boundaries、review cautions、lint-relevant issues

边界：

- 这是可读编译视图。
- 它不是 deterministic rule source。
- 它不是 current transaction accounting outcome。
- 它不是 accountant approval。
- 它不是 source evidence、case、entity、rule 或 governance record 的替代品。

### 4.2 Source-conflict / stale-summary warning

含义：摘要无法安全更新，或既有摘要与 source memory / governance history 不一致，需要标记 stale、conflict、supersession 或 review-needed。

边界：

- Warning 不修正 source logs。
- Warning 不自行选择冲突版本。
- Warning 不把不一致隐藏在自然语言里。

### 4.3 Knowledge update skipped / blocked handoff

含义：当前输入不足以编译可靠摘要，或候选事项尚未获得 source authority。

边界：

- Blocked handoff 是安全停止。
- 本节点不能用“先写摘要以后再修”绕过 source authority。
- 后续应返回 source memory workflow、Review、Governance Review、Post-Batch Lint 或人工澄清。

### 4.4 Candidate / follow-up signal

含义：编译过程中发现可能需要后续处理的候选或问题。

可能包括：

- stale entity / alias / role explanation candidate
- case memory consistency issue
- rule-health or rule-summary mismatch signal
- unresolved governance risk
- post-batch lint follow-up candidate
- review-facing clarification candidate

边界：

- Candidate signal 只供后续 workflow 评估。
- 它不是 durable approval。
- 它不修改 source memory。
- 它不改变 automation policy。

## 5. Deterministic Code vs LLM Semantic Judgment

Stage 2 的核心边界是：

**code owns source selection, authority gating, staleness/conflict discipline, and write boundaries; LLM may help compress and phrase source-grounded knowledge inside those limits.**

### 5.1 Deterministic code responsibility

Deterministic code 负责：

- 判断本节点是否被触发：是否存在需要编译或刷新客户知识摘要的 durable source change / handoff。
- 汇总并区分 source categories：Entity、Case、Rule、Governance、completed audit、intervention、lint / monitoring context。
- 检查每类输入的 authority：approved、completed、candidate-only、rejected、deferred、stale、conflicting、unresolved。
- 防止 candidate、draft、lint finding、runtime rationale 或 ambiguous accountant response 被写成稳定客户知识。
- 维护 source precedence：摘要必须服从 durable source logs / memory stores，而不是反过来覆盖它们。
- 标记 stale / conflict / supersession / unresolved 状态，防止过期摘要误导下游。
- 限制 durable write：本节点只能写 `Knowledge Log / Summary Log` 语义，不能写或修改 source authority stores。
- 防止摘要被下游误当作 deterministic rule source、stable entity authority、case authority、governance approval 或 Transaction Log。

### 5.2 LLM semantic judgment responsibility

LLM 可以在 code 允许的边界内辅助：

- 把多个 source-grounded cases 总结成可读的常见模式、例外条件和风险提示。
- 将 governance decisions、rule lifecycle、automation-policy context 转写成清楚的人类可读解释。
- 比较摘要草案与 source context，提示可能遗漏、过度概括、矛盾或 stale 的地方。
- 将 unresolved boundaries 写成明确警示，而不是模糊信心语言。
- 为 future agents 生成 compact context，使其知道哪些内容必须回查 source memory。

### 5.3 Hard boundary

LLM 不能：

- 生成 source logs 中不存在的客户事实
- 把 candidate 写成 approved fact
- 把 repeated cases 自动升级成 rule
- 把 summary wording 变成 rule condition
- 扩大 entity / alias / role authority
- 确认 role
- approve / reject alias
- 创建 stable entity
- merge / split entity
- 修改 automation policy
- create / promote / modify / delete / downgrade active rule
- 批准 governance event
- 选择 COA / HST treatment
- 生成或修正 journal entry
- 重写 Transaction Log、Case Log、Rule Log、Entity Log 或 Governance Log

## 6. Accountant Authority Boundary

Accountant 仍然拥有最终 accounting decision 和 durable authority。

`Knowledge Compilation Node` 可以总结 accountant-approved outcomes、accountant corrections、approved governance decisions 和已完成案例。

本节点不能：

- 把摘要写法解释为 accountant approval。
- 把 accountant silence、模糊回答或未完成 review 总结成稳定客户政策。
- 把当前交易 correction 自动变成长期治理事实。
- 把 repeated completed outcomes 自动升级成 active rule。
- 把 candidate alias、candidate role、`new_entity_candidate` 或 rule candidate 总结成已批准状态。
- 把未解决风险淡化为稳定自动化许可。

如果 source authority 不足，摘要应明确保留 candidate、unresolved、review-needed、governance-needed 或 blocked 语义。

## 7. Governance Authority Boundary

Governance-level changes 不属于 `Knowledge Compilation Node` 的 mutation authority。

本节点可以总结已记录的治理历史和未解决治理风险，但不能批准或执行治理变化。

本节点不能：

- approve / reject alias
- confirm role
- create stable entity authority
- merge / split entity
- archive / reactivate entity
- change automation policy
- create / promote / modify / delete / downgrade active rule
- approve governance event
- invalidate durable memory
- rewrite historical cases or transaction logs to match later summary wording

已批准治理变化可以进入摘要作为未来语境。
被拒绝、暂缓或未解决的治理事项只能作为限制、风险或开放边界出现，不能被总结成已生效 authority。

## 8. Memory / Log Boundary

Stage 2 采用四层边界：read / consume、write allowed、candidate-only、no direct mutation。

### 8.1 Read / consume boundary

`Knowledge Compilation Node` 可以读取或消费以下 conceptual context：

- `Entity Log` 中的 entity、alias、role、status、authority、risk flags、automation policy 和 evidence links。
- `Case Log` 中的 completed cases、final classifications、evidence、exceptions、accountant corrections 和 review context。
- `Rule Log` 中的 approved active rules、historical rule authority、rule lifecycle 和 governance status。
- `Governance Log` 中的 approvals、rejections、deferrals、restrictions、auto-applied downgrades 和 authority rationale。
- `Transaction Log` 中的 finalized audit history，只作可读背景、traceability 和 completed-history context。
- `Intervention Log` 中的 accountant questions、answers、corrections、confirmations 和 unresolved intervention context。
- `Evidence Log` references，只用于保持摘要可追溯，不用于覆盖 source memory authority。
- `Profile` 中与客户结构、tax config 或 automation boundary 有关的稳定背景或待确认限制。
- `Post-Batch Lint Node` / monitoring handoff 中需要进入摘要或后续关注的风险语境。

它不能读取这些 sources 后重新做 runtime classification、rule matching、case judgment、JE generation 或 governance approval。

### 8.2 Write allowed boundary

本节点可以执行的 durable write 只限于 `Knowledge Log / Summary Log` 语义：

- 写入或刷新 source-grounded customer knowledge summary。
- 标记摘要的风险、开放边界、stale / conflict / supersession 状态。
- 保存让 humans 和 agents 能回查 source memory 的摘要语境。

这些写入不等于：

- `Transaction Log` write
- `Case Log` write
- `Rule Log` mutation
- `Entity Log` authority mutation
- `Governance Log` approval
- `Profile` update
- report draft 或 review package

### 8.3 Candidate-only boundary

本节点只能作为候选或 issue signal 表达：

- source conflict / stale summary issue
- entity / alias / role summary mismatch candidate
- case memory consistency candidate
- rule-health / rule-summary mismatch candidate
- unresolved governance risk candidate
- automation-policy review candidate
- post-batch lint follow-up candidate
- review-facing clarification candidate

Candidate-only 表示后续 Governance Review、Post-Batch Lint、Review、Case Memory Update 或相关 memory workflow 应评估该信号。

它不是 durable approval，也不是 source memory operation contract。

### 8.4 No direct mutation boundary

本节点绝不能：

- 写入或修改 `Transaction Log`
- 写入或修改 `Case Log`
- 写入或修改 `Rule Log`
- 写入或修改 stable `Entity Log` authority
- 写入或批准 `Governance Log` mutation
- 修改 `Profile`
- 生成或修改 journal entry
- 创建 stable case memory
- 创建 stable entity
- approve / reject alias
- confirm role
- merge / split entity
- 修改 automation policy
- 创建、升级、修改、删除或降级 active rule
- 把 candidate、queue、lint finding、review draft 或 report draft 称为 `Log`
- 把 Knowledge Summary 变成 runtime decision source、deterministic rule source 或 accountant approval

## 9. Insufficient / Ambiguous / Conflicting Evidence Behavior

Stage 2 采用优先级边界：source authority first、traceability second、conflict preservation third、summary humility fourth。

### 9.1 Source authority first

如果输入缺少 durable source authority，本节点不能把它写成稳定客户知识。

典型情况：

- alias / role / entity 仍是 candidate。
- rule 只是 candidate、lint suggestion 或 repeated outcome。
- governance decision 仍 pending、deferred 或 authority 不足。
- accountant response 模糊，无法区分当前交易 correction 与长期政策。
- 当前交易仍未完成或未批准。

这些内容只能作为 candidate、unresolved、review-needed、governance-needed 或 blocked 语境出现。

### 9.2 Traceability second

摘要必须能回到 source memory、evidence reference、case、transaction audit history、intervention 或 governance decision。

如果无法追溯来源，本节点不能用自然语言总结填补缺口。

不可追溯内容应被排除、标记为 blocked，或产生 follow-up signal。

### 9.3 Conflict preservation third

如果 source memories 之间冲突，本节点不能用 LLM 选择一个“更合理”的版本写成摘要事实。

典型边界：

- Entity Log 与 governance history 冲突：标记 conflict，返回治理或 memory consistency workflow。
- Case Log 与 Rule Log 表达不同处理边界：摘要必须区分 case precedent 与 active rule。
- Transaction Log 历史处理与后续 governance state 不一致：不重写历史，通过治理历史解释时点差异。
- lint finding 与 approved authority 冲突：保持 warning / candidate，不改变 authority。

### 9.4 Summary humility fourth

摘要应压缩复杂语境，但不能过度概括。

本节点应避免：

- 把“通常如此”写成“必须如此”。
- 把少数例外隐藏在概括句里。
- 把未解决风险写成已解决结论。
- 把 stale summary 留给下游当作当前 authority。
- 用 confidence 语言掩盖 evidence、authority 或治理缺口。

### 9.5 Hard boundary

- Knowledge Summary 是编译视图，不是 source authority。
- Knowledge Summary 不等于 deterministic rule source。
- Knowledge Summary 不等于 stable entity authority。
- Knowledge Summary 不等于 case memory write。
- Knowledge Summary 不等于 governance approval。
- Transaction Log 是 audit-facing，不参与 runtime decision，也不是学习层。
- `new_entity_candidate` 不天然阻断当前交易分类，但不能在摘要中获得 stable entity、approved alias、confirmed role 或 rule authority。
- Active rule 变化必须经过 accountant / governance approval。
- Automation policy 升级或放宽必须 accountant approval。
- 模糊、冲突、缺失、过期或未批准状态不能被包装成稳定客户知识。

## 10. Stage 2 Open Boundaries

以下内容留到后续阶段，不在 Stage 2 冻结：

- exact input / output schema
- field names and object shape
- exact routing enum
- threshold numbers
- storage paths
- execution algorithm
- test matrix
- coding-agent task contract
- exact prompt structure or tool interface
- Knowledge Compilation 的 full-refresh、incremental-refresh、batch-refresh、governance-triggered refresh 边界
- `Knowledge Log / Summary Log` 的 summary granularity：client-level、entity-level、case-pattern-level、rule-level、governance-level 是否分层
- stale、superseded、conflict、review-needed summary 的 exact lifecycle
- source logs 与 summary 发生冲突时的 exact precedence and repair workflow
- Onboarding seed summary 与后续 runtime / batch summary 的 merge or replacement behavior
- rejected / deferred governance decision、unresolved lint finding 和 monitoring issue 的 exact summary wording boundary
- Knowledge Compilation 与 Post-Batch Lint 对 risk summary、monitoring finding、candidate follow-up 的 exact split
- downstream runtime nodes 读取 summary 时必须同步读取哪些 source memory 的 exact contract
