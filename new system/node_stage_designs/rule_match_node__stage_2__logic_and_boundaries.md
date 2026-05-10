# Rule Match Node — Stage 2：功能逻辑与决策边界

## 1. Stage 范围

本 Stage 2 定义 `Rule Match Node` 的功能逻辑与决策边界。

它回答：

- 什么触发该节点
- 它消费哪些输入类别
- 它可以产生哪些输出类别
- 哪些责任属于 deterministic code
- 哪些责任可以使用 LLM semantic judgment
- accountant / governance authority 边界
- memory/log read、candidate-only、no-mutation 边界
- 证据不足、模糊、冲突时的行为边界

本阶段不定义 schema、字段契约、对象结构、存储路径、执行算法、测试矩阵、implementation routing、threshold number、冻结枚举值或 coding-agent task contract。

## 2. Trigger Boundary

`Rule Match Node` 在主 workflow 中，`Entity Resolution Node` 已经为当前非结构性交易给出 entity-resolution context 之后触发。

概念触发条件是：

- 当前交易已有可追溯 evidence foundation、客观交易基础和稳定交易身份；并且
- 当前交易没有被 profile-backed structural path 完成；并且
- 当前交易已完成 entity resolution handoff；并且
- 后续 workflow 需要判断是否存在可以直接执行的 approved active rule。

典型触发场景包括：

- 当前交易已安全识别到 stable entity，且 alias / role / automation-policy 可能允许 rule match。
- 当前交易识别到 stable entity，但 role/context、alias 或 policy 可能阻断 rule match。
- 当前交易是 `new_entity_candidate`、ambiguous 或 unresolved，需要明确 deterministic rule path 不可用。
- 当前交易可能存在 active rule，但当前方向、金额、context 或其他已批准条件未满足。
- 当前交易存在 rule governance restriction、非 active rule、需要 review 的 rule context 或 automation policy block。

如果材料尚未完成 evidence intake、transaction identity、profile / structural gate 或 entity resolution，不应触发本节点。
如果当前交易已经由 structural path 完成，本节点不能重新解释为普通 rule transaction。
如果当前问题已经是 case precedent 判断、accountant pending、review approval、journal entry generation 或 final audit logging，本节点不能吸收这些下游职责。

## 3. Input Categories

Stage 2 按判断作用组织 input categories，不列字段清单。

### 3.1 Entity resolution basis

说明当前交易的 entity-resolution 状态及其 authority 语境。

来源类别包括 Entity Resolution output、Entity Log context、alias authority、role/context authority、entity lifecycle status 和 identity risk context。

核心边界：

- stable active entity 可以成为 rule eligibility 的必要基础。
- `new_entity_candidate` 不能支持 rule match。
- ambiguous entity candidates 不能支持 rule match。
- unresolved identity 不能支持 rule match。
- candidate alias 不能支持 rule match。
- rejected alias 不能被 rule match 绕过。
- unconfirmed role/context 不能支持需要该 role/context 的 rule。

### 3.2 Automation-policy basis

说明当前实体或语境是否允许 rule-based automation。

来源类别包括 Entity Log 中已生效 automation policy、governance context 和已批准 policy changes。

核心边界：

- 允许 case-based judgment 不等于允许 rule match。
- `rule_required` 表示只有 approved rule 可以自动分类；没有适用 approved rule 时必须离开 deterministic path。
- `review_required` 或 `disabled` 不能被 rule match 降级为自动处理。
- automation policy 的升级或放宽必须经过 accountant approval。

### 3.3 Approved rule basis

说明是否存在可用于当前 entity / role / context 的 active rule。

来源类别包括 `Rule Log` 中 accountant / governance 已批准的 deterministic rules，以及 rule lifecycle / governance 状态。

核心边界：

- 只有 active、approved、未被治理限制的 rule 可以支持 deterministic match。
- rule candidate、case memory、Knowledge Summary、repeated outcome 或 lint suggestion 不能作为 active rule source。
- 非 active、未批准、被拒绝、等待审批、处于 review 限制或 governance-blocked 的 rule 不能被当作 active rule 执行。

### 3.4 Rule condition basis

说明当前交易是否满足 rule 自身已经批准的适用条件。

