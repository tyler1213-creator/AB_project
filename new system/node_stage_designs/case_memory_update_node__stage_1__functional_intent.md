# Case Memory Update Node — Stage 1：功能意图

## 1. Stage 范围

本 Stage 1 文档定义 `Case Memory Update Node` 的功能意图。

它只说明这个节点为什么存在、单一核心责任是什么、明确不负责什么、位于 workflow 的什么位置、哪些下游行为依赖它，以及哪些内容已知或未决定。

本阶段不定义 schema、字段契约、对象结构、存储路径、执行算法、测试矩阵、实现任务、旧系统替代映射或 legacy 约束迁移。

## 2. 节点为什么存在

新系统的学习路径不是从 `Transaction Log` 直接反喂 runtime decision，也不是把一次系统判断自动升级成 deterministic rule。

已完成交易需要进入长期案例记忆，但这个动作必须和审计日志、治理审批、规则升级、实体权限变化分开。

`Case Memory Update Node` 存在的原因，是在当前交易已经完成必要 review、JE、final logging 或等价 finalization boundary 后，把可学习的完成交易沉淀为 `Case Log` 中的真实案例，并把可能需要后续治理的 entity / alias / role / rule 信号整理成候选。

它让系统以后能够回答：

- 过去真实完成的类似交易怎样处理。
- 当时有哪些证据、例外、correction 或 review context。
- 哪些经验只能作为案例先例，不能直接变成 rule。
- 哪些长期记忆变化需要交给治理流程，而不是由 runtime 节点自行生效。

## 3. 核心责任

`Case Memory Update Node` 是一个 **completed-transaction case-learning node**。

它的单一核心责任是：

> 在当前交易已完成并具备可学习 authority 后，把交易 outcome、证据语境、例外语境和 accountant correction / review context 沉淀为 case memory；同时把 entity、alias、role、rule 或 automation-policy 相关变化只提出为候选，交给后续治理或 lint workflow。

它负责“这笔已完成交易可以如何成为未来 case precedent”。

它不负责“这笔交易最终应该怎样处理”，也不负责“候选是否应成为稳定规则或治理变化”。

## 4. 明确不负责什么

`Case Memory Update Node` 不替代上游 workflow nodes。

它不负责：

- evidence intake 或客观结构标准化
- 分配或复用 `transaction_id`
- profile-backed structural match
- entity resolution
- deterministic rule match
- case-based runtime judgment
- pending clarification 提问
- accountant-facing review decision capture
- journal entry generation
- final audit logging

它消费已完成交易的 final outcome、authority trace、evidence / review / intervention context 和候选信号，而不是重做这些职责。

它不负责当前交易的最终会计决定。

它不能自行：

- 选择或修正 COA 科目
- 判断 HST/GST tax treatment
- 判断业务用途
- 把模糊 accountant response 解释成 correction 或 approval
- 把未完成、未批准或仍有冲突的交易写成可学习案例

它不负责高权限长期治理变化。

它不能直接：

- 创建 stable entity authority
- approve / reject alias
- confirm role
- merge / split entity
- create / promote / modify / delete / downgrade active rule
- upgrade or relax automation policy
- approve governance event
- 把 `new_entity_candidate` 升级成稳定实体
- 把一次 completed transaction outcome 自动升级成 deterministic rule

它也不负责把 `Transaction Log` 当作学习层使用。`Transaction Log` 是 audit-facing final log，只能作为完成交易和审计语境的来源之一；未来 runtime decision 应读取 `Case Log` / `Rule Log` / `Entity Log` 等相应记忆层，而不是直接从 `Transaction Log` 学习。

## 5. Workflow 位置

`Case Memory Update Node` 位于 `Transaction Logging Node` 之后，或位于具备等价 completed-transaction authority 的 finalization boundary 之后。

概念顺序是：

```text
finalized current transaction outcome
→ JE Generation / Review / Transaction Logging as required
→ Case Memory Update Node
→ Case Log write + candidate handoffs
→ Governance Review / Knowledge Compilation / Post-Batch Lint
```

它只处理已完成交易。

如果当前交易仍处于 pending、review-required、not-approved、JE-blocked、identity unresolved、evidence conflicting 或 governance-blocked 状态，本节点不应把它沉淀为完成案例。

Stage 1 不冻结 exact trigger：哪些 outcome 被视为具备 completed-transaction learning authority，留到后续阶段定义。

## 6. 下游依赖

`Case Judgment Node` 依赖 `Case Log` 中的历史案例和例外语境，判断未来交易是否有足够 case-supported basis 进入 operational classification，还是必须 pending / review。

`Rule Match Node` 不直接依赖 case memory。只有经过 accountant / governance approval 的 active rule 才能进入 deterministic rule match。

`Governance Review Node` 依赖本节点提出的 entity / alias / role / rule / automation-policy 候选，决定是否进入正式治理审批。候选本身不改变长期 authority。

`Knowledge Compilation Node` 可以把 Case Log、Entity Log、Rule Log 和 governance history 编译成客户知识摘要，但摘要不能成为 deterministic rule source。

`Post-Batch Lint Node` 可以读取 case memory 和候选信号，检查 case-to-rule 候选、entity 拆合风险、rule 稳定性和自动化风险。

## 7. 已确定内容

Stage 1 已确定以下内容：

- `Case Memory Update Node` 是 completed-transaction case-learning node。
- 它在完成交易具备可学习 authority 后运行。
- 它把已完成交易沉淀为 `Case Log` 中的 case memory。
- `Case Log` 保存真实历史案例、最终分类、证据、例外和 accountant correction。
- 它可以提出 entity / alias / role / rule / automation-policy / governance 候选。
- 候选不等于 durable authority。
- 它不写 `Transaction Log`；final audit logging 属于 `Transaction Logging Node`。
- 它不执行 entity governance、rule promotion 或 automation-policy 放宽。
- 它不把 `Transaction Log` 变成 runtime decision source 或学习层。
- `new_entity_candidate` 可以支持候选实体和 case-memory 语境，但不能获得稳定实体或规则权限。

## 8. Open Boundaries

以下问题留到后续阶段，不在 Stage 1 冻结：

- completed-transaction learning authority 的 exact boundary。
- Case Memory Update 是否必须等 final `Transaction Log` 完成后运行，还是可消费等价 finalization handoff。
- 哪些 high-confidence system outcomes 可直接形成 case，哪些必须先经 accountant review。
- accountant correction、review approval、intervention context 与 case memory 的 exact handoff contract。
- `new_entity_candidate` 相关完成交易应如何在 case memory 中表达待治理身份语境。
- case memory write 与 governance candidate handoff 的 exact separation。
- case-to-rule candidate 何时由本节点提出，何时由 `Post-Batch Lint Node` 提出。
- exact input / output schema、字段名、对象结构、routing enum、存储路径、执行算法、测试矩阵和 coding-agent task contract。
