# Governance Review Node — Stage 2：功能逻辑与决策边界

## 1. Stage 范围

本 Stage 2 定义 `Governance Review Node` 的功能逻辑与决策边界。

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

`Governance Review Node` 在存在高权限长期记忆变化候选，且该候选需要治理审查或 accountant / governance decision 时触发。

概念触发条件是：

- 上游 workflow 已产生可追溯的治理候选、风险信号、accountant instruction、review correction、lint finding 或 memory consistency issue；并且
- 候选事项可能影响 entity authority、alias authority、role authority、rule lifecycle、automation policy 或其他长期自动化权威；并且
- 当前事项不是普通 runtime classification、pending clarification、JE generation、final transaction logging 或 case memory write；并且
- 该事项尚未被正式批准、拒绝、退回或记录为已处理治理结果。

典型触发来源包括：

- `Case Judgment Node`、`Review Node` 或 `Case Memory Update Node` 提出的 entity / alias / role / rule / automation-policy 候选。
- `Transaction Logging Node` 暴露的 candidate relation、logging consistency issue 或治理相关审计语境。
- `Post-Batch Lint Node` 发现的 entity merge / split 风险、rule instability、case-to-rule 候选或 automation risk。
- accountant 在 review、pending、intervention 或 onboarding 语境中提出的长期记忆修正意图。
- 系统自动降级 automation policy 后，需要 durable governance history 和 accountant visibility 的事项。

以下情况不能触发正式 governance approval：

- 当前交易 outcome 仍 pending、not-approved、JE-blocked、unresolved 或 conflicting。
- 候选缺少 evidence foundation、affected memory context 或 authority basis。
- accountant response 模糊，无法区分当前交易 correction 与长期治理指令。
- 事项只是 runtime rationale、review draft、report draft、candidate-only note 或未绑定证据的 lint warning。

Stage 2 不冻结 exact routing：候选如何进入治理队列、如何排序、如何合并、如何再审，留到后续阶段定义。

## 3. Input Categories

Stage 2 按判断作用组织 input categories，不列字段清单。

### 3.1 Governance candidate basis

说明当前候选是什么，以及它可能改变哪类长期 authority。

来源类别包括 entity / alias / role candidate、merge / split candidate、rule candidate、rule conflict / rule-health concern、automation-policy candidate、auto-applied downgrade visibility、profile / tax config / account-mapping review candidate。

候选只说明“可能需要治理”，不等于可以批准。

### 3.2 Evidence and traceability basis

说明候选依据来自哪些可追溯 evidence、交易、case、review、intervention、audit history 或 lint finding。

来源类别包括 Evidence Log references、completed transaction context、Case Log context、Transaction Log audit history、Intervention Log context、Review Node decision context、Case Memory Update candidate context 和 Post-Batch Lint context。

`Transaction Log` 在这里只能作为 audit-facing historical context，不参与 runtime decision，也不能作为学习层或 rule source。

### 3.3 Current memory state basis

说明当前长期记忆处于什么状态，以及候选变化会影响什么。

来源类别包括 Entity Log、Rule Log、Governance Log、Case Log、Knowledge Log / Summary Log 和必要的 Profile context。

核心边界：

- Entity Log 回答“是谁、别名、角色、状态、authority、automation policy”。
- Case Log 回答“过去真实完成案例怎样处理”。
- Rule Log 回答“哪些 deterministic rules 已被批准”。
- Governance Log 回答“高权限长期变化及审批状态”。
- Knowledge Summary 是可读摘要，不是 deterministic rule source。

### 3.4 Authority and approval basis

说明当前候选最多允许什么治理结果，以及谁拥有最终 authority。

来源类别包括 accountant decision、review context、existing governance restriction、automation policy、rule lifecycle、entity authority、alias / role authority 和 system downgrade boundary。

Authority basis 是本节点输出的上限。

没有明确 authority 的候选不能被批准为长期变化。

### 3.5 Impact and downstream basis

说明候选若被批准，会影响哪些后续 workflow 和历史解释。

影响类别包括 future entity resolution、future rule match、future case judgment、case-to-rule eligibility、knowledge compilation、post-batch lint monitoring、review display 和 audit explanation。

本节点必须区分：

