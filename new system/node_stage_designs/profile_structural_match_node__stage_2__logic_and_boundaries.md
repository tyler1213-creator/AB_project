# Profile / Structural Match Node — Stage 2：功能逻辑与决策边界

## 1. Stage 范围

本 Stage 2 定义 `Profile / Structural Match Node` 的功能逻辑与决策边界。

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

`Profile / Structural Match Node` 在主 workflow 中，`Transaction Identity Node` 已经为当前交易建立或复用稳定交易身份之后触发。

概念触发条件是：

- 当前交易已经具备可消费的 objective transaction basis、evidence references 和稳定交易身份；并且
- 后续 workflow 必须先判断它是否属于 profile-backed structural transaction；并且
- 交易尚未进入普通 entity resolution、rule match 或 case judgment。

典型触发场景包括：

- 银行账户之间可能存在内部转账。
- 当前交易可能对应已知贷款还款。
- 当前交易可能被客户 `Profile` 中的稳定结构事实直接解释。
- 当前交易暴露出 profile 缺失、未确认关系或结构事实冲突，需要在进入 entity-first workflow 前显露。

如果材料尚未完成 evidence intake 或 transaction identity，不应触发本节点。
如果当前问题已经是普通 vendor/entity 识别、rule match、case judgment、review approval 或 final audit logging，本节点不能回头吸收这些下游职责。

## 3. Input Categories

Stage 2 按判断作用组织 input categories，不列字段清单。

### 3.1 Objective transaction basis

说明当前交易中可客观确定的结构事实，例如方向、金额、账户来源、交易日期和其他非会计判断型交易事实。

这一类输入来自上游 evidence / identity flow。
它用于结构性匹配，但不等于 profile authority、entity 结论或会计结论。

### 3.2 Evidence reference basis

说明当前结构性判断能回到哪些原始 evidence。

本节点可以使用 evidence references 支持结构性判断可追溯。
它不能用 evidence 摘要替代原始证据，也不能把证据问题隐藏在结构性结论后面。

### 3.3 Stable profile structural basis

说明当前客户 `Profile` 中已经具备 authority 的结构事实。

这一类输入可以支持结构性确定处理，例如已确认银行账户关系、已确认内部转账关系、已知贷款关系、已确认税务或客户结构事实。

核心边界：

- 只有 stable profile truth 可以支持结构性完成路径。
- profile candidate、onboarding 推断、runtime 疑似关系或未确认 accountant 说明，不能被本节点当作稳定结构事实。
- `Profile` 是客户结构事实层，不是普通 entity、case、rule 或 transaction audit layer。

### 3.4 Bank raw signal basis

说明当前交易是否包含银行原始信号，足以支持内部转账或类似结构关系判断。

内部转账匹配属于 bank-raw-signal 语义，而不是普通 canonical description 或 entity matching 语义。

这一类输入只能在 profile authority 允许的结构关系内使用。
银行原始信号本身不创建新的 profile truth。

### 3.5 Structural candidate / issue basis

说明当前交易是否暴露出疑似结构关系、profile 缺失、profile 候选、未确认贷款关系、账户关系不完整或结构事实冲突。

这类输入可以产生 pending / review / candidate signal。
它不能支持直接结构性完成路径，除非后续 accountant / governance workflow 已经确认相关 profile fact。

### 3.6 Existing workflow context basis

说明上游是否已经暴露 evidence issue、identity issue、duplicate candidate 或补充材料语境。

本节点可以消费这些 issue 来限制结构性判断。
它不能把 identity candidate、duplicate candidate 或 evidence candidate 当作已确认事实。

## 4. Output Categories

Stage 2 只定义 conceptual output categories，不冻结 routing enum 或对象形状。

### 4.1 Structural handled path

含义：当前交易可由 stable profile structural basis 确定为结构性交易，并进入结构性处理路径。

边界：

- 这是当前交易的 runtime structural path。
- 它不等于普通 entity classification。
- 它不创建或修改 profile facts。
- 它不批准 governance change。
- 它不写 `Transaction Log`。

### 4.2 Non-structural handoff path

含义：当前交易没有被 profile-backed structural facts 确定，应继续进入 `Entity Resolution Node`。

边界：

- 未命中结构性路径不等于实体已知或未知。
- 未命中结构性路径不等于 rule miss。
- 未命中结构性路径不等于 case judgment。
- 本节点不应为了避免下游不确定性而扩张结构性解释。

