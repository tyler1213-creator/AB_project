# AI Bookkeeper

## Document Role

`CLAUDE.md` 现在只保留**稳定总纲**。  
它不再承担当前窗口 handoff、动态优先级、或迁移过程中的临时状态说明。

**当前工作入口一律以 [AGENTS.md](/Users/yunpengjiang/Desktop/AB%20project/AGENTS.md) 为主。**

如果你要开始一个新任务，默认顺序应是：

1. `AGENTS.md`
2. `TASK_STATE.md`
3. `PLANS.md`
4. 再按任务加载对应 spec

---

## Project Overview

为加拿大会计师事务所构建的 AI Bookkeeping 系统。Accountant 上传客户银行流水和附件，系统自动分类交易、生成 Journal Entry（JE），输出审核报告供校验。业务约束包括：

- 加拿大 HST/GST 税制
- double-entry bookkeeping
- CRA 审计追溯与 7 年保留要求

当前仓库仍是 **spec-first、设计优先** 阶段。这里主要存放系统设计文档，不是实现代码仓库。

---

## Project Structure

```text
ai bookkeeper 8 nodes/     # 旧系统 node spec（当前主要作为参考与迁移来源）
tools/                     # 共享工具 spec
COA/                       # Chart of Accounts 相关资源
supporting documents/      # 跨节点设计文档、流程文档、deferred 项
new system/                # evidence-first 新系统重构草案
tricks.md                  # 临时记录
```

---

## Stable Architecture Principles

### WAT 分层

- `workflow（工作流）` = markdown SOP / 状态流
- `agent（代理）` = 做决策的智能层
- `tool（工具）` = 确定性脚本 / 存储 / 计算模块

原则是：

- AI 负责编排与判断
- code 负责确定性执行

### Legacy Workflow Baseline

旧系统 node spec 记录的是这条瀑布式 workflow：

```text
数据预处理 → Node 1 (Profile 匹配) → Node 2 (Rules 匹配) → Node 3 (AI 分类器)
          → Coordinator (PENDING 沟通) → 输出报告 → 审核 Agent (修正 + 规则管理)
```

- Node 1 / Node 2 = 确定性匹配
- Node 3 = AI 判断兜底
- 上一层命中即落地，未命中才下传

### 当前重构方向

- 当前设计工作以 `new system/new_system.md` 为主。
- 旧系统 spec 仍然有价值，但主要作为约束来源、比较对象和未来迁移输入。
- 当前到底在做什么，一律以 `AGENTS.md` 和 `TASK_STATE.md` 为准。

### 数据存储单一职责

每个存储只回答一个问题：

- `Profile（客户结构档案）` = 客户是谁、结构是什么
- `Rules（规则）` = 哪些交易可以被系统直接确定性执行
- `Observations（观察记录）` = 某类交易历史上怎么分过
- `Transaction Log（交易审计日志）` = 这笔交易为什么这么分
- `Intervention Log（人工干预日志）` = accountant 为什么改

---

## Critical Rules

- **确定性优先。** 能由 code 稳定解决的，不应交给 AI。
- **Accountant 拥有最终决定权。** Agent 只能辅助，不能替代。
- **Profile / Rules / Observations 的高 authority 修改必须基于 accountant 明确指令。**
- **Transaction Log 只写和查询，不参与主 workflow 分类决策。**
- **Rules 的升级必须经过治理，不应把一次性判断直接制度化。**
- **例外不应污染长期学习层。** 如果 accountant 判断“这笔只是例外”，应修正当期结果，但不要把例外当成一般规律回写。
- **讨论新系统时，不能把新假设偷偷混进旧 node spec。** 新系统内容统一看独立草案。

---

## Context Documents

### 工作入口

- [AGENTS.md](/Users/yunpengjiang/Desktop/AB%20project/AGENTS.md) — 当前工作入口、阅读顺序、handoff 重点
- [TASK_STATE.md](/Users/yunpengjiang/Desktop/AB%20project/TASK_STATE.md) — 当前目标、已完成内容、风险、下一步
- [PLANS.md](/Users/yunpengjiang/Desktop/AB%20project/PLANS.md) — 阶段、目标、开放问题

### 旧系统基线 spec

**数据存储节点**

- [profile_spec.md](ai%20bookkeeper%208%20nodes/profile_spec.md)
- [rules_spec_v2.md](ai%20bookkeeper%208%20nodes/rules_spec_v2.md)
- [observations_spec_v2.md](ai%20bookkeeper%208%20nodes/observations_spec_v2.md)
- [transaction_log_spec.md](ai%20bookkeeper%208%20nodes/transaction_log_spec.md)

**处理节点**

- [data_preprocessing_agent_spec_v3.md](ai%20bookkeeper%208%20nodes/data_preprocessing_agent_spec_v3.md)
- [confidence_classifier_spec.md](ai%20bookkeeper%208%20nodes/confidence_classifier_spec.md)
- [je_generator_spec.md](ai%20bookkeeper%208%20nodes/je_generator_spec.md)
- [coordinator_agent_spec_v3.md](ai%20bookkeeper%208%20nodes/coordinator_agent_spec_v3.md)
- [review_agent_spec_v3.md](ai%20bookkeeper%208%20nodes/review_agent_spec_v3.md)
- [output_report_spec.md](ai%20bookkeeper%208%20nodes/output_report_spec.md)
- [onboarding_agent_spec.md](ai%20bookkeeper%208%20nodes/onboarding_agent_spec.md)

**共享工具**

- [pattern_standardization_spec.md](tools/pattern_standardization_spec.md)
- [transaction_identity_and_dedup_spec.md](tools/transaction_identity_and_dedup_spec.md)

### 新系统重构草案

- [new_system.md](new%20system/new_system.md) — evidence-first 新系统总纲
- [different_node.md](new%20system/different_node.md) — 新旧节点差异与替代关系

### 跨节点约定

- [supporting documents/deferred_items.md](supporting%20documents/deferred_items.md)
- [supporting documents/spec_format.md](supporting%20documents/spec_format.md)
- [supporting documents/development_workflow.md](supporting%20documents/development_workflow.md)
- [supporting documents/communication_preferences.md](supporting%20documents/communication_preferences.md)

---

## Boundary Note

当前仓库存在两套并行设计语境：

- 旧系统 node spec：参考基线与迁移来源
- 新系统 evidence-first 草案：当前设计收敛目标

在真正开始重写 legacy spec 之前：

- 旧 node spec 仍然保留，但不再默认代表当前任务
- 新系统 contract 应先在独立文档中收敛清楚
- 所有动态选择、当前重点、下一步动作，一律以 `AGENTS.md` 和 `TASK_STATE.md` 为准
