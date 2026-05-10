# Entity Resolution Node — Stage 2：功能逻辑与决策边界

## 1. Stage 范围

本 Stage 2 定义 `Entity Resolution Node` 的功能逻辑与决策边界。

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

`Entity Resolution Node` 在主 workflow 中，`Profile / Structural Match Node` 已确认当前交易未被结构性路径完成之后触发。

概念触发条件是：

- 当前交易已有可追溯 evidence foundation、客观交易基础和稳定交易身份；并且
- 当前交易没有被 stable profile structural facts 完成处理；并且
- 后续普通交易 workflow 需要知道当前 evidence 指向哪个 counterparty / vendor / payee，或为什么不能安全确认。

典型触发场景包括：

- 银行描述、小票、支票、invoice、contract 或 accountant context 暴露出 vendor / payee / counterparty 信号。
- 当前 evidence 可能匹配已知实体或 approved alias。
- 当前 evidence 可能指向已知实体，但 role/context 未确认。
- 当前 evidence 看起来是新对象。
- 当前 evidence 可能对应多个实体或角色。
- 当前 evidence 不足以识别对象。

如果材料尚未完成 evidence intake 或 transaction identity，不应触发本节点。
如果当前交易已经由 profile-backed structural path 完成，本节点不能回头把它解释成普通 entity 交易。
如果当前问题已经是 rule execution、case-based accounting judgment、review approval 或 final audit logging，本节点不能吸收这些下游职责。

## 3. Input Categories

Stage 2 按判断作用组织 input categories，不列字段清单。

### 3.1 Current evidence identity signals

说明当前交易 evidence 中有哪些可用于识别对象的表面信号。

来源类别包括 raw bank text、receipt vendor、cheque payee、invoice / contract party、accountant-provided context 和其他 current evidence references。

这类输入只能支持“当前 evidence 指向谁”的判断。
它不等于会计分类、role confirmation、alias approval 或 governance authority。

### 3.2 Existing entity basis

说明 `Entity Log` 中是否存在可能对应的 stable entity、candidate entity、archived / merged entity、known aliases、known roles、status、authority、risk flags 或 automation-policy context。

Entity Resolution 可以读取这些 context 来判断当前交易 identity basis。

它不能把 entity existence 误读成 accounting classification。
它也不能把 active entity 误读成 automation permission；automation eligibility 还取决于 alias、role/context、policy 和下游规则边界。

### 3.3 Alias authority basis

说明当前表面写法是否已被确认、仍是候选、已被拒绝，或与多个对象存在相似关系。

核心边界：

- approved alias 可以支持稳定 entity resolution 和后续 rule eligibility。
- candidate alias 可以作为 Case Judgment 的上下文，但不能支持 rule match。
- rejected alias 是负证据，不能被 LLM 语义相似度绕过。
- 未确认表面写法不能自动变成 approved alias。

### 3.4 Role / context basis

说明当前交易是否需要客户关系中的 role/context 才能安全解释对象。

稳定实体只保存 accountant 确认过的 role。
运行时推断出的 candidate role 只能作为当前交易语境或后续确认候选。

如果实体已知但 role/context 未确认，本节点可以表达 role uncertainty，但不能自行确认 role。

### 3.5 Upstream workflow basis

说明上游 evidence、identity 和 profile / structural nodes 已经给出的约束。

包括 evidence quality / issue signals、duplicate / identity issue context、non-structural handoff context、profile issue context 和 stable transaction identity。

本节点必须消费这些约束，不能把上游 candidate 当作 confirmed fact。

### 3.6 Governance / intervention basis

说明是否存在已知治理限制、近期人工修正、rejected alias、merge / split history、automation policy 限制或身份风险。

这些 context 影响本节点能否输出 stable identity basis，以及下游最多能走到 rule、case、pending、review 还是治理候选。

## 4. Output Categories

Stage 2 只定义 conceptual output categories，不冻结 routing enum 或对象形状。

### 4.1 Stable entity basis

含义：当前 evidence 可以安全指向一个已知稳定实体，并且当前 identity basis 足以供下游消费。

边界：

- 这是实体识别结论，不是会计分类结论。
- 它不等于 rule match。
- 它不等于 automation permission 已满足。
- 它不创建新的 alias、role 或 governance approval。

### 4.2 Stable entity with unconfirmed role/context

含义：对象本身可识别，但当前交易所需 role/context 尚未获得 accountant-confirmed authority。

边界：

- 该状态可以支持 Case Judgment 的上下文理解。
- 未确认 role 通常不能支持 rule match。
- 本节点不能把 candidate role 写成 stable role。
- 是否 pending、review 或继续 case-based path，取决于下游 authority boundary。

### 4.3 New entity candidate

含义：当前 evidence 更像一个尚未稳定存在的新对象，而不是既有实体的安全匹配。

边界：

- `new_entity_candidate` 不天然阻断当前交易后续分类。
- 如果 current evidence 足够强且 authority 允许，后续 Case Judgment 可以把它作为当前交易上下文。
- 它不能支持 rule match。
- 它不能自动创建 stable entity authority。
- 它不能自动批准 alias、role、rule 或 automation policy。
- 它不能自动创建或升级 rule。

