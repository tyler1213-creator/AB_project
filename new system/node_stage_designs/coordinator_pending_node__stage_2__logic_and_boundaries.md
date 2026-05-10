# Coordinator / Pending Node — Stage 2：功能逻辑与决策边界

## 1. Stage 范围

本 Stage 2 定义 `Coordinator / Pending Node` 的功能逻辑与决策边界。

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

`Coordinator / Pending Node` 在当前交易或当前 batch 出现 clarification-needed / pending-needed / review-needed context 时触发。

概念触发条件是：

- 上游 workflow 已经整理出可追溯 evidence、稳定交易身份和当前处理语境；并且
- 至少一个上游节点说明当前交易不能安全继续自动完成；并且
- 该卡点可能通过 accountant clarification、补充 evidence、业务用途说明、身份/角色确认或 review context 得到推进；并且
- 当前问题尚未进入最终 review approval、journal entry generation、transaction logging 或 governance approval。

典型触发来源包括：

- Evidence Intake 暴露 missing evidence、conflicting evidence、unmatched evidence 或低质量 evidence。
- Transaction Identity 暴露 same-transaction / duplicate candidate、identity conflict 或补交 evidence 归属不清。
- Profile / Structural Match 暴露 profile fact 缺失、结构关系未确认或 profile conflict。
- Entity Resolution 暴露 ambiguous entity、unresolved identity、new entity candidate 需要 accountant context、unconfirmed role 或 alias authority 问题。
- Rule Match 暴露 rule blocked、rule ineligible、rule conflict、role / alias / policy authority gap 或 governance-needed context。
- Case Judgment 暴露 evidence insufficiency、case precedent 不适用、current evidence 与历史先例冲突、或判断不稳。

如果交易已经由 deterministic path 或 approved review path 完成，本节点不应重新打开分类判断。
如果问题是 governance approval，本节点最多收集 clarification 或候选信号，不能成为 approval gate。
如果问题不属于交易处理、accountant clarification、review 或治理语境，本节点不能吸收。

## 3. Input Categories

Stage 2 按判断作用组织 input categories，不列字段清单。

### 3.1 Current transaction and evidence context

说明当前 pending 对象是哪笔交易、有哪些 evidence、哪些 objective transaction basis 已确定、哪些 evidence issue 仍存在。

这类输入来自上游 evidence / identity flow。
它让问题可以绑定到稳定交易对象和可追溯 evidence，而不是变成泛泛业务询问。

### 3.2 Upstream pending / review context

说明上游节点为什么不能继续处理。

来源类别包括 evidence issue、identity issue、profile structural issue、entity ambiguity、rule blocked / miss reason、case judgment rationale、risk / policy context 和 review-required explanation。

本节点必须保留上游卡点的来源语境。
它不能把所有问题压平成“请说明这笔交易是什么”。

### 3.3 Accountant clarification basis

说明 accountant 需要补充或确认的内容类别，例如：

- 缺失 evidence 或附件归属
- 当前交易业务用途
- counterparty / vendor / payee 身份
- role / context
- profile structural fact
- rule exception 或 rule conflict
- case precedent 是否适用
- 当前交易是否应人工 review

这些类别只是 question target，不是字段契约或 routing enum。

### 3.4 Prior intervention context

说明同一交易、同一 batch 或同一客户近期是否已经发生过 accountant 提问、回答、修正或确认。

本节点可以读取这类 context 来避免重复提问、识别回答冲突，并保持 accountant interaction 可追溯。

Prior intervention context 不能替代当前 evidence、Entity Log、Case Log、Rule Log 或 Governance Log authority。

### 3.5 Authority and policy context

说明当前最多允许哪种后续动作：

- 继续补信息
- 进入 review
- 继续受限 runtime judgment
- 形成 candidate signal
- 进入 governance review

来源类别包括上游 authority limits、automation policy、rule lifecycle、alias / role authority、governance context 和 accountant / review boundary。

Authority context 是本节点输出的上限。
本节点不能通过提问绕过 hard block。

### 3.6 Accountant response context

说明 accountant 已经提供的回答、补充 evidence、业务说明、修正或确认。