- 可以影响未来 runtime authority 的长期变化。
- 只能作为历史解释保留的治理记录。
- 不能回写或改写历史 `Transaction Log` 的后续变化。

### 3.6 Conflict and risk basis

说明候选是否与 evidence、current memory、prior governance、accountant correction、case history、rule history、automation policy 或 audit history 冲突。

这类输入用于阻止不安全治理变化，或把候选退回 review、pending、lint、case memory update 或后续人工确认。

## 4. Output Categories

Stage 2 只定义 conceptual output categories，不冻结 routing enum 或对象形状。

### 4.1 Governance approval / rejection / deferral record

含义：治理候选被正式记录为批准、拒绝、退回、暂缓或已通过受控系统降级生效。

边界：

- 这是 governance history。
- 它必须保留 approval / rejection / deferral 的 authority 和 reason。
- 它不等于当前交易 accounting approval。
- 它不重写历史 `Transaction Log`。

### 4.2 Authorized durable memory change

含义：在 accountant / governance authority 明确允许后，长期记忆或自动化权威可以发生变化。

典型变化类别包括：

- alias approval / rejection
- role confirmation
- entity merge / split / lifecycle handling
- rule creation / promotion / modification / deletion / downgrade
- automation policy change

边界：

- 只有被授权的治理变化可以影响 future runtime authority。
- exact mutation contract 留到后续阶段冻结。
- 历史交易日志不随治理变化被重写。
- `new_entity_candidate` 只有经过治理批准后，才可能获得稳定实体或相关 authority。

### 4.3 Governance blocked / insufficient handoff

含义：候选不能被批准，因为 evidence、authority、impact、conflict resolution 或 accountant decision 不足。

边界：

- Blocked handoff 是安全停止，不是低可信治理记录补丁。
- 本节点不能用“先批准以后再修”绕过 durable authority。
- 后续应返回 Review、Coordinator、Case Memory Update、Post-Batch Lint、上游 correction 或人工治理。

### 4.4 Candidate refinement / grouping handoff

含义：多个候选需要合并、拆分、去重、补证据或按业务含义重组后再进入正式 approval。

边界：

- Refinement 不是 approval。
- grouping 不是 evidence。
- 去重或聚合不能把多个弱信号自动变成强 authority。

### 4.5 Knowledge / lint handoff

含义：治理结果或未解决风险需要交给 `Knowledge Compilation Node` 或 `Post-Batch Lint Node`，用于未来摘要、监控或再检查。

边界：

- Knowledge handoff 不是客户知识摘要本身。
- Lint handoff 不是治理审批。
- 摘要和 lint finding 不能成为 deterministic rule source。

## 5. Deterministic Code vs LLM Semantic Judgment

Stage 2 的核心边界是：

**code owns governance eligibility, authority enforcement, durable mutation limits, and auditability; LLM may help explain candidate meaning and evidence relationships inside those limits.**

### 5.1 Deterministic code responsibility

Deterministic code 负责：

- 判断本节点是否被触发：是否存在长期 authority 相关治理候选，且尚未被正式处理。
- 区分 current transaction correction、case memory candidate、audit logging context、lint finding 和 formal governance candidate。
- 汇总候选与 evidence、case、transaction、intervention、review、memory state 和 prior governance 的绑定关系。
- 判断候选是否具备进入治理审查的最低 authority / traceability basis。
- 执行 hard blocks：未完成当前交易、缺少证据、accountant decision 模糊、impact 不明、冲突未解决、governance restriction 存在时不得批准 durable change。
- 防止 candidate alias / role / entity / rule / automation-policy 被误写为 active authority。
- 防止 `new_entity_candidate` 在未治理前支持 rule match、stable entity authority 或 rule promotion。
- 防止 rule creation、promotion、modification、deletion 或 downgrade 绕过 accountant / governance approval。
- 防止 automation policy upgrade or relaxation 绕过 accountant approval。
- 保持 Governance Log 与 durable memory mutation、rejection、deferral 或 auto-applied downgrade visibility 的边界清晰。

### 5.2 LLM semantic judgment responsibility

LLM 可以在 code 允许的边界内辅助：

