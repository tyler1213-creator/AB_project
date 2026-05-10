# Transaction Identity Node — Stage 1：功能意图

## 1. Stage 范围

本 Stage 1 文档定义 `Transaction Identity Node` 的功能意图。

它只说明这个节点为什么存在、单一核心责任是什么、明确不负责什么、位于 workflow 的什么位置、哪些下游行为依赖它，以及哪些内容已知或未决定。

本阶段不定义 schema、字段契约、对象结构、存储路径、执行算法、测试矩阵、实现任务、旧系统替代映射或 legacy 约束迁移。

## 2. 节点为什么存在

新系统是 evidence-first，但 evidence-first 不等于每次导入都生成一笔新交易。

同一笔银行交易可能因为重复上传、补交附件、历史初始化、重新处理或来源材料变化而多次进入系统。如果没有稳定交易身份，下游会出现三个问题：

- 同一交易被重复处理或重复落账。
- 后续 review、pending、case memory、journal entry 和 audit trace 无法稳定引用同一对象。
- 交易在补证据、重跑或纠错后无法保持连续审计链。

`Transaction Identity Node` 存在的原因，是在任何业务判断之前先回答：

- 这是不是一笔已经见过的交易。
- 这是不是重复导入。
- 如果是新交易，应分配哪个永久交易身份。

它保护的是交易对象的稳定性，不是会计分类正确性。

## 3. 核心责任

`Transaction Identity Node` 是一个 **permanent transaction identity and dedupe node**。

它的单一核心责任是：

> 基于上游整理出的客观交易结构和 evidence references，为交易建立或复用稳定 `transaction_id`，并识别同一交易与重复导入关系，使后续 workflow nodes 都处理同一个永久交易对象。

它只回答交易身份问题。

它不回答“这是谁”、 “这笔该怎么分”、 “是否可以自动化”、或“哪些长期业务记忆应该改变”。

## 4. 明确不负责什么

`Transaction Identity Node` 不负责 evidence intake。

它不负责：

- 解析原始文件
- OCR 或读取 messy document
- 保存原始 evidence
- 判断附件是否业务上足以支持分类
- 把未整理材料变成 objective transaction basis

这些属于 `Evidence Intake / Preprocessing Node`。

它不负责结构性或语义性业务判断。

它不负责：

- 判断内部转账、贷款还款或其他 profile-driven 结构性交易
- 识别 counterparty / vendor / payee 所属 entity
- 判断 alias、role、entity status 或 automation policy
- 执行 deterministic rule match
- 使用 case memory 形成分类建议
- 决定 pending、review 或 operational classification path

它不负责会计结论。

它不能：

- 选择 COA 科目
- 判断 HST/GST 处理
- 生成 journal entry
- 批准 accountant review outcome

它不负责长期业务记忆或治理。

它不能：

- 写入或修改 `Entity Log`
- 写入或修改 `Case Log`
- 写入或修改 `Rule Log`
- 写入或批准 `Governance Log` 变化
- 创建或确认 stable entity
- 批准 alias、role、entity merge / split 或 automation policy 变化
- promote、modify、delete 或 downgrade active rule

它不写 `Transaction Log`。
`Transaction Log` 是最终处理结果和审计轨迹；它只写和查询，不参与 runtime decision，也不是交易身份去重的运行时输入层。

## 5. Workflow 位置

`Transaction Identity Node` 位于 `Evidence Intake / Preprocessing Node` 之后，`Profile / Structural Match Node` 之前。

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

它消费上游已整理的 objective transaction basis、evidence references、source context、association context 和 evidence quality / issue signals。

它不能回头吸收 evidence intake 的职责，也不能向后提前做 entity、rule、case 或 accounting judgment。

## 6. 下游依赖

`Profile / Structural Match Node` 依赖稳定 `transaction_id`，才能把结构性处理结果绑定到同一笔交易，而不是绑定到某次导入材料。

`Entity Resolution Node` 依赖交易身份稳定性，才能把 entity resolution context、candidate entity 或 ambiguity reason 归属于同一交易对象。

`Rule Match Node`、`Case Judgment Node` 和 `Coordinator / Pending Node` 依赖同一 `transaction_id` 串联 rule miss、case rationale、pending reason、accountant question 和补充证据。

`Review Node` 依赖它保证 accountant 审核的是同一笔交易，而不是重复导入产生的多个伪对象。

`JE Generation Node` 和 `Transaction Logging Node` 依赖它防止重复 journal entry 和重复 audit record。

`Case Memory Update Node` 依赖它把已完成交易沉淀为单一案例，而不是因为重复导入产生重复案例。

后续治理和知识摘要可以引用交易身份来解释历史事件，但不能把交易身份本身误读为 entity、case、rule 或 accounting authority。

## 7. 已确定内容

Stage 1 已确定以下内容：

- `Transaction Identity Node` 是永久交易身份与去重节点。
- 它发生在 evidence intake 之后、结构性匹配和 entity resolution 之前。
- 它基于客观交易结构和 evidence references 分配或复用稳定 `transaction_id`。
- 它处理同一交易识别和重复导入问题。
- 永久交易身份需要 durable identity registry / ingestion registry；身份不能仅靠日期序号重建。
- 它不解析原始 evidence，不保存业务结论。
- 它不做 profile / structural match、entity resolution、rule match 或 case judgment。
- 它不做会计分类、HST/GST 判断或 journal entry generation。
- 它不写 `Transaction Log`。
- 它不修改 Entity / Case / Rule / Governance 等长期业务记忆。
- 它不把 transient handoff、重复候选、临时队列或 report draft 称为 `Log`。

## 8. Open Boundaries

以下问题留到后续阶段，不在 Stage 1 冻结：

- durable identity registry / ingestion registry 的 exact contract。
- 什么证据足以确认“同一交易”，什么只能作为 duplicate candidate。
- 重复导入、新附件补交、修正导入、re-intake 和 reprocessing 的 precise workflow boundary。
- 已存在 `transaction_id` 的交易收到新 evidence 时，是 identity update、evidence amendment、review trigger，还是下游补充处理。
- historical onboarding transaction identity 与 runtime transaction identity 的衔接边界。
- 交易身份冲突或疑似重复时，下游是否继续处理，以及以什么限制继续处理。
