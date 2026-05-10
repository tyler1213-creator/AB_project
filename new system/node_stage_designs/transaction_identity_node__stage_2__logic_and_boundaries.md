# Transaction Identity Node — Stage 2：功能逻辑与决策边界

## 1. Stage 范围

本 Stage 2 定义 `Transaction Identity Node` 的功能逻辑与决策边界。

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

`Transaction Identity Node` 在主 workflow 中，`Evidence Intake / Preprocessing Node` 已经整理出可消费的 runtime evidence foundation 之后触发。

概念触发条件是：

- 当前材料已经具备客观交易结构和 evidence references；并且
- 系统需要判断这是否是一笔新交易、已存在交易、重复导入、或疑似同一交易；并且
- 后续 `Profile / Structural Match Node`、`Entity Resolution Node`、`Rule Match Node`、`Case Judgment Node` 或 review / logging flow 需要稳定交易身份才能继续。

典型触发场景包括：

- 新银行或支付账户交易进入主 workflow。
- 同一 batch 中出现可能重复的交易材料。
- 后续补交的小票、支票、invoice、contract 或 accountant note 可能属于已存在交易。
- 重新导入或 re-intake 材料可能与已登记交易重叠。

如果材料尚未完成 evidence intake，不应触发本节点。
如果问题已经是 business classification、entity governance、review approval 或 final audit logging，本节点不能回头吸收这些下游职责。

## 3. Input Categories

Stage 2 按判断作用组织 input categories，不列字段清单。

### 3.1 Objective transaction basis

说明当前材料中可客观确定的交易事实。

这一类输入来自 evidence intake 的标准化结果。
它用于交易身份判断，但不等于 entity 结论、case 结论或会计结论。

### 3.2 Evidence reference basis

说明当前交易材料能回到哪些原始 evidence references。

本节点使用 evidence references 来保持身份判断可追溯，并区分“同一交易材料重复出现”和“新 evidence 补充到旧交易”。

它不读取 evidence 的业务含义来做分类。

### 3.3 Source / import context basis

说明材料来自哪个导入来源、批次、账户来源、补交渠道或历史初始化语境。

这一类输入帮助区分：

- 首次导入
- 重复导入
- 同源修正
- 跨来源补充 evidence
- historical onboarding 与 runtime processing 的潜在衔接

### 3.4 Association / pairing context basis

说明上游 evidence intake 已经提出哪些客观关联、候选关联、无法关联或重复材料信号。

本节点可以消费这些信号，但不能把上游 candidate association 自动当作 confirmed same-transaction identity。

### 3.5 Existing identity basis

说明 durable identity registry / ingestion registry 中是否已有可能对应的交易身份。

这一类输入只支持交易身份判断。
它不提供 entity、rule、case、accounting 或 governance authority。

### 3.6 Evidence issue basis

说明当前材料是否存在缺失、模糊、冲突、解析不完整、来源不清或附件无法配对等问题。

这些问题可能限制 identity confidence，或使本节点只能输出 duplicate / same-transaction candidate，而不是 confirmed identity decision。

## 4. Output Categories

Stage 2 只定义 conceptual output categories，不冻结 routing enum 或对象形状。

### 4.1 New permanent transaction identity

含义：当前材料被判断为一笔尚未登记的新交易，应建立稳定 `transaction_id`。

边界：

- 这是交易对象身份，不是业务身份。
- 它不说明 counterparty / vendor / payee 是谁。
- 它不说明会计分类、HST/GST 或 automation path。

### 4.2 Existing transaction identity reuse

含义：当前材料属于已登记交易，应复用既有 `transaction_id`。

边界：

- 复用 identity 是为了保持同一交易连续性。
- 它不等于重写原始 evidence。
- 它不等于批准 review outcome 或重新分类。
- 如果当前材料是补充 evidence，后续 evidence amendment / reprocessing / review trigger 的具体边界留到后续阶段。

### 4.3 Duplicate import result

含义：当前材料看起来是已登记交易的重复导入，不应产生新的交易对象。

边界：