来源类别包括 objective transaction basis、direction、amount / range context、approved role/context condition、approved exception condition 和 current evidence references。

这些条件必须来自已批准 rule 或 objective transaction facts。
本节点不能临时发明新条件，也不能用 LLM 语义解释扩大 rule 适用范围。

### 3.5 Upstream workflow basis

说明上游 evidence、identity、profile / structural 和 entity-resolution nodes 已经给出的限制。

本节点必须消费上游 blocked reason、issue signal 和 authority limits。
它不能把上游 candidate 当作 confirmed fact，也不能把上游 unresolved / ambiguous 状态包装成 rule miss 后继续自动处理。

### 3.6 Governance / intervention basis

说明是否存在 rule、entity、alias、role、automation policy 或近期 accountant intervention 相关的治理限制。

`lint warning` 或近期 `intervention` 不应作为本节点临时额外判断直接改变 rule match。
它们只有在已经通过治理流程改变 automation policy、rule lifecycle 或 active rule 状态后，才影响 rule eligibility。

## 4. Output Categories

Stage 2 只定义 conceptual output categories，不冻结 routing enum 或对象形状。

### 4.1 Deterministic rule-handled path

含义：当前交易满足 rule match 的全部前置 authority 和 approved rule condition，可以进入 deterministic rule-handled path。

边界：

- 这是当前交易的 runtime deterministic path。
- 它不等于 accountant final review approval。
- 它不创建或修改 rule。
- 它不创建或修改 entity / alias / role / automation policy。
- 它不写 `Transaction Log`。

### 4.2 Rule miss path

含义：当前 entity / context 允许尝试 rule matching，但不存在适用 active rule，或当前交易不满足任何 active rule 的已批准适用条件。

边界：

- Rule miss 不是 case judgment。
- Rule miss 不是 permission to guess。
- Rule miss 不自动创建 rule candidate。
- 下游 `Case Judgment Node` 可以读取 miss reason 和当前 context 继续判断。

### 4.3 Rule blocked / ineligible path

含义：当前不是单纯没有命中 rule，而是 rule path 缺少必要 authority 或被 policy / governance 限制。

典型原因包括：

- entity 不是 stable active entity
- `new_entity_candidate`
- ambiguous / unresolved identity
- alias 不是 approved alias 或存在 rejected-alias conflict
- role/context 未确认
- automation policy 不允许 rule-based automation
- rule lifecycle 或 governance state 不允许执行

边界：

- Blocked / ineligible reason 是约束，不是 Case Judgment 或 LLM 可以自行解除的软建议。
- 下游应根据原因进入 pending、review-required、governance candidate 或 case-allowed path；exact routing 留到后续阶段。

### 4.4 Review-required / governance-needed signal

含义：当前 rule path 不能完成，因为需要 accountant review、role/alias/entity confirmation、rule governance、automation policy decision 或 rule conflict resolution。

边界：

- 本节点只暴露 review / governance need。
- 它不提问 accountant。
- 它不批准治理事件。
- 它不改变 active rule 或 automation policy。

### 4.5 Candidate signals

含义：本节点可以指出后续可能需要评估的候选信号，例如：

- rule candidate
- rule conflict review candidate
- rule stale / unstable candidate
- rule condition gap candidate
- entity / alias / role confirmation candidate
- automation-policy / governance candidate

边界：

- Candidate signal 只供后续节点评估。
- 它不是 durable approval。
- 它不进入 active rule set。
- 它不改变 Entity Log、Rule Log 或 Governance Log authority。

## 5. Deterministic Code vs LLM Semantic Judgment

Stage 2 的核心边界是：

**code owns rule eligibility, rule selection, rule-condition matching, and hard authority limits; LLM does not own rule match authority.**

### 5.1 Deterministic code responsibility

Deterministic code 负责：

