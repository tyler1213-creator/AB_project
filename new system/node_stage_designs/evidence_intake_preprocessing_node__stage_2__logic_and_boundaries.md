# Evidence Intake / Preprocessing Node — Stage 2：功能逻辑与决策边界

## 1. Stage 范围

本 Stage 2 定义 `Evidence Intake / Preprocessing Node` 的功能逻辑与决策边界。

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

`Evidence Intake / Preprocessing Node` 在主 workflow 接收新交易材料时触发。

概念触发条件是：

- 有新的 runtime transaction materials 进入系统；并且
- 这些材料需要被整理成可追溯 evidence foundation；并且
- 后续 `Transaction Identity Node`、结构性匹配、entity resolution、rule match 或 case judgment 尚不能安全消费未经整理的原始材料。

典型触发材料包括：

- 银行或支付账户导入材料
- 小票、支票、合同、发票或其他交易附件
- accountant 或 client 在运行中补交的当前交易证据
- 与当前 batch 或当前交易相关的原始说明

如果材料属于新客户历史初始化，应由 `Onboarding Node` 处理。
如果材料已经进入交易永久身份、业务判断、review 或治理阶段，本节点不能回头吸收这些下游职责。

补交 evidence 是否重新触发本节点，取决于后续阶段对 re-intake / amendment workflow 的设计；Stage 2 只确认补交材料仍然必须保持 evidence-first 和 no-business-conclusion 边界。

## 3. Input Categories

Stage 2 按判断作用组织 input categories，不列字段清单。

### 3.1 Raw transaction source basis

说明新交易来自哪些原始交易来源，以及哪些内容是 source-provided fact。

这一类输入只提供客观来源材料。
它不等于交易身份结论、entity 结论或会计结论。

### 3.2 Supporting evidence basis

说明当前交易是否有小票、支票、合同、发票、client note、accountant note 或其他支持性证据。

这类输入可以支持后续 entity resolution、case judgment、review 和 audit。
本节点只整理、保留和引用它们，不判断最终业务用途。

### 3.3 Pairing / association basis

说明多份原始材料之间是否可能属于同一笔交易或同一组交易证据。

例如交易行与附件之间、支票材料与银行交易之间、补交材料与当前交易候选之间的关联。

本节点可以表达客观配对或候选关联，但不能替代 `Transaction Identity Node` 对同一交易和重复导入的最终身份判断。

### 3.4 Objective structure basis

说明原始材料中哪些客观交易事实可以被稳定解析和统一。

这些事实是后续节点的共同运行基础。
本节点只处理客观结构，不把描述压成学习根，也不把 merchant/counterparty 语义归属写成 entity 结论。

### 3.5 Evidence quality / completeness basis

说明当前 evidence 是否存在缺失、不可读、格式异常、来源不清、附件无法配对、内容互相冲突或解析不完整。

这类输入用于限制后续自动化和帮助 Coordinator / Review 聚焦问题。
它不是本节点自行补业务判断的许可。

### 3.6 Existing runtime context basis

说明当前 batch 或当前客户是否已有可用的 intake context，例如已导入材料、已保存 evidence reference、或上游外部导入状态。

本节点可以消费这类 context 来避免重复整理或保留材料来源关系。
它不能读取 Transaction Log 来做 runtime decision，也不能把 downstream review / governance 结果当作入口 evidence 推断。

## 4. Output Categories

Stage 2 只定义 conceptual output categories，不冻结 routing enum 或对象形状。

### 4.1 Runtime evidence foundation

含义：新交易原始材料被整理为后续节点可引用的 evidence foundation。

边界：

- foundation 保留原始材料和证据引用。
- foundation 不保存业务结论。
- foundation 不等于 identity、entity、case、rule 或 accounting authority。

### 4.2 Objective normalized transaction basis

含义：可稳定解析的客观交易结构被统一为后续 `Transaction Identity Node` 和结构性匹配可消费的基础。

边界：

- 只表达客观事实。
- 不冻结最终 schema。
- 不产生交易永久身份。
- 不产生会计分类。

### 4.3 Evidence association result

