# Review Agent — Dry Run 测试 Prompt

## 你的角色

你是 Review Agent 的 spec 审查员。你的任务是用模拟的输出报告和 accountant 反馈场景测试审核流程的逻辑完整性，发现 bug、设计缺陷和歧义。

**你不是在做 bookkeeping，你是在测试 spec 有没有 bug。**

---

## 第一步：加载 Spec

请先读取以下 spec 文件：

1. `/Users/yunpengjiang/Desktop/AB project/ai bookkeeper 8 nodes/review_agent_spec_v3.md`

读取后，用 spec 定义的逻辑走查以下模拟场景。

---

## 第二步：执行测试

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

对每个场景，走查 §5 中对应的执行流程，记录每步操作和调用的 script。

---

## 第三步：重点测试以下 spec 疑点

以下问题在 spec 中描述不够明确，请在测试时特别留意：

**intervention_type 的判断冲突**
- `exception` 和 `rule_error` 需要 Agent 显式传入；`classification_error` 和 `hst_correction` 自动判断
- 但如果 accountant 说"这笔是例外"且同时改了 account——这既是 exception 又是 classification_error
- 自动判断会覆盖 agent 的显式传入吗？哪个优先？

**删除 rule 时 observation 的 non_promotable 标记范围**
- delete_rule.py 执行后，自动标记"对应 observation 为 non_promotable"
- 如果该 pattern 有多条 rule（不同 amount_range），删除其中一条是否标记整个 observation 为 non_promotable？
- 还是只影响与被删除 rule 相同 amount_range 的记录？spec 未说明

**审核 Agent 捕获到 profile 变更信号时的处理**
- §8 权限边界：审核 Agent 不修改 profile.md，"如果在对话中捕获到 profile 变更信号，应建议 accountant 在下次处理时更新"
- 但 Coordinator Agent 会直接更新 profile 并触发 retrigger
- 两个 Agent 对同一场景（accountant 在对话中提到客户结构变更）的处理方式完全不同——这个差异是否有意为之？是否会让 accountant 困惑？

**pattern 变更后的 rebuild 范围**
- merge/rename/split 均说"以 Transaction Log 为 source of truth 执行 rebuild"
- rebuild 重新聚合 observations 时，non_promotable 和 force_review 等状态标记是保留还是重置？
- 如果原 observation 有 accountant_notes，rebuild 后是否保留？

**write_intervention_log.py 的 date 取值**
- date 从 `transaction_ids[0]` 的 Transaction Log 记录中获取
- 如果一次干预影响多笔跨月交易（如审核 Agent 批量修正了 6 月和 7 月的同 rule 交易）
- 取 transaction_ids[0] 的 date 是否能正确反映干预时间？干预发生的时间不应该是 audit timestamp 而非交易日期？

**Section A 排查同 rule 其他交易的范围**
- §5.2 路径 A Step 3：调用 query_transaction_log.py 用 rule_id 查询"当期所有被该 rule 匹配的交易"
- "当期"是指当前这个 period（如 2024-07）还是历史全部？
- 如果 rule 已使用了 12 个月，accountant 是否需要看到所有历史交易？spec 未明确

---

## 第四步：输出结果

```
## Review Agent — 分析结果

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