- 判断本节点是否被触发：上游 evidence intake、transaction identity、profile / structural gate 和 entity resolution 已完成，且当前交易需要 ordinary rule eligibility check。
- 读取并汇总 entity resolution basis、alias authority、role/context authority、automation policy、approved rule basis、rule lifecycle 和 upstream issue context。
- 判断 entity 是否具备 rule eligibility：stable active entity、approved alias、confirmed required role/context。
- 判断 automation policy 是否允许 rule-based automation。
- 判断是否存在 active approved rule。
- 判断当前 objective transaction basis 是否满足 rule 自身已批准条件。
- 区分 deterministic rule-handled、rule miss、rule blocked / ineligible、review / governance-needed 和 candidate signal。
- 防止 `new_entity_candidate`、candidate alias、unconfirmed role、ambiguous / unresolved identity 支持 rule match。
- 防止 case memory、Knowledge Summary、Transaction Log、lint suggestion 或 repeated outcomes 被当作 active rule。
- 防止 LLM 语义解释扩大、缩小或改写 approved rule 条件。
- 限制 memory / governance actions：哪些只能作为 candidate，哪些绝不能直接修改。

### 5.2 LLM semantic judgment responsibility

LLM 通常不应参与 rule match 本身。

如果后续阶段允许 LLM 辅助，它最多可以在受限边界内帮助：

- 把 rule miss、blocked reason 或 governance need 解释成可读说明。
- 总结为什么当前交易未满足某个已批准 rule 条件。
- 帮助生成 pending / review explanation。
- 帮助整理 rule candidate 或 conflict candidate 的自然语言理由。

### 5.3 Hard boundary

LLM 不能：

- 决定 rule 是否命中
- 放宽 rule 条件
- 创造临时 rule condition
- 把 candidate rule 当作 active rule
- 把 case memory 当作 rule
- 把 `new_entity_candidate` 当作 rule-eligible entity
- 把 candidate alias 当作 approved alias
- 确认 role/context
- 忽略 automation policy 或 governance block
- promote、modify、delete 或 downgrade rule
- 选择 COA / HST 处理来替代 rule match
- 批准 accountant 或 governance decision
- 写入 `Transaction Log`

## 6. Accountant Authority Boundary

Accountant 仍然拥有最终 accounting decision 和 durable authority。

`Rule Match Node` 可以基于已批准 active rule 执行 deterministic rule-handled path，但不能替 accountant 创建或改变规则 authority。

本节点不能：

- 把 repeated runtime outcomes 自动升级为 rule
- 把 case precedent 自动升级为 rule
- 批准 rule candidate
- 修改 rule condition
- 确认 role/context
- 批准 alias
- 放宽 automation policy
- 替 accountant 解决 rule conflict 的业务含义
- 替 accountant 批准当前交易最终 review outcome

如果当前交易需要 accountant 确认业务用途、role/context、alias、rule exception、rule conflict 或 automation policy，本节点只能输出 pending / review / governance context 或 candidate signal。

## 7. Governance Authority Boundary

Governance-level changes 不属于 Rule Match authority。

本节点不能：

- create / promote active rule
- modify rule condition
- delete / downgrade active rule
- approve / reject rule candidate
- approve / reject alias
- confirm role
- create stable entity authority
- merge / split entity
- upgrade or relax automation policy
- approve governance event
- invalidate durable memory

本节点可以提出 governance candidate signal。
是否进入治理队列、如何聚合展示、是否批准，以及批准后如何修改长期 memory 或 active rules，属于 Review / Governance Review / memory update workflow。

## 8. Memory / Log Boundary

Stage 2 采用三层边界：read / consume、candidate-only、no direct mutation。

### 8.1 Read / consume boundary

`Rule Match Node` 可以读取或消费以下 conceptual context：

- runtime evidence foundation
- objective transaction basis
- stable transaction identity
- non-structural handoff context from `Profile / Structural Match Node`
- Entity Resolution output
- `Entity Log` 中的 stable entity、approved aliases、confirmed roles、status、authority、risk flags 和 automation-policy context
- `Rule Log` 中的 approved active rules、rule lifecycle 和 governance status
- `Governance Log` 或 governance context 中已生效的 alias、role、rule、policy 限制
- `Intervention Log` 中已经转化为治理状态或 review-required constraint 的相关语境

它不读取 `Transaction Log` 做 runtime rule decision。
它不读取 `Case Log` 来替代 active rule。
它不把 `Knowledge Log / Summary Log` 当作 deterministic rule source。
它不把 lint warning 或 recent intervention 当作临时 rule override，除非这些信号已经通过治理流程改变 rule 或 automation-policy authority。

