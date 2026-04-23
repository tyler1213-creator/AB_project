# 置信度分类器（Node 3 / AI 判断层）

---

## 1. 职责定义

对 Node 1（Profile 匹配）和 Node 2（Rules 匹配）均未命中的交易，进行语义理解和分类判断。置信度分类器综合交易数据、客户上下文、历史分类记录和会计知识，输出分类结果和置信度，将交易路由到对应的处理路径。

**置信度分类器不是 Agent。** 它是一个代码驱动的分类流程，LLM 在其中作为判断工具被调用。代码负责：

- 预查询 observations
- 提取 deterministic features
- 选择应加载的 domain packs / risk packs
- 计算 evidence overrides
- 决定是否 short-circuit 到 PENDING
- 在高置信度时写入 Observations 和 Transaction Log

LLM 只负责在给定上下文中做一次分类判断。LLM 不做信息获取决策、不调用工具、不做多步推理。

### 1.1 术语 / 字段解释

上面这几个词都不是“玄学步骤”，本质上是在 LLM 调用前，代码先整理好的几类结构化输入。

| 名称 | 它是什么 | 里面通常包含什么 | 它的作用 |
| --- | --- | --- | --- |
| `deterministic features` | 代码能直接算出来、不需要 AI 猜的事实 | 例如：`pattern_source` 是否为 `fallback`、是否命中 observation、`force_review` 是否为 true、description 里是否有 TFR/TRANSFER、交易是否 payroll-like、是否有 receipt / cheque_info、profile 里的 `owner_uses_company_account` / `has_employees` 等布尔条件 | 先把“已经确定的信号”整理出来，供后面激活 risk pack / 判断 short-circuit |
| `domain packs` | 按需加载的业务参考知识包 | 例如：`tax_reference`、`industry/{industry}`、`vendors/common_vendors` | 帮 LLM 理解行业语义、vendor 常识、税务背景，但它们本身不直接决定 blocking |
| `risk packs` | 低频但重要的风险规则包 | 例如：`force_review_gate`、`retail_personal_use_risk`、`payroll_profile_conflict`、`suspected_internal_transfer`、`fallback_pattern_caution` | 告诉系统“这笔交易为什么不能轻易高置信度自动落地” |
| `override evidence` | 能覆盖 soft risk 的强证据 | 例如：`supplementary_context_confirmed_purpose`、`receipt_business_use`、`receipt_tax_support`、`cheque_named_payee_memo`、`stable_single_observation` | 当某个 soft risk 已触发时，判断是否仍允许恢复为高置信度 |
| `policy_trace` | Node 3 最终产出的结构化审计轨迹 | `activated_packs`、`blocking_packs`、`override_evidence`、`unresolved_risks` | 让下游知道：这笔交易为什么被放行，或者为什么被卡成 PENDING |

可以把它们理解成一条顺序链：

`deterministic features`
→ 决定激活哪些 `risk packs`
→ 检查是否存在可用的 `override evidence`
→ 汇总成 `policy_trace`
→ 再决定这笔交易是 `high` 还是 `pending`

这里最容易混淆的一点是：

- `domain packs` 是“帮助理解业务”的参考知识
- `risk packs` 是“限制是否能自动落地”的风险规则
- `override evidence` 是“在有 soft risk 的前提下，允许恢复高置信度”的强证据

三者职责不同，不要混成一类。

**置信度只有两种：高置信度和非高置信度（PENDING）。** 不做中/低置信度的形式化区分。PENDING 交易根据输出内容自然分为：

- **带选项**：AI 能识别 vendor，但存在 2-3 个合理分类
- **不带选项**：AI 无法稳定识别 vendor 或业务目的

这个区分在下游 Coordinator Agent 的呈现层处理，不在分类层单独定义新的状态。

---

## 2. 上下文与 Prompt 组装

### 2.1 上游数据

来自 Node 2（Rules 匹配）未命中的交易队列。代码在 Node 1 和 Node 2 批量跑完后，将所有未匹配的交易收集到待处理队列，统一交给置信度分类器处理。

