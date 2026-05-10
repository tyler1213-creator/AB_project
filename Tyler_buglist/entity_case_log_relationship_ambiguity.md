# Entity 与 Case Log 关系定位模糊

## 状态

开放设计问题。

本文件记录 Tyler review 过程中暴露出的设计模糊点。它不是已接受的产品设计结论，也不应被当作已经冻结的 contract。

## 核心问题

当前设计还没有清楚区分三件被混在一起讨论的事情：

- entity 作为自然业务聚合中心和 runtime 查询入口
- Case Log 作为历史判例记录的 durable source
- case 的 authority boundary 独立于 entity 当前状态变更

这次对话暴露出一个问题：直接说“case 不是 entity 的子文档”过于粗糙。它听起来像是设计在没有证明必要性的情况下，把 cases 从 entity-centered operating model 里抽离出去。

真正的问题不是物理存储位置。

真正的问题是：

> case 能否被 entity 索引和组织，同时仍然保留自己的历史 evidence、outcome、context-at-the-time 和 authority trace？

## 触发的设计损失

Tyler 的否定主要来自 locality 和 operational clarity 的损失。

自然的 runtime model 是：

```text
match entity
-> inspect rules for that entity/context
-> inspect cases for that entity/context
-> classify, pending, review, or propose rule candidate
```

如果设计只说 Case Log 是独立的，却没有同时定义 entity-centered aggregate view，系统就会失去一条明显的操作路径：

> 给定这个 vendor/payee，系统如何直接看到它的历史 cases 和 rules？

这是 domain-modeling 问题，不只是命名问题。

## 已经清楚的内容

以下 product-intent 已经足够清楚，后续设计应保留：

- Entity 回答“这个 counterparty / vendor / payee 是谁”。
- Case 回答“某笔已完成交易在特定 evidence、context、exception 和 authority 条件下是如何被处理的”。
- Runtime classification 通常先 resolve entity，再使用该 entity context 去检查 rules 和 cases。
- 一个 entity 可以有多个 role、context、case group 和可能的分类结果。
- Case memory 可以用于 case-based judgment 和 case-to-rule analysis。
- Case memory write 不批准 alias、role、stable entity authority、automation policy 或 active rule change。
- Entity merge / split 不是表达不同处理模式的唯一方式；role/context、case group、rule condition 可能更合适。

## 仍然模糊的内容

设计仍需决定或定义：

- “case belongs to entity” 是否允许作为产品心智、存储方式或 UI 模型。
- Case Log 是否仍是 source-of-truth store，同时 entity 拥有 related cases 的 index 或 view。
- case records 是物理存储在 entity 下，还是全局存储并用 `entity_id` 索引，还是两种视图同时存在。
- 每个 case 是否必须保存 `entity_context_at_time`，以及其中包含什么。
- case 如何引用 stable entity、candidate entity、alias status、role/context 和 identity risk。
- `new_entity_candidate` 在治理批准前持久化在哪里。
- candidate entity 相关 cases 是存放在 candidate entity object 下、Case Log candidate context 中，还是 governance candidate store 中。
- entity merge / split 如何影响 case references、case views 和 case-to-rule analysis。
- 分类差异什么时候应该表达为 entity split、role/context split、case group split 或 rule condition split。
- entity governance event 之后，谁有 authority 移动、重新标注、重新解释或 supersede 历史 cases。

## 为什么重要

如果这个问题不解决，系统可能滑向两个坏形态之一。

第一种是过度碎片化：

cases 在技术上和 entities 分开了，但 runtime user 和 agent 很难恢复分类所需的 entity-centered history。

第二种是 entity 过度拥有：

cases 被当作当前 entity object 里的可变 notes，导致 entity governance changes 可以静默扭曲历史判例。

这两种都会以不同方式破坏 evidence-first model。

可能更合理的方向是：

```text
Entity = identity authority and aggregate navigation center
Case = entity-indexed historical precedent record with its own authority trace
Rule = approved deterministic automation derived from stable case groups and governance
```

但这必须被明确设计，不能靠隐含理解。

## 影响范围

- `Entity Resolution Node`
- `Case Judgment Node`
- `Case Memory Update Node`
- `Governance Review Node`
- `Knowledge Compilation Node`
- `Post-Batch Lint Node`
- Stage 3 shared contracts 中涉及 entity context、case context、candidate persistence 和 governance mutation locus 的部分

## 待解决设计问题

需要定义 domain aggregate model：

```text
Case Log 是否可以在组织和检索层面 entity-owned，
同时在 authority 层面仍然作为独立的 completed-transaction precedent record？
```

设计不应继续依赖模糊的“independent log”或“entity child document”语言。
