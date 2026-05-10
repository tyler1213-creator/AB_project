# Onboarding Node — Stage 1：功能意图

## 1. Stage 范围

本 Stage 1 文档定义 `Onboarding Node` 的功能意图。

它只说明这个节点为什么存在、单一核心责任是什么、明确不负责什么、位于 workflow 的什么位置、哪些下游行为依赖它，以及哪些内容已知或未决定。

本阶段不定义 schema、字段契约、存储路径、执行算法、测试矩阵、实现任务、旧系统替代映射或 legacy 约束迁移。

## 2. 节点为什么存在

新系统不是先把历史交易压成一个 `description / pattern`，再从压缩字符串学习规则。

新系统需要先从历史材料中建立可追溯的初始化基础：

- 原始证据是什么
- 客户结构事实有哪些候选
- 历史交易最可能指向哪些 entity
- accountant 已处理过的历史案例怎样分类
- 哪些对象稳定到值得进入 rule 审核或初始 rule 路径

`Onboarding Node` 存在的原因，是让新客户进入主 workflow 前，不是从空白状态开始，也不是从未经区分的历史统计开始，而是从 evidence-first 的初始记忆基础开始。

## 3. 核心责任

`Onboarding Node` 是一个 **initial memory bootstrapping node**。

它的单一核心责任是：

> 把新客户的历史材料转化为可追溯的初始 evidence、profile 候选、entity 基础、historical case memory 和 rule / governance 候选，使后续主 workflow 可以基于“是谁”和“过去如何处理”运行。

它处理的是初始化材料，不是运行中新交易的常规分类。

它建立初始工作基础，但不把所有推断都直接升级成长期 authority。

## 4. 明确不负责什么

`Onboarding Node` 不负责主 workflow 的 runtime classification。

它不替代：

- `Evidence Intake / Preprocessing Node`
- `Transaction Identity Node`
- `Profile / Structural Match Node`
- `Entity Resolution Node`
- `Rule Match Node`
- `Case Judgment Node`

它可以为这些节点准备初始化 context，但不吸收这些节点在新交易 runtime 中的职责。

它不负责最终 accountant review。

它不能：

- 替 accountant 批准会计结论
- 把缺少 accountant authority 的历史推断写成最终事实
- 把模糊或冲突材料强行收敛为稳定客户知识

它不负责治理批准。

它不能自行：

- 批准 entity merge / split
- 批准 alias 或 role 的高权限变化
- 放宽 automation policy
- promote、modify、delete 或 downgrade active rules
- 把候选 rule 直接变成无条件 deterministic authority

它不负责 journal entry 生成、Transaction Log 写入或 review-facing report 输出。

`Transaction Log` 是交易最终处理结果和审计轨迹，不参与 runtime decision；Onboarding 不应把初始化历史材料混写成新交易处理日志。

## 5. Workflow 位置

`Onboarding Node` 位于新客户主 workflow 之前。

它发生在客户初始化阶段，处理银行流水、历史账本、小票、支票和 accountant 补充说明等历史材料。

它的输出为后续 workflow nodes 提供初始语境：

- `Evidence Intake / Preprocessing Node` 和 `Transaction Identity Node` 可以沿用初始化形成的证据和历史交易身份基础。
- `Profile / Structural Match Node` 依赖已确认或待确认的客户结构事实。
- `Entity Resolution Node` 依赖初始化建立的 entity、alias 和 role context。
- `Rule Match Node` 只依赖已经具备足够 authority 的 deterministic rules。
- `Case Judgment Node` 依赖历史案例、例外条件和客户知识摘要。
- `Governance Review Node` 处理 Onboarding 产生的高权限候选或待批准变化。

它是 bootstrap node，不是 runtime decision gate，也不是 governance gate。

## 6. 下游依赖

下游主 workflow 依赖 `Onboarding Node` 提供以下基础：

- 可追溯的历史 evidence，使后续判断能回到原始材料。
- 初始 profile 候选，使结构性交易识别有客户事实来源。
- 初始 entity memory，使系统先识别对象，而不是依赖脆弱字符串。
- historical case memory，使 Case Judgment 能比较过去案例和当前证据。
- 客户知识摘要，使后续 agent 能读取压缩后的客户语境，但不把摘要当作 deterministic rule。
- rule / governance 候选，使 accountant 或治理流程可以批准高权限自动化变化。

如果 Onboarding 对某类材料无法安全判断，下游应看到的是候选、歧义或待确认状态，而不是被伪装成稳定 memory 的结论。

## 7. 已确定内容

Stage 1 已确定以下内容：

- `Onboarding Node` 是初始化节点，不是主 workflow 的常规 runtime 分类节点。
- 它处理历史材料，建立初始 evidence、profile 候选、entity、historical case memory 和 rule / governance 候选。
- 它的核心方向是 evidence-first：先保留证据，再建立 entity 和 case，最后才筛选 rule 候选或初始 rule 路径。
- 它可以使用 accountant 已处理过的历史账本作为高 authority 来源，但必须保留清楚的 source / authority 语境。
- 它不能把缺少 authority 的推断直接写成稳定客户事实。
- 它不能绕过 accountant authority 或 governance approval。
- 它不生成 journal entries。
- 它不写新交易的 `Transaction Log`。
- 它不把 transient handoff、候选队列或草稿称为 `Log`，除非该信息确实进入 durable storage。

## 8. Open Boundaries

以下问题留到后续阶段或治理设计，不在 Stage 1 冻结：

- 哪些历史材料足以支持稳定 entity 初始化，哪些只能形成 entity candidate。
- 哪些 accountant-derived role 可以在 Onboarding 中进入稳定 entity context。
- 初始 profile 候选怎样获得 accountant confirmation。
- 初始 rule 候选在什么审批边界后才能成为 active deterministic rule。
- Onboarding 产生的 governance candidates 由哪个后续节点聚合、展示和批准。
- re-onboarding 或增量历史导入是否复用同一节点边界。
- Onboarding 失败、部分完成或材料冲突时，主 workflow 是否允许启动，以及以什么限制启动。
