# Case Memory Update Node — Stage 2：功能逻辑与决策边界

## 1. Stage 范围

本 Stage 2 定义 `Case Memory Update Node` 的功能逻辑与决策边界。

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

`Case Memory Update Node` 在当前交易已经完成，并且具备可学习 authority 时触发。

概念触发条件是：

- 当前交易已有稳定 transaction identity 和可追溯 evidence foundation；并且
- 当前交易 outcome 已完成必要 review、correction、JE、final logging 或等价 finalization boundary；并且
- 当前交易不是 pending、still-pending、not-approved、JE-blocked、not-finalizable、unresolved、conflicting 或 governance-blocked；并且
- 当前完成交易尚未被安全沉淀为 case memory 或候选 handoff。

典型触发来源包括：

- structural path、rule path 或 case-supported path 已形成可学习的完成交易。
- pending / review 回收 accountant context 后，当前交易已完成并可沉淀。
- accountant correction 已明确绑定到当前交易，且后续 JE / logging boundary 已满足。
- final audit logging 后暴露出需要 Case Log 或治理候选处理的完成交易语境。

以下情况不能触发正常 case memory write：

- 当前交易仍缺 final outcome authority。
- 当前交易仍需 accountant clarification 或 review approval。
- 当前交易存在 unresolved identity、ambiguous evidence、conflicting evidence、JE-blocked、governance block 或 review-required condition。
- 当前内容只是 runtime judgment、candidate signal、review draft、report draft、lint finding 或 unapproved governance proposal。

Stage 2 不冻结 exact routing：Case Memory Update 必须严格后置于 `Transaction Logging Node`，还是可以消费等价 completed-transaction handoff，留到后续阶段定义。

## 3. Input Categories

Stage 2 按判断作用组织 input categories，不列字段清单。

### 3.1 Completed transaction basis

说明当前要沉淀的是哪一笔已完成交易，以及它的客观交易基础、稳定身份和完成状态。

来源类别包括 Evidence Intake / Preprocessing、Transaction Identity、final outcome context、JE completion context 和 final logging / finalization context。

本节点只使用这类输入判断是否可以进入 case-learning flow。
它不能用这些输入重新做分类、税务判断、JE 计算或 final logging。

### 3.2 Final outcome and authority basis

说明当前交易最终怎样处理，以及该结果为什么具备可学习 authority。

来源类别包括 structural result、rule-handled result、case-supported result、pending clarification result、accountant-approved result、accountant-corrected result、review trace 和 authority trace。

核心边界：

- 只有已完成、可追溯、具备 authority 的 outcome 可以沉淀为 case。
- 未批准、仍 pending、仍冲突或仅为系统建议的内容不能写成完成案例。
- 当前交易 outcome 可以成为 case precedent，但不自动成为 rule 或 governance authority。

### 3.3 Evidence and exception basis

说明这笔完成交易为什么具有未来案例价值。

来源类别包括 Evidence Log references、receipt / cheque / accountant context、upstream rationale、case judgment rationale、review / correction rationale、exception context、risk context 和 intervention context。

本节点关注的是未来 case judgment 需要理解的条件和例外，而不是重新审计整条 workflow。

### 3.4 Entity and identity basis

说明完成交易当时指向哪个稳定实体、候选实体、alias、role 或 identity risk。

来源类别包括 Entity Resolution context、Entity Log context、alias / role context、new entity candidate context、ambiguous / unresolved history that has since been resolved、review correction context。

边界：

- 稳定 entity / approved alias / confirmed role 可以作为 case context 被引用。
- `new_entity_candidate` 可以随完成交易形成待治理 case 语境或候选信号。
- `new_entity_candidate` 不能因此变成 stable entity。
- candidate alias / candidate role 不能因此变成 approved alias 或 confirmed role。

### 3.5 Candidate and governance basis

说明这笔完成交易是否暴露出后续治理或规则候选。

来源类别包括上游 candidate signals、review correction、repeated pattern hints、case judgment rationale、entity / alias / role uncertainty、rule conflict、automation-policy concern 和 post-batch-lint-relevant context。

这类输入只支持候选 handoff。
它不支持本节点直接修改 Entity Log、Rule Log、Governance Log、Profile 或 automation policy。

### 3.6 Prior memory and duplication basis

说明这笔完成交易是否已经存在 case memory，或与既有 case / entity / rule / governance history 发生重复、冲突或 supersession risk。