- 总结候选的业务含义、证据链和影响范围。
- 比较候选与既有 Entity Log、Case Log、Rule Log、Governance history 的语义冲突。
- 将多个候选按业务含义聚合，提示可能的重复、拆分、合并或冲突。
- 解释 accountant natural-language instruction 是否看起来像当前交易 correction、长期治理意图，或仍需确认的模糊表达。
- 生成 approval / rejection / deferral explanation 的人类可读草案。

### 5.3 Hard boundary

LLM 不能：

- 批准 governance event
- 替 accountant 作长期治理决定
- 把模糊 accountant response 解释成 durable approval
- 把候选变成 stable entity、approved alias、confirmed role 或 active rule
- merge / split entity
- create / promote / modify / delete / downgrade active rule
- upgrade or relax automation policy
- 把 repeated cases 自动升级成 rule
- 改写 historical Transaction Log
- 选择 COA 科目或 HST/GST treatment
- 生成或修正 journal entry
- 把 governance approval 当成当前交易 accounting approval

## 6. Accountant Authority Boundary

Accountant 仍然拥有最终 accounting decision 和 durable governance authority。

`Governance Review Node` 可以捕捉并执行边界内的 accountant / governance decision，但不能替 accountant 做决定。

本节点不能：

- 把 accountant silence 解释为 approval。
- 把模糊自然语言解释为长期治理批准。
- 把当前交易 correction 自动变成 stable policy。
- 把 repeated completed outcomes 自动升级成 active rule。
- 把 candidate alias、candidate role 或 `new_entity_candidate` 自动批准。
- 把系统 lint finding 自动升级成放宽 automation policy 的依据。

对当前交易，accountant approval / correction 属于 Review / transaction finalization 语境。
对长期记忆，只有明确治理 decision 才能改变 durable authority。

## 7. Governance Authority Boundary

Governance-level changes 是本节点的核心处理对象，但不是无条件 mutation 权限。

本节点可以在明确 authority 边界内处理：

- alias approval / rejection
- role confirmation
- entity merge / split / lifecycle handling
- rule creation / promotion / modification / deletion / downgrade
- automation policy downgrade / upgrade / relaxation review
- governance rejection、deferral、restriction 或 no-promotion decision

但本节点必须保持三条边界：

- 候选不等于 approval。
- approval 不等于执行算法或字段契约已经冻结。
- approved governance change 只影响 future authority；历史 `Transaction Log` 不被重写。

系统自动降低 automation policy 可以在受控边界内立即生效，但必须作为治理历史和 review visibility 处理。升级或放宽 automation policy 必须 accountant approval。

## 8. Memory / Log Boundary

Stage 2 采用四层边界：read / consume、write allowed、candidate-only、no unauthorized mutation。

### 8.1 Read / consume boundary

`Governance Review Node` 可以读取或消费以下 conceptual context：

- Evidence Log references and objective evidence context
- Entity Log authority、alias、role、status、risk 和 automation-policy context
- Case Log completed-case precedent、exception 和 accountant correction context
- Rule Log active / historical rule authority 和 rule-health context
- Transaction Log finalized audit history，只作历史审计语境和 candidate grounding
- Intervention Log accountant question / answer / correction / confirmation context
- Governance Log prior approvals、rejections、deferrals、restrictions 和 auto-applied downgrade history
- Knowledge Log / Summary Log 的客户知识摘要，只作可读背景
- Profile context 中与 governance candidate 有关的结构事实或限制

### 8.2 Write allowed boundary

本节点可以写入或推动写入的 durable 内容只限于治理语义：

- 记录治理候选的正式处理结果。
- 记录 accountant / governance approval、rejection、deferral、restriction 或 auto-applied downgrade visibility。
- 在明确授权边界内推动对应长期记忆或自动化权威变化。

这些写入或 mutation 不等于：

- 当前交易 final accounting outcome
- `Transaction Log` write
- `Case Log` completed-case write
- JE generation
- report output

Exact durable mutation contract 留到后续阶段冻结。

### 8.3 Candidate-only boundary

本节点仍只能作为候选或 handoff 表达：

- evidence re-check candidate
- current-transaction review correction candidate
- case memory correction / supersession candidate
- profile / tax config / account-mapping review candidate
- knowledge compilation candidate
- post-batch lint follow-up candidate
- unresolved governance risk candidate

Candidate-only 表示后续 workflow 应评估，不是 durable approval。

### 8.4 No unauthorized mutation boundary

