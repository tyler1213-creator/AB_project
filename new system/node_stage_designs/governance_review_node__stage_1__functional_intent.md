# Governance Review Node — Stage 1：功能意图

## 1. Stage 范围

本 Stage 1 文档定义 `Governance Review Node` 的功能意图。

它只说明这个节点为什么存在、单一核心责任是什么、明确不负责什么、位于 workflow 的什么位置、哪些下游行为依赖它，以及哪些内容已知或未决定。

本阶段不定义 schema、字段契约、对象结构、存储路径、执行算法、测试矩阵、实现任务、旧系统替代映射或 legacy 约束迁移。

## 2. 节点为什么存在

新系统会从 runtime judgment、review、case memory update、transaction logging 和 post-batch lint 中暴露长期记忆变化候选。

这些候选可能影响：

- entity 是否稳定
- alias 是否可用于后续识别和 rule match
- role/context 是否被确认
- entity 是否需要 merge / split
- rule 是否应创建、升级、修改、删除或降级
- automation policy 是否应改变

这些都不是普通 runtime 节点可以自行决定的事项。

`Governance Review Node` 存在的原因，是把这些高权限长期记忆变化从普通交易处理、case learning、audit logging 和 review package 中分离出来，进入正式治理边界：先确认候选是否有足够证据和 authority，再让 accountant / governance authority 批准、拒绝、退回或记录限制。

它防止系统把一次 runtime outcome、一次 review correction、一个候选信号或一个 lint finding 直接变成长期自动化权威。

## 3. 核心责任

`Governance Review Node` 是一个 **durable-memory governance gate**。

它的单一核心责任是：

> 对 entity、alias、role、rule、automation policy 等高权限长期记忆变化候选进行治理级审查，捕捉 accountant / governance decision，并在被明确授权的边界内形成或推动长期记忆变化。

它负责“长期记忆和自动化权威是否可以改变”。

它不负责“当前交易应该怎样分类”，也不负责“把当前交易写成审计日志或案例记忆”。

## 4. 明确不负责什么

`Governance Review Node` 不替代上游 workflow nodes。

它不负责：

- evidence intake 或客观结构标准化
- 分配或复用 `transaction_id`
- profile-backed structural match
- entity resolution
- deterministic rule match
- case-based runtime judgment
- pending clarification 提问
- accountant-facing current-transaction review package
- journal entry generation
- final transaction logging
- completed-transaction case memory write

它消费这些节点产生的候选、证据、review / intervention 语境、audit history 和 lint / consistency signal，而不是重做这些职责。

它不负责当前交易的会计处理。

它不能自行：

- 选择 COA 科目
- 判断 HST/GST treatment
- 判断业务用途
- 生成或修正 journal entry
- 把未完成、未批准或仍有冲突的当前交易推进到 finalization
- 把 governance approval 当成当前交易 accounting approval

它不把候选、队列、review draft、report draft 或 lint finding 称为 `Log`。

`Log` 只用于 durable store。治理过程中的临时候选和待审事项不是 `Log`，除非它们被写入 active baseline 定义的 durable `Governance Log`。

## 5. Workflow 位置

`Governance Review Node` 位于普通交易处理和长期治理变化之间。

概念顺序是：

```text
runtime / review / logging / case-learning / lint candidates
→ Governance Review Node
→ accountant / governance decision
→ authorized durable memory change or rejected / deferred governance record
→ Knowledge Compilation / future runtime workflow / post-batch monitoring
```

它可以消费来自以下节点或语境的治理候选：

- `Entity Resolution Node`
- `Rule Match Node`
- `Case Judgment Node`
- `Coordinator / Pending Node`
- `Review Node`
- `Transaction Logging Node`
- `Case Memory Update Node`
- `Post-Batch Lint Node`
- onboarding 或 accountant instruction 形成的治理候选

它位于 `Review Node` 之后或并行交接处，但两者职责不同：

- `Review Node` 捕捉 accountant 对当前交易结果、review package 和候选展示的审核决定。
- `Governance Review Node` 处理长期记忆和自动化权威变化。

## 6. 下游依赖

`Entity Resolution Node` 依赖治理后的 entity、alias、role 和 merge / split 结果，决定未来交易是否能安全识别到稳定实体。

`Rule Match Node` 依赖治理后的 approved alias、confirmed role、automation policy 和 active rule，决定未来交易是否可走 deterministic rule path。

`Case Judgment Node` 依赖治理后的 entity / rule / automation authority 边界，判断未来 case-based runtime judgment 的允许范围。

`Knowledge Compilation Node` 依赖治理历史，把 entity、case、rule 和 governance 变化编译成人和 agent 可读的客户知识摘要。摘要不能成为 deterministic rule source。

`Post-Batch Lint Node` 可以读取治理结果和未解决治理风险，继续检查 rule 稳定性、entity 拆合、case-to-rule 候选和自动化风险。

未来 audit / review flow 可以查询治理历史解释为什么某个实体、alias、role、rule 或 automation policy 在某时点发生变化。历史 `Transaction Log` 不应因为后续治理变化被重写。

## 7. 已确定内容

Stage 1 已确定以下内容：

- `Governance Review Node` 是 durable-memory governance gate。
- 它处理高权限长期记忆变化候选。
- 典型治理对象包括 entity merge / split、alias approval / rejection、role confirmation、rule promotion / modification / deletion / downgrade、automation policy change。
- accountant authority 仍然是长期治理变化的最终 authority。
- 候选信号不等于 durable authority。
- Case Judgment、Review、Transaction Logging 和 Case Memory Update 都不能直接批准治理变化。
- `new_entity_candidate` 不天然阻断当前交易分类，但不能未经治理成为稳定实体、支持 rule match 或自动创建 / 升级 rule。
- rule promotion 和 active rule 变化必须经过治理 / accountant approval。
- automation policy 升级或放宽必须 accountant approval；系统自动降级可以在受控边界内生效，但必须作为治理历史和 review visibility 处理。
- `Transaction Log` 是 audit-facing，不参与 runtime decision，也不因治理变化被重写。
- `Governance Log` 保存高权限长期记忆变化及其审批状态。

## 8. Open Boundaries

以下问题留到后续阶段，不在 Stage 1 冻结：

- Governance Review 与 Review Node 对 accountant approval capture、formal governance approval 和 durable mutation execution 的 exact split。
- Governance Review 是否直接执行 approved durable memory mutation，还是只生成授权 handoff 给专门 memory update workflow。
- 哪些 profile / tax config / account-mapping change 属于本节点治理范围，哪些属于其他 profile governance workflow。
- 系统自动降级 automation policy 与 accountant 审批型治理事件的 exact boundary。
- rule candidate 由 Case Memory Update、Post-Batch Lint、Governance Review 还是组合流程提出的 exact division。
- rejected / deferred governance candidate 后续如何保留、再审或过期。
- governance decision 与 Knowledge Compilation、Post-Batch Lint、future runtime authority 的 exact handoff contract。
- exact input / output schema、字段名、对象结构、routing enum、存储路径、执行算法、测试矩阵和 coding-agent task contract。
