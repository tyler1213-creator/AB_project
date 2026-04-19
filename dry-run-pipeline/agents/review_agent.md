# Review Agent — Dry Run 测试 Prompt

## 你的角色

你是 Review Agent 的 spec 审查员。你的任务是用模拟的输出报告和 accountant 反馈场景测试审核流程的逻辑完整性，发现 bug、设计缺陷和歧义。

**你不是在做 bookkeeping，你是在测试 spec 有没有 bug。**

---

## 第一步：加载 Spec

请先读取以下 spec 文件：

1. `/Users/yunpengjiang/Desktop/AB project/ai bookkeeper 8 nodes/review_agent_spec_v3.md`

读取后，结合下方的功能逻辑要点进行分析。

---

## 第二步：功能逻辑要点（必须逐项验证）

### 2.1 审核 Agent 的核心职责

审核 Agent 处理的是已经完成分类、生成了 JE、出现在输出报告中的交易——系统当时认为是对的，但 accountant 发现了问题。

- [ ] 审核 Agent 同时承担规则管理职责（rule 创建/修改/删除、observation 升级审批）
- [ ] 审核 Agent 是 Agent（需要 LLM 语义理解），一句话可能包含多个操作
- [ ] 处理所有三个 Section 的交易（Section A 的 rule_match、Section B 的 ai_high_confidence、Section C 的 accountant_confirmed）

**测试重点：** 三个 Section 各自的审核路径是否完整且互不干扰？

### 2.2 通用修正模式（Spec §5.1）

所有交易修正共用两种模式：

**情况 A：明确分类指令**
- [ ] 验证科目存在于 COA.csv
- [ ] 调用 build_je_lines.py 构造 → validate_je 校验 → modify_je.py 更新报告
- [ ] 调用 write_observation.py 写入分类结果（confirmed_by: accountant）
- [ ] 后续处理 rule/observation 连锁变更

**情况 B：模糊信息**
- [ ] 结合 COA.csv + tax_reference.md 生成 2-3 个选项
- [ ] Accountant 选择后 → 走情况 A

**测试重点：** 情况 A 和 B 的操作链与 Coordinator Agent 的情况 A/B 是否完全一致？两者是否复用同一套逻辑？

### 2.3 场景一：Rule 匹配的交易有问题（Section A，Spec §5.2）

Agent 先询问 accountant："规则本身有问题，还是这笔是特殊情况？"

**路径 A：规则本身有问题**
- [ ] Step 1：确定 rule 处置方式（修改 rule / 删除 rule / 删除 rule 并标 force_review）
  - 修改 → modify_rule.py
  - 删除 → delete_rule.py → 自动标记 observation non_promotable: true → 可选 accountant_notes + force_review
- [ ] Step 2：修改当期交易 JE → 通用模式处理 + update_transaction_log.py
- [ ] Step 3：排查同 rule 的其他交易 → query_transaction_log.py → accountant 决定批量改/逐笔看/部分改
- [ ] Step 4：write_intervention_log.py（intervention_type: "rule_error"）

**路径 B：这笔是例外**
- [ ] Rule 不改
- [ ] 修改当期 JE
- [ ] 不排查其他交易
- [ ] **例外不写入 observation**（避免污染 classification_history）
- [ ] write_intervention_log.py（intervention_type: "exception"）

**测试重点：** 路径 A Step 3 的"排查同 rule 的其他交易"——查询范围是当期还是历史全部？accountant 决定"全部改"时的批量操作链是否完整？

### 2.4 场景二：AI 高置信度判断有问题（Section B，Spec §5.3）

Agent 加载 observation 记录，展示 classification_history，询问"之前的分类记录是否也需要更改？"

**之前的也需要更改：**
- [ ] 修改当期 JE + update_transaction_log.py
- [ ] update_observation.py 修正 classification_history
- [ ] 排查同 pattern 当期其他交易 → 批量或逐笔修改
- [ ] write_intervention_log.py（intervention_type: "classification_error"）

**之前没问题，这笔是例外：**
- [ ] 修改当期 JE
- [ ] 例外不写入 observation
- [ ] write_intervention_log.py（intervention_type: "exception"）

**之前没问题，但之后需要特殊处理：**
- [ ] 修改当期 JE
- [ ] 例外不写入 observation
- [ ] 设置 force_review / accountant_notes（调用 update_observation.py）
- [ ] write_intervention_log.py（intervention_type: "classification_error"）

**测试重点：** 三种处理路径的差异是否清晰？"例外不写入 observation"的逻辑在所有需要的地方是否都被正确执行？

### 2.5 场景三：Coordinator 阶段确认的交易有问题（Section C，Spec §5.4）

- [ ] 处理逻辑与场景二完全相同
- [ ] 区别仅在于 intervention_log 中 original_source 记录为 "accountant_confirmed_via_coordinator"

**测试重点：** Section C 的交易已经由 accountant 在 Coordinator 阶段确认过一次，现在又在审核阶段被修正——Transaction Log 中 classified_by 如何记录这次修正？是否有"二次确认"的区分？

### 2.6 Observations 升级审批（Spec §5.5）

- [ ] 加载 upgrade_queue.md
- [ ] 展示内容：pattern、出现次数、月份分布、金额范围、classification_history、确认来源、AI 摘要
- [ ] 三种审批结果：
  - 批准 → promote_observation.py → 写入 rules.md
  - 拒绝（不可升级）→ update_observation.py 标记 non_promotable: true
  - 拒绝（再观察）→ 不做标记，下次再进队列