### 2.2 四层框架

Node 3 的 progressive disclosure 设计分为四层：

| 层级 | 名称 | 作用 | 加载方式 |
| --- | --- | --- | --- |
| Layer 1 | Core Skill | 最小必要行为规则：输出格式、信息源优先级、高置信度基础定义、行为边界 | 永远加载 |
| Layer 2 | Domain Packs | 行业/税务/vendor 参考知识，帮助识别业务语义 | 按客户/行业/交易条件加载 |
| Layer 3 | Risk / Exception Packs | 低频但重要的风险规则、例外处理、置信度修正规则 | 仅当 deterministic predicate 命中时加载 |
| Layer 4 | Evidence Overrides | 不是知识包，而是可覆盖 soft risk 的结构化强证据 | 代码提取并随交易提供 |

四层框架描述的是**什么类型的知识会被挂载**；真正发送给 LLM 时，仍按稳定层 / 交易层组装。

### 2.3 稳定层

每个客户加载一次，通过 prompt caching 复用。

| 信息源 | 内容 | 加载方式 |
| --- | --- | --- |
| Core Skill | 输出格式、信息源优先级、高置信度基础定义、行为边界 | 始终加载，system prompt 核心部分 |
| `tax_reference` | 加拿大税务事实性参考 | 始终加载 |
| profile 基础上下文 | `industry`, `business_type`, `province`, `has_hst_registration`, `tax_config`, `loans`, `bank_accounts` | 始终加载 |
| `COA.csv` | 完整科目表 | 始终加载 |
| HST 税率 | 由 `profile.tax_config` / `province` 推算 | 代码计算后硬编码进 prompt |
| `industry/{industry}` | 行业规则文件 | 按 `profile.industry` 条件加载，文件不存在则跳过 |

### 2.4 交易层

每笔交易独立组装，写入 user message。

| 信息源 | 内容 | 加载方式 |
| --- | --- | --- |
| 交易数据 | `date`, `description`, `amount`, `direction`, `raw_description`, `pattern_source`, `bank_account`, `currency` | 始终提供 |
| `supplementary_context` | Coordinator 在拆分交易后子交易重新走 workflow 时注入的额外说明 | 非空时提供 |
| `cheque_info` | `cheque_number`, `payee`, `memo`, `match_method` | 非 null 时提供 |
| `receipt` | `vendor_name`, `items[]`, `tax_amount`, `match_confidence` | 非 null 时提供 |
| observation 记录 | `classification_history`, `force_review`, `accountant_notes`, `non_promotable`, `count`, `months_seen` | 用 `(pattern, direction)` 精确匹配 observations，命中时提供 |
| `vendors/common_vendors` | 通用 vendor 参考 | 仅 observation 未命中且需要辅助识别时加载 |
| risk pack inputs | 激活了哪些 risk packs、有哪些 override evidence | 代码按需注入 |

### 2.5 基础 profile 上下文

以下字段作为 Node 3 的基础业务背景，由代码从 profile 中提取：

| 字段 | 用途 |
| --- | --- |
| `industry` | 影响业务语义和 COA 选择 |
| `business_type` | 决定个人消费落 Shareholder Loan 还是 Owner's Draw |
| `province` | 决定税制环境 |
| `has_hst_registration` | 决定 HST 是否强制 exempt |
| `tax_config` | 提供税率和税制类型 |
| `loans` | 识别还贷等固定语义 |
| `bank_accounts` | 辅助识别疑似内部转账 |

以下 profile 字段不再作为“常驻自然语言规则”，而是只在相关 risk pack 触发时作为 predicate 输入：

- `owner_uses_company_account`
- `has_employees`

### 2.6 信息源优先级

当不同信息源给出矛盾信号时，按以下顺序处理：

1. **blocking risk packs**
2. **supplementary_context**
3. **accountant_notes**
4. **receipt 信息**
5. **cheque_info**
6. **stable_single_observation**
7. **Domain Packs**
8. **AI 自身推理**

