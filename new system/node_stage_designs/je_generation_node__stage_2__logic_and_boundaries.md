# JE Generation Node — Stage 2：功能逻辑与决策边界

## 1. Stage 范围

本 Stage 2 定义 `JE Generation Node` 的功能逻辑与决策边界。

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

`JE Generation Node` 在当前交易具备 finalizable accounting outcome，且需要转换为 journal entry 时触发。

概念触发条件是：

- 当前交易已经完成 evidence intake、transaction identity 和必要的上游 classification / review workflow；并且
- 当前交易已有可追溯、可绑定到当前交易的 accounting outcome；并且
- 当前 outcome 的 authority 足以支持本笔交易进入 JE finalization；并且
- 当前交易尚未完成 final transaction logging。

典型触发来源包括：

- profile-backed structural path 已形成可落账结果。
- deterministic rule-handled path 已形成可落账结果。
- case-supported path 在当前 authority 边界内已形成可继续结果。
- pending clarification 或 review 已回收 accountant-provided context，并形成可继续结果。
- accountant 已在 `Review Node` 中批准或修正当前交易 outcome。

以下情况不能触发正常 JE generation：

- 当前交易仍是 pending、still-pending、not-approved 或 unresolved。
- 当前交易存在 unresolved identity、ambiguous evidence、conflicting evidence、authority block、governance block 或 review-required condition。
- 当前分类、COA、tax treatment、amount basis 或 direction basis 不足以生成一致分录。
- 当前 outcome 只是 candidate signal、review draft、governance candidate、case memory candidate 或 rule candidate。

Stage 2 不冻结 exact routing：哪些高可信系统结果可直接进入 JE，哪些必须先经 `Review Node`，留到后续阶段定义。

## 3. Input Categories

Stage 2 按判断作用组织 input categories，不列字段清单。

### 3.1 Objective transaction basis

说明当前交易的客观金额、方向、日期、账户语境和交易身份基础。

来源类别包括 Evidence Intake / Preprocessing、Transaction Identity、Profile / Structural context 和当前交易证据引用。

这些输入用于分录计算和一致性检查。
本节点不能用它们重新判断 business purpose、entity identity 或 classification。

### 3.2 Finalizable accounting outcome basis

说明当前交易最终或当前可 finalization 的会计处理结果是什么，以及来自哪条上游 authority path。

来源类别包括 structural result、rule-handled result、case-supported result、pending clarification result、accountant-approved result 或 accountant-corrected result。

核心边界：

- 可 finalization 的 outcome 可以支持 JE。
- 未批准、仍 pending、review-required、candidate-only 或 governance-needed context 不能支持 JE。
- 本节点不能把上游 rationale 重新解释成新的 accounting outcome。

### 3.3 COA and account-mapping basis

说明当前 outcome 应落到哪些已存在或已授权的会计科目语境。

来源类别包括 approved accounting outcome、客户 COA / accounting configuration、structural context、rule result 或 accountant correction。

本节点只能使用已经具备 authority 的 account basis。
它不能自行创建 COA 科目、选择替代科目、合并科目或修正客户账套结构。

### 3.4 Tax treatment basis

说明当前交易的 GST/HST 处理是否已由上游 outcome、客户 tax config、approved rule、structural logic 或 accountant decision 给出。

这类输入用于 tax line computation 和 consistency check。

本节点不能自行判断：

- 当前交易是否 taxable、exempt、zero-rated 或 out-of-scope
- 应使用哪个 tax rate
- 应落入 HST/GST Receivable、HST/GST Payable 或其他 tax control treatment
- receipt / invoice 是否足以支持 ITC 或 tax claim

如果 tax basis 不足或冲突，本节点应阻止 JE finalization。

### 3.5 Authority and review basis

说明当前 outcome 为什么可以进入 JE，或为什么不能进入 JE。

来源类别包括 automation policy、rule lifecycle、review decision、accountant correction、pending resolution、upstream blocked reason 和 governance restriction。

