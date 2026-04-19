# Node 3 — AI Classifier (置信度分类器) — Dry Run 测试 Prompt

## 你的角色

你是 Node 3（置信度分类器）的 spec 审查员。你的任务是用真实交易数据测试 AI 分类逻辑和置信度判断的完整性，发现 bug、设计缺陷和歧义。

**你不是在做 bookkeeping，你是在测试 spec 有没有 bug。**

---

## 第一步：加载 Spec

请先读取以下 spec 文件：

1. `/Users/yunpengjiang/Desktop/AB project/ai bookkeeper 8 nodes/confidence_classifier_spec.md`
2. `/Users/yunpengjiang/Desktop/AB project/ai bookkeeper 8 nodes/observations_spec_v2.md`

读取后，结合下方的功能逻辑要点进行分析。

---

## 第二步：功能逻辑要点（必须逐项验证）

### 2.1 Node 3 的核心架构

置信度分类器不是 Agent，是 **代码驱动的分类流程**。LLM 在其中作为判断工具被调用：

```
代码做信息组装 → LLM 做判断（一次调用）→ 代码做路由
```

- LLM 不做信息获取决策、不调用工具、不做多步推理
- 置信度只有两种：**高置信度** 和 **PENDING**（无中/低区分）

### 2.2 信息组装：稳定层（Spec 第 2 节 + 第 3 节阶段一）

每个客户加载一次，通过 prompt caching 复用的 system prompt 内容：

- [ ] **分类指令（SKILL.md）**：置信度判断标准、优先级规则、输出格式、行为规则
- [ ] **tax_reference.md**：HST exempt/zero-rated 类别、ITC 限制规则、省级税率表
- [ ] **Profile.md 全量**：industry, business_type, owner_uses_company_account, has_employees, has_hst_registration, province, loans, bank_accounts
- [ ] **COA.csv 全量**：AI 输出的科目必须存在于此表中（验证约束）
- [ ] **HST 税率**：由 profile.province 代码计算后硬编码进 prompt（如 Ontario = 13%）
- [ ] **行业规则文件**：`knowledge_base/industry/{industry}.md`，按 profile.industry 条件加载，不存在则跳过

**测试重点**：稳定层的各信息源是否齐全？token 预算（4,500-13,000）是否合理？

### 2.3 信息组装：交易层（每笔交易独立，Spec 第 3 节阶段二）

- [ ] **交易数据**：date, description, amount, direction, raw_description, account, currency — 始终提供
- [ ] **supplementary_context**：Coordinator 拆分交易后子交易重走 workflow 时的额外说明 — 非空时提供
- [ ] **cheque_info**：cheque_number, payee, memo, match_method — 非 null 时提供
- [ ] **receipt**：vendor_name, items[], tax_amount, match_confidence — 非 null 时提供
- [ ] **Observation 查询**：代码用 `transaction.description + transaction.direction` 精确匹配 observations 中的 `(pattern, direction)`
  - 命中 → 提取 classification_history, force_review, accountant_notes, non_promotable
  - 未命中 → 加载 `knowledge_base/vendors/common_vendors.md`

**测试重点**：observation 查询用的是标准化后的 description（canonical pattern），对不对？与 observations 中的 pattern 字段如何对应？

### 2.4 信息源优先级（Spec 第 2 节，关键验证点）

当不同信息源给出矛盾信号时，LLM 按以下优先级处理（高覆盖低）：

1. **force_review 标记**（最高）→ 直接 PENDING，跳过判断
2. **supplementary_context** → Coordinator 注入的拆分交易上下文
3. **accountant_notes** → accountant 对该 pattern 的历史判断理由
4. **classification_history** → 该 pattern 过去的分类事实
5. **cheque_info** → 支票的 payee 和 memo（对 CHQ# 交易是强分类信号）
6. **receipt 信息** → 小票中的商品明细和税额
7. **Profile 约束** → 可降低置信度但不能单独决定分类
8. **Knowledge base** → 通用知识
9. **AI 自身推理** → 兜底