### 2.7 当前批次的 profile snapshot 原则

Node 3 只读取**当前批次开始时已提交的 profile 快照**。

这意味着：

- Coordinator 阶段后来捕获到的 `profile_change_request` 不会回写本批次中的 Node 3 判断
- Review Agent 在审核开始前统一处理 `pending_profile_changes`
- profile 变更主要影响下一批次，而不是当前批次中已跑过的 Node 3 路由

这条规则必须与 deferred `profile_change_request -> Review Agent` 设计保持一致，避免批次中途 profile 漂移。

---

## 3. Risk & Override 系统

### 3.1 Core Skill

Core Skill 永远加载，只保留最小必要原则，不承载低频例外规则。

包含：

- 输出格式
- 信息源优先级
- 高置信度 / PENDING 的基础定义
- 允许与不允许的行为边界
- HST 判断只输出方式，不做金额拆分
- COA 校验约束

**不应放入 Core Skill 的内容：**

- `owner_uses_company_account = true` 时的零售类个人消费风险
- `has_employees = false` 时的 payroll 冲突
- 疑似未配置的内部转账
- fallback pattern 的特殊降置信度逻辑
- `force_review` 的处理规则

这些都属于 Risk / Exception Packs。

### 3.2 Domain Packs

| Pack | 内容 | 加载方式 |
| --- | --- | --- |
| `tax_reference` | 加拿大税务事实性参考（HST exempt/zero-rated 类别、ITC 限制规则、省级税率） | 始终加载 |
| `industry/{industry}` | 某行业的会计语义和常见交易解释 | 按 `profile.industry` 条件加载 |
| `vendors/common_vendors` | 通用 vendor 参考 | 仅 observation 未命中且需要 vendor 辅助识别时加载 |

### 3.3 Evidence Overrides

Evidence Overrides 不是知识 pack，而是代码提取的结构化强证据，用于覆盖 soft risk packs。

| Evidence ID | 来源 | 用途 |
| --- | --- | --- |
| `supplementary_context_confirmed_purpose` | `transaction.supplementary_context` | accountant 已明确提供业务用途，强覆盖证据 |
| `receipt_business_use` | `receipt.items[]` / `receipt.vendor_name` | 小票明确指向业务用途 |
| `receipt_tax_support` | `receipt.tax_amount` | 支持 HST 方式判断 |
| `cheque_named_payee_memo` | `cheque_info.payee` + `cheque_info.memo` | 支票对象和用途明确 |
| `stable_single_observation` | `classification_history` + `months_seen` + `accountant_notes` | 历史长期单一且无混用警告 |

关键原则：

- override 只能覆盖 `soft_risk` packs，不能覆盖 `blocking` packs
- 同一笔交易是否允许高置信度，不再由某个 profile 字段直接决定，而由：
  - 激活了哪些 risk packs
  - 是否存在可接受的 override evidence
共同决定

#### `stable_single_observation` 的成立条件

只有满足以下全部条件时，observation 才能被视为 override evidence，而不只是普通历史参考：

- 命中 observation
- `force_review = false`
- `non_promotable = false`
- `classification_history` 只有一种分类
- `count >= 3`
- `months_seen` 跨至少 2 个月
- `accountant_notes` 没有显式写明 mixed-use / always ask / 特殊情况

observation 查询与命中 / 未命中的底层 contract 以 [observations_spec_v2.md](/Users/yunpengjiang/Desktop/AB%20project/ai%20bookkeeper%208%20nodes/observations_spec_v2.md:125) 为准；本文件只定义 Node 3 如何消费这些结果。

### 3.4 `policy_trace`

代码根据 deterministic predicates 生成以下结构：

```yaml
policy_trace:
  activated_packs: []
  blocking_packs: []
  override_evidence: []
  unresolved_risks: []
```

`policy_trace` 是 Node 3 的标准结构化输出，并正式进入两个下游 contract：

