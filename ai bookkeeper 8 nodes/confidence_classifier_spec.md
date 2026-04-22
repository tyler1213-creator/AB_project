# 置信度分类器（Node 3）

---

## 1. 职责定义

对 Node 1（Profile 匹配）和 Node 2（Rules 匹配）均未命中的交易，进行语义理解和分类判断。置信度分类器综合交易数据、客户上下文、历史分类记录和会计知识，输出分类结果和置信度，将交易路由到对应的处理路径。

**置信度分类器不是 Agent。** 它是一个代码驱动的分类流程，LLM 在其中作为判断工具被调用。代码负责：

- 预查询 observations
- 提取 deterministic features
- 选择应加载的 domain packs / risk packs
- 计算 evidence overrides
- 决定是否需要 short-circuit 到 PENDING
- 在高置信度时写入 Observations 和 Transaction Log

LLM 只负责在给定上下文中做一次分类判断。LLM 不做信息获取决策、不调用工具、不做多步推理。

**置信度只有两种：高置信度和非高置信度（PENDING）。** 不做中/低置信度的形式化区分。PENDING 交易根据输出内容自然分为"带选项"和"不带选项"，这个区分在下游 Coordinator Agent 的呈现层处理，不在分类层单独定义新的状态。

---

## 2. 输入与四层上下文结构

### 2.1 上游数据

来自 Node 2（Rules 匹配）未命中的交易队列。代码在 Node 1 和 Node 2 批量跑完后，将所有未匹配的交易收集到待处理队列，统一交给置信度分类器处理。

### 2.2 四层上下文结构

Node 3 的 progressive disclosure 设计明确分为四层：

| 层级 | 名称 | 作用 | 加载方式 |
| --- | --- | --- | --- |
| Layer 1 | Core Skill | 最小必要行为规则：输出格式、信息源优先级、高置信度基础定义、行为边界 | 永远加载 |
| Layer 2 | Domain Packs | 行业/税务/vendor 参考知识，帮助识别业务语义 | 按客户/行业/交易条件加载 |
| Layer 3 | Risk / Exception Packs | 低频但重要的风险规则、例外处理、置信度修正规则 | 仅当 deterministic predicate 命中时加载 |
| Layer 4 | Evidence Overrides | 不属于知识包，而是可覆盖 soft risk 的结构化强证据 | 代码提取并随交易提供 |

这四层之外，还有两类**结构化输入**，它们不是 pack：

- **客户基础上下文**：business_type, industry, province, has_hst_registration, tax_config, loans, bank_accounts 等稳定业务背景
- **交易事实包**：date, description, raw_description, amount, direction, bank_account, currency, receipt, cheque_info, supplementary_context 等当前交易信息

### 2.3 Layer 1 — Core Skill

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

这些都属于 Layer 3 的 Risk / Exception Packs。

### 2.4 Layer 2 — Domain Packs

Domain Packs 用来承载客户、行业、税务、vendor 语义知识。

| Pack | 内容 | 加载方式 |
| --- | --- | --- |
| `tax_reference` | 加拿大税务事实性参考（HST exempt/zero-rated 类别、ITC 限制规则、省级税率） | 始终加载 |
| `industry/{industry}` | 某行业的会计语义和常见交易解释 | 按 `profile.industry` 条件加载 |
| `vendors/common_vendors` | 通用 vendor 参考 | 仅 observation 未命中且需要 vendor 辅助识别时加载 |

### 2.5 Layer 3 — Risk / Exception Packs

Risk / Exception Packs 是本次设计新增的统一抽象。

它们的特征是：

- 不是常驻背景知识
- 由代码根据 deterministic predicate 触发
- 每个 pack 都只表达一个明确风险
- 每个 pack 都定义默认行为和可否被 override

首批 pack 如下：

| Pack ID | 类型 | 触发条件摘要 |
| --- | --- | --- |
| `force_review_gate` | blocking | 命中 observation 且 `force_review = true` |
| `retail_personal_use_risk` | soft_risk | 零售/多品类 vendor 且 `owner_uses_company_account = true` |
| `payroll_profile_conflict` | blocking | 交易疑似 payroll 且 `has_employees = false` |
| `suspected_internal_transfer` | blocking | 存在 transfer-like 信号，但 Node 1 未命中 |
| `fallback_pattern_caution` | soft_risk | `pattern_source = fallback` |