### 8.2 Candidate-only boundary

本节点只能作为候选或 issue signal 表达：

- rule candidate
- rule condition gap candidate
- rule conflict candidate
- rule stale / unstable candidate
- missing role/context confirmation issue
- alias / entity authority issue
- automation-policy / governance candidate

Candidate-only 表示后续 Coordinator、Review、Case Memory Update、Post-Batch Lint 或 Governance Review workflow 应评估该信号。
它不是 Rule Log mutation，也不是 durable approval。

### 8.3 No direct mutation boundary

本节点绝不能：

- 写入 `Transaction Log`
- 写入或修改 `Entity Log`
- 写入或修改 `Case Log`
- 写入或修改 `Rule Log`
- 写入或批准 `Governance Log`
- 创建、升级、修改、删除或降级 active rule
- 批准 alias
- 确认 role/context
- 创建 stable entity
- 修改 automation policy
- 把 case memory 或 repeated outcome 直接变成 rule
- 把 runtime rule miss 直接变成 rule promotion

## 9. Insufficient / Ambiguous / Conflicting Evidence Behavior

Stage 2 采用优先级边界：authority first、deterministic fit second、safe handoff third。

### 9.1 Authority first

如果 entity、alias、role/context、automation policy、rule lifecycle 或 governance context 缺少必要 authority，本节点不能完成 rule-handled path。

典型情况：

- 当前是 `new_entity_candidate`。
- 当前 entity ambiguous 或 unresolved。
- matched alias 只是 candidate alias。
- matched alias 与 rejected alias 或治理历史冲突。
- required role/context 尚未 accountant-confirmed。
- automation policy 不允许 rule-based automation。
- rule 不是 active approved rule。
- rule 正在等待审批、处于 review 限制、被治理限制或需要人工确认。

这些情况应输出 blocked / ineligible reason、pending / review context 或 governance candidate signal，而不是 rule-handled result。

### 9.2 Deterministic fit second

即使 authority 完整，当前交易也必须满足 active rule 自身已批准条件。

如果 direction、amount / range、role/context、evidence requirement 或其他 approved condition 不满足，本节点不能语义扩张规则。

它应输出 rule miss 或 condition-mismatch context，并交给下游 case / pending / review flow。

### 9.3 Safe handoff third

如果没有适用 active rule，且不存在必须先处理的 rule authority block，应把 deterministic path 未完成原因交给 `Case Judgment Node`。

Rule miss 是正常路径，不是失败。

本节点不应为了提高自动化率而把 case memory、Knowledge Summary、recent intervention 或 repeated outcomes 当作 active rule。

### 9.4 Conflict behavior

如果 current evidence、entity-resolution context、Rule Log、automation policy、governance history 或 accountant context 冲突，本节点应保守处理。

典型边界：

- 冲突只是缺一个具体事实确认：输出 pending / review context。
- 冲突涉及 rule 是否仍应 active：输出 governance candidate。
- 冲突影响当前 rule 是否能确定性适用：不能输出 rule-handled path。

不能让 LLM 或 deterministic fallback 选择一个“看起来更合理”的版本覆盖冲突。

### 9.5 Hard boundary

- `new_entity_candidate` 不支持 rule match。
- Candidate alias 不支持 rule match。
- Candidate role 不等于 confirmed role。
- Case memory 不等于 rule。
- Knowledge Summary 不等于 deterministic rule source。
- Transaction Log 不参与 runtime rule decision。
- Lint warning 和 recent intervention 只有通过治理改变 active authority 后，才影响 rule eligibility。
- Rule miss 不等于 rule candidate approval。
- Rule match confidence 不应替代 approved authority。

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
- role/context requirement 与 rule applicability 的 exact contract
- 多条 active rules 同时适用时的 exact conflict handling
- rule lifecycle states 与 governance state 的 exact contract
- rule miss、rule blocked、rule conflict、rule candidate signal 的 exact downstream routing
- accountant 补充确认后是否重新触发 Rule Match
- deterministic rule-handled result 与 JE generation、review、transaction logging 的 exact handoff contract
