# Review Node — Stage 2：功能逻辑与决策边界

## 1. Stage 范围

本 Stage 2 定义 `Review Node` 的功能逻辑与决策边界。

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

`Review Node` 在当前交易、批次或治理候选存在 accountant-facing review need 时触发。

概念触发条件是：

- 上游 workflow 已形成可追溯 evidence、稳定交易身份、系统处理结果、pending clarification result、review-required context 或 candidate signal；并且
- 当前事项需要 accountant 审核、批准、修正、拒绝或继续保持 pending；并且
- 该事项尚未进入 JE finalization、final transaction logging 或 durable governance mutation execution。

典型触发来源包括：

- upstream deterministic 或 case-supported result 需要 accountant review。
- `Coordinator / Pending Node` 回收了 accountant clarification、correction 或 supplemental context，需要决定当前交易是否足以继续。
- 上游节点暴露 review-required、governance-needed、conflicting evidence 或 authority-risk context。
- `Case Judgment Node` 产生 runtime rationale 或 candidate signals，需要 accountant-facing review context。
- `Rule Match Node`、`Entity Resolution Node` 或 `Post-Batch Lint Node` 产生 rule / alias / role / entity / automation-policy 候选或风险说明。
- 系统需要在 JE generation 和 final audit logging 之前捕捉 accountant approval / correction。

如果当前事项只是可补信息缺口，且尚未形成 review package，应由 `Coordinator / Pending Node` 处理。
如果当前事项已经是高权限 durable governance mutation 的正式审批和执行，应进入 `Governance Review Node` 或相关 governance workflow。
如果当前交易已经完成 final logging，本节点不应作为 runtime decision source 重开交易结果。

## 3. Input Categories

Stage 2 按判断作用组织 input categories，不列字段清单。

### 3.1 Reviewable transaction result context

说明当前交易已经形成了什么系统处理结果、来自哪条 workflow path、为什么认为可审核。

来源类别包括 structural result、rule-handled result、case judgment result、pending 后续处理结果、review-required handoff 和相关 rationale。

这类输入是 review package 的主体，但不等于 accountant approval。

### 3.2 Evidence and audit-support context

说明 accountant 审核当前结果需要看到哪些 evidence foundation、evidence references、objective transaction basis、upstream rationale、risk reason 和 unresolved issue。

来源类别包括 Evidence Log references、当前交易证据、profile / entity / rule / case context、Coordinator intervention context 和 upstream review explanation。

`Transaction Log` 可以作为既有 audit-facing 历史参考被展示，但不能作为当前 runtime classification、rule match、case judgment 或 learning authority。

### 3.3 Accountant intervention and correction context

说明 accountant 已经通过 pending、review 或人工修正提供过哪些 clarification、correction、confirmation 或 objection。

来源类别包括 `Intervention Log` 语境、Coordinator handoff、current review interaction 和 accountant-provided context。

这些 context 可以支持当前 review decision，但不能自动升级成 durable profile truth、stable entity authority、approved alias、confirmed role、active rule 或 governance approval。

### 3.4 Candidate and governance context

说明当前 review package 中有哪些 memory / governance 候选或风险：

- case memory update candidate
- entity / alias / role candidate
- rule candidate、rule conflict 或 rule-health concern
- automation-policy candidate
- merge / split candidate
- auto-applied downgrade needing accountant visibility

这些输入可以被组织给 accountant 审核，但 candidate 不等于 active authority。

### 3.5 Authority and policy context

说明当前 review item 最多允许产生什么后续结果：

- approve current transaction outcome
- apply accountant correction to current transaction flow
- keep pending or return for clarification
- create candidate handoff
- enter governance review
- block finalization

来源类别包括 automation policy、rule lifecycle、entity / alias / role authority、governance restrictions、upstream hard blocks 和 accountant authority boundaries。

Authority context 是 Review Node 输出的上限。

### 3.6 Batch-level review context

说明一组交易或候选是否需要聚合给 accountant 审核，例如重复风险、同类 correction、case-to-rule candidate、entity split / merge concern 或 automation-risk trend。

这类输入可以提高 review 效率，但不能把批次趋势直接变成 rule、entity 或 automation-policy authority。

## 4. Output Categories

