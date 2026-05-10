# Transaction Logging Node — Stage 2：功能逻辑与决策边界

## 1. Stage 范围

本 Stage 2 定义 `Transaction Logging Node` 的功能逻辑与决策边界。

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

`Transaction Logging Node` 在当前交易具备 final logging authority，且需要形成 audit-facing `Transaction Log` 记录时触发。

概念触发条件是：

- 当前交易已经完成 evidence intake、transaction identity 和必要的上游 classification / review workflow；并且
- 当前交易已有稳定 `transaction_id` 和可追溯 evidence foundation；并且
- 当前交易 outcome 已具备 finalization authority；并且
- 必要的 journal entry result 已由 `JE Generation Node` 形成，或后续阶段明确允许某类 terminal non-JE outcome 被最终记录；并且
- 当前交易尚未完成 final transaction logging。

典型触发来源包括：

- profile-backed structural path 已形成可落账结果，并完成必要 JE / review boundary。
- deterministic rule-handled path 已形成可落账结果，并完成必要 JE / review boundary。
- case-supported path 在当前 authority 边界内已形成可继续结果，并完成必要 JE / review boundary。
- pending clarification 或 review 已回收 accountant-provided context，形成可 final logging 的 outcome。
- accountant 已在 `Review Node` 中批准或修正当前交易 outcome，并且 `JE Generation Node` 已完成可用分录结果。

以下情况不能触发正常 final transaction logging：

- 当前交易仍 pending、still-pending、not-approved 或 unresolved。
- 当前交易存在 unresolved identity、ambiguous evidence、conflicting evidence、authority block、governance block 或 review-required condition。
- 当前交易尚未生成必要 journal entry result，或 JE generation 暴露 not-finalizable / consistency issue。
- 当前内容只是 candidate signal、review package、report draft、governance candidate、case memory candidate、rule candidate 或 lint finding。

Stage 2 不冻结 exact routing：JE-blocked / not-finalizable 是否存在 terminal audit record，以及何时由本节点处理，留到后续阶段定义。

## 3. Input Categories

Stage 2 按判断作用组织 input categories，不列字段清单。

### 3.1 Transaction identity and objective basis

说明当前日志对象是哪一笔交易，以及这笔交易的客观基础是什么。

来源类别包括 Evidence Intake / Preprocessing、Transaction Identity、objective transaction basis、bank account context、amount / direction basis 和 evidence references。

本节点只使用这类输入绑定审计记录和核对 traceability。
它不能用这些输入重新做 entity resolution、classification、tax judgment 或 JE computation。

### 3.2 Final outcome basis

说明当前交易最终被怎样处理，以及该 outcome 来自哪条 authority path。

来源类别包括 structural result、rule-handled result、case-supported result、pending clarification result、accountant-approved result、accountant-corrected result 或其他已授权 final outcome。

核心边界：

- final outcome 必须已经具备当前交易 finalization authority。
- pending、review-required、candidate-only、governance-needed 或 not-approved context 不能支持正常 final logging。
- 本节点不能把 upstream rationale 重新解释成新的 accounting outcome。

### 3.3 Journal entry completion basis

说明当前交易是否已有可供审计和输出使用的 journal entry result，以及分录生成是否通过必要一致性边界。

来源类别包括 `JE Generation Node` 的 journal entry result、JE calculation rationale、consistency status 和 JE-blocked / not-finalizable handoff。

本节点不能生成、修正、补齐或重算 JE。

如果 JE basis 不足或冲突，正常 final logging 应停止。JE-blocked 是否需要另行形成 terminal audit record，是后续阶段的 Open Boundary。

### 3.4 Authority and review basis

说明当前 outcome 为什么可以被最终记录，或为什么不能被最终记录。

来源类别包括 automation policy、rule lifecycle、review decision、accountant correction、pending resolution、upstream blocked reason、governance restriction 和 review / intervention trace。

Authority basis 是本节点输出的上限。
本节点不能通过日志落盘把 review-required、governance-needed、candidate-only 或 not-approved context 变成 final outcome。

### 3.5 Audit-support trace basis

说明最终日志需要保留哪些关键审计轨迹。

来源类别包括 Evidence Log references、Profile / Structural context、Entity Resolution context、Rule Match rationale、Case Judgment rationale、AI-side judgment / policy activation trace、Coordinator / Pending intervention context、Review decision context、JE rationale 和 governance-related references。

这类输入只用于审计可追溯性。
它不能成为本节点重新做 runtime decision、学习、rule promotion 或 governance approval 的来源。

