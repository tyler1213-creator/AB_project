# Onboarding Node — Stage 2：功能逻辑与决策边界

## 1. Stage 范围

本 Stage 2 定义 `Onboarding Node` 的功能逻辑与决策边界。

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

`Onboarding Node` 在新客户初始化时触发。

它的 conceptual trigger 是：

- 有一批客户历史材料需要进入新系统；并且
- 这些材料需要被转化为 evidence-first 的初始记忆基础；并且
- 主 workflow 尚不能安全依赖空白 memory 直接运行，或需要先获得初始化 context。

典型触发材料包括：

- 历史银行流水
- accountant 已处理过的历史账本
- 小票、支票、合同或其他交易证据
- accountant 对客户结构、业务背景或特殊处理的说明

如果是主 workflow 中的新交易运行时处理，不应触发 Onboarding；应进入 Evidence Intake / Preprocessing 及后续 runtime nodes。

如果是增量历史导入、客户迁移后补材料或 re-onboarding，是否复用本节点边界仍是 Open Boundary。

## 3. Input Categories

Stage 2 按判断作用组织 input categories，不列字段清单。

### 3.1 Historical evidence basis

说明历史材料中有哪些原始证据可以保留和引用。

包括银行原始描述、小票、支票信息、历史账本原文、accountant 原话和其他可追溯来源。

这一类输入只能提供 evidence basis；它本身不等于业务结论。

### 3.2 Accountant-processed historical basis

说明哪些历史交易已经被 accountant 或 accountant-prepared books 处理过。

这类输入可以支持 historical case memory，因为它带有比普通 raw evidence 更高的会计 authority。

但它仍然需要保留 source / authority 语境，不能被抹平成系统自行推断。

### 3.3 Customer structural basis

说明历史材料是否暗示客户结构事实，例如银行账户、内部转账关系、贷款、员工、tax config、owner 使用公司账户等。

这类输入可以形成 profile candidates。
除非 active docs 或 accountant authority 已经支持稳定确认，否则不能把推断直接写成最终 profile truth。

### 3.4 Entity basis

说明历史材料中出现了哪些 counterparty、vendor、payee、alias、简称或表面写法。

Onboarding 需要判断这些表面写法是否可能会合为同一 entity，以及它们是否足以建立稳定 entity context 或只能成为 candidate。

实体层只回答“是谁”和“在客户关系里的 role/context”，不回答 COA、HST 或 journal entry。

### 3.5 Case precedent basis

说明历史交易如何被处理，以及处理条件、证据和例外是什么。

只有具备 accountant-processed basis 或其他足够 authority 的历史处理结果，才可以支持 historical case memory。

没有可靠分类 authority 的历史材料，可以作为 evidence 或 candidate context，但不能伪装成已确认 case precedent。

### 3.6 Rule stability basis

说明是否存在少量稳定对象，历史分类长期一致，例外边界清楚，且适合进入 initial rule review 或 approval path。

这类输入最多支持 rule candidate 或待批准的初始 rule 路径。
active deterministic rule authority 仍受 accountant / governance approval 约束。

### 3.7 Risk / conflict basis

说明初始化材料中是否存在混用风险、身份歧义、账本和证据不一致、分类例外、近期人工修正、role 未确认或治理风险。

这些输入用于限制初始化结论的 authority，而不是让系统用语义判断覆盖风险。

## 4. Output Categories

Stage 2 只定义 conceptual output categories，不冻结 routing enum 或对象形状。

### 4.1 Initial evidence foundation

含义：历史原始材料被保留为可追溯 evidence，并可被后续 entity、case、review 和 audit 语境引用。

边界：

- evidence 保存原始材料和引用。
- evidence 不保存业务结论。
- evidence 不等于 classification authority。

### 4.2 Profile candidates

含义：从历史材料中识别出的客户结构事实候选。

边界：

- candidate 可以帮助 Review / accountant 聚焦确认。
- candidate 不能在缺少 authority 时变成稳定 profile truth。
- profile truth 的确认边界留给 accountant authority 或后续 governance/review 流程。

### 4.3 Initial entity foundation

含义：历史材料中的 counterparty / vendor / payee 被会合为初始 entity context，或被保留为 entity candidates / alias candidates / role candidates。

