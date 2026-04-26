# 延期事项

只记录当前仍未解决、且明确决定延后的事项。

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

## 扩展

- 审核专页前端
- 输出报告的会计软件导入格式（QBO 等）