来源类别包括 Case Log、Entity Log、Rule Log、Governance context、prior candidate handoffs 和 final audit history。

这类输入只用于防止重复、保护历史一致性和识别候选风险。
它不允许本节点重写历史审计日志或自行执行治理变更。

## 4. Output Categories

Stage 2 只定义 conceptual output categories，不冻结 routing enum 或对象形状。

### 4.1 Case memory write

含义：当前已完成交易被沉淀为 `Case Log` 中的真实历史案例。

边界：

- 这是 case-learning memory，不是 audit-facing `Transaction Log`。
- 它保存完成交易的 outcome、证据语境、例外语境和 correction / review context。
- 它支持未来 `Case Judgment Node` 的 case-based judgment。
- 它不参与 deterministic rule match。
- 它不等于 accountant 批准 rule。
- 它不等于 entity / alias / role / automation-policy governance approval。

### 4.2 Case memory skipped / blocked handoff

含义：当前交易不能安全沉淀为 case memory，因为完成状态、authority、证据、身份、review 或 consistency basis 不足。

边界：

- Blocked handoff 是安全停止，不是用低可信 case 填补学习层。
- 本节点不能用“先记成案例以后再修”绕过 authority 或 traceability。
- 后续应返回 Review、Coordinator、Transaction Logging、上游修正或 governance workflow。

### 4.3 Entity / alias / role candidate handoff

含义：完成交易暴露出可能需要新增实体、确认 alias、确认 role、合并 / 拆分实体或修正身份记忆的候选。

边界：

- 候选只表示后续应评估。
- 它不创建 stable entity。
- 它不 approve / reject alias。
- 它不 confirm role。
- 它不执行 merge / split。
- 它不改变 automation policy。

### 4.4 Rule / automation-policy candidate handoff

含义：完成交易暴露出可能需要 rule promotion、rule review、rule conflict handling、rule downgrade、automation-policy downgrade / upgrade review 或 no-promotion restriction 的候选。

边界：

- 本节点可以提出 rule 或 automation-policy 候选。
- 它不能 create / promote / modify / delete / downgrade active rule。
- 它不能 upgrade or relax automation policy。
- 系统自动降级 automation policy 的正式边界属于 lint / governance 相关 workflow，不在本节点内冻结。
- `case_allowed_but_no_promotion` 的实体不得被本节点推进为 rule promotion 候选。

### 4.5 Knowledge compilation handoff

含义：新 case 或候选信号可能使客户知识摘要需要更新。

边界：

- 该 handoff 只提示 `Knowledge Compilation Node` 后续编译。
- 它不是客户知识摘要本身。
- 摘要不能反过来成为 deterministic rule source。

### 4.6 Consistency issue signal

含义：本节点发现完成交易、case memory、entity context、rule context、review correction、audit history 或 governance history 之间存在不一致。

边界：

- 该 signal 不自行修正历史。
- 它不重写 `Transaction Log`。
- 它不修改 active memory。
- 它应进入 review、governance 或 lint 语境。

## 5. Deterministic Code vs LLM Semantic Judgment

Stage 2 的核心边界是：

**code owns learning eligibility, durable-write discipline, duplication control, and governance no-mutation enforcement; LLM may help summarize case meaning and identify candidate signals inside those limits.**

### 5.1 Deterministic code responsibility

Deterministic code 负责：

- 判断本节点是否被触发：当前交易是否已完成并具备可学习 authority。
- 检查 transaction identity、final outcome、JE / finalization context、review / correction trace 和 evidence foundation 是否足以支持 case memory write。
- 阻止 pending、not-approved、review-required、governance-needed、candidate-only、JE-blocked、not-finalizable 或 conflicting context 写入 Case Log。
- 区分 Case Log write、candidate handoff、consistency issue 和 blocked handoff。
- 防止同一完成交易重复写入 case memory，或在 reprocessing / correction 语境中产生互相矛盾的案例。
- 执行 Case Log 的 durable write discipline。
- 防止 `Transaction Log` 被当作 runtime decision source 或学习层。
- 防止本节点修改 Profile、stable Entity Log authority、Rule Log 或 Governance Log。
- 防止 candidate entity / alias / role / rule / automation-policy 被误写为 durable authority。
- 执行 `new_entity_candidate` 边界：可以形成候选和 case 语境，但不能支持 rule match、稳定实体创建或 rule promotion。