### 4.3 Structural pending / review-needed path

含义：当前交易可能是结构性交易，但缺少关键 profile fact、accountant confirmation、evidence clarification 或 identity/evidence stability，因此不能安全完成结构性处理。

边界：

- 如果问题是可补信息，后续由 `Coordinator / Pending Node` 聚焦提问。
- 如果问题是 profile authority、治理或结构事实冲突，后续应进入 review / governance 相关路径。
- 本节点不自行提问，不自行批准回答。

### 4.4 Structural issue signals

含义：本节点可以输出结构性问题语境，例如疑似内部转账未配置、疑似贷款关系未确认、已知 profile relation 与当前 evidence 冲突、结构性 evidence 不足等。

边界：

- issue signal 不是 accountant decision。
- issue signal 不是 governance approval。
- issue signal 不改变 profile。

### 4.5 Candidate signals

含义：本节点可以提出后续可能需要评估的候选信号，例如：

- profile fact candidate
- internal transfer relationship candidate
- loan relationship candidate
- profile conflict review candidate
- governance candidate

边界：

- candidate 只供后续节点评估。
- candidate 不写入 stable `Profile`。
- candidate 不支持本笔交易的 structural handled path。
- candidate 不创建 rule、case 或 entity authority。

## 5. Deterministic Code vs LLM Semantic Judgment

Stage 2 的核心边界是：

**code owns structural matching, profile authority checks, and hard routing limits; LLM may only assist explanation or messy evidence interpretation inside those limits.**

### 5.1 Deterministic code responsibility

Deterministic code 负责：

- 判断本节点是否被触发：上游 evidence intake 和 transaction identity 已完成，且交易尚未进入 entity-first workflow。
- 读取当前客户 stable profile structural basis。
- 判断 profile authority 是否足以支持 structural handled path。
- 执行结构性匹配，例如内部转账、已知贷款还款或其他已确认结构关系。
- 保持 bank-raw-signal 语义与 ordinary canonical description / entity matching 语义分离。
- 区分 structural handled、non-structural handoff、structural pending / review-needed、issue signal 和 candidate signal。
- 防止 profile candidate、未确认关系或模糊信号被当作 stable profile truth。
- 防止结构性交易错误穿透到普通 entity/rule/case 路径。
- 防止普通 vendor/entity 交易被错误截断为结构性交易。
- 防止本节点写入 `Transaction Log` 或修改 Entity / Case / Rule / Governance memory。

### 5.2 LLM semantic judgment responsibility

LLM 通常不应拥有结构性匹配 authority。

如果后续阶段允许 LLM 辅助，它最多可以在受限边界内帮助：

- 解释 messy evidence 中的人类可读线索。
- 总结为什么当前交易看起来可能是结构性交易。
- 生成 pending / review explanation。
- 帮助整理 profile issue 或 candidate signal 的可读说明。

### 5.3 Hard boundary

LLM 不能：

- 确认内部转账关系
- 确认贷款关系
- 把 profile candidate 升级为 stable profile truth
- 创建或修改 `Profile`
- 把未确认银行原始信号当作结构性完成依据
- 判断普通 vendor/entity identity
- 执行 rule match 或 case judgment
- 选择普通交易 COA / HST 处理
- 生成 journal entry
- 批准 accountant 或 governance decision

## 6. Accountant Authority Boundary

Accountant 仍然拥有最终 accounting decision 和 durable profile authority。

`Profile / Structural Match Node` 可以基于已经确认的 profile facts 执行结构性处理，但不能替 accountant 确认新的客户结构事实。

本节点不能：

- 替 accountant 批准新增银行账户关系
- 替 accountant 确认内部转账关系
- 替 accountant 确认贷款关系
- 把 client-provided 或系统推断的结构说明直接写成 stable profile truth
- 把结构性疑似交易当作已确认结构性交易处理
- 替 accountant 解决 profile conflict 的业务含义

如果当前交易需要 accountant 确认结构事实，本节点只能输出 pending / review-needed context 或 candidate signal。

## 7. Governance Authority Boundary

Governance-level changes 不属于本节点最终批准 authority。

本节点不能：