Authority basis 是本节点输出的上限。
本节点不能通过计算把 review-required 或 governance-needed context 降级为可落账结果。

### 3.6 Audit-support context

说明后续 `Transaction Logging Node` 需要知道本次 JE 来自哪个 outcome、哪些 evidence reference、哪些 review / intervention context 和哪些 upstream rationale。

这类输入只用于保留 traceability。
它不能成为本节点重新做 runtime classification 或 memory learning 的来源。

`Transaction Log` 的既有 finalized audit history 不能作为本节点当前 runtime decision source。

## 4. Output Categories

Stage 2 只定义 conceptual output categories，不冻结 routing enum 或对象形状。

### 4.1 Journal entry result

含义：当前交易的 finalizable accounting outcome 已被转换成借贷平衡、tax treatment 一致、可供 final logging 和输出使用的 journal entry。

边界：

- 这是当前交易的分录计算结果。
- 它不等于 accountant review approval。
- 它不等于 `Transaction Log` write。
- 它不等于 Case Log memory write。
- 它不等于 rule、entity、alias、role 或 automation-policy approval。

### 4.2 JE-blocked / not-finalizable handoff

含义：当前交易尚不能生成 journal entry，因为缺少或冲突的是 finalization 必需条件。

典型原因包括：

- accounting outcome 尚未 finalizable
- account basis 缺失或冲突
- tax treatment basis 缺失或冲突
- amount / direction basis 不一致
- authority / review basis 不足
- governance block 或 review-required condition 尚未解决

边界：

- Blocked handoff 是安全停止，不是分类判断。
- 本节点不能用 fallback 科目、默认税务处理或 confidence 语言绕过阻断。
- 后续应由 Review、Coordinator、上游 workflow 或 governance workflow 处理。

### 4.3 Consistency issue signal

含义：本节点在分录计算前后发现 current outcome、objective transaction basis、tax treatment、account basis 或 authority trace 之间存在不一致。

边界：

- 该 signal 只说明 JE 不能安全 finalization。
- 它不自行修正 accounting outcome。
- 它不自行创建 governance event。
- 它不写长期 memory。

### 4.4 Audit-support handoff

含义：本节点可以把 JE result、JE-blocked reason、calculation rationale 和 upstream authority trace 交给 `Transaction Logging Node` 或输出 flow。

边界：

- Handoff 不等于 durable audit log。
- Final audit-facing write 属于 `Transaction Logging Node`。
- Handoff 不能被 `Case Log`、`Rule Log`、Entity / Governance memory 直接当成 durable authority。

### 4.5 Candidate signal

含义：如果 JE generation 暴露出长期配置或治理问题，本节点可以提出候选信号。

典型候选包括：

- COA / account-mapping review candidate
- tax configuration review candidate
- rule condition gap candidate
- structural-profile issue candidate
- review / governance candidate

边界：

- Candidate signal 只表示后续应评估。
- 它不修改 COA、Profile、Rule Log、Entity Log、Case Log 或 Governance Log。
- 它不批准 governance event。

## 5. Deterministic Code vs LLM Semantic Judgment

Stage 2 的核心边界是：

**code owns JE computation, balancing, consistency checks, and authority gating; LLM does not own accounting classification, tax treatment, or journal-entry math.**

### 5.1 Deterministic code responsibility

Deterministic code 负责：

- 判断本节点是否被触发：当前交易是否已有 finalizable accounting outcome，且尚未 final logging。
- 检查当前 outcome 是否具备 JE generation 所需 authority。
- 检查 pending、review-required、governance-needed、candidate-only 或 not-approved context 不会进入 JE。
- 使用 objective transaction basis、approved account basis 和 approved tax basis 计算借贷分录。
- 保持金额方向语义一致，避免重复 sign 解释。
- 保持借贷平衡。
- 保持 GST/HST treatment 与 approved outcome 和客户 tax config 一致。
- 识别 tax、amount、direction、account basis 或 authority trace 的缺失 / 冲突。
- 区分 JE result、JE-blocked handoff、consistency issue signal 和 candidate signal。
- 防止本节点写入 `Transaction Log` 或长期 memory。
- 防止 `Transaction Log`、Knowledge Summary、case precedent 或 candidate signal 被当作当前 JE authority。