Stage 2 只定义 conceptual output categories，不冻结 routing enum 或对象形状。

### 4.1 Accountant-approved current outcome handoff

含义：accountant 已批准当前交易的处理结果，后续可以进入 JE generation、final completion 和 audit logging flow。

边界：

- 这是当前交易的 accountant-facing approval。
- 它不等于 rule promotion。
- 它不等于 case memory write。
- 它不等于 entity / alias / role / automation-policy approval。
- 它不写 `Transaction Log`；final audit logging 属于 `Transaction Logging Node`。

### 4.2 Accountant-corrected current outcome handoff

含义：accountant 修正了当前交易处理结果或相关业务语境，后续 workflow 应基于修正语境继续处理、生成 JE 或形成候选信号。

边界：

- Correction 可以改变当前交易 outcome。
- Correction 不自动改变长期 memory。
- Correction 不自动创建 active rule。
- Correction 不自动批准 alias、role、entity 或 automation policy。
- 如果 correction 暗示长期记忆错误，应形成 candidate / governance handoff。

### 4.3 Rejected / not-approved / still-pending handoff

含义：accountant 未批准当前系统结果，或当前 review package 仍缺关键 evidence、clarification、authority 或 conflict resolution。

边界：

- 未批准不能被系统解释成“选择最接近的系统建议”。
- still-pending 应返回补信息或上游修正语境。
- conflict unresolved 时不能进入 JE generation 或 final logging。

### 4.4 Review intervention record

含义：accountant 在 review 中的 approval、correction、rejection、confirmation、objection 或说明被保留为 intervention / review 语境。

边界：

- 该记录保存 accountant interaction 和 review rationale。
- 它不等于 final `Transaction Log`。
- 它不等于 `Case Log`、`Rule Log`、stable `Entity Log` 或 `Governance Log` mutation。
- 它不把 transient review draft、queue 或 handoff 称为 `Log`。

### 4.5 Memory / governance candidate handoff

含义：Review Node 可以把 accountant review 中暴露的长期记忆或治理事项整理为后续 workflow 候选。

典型候选包括：

- case memory update candidate
- entity / alias / role candidate
- rule candidate 或 rule conflict candidate
- automation-policy candidate
- merge / split candidate
- governance review candidate

边界：

- Candidate handoff 只表示“后续应评估”。
- 它不写长期 memory。
- 它不批准 governance event。
- 它不改变 active rule 或 automation policy。

### 4.6 Batch review summary handoff

含义：对于一组交易或候选，Review Node 可以输出 accountant-facing review summary、已处理事项、未处理事项、仍需澄清事项和治理候选分组。

边界：

- Summary 是审核辅助，不是 deterministic rule source。
- Summary 不替代 `Knowledge Log / Summary Log` 的客户知识编译职责。
- Summary 不能直接作为 future runtime authority。

## 5. Deterministic Code vs LLM Semantic Judgment

Stage 2 的核心边界是：

**code owns review eligibility, authority limits, traceability, and no-mutation discipline; LLM may help summarize review context and accountant language inside those limits.**

### 5.1 Deterministic code responsibility

Deterministic code 负责：

- 判断本节点是否被触发：存在 accountant-facing review need，且尚未进入 JE finalization、final logging 或 governance mutation execution。
- 汇总上游 result、rationale、evidence references、intervention context、candidate signals 和 authority limits。
- 区分 current transaction approval、current transaction correction、still-pending、review-required、governance-needed 和 candidate-only context。
- 保持 review package 与具体交易、批次、evidence 或候选事项绑定。
- 防止未经 accountant 明确决定的系统建议进入 approved outcome。
- 防止 review correction 直接写入 `Profile`、Entity / Case / Rule / Governance memory。
- 防止本节点写入 `Transaction Log` 或生成 journal entry。
- 标记哪些 accountant decision 只影响当前交易，哪些只能形成 memory / governance candidate。
- 执行 hard blocks：unresolved identity、ambiguous evidence、review-required policy、governance block、rule-required condition、disabled automation 或 conflicting evidence 不能被 review summary 语言绕过。

### 5.2 LLM semantic judgment responsibility

LLM 可以在 code 允许的边界内辅助：