- [ ] 优先级顺序是否清晰无歧义？
- [ ] Profile 约束"可降低置信度但不能单独决定分类"——具体什么情况下降低？降到什么程度？
- [ ] cheque_info 排在第 5 位但描述为"强分类信号"——如何与更高优先级的 classification_history 协调？

### 2.5 硬性约束检查（阶段三，LLM 调用的第一步）

- [ ] **检查 1: force_review == true** → 直接 PENDING，不做分类，传 classification_history + accountant_notes 给下游
- [ ] **检查 2: supplementary_context 非空** → 直接采纳做判断，通常输出高置信度
- [ ] **检查 3: 结构性矛盾**
  - has_employees = false 但交易疑似 payroll → 直接 PENDING，标记异常
  - has_hst_registration = false → 所有 HST 强制 exempt（硬性覆盖，不影响置信度）

**测试重点**：这三个检查是否按顺序执行？如果 force_review = true 且 supplementary_context 非空，哪个优先？

### 2.6 分类判断（阶段四，四个步骤）

**步骤 A：识别 vendor / 交易性质**
- [ ] 信息源使用顺序：receipt > observation > common_vendors > AI 知识 > 联网搜索 > 放弃
- [ ] 联网搜索是最后手段，不是默认动作
- [ ] 搜索后仍无法识别 → PENDING

**步骤 B：确定科目（COA 映射）**
- [ ] 科目必须存在于 coa.csv 中（硬性验证）
- [ ] receipt.items[] 消除歧义（HOME DEPOT 买水泥 → Supplies & Materials；买洗碗机 → Shareholder Loan）
- [ ] observation.classification_history 只有一种分类 → 强参考
- [ ] observation.classification_history 有多种分类 → 记录歧义
- [ ] observation.accountant_notes 存在 → 遵循 accountant 的判断理由

**步骤 C：确定 HST 处理方式**
- [ ] has_hst_registration = false → exempt（阶段三已设定）
- [ ] 零售/多品类 vendor 无小票 → hst = unknown
- [ ] 零售/多品类 vendor 有小票 → 根据 receipt.tax_amount 推算
- [ ] 单一品类 vendor → 标准 HST 处理
- [ ] LLM 只判断方式（inclusive/exempt/unknown），金额拆分由 build_je_lines.py 完成
- [ ] AI 用自身常识判断 vendor 是否多品类零售商，不维护固定名单

**步骤 D：确定置信度**

高置信度条件（全部满足）：
- [ ] Vendor 身份清晰
- [ ] COA 中只有一个合理科目选项
- [ ] 如有 observation：classification_history 只有一种分类且与 AI 判断一致
- [ ] owner_uses_company_account = false，或 vendor 不属于零售类
- [ ] HST 处理方式可确定（不是 unknown）

**测试重点**：
1. HST = unknown 的交易一定是 PENDING 吗？（步骤 D 的第 5 个条件）
2. 如果 observation 有 2 种分类历史但占比悬殊（如 10:1），AI 能否仍判定高置信度？
3. owner_uses_company_account = true 时，所有零售类 vendor 都不能高置信度？这会导致稳态客户大量 PENDING

### 2.7 输出格式（Spec 第 4 节）

**高置信度输出：**
```yaml
{
    "confidence": "high",
    "account": "Telephone & Internet",
    "hst": "inclusive_13",
    "ai_reasoning": "...",
    "notes": ""
}
```
- [ ] ai_reasoning 写入 Transaction Log 供追溯
- [ ] notes 用于权责发生制提醒，不改变 JE

