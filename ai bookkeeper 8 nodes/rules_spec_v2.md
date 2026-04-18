# Rules.md

---

## 1. 职责定义

在主 Workflow 运行时，为匹配到的交易提供可直接执行的确定性分类答案。Rules 只回答一个问题：**这条 pattern 能不能被系统直接用来生成 JE？** Rules 不承担记录历史争议、保存人工思考过程、承接例外情况等职责。

---

## 2. 数据格式

```yaml
- rule_id: "rule_003"
  pattern: "WHT-STF TX"
  amount_range: [2000, 3000]
  direction: "debit"
  account: "Payroll Liabilities"
  hst: "exempt"
  source: "promoted_from_observation, approved_by_accountant, 2024-07-09"
  created_date: "2024-07-09"
  match_count: 0
```

### 字段说明

- **rule_id**：规则的唯一标识编码。用于 Transaction Log 中关联交易和 rule 的匹配记录，以及审核 Agent 按 rule_id 查询历史交易
- **pattern**：用于匹配交易 description 的字符串。Node 2 使用精确匹配（`transaction.description == rule.pattern`）。Pattern 标准化工具已保证同一商户的所有 description 变体收敛为同一 canonical pattern，因此 exact match 在上游标准化完成后即已足够
- **amount_range**：金额范围限制，用于区分同一 vendor 的不同业务类型（如 CRA 按金额区分税种）。为 null 时表示不限金额
- **direction**：交易方向（debit / credit）
- **account**：对应的 COA 科目名称
- **hst**：HST 处理方式（exempt / inclusive_13 / unknown）
- **source**：这条 rule 的来源记录。三种值：`promoted_from_observation, approved_by_accountant, {date}` 或 `manually_created_by_accountant, {date}` 或 `promoted_from_observation_onboarding, {date}`
- **created_date**：rule 创建日期
- **match_count**：rule 创建后累计匹配成功的次数。每次 Node 2 匹配成功时 +1。用于 accountant 审核时了解该 rule 的实际使用频率

---

## 3. 数据来源

### 来源一：从 observations 升级（主要来源）

升级必须同时满足以下全部硬性条件：

1. **出现次数**：同一 pattern 在 observations 中累计出现 ≥ 3 次
2. **跨月出现**：至少在 2 个不同月份出现过
3. **分类一致性**：classification_history 中只有一种分类结果（account 和 hst 完全相同）
4. **Accountant 确认**：人工审核批准升级

满足前三项硬性条件后，进入待升级队列。

**触发时机：** 每月批次处理完成、输出报告生成后，由代码统一扫描所有 observations，将满足条件的候选一次性打包，交由审核 Agent 在 accountant 审核报告时一并处理升级审批。

系统为每条候选生成升级摘要供 accountant 审核，包含以下信息（从上而下展示）：

- 该 pattern 出现的总次数和月份分布
- 每次的金额范围
- 每次的确认来源（ai / accountant）
- 当前分类结果（account + hst）
- AI 对该分类的业务合理性分析和升级建议

Accountant 审核时两种结果：

- **批准**：写入 rules.md，source 标记为 `promoted_from_observation`
- **拒绝**：
  - 标记为 non-promotable → observation 保留但不再进入待升级队列（除非 accountant 未来手动升级）
  - 不做标记 → 保留在 observations 中，下次满足条件时再次进入审核队列

### 来源二：Accountant 主动创建

Accountant 通过审核 Agent 直接创建 rule，无需经过 observations 积累。适用于 accountant 已经确定某个 pattern 会周期性出现的场景（如新签月租合同、新增固定供应商）。source 标记为 `manually_created_by_accountant`，与自然升级的 rule 区分，便于后期复盘两种来源的出错率差异。

### 来源三：Onboarding 历史数据自动升级

新客户 Onboarding 时，从历史账本中提取的 observations 满足升级硬性条件（≥3次 + 跨2月 + 单一分类）后，直接写入 rules.md，**无需 accountant 二次确认**。

与来源一的区别：来源一的分类结果来自运行时的 AI 判断或 accountant 逐笔确认，需要 accountant 审核升级以确保质量。来源三的分类结果直接来自 accountant 历史账本中已完成的分类，数据本身已是 accountant 审核过的，因此跳过二次确认。