### 5.2 LLM semantic judgment responsibility

LLM 通常不应参与 JE 生成本身。

如果后续阶段允许 LLM 辅助，它最多可以在受限边界内帮助：

- 把 JE-blocked reason 总结成 accountant / reviewer 可读说明。
- 解释分录计算为什么不能继续。
- 将多个 consistency issue 合并成更清晰的 review / pending explanation。
- 生成候选信号的自然语言说明。

### 5.3 Hard boundary

LLM 不能：

- 选择 COA 科目
- 判断 HST/GST tax treatment
- 决定 current outcome 是否 finalizable
- 把 pending 或 review-required 交易推进到 JE
- 修正 amount、direction 或 tax basis
- 为了平衡分录而发明调整行
- 使用 fallback account 或默认 tax treatment 补缺口
- 替 accountant approve current outcome
- 创建或修改 rule
- 修改 Profile、Entity Log、Case Log、Rule Log 或 Governance Log
- 写入 `Transaction Log`

## 6. Accountant Authority Boundary

Accountant 仍然拥有最终 accounting decision 和 durable authority。

`JE Generation Node` 可以把 accountant-approved 或 otherwise-authorized current outcome 转换为 journal entry，但不能替 accountant 作会计判断。

本节点不能：

- 选择或修正当前交易分类
- 选择或修正 COA account
- 选择或修正 GST/HST treatment
- 把 accountant 模糊回答解释为批准
- 把系统高置信建议解释为 accountant approval
- 把 JE 成功生成解释为 accountant 已审核
- 把当前交易 JE 结果变成长期客户政策

如果分录生成暴露出需要 accountant 判断的问题，本节点应停止并输出 JE-blocked / review-needed context。

## 7. Governance Authority Boundary

Governance-level changes 不属于 `JE Generation Node` authority。

本节点不能：

- 修改 `Profile`
- 创建、升级、修改、删除或降级 active rule
- approve / reject alias
- confirm role
- create stable entity authority
- merge / split entity
- archive / reactivate entity
- change automation policy
- 修改 tax configuration 或 account-mapping authority
- 批准 governance event
- invalidate durable memory

如果 JE generation 暴露出 account mapping、tax config、rule condition、profile structural fact 或 automation policy 的长期问题，本节点只能提出 candidate signal，交给 Review / Governance Review / relevant memory workflow。

## 8. Memory / Log Boundary

Stage 2 采用三层边界：read / consume、candidate-only、no direct mutation。

### 8.1 Read / consume boundary

`JE Generation Node` 可以读取或消费以下 conceptual context：

- objective transaction basis、stable transaction identity 和 current evidence references
- finalizable accounting outcome from upstream workflow
- approved account basis、customer COA / accounting configuration 和 structural accounting context
- approved tax treatment basis 和客户 tax config
- review / intervention context that establishes current outcome authority
- upstream rationale and authority trace needed for audit-support handoff

它可以消费 Entity / Case / Rule / Governance context 的摘要或引用，但只能作为 upstream authority trace 或 blocked reason context，不能重新做 entity resolution、case judgment、rule match 或 governance decision。

`Transaction Log` 可以作为 finalized audit history 被查询或展示，但不能参与当前 runtime JE decision，也不能作为 learning layer。

### 8.2 Candidate-only boundary

本节点只能作为候选或 handoff signal 表达：

- account-mapping review candidate
- tax configuration review candidate
- profile structural issue candidate
- rule condition gap or rule conflict candidate
- review-needed or governance-needed candidate
- evidence / amount / direction inconsistency candidate