- 创建、修改或删除 stable profile facts
- 批准 profile governance event
- approve / reject alias
- confirm role
- create stable entity
- merge / split entity
- promote / modify / delete / downgrade active rule
- upgrade or relax automation policy
- invalidate durable memory

如果结构性问题暴露出长期 profile 或治理风险，本节点最多提出 candidate signal。
是否批准、如何写入、是否影响未来 automation，属于 Review / Governance Review / memory update workflow。

## 8. Memory / Log Boundary

Stage 2 采用三层边界：read / consume、candidate-only、no direct mutation。

### 8.1 Read / consume boundary

`Profile / Structural Match Node` 可以读取或消费以下 conceptual context：

- runtime evidence foundation
- objective transaction basis
- evidence references
- stable transaction identity
- current customer `Profile`
- profile authority / confirmation context
- current batch issue context from upstream evidence or identity nodes

它不读取 `Transaction Log` 做 runtime structural decision。
它不读取 `Case Log` 或 `Rule Log` 来决定是否为结构性交易。
它不把 `Knowledge Log / Summary Log` 当作 stable profile authority。

### 8.2 Candidate-only boundary

本节点只能作为候选或 issue signal 表达：

- profile fact candidate
- internal transfer relationship candidate
- loan relationship candidate
- bank account relationship issue
- profile conflict issue
- missing profile fact issue
- governance / review candidate

Candidate-only 表示后续 Coordinator、Review、Profile update 或 Governance Review workflow 应评估该信号。
它不是 profile write contract，也不是 durable approval。

### 8.3 No direct mutation boundary

本节点绝不能：

- 写入 `Transaction Log`
- 写入或修改 `Profile`
- 写入或修改 `Entity Log`
- 写入或修改 `Case Log`
- 写入或修改 `Rule Log`
- 写入或批准 `Governance Log`
- 创建 stable entity
- 批准 alias、role、rule、automation policy 或 entity governance change
- 把 profile candidate 当作 stable profile truth
- 把 structural candidate 当作 handled transaction

## 9. Insufficient / Ambiguous / Conflicting Evidence Behavior

Stage 2 采用优先级边界：profile authority first、structural certainty second、safe handoff third。

### 9.1 Profile authority first

如果缺少已确认 profile fact，本节点不能完成 structural handled path。

典型情况：

- 疑似内部转账，但 profile 中没有已确认关系。
- 疑似贷款还款，但贷款关系或还款语境未确认。
- onboarding 只产生了 profile candidate，尚未获得 authority。
- client 或系统说明尚未被 accountant / governance 确认。

这些情况应输出 pending / review-needed context 或 candidate signal，而不是结构性完成结果。

### 9.2 Structural certainty second

即使存在 stable profile fact，当前交易证据也必须足以落入该结构关系。

如果 bank raw signal、objective transaction basis、账户关系或金额/方向语境不足以支持结构性判断，本节点不能猜。

它应暴露 structural issue，而不是为了避免普通 workflow 不确定性而硬截断。

### 9.3 Safe handoff third

如果当前交易无法被结构性确定，且不存在必须先处理的 profile authority 问题，应交给 `Entity Resolution Node`。

Non-structural handoff 是正常路径，不是失败。

本节点不应把所有不熟悉或证据薄弱的交易都留在 profile layer；只有真正涉及客户结构事实的问题才属于本节点边界。

### 9.4 Conflict behavior

如果 current evidence 与 stable profile facts 冲突，本节点应保守处理。

典型边界：

- 冲突可能只是 evidence 缺失或配对不清：输出 pending context。
- 冲突可能说明 profile 已过期或错误：输出 review / governance candidate。
- 冲突影响当前交易是否结构性：不能完成 structural handled path。

不能让 LLM 或 deterministic fallback 选择一个“看起来更合理”的版本覆盖冲突。

### 9.5 Hard boundary

- Profile ambiguity 不等于可以猜。
- Profile candidate 不等于 stable profile truth。
- Bank raw signal 不等于 profile authority。
- 结构性疑似不等于结构性完成。
- 当前交易的结构性处理不能创建长期 profile authority。
- `Transaction Log` 不参与 runtime structural decision。

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
- stable profile fact 的 exact authority categories
- structural handled path 与 JE generation 的 exact handoff contract
- profile candidate 到 stable profile truth 的 confirmation workflow
- accountant 补充确认后是否重新触发本节点
- profile conflict 的人工处理与 governance workflow 边界