- PENDING handoff 给 Coordinator Agent
- `classified_by = ai_high_confidence` 时写入 Transaction Log

`policy_trace` **不进入** `report_draft` / 最终 `.xlsx` 的可见列。审核视图保持 review-facing；需要追查 risk pack / override 细节时，由 Review Agent 按 `transaction_id` 读取 Transaction Log。

### 3.5 Pack 激活规则

#### `force_review_gate`

- **Predicate**：observation 命中且 `force_review = true`
- **类型**：blocking
- **默认行为**：直接 short-circuit 为 PENDING
- **可否 override**：不可
- **下游含义**：Coordinator 应直接问 accountant，不做自动分类

#### `retail_personal_use_risk`

- **Predicate**：vendor 被识别为零售/多品类，且 `profile.owner_uses_company_account = true`
- **类型**：soft_risk
- **默认行为**：默认不应高置信度
- **可接受 override**：
  - `supplementary_context_confirmed_purpose`
  - `receipt_business_use`
  - `stable_single_observation`
- **设计含义**：`owner_uses_company_account` 不再单独决定置信度，它现在只负责激活这个 risk pack

#### `payroll_profile_conflict`

- **Predicate**：交易 payroll-like，且 `profile.has_employees = false`
- **类型**：blocking
- **默认行为**：直接 PENDING，标记结构性异常
- **可否 override**：不可在当前批次内由 Node 3 override
- **设计意图**：
  - Node 3 不根据未确认的 profile 变更自行改判
  - Coordinator 可以捕获 `profile_change_request`
  - Review Agent 再统一确认并写入 profile

#### `suspected_internal_transfer`

- **Predicate**：description 含有 TFR / TRANSFER 等强转账信号，且 Node 1 未命中
- **类型**：blocking
- **默认行为**：直接 PENDING，提示可能是 profile 中漏配的内部转账
- **可否 override**：不可
- **设计意图**：内部转账的确定性归属应回到 Node 1 / `profile.account_relationships`，不应由 Node 3 直接吞下

#### `fallback_pattern_caution`

- **Predicate**：`pattern_source = fallback`
- **类型**：soft_risk
- **默认行为**：默认降置信度，因为 canonical pattern 不稳定
- **可接受 override**：
  - `supplementary_context_confirmed_purpose`
  - `receipt_business_use`
  - `cheque_named_payee_memo`
- **额外约束**：即使最终高置信度，也**不得写入 observations**

fallback pattern 的基本 contract 以 [pattern_standardization_spec.md](/Users/yunpengjiang/Desktop/AB%20project/tools/pattern_standardization_spec.md:170) 为准；本文件只补充 Node 3 的 risk / override 行为。

---

## 4. 执行逻辑

### 4.1 整体架构

```text
代码做预查询与 pack activation
→ 判断是否 short-circuit
→ 需要时调用 LLM 做一次分类
→ 代码做路由与写入
```

### 4.2 调用流程（伪代码）

```python
stable_context = build_stable_context(client_id)  # core + base profile + coa + domain packs

for transaction in pending_queue:
    observation = query_observation(transaction.description, transaction.direction, client_id)
    domain_packs = select_domain_packs(transaction, observation, stable_context)
    evidence_flags = derive_evidence_flags(transaction, observation)
    risk_packs = activate_risk_packs(transaction, observation, stable_context.profile_flags, evidence_flags)
    policy_trace = build_policy_trace(risk_packs, evidence_flags)

    if has_blocking_short_circuit(risk_packs):
        result = build_pending_from_policy_trace(transaction, observation, policy_trace)
    else:
        user_message = assemble_transaction_payload(
            transaction=transaction,
            observation=observation,
            domain_packs=domain_packs,
            risk_packs=risk_packs,
            evidence_flags=evidence_flags,
        )
        result = llm_call(system=stable_context.system_prompt, user=user_message)

    if result.confidence == "high":
        je_input = build_je_lines(transaction, result, client_id)
        je_result = validate_je(je_input)

        if transaction.pattern_source != "fallback":
            write_observation(result)

        write_transaction_log(
            transaction=transaction,
            je_lines=je_result.je_lines,
            classified_by="ai_high_confidence",
            ai_reasoning=result.ai_reasoning,
        )
    else:
        mark_pending(transaction, result)
```

