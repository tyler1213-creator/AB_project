# Rule Match Node — Stage 1：功能意图

## 1. Stage 范围

本 Stage 1 文档定义 `Rule Match Node` 的功能意图。

它只说明这个节点为什么存在、单一核心责任是什么、明确不负责什么、位于 workflow 的什么位置、哪些下游行为依赖它，以及哪些内容已知或未决定。

本阶段不定义 schema、字段契约、对象结构、存储路径、执行算法、测试矩阵、实现任务、旧系统替代映射或 legacy 约束迁移。

## 2. 节点为什么存在

新系统的核心链条是：

```text
raw evidence
→ entity
→ case memory
→ rule
```

其中 `rule` 仍然是确定性执行层。

系统不能把所有已知对象交易都交给 LLM 或 case-based judgment；当当前交易已经具备足够的 entity、alias、role/context、automation policy 和 active rule authority 时，系统应使用已批准规则直接处理，而不是重复语义判断。

`Rule Match Node` 存在的原因，是在普通非结构性交易完成 entity resolution 后，识别当前交易是否满足已批准 deterministic rule 的全部适用条件，并在 authority 完整时给出确定性处理路径。

它让高 authority、可重复、已治理的客户规则保持确定性，也防止未确认实体、候选 alias、未确认 role、case memory 或一次性判断被误用为 rule authority。

## 3. 核心责任

`Rule Match Node` 是一个 **approved-rule deterministic execution gate**。

它的单一核心责任是：

> 在非结构性交易已完成 entity resolution 后，判断当前交易是否满足已批准 active rule 的全部 authority 和适用条件；如果满足，则给出 deterministic rule-handled path；如果不满足，则明确说明 deterministic path 为什么未完成，并交给后续 case / pending / review / governance workflow。

它只执行已有 authority 内的 deterministic rule match。

它不创造 rule。它不解释 case precedent。它不把 runtime evidence 或 candidate signal 升级为长期规则或治理结论。

## 4. 明确不负责什么

`Rule Match Node` 不负责 evidence intake、交易身份或结构性交易处理。

它不负责：

- 解析原始材料
- 保存 evidence
- 分配或复用 `transaction_id`
- 判断重复导入
- 判断内部转账、贷款还款或其他 profile-backed structural transactions

这些分别属于 `Evidence Intake / Preprocessing Node`、`Transaction Identity Node` 和 `Profile / Structural Match Node`。

它不负责实体识别或实体治理。

它不负责：

- 判断当前 evidence 指向哪个 vendor / payee / counterparty
- 创建 stable entity
- 批准 alias
- 确认 role/context
- merge / split entity
- 修改 entity lifecycle status
- 修改 automation policy

这些属于 `Entity Resolution Node` 或后续 governance workflow。

它不负责 case-based judgment 或会计语义判断。

它不负责：

- 判断 historical case precedent 是否适用
- 使用 case memory 选择 COA / HST 处理
- 在没有 active rule 时做高置信分类
- 处理 mixed-use 例外判断
- 在证据不足时猜测分类

这些属于 `Case Judgment Node`、`Coordinator / Pending Node`、`Review Node` 或后续 accounting workflow。

它不负责长期 rule governance。

它不能：

- 创建、升级、修改、删除或降级 active rule
- 把 case memory 或 repeated outcomes 自动 promote 成 rule
- 把 `new_entity_candidate`、candidate alias 或 candidate role 用作 rule match authority
- 放宽 automation policy
- 批准 governance-level change

它不生成 journal entry。
它不写 `Transaction Log`。
`Transaction Log` 保存最终处理结果和审计轨迹，只写和查询，不参与 runtime rule decision，也不是 rule source。

## 5. Workflow 位置

`Rule Match Node` 位于 `Entity Resolution Node` 之后，`Case Judgment Node` 之前。

概念顺序是：

```text
new runtime materials
→ Evidence Intake / Preprocessing Node
→ Transaction Identity Node
→ Profile / Structural Match Node
→ Entity Resolution Node
→ Rule Match Node
→ Case Judgment Node / downstream review and logging flow
```

它只处理已经过上游 evidence intake、transaction identity、profile / structural gate 和 entity resolution 的非结构性交易。

如果当前交易已由 profile-backed structural path 完成，本节点不应运行。
如果当前交易没有足够 entity / alias / role authority，本节点不能用 rule 补救。
如果没有适用 active rule，或 active rule 的适用条件不完整，本节点应把 deterministic path 未完成的原因交给下游，而不是进入语义判断。

## 6. 下游依赖

`Case Judgment Node` 依赖本节点说明 deterministic path 是否已完成，以及未完成原因。

如果 rule match 成功，后续 `JE Generation Node`、`Review Node` 和 `Transaction Logging Node` 可以使用 rule-handled result 和 rule rationale 形成分录、审核语境和审计轨迹。

如果 rule match 未完成，`Case Judgment Node` 需要知道原因属于：

- 没有适用 active rule
- entity / alias / role/context authority 不足
- automation policy 不允许 rule-based automation
- active rule 条件未满足
- rule 被治理限制、禁用或需要 review

`Coordinator / Pending Node` 依赖这些原因提出聚焦问题，而不是泛泛询问“这是什么交易”。

`Review Node` 和 `Governance Review Node` 可以使用本节点暴露的 rule miss、rule blocked、rule conflict 或 rule candidate 语境，但这些信号不等于 rule mutation approval。

`Case Memory Update Node` 和 `Post-Batch Lint Node` 可以在交易完成后评估是否存在 case-to-rule 或 rule-health 候选；本节点的 runtime miss 或 match 本身不是 rule promotion。

## 7. 已确定内容

Stage 1 已确定以下内容：

- `Rule Match Node` 是 approved-rule deterministic execution gate。
- 它位于 `Entity Resolution Node` 之后、`Case Judgment Node` 之前。
- 它只处理未被结构性路径完成、且已有 entity resolution output 的非结构性交易。
- 它只在 entity、alias、role/context、automation policy、active rule 和 rule 条件全部允许时完成 deterministic rule-handled path。
- `new_entity_candidate` 不能支持 rule match。
- candidate alias 不能支持 rule match；approved alias 才能支持 rule match。
- 未确认 role/context 不能支持需要该 role/context 的 rule match。
- Rule match 是确定性路径，不是 LLM 语义判断路径。
- 它不执行 entity resolution、case judgment、COA / HST 语义判断或 journal entry generation。
- 它不写 `Transaction Log`。
- 它不创建、升级、修改、删除、降级或批准 rules。
- Rule promotion 和 active rule changes 必须经过 accountant / governance approval。

## 8. Open Boundaries

以下问题留到后续阶段，不在 Stage 1 冻结：

- rule 条件的 exact input / output schema、字段名和对象结构。
- exact routing enum：rule hit、rule miss、rule blocked、review-required 等状态如何命名。
- role/context requirement 与 automation policy 的精确组合规则。
- 多条 active rules 同时可能适用时的 exact conflict handling。
- 非 active rule、rule stability concern、recent intervention 或 lint warning 如何通过治理状态影响 future match。
- rule miss、rule blocked 和 rule candidate signal 的 exact downstream handoff contract。
- rule-handled result 与 JE generation、review 和 transaction logging 的 exact contract。
- accountant 补充确认或 governance approval 后是否重新触发本节点。
- execution algorithm、storage path、test matrix 和 coding-agent task contract。
