# AI Bookkeeper

## Project Overview

为加拿大会计师事务所构建的 AI Bookkeeping 系统。Accountant 上传客户银行流水和附件，系统自动分类交易、生成 Journal Entry（JE），输出审核报告供校验。业务约束：加拿大 HST/GST 税制、double-entry bookkeeping、CRA 审计合规（7 年保留）。

当前阶段：**设计完成、实现未开始**。仓库里是 spec，不是代码。

## Tech Stack

（待补充 —— 目前 spec 未锁定具体实现栈。SQLite 用于 Pattern Dictionary 和 Intervention Log，Excel 为最终交付格式，其余未定。）

## Project Structure

```
ai bookkeeper 8 nodes/     # 各节点完整 spec（按需加载，见下方 Context Documents）
tools/                     # 共享工具 spec（未来放 .py 实现）
COA/                       # Chart of Accounts 相关资源
supporting documents/      # 跨节点的设计文档（沟通偏好、deferred items、spec 格式约定）
tricks.md                  # 临时记录
```

## Development Commands

（待补充 —— 暂无实现代码，无构建/测试/运行命令。）

## Architecture Decisions

**WAT 分层**（Workflows × Agents × Tools）：workflow 是 markdown SOP，agent 是决策者（Claude 的角色），tool 是确定性 Python 脚本。AI 负责编排，脚本负责执行。

**主 workflow 瀑布式三层分类**：
```
数据预处理 → Node 1 (Profile 匹配) → Node 2 (Rules 匹配) → Node 3 (AI 分类器)
          → Coordinator (PENDING 沟通) → 输出报告 → 审核 Agent (修正 + 规则管理)
```
Node 1/2 为确定性匹配，Node 3 为 AI 判断。前一层命中即落地，未命中才下传。

**数据存储职责单一**：每个存储只回答一个问题。
- Profile = 客户是谁
- Rules = 这个 pattern 怎么分
- Observations = 这个 pattern 历史上怎么分
- Transaction Log = 这笔交易为什么这么分
- Intervention Log = accountant 为什么改

**classified_by 四种取值**：`profile_match` / `rule_match` / `ai_high_confidence` / `accountant_confirmed`。

## Critical Rules

- **IMPORTANT：确定性优先**。能用代码解决的不要用 AI。AI 是兜底。
- **IMPORTANT：Accountant 拥有最终决定权**。Agent 辅助但不替代，所有分类以 accountant 确认为准。
- **MUST：agent 对 Profile/Rules/Observations 的任何修改，必须基于 accountant 的明确指令**，不能自行推断或"优化"。
- **MUST：Transaction Log 只写+查询，不参与分类决策**。Node 1/2/3 和 Coordinator 只写，不读回来做判断。
- **MUST：Rules 升级必须 accountant 批准**，observation 达到阈值只是进入待升级队列。
- **例外不污染 observations**：accountant 判定为"这笔是例外"（rule/AI 本身没错）时，只改当期 JE，不写入 observation 的 classification_history；只有判定为"规则/AI 判断有误"时才回写。
- **讨论具体节点时按需加载对应 spec**，不要一次性拉完全部 spec。

## Context Documents

按任务类型加载对应 spec：

**数据存储节点**
- [profile_spec.md](ai%20bookkeeper%208%20nodes/profile_spec.md) — 客户结构性身份信息；Node 1 的匹配逻辑也在此
- [rules_spec_v2.md](ai%20bookkeeper%208%20nodes/rules_spec_v2.md) — 确定性规则定义与 Node 2 匹配逻辑
- [observations_spec_v2.md](ai%20bookkeeper%208%20nodes/observations_spec_v2.md) — pattern 历史聚合与升级路径
- [transaction_log_spec.md](ai%20bookkeeper%208%20nodes/transaction_log_spec.md) — 五层审计结构与字段定义

**处理节点**
- [data_preprocessing_agent_spec_v3.md](ai%20bookkeeper%208%20nodes/data_preprocessing_agent_spec_v3.md) — 原始文件解析、配对、标准化
- [confidence_classifier_spec.md](ai%20bookkeeper%208%20nodes/confidence_classifier_spec.md) — Node 3 AI 分类器，含信息源优先级
- [je_generator_spec.md](ai%20bookkeeper%208%20nodes/je_generator_spec.md) — build_je_lines 与 validate_je
- [coordinator_agent_spec_v3.md](ai%20bookkeeper%208%20nodes/coordinator_agent_spec_v3.md) — PENDING 交易与 accountant 沟通
- [review_agent_spec_v3.md](ai%20bookkeeper%208%20nodes/review_agent_spec_v3.md) — 审核修正、规则管理、Intervention Log（第 7 节）
- [output_report_spec.md](ai%20bookkeeper%208%20nodes/output_report_spec.md) — Excel 输出格式
- [onboarding_agent_spec.md](ai%20bookkeeper%208%20nodes/onboarding_agent_spec.md) — 新客户初始化（一次性）

**共享工具**
- [tools/pattern_standardization_spec.md](tools/pattern_standardization_spec.md) — description 标准化与 Pattern Dictionary

**跨节点约定**
- [supporting documents/communication_preferences.md](supporting%20documents/communication_preferences.md)
- [supporting documents/deferred_items.md](supporting%20documents/deferred_items.md) — 所有 deferred 统一在此，禁止散落各 spec
- [supporting documents/spec_format.md](supporting%20documents/spec_format.md)
- [supporting documents/development_workflow.md](supporting%20documents/development_workflow.md) — 开发流程框架（Phase 0-5 + 跨会话一致性规则）

## Current Focus

- Phase 0 synthetic dry run findings have been fed back into the specs.
- Remaining focus:
  - decide whether and how Node 3 `policy_trace` should propagate into downstream specs, with `Coordinator` first and `Transaction Log` second
  - align any downstream handoff/logging decisions with the deferred `profile_change_request -> Review Agent` ownership model
  - rerun `synthetic_pack_v1` against the updated specs
  - resolve `BUG-001` (cheque pattern standardization)
  - resolve `BUG-002` (Node 1 transfer matching contract)