含义：本节点可以说明哪些原始材料已被客观关联，哪些只是候选关联，哪些无法安全关联。

边界：

- 关联结果帮助后续 identity、review 和 audit。
- 候选关联不能被当作已确认同一交易。
- 最终交易身份和去重不属于本节点。

### 4.4 Evidence quality / issue signals

含义：本节点可以暴露 evidence 缺失、冲突、解析失败、来源不清、附件不匹配或需要人工补充的信号。

边界：

- issue signal 不是 accountant question 本身。
- issue signal 不等于 pending routing 的最终决定。
- 下游 Coordinator / Pending Node 或 Review Node 负责把它转化为人工交互或审核动作。

### 4.5 Downstream handoff context

含义：本节点为后续 workflow nodes 提供同一组 evidence references、objective basis、quality context 和 association context。

边界：

- handoff 是运行时交接，不是 durable business memory。
- 不能把 handoff、临时队列、候选配对或草稿称为 `Log`，除非它们确实进入 durable log/store。

## 5. Deterministic Code vs LLM Semantic Judgment

Stage 2 的核心边界是：

**code owns objective extraction, evidence preservation, association discipline, and no-conclusion limits; LLM may assist messy-document understanding inside those limits.**

### 5.1 Deterministic code responsibility

Deterministic code 负责：

- 判断材料属于 runtime evidence intake，而不是 onboarding initialization、transaction identity、review 或 governance。
- 解析可客观确定的交易结构。
- 保留原始 evidence 与可追溯 references。
- 标记 evidence 来源类别和 intake 状态。
- 执行格式、完整性、一致性和可引用性检查。
- 区分已客观关联的 evidence、候选关联 evidence、无法关联 evidence。
- 防止本节点生成 transaction identity、entity identity、rule result、case judgment 或 accounting conclusion。
- 防止 `Transaction Log` 被误用为 runtime evidence source 或 learning layer。
- 防止 transient handoff、candidate association、临时解析结果或 report draft 被命名为 durable `Log`。

### 5.2 LLM semantic judgment responsibility

LLM 可以辅助：

- 从非结构化或半结构化材料中读取 human-visible text。
- 解释小票、支票、合同、invoice 或 note 中的自然语言内容。
- 帮助识别材料之间可能有关联的线索。
- 生成 evidence quality / missing-context explanation。
- 为下游 pending / review 提供可读的 evidence issue summary。

### 5.3 Hard boundary

LLM 不能：

- 把 messy evidence 解释成最终会计用途
- 判断稳定 entity
- 确认 alias 或 role
- 生成 deterministic rule result
- 判断 case precedent 是否足以分类
- 分配 transaction identity
- 写入 Transaction Log
- 修改 Entity / Case / Rule / Governance memory
- 把候选关联当作已确认事实
- 因为材料“看起来合理”而隐藏证据缺失或冲突

## 6. Accountant Authority Boundary

Accountant 仍然拥有最终 accounting decision 和 durable authority。

`Evidence Intake / Preprocessing Node` 不能：

- 替 accountant 判断业务用途
- 替 accountant 确认缺失或冲突证据的真实含义
- 把 accountant 尚未确认的说明写成最终客户政策
- 把 client-provided context 直接升级成 accountant-approved conclusion
- 批准当前交易的 review outcome

如果当前材料显示需要 accountant 补充信息，本节点只能保留 issue signal 或 handoff context。
是否提问、如何提问、是否接受回答，属于下游 `Coordinator / Pending Node`、`Review Node` 或相关 governance flow。

## 7. Governance Authority Boundary

Governance-level changes 不属于 Evidence Intake authority。

本节点不能：

- approve / reject alias
- confirm role
- create stable entity
- merge / split entity
- promote / modify / delete / downgrade active rule
- upgrade or relax automation policy
- approve governance event
- invalidate durable memory

本节点通常不产生 governance candidate。
如果 evidence 本身暴露出可能的治理风险，例如材料来源冲突、同一对象表面写法异常、或附件与交易关联反复失败，它最多只能输出 evidence issue signal，供后续节点决定是否形成 governance candidate。

## 8. Memory / Log Boundary