Accountant response 可以成为当前交易的补充 context 或 intervention record。
但本节点不能把回答直接升级为 durable profile truth、stable entity authority、approved alias、confirmed role、active rule 或 governance approval。

## 4. Output Categories

Stage 2 只定义 conceptual output categories，不冻结 routing enum 或对象形状。

### 4.1 Focused accountant clarification

含义：本节点把上游卡点转化为 accountant 可以回答的聚焦问题。

边界：

- 问题必须服务于已知卡点。
- 问题不应要求 accountant 重新设计系统内部流程。
- 问题不应把未确认候选包装成事实。
- 问题本身不是 accountant decision。

### 4.2 Intervention record / answer context

含义：accountant 的提问、回答、修正、确认或补充 context 被保留为 intervention 语境。

边界：

- 这是 accountant interaction 的可追溯记录。
- 它不等于最终会计分类。
- 它不等于 durable memory mutation。
- 它不等于 governance approval。

### 4.3 Supplemental evidence / context handoff

含义：如果 accountant 提供新 evidence、附件归属说明或当前交易上下文，本节点可以把它作为后续 workflow 的补充 handoff。

边界：

- 补交原始 evidence 仍必须保持 evidence-first 语义。
- evidence amendment、re-intake 或 reprocessing 的 exact workflow 留到后续阶段。
- 本节点不能用自然语言回答覆盖原始 evidence。

### 4.4 Runtime continuation handoff

含义：accountant clarification 可能让交易回到受限的上游或下游 workflow，继续 evidence intake、identity handling、structural match、entity resolution、rule match、case judgment、review 或 completion flow。

边界：

- 继续处理不等于本节点完成分类。
- 继续处理不等于自动批准 review outcome。
- 是否重新触发哪个节点、以什么边界重跑，留到后续阶段。

### 4.5 Review / governance candidate handoff

含义：如果 accountant 回答暴露出长期 profile、entity、alias、role、rule、automation policy 或 case-memory 风险，本节点可以形成候选信号交给后续 review / governance workflow。

边界：

- Candidate handoff 只表示“后续应评估”。
- 它不写长期 memory。
- 它不批准治理事件。
- 它不改变 active rule 或 automation policy。

### 4.6 Still-pending / unresolved handoff

含义：如果 accountant 没有回答、回答不足、回答模糊、回答冲突或仍缺关键 evidence，本节点应保持 pending / review-needed 语义。

边界：

- 未解决不确定性不能被 confidence 语言掩盖。
- 本节点不能为了推动 workflow 而猜测。
- 下游应看到仍然缺什么、为什么不能继续。

## 5. Deterministic Code vs LLM Semantic Judgment

Stage 2 的核心边界是：

**code owns authority, routing limits, traceability, and no-mutation discipline; LLM may help formulate and interpret human-facing clarification inside those limits.**

### 5.1 Deterministic code responsibility

Deterministic code 负责：

- 判断本节点是否被触发：存在 pending / clarification-needed / review-needed context，且尚未进入最终 approval 或 logging。
- 汇总上游卡点、来源节点、交易身份、evidence references、authority limits 和 prior intervention context。
- 区分 ordinary pending、review-needed、governance-needed、supplemental evidence needed 和 still-unresolved context。
- 保持问题与上游卡点绑定，避免泛化或重复提问。
- 防止 accountant answer 被直接写入 `Profile`、Entity / Case / Rule / Governance memory。
- 防止本节点写入 `Transaction Log`。
- 防止 `Transaction Log` 被用作 runtime pending decision source。
- 记录 accountant interaction 的 intervention 语境，但不把 interaction record 当作 durable business memory approval。
- 标记哪些回答只能作为 candidate，哪些必须交给 Review / Governance Review。
- 执行 hard blocks：policy、governance、unresolved identity、ambiguous entity、unconfirmed role、rule-required condition 或 review-required condition 不能被本节点通过提问自行解除。

### 5.2 LLM semantic judgment responsibility

LLM 可以在 code 允许的边界内辅助：

