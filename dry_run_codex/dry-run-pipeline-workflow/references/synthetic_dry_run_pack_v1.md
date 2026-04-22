# Synthetic Dry Run Pack v1 — 系统设计验证包

---

## 1. 职责定义

`Synthetic Dry Run Pack v1` 的目标不是模拟真实客户的全部复杂性，而是**在完全可控的输入条件下，验证 AI Bookkeeper 整套系统设计是否通畅**。

它主要回答 4 个问题：

1. 主 Workflow 的控制流是否完整
2. 节点之间的 handoff / contract 是否匹配
3. 共享数据结构是否足够清晰，能支撑后续代码实现
4. 当出现 PENDING / split / review / retrigger 等状态变化时，系统设计是否仍然自洽

**成功标准不是“看起来像真的”，而是“能暴露 design / contract 问题”。**

---

## 2. 为什么需要 Synthetic Pack

直接拿真实 bank statement 跑 dry run 会把多种问题混在一起：

- OCR / parser 问题
- 交易提取噪音
- 客户资料缺失
- 节点逻辑问题
- 节点接口不匹配

这会导致 dry run 的结果难以解释：我们无法快速判断，失败究竟是系统设计问题，还是输入脏数据问题。

因此 Phase 0 的推荐顺序应为：

1. **Synthetic Dry Run**
   - 验证 system design / interface / state flow
2. **Real-World Dry Run**
   - 验证 ingestion / OCR / parser / incomplete context 下的表现

Synthetic Pack 是第一层，不替代真实数据测试，但优先级更高，因为它更直接服务于后续代码开发。

---

## 3. Pack 组成

一次完整的 synthetic dry run 应包含以下材料：

### 3.1 Structured Transactions

一批完全结构化的交易数据，不依赖 OCR / PDF 解析。

每笔交易至少包含：

- `transaction_id`
- `date`
- `bank_account`
- `amount`
- `direction`
- `raw_description`
- `description`
- `pattern_source`
- `currency`
- `balance`
- `receipt`
- `cheque_info`
- `supplementary_context`
- `bs_source`

### 3.2 Client Foundation Pack

提供系统运行所需的完整基础材料：

- `profile_data`
- `coa_data`
- `rules_data`
- `observations_data`
- `tax context`

### 3.3 Expected Routing Map

对每笔交易预先定义“理论上应该走哪条路径”，用于验证接口和控制流是否符合预期。

例如：

- `TXN-01` → Node 1 命中
- `TXN-02` → Node 2 命中
- `TXN-03` → Node 3 高置信
- `TXN-04` → Node 3 pending（带选项）
- `TXN-05` → Coordinator 后解决
- `TXN-06` → split 后 retrigger

### 3.4 Accountant Simulation Script

为 Coordinator 和 Review 阶段准备一套“模拟 accountant 回复”。

目的不是表演聊天，而是验证：

- pending 交易能否被正确组织给 accountant
- accountant 的回复能否被解释成系统动作
- split / profile update / manual confirm / review correction 是否会触发正确状态变化

### 3.5 Bug Harvest Template

统一记录本轮 dry run 的发现，按以下类别输出：

- `design_bug`
- `interface_mismatch`
- `schema_gap`
- `state_flow_issue`
- `prompt_scope_issue`
- `timing_or_timeout_issue`

---

## 4. 测试范围

`Synthetic Dry Run Pack v1` 不追求“覆盖所有业务世界”，而是优先覆盖最关键的系统设计路径。

### 4.1 必测主路径

1. Data Preprocessing 已提供标准化交易
2. Node 1 Profile Match 命中
3. Node 2 Rules Match 命中
4. Node 3 高置信分类
5. Node 3 Pending（带选项）
6. Node 3 Pending（不带选项）
7. JE Generator 生成 2-line JE
8. JE Generator 生成 3-line JE（含 HST）
9. Coordinator 解析 accountant 明确确认
10. Output Report 正常生成
11. Review Agent 执行一次人工修正

### 4.2 必测边界路径

1. 内部转账
2. 支票交易
3. fallback pattern
4. force_review observation
5. split transaction
6. retrigger workflow
7. profile update 影响当前 pending
8. rule / observation / transaction log 的联动边界

---

## 5. 建议交易场景矩阵

建议 v1 先用 **12 笔交易**，覆盖而不臃肿。