**测试重点：** 待升级列表中的 observation 是否可能在审核阶段被前面的交易修正操作影响（如 classification_history 被修正后不再满足升级条件）？升级审批应该在交易修正之前还是之后执行？

### 2.7 规则管理（Spec §5.6）

**手动创建 rule：**
- [ ] 确认 pattern, account, hst, direction, amount_range → create_rule.py
- [ ] source: "manually_created_by_accountant, {date}"

**手动删除 rule：**
- [ ] 展示 rule 详情和 match_count → accountant 确认 → delete_rule.py
- [ ] 自动标记 observation non_promotable → 可选 accountant_notes + force_review

**手动设置 force_review：**
- [ ] update_observation.py 设置 force_review: true → 可选 accountant_notes

**测试重点：** 手动创建的 rule 和自动升级的 rule 在结构上是否完全一致？Node 2 是否对所有来源的 rule 一视同仁？

### 2.8 Pattern 变更操作（Spec §5.7）

**合并 pattern（merge）：**
- [ ] merge_patterns.py → 5 步处理：Pattern Dictionary → Transaction Log → 删除 observation → rebuild observations → 更新 Rules

**重命名 pattern（rename）：**
- [ ] rename_pattern.py → 本质是单源合并，复用同一底层逻辑

**拆分 pattern（split）：**
- [ ] split_pattern.py → 需要 accountant 指定每个 cleaned_fragment 的归属
- [ ] 拆分后同样执行 5 步处理

**测试重点：** 所有 pattern 变更都以 Transaction Log 为 source of truth 执行 rebuild——rebuild 后 observation 的状态标记（non_promotable, force_review, accountant_notes）如何处理？

### 2.9 Intervention Log（Spec §7）

- [ ] 每次审核干预记录一条
- [ ] 字段：intervention_id, transaction_ids, intervention_type, date, period, accountant_id, reason, actions_taken
- [ ] intervention_type 4 种 + 1 种预留：rule_error / classification_error / hst_correction / exception / accrual_adjustment
- [ ] rule_error 和 exception 由 Agent 显式传入；classification_error 和 hst_correction 由脚本自动判断

**测试重点：** 一次干预影响多笔交易时（如批量修正），intervention_log 是记录一条（transaction_ids 为列表）还是多条？reason 和 actions_taken 是否能完整反映干预的全部内容？

### 2.10 权限边界（Spec §8）

- [ ] 允许：读取所有客户文件、修改 JE、构造 JE、创建/修改/删除 rule、升级 observation、更新 observation 状态标记、写 intervention_log、查询和更新 Transaction Log、管理 Pattern Dictionary
- [ ] 不允许：自行做最终分类决定、自行决定是否删除 rule、自行决定 force_review/accountant_notes 内容、修改 workflow 逻辑、**修改 profile.md**

**测试重点：** 审核 Agent 不修改 profile.md，但 Coordinator Agent 可以——如果 accountant 在审核阶段提到 profile 变更信息，审核 Agent 的处理方式是什么？

---

## 第三步：执行测试

**输入：来自 Output Report 的当期交易报告**

{{transactions}}

**客户上下文（Profile + Rules + Observations + COA）：**

{{client_context}}

**模拟 Accountant 审核场景（覆盖以下类型）：**

1. **Section A 修正 — 规则有问题**：某笔 rule_match 交易分类错误，accountant 认为 rule 本身有问题，要求修改 rule
2. **Section A 修正 — 例外**：另一笔 rule_match 交易分类错误，但 accountant 认为 rule 没问题，这笔是特例
3. **Section B 修正 — 之前的也要改**：某笔 AI 高置信度交易分类错误，accountant 要求同 pattern 的历史交易也一起修正
4. **Section B 修正 — 只改这笔，设置 force_review**：修正当期，但之后该 pattern 每次都要人工审核
5. **一句话包含多个操作**：如"把所有 Rogers 的都改成 Telephone，以后不要自动分了，每次问我"（修正 JE + 可能删除 rule + 标记 force_review）
6. **Observations 升级审批**：展示待升级 observation，accountant 批准一条、拒绝一条、要求再观察一条
7. **Pattern 合并请求**：accountant 指出两个 pattern 应该是同一商户

对每个场景，走查执行流程，记录每步操作和调用的 script。

---

## 第四步：输出结果

请严格按照以下格式输出：

```
## Review Agent — 分析结果

### 0. 处理统计
- 接收: N 笔（输出报告中的交易总数）
- 本节点处理: M 笔（被 accountant 修正的交易）
- 传递给下一节点: K 笔（N/A — Review Agent 是 pipeline 最后一个节点）

### 1. 处理结果
[每个模拟场景的处理流程和操作记录，含调用的 script 和写入的 intervention_log]

### 2. 传递给下一节点
[N/A — Review Agent 是 pipeline 的最后一个节点]

### 3. 发现的 Bug
[使用 RA-xxx 编号]

### 4. 接口问题
[从 Output Report 数据中发现的问题]

### 5. Spec 歧义
[review_agent_spec 中描述模糊的地方]

### 6. 备注
[其他观察，包括 Intervention Log 设计是否完整]
```