### 3.6 Downstream handoff basis

说明本次 final logging 后，哪些后续 workflow 可能需要读取已完成交易的审计语境。

来源类别包括 case memory candidate context、governance candidate context、post-batch lint context、knowledge compilation context 和 output flow context。

本节点可以保留或传递 candidate context，但不能执行这些后续 workflow 的 durable mutation。

## 4. Output Categories

Stage 2 只定义 conceptual output categories，不冻结 routing enum 或对象形状。

### 4.1 Final transaction audit record

含义：当前交易的最终处理结果和关键审计轨迹被写入 audit-facing `Transaction Log`。

边界：

- 这是 durable audit record。
- 它记录当前交易当时的 final outcome、authority trace、evidence / review / intervention context 和 JE completion context。
- 它不参与未来 runtime decision。
- 它不是 Case Log memory write。
- 它不是 Rule Log、Entity Log、Governance Log 或 Profile mutation。
- 它不是 report draft、review package、handoff queue 或 candidate registry。

### 4.2 Final logging blocked handoff

含义：当前交易不能形成正常 final transaction audit record，因为 final logging 必需条件缺失、冲突或未获 authority。

典型原因包括：

- transaction identity 不稳定或无法绑定
- final outcome authority 不足
- review / accountant approval 缺失或冲突
- journal entry result 缺失、冲突或 not-finalizable
- evidence references 无法支撑 audit traceability
- governance block 或 unresolved conflict 存在

边界：

- Blocked handoff 是安全停止，不是审计记录补丁。
- 本节点不能用“先记下来再说”绕过 finalization authority。
- 后续应由 Review、Coordinator、JE Generation、上游 workflow 或 governance workflow 处理。

### 4.3 Audit-support query surface

含义：`Transaction Log` 可被后续节点、人类 review、输出 flow、knowledge compilation 或 post-batch lint 查询，用于理解已完成交易的历史处理依据。

边界：

- 查询是审计 / 分析用途，不是 runtime classification authority。
- 查询结果不能直接作为 rule source、case memory write 或 governance approval。
- 后续治理变化不应重写历史交易日志。

### 4.4 Candidate handoff preservation

含义：如果 final logging 过程中存在 case memory、entity / alias / role、rule、automation-policy、profile、tax config 或 governance 候选，本节点可以保留其与已完成交易的关系，供后续 workflow 评估。

边界：

- Candidate handoff 只表示“后续应评估”。
- 它不写长期 business memory。
- 它不批准 governance event。
- 它不改变 active rule、entity authority、Profile 或 automation policy。

### 4.5 Logging consistency issue signal

含义：本节点发现 final outcome、JE completion context、evidence references、review / intervention trace 或 transaction identity 之间存在不一致。

边界：

- 该 signal 只说明不能安全 final logging。
- 它不自行修正 upstream outcome。
- 它不自行重算 JE。
- 它不创建 governance event。

## 5. Deterministic Code vs LLM Semantic Judgment

Stage 2 的核心边界是：

**code owns final logging eligibility, persistence discipline, traceability, idempotency boundary, and no-mutation enforcement; LLM may only help summarize audit explanations inside those limits.**

### 5.1 Deterministic code responsibility

Deterministic code 负责：

- 判断本节点是否被触发：当前交易是否具备 final logging authority，且尚未完成 final transaction logging。
- 检查当前交易是否有稳定 transaction identity 和可追溯 evidence foundation。
- 检查 final outcome、review / intervention trace、authority basis 和 JE completion context 是否足以支持 final logging。
- 阻止 pending、review-required、governance-needed、candidate-only、not-approved、not-finalizable 或 conflicting context 进入正常 final audit record。
- 执行 Transaction Log 的 durable write discipline。
- 保持日志记录与当前交易、evidence references、upstream path、review decision、JE result 和 authority trace 的绑定。
- 防止 Transaction Log 被用作 runtime decision、learning layer、rule source 或 governance approval。
- 防止 transient handoff、queue、draft、candidate 或 report artifact 被称为 `Log`。
- 识别 final logging 前的 traceability 缺失、重复落盘风险、authority conflict 或 JE consistency issue。
- 防止本节点修改 Profile、Entity Log、Case Log、Rule Log 或 Governance Log。

### 5.2 LLM semantic judgment responsibility

LLM 通常不应参与 final logging eligibility 或 durable write decision。

如果后续阶段允许 LLM 辅助，它最多可以在 code 允许的边界内帮助：

