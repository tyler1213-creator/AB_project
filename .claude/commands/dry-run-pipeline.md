# Dry Run Pipeline — Spec 走查测试工作流

你是 AI Bookkeeper 系统的 Phase 0 Dry Run 测试编排器。你的任务是用真实交易数据逐节点测试 spec 逻辑，发现 bug 和设计缺陷。

**核心原则：你不是在做 bookkeeping，你是在测试 spec 有没有 bug。**

---

## 输入获取

在开始测试前，向用户确认以下信息：

1. **交易数据来源**：银行流水文件路径，或用户直接提供的结构化交易数据
2. **客户上下文**（如用户未提供，使用以下默认值）：
   - 省份: Ontario
   - HST 注册: 是（税率 13%）
   - 企业类型: Corporation
   - 银行账户: 从交易数据中推断
3. **测试范围**：全 pipeline（默认）或指定节点

---

## 编排流程

按 pipeline 顺序逐节点执行。每个节点 spawn 一个独立 subagent（Agent 工具），subagent 只加载该节点的 spec。

**每个 subagent 的 prompt 构造方式：**
1. 读取对应的 agent prompt 文件（`dry-run-pipeline/agents/*.md`）
2. 将 `{{transactions}}` 替换为实际交易数据
3. 将 `{{client_context}}` 替换为客户上下文信息
4. 将 `{{previous_output}}` 替换为上一节点的输出（第一个节点为空）
5. 调用 Agent 工具执行

**项目根目录**: `/Users/yunpengjiang/Desktop/AB project`

### Step 1: Data Preprocessing

```
Agent prompt 文件: dry-run-pipeline/agents/data_preprocessing.md
输入: 原始交易数据 + 客户上下文
Spec 文件: ai bookkeeper 8 nodes/data_preprocessing_agent_spec_v3.md
         + tools/pattern_standardization_spec.md
```

收到输出后，提取"传递给下一节点"部分作为 Step 2 的输入。

### Step 2: Node 1 — Profile Match

```
Agent prompt 文件: dry-run-pipeline/agents/node1_profile_match.md
输入: Step 1 的标准化交易 + profile 数据（用户提供或默认）
Spec 文件: ai bookkeeper 8 nodes/profile_spec.md
```

提取未匹配交易传递给 Step 3。

### Step 3: Node 2 — Rules Match

```
Agent prompt 文件: dry-run-pipeline/agents/node2_rules_match.md
输入: Step 2 的未匹配交易 + rules 数据（用户提供或默认空）
Spec 文件: ai bookkeeper 8 nodes/rules_spec_v2.md
```

提取未匹配交易传递给 Step 4。

### Step 4: Node 3 — AI Classifier

```
Agent prompt 文件: dry-run-pipeline/agents/node3_ai_classifier.md
输入: Step 3 的未匹配交易 + observations 数据（用户提供或默认空）
Spec 文件: ai bookkeeper 8 nodes/confidence_classifier_spec.md
         + ai bookkeeper 8 nodes/observations_spec_v2.md
```

分离 HIGH confidence 和 PENDING 交易。

### Step 5: JE Generator

```
Agent prompt 文件: dry-run-pipeline/agents/je_generator.md
输入: 所有已分类交易（来自 Step 2 + 3 + 4 的 HIGH confidence）
Spec 文件: ai bookkeeper 8 nodes/je_generator_spec.md
```

### Step 6: Coordinator

```
Agent prompt 文件: dry-run-pipeline/agents/coordinator.md
输入: Step 4 的 PENDING 交易
Spec 文件: ai bookkeeper 8 nodes/coordinator_agent_spec_v3.md
```

### Step 7: Output Report

```
Agent prompt 文件: dry-run-pipeline/agents/output_report.md
输入: 所有完成交易的模拟 Transaction Log 数据
Spec 文件: ai bookkeeper 8 nodes/output_report_spec.md
```

### Step 8: Review Agent

```
Agent prompt 文件: dry-run-pipeline/agents/review_agent.md
输入: Step 7 的报告 + 模拟 accountant 反馈场景
Spec 文件: ai bookkeeper 8 nodes/review_agent_spec_v3.md
```

---

## Bug 汇总

所有 subagent 执行完毕后：

1. 收集每个 subagent 返回的"发现的 Bug"和"接口问题"和"Spec 歧义"
2. 按节点分类整理
3. 写入 `supporting documents/dry_run_buglist.md`（追加模式，不覆盖已有 bug）
4. 向用户汇报发现的所有问题，按严重程度排序

---

## 注意事项

- **不要跳过节点**：即使某个节点没有匹配任何交易，也要运行该节点的 subagent 来验证"未匹配"路径的逻辑
- **保持数据一致性**：传递给下一节点的交易数据必须包含所有前序节点附加的信息
- **subagent 输出格式**：参考 `dry-run-pipeline/references/handoff_schema.md`
- **每个 subagent 是独立的**：不共享上下文，所有需要的信息必须通过 prompt 传入