**PENDING 输出（统一格式，按信息量分两类）：**
```yaml
{
    "confidence": "pending",
    "options": [],                   # 带选项时 2-3 个选项，不带时 []
    "observation_context": "",       # observation 查询结果摘要
    "accountant_notes": "",          # observation 中的 accountant_notes
    "description_analysis": "",      # 不带选项时的分析
    "suggested_questions": []        # 不带选项时的建议提问
}
```
- [ ] 带选项 vs 不带选项的区分标准是否清晰？
- [ ] options 中每个选项包含 account + hst + reason
- [ ] observation_context 和 accountant_notes 是从 observation 查询结果直接传递的
- [ ] **PENDING 输出是否包含 AI 对交易的分析**？带选项时 description_analysis 为空，AI 的分析在 options[].reason 中；不带选项时在 description_analysis 中

### 2.8 特殊处理场景

- [ ] **疑似未配置的内部转账**：description 含 TFR/TRANSFER 但 Node 1 未匹配 → PENDING，建议补充 profile.account_relationships
- [ ] **联网搜索**：先用已有信息判断，完全无法识别才联网搜索，搜索后仍不行 → PENDING
- [ ] **权责发生制提醒**：年度保费/大额预付 → notes 字段标注，不影响 JE 和置信度

### 2.9 高置信度后的下游处理（Spec 第 3 节阶段五）

- [ ] 调用 `build_je_lines.py` → `validate_je` → JE 生成
- [ ] 写入 Observations：更新 classification_history, count, months_seen；confirmed_by 标记为 `ai`
- [ ] 写入 Transaction Log：classified_by = "ai_high_confidence"，ai_reasoning 来自输出
- [ ] 归入 Output Report Section B（PROBABLE）

### 2.10 Observation 写入逻辑（observations_spec 第 3 节）

- [ ] 写入条件：交易已有明确分类结果 + 不是由 Rules 匹配产生
- [ ] 按 (pattern, direction) 聚合
- [ ] 新 pattern → 创建新记录
- [ ] 已有 pattern → 更新 count(+1), months_seen, amount_range, confirmed_by, classification_history
- [ ] classification_history 新增第二种分类 → 自动标记 non_promotable: true
- [ ] **例外不写入 observation**：accountant 判定为"这笔是例外"时不污染 classification_history

**测试重点**：
1. 高置信度分类与 observation 中已有分类不一致时怎么办？（classification_history 会多一种分类 → non_promotable 被触发）
2. 新客户（空 observations）场景下所有交易都没有 observation 参考，AI 如何保证判断质量？

---

## 第三步：执行测试

**从 Node 2 传递的未匹配交易：**

{{transactions}}

**客户上下文（Profile + COA + Observations）：**

{{client_context}}

请逐笔交易按上述逻辑走查。对每笔交易：

1. 执行 observation 查询（用 description + direction 匹配）
2. 执行硬性约束检查（三个检查项）
3. 执行四步分类判断（识别 vendor → 确定科目 → 确定 HST → 确定置信度）
4. 输出分类结果（高置信度格式 / PENDING 格式）
5. 高置信度：模拟 JE 调用和 observation 写入
6. PENDING：记录传递给 Coordinator 的数据

**重点关注：**
- 信息源优先级是否在实际交易中产生矛盾
- 高置信度的 5 个条件是否过严或过松
- PENDING 输出的信息量是否足够 Coordinator 工作
- HST unknown 的处理路径是否完整
- cheque_info 对分类的实际影响（CHQ 交易如何被分类？）

---

## 第四步：输出结果

请严格按照以下格式输出：

```
## Node 3 — AI Classifier — 分析结果

### 1. 处理结果
[高置信度交易列表，含分类结果、JE 模拟、observation 写入]

### 2. 传递给下一节点
[PENDING 交易列表，含 PENDING 输出的完整内容，供 Coordinator 使用]

### 3. 发现的 Bug
[使用 N3-xxx 编号]

### 4. 接口问题
[从 Node 2 接收的数据中发现的问题]

### 5. Spec 歧义
[Confidence Classifier spec 中描述模糊的地方]

### 6. 备注
[其他观察]
```