#### 4.2.1 伪代码变量解释

上面的变量名比较像实现草图，下面把它们翻成人话：

| 变量 | 代表什么 | 里面通常有什么 |
| --- | --- | --- |
| `stable_context` | 对同一客户整批交易都共用的稳定上下文 | Core Skill、基础 profile、COA、税务参考、行业 pack |
| `observation` | 当前 `(pattern, direction)` 命中的 observation 记录 | `classification_history`、`force_review`、`accountant_notes`、`count`、`months_seen`、`non_promotable` |
| `domain_packs` | 这笔交易实际需要加载的参考知识包 | 例如 `industry/construction`、`vendors/common_vendors` |
| `evidence_flags` | 这笔交易目前具备哪些强证据 | 例如是否有 `receipt_business_use`、`cheque_named_payee_memo`、`stable_single_observation` |
| `risk_packs` | 这笔交易被激活了哪些风险规则 | 例如 `retail_personal_use_risk`、`payroll_profile_conflict` |
| `policy_trace` | 把 risk / override 结果整理成标准输出 | `activated_packs`、`blocking_packs`、`override_evidence`、`unresolved_risks` |
| `result` | Node 3 对这笔交易的最终输出 | 如果 `high`：`account`、`hst`、`ai_reasoning`、`policy_trace`；如果 `pending`：`options`、`suggested_questions`、`description_analysis`、`policy_trace` |

换句话说：

- `observation` 是“历史上这个 pattern 发生过什么”
- `domain_packs` 是“为了理解这笔交易，额外给 AI 的参考资料”
- `risk_packs` 是“代码判断出来的风险标签”
- `evidence_flags` 是“代码判断出来的放行证据”
- `policy_trace` 是“最后把风险和证据汇总给下游看的摘要”

### 4.3 short-circuit 规则（代码）

若激活了以下 blocking packs，代码可直接跳过 LLM 调用并输出 PENDING：

- `force_review_gate`
- `payroll_profile_conflict`
- `suspected_internal_transfer`

这三类场景的核心问题不是“AI 还需要再猜一猜”，而是系统已经知道现在不应自动落地。

### 4.4 LLM 判断步骤

当没有触发 blocking short-circuit 时，LLM 仍按原 spec 的 A / B / C / D 逻辑判断，只是前面多了一层 activation / override 控制。

#### 步骤 A：识别 vendor / 交易性质

```text
读取 transaction.description + transaction.raw_description

如果有 receipt → 读取 receipt.vendor_name + receipt.items[]（最强信号）
如果有 cheque_info → 读取 payee + memo
如果有 observation → 读取 classification_history 作为历史参考
如果无 observation → 参考 common_vendors（如果已加载）
最后手段 → AI 自身知识判断，完全无法识别时联网搜索
联网搜索后仍无法识别 → 放弃识别，输出 PENDING
```

#### 步骤 B：确定科目（COA 映射）

```text
根据 vendor 身份 + profile.industry + profile.business_type 从 coa.csv 中选择科目

如果有 receipt.items[] → 用商品明细消除歧义
  （如 HOME DEPOT 买水泥 → Supplies & Materials；买洗碗机 → Shareholder Loan）

如果 observation.classification_history 只有一种分类 → 强参考该结果
如果 observation.classification_history 有多种分类 → 记录歧义
如果 observation.accountant_notes 存在 → 遵循 accountant 的判断理由

验证选择的科目是否存在于 coa.csv 中
```

#### 步骤 C：确定 HST 处理方式