- duplicate import result 防止重复处理和重复落账。
- 它不删除原始 evidence。
- 它不写 `Transaction Log`。
- 它不决定是否需要 accountant review；若重复信号暴露异常，由下游 review / issue handling 处理。

### 4.4 Same-transaction / duplicate candidate

含义：当前材料可能对应已存在交易，但 evidence 不足、冲突或来源关系不清，不能安全确认。

边界：

- candidate 不能被当作 confirmed identity。
- candidate 不能自动复用 `transaction_id`。
- candidate 不能自动丢弃当前材料。
- 下游是否 pending、review 或暂停处理留给后续 workflow 边界。

### 4.5 Identity issue signal

含义：本节点可以暴露身份层问题，例如疑似重复、同一交易冲突、来源不清、补交 evidence 无法归属、或 identity registry 与当前材料不一致。

边界：

- issue signal 不是 accountant question 本身。
- issue signal 不等于 governance event。
- issue signal 不等于 final audit record。

## 5. Deterministic Code vs LLM Semantic Judgment

Stage 2 的核心边界是：

**code owns permanent identity, dedupe discipline, registry mutation, and authority limits; LLM should not create transaction identity authority.**

### 5.1 Deterministic code responsibility

Deterministic code 负责：

- 判断本节点是否被触发：evidence intake 已完成，且后续 workflow 需要交易身份。
- 基于客观交易结构、source context、evidence references 和 existing identity basis 判断新建、复用、重复或候选。
- 为新交易分配永久 `transaction_id`。
- 在 durable identity registry / ingestion registry 中建立或复用交易身份。
- 防止日期序号、展示文本或可变描述成为唯一身份 authority。
- 防止同一交易重复产生多个交易对象。
- 防止 duplicate candidate 被当作 confirmed duplicate。
- 防止 transaction identity 被下游误读为 entity、case、rule 或 accounting authority。
- 防止 `Transaction Log` 被用于 runtime dedupe decision。
- 防止本节点写入 Entity / Case / Rule / Governance 等长期业务记忆。

### 5.2 LLM semantic judgment responsibility

LLM 通常不应拥有交易身份决策 authority。

如果后续阶段允许 LLM 辅助，它最多可以在受限边界内帮助：

- 解释 messy source context 的人类可读含义。
- 总结为什么 evidence 看起来可能属于同一交易。
- 生成 identity issue explanation，供 pending / review 理解。

### 5.3 Hard boundary

LLM 不能：

- 分配 `transaction_id`
- 确认 same-transaction identity
- 确认 duplicate import
- 决定丢弃或覆盖 evidence
- 从 vendor 名称、描述相似或业务语义推断永久交易身份
- 把 identity candidate 升级为 confirmed identity
- 修改 durable identity registry
- 写入 `Transaction Log`
- 批准 entity、case、rule 或 governance change

## 6. Accountant Authority Boundary

Accountant 仍然拥有最终 accounting decision 和 durable governance authority。

`Transaction Identity Node` 不需要 accountant 来批准普通 deterministic identity assignment，但它也不能替 accountant 判断业务含义。

本节点不能：

- 替 accountant 判断交易用途
- 替 accountant 确认分类结果
- 替 accountant 决定某个冲突 evidence 的业务解释
- 把 accountant 尚未确认的说明写成最终客户政策
- 把重复导入问题转化为会计结论

如果身份冲突或疑似重复需要人工判断，本节点只能输出 identity issue signal 或 candidate context。
是否提问、如何提问、是否接受回答，属于 `Coordinator / Pending Node`、`Review Node` 或相关治理流程。

## 7. Governance Authority Boundary

Governance-level changes 不属于 Transaction Identity authority。

本节点不能：

- approve / reject alias
- confirm role
- create stable entity
- merge / split entity
- promote / modify / delete / downgrade active rule
- upgrade or relax automation policy
- approve governance event
- invalidate durable business memory

交易身份冲突可能暴露后续治理风险，例如同一 evidence 被挂到多个业务对象、或历史案例可能重复。
但本节点最多输出 identity issue signal；是否形成 entity、case、rule 或 governance candidate，属于后续节点。

## 8. Memory / Log Boundary

Stage 2 采用四层边界：read / consume、write allowed、candidate-only、no direct mutation。