边界：

- 稳定 entity 初始化必须有足够 evidence 和 source authority。
- candidate alias 可以作为后续语境，但不能支持 rule match。
- role 如果不是 accountant-confirmed 或明确 accountant-derived，不能写成稳定 role。
- entity merge / split 只能作为 governance candidate，不能由 Onboarding 无审批执行。

### 4.4 Historical case foundation

含义：accountant 已处理过的历史交易可以成为 historical case memory，使后续 Case Judgment 读取真实案例、分类结果、证据和例外。

边界：

- historical case 依赖可追溯 accountant-processed basis。
- 没有可靠 authority 的历史推断不能成为已确认 case。
- case memory 是案例和条件，不是统计压缩，也不是 deterministic rule。

### 4.5 Customer knowledge summary seed

含义：从 entity、case 和风险语境中生成客户专属知识摘要，帮助后续 humans 和 agents 理解常见模式、例外和风险。

边界：

- summary 是可读语境。
- summary 不是 deterministic rule source。
- summary 不能替代 raw evidence、case memory 或 accountant approval。

### 4.6 Rule / governance candidates

含义：少量稳定对象可能被提出为 initial rule candidate、automation policy candidate、alias / role governance candidate 或 entity governance candidate。

边界：

- candidate 只表示后续 review/governance 应评估。
- candidate 不改变 active rule。
- candidate 不放宽 automation policy。
- candidate 不批准 alias、role、entity merge/split 或 rule promotion。

## 5. Deterministic Code vs LLM Semantic Judgment

Stage 2 的核心边界是：

**code owns normalization, identity discipline, evidence preservation, dedupe, and authority limits; LLM may assist semantic extraction and reconciliation inside those limits.**

### 5.1 Deterministic code responsibility

Deterministic code 负责：

- 判断输入属于 onboarding / historical initialization，而不是 runtime transaction processing。
- 对客观结构信息做标准化。
- 为历史交易建立稳定身份并处理去重。
- 保留原始 evidence 和 evidence references。
- 标记材料来源与 authority category。
- 区分 evidence、candidate、accountant-derived historical case、rule candidate 和 governance candidate。
- 执行已知 authority limits：没有 accountant authority 的 profile、role、rule 或 governance 变化不能被写成最终 authority。
- 防止 `Transaction Log` 被误用为 onboarding 学习层。
- 防止 transient handoff、候选队列、报告草稿被命名或处理成 durable `Log`。

### 5.2 LLM semantic judgment responsibility

LLM 可以辅助：

- 从历史材料中识别可能的 vendor、payee、counterparty、简称和 alias。
- 判断多个表面写法是否可能指向同一 entity。
- 从 accountant-prepared historical books 中抽取 historical case meaning。
- 总结客户专属知识、常见处理方式、例外条件和风险提示。
- 提出 profile、entity、case、rule 或 governance candidates 的解释。

### 5.3 Hard boundary

LLM 不能：

- 把 raw evidence 直接升级为 accountant-confirmed conclusion
- 把 candidate profile fact 写成稳定 profile truth
- 把 candidate alias 支持 rule match
- 把 candidate role 写成稳定 role
- 把 rule candidate 变成 active rule
- 放宽 automation policy
- 批准 entity merge / split
- 用 summary 替代 evidence、case 或 approval
- 为缺少 accountant authority 的历史材料发明会计结论

## 6. Accountant Authority Boundary

Accountant 仍然拥有最终 accounting decision 和 durable authority。

Onboarding 可以利用 accountant 已处理过的历史账本和 accountant 说明作为高 authority 来源，但必须保留来源语境。

Onboarding 不能：

- 替 accountant 批准未确认的 profile fact
- 替 accountant 确认 role / alias / entity governance change
- 把不稳定历史模式升级成 active deterministic rule
- 把历史材料中的歧义解释成最终客户政策
- 把缺证据或冲突材料写成稳定客户知识

当初始化材料缺少 accountant authority 时，输出应保持 candidate、pending confirmation 或 review/governance candidate，而不是稳定结论。

## 7. Governance Authority Boundary

Governance-level changes 不属于 Onboarding 的最终批准 authority。

Onboarding 可以提出治理候选，例如：