Stage 2 采用四层边界：read / consume、write allowed、candidate-only、no direct mutation。

### 8.1 Read / consume boundary

Evidence Intake 可以读取或消费以下 conceptual context：

- 当前 runtime raw materials
- 当前 batch 的 intake context
- 已存在的 evidence references，用于避免重复保存或保留来源关系
- 外部导入状态或材料来源说明

它不读取 `Transaction Log` 做 runtime decision。
它不读取 `Case Log`、`Rule Log` 或 `Knowledge Log / Summary Log` 来判断当前交易业务含义。
如需客户结构或 entity context，应由后续节点读取其权威来源，而不是由本节点提前消费并作结论。

### 8.2 Write allowed boundary

Evidence Intake 可以建立或追加 evidence foundation，但只能在 evidence 层职责内：

- 保存原始 evidence 或 evidence references
- 保存客观 intake / normalization context
- 保存 evidence quality、source clarity、association status 或 parsing issue context

这些写入不包含业务结论，不创建 accounting authority，不创建 governance authority。

如果后续 Stage 决定某些 intake result 在确认前只作为 runtime handoff，而不是 durable evidence write，应以 Stage 3+ contract 为准；Stage 2 只确认“可写内容必须限于 evidence layer”。

### 8.3 Candidate-only boundary

Evidence Intake 只能作为候选或 issue signal 表达：

- evidence association candidate
- unmatched supporting evidence candidate
- duplicate-looking raw material candidate
- missing evidence issue
- conflicting evidence issue
- low-quality / unreadable evidence issue

Candidate-only 表示后续 identity、pending、review 或 governance workflow 应评估该信号。
它不是 durable business conclusion，也不是最终 routing decision。

### 8.4 No direct mutation boundary

Evidence Intake 绝不能：

- 写入 `Transaction Log`
- 写入或修改 `Entity Log`
- 写入或修改 `Case Log`
- 写入或修改 `Rule Log`
- 写入或批准 `Governance Log`
- 修改 `Profile`
- 创建 transaction identity
- 创建 stable entity
- 批准 alias、role、rule、automation policy 或 entity governance change
- 把 evidence issue signal 直接变成 accountant decision

## 9. Insufficient / Ambiguous / Conflicting Evidence Behavior

Stage 2 采用优先级边界：preserve first、separate objective from uncertain second、surface issue third。

### 9.1 Preserve first

如果材料不完整、难读、格式异常或无法完全解析，本节点仍应尽可能保留原始 evidence 和来源关系。

不能因为无法解析就丢弃 evidence。
不能用模型摘要替代原始材料。

### 9.2 Separate objective from uncertain second

如果一部分客观结构可确定，另一部分不确定，本节点应把可确定部分和不确定部分分开表达。

不能为了让下游继续运行而把不确定内容伪装成客观事实。

候选配对、疑似重复、疑似同一材料、疑似附件归属，都必须保持候选语义，不能变成 confirmed identity 或 confirmed association。

### 9.3 Surface issue third

如果 evidence 缺失、模糊或冲突，本节点应把问题显露给下游，而不是自行解决业务含义。

典型行为边界：

- 缺少支持性证据：输出 missing evidence issue。
- 附件无法配对：输出 unmatched / candidate association issue。
- 原始材料互相矛盾：输出 conflicting evidence issue。
- 材料来源不清：输出 source clarity issue。
- 解析失败或低质量：输出 parsing / quality issue。

这些 issue 可以帮助下游 pending / review，但本节点不决定最终 pending、review 或 classification path。

### 9.4 Hard boundary

- Evidence ambiguity 不等于可以猜。
- Evidence conflict 不等于可以选择一个看起来更合理的版本。
- OCR / parser / LLM extraction 结果不能覆盖原始 evidence。
- 客观 intake issue 不能被静默转化为 business conclusion。
- 本节点应保留证据问题，而不是隐藏证据问题。

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
- evidence write 与 runtime handoff 的精确时机
- re-intake / supplemental evidence 的触发和覆盖规则
- evidence association candidate 到 confirmed association 的 exact authority boundary
- duplicate-looking raw material 与 transaction identity dedupe 的 exact handoff contract