Candidate-only 表示后续节点应评估该信号。
它不是 durable approval，也不是 memory operation contract。

### 8.3 No direct mutation boundary

本节点绝不能：

- 写入 `Transaction Log`
- 写入或修改 `Case Log`
- 写入或修改 `Rule Log`
- 写入或修改 stable `Entity Log` authority
- 写入或批准 `Governance Log` mutation
- 修改 `Profile`
- 修改 COA / tax config / automation policy
- 创建 stable case memory
- 创建 stable rule
- 批准 alias、role、entity 或 governance event
- 把 JE result 或 JE-blocked reason 当作长期 authority

## 9. Insufficient / Ambiguous / Conflicting Evidence Behavior

Stage 2 采用优先级边界：authority first、accounting basis second、calculation consistency third。

### 9.1 Authority first

如果当前 outcome 尚未具备 JE finalization authority，本节点不能生成 journal entry。

典型情况：

- transaction outcome still pending
- review not approved
- accountant correction ambiguous
- unresolved / ambiguous identity 仍影响 current outcome
- review-required policy 尚未处理
- governance block 存在
- 当前内容只是 candidate signal

这些情况应输出 JE-blocked / not-finalizable handoff。

### 9.2 Accounting basis second

如果 authority 允许继续，但 account basis、tax basis、amount basis 或 direction basis 不足，本节点仍不能生成 journal entry。

典型情况：

- COA account 未确定或存在冲突
- GST/HST treatment 未确定或与 evidence / config 冲突
- tax control treatment 不明确
- 金额、方向或退款 / reversal 语义不一致
- 当前交易需要 split 或 multi-line 处理，但上游 outcome 未给出足够会计 basis

本节点不能用默认值、fallback account、fallback tax treatment 或 LLM guess 补齐。

### 9.3 Calculation consistency third

如果输入 basis 看似足够，但计算结果不能保持借贷平衡、tax treatment 一致或 traceability 完整，本节点应阻止 finalization。

典型情况：

- debit / credit 不平衡
- tax line 与 approved tax basis 不一致
- gross / net / tax 关系不一致
- 交易方向与分录方向矛盾
- JE result 无法绑定到当前 transaction identity 或 authority trace

这些情况应输出 consistency issue signal，而不是自动调整到平衡。

### 9.4 Conflict preservation

如果 current outcome 与 raw evidence、Profile、COA / tax config、review decision、rule result、case rationale 或 accountant correction 冲突，本节点不能选择一个版本继续。

冲突只缺具体事实时，返回 pending / clarification context。
冲突影响 current outcome authority 时，返回 review-required context。
冲突暗示长期配置或治理问题时，形成 candidate signal。

### 9.5 Hard boundary

- JE generation 是 pure computation，不是 hidden classification layer。
- 能算出平衡分录不等于该 outcome 有 accountant authority。
- 不能为了 batch completion 使用 suspense / fallback / default tax treatment，除非该处理本身已由上游 authority 明确允许。
- `Transaction Log` 是 audit-facing final log，不参与 runtime JE decision。
- 模糊、冲突或缺失 basis 不能被包装成 confidence。

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
- 哪些 upstream outcome 可被视为 `finalizable accounting outcome`
- Review Node 是否覆盖所有 JE 前交易，还是只覆盖 review-required / sampled / governance-candidate items
- high-confidence structural / rule / case-supported result 是否可以不经逐笔 review 直接触发 JE
- accountant approval、correction、still-pending 与 JE Generation 的 exact handoff contract
- JE-blocked reason 与 Coordinator / Review / upstream rework / Governance Review 的 exact routing
- split、refund、reversal、multi-line、tax-included / tax-excluded、zero-tax、partial-tax、foreign currency 等复杂分录类别的 exact behavior
- account-mapping、tax configuration 和 COA governance 的 precise ownership split