- 把上游 pending reason 转成 accountant 能理解的简洁问题。
- 对多个 pending reasons 做可读合并，避免重复问同一事实。
- 解释 accountant 自然语言回答的可能含义。
- 总结回答是否补足了原卡点，或仍缺哪些信息。
- 生成 review explanation、governance candidate explanation 或 unresolved explanation。

### 5.3 Hard boundary

LLM 不能：

- 扩大 automation authority
- 把 accountant 模糊回答当作明确确认
- 把当前交易回答变成长期 profile truth
- approve / reject alias
- confirm role
- create stable entity
- merge / split entity
- promote、modify、delete 或 downgrade active rule
- upgrade or relax automation policy
- 批准 governance event
- 选择 COA / HST 处理来替代上游 judgment
- 生成 journal entry
- 写入 `Transaction Log`

## 6. Accountant Authority Boundary

Accountant 仍然拥有最终 accounting decision 和 durable authority。

`Coordinator / Pending Node` 可以向 accountant 请求当前交易所需的 clarification，并保留 accountant 的回答语境。

但本节点不能把 accountant response 自动解释为所有下游 authority 都已满足。

本节点不能：

- 替 accountant 作最终 review approval
- 把 accountant 当前交易回答直接变成长期客户政策
- 把 profile change signal 直接写入 `Profile`
- 把 entity / alias / role clarification 直接写成 stable Entity Log authority
- 把 case clarification 直接写成 confirmed Case Log memory
- 把 repeated answer 或当前回答直接升级成 active rule
- 把 accountant clarification 直接变成 governance approval

Accountant response 可以支持当前交易继续处理、进入 review、形成 candidate signal 或保留 unresolved pending。
具体采用哪条后续路径，必须受上游 authority、Review Node 和 Governance Review Node 边界限制。

## 7. Governance Authority Boundary

Governance-level changes 不属于 `Coordinator / Pending Node` authority。

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

本节点可以把 accountant 回答中暴露的高权限变化整理为 governance candidate signal。

是否进入治理队列、如何聚合展示、是否批准，以及批准后如何修改长期 memory 或 active rules，属于 Review / Governance Review / memory update workflow。

## 8. Memory / Log Boundary

Stage 2 采用四层边界：read / consume、write allowed、candidate-only、no direct mutation。

### 8.1 Read / consume boundary

`Coordinator / Pending Node` 可以读取或消费以下 conceptual context：

- runtime evidence foundation、objective transaction basis 和 stable transaction identity
- upstream pending / review context from Evidence Intake、Transaction Identity、Profile / Structural Match、Entity Resolution、Rule Match 和 Case Judgment
- current evidence issue、identity issue、profile issue、entity ambiguity、rule blocked / miss reason、case judgment rationale 和 risk / policy context
- `Intervention Log` 中与当前交易、batch 或客户相关的 prior questions、answers、corrections 和 confirmations
- `Profile`、Entity / Case / Rule / Governance context 中由上游节点已带入的 authority limits 或 review-needed context

它不读取 `Transaction Log` 做 runtime pending decision。
它不把 `Knowledge Log / Summary Log` 当作 deterministic rule source、stable profile authority 或 accountant approval。
它不把 prior intervention 自动当作 active governance state，除非后续 governance / review workflow 已经把它转化为有效 authority。

### 8.2 Write allowed boundary

`Coordinator / Pending Node` 可以在 intervention 语境内执行有限 durable write：

- 记录 accountant-facing question。
- 记录 accountant answer、clarification、correction 或 confirmation 的交互语境。
- 保留本次 pending 为什么发生、回答解决了什么、仍缺什么的介入语境。

这些写入只属于 `Intervention Log` 语义。
它们不包含最终会计结论，不创建 entity / case / rule / governance authority，也不写 `Transaction Log`。

### 8.3 Candidate-only boundary

本节点只能作为候选或 handoff signal 表达：

- supplemental evidence / re-intake candidate
- profile change signal or profile confirmation candidate
- entity / alias / role confirmation candidate
- case memory update candidate
- rule candidate or rule conflict candidate
- automation-policy / governance candidate
- review-needed or unresolved-pending signal