- 将上游 rationale、pending history 和 evidence context 总结成 accountant 可读的 review explanation。
- 对多个候选或风险按业务含义聚合展示。
- 解释 accountant 自然语言 correction 的可能含义，并标记仍需确认的歧义。
- 总结 system result 与 accountant correction 的差异。
- 生成 governance candidate explanation、still-pending explanation 或 unresolved-review explanation。

### 5.3 Hard boundary

LLM 不能：

- 替 accountant approve current outcome
- 把模糊回答当作明确批准
- 选择 COA / HST 处理来替代 accountant correction
- 扩大 automation authority
- 把 candidate 变成 durable memory
- approve / reject alias
- confirm role
- create stable entity
- merge / split entity
- create / promote / modify / delete / downgrade active rule
- upgrade or relax automation policy
- 批准 governance event
- 生成 journal entry
- 写入 `Transaction Log`

## 6. Accountant Authority Boundary

Accountant 仍然拥有最终 accounting decision 和 durable authority。

`Review Node` 可以捕捉 accountant 对当前交易结果的批准、修正、拒绝或继续待处理决定。

本节点不能把 accountant silence、模糊自然语言、批量趋势或系统建议自动解释为 accountant approval。

对当前交易，accountant 的明确 approval / correction 可以成为后续 JE generation 和 final logging 的依据。
对长期记忆和治理事项，accountant review context 只能在相应 governance / memory workflow 边界内生效。

本节点不能：

- 替 accountant 作最终决定
- 把未确认 review package 变成 approved outcome
- 把当前交易 correction 直接变成长期客户政策
- 把 repeated correction 自动升级成 active rule
- 把 candidate alias / role / entity 直接批准
- 把 automation policy upgrade or relaxation 直接生效

## 7. Governance Authority Boundary

Governance-level changes 不属于 `Review Node` 的直接 mutation authority。

本节点可以把治理候选、风险说明、auto-applied downgrade visibility 和 accountant-facing response 组织成 handoff。

但本节点不能直接：

- approve / reject alias as durable authority
- confirm role as durable authority
- create stable entity authority
- merge / split entity
- archive / reactivate entity
- change automation policy
- create / promote / modify / delete / downgrade active rule
- approve governance event
- invalidate durable memory

高权限长期记忆变化应由 `Governance Review Node` 或相关 governance workflow 处理。
Review Node 与 Governance Review Node 对 accountant approval capture、governance event approval 和 durable mutation execution 的 exact split 留到后续阶段冻结。

## 8. Memory / Log Boundary

Stage 2 采用四层边界：read / consume、write allowed、candidate-only、no direct mutation。

### 8.1 Read / consume boundary

`Review Node` 可以读取或消费以下 conceptual context：

- current evidence foundation、objective transaction basis 和 stable transaction identity
- upstream results and rationale from Profile / Structural Match、Entity Resolution、Rule Match、Case Judgment 和 Coordinator / Pending Node
- `Intervention Log` 中与当前交易、批次或客户相关的 questions、answers、corrections、confirmations 和 prior review context
- `Profile`、Entity / Case / Rule / Governance context 中与当前 review item 相关的 authority limits、risk flags、automation policy、rule lifecycle 或 candidate state
- `Knowledge Log / Summary Log` 中可读的客户知识摘要，但只能作为 review context，不能替代 deterministic rule source 或 durable authority
- `Transaction Log` 中既有 finalized audit history，但不能作为当前 runtime decision、rule source、case memory 或 learning layer

### 8.2 Write allowed boundary

`Review Node` 可以在 review / intervention 语境内执行有限 durable write 或形成等价 handoff：

- 记录 accountant review action。
- 记录 accountant approval、correction、rejection、confirmation、objection 或 still-pending explanation。
- 记录 review package 为什么被批准、修正、拒绝或退回。

这些记录只属于 intervention / review interaction 语义。
它们不包含 final Transaction Log write，不创建 entity / case / rule / governance authority，也不执行 JE generation。

### 8.3 Candidate-only boundary

本节点只能作为候选或 handoff signal 表达：

- supplemental evidence / reprocessing candidate
- profile change or profile confirmation candidate
- entity / alias / role confirmation candidate
- case memory update candidate
- rule candidate、rule conflict candidate 或 rule-health candidate
- automation-policy / governance candidate
- merge / split candidate
- still-pending or unresolved-review signal