### 4.4 Ambiguous entity candidates

含义：当前 evidence 可能对应多个已知实体、alias 或 role/context，不能安全归属。

边界：

- 歧义不是让 LLM 选择一个看起来最像对象的许可。
- 该状态通常限制 deterministic rule 和 case-based automation。
- 下游应得到清楚的 ambiguity reason，以便 pending、review 或 governance flow 处理。

### 4.5 Unresolved identity

含义：当前 evidence 不足以判断 counterparty / vendor / payee 是谁。

边界：

- unresolved 不是会计分类失败的总称，而是身份识别不足。
- 本节点不应为了让 workflow 继续而伪造 entity。
- 下游应得到缺失或不足原因。

### 4.6 Candidate and issue signals

含义：本节点可以指出后续可能需要评估的候选或问题信号，例如：

- alias candidate
- role confirmation candidate
- new entity candidate
- merge / split candidate
- rejected-alias conflict issue
- identity ambiguity issue
- automation-policy / governance candidate

边界：

- Candidate signal 只供后续节点评估。
- 它不是 durable approval。
- 它不改变 stable Entity Log authority。
- 它不改变 active rule 或 automation policy。

## 5. Deterministic Code vs LLM Semantic Judgment

Stage 2 的核心边界是：

**code owns authority checks, identity-state limits, and downstream eligibility constraints; LLM may assist semantic identity matching inside those limits.**

### 5.1 Deterministic code responsibility

Deterministic code 负责：

- 判断本节点是否被触发：上游 evidence intake、transaction identity 和 profile / structural gate 已完成，且当前交易需要普通 entity-first workflow。
- 汇总当前 evidence identity signals、existing entity basis、alias authority、role authority、automation-policy context 和 upstream issue context。
- 执行 authority checks：approved alias、candidate alias、rejected alias、confirmed role、candidate role、entity lifecycle status、automation-policy 限制。
- 防止结构性交易穿透后被当作普通 entity 交易处理。
- 防止 candidate alias 支持 rule match。
- 防止 rejected alias 被语义相似度绕过。
- 防止 unconfirmed role 被当作 stable role。
- 防止 `new_entity_candidate` 获得 stable entity、rule 或 governance authority。
- 防止 ambiguous / unresolved identity 被自动升级为 stable entity basis。
- 标记下游 eligibility 上限：可进入 rule eligibility、只能作为 case context、需要 pending / review、或只能产生 governance candidate。
- 限制 memory / governance actions：哪些只能作为 candidate，哪些绝不能直接修改。

### 5.2 LLM semantic judgment responsibility

LLM 可以在 code 允许的边界内辅助：

- 比较 messy evidence 中的 vendor / payee / counterparty 表面写法。
- 判断 current evidence 是否语义上更像已知实体、全新对象，还是多实体歧义。
- 解释小票、支票、invoice、contract 或 accountant note 中的人类可读 identity clues。
- 总结 identity rationale、ambiguity reason、missing-evidence reason 或 candidate explanation。

### 5.3 Hard boundary

LLM 不能：

- 扩大 entity / alias / role authority
- 把 candidate alias 当作 approved alias
- 忽略 rejected alias
- 确认 role
- 创建 stable entity
- merge / split entity
- 修改 automation policy
- 执行 rule match
- 判断 case precedent 是否足以分类
- 选择 COA / HST 处理
- 批准 governance event
- 写入 `Transaction Log`

## 6. Accountant Authority Boundary

Accountant 仍然拥有最终 accounting decision 和 durable authority。

`Entity Resolution Node` 不能：

- 替 accountant 确认 role/context
- 替 accountant approve / reject alias
- 替 accountant 判断两个对象是否应长期 merge / split
- 把 runtime identity guess 变成 accountant-confirmed entity memory
- 把 client-provided context 直接升级成 accountant-approved authority
- 替 accountant 批准当前交易最终分类或 review outcome

如果当前 identity 需要 accountant information、alias 确认、role 确认、业务关系确认或歧义解除，本节点只能输出 pending / review context 或 candidate signal。

## 7. Governance Authority Boundary

Governance-level changes 不属于 Entity Resolution authority。

本节点不能：

- approve / reject alias
- confirm role
- create stable entity authority
- merge / split entity
- archive / reactivate entity
- upgrade or relax automation policy
- promote / modify / delete / downgrade active rule
- approve governance event
- invalidate durable memory

本节点可以提出 governance candidate signal。
是否进入治理队列、如何聚合展示、是否批准，以及批准后如何修改长期 memory，属于 Review / Governance Review / memory update workflow。

## 8. Memory / Log Boundary

Stage 2 采用三层边界：read / consume、candidate-only、no direct mutation。

### 8.1 Read / consume boundary

`Entity Resolution Node` 可以读取或消费以下 conceptual context：