### 5.2 LLM semantic judgment responsibility

LLM 可以在 code 允许的边界内辅助：

- 总结完成交易中对未来案例有用的业务语境、证据语境和例外语境。
- 解释 accountant correction 或 review rationale 对 case precedent 的意义。
- 比较当前完成交易与既有 case memory 的语义关系，提示是否存在重复、例外或冲突风险。
- 识别可能的 entity / alias / role / rule / governance candidate signal，并生成解释。
- 将 case memory 的人类可读说明写得清楚、可追溯、不过度概括。

### 5.3 Hard boundary

LLM 不能：

- 决定当前交易是否具备可学习 authority
- 把 pending / not-approved / conflicting 交易写成完成案例
- 选择 COA 科目或 HST/GST treatment
- 生成或修正 journal entry
- 替 accountant approve current outcome
- 把 runtime rationale 当作 accountant correction
- 把 `new_entity_candidate` 变成 stable entity
- approve / reject alias
- confirm role
- merge / split entity
- create / promote / modify / delete / downgrade active rule
- upgrade or relax automation policy
- 批准 governance event
- 重写 `Transaction Log` 或既有 durable memory

## 6. Accountant Authority Boundary

Accountant 仍然拥有最终 accounting decision 和 durable authority。

`Case Memory Update Node` 可以沉淀 accountant-approved、otherwise-authorized 或 accountant-corrected completed transaction outcome。

本节点不能：

- 把系统高置信结果解释为 accountant approval。
- 把 accountant silence、模糊回答或未完成 review 解释为 approval。
- 把当前交易 correction 自动变成长期客户政策。
- 把 repeated completed outcomes 自动升级成 active rule。
- 把 alias / role / entity clarification 自动批准为 durable authority。
- 把 case memory write 解释为 accountant 已批准后续治理候选。

对当前交易，明确 approval / correction 可以成为 case memory 的 authority basis。
对长期记忆和治理事项，accountant context 只能形成候选或交给治理流程，除非后续 governance boundary 明确批准。

## 7. Governance Authority Boundary

Governance-level changes 不属于 `Case Memory Update Node` 的直接 mutation authority。

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
- rewrite historical cases to follow later governance state without approved process

本节点可以提出 governance candidate signal。
后续是否进入治理队列、如何审批、是否修改长期 memory 或 active rule，属于 `Governance Review Node`、`Post-Batch Lint Node` 或相关 governance workflow。

## 8. Memory / Log Boundary

Stage 2 采用四层边界：read / consume、write allowed、candidate-only、no direct mutation。

### 8.1 Read / consume boundary

`Case Memory Update Node` 可以读取或消费以下 conceptual context：

- current transaction identity、objective transaction basis 和 evidence references
- completed outcome from structural / rule / case / pending / review workflow
- JE completion / finalization context，只用于确认交易已完成和 case traceability
- final audit context from `Transaction Log` 或等价 finalization handoff
- upstream rationale from Profile / Structural Match、Entity Resolution、Rule Match、Case Judgment、Coordinator / Pending Node、Review Node 和 JE Generation Node
- `Intervention Log` 中与当前交易相关的 questions、answers、corrections、confirmations 和 review context
- Entity / Case / Rule / Governance context 中与当前 case 或候选相关的 authority、risk、history 和 restriction
- `Knowledge Log / Summary Log` 中的人类可读客户知识摘要，但只能作为 case wording 或 candidate context 的背景，不能作为 deterministic rule source

它不能读取 `Transaction Log` 来做未来 runtime classification、rule match、case judgment 或 direct learning authority。

### 8.2 Write allowed boundary

本节点可以执行的 durable write 只限于 `Case Log` 语义：

- 把已完成交易沉淀为真实历史案例。
- 保留支持该案例的 evidence、outcome、exception、review / correction 和 authority context。
- 标记该案例在未来只提供 case precedent，而不是 deterministic rule authority。

这些写入只属于 Case Log。
它们不写 Transaction Log、Rule Log、stable Entity Log、Governance Log 或 Profile。

### 8.3 Candidate-only boundary

本节点只能作为候选或 handoff signal 表达：

- entity creation / merge / split candidate
- alias approval / rejection candidate
- role confirmation candidate
- rule candidate、rule conflict candidate、rule-health candidate 或 case-to-rule candidate
- automation-policy downgrade / upgrade-review candidate
- profile / tax config / account-mapping review candidate
- knowledge compilation candidate
- post-batch lint candidate
- consistency issue signal

