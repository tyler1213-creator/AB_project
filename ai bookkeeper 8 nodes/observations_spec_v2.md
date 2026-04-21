# Observations.md

---

## 1. 职责定义

记录所有非 Rules 匹配的、已有明确分类结果的交易 pattern 的历史分类事实。Observations 承担两个职责：

1. **Rules 的候选暂存区**：积累 pattern 的出现次数和分类一致性，满足条件后进入待升级队列
2. **AI 层的历史参考源**：当交易未命中 Rule 进入 AI 层时，AI 查询 observations 中同 (pattern, direction) 的历史分类记录作为判断参考

Observations 只记录"发生过什么"，不做制度性判断，不承担规则执行职责。

---

## 2. 数据格式

```yaml
- pattern: "HOME DEPOT"
  direction: "debit"
  count: 5
  months_seen: ["2024-05", "2024-06", "2024-07", "2024-08", "2024-09"]
  amount_range: [45.00, 890.00]
  confirmed_by: "accountant"
  classification_history:
    - account: "Supplies & Materials"
      hst: "inclusive_13"
      count: 4
    - account: "Shareholder Loan"
      hst: "exempt"
      count: 1
  non_promotable: false
  force_review: false
  accountant_notes: ""
```

### 字段说明

- **pattern**：交易 description 的标准化 pattern
- **direction**：交易方向（debit / credit）。同一 pattern 在不同 direction 下会计意义不同（如 CRA debit = 缴税，credit = 退税），因此 (pattern, direction) 共同构成 observation 的聚合 key
- **count**：该 pattern 累计出现总次数
- **months_seen**：出现过的月份列表，用于判断跨月升级条件和清理机制中的过期判断
- **amount_range**：历史出现的金额范围 [最小值, 最大值]，为 accountant 审核升级时提供参考
- **confirmed_by**：最近一次分类的确认来源，两种值：`ai` / `accountant`
- **classification_history**：该 pattern 所有出现过的分类结果及各自出现次数。每条记录包含 account（COA 科目）、hst（HST 处理方式）、count（该分类出现的次数）。所有条目的 count 之和 = 顶层 count
- **non_promotable**：是否被标记为不可升级。以下情况设为 true：
  - classification_history 中存在 2 种及以上不同分类结果时 → 自动设为 true
  - Accountant 审核升级时拒绝且选择不可升级 → 手动设为 true
  - Rule 被删除回退到 observation 时 → 手动设为 true
- **force_review**：是否强制每次都走人工审核。仅由 accountant 主动决定开启，系统不自动设置
- **accountant_notes**：accountant 的判断理由或备注。AI 层读取此字段作为上下文参考。典型写入场景：rule 被删除回退时、accountant 标记 force_review 时、accountant 对该 pattern 有特殊说明时

---

## 3. 数据来源

**写入 observations 的条件：交易已有明确分类结果 + 不是由 Rules 匹配产生的。**

### 两种写入来源

1. **Node 3（置信度分类器）高置信度判断**：AI 层高置信度分类后，写入 observations，confirmed_by 标记为 `ai`
2. **Accountant 确认（通过 Coordinator Agent 或审核 Agent）**：PENDING 交易经 accountant 确认后，或审核阶段 accountant 修正分类后，写入 observations，confirmed_by 标记为 `accountant`

### 不写入 observations 的情况

- Rules 匹配的交易（已有确定性规则，无需再积累）
- PENDING 状态的交易（尚无明确分类结果）
- `pattern_source = fallback` 的交易（标准化结果不稳定，避免污染 pattern 聚合）

### 写入时的聚合逻辑

按 (pattern, direction) 聚合，同一 (pattern, direction) 只保留一条记录。新交易匹配到已有 (pattern, direction) 时：

- 更新 count（+1）
- 更新 months_seen（如当月不在列表中则追加）
- 更新 amount_range（如金额超出已有范围则扩展）
- 更新 confirmed_by（更新为最新一次的确认来源）
- 更新 classification_history：
  - 如果新分类结果与已有某条记录的 account + hst 完全一致 → 该条记录的 count +1
  - 如果新分类结果与所有已有记录都不一致 → 新增一条记录
  - 如果新增后 classification_history 中存在 2 种及以上不同分类 → 自动将 non_promotable 设为 true

---

## 4. 状态与生命周期

**Observation 有三种状态标记，可组合：**

| 标记 | 含义 | 设置方式 |
| --- | --- | --- |
| 默认（non_promotable: false, force_review: false） | 正常积累，可升级 | 新记录默认状态 |
| non_promotable: true | 不可升级为 rule | 自动（分类不一致时）或手动（accountant 拒绝升级 / rule 回退） |
| force_review: true | 每次必须走人工审核 | 仅 accountant 手动决定 |

### 生命周期

