# Case Judgment Node — Stage 2：功能逻辑与决策边界

## 1. Stage 范围

本 Stage 2 定义 `Case Judgment Node` 的功能逻辑与决策边界。

它回答：

- 什么触发该节点
- 它消费哪些输入类别
- 它可以产生哪些输出类别
- 哪些责任属于 deterministic code
- 哪些责任属于 LLM semantic judgment
- accountant / governance authority 边界
- memory/log read、candidate-only、no-mutation 边界
- 证据不足、模糊、冲突时的行为边界

本阶段不定义 schema、字段契约、存储路径、执行算法、测试矩阵、implementation routing、threshold number 或冻结枚举值。

## 2. Trigger Boundary

`Case Judgment Node` 在以下 conceptual boundary 下触发：

- 当前交易不是已经由结构性确定路径完成的交易；并且
- deterministic path 未能完成当前交易。

关键不是“只有 no rule”，而是 deterministic path 没有完成当前非结构性交易。

因此，该节点接收所有 `非结构性交易 + deterministic path 未完成` 的情况，包括：

- 没有适用 deterministic rule
- rule path 因 automation authority、role、alias、entity、governance 或 review 要求而不能完成
- rule match 结果本身说明当前交易不能通过 deterministic path 自动处理

但 Case Judgment 读取 blocked reason，不等于可以解除 blocked reason。

如果 authority 允许 case-based automation，Case Judgment 可以判断是否进入 operational classification path。
如果 authority / policy 本身要求 rule、review 或 governance，它不能绕过政策，只能输出 pending reason、review reason 或 candidate signal。

## 3. Input Categories

Stage 2 按判断作用组织 input categories，并在概念层说明来源类别。这里不是字段清单。

### 3.1 Identity basis

说明交易当前被认为指向谁。

来源类别包括 Entity Resolution context、Entity Log、alias / role context。

关键判断不是读取了哪个字段，而是：

- entity 是否足够支持当前 runtime judgment
- alias / role 是否足以支持自动化
- 当前 identity basis 是否允许 case-based judgment

`new_entity_candidate` 不天然阻断当前交易分类。只要 authority 允许，且 current evidence 足够强，Case Judgment 可以让本笔交易进入 operational classification path。

但 `new_entity_candidate` 不能支持 rule match，不能未经治理变成稳定 entity，也不能自动创建或升级 rule。

`ambiguous_entity_candidates` 或 `unresolved` 更保守：如果无法安全归属对象，通常不能支持 operational classification，应进入 pending 或 review-required，取决于是可补信息问题，还是 identity / governance risk。

### 3.2 Structural / profile basis

说明这笔交易是否受客户结构事实影响，例如 internal transfer、loan、tax config、employee context 等。

来源类别包括 Profile、Profile / Structural Match context。

Case Judgment 不重做结构性确定分类。它只消费上游结构性处理结果、未完成原因或 blocked reason。

### 3.3 Case precedent basis

说明过去类似案例怎样处理，以及哪些条件下存在例外。

来源类别包括 Case Log、customer knowledge summary。

Case memory 是条件化先例，不是简单多数投票。Case Judgment 需要判断当前交易是否真的落在历史先例适用条件内。

### 3.4 Current evidence basis

说明本次交易有哪些证据支持或推翻历史先例。

来源类别包括 Evidence Log references、current transaction evidence、receipt、cheque、accountant-provided context 等。

当前强证据可以支持 runtime operational judgment，但不能自动变成长期 authority。

### 3.5 Risk and blocking basis

说明当前是否存在 mixed-use、unconfirmed role、new entity candidate、ambiguous / unresolved identity、policy block、rule block、recent intervention、governance restriction 等风险或阻断原因。

来源类别包括 Entity Resolution output、Rule Match result、automation policy、Intervention / Governance context。

Blocked reason 是约束，不是 Case Judgment 可以自行解除的障碍。
Candidate identity 是风险语境，不等于一律 hard block；是否允许 operational path 取决于 authority 和 current evidence strength。

### 3.6 Authority basis

说明当前最多允许哪种层级的 runtime action：

- operational classification path
- pending / review path
- candidate signal
- governance candidate

来源类别包括 automation policy、rule lifecycle、accountant / governance boundaries。