- runtime evidence foundation
- objective transaction basis
- evidence references
- stable transaction identity
- non-structural handoff context from `Profile / Structural Match Node`
- `Entity Log` 中的 known entities、aliases、roles、status、authority、risk flags 和 automation-policy context
- `Governance Log` 或 governance context 中已生效的 alias、role、merge/split、policy 限制
- `Intervention Log` 中与 identity correction 有关的近期人工介入语境
- `Knowledge Log / Summary Log` 中可读的客户知识摘要，但只能作为辅助上下文，不能替代 Entity Log authority

它不读取 `Transaction Log` 做 runtime identity decision。
它不读取 `Case Log` 或 `Rule Log` 来绕过 entity / alias / role authority。
它不把 Knowledge Summary 当作 deterministic rule source 或 stable entity authority。

### 8.2 Candidate-only boundary

本节点只能作为候选或 issue signal 表达：

- new entity candidate
- alias candidate
- role confirmation candidate
- entity ambiguity issue
- unresolved identity issue
- rejected-alias conflict issue
- merge / split candidate
- automation-policy / governance candidate

Candidate-only 表示后续 Coordinator、Review、Case Memory Update 或 Governance Review workflow 应评估该信号。
它不是 stable Entity Log mutation，也不是 durable approval。

Active baseline 允许 `new_entity_candidate` 作为待治理记忆存在，但 Stage 2 不冻结由本节点直接落盘、还是由后续 memory-update / governance 节点落盘。无论后续 contract 选择哪种方式，候选都不能获得 stable entity、approved alias、confirmed role、rule 或 automation authority。

### 8.3 No direct mutation boundary

本节点绝不能：

- 写入 `Transaction Log`
- 修改 stable `Entity Log` authority
- 批准 alias
- 拒绝 alias
- 确认 role
- merge / split entity
- 修改 entity lifecycle status 为 stable authority
- 修改 automation policy
- 写入或修改 `Case Log`
- 写入或修改 `Rule Log`
- 写入或批准 `Governance Log`
- 创建、升级、修改、删除或降级 active rule
- 把 runtime identity result 直接变成 accountant decision

## 9. Insufficient / Ambiguous / Conflicting Evidence Behavior

Stage 2 采用优先级边界：authority first、identity safety second、candidate clarity third。

### 9.1 Authority first

如果 alias、role、entity lifecycle、automation policy 或 governance context 已经限制当前 identity basis，本节点不能用语义相似度绕过。

典型情况：

- 表面写法对应 rejected alias。
- 当前 alias 只是 candidate alias。
- 当前 role/context 需要确认但尚未确认。
- known entity 存在治理限制。
- automation policy 限制下游自动化。
- merge / split history 显示旧实体引用需要治理解释。

这些情况应输出受限 identity basis、pending / review context 或 governance candidate signal，而不是伪装成稳定可自动化对象。

### 9.2 Identity safety second

如果 current evidence 可以安全指向一个已知实体，本节点应输出 stable identity basis。
如果证据指向新对象，应保持 `new_entity_candidate` 语义。
如果证据不足或多个对象都合理，应保持 ambiguous 或 unresolved。

不能为了提升自动化率而把新对象压进相似旧实体。
不能为了避免 pending 而在多个候选中猜一个。

### 9.3 Candidate clarity third

当 evidence 缺失、模糊或冲突时，本节点应清楚说明卡点属于哪类问题：

- 缺少可识别对象信号
- 表面写法相似但 authority 不足
- 可能是新对象
- 多个实体或 role/context 竞争
- rejected alias 或治理历史冲突
- evidence source 之间互相矛盾

下游需要的是可处理的不确定性，而不是被 confidence 语言掩盖的猜测。

### 9.4 Conflict behavior

如果 current evidence 与 Entity Log、alias authority、role authority、governance history 或 accountant context 冲突，本节点应保守处理。

典型边界：

- 冲突只是缺一个具体事实确认：输出 pending context。
- 冲突涉及长期 entity memory 是否错误：输出 review / governance candidate。
- 冲突影响当前是否能安全识别对象：不能输出 stable identity basis。

LLM 不能选择一个“看起来更合理”的版本覆盖冲突。

### 9.5 Hard boundary

- 相似名称不等于同一实体。
- Candidate alias 不等于 approved alias。
- Candidate role 不等于 confirmed role。
- `new_entity_candidate` 不天然 hard block，但也不提供 durable authority。
- Ambiguity 不等于可以猜。
- Entity resolution confidence 只表示身份识别信心，不表示会计分类信心。
- `Transaction Log` 不参与 runtime identity decision。

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
- stable entity resolution 所需 evidence categories 的精确门槛
- candidate entity 是否由 Entity Resolution 直接落盘，还是由 Case Memory Update / Governance workflow 落盘
- candidate alias / role / merge-split signal 的 exact memory operation contract
- accountant 补充确认后是否重新触发本节点
- role/context 未确认时下游 rule、case、pending、review 的 exact routing contract
- Knowledge Summary 与 Entity Log authority 冲突时的精确处理 contract