source 标记为 `promoted_from_observation_onboarding, {date}`，与来源一的 `promoted_from_observation, approved_by_accountant, {date}` 区分，便于后期复盘不同来源的出错率差异。

**不能直接创建 rule 的路径以外的方式。** 任何 agent 和代码流程都只能通过以上三条路径创建 rule。

---

## 4. 状态与生命周期

**Rule 只有两种状态：存在（active）或不存在（已删除）。没有中间态。**

```
路径一：自然升级
Observation 满足硬性条件（≥3次 + 跨2月 + 单一分类）→ 进入待升级队列
  → Accountant 批准 → 写入 rules.md（active）
  → Accountant 拒绝 → 留在 observations / 标记 non-promotable

路径二：人工直接创建
Accountant 主动通过审核 Agent 创建 → 写入 rules.md（active）

路径三：Onboarding 历史数据自动升级
历史账本提取的 observation 满足硬性条件 → 直接写入 rules.md（active）

Active rule 在审核阶段被发现问题 → 三种处理方向：
  → 修改 rule：修正 account 或 hst，rule 继续使用
  → 忽略例外：rule 不动，这笔交易单独记录正确分类
  → 删除 rule：从 rules.md 中移除，对应 observation 标记 non_promotable + 写入 accountant 判断理由

Active rule 被 accountant 主动删除：
  → Accountant 通过审核 Agent 直接删除 rule
```

**没有过期清理机制。** Rule 一旦创建，除非被人工删除，否则永久有效。

---

## 5. 被谁读取

**Rules 只被 Node 2 读取，不被其他节点或 Agent 读取（审核 Agent 查看 rule 详情除外）。**

| 读取者 | 时机 | 目的 |
| --- | --- | --- |
| Node 2（Rules 匹配） | 每笔交易经过主 Workflow 时 | 尝试确定性匹配，命中则直接生成 JE |
| 审核 Agent | 审核阶段 accountant 质疑某条 rule 时 | 查看 rule 的详情（pattern, account, hst, match_count, rule_id, source） |

---

## 6. 被谁修改

**所有 Agent 对 rule 的操作必须基于 accountant 的明确指令，不能自行决定。**

### 维护流程（代码）

| 操作 | 触发条件 |
| --- | --- |
| 新增 rule | Observation 满足升级条件且 accountant 批准 |

### Node 2（代码）

| 操作 | 触发条件 |
| --- | --- |
| 更新 match_count | 每次 rule 匹配成功时 +1 |
| 调用 write_transaction_log.py 写入 Transaction Log | 每次 rule 匹配成功且 JE 生成后，写入完整交易记录（classified_by = rule_match，rule_id） |

### 审核 Agent

| 操作 | 触发条件 |
| --- | --- |
| 新增 rule | Accountant 主动要求创建 |
| 修改 rule 的 account / hst | Accountant 在审核阶段发现 rule 分类结果有误，选择修改 |
| 删除 rule | Accountant 在审核阶段判断该 rule 不再适用；或 accountant 主动要求删除 |

---

## 7. 与其他组件的关系

### 上游（数据来源）

| 组件 | 关系 |
| --- | --- |
| Observations | Rule 的主要数据来源（自然升级路径） |
| Accountant（通过审核 Agent） | Rule 的直接创建来源（人工主动创建路径） |

### 消费者（谁读取 Rules）

| 组件 | 关系 |
| --- | --- |
| Node 2（Rules 匹配） | 读取 rules 做确定性匹配 |
| 审核 Agent | 查看 rule 详情辅助审核决策 |

### 下游（匹配成功后触发）

| 组件 | 关系 |
| --- | --- |
| build_je_lines.py + validate_je | Rule 匹配成功后，根据 account + hst 构造并校验 JE |
| Transaction Log | Rule 匹配成功后，记录该交易的处理明细（含 rule_id） |

### 修改者

| 组件 | 关系 |
| --- | --- |
| 审核 Agent | 接收 accountant 指令后新增、修改或删除 rule |
| 维护流程（代码） | 负责将已批准的 observation 写入 rules |
| Node 2（代码） | 匹配成功时更新 match_count |

### 反向影响

| 组件 | 关系 |
| --- | --- |
| Observations | 当 rule 被删除时，对应 observation 被标记 non_promotable 并写入 accountant 判断理由 |