### 2.6 Layer 4 — Evidence Overrides

Evidence Overrides 不是知识 pack，而是代码提取的结构化强证据，用于覆盖 Layer 3 中的 soft risk packs。

首批 override 证据如下：

| Evidence ID | 来源 | 用途 |
| --- | --- | --- |
| `supplementary_context_confirmed_purpose` | `transaction.supplementary_context` | accountant 已明确提供业务用途，强覆盖证据 |
| `receipt_business_use` | `receipt.items[]` / `receipt.vendor_name` | 小票明确指向业务用途 |
| `receipt_tax_support` | `receipt.tax_amount` | 支持 HST 方式判断 |
| `cheque_named_payee_memo` | `cheque_info.payee` + `cheque_info.memo` | 支票对象和用途明确 |
| `stable_single_observation` | `classification_history` + `months_seen` + `accountant_notes` | 历史长期单一且无混用警告 |

**关键原则：**

- override 只能覆盖 `soft_risk` pack，不能覆盖 `blocking` pack
- 同一笔交易是否允许高置信度，不再由某个 profile 字段直接决定，而由：
  - 激活了哪些 risk packs
  - 是否存在可接受的 override evidence
 共同决定

### 2.7 当前批次的 profile snapshot 原则

Node 3 只读取**当前批次开始时已提交的 profile 快照**。

这意味着：

- Coordinator 阶段后来捕获到的 `profile_change_request` 不会回写本批次中的 Node 3 判断
- Review Agent 在审核开始前统一处理 `pending_profile_changes`
- profile 变更主要影响下一批次，而不是当前批次中已跑过的 Node 3 路由

这条规则必须与 deferred `profile_change_request -> Review Agent` 设计保持一致，避免批次中途 profile 漂移。

---

## 3. 结构化输入

### 3.1 客户基础上下文

以下字段作为 Node 3 的基础业务背景，由代码从 profile 中提取：

| 字段 | 用途 | 加载方式 |
| --- | --- | --- |
| `industry` | 影响业务语义和 COA 选择 | 始终提供 |
| `business_type` | 决定个人消费落 Shareholder Loan 还是 Owner's Draw | 始终提供 |
| `province` | 决定税制环境 | 始终提供 |
| `has_hst_registration` | 决定 HST 是否强制 exempt | 始终提供 |
| `tax_config` | 提供税率和税制类型 | 始终提供 |
| `loans` | 识别还贷等固定语义 | 始终提供 |
| `bank_accounts` | 辅助识别疑似内部转账 | 始终提供 |

以下 profile 字段**不作为常驻自然语言背景规则**，而是只在相关 risk pack 触发时由代码注入：

- `owner_uses_company_account`
- `has_employees`

### 3.2 交易事实包

| 信息源 | 内容 | 加载方式 |
| --- | --- | --- |
| 交易数据 | `date`, `description`, `amount`, `direction`, `raw_description`, `pattern_source`, `bank_account`, `currency` | 始终提供 |
| `supplementary_context` | Coordinator 在拆分后子交易重跑 workflow 时注入的说明 | 非空时提供 |
| `cheque_info` | `cheque_number`, `payee`, `memo`, `match_method` | 非 null 时提供 |
| `receipt` | `vendor_name`, `items[]`, `tax_amount`, `match_confidence` | 非 null 时提供 |
| Observation | `classification_history`, `force_review`, `accountant_notes`, `non_promotable`, `count`, `months_seen` | 用 `(pattern, direction)` 查询命中时提供 |

### 3.3 信息源优先级

当不同信息源给出矛盾信号时，按以下顺序处理：

1. **blocking risk packs**
2. **supplementary_context**
3. **accountant_notes**
4. **receipt 信息**
5. **cheque_info**
6. **stable_single_observation**
7. **Domain Packs**
8. **AI 自身推理**

**说明：**

- profile 风险字段（如 `owner_uses_company_account`, `has_employees`）不再作为普通上下文优先级项，而是先被代码转为 risk pack activation
- `force_review` 也不再只是 observation 的一条普通信息，而是转化为 `force_review_gate`

---

## 4. 执行逻辑

### 整体架构

```text
代码做预查询与 pack activation
→ 判断是否 short-circuit
→ 需要时调用 LLM 做一次分类
→ 代码做路由与写入
```

### 阶段 0：构建当前批次快照（代码，每个客户一次）