```
交易分类完成（来自 Node 3（置信度分类器）/ Accountant 确认）
  → 写入 observations（新 pattern 创建记录，已有 pattern 更新计数和 classification_history）
  → 如果 classification_history 出现第二种分类结果 → 自动标记 non_promotable: true

积累过程中（仅 non_promotable: false 的记录参与升级检查）：
  → 满足升级条件（≥3次 + 跨2月 + classification_history 中只有一种分类结果）
  → 进入待升级队列
    → Accountant 批准 → 升级为 rule，observation 记录保留
    → Accountant 拒绝（不可升级）→ 标记 non_promotable: true
    → Accountant 拒绝（再观察）→ 不做标记，下次满足条件时再次进入队列

Rule 被删除回退：
  → 对应 observation 标记 non_promotable: true
  → accountant_notes 写入判断理由

Accountant 主动标记 force_review：
  → force_review 设为 true
  → accountant_notes 写入原因

清理机制（维护流程执行）：
  → count ≤ 2 且 months_seen 中最后一个月份距今超过 18 个月 → 删除
```

### 升级为 rule 后 observation 是否保留

**保留。** Rule 可能被删除，删除后 observation 需要继续作为 AI 层参考和未来重新升级的基础。Rule 存续期间，该 pattern 的交易由 rule 匹配处理，observation 的 count 和 classification_history 不再更新。

---

## 5. 被谁读取

| 读取者 | 时机 | 目的 |
| --- | --- | --- |
| Node 3（置信度分类器） | 交易未命中 Rule 进入 AI 判断时 | 查询同 (pattern, direction) 的历史分类记录、force_review 标记、accountant_notes 作为判断参考 |
| 维护流程（代码） | 定期执行 | 检查是否有 observation 满足升级条件；执行过期清理 |

### Node 3（置信度分类器）读取 observations 后的执行逻辑

```
交易进入置信度分类器
  → 第一步：查 observations 中是否有同 (pattern, direction) 记录

  → 有记录且 force_review: true
    → 直接走中/低置信度路径
    → 带着 classification_history 和 accountant_notes 发给 accountant

  → 有记录且 force_review: false
    → AI 参考 classification_history 和 accountant_notes
    → 结合交易本身信息（金额、方向、附件/小票等）独立判断置信度
    → 信息充足 → 高置信度，直接分类
    → 信息不足 → 中/低置信度，生成选项发给 accountant

  → 无记录
    → AI 完全独立判断，不受 observations 影响
```

---

## 6. 被谁修改

### 主 Workflow 写入（代码）

| 操作 | 触发条件 |
| --- | --- |
| 新增记录 | 新 pattern 首次出现，来自 Node 3（置信度分类器）/ Accountant 确认 |
| 更新已有记录（count / months_seen / amount_range / classification_history） | 已有 pattern 再次出现 |
| 自动标记 non_promotable: true | classification_history 中出现第二种分类结果 |

### 审核 Agent

| 操作 | 触发条件 |
| --- | --- |
| 新增或更新记录（confirmed_by: accountant） | Accountant 在审核阶段修正了一笔交易的分类 |
| 标记 non_promotable: true + 写入 accountant_notes | Rule 被删除回退到 observation |
| 标记 force_review: true + 写入 accountant_notes | Accountant 主动决定该 pattern 以后必须走人工审核 |
| 更新 classification_history 中的历史记录 | Accountant 确认之前的分类结果需要更改（修正历史） |

### 维护流程（代码）

| 操作 | 触发条件 |
| --- | --- |
| 删除记录 | count ≤ 2 且 months_seen 中最后月份距今超过 18 个月 |
| 将满足条件的 observation 加入待升级队列 | non_promotable: false + count ≥ 3 + 跨 2 月 + classification_history 中只有一种分类 |

### Accountant 确认之前分类结果需要更改时的处理

当 accountant 在审核阶段发现某 pattern 的分类有误，且确认之前的分类结果也需要更改时：

1. 审核 Agent 修改当期交易的 JE
2. 审核 Agent 更新 observation 的 classification_history（修正历史分类的 account / hst）
3. 审核 Agent 列出该 pattern 在当期报告中的所有其他交易，由 accountant 决定是否逐笔审查修改

### Accountant 确认这是一次例外时的处理

当 accountant 判断当前分类问题是一次例外，之前的分类没有问题时：

1. 审核 Agent 修改当期交易的 JE
2. **例外不写入 observation**，避免污染 classification_history 的分布数据
3. 例外记录写入 intervention_log（记录"人为什么改"）

---

## 7. 与其他组件的关系

### 上游（数据来源）

| 组件 | 关系 |
| --- | --- |
| Node 3（置信度分类器） | AI 高置信度判断后写入 observation |
| Coordinator Agent | Accountant 确认 PENDING 交易后写入 observation |
| 审核 Agent | Accountant 修正分类后写入或更新 observation |

### 消费者（谁读取 Observations）

| 组件 | 关系 |
| --- | --- |
| Node 3（置信度分类器） | 读取同 (pattern, direction) 的 classification_history、force_review、accountant_notes 作为判断参考 |
| 维护流程 | 读取全部 observations 检查升级条件和清理条件 |

### 下游（升级路径）

| 组件 | 关系 |
| --- | --- |
| Rules | Observation 满足升级条件（non_promotable: false + ≥3次 + 跨2月 + 单一分类）且 accountant 批准后写入 rules.md |

### 反向影响

| 组件 | 关系 |
| --- | --- |
| Rules（反向） | Rule 被删除时，对应 observation 标记 non_promotable: true + 写入 accountant_notes |