Authority basis 是 Case Judgment 输出的上限。

## 4. Output Categories

Stage 2 只定义 conceptual output categories，不冻结 routing enum。

### 4.1 Operational classification path

含义：当前 authority 允许 case-based automation，且 case precedent + current evidence 足够支持本笔交易进入 operational classification。

对 `new_entity_candidate`，只有在 authority 允许且 current evidence 足够强时，才可进入此路径。

边界：

- 这是当前交易的 runtime path。
- 它不等于长期 case 写入。
- 它不等于 entity / alias / role approval。
- 它不等于 rule promotion。
- 它不等于 governance approval。

### 4.2 Pending path

含义：当前交易可能可判断，但缺少关键 accountant information、evidence clarification 或 context confirmation。

下游由 Coordinator / Pending Node 生成聚焦问题。

边界：

- Pending 是为了补信息。
- Pending 本身不是治理批准流程。
- Case Judgment 不应在可补证据缺失时自行猜测。

### 4.3 Review-required path

含义：当前问题不是单纯缺信息，而是 automation policy、required role confirmation、ambiguous / unresolved identity、rule-required condition、review-required condition、disabled automation、governance block 等 authority 原因要求人工确认或治理处理。

边界：

- Case Judgment 不能把 review-required path 降级成 operational classification path。
- Review-required 可能进入 Review Node、Governance Review Node 或 pending-review flow，但具体 routing 留到后续阶段。

### 4.4 Candidate signals

含义：Case Judgment 可以指出后续可能需要处理的候选信号，例如：

- case memory update candidate
- entity / alias / role candidate
- rule candidate
- automation policy / governance candidate

边界：

- Candidate signals 只供后续节点评估。
- 它们本身不写长期 memory。
- 它们不批准 governance。
- 它们不改变 active rule 或 automation policy。

## 5. Deterministic Code vs LLM Semantic Judgment

Stage 2 的核心边界是：

**code owns authority and eligibility; LLM owns semantic fit and evidence sufficiency inside the allowed boundary.**

### 5.1 Deterministic code responsibility

Deterministic code 负责：

- 判断 Case Judgment 是否被触发：非结构性交易，且 deterministic path 未完成。
- 汇总并标记上游 context：profile / structural result、entity resolution result、rule match result、blocking reason、automation policy、known governance constraints。
- 判断 authority / eligibility 上限：当前是否允许 operational classification，还是只能 pending、review-required 或 candidate signal。
- 执行 hard blocks：ambiguous / unresolved identity、rejected alias、required but unconfirmed role、review-required policy、disabled automation、rule-required condition without approved rule、governance block 等不能被 LLM 语义理由绕过。
- 对 `new_entity_candidate` 执行受限判断：它不能支持 rule match 或 durable memory authority；只有在 authority 允许且 current evidence 足够强时，才可能进入 operational classification path，否则进入 pending 或 review-required。
- 限制 memory / governance actions：哪些只能作为 candidate，哪些绝不能直接写入或批准。

### 5.2 LLM semantic judgment responsibility

LLM 可以负责：

- 比较 case precedent 与 current evidence 的语义匹配度。
- 判断当前证据是否足以支持本笔交易的 operational judgment。
- 解释历史先例的适用条件、例外条件，以及当前交易是否落在例外里。
- 生成 rationale、pending reason、review explanation、candidate signal explanation。

### 5.3 Hard boundary

LLM 可以在 code 允许的边界内判断“证据是否足够”。

LLM 不能：

- 扩大 automation authority
- 把 blocked reason 当作软建议
- 绕过 hard block
- 把 `new_entity_candidate` 变成 stable entity
- 批准长期记忆变化
- 批准治理变化

## 6. Accountant Authority Boundary

Accountant 仍然拥有最终 accounting decision 和 durable authority。

Case Judgment 不能：

- 替 accountant 作最终 review approval
- 把 runtime operational judgment 变成 accountant-confirmed outcome
- 确认 role、alias、entity、rule 或 automation policy
- 把一次 runtime result 当作长期客户知识

当交易需要 accountant information、业务用途确认、身份/角色确认、policy 例外确认或 review approval 时，Case Judgment 只能进入 pending / review-required path，并提供解释。

## 7. Governance Authority Boundary

