# Rule 机制与 Evidence Predicate 生命周期模糊

## 状态

开放设计问题。

本文件记录 Tyler review 过程中暴露出的设计模糊点。它不是已接受的产品设计结论，也不应被当作已经冻结的 contract。

## 核心问题

当前设计说 `Rule Match Node` 是 deterministic，不是 LLM semantic judgment；同时 `Case Judgment Node` 使用 semantic fit 和 evidence sufficiency。

这个边界在概念上是对的，但系统还没有定义中间缺失的一层：

```text
raw evidence
-> extracted fact
-> reviewed / authority-qualified fact
-> rule-eligible predicate
-> approved rule condition
```

如果没有这条生命周期，一条依赖 receipt 内容、item type、business context 或 exception condition 的 rule，很容易重新滑回 case-based semantic judgment。

如果 rule match 仍然需要问 LLM 当前 evidence 是否“像”历史 cases，那么它就不是 rule match，而是披着 rule 外衣的 high-confidence case judgment。

## 触发的设计损失

Tyler 的否定主要来自 deterministic rule execution 和 semantic case-based classification 之间的真实区别消失。

触发例子是：

```text
Home Depot
-> multiple case groups
-> one case group becomes a rule
-> next transaction must still check whether receipt evidence and business context match the rule
```

如果检查这些条件时仍然需要 runtime semantic interpretation，而系统没有 structured predicate layer，那么 rule 机制本身就不清楚。它会变成 confidence classification path，而不是 deterministic authority path。

## 已经清楚的内容

以下 product-intent 已经足够清楚，后续设计应保留：

- Rule Match 发生在 Entity Resolution 之后。
- Rule Match 需要 stable entity、相关场景下的 approved alias、confirmed role/context、允许的 automation policy，以及 active approved rule。
- `new_entity_candidate`、candidate alias、ambiguous identity 和 unresolved identity 不能支持 rule match。
- Case memory、repeated outcomes、lint findings 和 Knowledge Summary 不能替代 approved active rules。
- LLM 不应该决定 rule 是否命中。
- Case Judgment 可以在 authority limits 内使用 LLM semantic judgment 去比较 case precedent 和 current evidence。

## 仍然模糊的内容

设计仍需定义：

- 什么算 rule condition。
- 哪些 evidence facts 可以被 rule condition 消费。
- 哪些 evidence facts 属于 objective extraction，哪些属于 semantic annotation。
- receipt / invoice / cheque / contract facts 在哪里抽取。
- receipt 处理颗粒度应该到 document-level、line-item-level、category-level、purpose-level，还是 tax-support-level。
- 是否存在 `receipt_item_category`、`business_context`、`purchase_purpose_signal`、`tax_support_status` 或类似 predicates。
- 哪些 extracted facts 只能给 Case Judgment 使用，哪些可以成为 rule-eligible predicates。
- semantic evidence annotation 在支持 deterministic rule match 前需要什么 authority。
- 某类 fact type 成为 rule condition input 前是否需要 accountant review 或 governance approval。
- confidence、source span、extraction provenance 和 review status 如何表示。
- 当上游 extraction 可能使用 LLM 时，rule condition matching 如何保持 deterministic。

## Evidence 颗粒度缺口

当前 Stage 1/2 文档已经明确：Evidence Intake 会保存 raw evidence、supporting evidence、objective structure、association status 和 issue signals。

但当前文档还没有冻结 receipt 等 supporting documents 的 line-item 或 predicate contract。

一个需要明确设计的可能颗粒度阶梯是：

```text
第 0 层：原始 evidence
  receipt image, OCR text, original file, source reference

第 1 层：客观文档事实
  vendor, date, subtotal, tax, total, invoice number, payment method

第 2 层：line-item 事实
  item description, quantity, unit price, line amount, tax flag

第 3 层：标准化 evidence facts
  item_category, business_context signal, asset/supply/service hint,
  tax-support status, mixed-use signal, exception signal

第 4 层：会计解释
  COA account, GST/HST treatment, capital vs expense,
  business vs personal classification
```

可能的边界是：

- 第 0-2 层属于 evidence preservation / objective extraction concerns。
- 第 3 层是尚未解决的 predicate / annotation layer。
- 第 4 层属于 accounting judgment、review、rule outcome 或 case judgment，不属于 raw Evidence Intake。

这个阶梯只是设计辅助，不是已接受 contract。

## 为什么重要

如果这个问题不解决：

- Rule Match 可能变成伪装成 deterministic automation 的 LLM case judgment。
- Case-to-rule promotion 不会有清楚的 eligibility test。
- Accountant 对 rule 的 governance approval 会变得模糊，因为被批准的 condition 本身不清楚。
- 测试无法可靠证明 rule execution 是 deterministic。
- receipt-heavy 和 mixed-use 交易会持续重新打开 evidence extraction、case judgment、review 和 rule execution 之间的边界。

## 影响范围

- `Evidence Intake / Preprocessing Node`
- `Rule Match Node`
- `Case Judgment Node`
- `Case Memory Update Node`
- `Governance Review Node`
- `Post-Batch Lint Node`
- Stage 3 shared contracts 中涉及 objective transaction basis、evidence references、rule conditions、case precedent 和 governance approval 的部分

## 待解决设计问题

需要定义 evidence fact / predicate lifecycle：

```text
messy supporting evidence 何时、如何变成 structured、
source-grounded、authority-qualified predicate，
使 approved rule 可以 deterministic check？
```

设计必须让下面两件事无法被混淆：

```text
LLM semantic fit against cases
```

和：

```text
deterministic rule condition match against approved predicates
```