Candidate-only 表示后续 Governance Review、Post-Batch Lint、Knowledge Compilation、Review 或相关 memory workflow 应评估该信号。

它不是 durable approval，也不是 final memory operation contract。

### 8.4 No direct mutation boundary

本节点绝不能：

- 写入 `Transaction Log`
- 生成或修改 journal entry
- 修改 `Profile`
- 写入或修改 stable `Entity Log` authority
- 写入或修改 `Rule Log`
- 直接写入或批准 `Governance Log` mutation
- 创建 stable entity
- approve / reject alias as durable authority
- confirm role as durable authority
- merge / split entity
- 修改 automation policy
- 创建、升级、修改、删除或降级 active rule
- 把 candidate、summary、review draft 或 lint finding 称为 `Log`
- 把 Case Log 或 Transaction Log 变成 deterministic rule source

## 9. Insufficient / Ambiguous / Conflicting Evidence Behavior

Stage 2 采用优先级边界：completed authority first、case traceability second、governance caution third。

### 9.1 Completed authority first

如果当前交易尚未完成或不具备可学习 authority，本节点不能写正常 case memory。

典型情况：

- transaction outcome still pending
- review not approved
- accountant correction ambiguous
- JE generation not-finalizable
- final logging / finalization boundary 未满足
- unresolved / ambiguous identity 仍影响 current outcome
- 当前内容只是 candidate signal、runtime judgment 或 review draft
- governance block 存在

这些情况应输出 case memory blocked handoff 或 consistency issue，而不是生成低可信案例。

### 9.2 Case traceability second

如果 authority 允许继续，但交易身份、evidence references、review / correction trace、upstream rationale 或 final outcome 无法可靠绑定，本节点仍不能正常写 Case Log。

本节点不能用自然语言摘要、confidence 或历史相似性填补 traceability 缺口。

### 9.3 Governance caution third

如果完成交易暗示 entity、alias、role、rule、automation policy、Profile 或 tax config 需要长期变化，本节点应拆分：

- 当前完成交易可以作为 case memory 的部分。
- 长期变化只能作为 candidate 或 governance handoff。

如果候选证据不足、影响范围不清、authority 不足或 accountant response 模糊，本节点不能把它升级成 durable memory mutation。

### 9.4 Conflict behavior

如果完成交易 outcome 与 raw evidence、review correction、Entity Log、Case Log、Rule Log、Governance history、prior intervention 或 Transaction Log 发生冲突，本节点应保守处理。

典型边界：

- 冲突影响当前交易完成结果：阻止 case memory write，返回 review / upstream correction。
- 冲突只影响长期记忆：写入当前 case 的能力取决于 completed authority；长期变化只形成 candidate。
- 冲突影响 entity safety、rule authority 或 automation policy：形成 governance / lint candidate，不直接 mutation。
- 发现重复或 reprocessed transaction：不得产生互相矛盾的并列案例，具体 supersession 行为留到后续阶段。

### 9.5 Hard boundary

- Case memory 是学习层，不是审计日志。
- Transaction Log 是 audit-facing final log，不参与 runtime decision，也不是学习层。
- Case Log 可以支持未来 Case Judgment，但不能支持 deterministic rule match。
- Active rule 只能来自 accountant / governance approved Rule Log。
- `new_entity_candidate` 不天然阻断当前交易分类，但不创造 durable authority。
- Completed transaction outcome 可以成为 case precedent，但不能自动成为 rule、stable entity、approved alias、confirmed role 或 automation-policy change。
- 模糊、冲突、缺失或未批准状态不能被包装成可学习案例。

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
- completed-transaction learning authority 的 exact contract
- Case Memory Update 与 final `Transaction Log` 的 exact trigger order
- high-confidence structural / rule / case-supported outcome 是否可不经逐笔 accountant review 直接形成 case
- accountant approval、correction、rejection、still-pending 与 Case Log write 的 exact handoff contract
- `new_entity_candidate` 相关完成交易在 Case Log 中的 exact authority expression
- duplicate / reprocessed / corrected / reversed / split transaction 对 case memory 的 exact behavior
- case-to-rule candidate 由本节点、Post-Batch Lint Node、Governance Review Node 还是组合流程提出