```text
如果 profile.has_hst_registration = false → exempt
如果 vendor 是零售/多品类 且无小票 → hst = unknown
如果 vendor 是零售/多品类 且有小票 → 根据 receipt.tax_amount 推算
如果 vendor 是单一品类（如电力、电信）→ 标准 HST 处理

LLM 只判断 HST 处理方式（inclusive / exempt / unknown），金额拆分由下游 build_je_lines.py 完成。
```

#### 步骤 D：确定置信度

```text
先检查是否存在 unresolved blocking pack
再检查所有 soft risk pack 是否已被兼容的 override evidence 覆盖
以上都通过后，才允许输出 high
否则输出 pending
```

### 4.5 高置信度代码路由

```text
→ 调用 build_je_lines.py
→ 调用 validate_je
→ 若 pattern_source != fallback：
     写入 observations（confirmed_by = ai）
→ 若 pattern_source = fallback：
     跳过 observations
→ 写入 Transaction Log：
     classified_by = ai_high_confidence
     ai_reasoning = 本次输出
     policy_trace = 本次输出
→ `policy_trace` 进入 Transaction Log 的审计层，
   但不要求 report_draft / 最终报告显示该字段
```

### 4.6 PENDING 代码路由

```text
→ 不写 observations
→ 不写 Transaction Log
→ 将 classifier_output（含 `policy_trace`）保留给下游 Coordinator
```

---

## 5. 高置信度判断规则

高置信度必须同时满足：

- Vendor 身份清晰
- COA 中只有一个合理科目
- HST 处理方式可确定（不是 `unknown`）
- 没有激活任何 unresolved blocking pack
- 所有激活的 soft risk packs 都已被兼容的 override evidence 覆盖

这意味着：

- `owner_uses_company_account` 不再单独决定置信度
- 触发 `retail_personal_use_risk` 后默认降置信度
- 只有存在兼容 override evidence 时，才允许恢复高置信度

这就是 T03 / T12 这类场景可以进入 Section B，而不会因一个 profile 字段被硬挡回 PENDING 的原因。

---

## 6. 输出格式

### 6.1 高置信度输出

```yaml
{
  "confidence": "high",
  "account": "Supplies & Materials",
  "hst": "inclusive_13",
  "ai_reasoning": "HOME DEPOT 为建材零售商。小票显示 Portland Cement 和 Rebar，均明确为施工材料。虽然客户存在个人消费风险，但本笔触发的 retail_personal_use_risk 已被 receipt_business_use 与 stable_single_observation 覆盖，因此可高置信度分类为 Supplies & Materials。",
  "notes": "",
  "policy_trace": {
    "activated_packs": ["retail_personal_use_risk"],
    "blocking_packs": [],
    "override_evidence": ["receipt_business_use", "stable_single_observation"],
    "unresolved_risks": []
  }
}
```

- `ai_reasoning`：写入 Transaction Log，供 accountant 追溯
- `notes`：用于 accrual 等提醒，不改变 JE
- `policy_trace`：记录触发了哪些 policy packs，以及哪些 override evidence 使其最终仍可高置信度。该字段在高置信度路径写入 Transaction Log，供 Review Agent / dry run 审计追查；不进入 report_draft 的可见列

`ai_reasoning` 的写法仍保持原 spec 的要求：内容需让不同水平的 accountant 都能看懂，包括：

- 识别到的 vendor 类型
- 参考了哪些历史数据
- 小票 / 支票 / supplementary_context 如何支持判断
- HST 处理依据
- 如触发了 risk pack，说明为何被 override 或为何仍 unresolved

### 6.2 PENDING 输出

PENDING 输出统一保留以下结构：

```yaml
{
  "confidence": "pending",
  "options": [],
  "observation_context": "",
  "accountant_notes": "",
  "description_analysis": "",
  "suggested_questions": [],
  "policy_trace": {
    "activated_packs": [],
    "blocking_packs": [],
    "override_evidence": [],
    "unresolved_risks": []
  }
}
```

#### 带选项示例

