# 延期事项

只记录当前仍未解决、且明确决定延后的事项。

新系统总纲见 `supporting documents/2026-04-27 new system/new_system.md`。  
新旧节点差异见 `supporting documents/2026-04-27 new system/different_node.md`。

## 设计

- 用第一性原理审视所有字段名
- 标准化工具的重新构思
- 把所有字段统一，例如 canonical pattern 本质上就是后续的 description，那完全可以统一改名为 canonical description
- onboarding agent阶段，很多记录中的交易名称等都是简化版的，如果用我们现有的字段清洗标准和匹配方式，和后续新的交易的 raw description 不一定能匹配上，这个情况该怎么处理？
- 写入observation这件事情是否应该有一个大模型来专门负责
- cheque `payee` 的轻量归一化策略
- `accrual_adjustment` 设计
- Node 3 的 LLM 输出校验与解析失败处理
- Node 3 的 LLM 调用失败 fallback

## 新系统bug

- 原疑问：如果不用模型做识别，那就还是按照交易 description 的字符串和 memory 中的实体对象做匹配，类似于 tims、home depo 这样的效果会很好；但如果一家科技公司叫做 tims button，通过字符串匹配到了 Tim Hortons，之后直接按照 Tim Hortons 处理了怎么办。
- 核心记录：字符串相似只能找候选，不能直接认实体；如果不用模型，就必须接受更保守的自动化边界，否则会持续发生 false merge，并污染规则链和记忆链。
- 核心记录：Entity Resolution 不是一个“步骤”，而是新系统里最难的工程问题之一。当前 pattern standardization 至少有明确的三层可编码 spec；如果改成“先精确别名、再模糊检索、再用模型”的 entity resolution，但不定义模糊检索算法、阈值、多候选决策、模型输入输出 schema，本质上就是用一个更难、却更不具体的模块替换掉一个已有具体设计的模块。
- 核心记录：`Transaction Log` 和 `Case Memory` 的边界目前是模糊的。两者信息来源高度重叠，但尚未说清 `Case Memory` 是从 `Transaction Log` 按 `entity_id` 聚合出的视图，还是独立存储；如果是独立存储，就有一致性风险，如果只是视图，就要重新论证它是否还需要作为独立概念存在。

## 扩展

- 审核专页前端
- 输出报告的会计软件导入格式（QBO 等）