- 把上游 rationale、review / intervention context 和 JE explanation 总结成人类可读审计说明。
- 将多个 audit-support traces 合并成清晰 narrative。
- 解释为什么 final logging 被阻止。
- 生成候选信号的自然语言说明。

### 5.3 Hard boundary

LLM 不能：

- 决定当前交易是否具备 final logging authority
- 把 pending、not-approved 或 review-required 交易推进到 final logging
- 把 JE-blocked reason 改写成可落账结果
- 选择 COA 科目
- 判断 HST/GST tax treatment
- 生成或修正 journal entry
- 替 accountant approve current outcome
- 把 candidate 变成 durable memory
- approve / reject alias
- confirm role
- create stable entity
- merge / split entity
- create / promote / modify / delete / downgrade active rule
- upgrade or relax automation policy
- 批准 governance event
- 修改 `Profile`、Entity Log、Case Log、Rule Log 或 Governance Log

## 6. Accountant Authority Boundary

Accountant 仍然拥有最终 accounting decision 和 durable authority。

`Transaction Logging Node` 可以记录 accountant-approved 或 otherwise-authorized current outcome，但不能替 accountant 作决定。

本节点不能：

- 把系统高置信结果解释为 accountant approval
- 把 accountant silence、模糊回答或未完成 review 解释为 approval
- 把 review package 本身当作最终会计决定
- 把当前交易 correction 直接变成长期客户政策
- 把 repeated correction 自动升级成 active rule
- 把 alias / role / entity clarification 直接批准为 durable authority
- 把日志落盘解释为 accountant 已批准所有治理候选

对当前交易，明确 approval / correction 可以成为 final logging 的 authority basis。
对长期记忆和治理事项，日志只能保留审计语境或候选关系，不能执行 durable change。

## 7. Governance Authority Boundary

Governance-level changes 不属于 `Transaction Logging Node` authority。

本节点不能：

- 修改 `Profile`
- approve / reject alias
- confirm role
- create stable entity authority
- merge / split entity
- archive / reactivate entity
- change automation policy
- create / promote / modify / delete / downgrade active rule
- approve governance event
- invalidate durable memory
- rewrite historical transaction logs to follow later governance changes

如果 final logging 暴露出 entity、alias、role、rule、profile、tax config、automation policy 或 governance risk，本节点只能保留 candidate handoff 或 consistency issue signal。

后续是否进入治理队列、如何审批、是否修改长期 memory 或 active rule，属于 `Governance Review Node`、相关 memory update workflow 和 accountant / governance approval。

## 8. Memory / Log Boundary

Stage 2 采用四层边界：read / consume、write allowed、candidate-only、no direct mutation。

### 8.1 Read / consume boundary

`Transaction Logging Node` 可以读取或消费以下 conceptual context：

- current transaction identity、objective transaction basis 和 evidence references
- final outcome from structural / rule / case / pending / review workflow
- journal entry result、JE rationale 和 JE consistency context
- upstream rationale and authority trace from Profile / Structural Match、Entity Resolution、Rule Match、Case Judgment、Coordinator / Pending Node 和 Review Node
- `Intervention Log` 中与当前交易相关的 questions、answers、corrections、confirmations 和 review context
- Entity / Case / Rule / Governance context 的引用或摘要，但只能作为 final audit trace 或 candidate context，不能重新做 runtime decision
- prior `Transaction Log` records only for duplicate-final-log prevention, audit continuity, historical display, or downstream analysis boundaries

它不能读取 `Transaction Log` 来做当前 runtime classification、rule match、case judgment、JE decision 或 learning。

### 8.2 Write allowed boundary

本节点可以执行的 durable write 只有 audit-facing `Transaction Log` 语义：

- 记录本笔交易最终处理结果。
- 记录 final outcome 的 workflow path 和 authority trace。
- 记录支持该结果的 evidence / review / intervention / JE 审计语境。
- 记录与后续 case memory、governance、knowledge compilation 或 lint 评估相关的候选关系。

这些写入只属于 `Transaction Log`。
它们不写 Case Log、Rule Log、stable Entity Log、Governance Log 或 Profile。

### 8.3 Candidate-only boundary

本节点只能作为候选或 handoff signal 表达：

- case memory update candidate context
- entity / alias / role candidate context
- rule candidate、rule conflict 或 rule-health candidate context
- profile confirmation / profile change candidate context
- tax config or account-mapping review candidate context
- automation-policy / governance candidate context
- post-batch lint candidate context
- logging consistency issue signal

Candidate-only 表示后续 Case Memory Update、Governance Review、Knowledge Compilation、Post-Batch Lint 或相关 memory workflow 应评估该信号。