Candidate-only 表示后续 Coordinator、Evidence Intake、Case Memory Update、Governance Review、Post-Batch Lint 或相关 memory workflow 应评估该信号。
它不是 durable approval，也不是 memory operation contract。

### 8.4 No direct mutation boundary

本节点绝不能：

- 写入 `Transaction Log`
- 生成 journal entry
- 修改 `Profile`
- 写入或修改 stable `Entity Log` authority
- 写入或修改 `Case Log`
- 写入或修改 `Rule Log`
- 直接写入或批准 `Governance Log` mutation
- 创建 stable entity
- approve / reject alias as durable authority
- confirm role as durable authority
- merge / split entity
- 修改 automation policy
- 创建、升级、修改、删除或降级 active rule
- 把 review summary、candidate 或 accountant 模糊回答变成 durable authority

## 9. Insufficient / Ambiguous / Conflicting Evidence Behavior

Stage 2 采用优先级边界：do not approve incomplete review、preserve conflict、separate current outcome from durable authority。

### 9.1 Do not approve incomplete review

如果 review package 缺少关键 evidence、upstream rationale、transaction identity、accountant decision 或 authority basis，本节点不能输出 approved current outcome。

典型情况：

- evidence reference 不足以支持 accountant 审核。
- system result 没有说明来源 path 或 rationale。
- pending answer 未绑定到具体交易或问题。
- accountant response 不完整、指代不明或没有表达明确 approval / correction。
- governance candidate 缺少业务含义或证据说明。

这些情况应保持 still-pending、退回 clarification / upstream rework，或进入 review-required context。

### 9.2 Preserve conflict

如果 accountant correction 与 raw evidence、Profile、Entity Log、Case Log、Rule Log、Governance context、prior intervention 或 system rationale 冲突，本节点应保留冲突并阻止静默 finalization。

典型边界：

- 冲突只缺一个具体事实：返回 pending / clarification。
- 冲突影响当前交易处理：保持 not-approved / review-required，不能进入 JE generation。
- 冲突暗示长期 memory 错误：形成 governance / memory candidate。
- 冲突影响 evidence authenticity、transaction identity 或 entity safety：不能继续 finalization。

LLM 不能选择一个“看起来更合理”的版本覆盖冲突。

### 9.3 Separate current outcome from durable authority

Accountant 可以批准或修正当前交易 outcome，但这不自动改变长期 memory 或 automation behavior。

典型边界：

- 当前交易 approval 不等于 case memory write。
- 当前交易 correction 不等于 active rule change。
- repeated correction 不等于 rule promotion。
- alias / role / entity clarification 不等于 durable authority。
- automation policy upgrade or relaxation 必须进入 governance approval。

如果 current outcome 与 durable memory 都可能受影响，应拆成当前交易 handoff 和 memory / governance candidate handoff。

### 9.4 Governance caution

如果治理候选证据不足、业务含义不清、影响范围不明、或 accountant response 模糊，本节点不能把候选转成 approved governance event。

它应输出 candidate handoff、still-pending governance review context 或 rejection context，具体治理处理留给 `Governance Review Node`。

### 9.5 Hard boundary

- Review 是 accountant authority interface，不是 LLM final decision interface。
- Accountant approval 必须明确、可追溯、可绑定到具体交易或候选事项。
- Transaction Log 是 audit-facing final log，不参与 runtime review decision。
- Intervention / review record 不等于 Transaction Log、Case Log、Rule Log、Entity Log 或 Governance Log mutation。
- Governance-needed 不能被降级成普通 current-transaction approval。
- 模糊、冲突或缺失 review 不能被包装成 confidence。

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
- Review Node 是否覆盖所有交易、只覆盖 review-required items、还是以 batch review / sampling / policy 组合触发
- accountant approval、correction、rejection、still-pending 与 JE Generation 的 exact handoff contract
- Review Node 与 `Governance Review Node` 在 accountant governance approval capture、governance event approval 和 durable mutation execution 上的 exact split
- review / intervention record 与 `Intervention Log` 的 exact contract
- review trace 如何被 `Transaction Logging Node` 纳入 final audit trail
- 多交易、多候选的聚合、去重、排序、展示和部分批准边界