```text
1. 读取当前已提交的 profile
2. 提取基础上下文：
   - industry
   - business_type
   - province
   - has_hst_registration
   - tax_config
   - loans
   - bank_accounts
3. 记录 risk predicate 会用到的 profile flags：
   - owner_uses_company_account
   - has_employees
4. 读取 coa.csv
5. 读取 tax_reference
6. 检查 industry pack 是否存在
```

### 阶段 1：逐笔预查询与特征提取（代码，每笔交易执行）

```text
1. 用 (transaction.description, transaction.direction) 查询 observation
2. 提取 deterministic transaction features：
   - vendor 是否疑似零售 / 多品类
   - description 是否 payroll-like
   - description 是否 transfer-like
   - pattern_source 是否为 fallback
3. 提取 evidence flags：
   - supplementary_context_confirmed_purpose
   - receipt_business_use
   - receipt_tax_support
   - cheque_named_payee_memo
   - stable_single_observation
4. 计算 activated domain packs
5. 计算 activated risk packs
```

### 阶段 2：Policy Pack Activation Layer（代码）

代码根据 deterministic predicates 生成以下结构：

```yaml
policy_trace:
  activated_packs: []
  blocking_packs: []
  override_evidence: []
  unresolved_risks: []
```

#### Pack 分类

| 类型 | 行为 |
| --- | --- |
| `blocking` | 直接阻止高置信度；必要时可 short-circuit 为 PENDING |
| `soft_risk` | 默认降置信度；只有命中兼容的 override evidence 才允许高置信度 |

#### Pack 激活规则

##### `force_review_gate`

- **Predicate**：observation 命中且 `force_review = true`
- **类型**：blocking
- **默认行为**：直接 short-circuit 为 PENDING
- **可否 override**：不可
- **下游含义**：Coordinator 应直接问 accountant，不做自动分类

##### `retail_personal_use_risk`

- **Predicate**：vendor 被识别为零售/多品类，且 `profile.owner_uses_company_account = true`
- **类型**：soft_risk
- **默认行为**：默认不应高置信度
- **可接受 override**：
  - `supplementary_context_confirmed_purpose`
  - `receipt_business_use`
  - `stable_single_observation`
- **备注**：这是 `owner_uses_company_account` 的工程化承载方式，不再写成 Core Skill 的常驻规则

##### `payroll_profile_conflict`

- **Predicate**：交易 payroll-like，且 `profile.has_employees = false`
- **类型**：blocking
- **默认行为**：直接 PENDING，标记结构性异常
- **可否 override**：不可在当前批次内由 Node 3 override
- **设计意图**：
  - Node 3 不根据未确认的 profile 变更自行改判
  - Coordinator 可以捕获 `profile_change_request`
  - Review Agent 再统一确认并写入 profile

##### `suspected_internal_transfer`

- **Predicate**：description 含有 TFR / TRANSFER 等强转账信号，且 Node 1 未命中
- **类型**：blocking
- **默认行为**：直接 PENDING，提示可能是 profile 中漏配的内部转账
- **可否 override**：不可
- **设计意图**：内部转账的确定性归属应回到 Node 1 / profile.account_relationships，不应由 Node 3 直接吞下

##### `fallback_pattern_caution`

- **Predicate**：`pattern_source = fallback`
- **类型**：soft_risk
- **默认行为**：默认降置信度，因为 canonical pattern 不稳定
- **可接受 override**：
  - `supplementary_context_confirmed_purpose`
  - `receipt_business_use`
  - `cheque_named_payee_memo`
- **额外约束**：即使最终高置信度，也**不得写入 observations**

### 阶段 3：short-circuit 规则（代码）

若激活了以下 blocking packs，代码可直接跳过 LLM 调用并输出 PENDING：

- `force_review_gate`
- `payroll_profile_conflict`
- `suspected_internal_transfer`

这三类场景的核心问题不是"AI 还需要再猜一猜"，而是系统已经知道现在不应自动落地。

### 阶段 4：Prompt 组装（代码）

#### 稳定层（可缓存）

```text
1. Core Skill
2. 基础 profile 上下文（不含 risk-only flags）
3. COA
4. tax_reference
5. industry pack（如有）
```

#### 交易层（每笔独立）

```text
1. 当前交易事实包
2. observation 查询结果（如有）
3. activated risk packs 的小型说明
4. override evidence 列表
5. common_vendors（仅 observation 未命中且需要时）
```