Candidate-only 表示后续 Review、Governance Review、Evidence Intake、Case Memory Update 或相关 memory workflow 应评估该信号。
它不是 durable approval，也不是 memory operation contract。

### 8.4 No direct mutation boundary

本节点绝不能：

- 写入 `Transaction Log`
- 修改 `Profile`
- 写入或修改 `Entity Log`
- 写入或修改 `Case Log`
- 写入或修改 `Rule Log`
- 写入或批准 `Governance Log`
- 创建 stable entity
- approve / reject alias
- confirm role
- merge / split entity
- 修改 automation policy
- 创建、升级、修改、删除或降级 active rule
- 生成 journal entry
- 把 accountant answer 直接变成 final accounting result

## 9. Insufficient / Ambiguous / Conflicting Evidence Behavior

Stage 2 采用优先级边界：ask only for repairable gaps、preserve authority limits、escalate conflicts。

### 9.1 Ask only for repairable gaps

如果当前卡点可以通过 accountant 补充一个具体事实推进，本节点应提出聚焦问题。

典型情况：

- 缺 receipt、invoice、contract、cheque context 或附件归属说明。
- 业务用途不明。
- counterparty / vendor / payee 身份需要确认。
- role/context 需要 accountant 说明。
- profile structural fact 需要确认。
- case precedent 是否适用缺少一个具体条件。

如果问题不是可补信息，而是需要 review approval 或 governance decision，本节点不应伪装成普通 pending 问题。

### 9.2 Preserve authority limits

Accountant 回答可以补充当前交易 context，但不能让本节点绕过已知 authority limits。

典型边界：

- `new_entity_candidate` 不因一次回答获得 stable entity authority。
- candidate alias 不因一次 pending 回答直接成为 approved alias。
- candidate role 不因本节点解释直接成为 confirmed role。
- profile candidate 不因本节点记录直接成为 stable profile truth。
- rule candidate 不因 accountant 当前回答直接成为 active rule。
- automation policy upgrade or relaxation 必须走 approval。

如果回答足以形成候选，应交给后续 review / governance workflow。

### 9.3 Escalate conflicts

如果 accountant response 与 raw evidence、profile、Entity Log、Case Log、Rule Log、Governance context 或 prior intervention 冲突，本节点应保守处理。

典型边界：

- 冲突只是缺少一个可补事实：保持 pending，并提出更具体 clarification。
- 冲突影响当前交易分类：进入 Review Node 语境，而不是自动选择一方。
- 冲突暗示长期 memory 错误：形成 governance / memory candidate。
- 冲突影响 evidence authenticity 或 identity safety：不能继续 operational path。

LLM 不能选择一个“看起来更合理”的版本覆盖冲突。

### 9.4 Ambiguous or missing answer

如果 accountant 未回答、回答不完整、回答指代不明或回答无法绑定到具体交易 / evidence / issue，本节点不能自行填补。

它应保持 still-pending / unresolved 语义，并说明仍缺哪类信息。

### 9.5 Hard boundary

- Pending 是补信息机制，不是治理批准机制。
- Accountant answer 是高价值 context，但不是本节点的 durable memory mutation 权限。
- Intervention Log 记录介入过程，不等于 Case Log、Rule Log、Entity Log 或 Transaction Log。
- Transaction Log 不参与 runtime pending decision。
- Review-required 不能被本节点降级成普通自动化路径。
- Governance-needed 不能被本节点降级成普通 pending completion。
- 模糊、冲突或缺失回答不能被包装成 confidence。

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
- accountant 回答后是否重新触发哪个上游节点，以及重跑边界
- `Intervention Log` exact contract，以及它与 Evidence Log、Review Node、Governance Log 的交接边界
- 补交 evidence 是否由本节点接收后转交，还是必须重新进入 Evidence Intake / Preprocessing
- ordinary pending、review-required、governance-needed 和 still-unresolved 的 exact routing contract
- accountant response 何时足以支持当前交易继续处理，何时必须进入 Review Node
- 多笔 pending 交易的问题聚合、去重、排序和展示边界