它不是 durable approval，也不是 memory operation contract。

### 8.4 No direct mutation boundary

本节点绝不能：

- 修改 `Profile`
- 写入或修改 `Case Log`
- 写入或修改 `Rule Log`
- 写入或修改 stable `Entity Log` authority
- 写入或批准 `Governance Log` mutation
- 生成或修改 journal entry
- 创建 stable case memory
- 创建 stable rule
- 创建 stable entity
- approve / reject alias
- confirm role
- merge / split entity
- 修改 automation policy
- 把 review / intervention record 当作 final transaction log 的替代品
- 把 Transaction Log 变成 runtime decision source 或 learning layer
- 重写历史日志以追随后续治理变化

## 9. Insufficient / Ambiguous / Conflicting Evidence Behavior

Stage 2 采用优先级边界：final authority first、traceability second、historical integrity third。

### 9.1 Final authority first

如果当前交易尚未具备 final logging authority，本节点不能写正常 final transaction audit record。

典型情况：

- transaction outcome still pending
- review not approved
- accountant correction ambiguous
- unresolved / ambiguous identity 仍影响 current outcome
- review-required policy 尚未处理
- governance block 存在
- 当前内容只是 candidate signal
- JE generation not-finalizable 或 consistency issue 未解决

这些情况应输出 final logging blocked handoff，而不是生成半成品审计记录。

### 9.2 Traceability second

如果 authority 允许继续，但交易身份、evidence references、upstream path、review / intervention trace 或 JE completion context 无法被可靠绑定，本节点仍不能正常 final logging。

典型情况：

- final outcome 无法绑定到稳定 `transaction_id`
- evidence references 缺失到无法支持审计解释
- review / accountant approval 无法绑定到具体交易或问题
- journal entry result 与当前交易或 authority trace 无法对应
- upstream rationale 与 final outcome 不一致

本节点不能用自然语言摘要、confidence 或 report draft 填补 traceability 缺口。

### 9.3 Historical integrity third

如果当前 final logging context 与既有 Transaction Log、governance history、entity / rule state 或 intervention history 发生冲突，本节点应保守处理。

典型边界：

- 同一交易疑似已完成 final logging：阻止重复正常落盘，输出 consistency issue。
- 后续 governance state 与历史交易当时引用不一致：不重写历史日志，通过 governance event 或后续解释处理。
- accountant correction 与 prior intervention 或 evidence 冲突：退回 Review / Coordinator，而不是选择一个版本落盘。
- rule / entity / alias / role authority 在处理过程中变化：记录或保留当时 authority trace；是否重新处理当前交易留到后续 workflow。

### 9.4 Blocked and not-finalizable caution

JE-blocked、not-finalizable、review-required、governance-needed 或 still-pending 状态不能被普通 final audit record 掩盖。

如果后续阶段决定某些 terminal non-posting outcomes 也需要 audit-facing durable record，该边界必须单独定义，不能混入正常 completed-transaction logging。

### 9.5 Hard boundary

- Transaction Logging 是 final audit persistence，不是 hidden review、classification、JE 或 governance layer。
- 能写日志不等于 outcome 有 accountant authority。
- Transaction Log 不参与 runtime decision，也不是学习层。
- Intervention Log 记录介入过程，不等于 final Transaction Log。
- Case Log 保存已完成交易可沉淀的案例，不等于 Transaction Log。
- Governance Log 保存高权限变化审批，不等于 Transaction Log。
- 模糊、冲突、缺失或未批准状态不能被包装成 final audit record。

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
- 哪些 upstream outcome 可被视为具备 `final logging authority`
- Review Node 是否覆盖所有 final logging 前交易，还是只覆盖 review-required / sampled / governance-candidate items
- high-confidence structural / rule / case-supported result 是否可以不经逐笔 review 直接进入 JE 和 final logging
- accountant approval、correction、rejection、still-pending 与 final logging 的 exact handoff contract
- JE-blocked / not-finalizable handoff 是否需要 terminal audit record，以及它与正常 completed-transaction logging 的边界
- review / intervention record 与 final `Transaction Log` 的 exact persistence contract
- final logging blocked handoff 应返回 Coordinator、Review、JE Generation、upstream rework 还是 governance workflow
- Transaction Log 与 Case Memory Update、Governance Review、Knowledge Compilation、Post-Batch Lint、output flow 的 exact downstream handoff contract
- duplicate final logging prevention、correction / reversal / superseded transaction、split transaction 和 reprocessing 的 exact behavior