### 阶段 5：LLM 分类判断（一次调用）

当没有触发 blocking short-circuit 时，LLM 按以下顺序判断：

1. 识别 vendor / 交易性质
2. 选择 COA account
3. 决定 HST 处理方式
4. 应用激活的 soft risk packs
5. 检查 override evidence 是否足以覆盖所有 soft risk
6. 输出高置信度或 PENDING

### 阶段 6：代码路由

#### 高置信度

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
```

#### PENDING

```text
→ 不写 observations
→ 不写 Transaction Log
→ 将 classifier_output + policy_trace 一并传给 Coordinator
```

---

## 5. 高置信度判断规则

**高置信度必须同时满足以下条件：**

- Vendor 身份清晰
- COA 中只有一个合理科目
- HST 处理方式可确定（不是 `unknown`）
- 没有激活任何 unresolved blocking pack
- 所有激活的 soft risk packs 都已被兼容的 override evidence 覆盖

### `stable_single_observation` 的成立条件

只有满足以下全部条件时，observation 才能被视为 override evidence，而不只是普通历史参考：

- 命中 observation
- `force_review = false`
- `non_promotable = false`
- `classification_history` 只有一种分类
- `count >= 3`
- `months_seen` 跨至少 2 个月
- `accountant_notes` 没有显式写明 mixed-use / always ask / 特殊情况

### `owner_uses_company_account` 的系统化解释

`owner_uses_company_account` 不再单独决定置信度。它现在只负责激活 `retail_personal_use_risk`。

因此：

- 没触发该 pack 时，它不影响高置信度
- 触发后默认降置信度
- 只有存在兼容 override evidence 时，才允许恢复高置信度

这就是 T03 / T12 这类场景可以进入 Section B，而不会因一个 profile 字段被硬挡回 PENDING 的原因。

---

## 6. 输出

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
- `policy_trace`：记录触发了哪些 policy packs，以及哪些 override evidence 使其最终仍可高置信度

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

---

## 8. Reference 材料说明

### Layer 1 — Core Skill

只包含：

- 输出格式
- 信息源优先级
- 高置信度与 PENDING 的基本定义
- 行为边界

### Layer 2 — Domain Packs

#### `tax_reference`

包含：

- HST exempt 类别
- zero-rated 类别
- exempt / zero-rated 对 ITC 的影响
- ITC 限制规则
- 各省税率

#### `industry/{industry}`

包含某一行业的常见业务语义和易错点。仅在该行业客户上加载。

#### `vendors/common_vendors`

用于冷启动和 observation 未命中场景，不替代 observation。

### Layer 3 — Risk / Exception Packs

每个 pack 只承载一个风险，不承载通用会计知识。

示例：

- `retail_personal_use_risk`
- `payroll_profile_conflict`
- `suspected_internal_transfer`
- `fallback_pattern_caution`
- `force_review_gate`

### Layer 4 — Evidence Overrides

Evidence Overrides 由代码以结构化字段传入，不以自然语言知识包形式长期挂载。

---

## 9. 技术实现要点

### 9.1 推荐目录结构

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

### 9.2 调用流程（伪代码）

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
            policy_trace=result.policy_trace,
        )
    else:
        mark_pending(transaction, result)
```

### 9.3 Prompt 体量控制原则

- Core Skill 保持最小
- 风险类规则不再进入常驻 prompt
- 每个 risk pack 应尽量小而专一
- soft risk packs 只描述：
  - 风险是什么
  - 默认如何降置信度
  - 哪些 evidence 可以 override

### 9.4 dry run 可观察性

未来 synthetic rerun 时，应把 `policy_trace` 作为 Node 3 的可观察输出之一，用于验证：

- 哪些 case 激活了哪些 risk packs
- 哪些 case 是被 override 后进入高置信度
- 哪些 case 因 blocking pack 正确停在 PENDING

---

## 10. 与其他组件的关系

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
| 高置信度分类 | Transaction Log | 写入 `ai_reasoning` + `policy_trace` |
| PENDING | Coordinator Agent | 带着 `policy_trace` 进入沟通流程 |

### 与 deferred profile change 的关系

| 组件 | 关系 |
| --- | --- |
| Coordinator Agent | 负责记录 `profile_change_request`，不反写当前批次 Node 3 |
| Review Agent | 在审核开始前处理 `pending_profile_changes`，影响下一批次的 Node 3 上下文 |