```yaml
{
  "confidence": "pending",
  "options": [
    {
      "account": "Office Supplies",
      "hst": "inclusive_13",
      "reason": "Dollarama 常见办公用品采购"
    },
    {
      "account": "Shareholder Loan",
      "hst": "exempt",
      "reason": "存在个人消费风险"
    }
  ],
  "observation_context": "历史上 5 次均为 Office Supplies",
  "accountant_notes": "",
  "description_analysis": "",
  "suggested_questions": [],
  "policy_trace": {
    "activated_packs": ["retail_personal_use_risk"],
    "blocking_packs": [],
    "override_evidence": [],
    "unresolved_risks": ["retail_personal_use_risk"]
  }
}
```

#### 不带选项示例

```yaml
{
  "confidence": "pending",
  "options": [],
  "observation_context": "",
  "accountant_notes": "",
  "description_analysis": "交易描述显示 payroll-like，但当前已提交 profile 中 has_employees = false，存在结构性冲突。",
  "suggested_questions": [
    "这笔款项是否为工资？如果是，客户是否已开始雇员并需要更新 profile？"
  ],
  "policy_trace": {
    "activated_packs": ["payroll_profile_conflict"],
    "blocking_packs": ["payroll_profile_conflict"],
    "override_evidence": [],
    "unresolved_risks": ["payroll_profile_conflict"]
  }
}
```

---

## 7. 特殊场景

### 7.1 receipt 处理

- `receipt.items[]` 是最强的业务用途证据之一
- `receipt.tax_amount` 支持 HST 方式判断
- `receipt_business_use` 可覆盖 `retail_personal_use_risk`
- 若 `pattern_source = fallback`，receipt 也可作为允许高置信度的直接证据，但仍不写 observations

### 7.2 cheque_info 处理

- `cheque_info.payee` + `memo` 是支票交易的重要直接证据
- 可作为 `fallback_pattern_caution` 的 override evidence
- 但若 cheque canonicalization 仍坍缩为 `CHQ`，学习路径问题仍属于 `BUG-001`

### 7.3 mixed HST vendor

对于零售类/多品类 vendor（Costco、Walmart、Amazon、药房、餐饮等）：

- 无 receipt → 通常 `hst = unknown`
- 有 receipt → 用 `receipt.tax_amount` 支持判断
- AI 仍然用自身常识判断 vendor 是否为多品类零售商，不维护固定名单

### 7.4 payroll-like 但当前 profile 无员工

- Node 3 直接走 `payroll_profile_conflict`
- 不因未确认的 profile 变更而在当前批次自动改判
- 当前交易由 Coordinator 与 accountant 完成分类
- profile 更新由 Review Agent 统一处理

### 7.5 疑似未配置内部转账

- Node 3 不自行把它归为普通费用
- 路由为 `suspected_internal_transfer`
- Coordinator 可提示 accountant 补充 `profile.account_relationships`

### 7.6 fallback pattern

- fallback pattern 不参与 observations 学习路径
- 即使最终高置信度，也不写 observations
- 只有 direct evidence 足够强时才允许高置信度

### 7.7 联网搜索

- AI 先用已有上下文判断
- 完全无法识别 vendor 时才触发联网搜索
- 搜索后仍无法识别 → PENDING
- 联网搜索不能覆盖 blocking packs

### 7.8 accrual 提醒

AI 在处理交易时如果发现可能涉及 accrual 的交易（如年度保费、大额预付）：

- 在输出的 `notes` 字段中标注提醒
- 不改变 JE 本身（仍然是现金制）
- 标注不影响置信度判断

---

## 8. Reference 与实现说明

### 8.1 Domain reference 的角色

#### `tax_reference`

包含：

- HST exempt 类别
- zero-rated 类别
- exempt / zero-rated 对 ITC 的影响
- ITC 限制规则
- 各省税率

原则：

- 这是事实性参考，不是行为指令
- 税法变更时由人工更新
- 不随系统运行自动增长
- 预估体量约 `500 - 1,500 tokens`