| 编号 | 场景 | 预期路径 | 设计验证重点 |
|---|---|---|---|
| T01 | 内部转账（chequing → savings） | Node 1 | `account_relationships` 与交易字段契约 |
| T02 | 稳定 recurring telecom | Node 2 | rule schema / direction / account / hst |
| T03 | HOME DEPOT + receipt | Node 3 high | observation + receipt + HST 路径 |
| T04 | AMAZON 无 receipt | Node 3 pending with options | pending options 输出结构 |
| T05 | EMT 给分包商，需 accountant 说明 | Coordinator resolve | pending → accountant_confirmed |
| T06 | 大额 mixed-use transaction | split → retrigger | split / parent-child / supplementary_context |
| T07 | CHQ# 交易 + cheque_info | Node 3 or pending | cheque_info 是否贯穿 |
| T08 | fallback pattern 交易 | pending / excluded from observations | fallback contract |
| T09 | payroll-like 交易，但 profile.has_employees = false | pending anomaly | profile constraint 是否生效 |
| T10 | bank fee | deterministic or high confidence | 简单低价值常见路径 |
| T11 | force_review observation 命中 | pending | observations 影响 Node 3 的 contract |
| T12 | review 阶段被 accountant 改分类 | Review Agent | transaction log / intervention link |

---

## 6. 基础材料设计原则

### 6.1 Profile

必须足够完整，避免把“资料缺失”误判成“设计失败”。

建议至少包含：

- `industry`
- `business_type`
- `province`
- `has_hst_registration`
- `has_employees`
- `owner_uses_company_account`
- `bank_accounts`
- `account_relationships`
- `loans`

### 6.2 COA

必须是可工作的、有限但完整的样本表，不需要很大，但要覆盖：

- expense
- income
- asset
- liability
- bank accounts
- HST receivable / payable

### 6.3 Rules

至少准备 2-3 条确定性规则：

- 单一 recurring vendor
- bank fee
- 可选一条 direction-sensitive rule

### 6.4 Observations

至少准备 3 类 observation：

- 单一分类、可作为高置信参考
- `force_review = true`
- `non_promotable = true`

---

## 7. Accountant Simulation 设计

在 synthetic run 中，由 orchestrator 扮演 accountant 是合理的，但要注意边界：

- orchestrator 不是自由 improvisation
- orchestrator 必须按预设剧本回应
- 每次回复都要有明确的“系统意义”

### 7.1 必备 accountant 响应类型

1. **明确选项确认**
   - 例如：“T04 选 B”
2. **提供业务说明但不直接给 account**
   - 例如：“T05 是付给分包商的工程款”
3. **要求 split**
   - 例如：“T06 里 3000 是材料，2000 是老板个人消费”
4. **提供 profile 更新**
   - 例如：“公司从这个月开始有员工了”
5. **review correction**
   - 例如：“T12 不该记 Office Supplies，应改 Shareholder Loan”

### 7.2 orchestrator 的角色边界

orchestrator 扮演 accountant 时，只负责：

- 提供预设业务信息
- 触发明确状态变化
- 检验 Coordinator / Review 的解释逻辑

不负责：

- 临场创造新业务世界
- 在每轮都改设定
- 用模糊回复增加无意义噪音

---

## 8. 运行方式

### 8.1 推荐执行顺序

1. Orchestrator 加载 synthetic pack
2. 不跑 OCR / parser / statement extraction
3. 从 Data Preprocessing 的“结构化输入路径”开始
4. 每个节点仍由独立 subagent 执行
5. 每步先做 schema 校验，再路由下游
6. Coordinator / Review 阶段由 orchestrator 提供 accountant script
7. 结束后输出 bug harvest

### 8.2 与真实 dry run 的区别

| 项目 | Synthetic Dry Run | Real-World Dry Run |
|---|---|---|
| 输入来源 | 人工构造结构化数据 | PDF / OCR / CSV / 真实上下文 |
| 主要目标 | 验证设计与接口 | 验证现实世界鲁棒性 |
| accountant 参与 | 由 orchestrator 模拟 | 真实或半真实 |
| 最适合发现的问题 | contract / state flow / schema gaps | ingestion / parser / missing context |

---

## 9. 成功标准

一次 synthetic dry run 成功，不是指所有交易都被系统漂亮处理，而是满足以下条件：

1. 每笔交易都能明确进入某条设计预期路径
2. 每个节点都能稳定输出符合 handoff schema 的结构
3. 上下游字段名、语义、状态流转没有断裂
4. Coordinator / Review 的人机交互能被映射成系统动作
5. 能产出一份高质量的 bug / ambiguity / contract gap 清单

---

## 10. 本轮产出物

`Synthetic Dry Run Pack v1` 一轮执行结束后，至少应产出：

- `synthetic_source_bundle.json`
- `client_foundation_pack.json`
- `expected_routing_map.md`
- `accountant_simulation_script.md`
- 每步 handoff artifact
- `synthetic_dry_run_findings.md`
- `dry_run_buglist.md` 的更新

---

## 11. v1 边界

本版本**不解决**以下问题：

- OCR / PDF parser 准确率
- 多来源 statement ingestion
- 真实世界缺失资料下的最终自动化率
- accountant 自然语言回复的全部混乱性

这些属于后续 `Real-World Dry Run` 和产品化阶段的问题。

v1 的唯一目标是：

**让 system design 在写代码前尽可能暴露结构性问题。**
