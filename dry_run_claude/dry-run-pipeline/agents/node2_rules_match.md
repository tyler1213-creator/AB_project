# Node 2 — Rules Match — Dry Run 测试 Prompt

## 你的角色

你是 Node 2（Rules Match）的 spec 审查员。你的任务是用真实交易数据测试 Rules 匹配逻辑的完整性，发现 bug、设计缺陷和歧义。

**你不是在做 bookkeeping，你是在测试 spec 有没有 bug。**

---

## 第一步：加载 Spec

请先读取以下 spec 文件：

1. `/Users/yunpengjiang/Desktop/AB project/ai bookkeeper 8 nodes/rules_spec_v2.md`

读取后，结合下方的功能逻辑要点进行分析。

---

## 第二步：功能逻辑要点（必须逐项验证）

### 2.1 Node 2 的核心职责

Node 2 是主 Workflow 的第二个分类节点。它基于已有的 **确定性规则**（Rules）匹配交易 description，为命中的交易提供可直接执行的分类答案。

**输入**：Node 1 未匹配的交易列表
**输出**：已匹配交易（含分类结果 + JE） + 未匹配交易（传递给 Node 3）

### 2.2 Rule 数据结构

每条 rule 包含以下字段：

```yaml
- rule_id: "rule_003"           # 唯一标识
  pattern: "WHT-STF TX"         # 匹配 description 的字符串
  amount_range: [2000, 3000]    # 金额范围限制（null = 不限）
  direction: "debit"            # 交易方向
  account: "Payroll Liabilities" # COA 科目
  hst: "exempt"                 # HST 处理方式
  source: "promoted_from_observation, approved_by_accountant, 2024-07-09"
  created_date: "2024-07-09"
  match_count: 0                # 累计匹配次数
```

### 2.3 匹配逻辑（核心验证点）

Node 2 的匹配逻辑需要同时满足以下条件：

**条件 1：Pattern 精确匹配**
- [ ] `transaction.description == rule.pattern`（精确匹配，不是模糊匹配、不是 contains）
- [ ] Pattern Standardization 已保证同一商户的所有 description 变体收敛为同一 canonical pattern，因此 exact match 足够
- [ ] 大小写处理：标准化后的 description 和 rule.pattern 是否都是大写？

**条件 2：Direction 匹配**
- [ ] `transaction.direction == rule.direction`
- [ ] 同一 vendor 可能有 debit 和 credit 两条 rule（如正常消费和退款）

**条件 3：Amount Range 匹配（如果 rule 设定了 amount_range）**
- [ ] `rule.amount_range` 为 null → 不限金额，只要 pattern + direction 匹配就命中
- [ ] `rule.amount_range = [min, max]` → `min ≤ transaction.amount ≤ max` 才命中
- [ ] amount_range 的用途：区分同一 vendor 的不同业务类型。例如 CRA 的小额 debit 可能是所得税，大额可能是 HST 退税
- [ ] **边界情况**：如果交易金额刚好等于 min 或 max，是否命中？（含边界 vs 不含边界）
- [ ] **边界情况**：如果同一 pattern + direction 有多条 rule（不同 amount_range），匹配顺序是什么？是否可能匹配到多条？

**匹配优先级与冲突处理**
- [ ] 当多条 rule 都匹配同一笔交易时（如同一 pattern 不同 amount_range），如何选择？
- [ ] spec 是否定义了匹配优先级？（如 amount_range 更窄的优先？先定义的优先？）
- [ ] 如果没有定义，这是一个 spec 缺陷

### 2.4 匹配成功后的处理

- [ ] 分类结果：`classified_by: "rule_match"`
- [ ] JE 生成：调用 `build_je_lines.py`，使用 rule 中的 `account` 和 `hst` 值
  - hst = "exempt" → exempt JE 模板（不拆 HST）
  - hst = "inclusive_13" → inclusive JE 模板（拆 HST）
  - hst = "unknown" → unknown JE 模板（？此场景是否合理——rule 的 hst 能是 unknown 吗？）
- [ ] match_count += 1
- [ ] Transaction Log 写入：
  - classified_by: "rule_match"
  - rule_id: 匹配的 rule 的 rule_id
- [ ] **写入 Observations**：Rule 匹配的交易是否写入 observations？
  - 根据 observations_spec：Node 2 匹配的交易应该写入 observation 的 classification_history（confirmed_by: "rule"）
  - 这影响 observation 的 count 和 months_seen 统计

### 2.5 匹配失败后的处理

- [ ] 交易原样传递给 Node 3（AI Classifier）
- [ ] 传递时数据格式与 Node 3 的输入要求是否一致？
- [ ] 是否需要附加"Node 1 + Node 2 均未匹配"的标记？

### 2.6 Rule 的三种创建路径（测试理解）

虽然 Node 2 不创建 rule，但理解创建路径有助于验证匹配逻辑的合理性：

- [ ] 路径一：Observation 自然升级（≥3 次 + 跨 2 月 + 单一分类 + accountant 批准）
- [ ] 路径二：Accountant 主动创建（通过审核 Agent）
- [ ] 路径三：Onboarding 历史数据自动升级（无需 accountant 二次确认）

**测试重点**：不同来源的 rule 结构是否完全一致？匹配逻辑是否对所有来源的 rule 一视同仁？

### 2.7 Rule 的修改和删除对 Node 2 的影响

- [ ] Rule 被修改（account/hst 变更）后，Node 2 下次运行是否自动使用新值？
- [ ] Rule 被删除后，之前被该 rule 匹配的交易在下次运行时会落到 Node 3
- [ ] match_count 是否会被重置？（Rule 修改后 match_count 是否清零？）

### 2.8 新客户场景（rules.md 为空）

- [ ] 全新客户（方式一问卷 onboarding）rules.md 为空文件
- [ ] Node 2 处理空 rules 列表是否有异常？所有交易是否正确传递给 Node 3？
- [ ] Onboarding 历史数据方式下，rules.md 可能有自动升级的 rule，Node 2 是否能正确匹配？

---

## 第三步：执行测试

**从 Node 1 传递的未匹配交易：**

{{transactions}}

**Rules 数据（用户提供或默认空）：**

{{client_context}}

请逐笔交易按上述匹配逻辑走查。对每笔交易：

1. 确认 description（canonical pattern）
2. 遍历所有 rule，检查 pattern + direction + amount_range 三个条件
3. 记录匹配结果（命中哪条 rule / 未命中 / 多条 rule 冲突）
4. 命中的交易：模拟 JE 生成（选择正确的 JE 模板）
5. 未命中的交易：记录传递给 Node 3 的数据

**重点关注：**
- 空 rules 场景是否所有交易都正确下传
- amount_range 边界情况
- 多 rule 冲突处理逻辑是否明确
- 匹配成功后 observation 写入逻辑是否清晰

---

## 第四步：输出结果

请严格按照以下格式输出：

```
## Node 2 — Rules Match — 分析结果

### 1. 处理结果
[已匹配交易列表，含匹配的 rule_id 和 JE 模拟]

### 2. 传递给下一节点
[未匹配交易列表，供 Node 3 AI Classifier 使用]

### 3. 发现的 Bug
[使用 N2-xxx 编号]

### 4. 接口问题
[从 Node 1 接收的数据中发现的问题]

### 5. Spec 歧义
[Rules spec 中描述模糊的地方]

### 6. 备注
[其他观察]
```
