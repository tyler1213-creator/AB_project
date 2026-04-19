# 延迟事项清单

记录已识别但决定推迟实施的设计和开发项。每项注明来源上下文和优先级判断。

---

## 缺失 spec（需补写）

| 事项 | 说明 | 来源 |
|------|------|------|

## 各节点内部待定细节

| 事项 | 所属节点 | 说明 |
|------|----------|------|
| 多轮对话状态管理 / 超时提醒机制 | Coordinator Agent | 与 accountant 沟通未及时回复时的处理 |

| Accrual adjustment 设计 | 审核 Agent | 有意推迟，非 MVP 功能 |

| LLM 输出格式校验 | 置信度分类器 / validate_je | LLM 返回的 account 不在 COA.csv 中、输出 parse 失败等情况的处理。可在 JE 校验环节做代码检查 |

| LLM 调用失败 fallback 策略 | 置信度分类器 | timeout / rate limit / 格式错误时的处理策略。建议：失败的交易直接标记 PENDING |
## 产品功能扩展

| 事项 | 说明 |
|------|------|
| 审核专页前端 | 聊天入口 MVP 验证后，开发独立的审核 Web 页面（表格视图、批量操作、筛选排序） |
| 导入会计软件格式 | 输出报告支持 QBO（QuickBooks Online）等会计软件的导入格式 |
| 各 Agent spec 补充交互设计板块 | Coordinator、Review、Onboarding Agent 的 spec 各自补充人机交互设计（消息格式、聊天流程、错误处理），嵌入各 Agent spec 而非单独文档 |