- alias approval candidate
- role confirmation candidate
- entity merge / split candidate
- automation policy candidate
- rule promotion / initial rule candidate

Onboarding 不能直接批准：

- entity merge / split
- alias approval / rejection
- role confirmation
- active rule promotion / modification / deletion / downgrade
- automation policy upgrade or relaxation
- governance event approval

如果 active docs 允许某类初始化变化以 `onboarding` 作为来源进入治理事件，该事件仍必须保留 approval boundary；需要 accountant approval 的事件，在批准前不得改变长期 memory authority。

## 8. Memory / Log Boundary

Stage 2 采用四层边界：read / consume、write allowed、candidate-only、no direct mutation。

### 8.1 Read / consume boundary

Onboarding 可以读取或消费以下 conceptual context：

- 历史 raw evidence：银行流水、小票、支票、历史账本文本、accountant 原话。
- accountant-processed historical records：已由 accountant 处理过的历史分类材料。
- existing customer context：如果存在迁移资料或客户说明，可以作为初始化参考。
- existing governance / intervention context：如果初始化发生在迁移或补材料场景，可作为风险语境；该场景是否常规支持仍是 Open Boundary。

### 8.2 Write allowed boundary

Onboarding 可以建立以下初始化基础，但必须保留 authority/source 语境：

- durable evidence foundation
- accountant-derived historical case foundation
- sufficiently supported initial entity foundation
- customer knowledge summary seed

这些写入不等于无限 authority。它们只在各自 memory layer 的职责范围内有效。

### 8.3 Candidate-only boundary

Onboarding 只能作为候选提出：

- profile facts that require confirmation
- entity / alias / role changes that require governance
- rule candidates or initial rule approval candidates
- automation policy changes
- entity merge / split candidates
- unresolved conflict notes requiring accountant review

Candidate-only 表示后续 Review / Governance Review / memory workflow 应评估该信号，不是 durable approval。

### 8.4 No direct mutation boundary

Onboarding 绝不能：

- 写入新交易的 `Transaction Log`
- 把候选 rule 写成 active `Rule Log` authority
- 把 candidate alias 当作 approved alias 使用
- 把 candidate role 写入稳定 entity role
- 执行 entity merge / split
- 放宽 automation policy
- 把 customer knowledge summary 当作 deterministic rule source
- 把不可靠历史材料沉淀为 confirmed case memory

## 9. Insufficient / Ambiguous / Conflicting Evidence Behavior

Stage 2 采用优先级边界：source authority first、evidence traceability second、conflict caution third。

### 9.1 Source authority first

如果历史分类来自 accountant-prepared books 或明确 accountant instruction，它可以支持 historical case foundation。

如果历史材料只是 raw bank evidence、receipt、cheque 或系统推断，不能直接产生已确认 accounting conclusion。

缺少 source authority 时，应输出 candidate 或 review-needed context。

### 9.2 Evidence traceability second

任何初始化结论都必须能回到原始材料或 accountant source。

如果无法追溯来源，不能把结论写成稳定 memory。

如果材料足以保存 evidence 但不足以形成 entity、case 或 rule basis，应只保存 evidence 和候选说明。

### 9.3 Conflict caution third

如果历史账本、receipt、bank description、cheque information 或 accountant notes 互相冲突，Onboarding 不应自行选择最顺眼的版本作为稳定事实。

冲突行为边界：

- 可以保留冲突证据。
- 可以提出 review / governance candidate。
- 可以生成面向 accountant 的冲突说明。
- 不能把冲突隐藏在 summary 中。
- 不能把冲突材料升级为 deterministic rule。

### 9.4 Ambiguity handling

如果多个 entity、alias、role 或客户结构解释都可能成立，Onboarding 应保持候选或歧义状态。

Ambiguity 不等于可以归一化成单一稳定对象。

如果歧义只影响后续自动化权限，应限制 rule / automation path。
如果歧义影响历史案例本身是否可信，应避免写入 confirmed case memory。

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
- incremental onboarding / re-onboarding 是否复用同一 trigger boundary
- 初始 rule candidate 到 active rule 的具体 approval workflow
- profile candidate 到 stable profile truth 的具体 confirmation workflow
- 初始化部分失败时主 workflow 的启动限制