本节点绝不能：

- 在 accountant / governance authority 不足时修改 Entity Log、Rule Log、Governance Log、Profile 或 automation policy。
- 把 candidate alias 写成 approved alias。
- 把 candidate role 写成 confirmed role。
- 把 `new_entity_candidate` 写成 stable entity。
- 在未批准时 merge / split entity。
- 在未批准时 create / promote / modify / delete / downgrade active rule。
- 在未批准时 upgrade or relax automation policy。
- 把 governance note、review draft、lint finding、queue 或 candidate registry 称为 `Log`。
- 把 Transaction Log、Case Log 或 Knowledge Summary 变成 deterministic rule source。
- 重写 historical Transaction Log 来追随后续治理变化。

## 9. Insufficient / Ambiguous / Conflicting Evidence Behavior

Stage 2 采用优先级边界：authority first、traceability second、impact clarity third、conflict preservation fourth。

### 9.1 Authority first

如果候选缺少明确 accountant / governance authority，本节点不能批准 durable change。

典型情况：

- accountant response 模糊或沉默。
- review correction 只影响当前交易，没有表达长期治理意图。
- candidate 来自 runtime judgment 或 lint finding，但未经过必要 review。
- automation policy upgrade / relaxation 缺少 accountant approval。
- rule promotion / active rule change 缺少 accountant approval。

这些情况应保持 candidate、退回 clarification，或记录为 deferred / rejected governance result。

### 9.2 Traceability second

如果候选无法绑定到 evidence、case、transaction、intervention、review decision、current memory state 或 prior governance context，本节点不能批准 durable change。

本节点不能用自然语言摘要、相似性、频率或 confidence 填补 traceability 缺口。

### 9.3 Impact clarity third

如果候选会影响 future entity resolution、rule match、case judgment、automation policy 或历史解释，但影响范围不清，本节点不能直接批准。

典型情况：

- merge / split 会影响多个实体、alias、rules 或 cases，但影响边界不清。
- rule promotion 的适用条件不清。
- role confirmation 会改变未来 rule eligibility，但 accountant intent 不清。
- automation policy change 会放宽自动化，但风险边界不清。

这些情况应进入 candidate refinement、manual review 或 deferred governance。

### 9.4 Conflict preservation fourth

如果候选与 raw evidence、completed cases、active rules、prior governance、accountant correction、Transaction Log audit history 或 Entity Log authority 冲突，本节点应保守处理。

典型边界：

- 冲突影响当前交易 final outcome：返回 Review / Coordinator / upstream correction，不做治理批准。
- 冲突影响长期记忆：保持治理候选或 deferral，直到冲突被解释或 accountant 明确决策。
- 冲突影响 historical audit explanation：不重写 Transaction Log，通过 governance history 解释后续变化。
- 冲突影响 rule authority 或 automation policy：不能用 LLM 选择一个版本直接生效。

### 9.5 Hard boundary

- Governance Review 是 durable authority gate，不是 runtime classifier。
- 候选不等于批准。
- accountant 当前交易 correction 不自动等于长期治理指令。
- `new_entity_candidate` 不天然阻断当前交易分类，但不创造 stable entity、approved alias、confirmed role 或 rule authority。
- Active rule 变化必须经过 accountant / governance approval。
- Automation policy 升级或放宽必须 accountant approval。
- Transaction Log 是 audit-facing，不参与 runtime decision，也不因治理变化被重写。
- 模糊、冲突、缺失或未批准状态不能被包装成 durable governance approval。

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
- Governance Review 与 Review Node 对 accountant approval capture、formal governance approval 和 durable mutation execution 的 exact split
- approved governance change 是由本节点直接执行，还是由专门 memory update workflow 执行
- governance candidate queue、grouping、dedup、expiry、reopen 和 supersession 的 exact behavior
- profile / tax config / account-mapping candidate 是否属于本节点治理范围
- auto-applied automation-policy downgrade 与 approval-required policy change 的 exact contract
- entity merge / split 后 cases、aliases、roles、rules 和 future matching 的 exact migration behavior
- rule promotion / modification / downgrade 的 exact eligibility contract
- rejected / deferred governance decision 对 future runtime warning、Knowledge Summary 和 Post-Batch Lint 的 exact handoff