### 8.1 Read / consume boundary

Transaction Identity 可以读取或消费以下 conceptual context：

- runtime evidence foundation
- objective normalized transaction basis
- evidence references
- source / import context
- evidence association result 或 duplicate-looking raw material candidate
- durable identity registry / ingestion registry 中的既有交易身份
- 当前 batch identity context

它不读取 `Transaction Log` 做 runtime dedupe decision。
它不读取 `Case Log`、`Rule Log` 或 `Knowledge Log / Summary Log` 来判断交易是否同一笔。
它不读取 `Entity Log` 来用 vendor/entity 相似性替代交易身份判断。

### 8.2 Write allowed boundary

Transaction Identity 可以在交易身份层执行有限 durable write：

- 为新交易登记永久 `transaction_id`。
- 记录交易身份与 evidence references / source context 的可追溯关联。
- 标记重复导入或 identity issue 的身份层结果。

这些写入只属于 transaction identity / ingestion registry 语义。
它们不包含业务结论，不创建 accounting authority，不创建 entity / case / rule / governance authority。

### 8.3 Candidate-only boundary

Transaction Identity 只能作为候选或 issue signal 表达：

- same-transaction candidate
- duplicate import candidate
- supplemental evidence candidate for existing transaction
- identity conflict issue
- source ambiguity issue
- registry inconsistency issue

Candidate-only 表示后续 identity review、pending、evidence amendment 或 review workflow 应评估该信号。
它不是 confirmed identity decision，也不是 business conclusion。

### 8.4 No direct mutation boundary

Transaction Identity 绝不能：

- 写入 `Transaction Log`
- 写入或修改 `Entity Log`
- 写入或修改 `Case Log`
- 写入或修改 `Rule Log`
- 写入或批准 `Governance Log`
- 修改 `Profile`
- 创建 stable entity
- 批准 alias、role、rule、automation policy 或 entity governance change
- 删除、覆盖或丢弃原始 evidence
- 把 duplicate candidate 当作 confirmed duplicate 处理
- 把 transaction identity result 直接变成 accountant decision

## 9. Insufficient / Ambiguous / Conflicting Evidence Behavior

Stage 2 采用优先级边界：preserve identity stability first、do not duplicate second、do not over-merge third。

### 9.1 Preserve identity stability first

如果材料足以确认属于已登记交易，本节点应复用既有 `transaction_id`，保持交易身份连续。

不能因为重新导入、补充附件或材料展示格式变化，就随意创建新交易身份。

### 9.2 Do not duplicate second

如果材料明显是重复导入，本节点应阻止新交易对象产生。

但阻止重复交易对象不等于丢弃 evidence。
重复材料本身仍应保持可追溯，具体 evidence retention / amendment contract 留到后续阶段。

### 9.3 Do not over-merge third

如果材料可能属于同一交易，但 evidence 不足、来源冲突或关键客观事实不一致，本节点不能强行复用既有 `transaction_id`。

它应输出 same-transaction / duplicate candidate 或 identity issue signal，而不是把两笔可能不同的交易合并。

### 9.4 Conflict behavior

如果 existing identity basis 与当前 objective transaction basis 冲突，本节点应保守处理。

典型边界：

- 可确认重复：复用或标记 duplicate import。
- 可确认新交易：分配新永久身份。
- 无法确认：输出 candidate / issue signal。
- 冲突影响 downstream safety：交给 pending / review / identity issue handling，而不是自行猜测。

### 9.5 Hard boundary

- 相似 vendor 或相似描述不等于同一交易。
- 同一金额不等于同一交易。
- 同一 evidence candidate 不等于 confirmed same transaction。
- `transaction_id` 稳定性优先于导入便利。
- 去重不能靠会计语义猜测完成。
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
- durable identity registry / ingestion registry 的 exact contract
- duplicate candidate 到 confirmed duplicate 的 exact authority boundary
- supplemental evidence 归属已存在交易后的 reprocessing / review trigger
- identity conflict 的人工处理 workflow
- historical onboarding identity 与 runtime identity registry 的合并或衔接规则
- identity registry write 与 Evidence Log write 的精确事务边界