Governance-level changes 不属于 Case Judgment authority。

Case Judgment 不能：

- approve / reject alias
- confirm role
- merge / split entity
- promote / modify / delete / downgrade active rule
- upgrade or relax automation policy
- approve governance event
- invalidate durable memory

它可以提出 governance candidate signal，但后续是否处理、如何处理、是否批准，属于 Review / Governance Review / memory update workflow。

## 8. Memory / Log Boundary

Stage 2 采用三层边界：read、candidate-only、no direct mutation。

### 8.1 Read boundary

Case Judgment 可以读取或消费以下 conceptual context：

- Current Evidence / Evidence Log references：当前交易证据、receipt、cheque、accountant context 等。
- Profile / Structural context：结构性事实和结构性匹配结果。
- Entity context / Entity Log：已识别实体、candidate entity、alias / role 状态、automation policy、identity risk。
- Case Log / customer knowledge summary：历史案例、例外条件、客户专属知识摘要。
- Rule / blocking context / Rule Log：rule miss、rule blocked、deterministic path 未完成原因。
- Intervention / Governance context：近期人工干预、治理风险、已有治理限制。

### 8.2 Candidate-only boundary

Case Judgment 可以提出候选信号，但不能执行变化：

- case memory update candidate：本次处理之后可能值得沉淀为 case。
- entity / alias / role candidate：可能需要后续确认或治理。
- rule candidate：可能存在 rule promotion 或 rule review 价值。
- automation policy / governance candidate：可能需要降级、review 或治理动作。

Candidate-only 只表示“后续节点应该评估这个信号”，不是 memory operation contract。

### 8.3 No direct mutation boundary

Case Judgment 绝不能：

- 直接写 Entity Log、Case Log、Rule Log 或 Governance Log
- 直接 append / update / promote / invalidate 长期 memory
- 修改 active rule
- 批准 alias、role、entity、rule 或 automation policy
- 执行 entity merge / split
- 把 runtime judgment 当作长期 authority

## 9. Insufficient / Ambiguous / Conflicting Evidence Behavior

Stage 2 采用优先级边界：authority block first、evidence repairability second、conflict caution third。

### 9.1 Authority block first

如果存在 policy、governance 或 identity hard block，Case Judgment 不能把它转成 operational classification。

例如：

- policy 要求 approved rule，但当前没有可用 approved rule
- policy 要求 review
- automation disabled
- required role 未确认且不能支持自动化
- alias 被拒绝或不能作为当前 identity basis
- ambiguous / unresolved entity 不能安全归属
- `new_entity_candidate` 缺少足够 current evidence 或 authority support
- governance block 存在

这些情况应进入 review-required path，或产生 governance / review candidate signal。

### 9.2 Evidence repairability second

如果 authority 允许 case-based judgment，但缺少关键证据或上下文，而 accountant 可以补充信息解决，则进入 pending path。

Pending 的目标是让 Coordinator 问出最小必要问题，而不是让 Case Judgment 猜。

例如：

- receipt 缺失
- 用途不明
- 当前证据不足以判断历史先例是否适用
- `new_entity_candidate` 需要 accountant context 才能支持本笔判断
- accountant context 缺失

### 9.3 Conflict caution third

如果 current evidence 与 case precedent、customer knowledge、risk signal 或 policy context 发生冲突，Case Judgment 应保守处理。

冲突不是 LLM 自由裁决的许可。

如果冲突需要业务判断，或可能改变长期理解，进入 review-required path。
如果冲突只是缺一个具体事实确认，进入 pending path，并保留 review caution。

### 9.4 Hard boundary

- Ambiguity 不等于可以猜。
- Conflicting evidence 不等于可以选择一个看起来更合理的版本。
- `new_entity_candidate` 不天然阻断当前交易分类，但也不提供 durable authority。
- Case Judgment 应输出最安全的 runtime path 和解释，而不是把不确定性隐藏在 confidence 语言里。

## 10. Stage 2 Open Boundaries

以下内容留到后续阶段，不在 Stage 2 冻结：

- exact input / output schema
- field names and object shape
- exact routing enum
- threshold numbers
- memory operation contract
- execution algorithm
- implementation files
- test matrix
- coding-agent task contract
- exact prompt structure or tool interface