#### `industry/{industry}`

包含某一行业的常见业务语义和易错点。仅在该行业客户上加载。

原则：

- 行业 pack 不预先无限扩张
- 运行中如果发现 AI 对某行业反复犯错，再逐步沉淀
- 单个文件不建议超过 `2,000 tokens`

#### `vendors/common_vendors`

用于冷启动和 observation 未命中场景，不替代 observation。

### 8.2 Profile 与 COA 的保留原则

- Profile 仍提供完整客户业务背景
- COA 仍全量提供，AI 选择的科目必须存在于表中
- `has_hst_registration = false` 时所有 HST 强制 exempt

### 8.3 推荐目录结构

```text
confidence_classifier/
  core/
    skill.md
  domain/
    tax_reference.md
    industry/
      construction.md
    vendors/
      common_vendors.md
  risk/
    force_review_gate.md
    retail_personal_use_risk.md
    payroll_profile_conflict.md
    suspected_internal_transfer.md
    fallback_pattern_caution.md
```

### 8.4 Prompt 结构

```text
┌─────────────────────────────────────────────────┐
│ System Prompt（稳定层，prompt caching 复用）     │
│                                                 │
│  - Core Skill                                   │
│  - tax_reference                                │
│  - profile 基础上下文                           │
│  - COA.csv                                      │
│  - HST 税率 / tax_config                        │
│  - industry pack（如有）                        │
│                                                 │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ User Message（交易层，每笔交易独立）             │
│                                                 │
│  - 当前交易数据                                  │
│  - supplementary_context（如有）                  │
│  - cheque_info（如有）                            │
│  - receipt 信息（如有）                           │
│  - observation 查询结果（如有）                   │
│  - activated risk packs                           │
│  - override evidence                              │
│  - common_vendors（需要时）                       │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 8.5 上下文体量估算

| 内容 | 估算 token 量 |
| --- | --- |
| Core Skill | 1,000 - 2,000 |
| `tax_reference` | 500 - 1,500 |
| profile 基础上下文 | 500 - 3,000 |
| `COA.csv` | 2,000 - 5,000 |
| 行业 pack（如有） | 500 - 1,500 |
| risk packs（按需） | 100 - 500 |
| 交易层（含 observation / receipt / cheque） | 200 - 900 |
| **总输入** | **约 5,000 - 14,000+** |

当前设计的目标不是无限压缩 token，而是把低频风险规则从 always-on prompt 中剥离出来。

### 8.6 dry run 可观察性

未来 synthetic rerun 时，应把 `policy_trace` 作为 Node 3 的可观察输出之一，用于验证：

- 哪些 case 激活了哪些 risk packs
- 哪些 case 是被 override 后进入高置信度
- 哪些 case 因 blocking pack 正确停在 PENDING

---

## 9. 与其他组件的关系

### 上游

| 组件 | 关系 |
| --- | --- |
| Node 2（Rules 匹配） | 将未命中规则的交易传给 Node 3 |
| Profile.md | 提供基础业务上下文和 risk predicate 所需字段 |
| Observations.md | 提供历史分类、force_review、accountant_notes |
| COA.csv | 提供可选科目全集 |

### 下游

| 输出 | 去向 | 说明 |
| --- | --- | --- |
| 高置信度分类 | build_je_lines.py + validate_je | 构造并校验 JE |
| 高置信度分类 | Observations | 非 fallback pattern 写入 observations |
| 高置信度分类 | Transaction Log | 写入 `ai_reasoning` 和 `policy_trace` |
| PENDING | Coordinator Agent | 接收 Node 3 的 pending 结果和 `policy_trace` |

### 与 deferred profile change 的关系

| 组件 | 关系 |
| --- | --- |
| Coordinator Agent | 负责记录 `profile_change_request`，不反写当前批次 Node 3 |
| Review Agent | 在审核开始前处理 `pending_profile_changes`，影响下一批次的 Node 3 上下文 |
