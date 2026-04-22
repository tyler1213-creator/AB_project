#  置信度分类器（AI 判断层）

---

## 1. 职责定义

对 Node 1（Profile 匹配）和 Node 2（Rules 匹配）均未命中的交易，进行语义理解和分类判断。置信度分类器综合交易数据、客户上下文、历史分类记录和会计知识，输出分类结果和置信度，将交易路由到对应的处理路径。

**置信度分类器不是 Agent。** 它是一个代码驱动的分类流程，LLM 在其中作为判断工具被调用。代码负责信息组装和结果路由，LLM 负责在给定的上下文中做分类判断。LLM 不做信息获取决策、不调用工具、不做多步推理。

**置信度只有两种：高置信度和非高置信度（PENDING）。** 不做中/低置信度的形式化区分。PENDING 交易根据 LLM 输出内容自然分为"带选项"（AI 有判断但不确定）和"不带选项"（AI 无法判断），这个区分在下游 Coordinator Agent 的呈现层处理，不在分类层处理。

---

## 2. 输入

### 上游数据

来自 Node 2（Rules 匹配）未命中的交易队列。代码在 Node 1 和 Node 2 批量跑完后，将所有未匹配的交易收集到待处理队列，统一交给置信度分类器处理。

### 信息源

分为稳定层（每个客户加载一次，通过 prompt caching 复用）和交易层（每笔交易独立组装）。

#### 稳定层（写入 system prompt）

| 信息源 | 内容 | 加载方式 |
| --- | --- | --- |
| 分类指令（SKILL.md） | 置信度判断标准、优先级规则、输出格式、行为规则 | 始终加载，system prompt 核心部分 |
| tax_reference.md | 加拿大税务事实性参考（HST exempt/zero-rated 类别、ITC 限制规则、省级税率表） | 始终加载 |
| Profile.md | industry, business_type, owner_uses_company_account, has_employees, has_hst_registration, province, loans, bank_accounts | 始终全量加载 |
| COA.csv | 完整科目表 | 始终全量加载（AI 输出的科目必须存在于此表中） |
| HST 税率 | 由 profile.province 推算（如 Ontario = 13%） | 代码计算后硬编码进 prompt |
| 行业规则文件 | knowledge_base/industry/{industry}.md | 按 profile.industry 条件加载，文件不存在则跳过 |

#### 交易层（每笔交易独立组装，写入 user message）

| 信息源 | 内容 | 加载方式 |
| --- | --- | --- |
| 交易数据 | date, description, amount, direction, raw_description, pattern_source, bank_account, currency | 始终提供 |
| supplementary_context | Coordinator Agent 在拆分交易后子交易重新走 workflow 时注入的额外说明 | 交易数据自带字段，非空时提供 |
| cheque_info | cheque_number, payee, memo, match_method | 交易数据自带字段，非 null 时提供（仅 CHQ# 支票交易） |
| receipt | vendor_name, items[], tax_amount, match_confidence | 交易数据自带字段，非 null 时提供 |
| Observation 同 (pattern, direction) 记录 | classification_history, force_review, accountant_notes, non_promotable | 代码用 transaction.description + transaction.direction 精确匹配 observations 中的 (pattern, direction)，命中返回该条记录，未命中返回空 |
| 通用 Vendor 参考 | knowledge_base/vendors/common_vendors.md | 仅当 observation 查询未命中时加载 |

### 信息源优先级

当不同信息源给出矛盾信号时，LLM 按以下优先级处理（高覆盖低）：

1. **force_review 标记**（来自 observation）— 最高优先级，直接跳过判断
2. **supplementary_context**（来自交易数据）— Coordinator Agent 注入的拆分交易上下文（子交易重新走 workflow 时携带 accountant 提供的业务说明）
3. **accountant_notes**（来自 observation）— accountant 对该 pattern 的历史判断理由
4. **classification_history**（来自 observation）— 该 pattern 过去的分类事实
5. **cheque_info**（来自交易数据）— 支票的 payee 和 memo，对 CHQ# 交易是强分类信号（直接说明付款对象和用途）
6. **receipt 信息** — 小票中的商品明细和税额
7. **Profile 约束** — 可以降低置信度但不能单独决定分类
8. **Knowledge base** — 通用知识，被客户级信息覆盖
9. **AI 自身推理** — 兜底，以上信息都没有时才纯靠 AI 判断

---

## 3. 执行逻辑

### 整体架构

```
代码做信息组装 → LLM 做判断（一次调用）→ 代码做路由
```

### 阶段一：稳定上下文组装（代码，每个客户执行一次）

```
1. 读取分类指令（SKILL.md）
2. 读取 tax_reference.md
3. 读取客户 profile.md 全量
4. 读取客户 coa.csv 全量
5. 由 profile.province 计算 HST 税率，硬编码进 prompt
6. 检查 profile.industry 对应的行业规则文件是否存在
   → 存在 → 加载
   → 不存在 → 跳过
7. 以上内容组装为 system prompt
```

同一客户的多笔交易共享此 system prompt，通过 prompt caching 机制复用，后续调用只需发送交易层内容。

### 阶段二：逐笔交易预查询（代码，每笔交易独立执行）

```
1. 用 transaction.description + transaction.direction 匹配 observations 中的 (pattern, direction)
   → 命中 → 提取该条 observation 记录（classification_history, force_review, accountant_notes, non_promotable）
   → 未命中 → 加载 knowledge_base/vendors/common_vendors.md

2. 组装交易层 prompt：
   - 交易数据（date, description, amount, direction, raw_description, pattern_source, bank_account, currency）
   - supplementary_context（如果非空）
   - cheque_info（如果非 null，包含 cheque_number、payee、memo）
   - receipt（如果非 null）
   - observation 记录（如果查询命中）
   - common_vendors 参考（如果已加载）
```

### 阶段三：硬性约束检查（LLM，同一次调用的第一步）

```
检查 1: observation.force_review == true？
  → 是 → 直接输出 PENDING
         不做分类判断
         将 classification_history + accountant_notes 传给下游

检查 2: transaction.supplementary_context 非空？
  → 是 → 直接采纳该信息做判断
         通常输出高置信度（accountant 已提供关键信息）

检查 3: 结构性矛盾？
  → profile.has_employees = false 但交易疑似 payroll
    → 是 → 直接输出 PENDING，标记异常
  → profile.has_hst_registration = false
    → 所有 HST 强制设为 exempt（硬性覆盖，不影响置信度判断）

以上均未触发 → 进入阶段四
```

### 阶段四：分类判断（LLM，同一次调用的第二步）

#### 步骤 A：识别 vendor / 交易性质

```
读取 transaction.description + transaction.raw_description

如果有 receipt → 读取 receipt.vendor_name + receipt.items[]（最强信号）
如果有 observation → 读取 classification_history 参考历史分类
如果无 observation → 参考 common_vendors.md（如果已加载）
最后手段 → AI 自身知识判断，完全无法识别时联网搜索
联网搜索后仍无法识别 → 放弃识别，输出 PENDING
```

#### 步骤 B：确定科目（COA 映射）

```
根据 vendor 身份 + profile.industry + profile.business_type 从 coa.csv 中选择科目

如果有 receipt.items[] → 用商品明细消除歧义
  （如 HOME DEPOT 买水泥 → Supplies & Materials；买洗碗机 → Shareholder Loan）

如果 observation.classification_history 只有一种分类 → 强参考该结果
如果 observation.classification_history 有多种分类 → 记录歧义
如果 observation.accountant_notes 存在 → 遵循 accountant 的判断理由

验证选择的科目是否存在于 coa.csv 中
```

#### 步骤 C：确定 HST 处理方式

```
如果 profile.has_hst_registration = false → exempt（阶段三已设定）
如果 vendor 是零售/多品类 且无小票 → hst = unknown
如果 vendor 是零售/多品类 且有小票 → 根据 receipt.tax_amount 推算
如果 vendor 是单一品类（如电力、电信）→ 标准 HST 处理

LLM 只判断 HST 处理方式（inclusive / exempt / unknown），金额拆分由下游 build_je_lines.py 完成。
```

AI 用自身常识判断 vendor 是否为多品类零售商，不维护固定名单。

#### 步骤 D：确定置信度

**高置信度 — 以下条件必须全部满足：**

- Vendor 身份清晰（description 无歧义，或 receipt 确认）
- COA 中只有一个合理科目选项
- 如有 observation：classification_history 只有一种分类，且与 AI 判断一致
- 如果 vendor 属于零售类且 `profile.owner_uses_company_account = true`：
  - 默认不应高置信度
  - 但当存在足够强的反证时仍可高置信度，例如：
    - receipt.items[] 已明确指向业务用途
    - supplementary_context 直接给出 accountant 已确认的业务说明
    - observation.classification_history 长期单一且与当前判断一致，且没有个人用途冲突信号
- HST 处理方式可确定（不是 unknown）

**非高置信度（PENDING）— 以上任一条件不满足。** 根据 AI 能提供的信息量，输出内容自然分为两类：

- **带选项**：AI 能识别 vendor 但有多种合理分类，输出 2-3 个选项供 accountant 选择
- **不带选项**：AI 无法识别 vendor 或业务目的，输出分析说明和建议提问

---

## 4. 输出

### 输出格式

LLM 输出为结构化数据，格式根据置信度不同：

#### 高置信度输出

```yaml
{
    "confidence": "high",
    "account": "Telephone & Internet",
    "hst": "inclusive_13",
    "ai_reasoning": "Rogers Wireless 是加拿大主要电信运营商，业务单一。Observation 中该 pattern 历史 5 次均分类为 Telephone & Internet，金额稳定在 $85-92 区间。HST 按 Ontario 13% inclusive 处理。",
    "notes": ""
}
```

- ai_reasoning 字段：AI 判断逻辑的说明，写入 Transaction Log 供 accountant 事后追溯分类依据。内容需让不同水平的 accountant 都能看懂，包括：识别到的 vendor 类型、参考了哪些历史数据、HST 处理依据。不需要复现完整决策流程，但要说清判断逻辑
- notes 字段：用于权责发生制提醒（如"年度保费，建议标注 accrual"），不改变 JE 本身

#### PENDING 输出

PENDING 输出采用统一格式，所有字段始终存在。根据 AI 能提供的信息量，字段的填充方式不同：

- **带选项**：AI 能识别 vendor 但有多种合理分类 → options 非空，description_analysis 和 suggested_questions 为空
- **不带选项**：AI 无法识别 vendor 或业务目的 → options 为空，description_analysis 和 suggested_questions 非空

```yaml
{
    "confidence": "pending",
    "options": [],                        # 无选项时为 []，有选项时为 2-3 个选项
    "observation_context": "",            # 无 observation 记录时为 ""
    "accountant_notes": "",               # 无 notes 时为 ""
    "description_analysis": "",           # 有选项时为 ""
    "suggested_questions": []             # 有选项时为 []
}
```

**带选项示例：**

```yaml
{
    "confidence": "pending",
    "options": [
        {
            "account": "Office Supplies",
            "hst": "inclusive_13",
            "reason": "Amazon 常见办公用品采购"
        },
        {
            "account": "Supplies & Materials",
            "hst": "inclusive_13",
            "reason": "该客户为建筑公司，可能是施工材料"
        },
        {
            "account": "Shareholder Loan",
            "hst": "exempt",
            "reason": "客户有个人消费记录"
        }
    ],
    "observation_context": "历史上 4 次 Supplies & Materials，1 次 Shareholder Loan",
    "accountant_notes": "该客户偶有个人消费走公司账户",
    "description_analysis": "",
    "suggested_questions": []
}
```

**不带选项示例：**

```yaml
{
    "confidence": "pending",
    "options": [],
    "observation_context": "",
    "accountant_notes": "",
    "description_analysis": "EMT 电子转账，无法从 description 判断业务目的",
    "suggested_questions": [
        "这笔 $2,500 的 EMT 转账是付给谁的？用途是什么？"
    ]
}
```

---

## 5. 特殊处理场景

### 附件/小票处理

当交易数据的 receipt 字段非 null 时：

- receipt 中的 items[] 是消除分类歧义的最强信号
- receipt 中的 tax_amount 可直接用于确定 HST 处理方式
- 有 receipt 的交易置信度通常更高
- 当 receipt.items[] 已明确指向业务用途时，可覆盖 `owner_uses_company_account = true` 带来的零售类个人消费疑虑

交易数据的 receipt 字段由数据预处理 Agent 在上游完成填充（小票已提取为结构化数据并配对到交易）。置信度分类器不直接处理图片，只读取结构化的 receipt 字段。

### 混合 HST Vendor 处理

对于零售类/多品类 vendor（如 Costco、Walmart、Amazon、药房、餐饮类）：

- 无小票 → HST 标记为 unknown
- 有小票 → 根据 receipt.tax_amount 推算 HST
- AI 用自身常识判断 vendor 是否为多品类零售商，不维护固定名单

### 权责发生制提醒

AI 在处理交易时如果发现可能涉及 accrual 的交易（如年度保费、大额预付）：

- 在输出的 notes 字段中标注提醒
- 不改变 JE 本身（仍然是现金制）
- 标注不影响置信度判断

### 联网搜索

- AI 先用自身知识 + 已有上下文判断
- 完全无法识别 vendor 时才触发联网搜索
- 搜索后仍无法识别 → 输出 PENDING
- 联网搜索是最后手段，不是默认动作

### 疑似未配置的内部转账

AI 看到 description 中含有疑似转账关键词（TFR、TRANSFER 等），但 Node 1 未匹配到：

- 参考 profile.bank_accounts 判断是否可能是 profile 中漏配的内部转账
- 如果判断为漏配 → 输出 PENDING，建议 accountant 补充 profile.account_relationships
- 不自行做内部转账的分类判断

---

## 6. Reference 材料说明

### 始终提供的材料

**分类指令（SKILL.md）**

置信度判断标准、信息源优先级、输出格式要求、硬性约束检查规则、特殊场景处理原则。这是 system prompt 的核心部分。

**tax_reference.md**

加拿大税务事实性参考数据，补齐 AI 训练数据可能不精确或过时的确定性知识。不是行为指令，不是纠正规则。

内容分类：

- **HST Exempt 类别清单：** 金融服务（银行手续费、利息）、住宅租金、医疗服务、儿童看护、保险保费、教育服务等。这些类别不征收 HST，供应方不可 claim ITC。
- **Zero-rated 类别清单：** 处方药、基本食品杂货（未加工/未加热）、出口商品等。税率为 0%，但供应方仍可 claim ITC。这是与 exempt 的关键区别。
- **Exempt vs. Zero-rated 对 ITC 的影响：** Exempt 供应方不可 claim ITC；zero-rated 供应方可以。对于买方（本系统的客户），购买 exempt 商品/服务时支付金额中不含 HST，购买 zero-rated 商品时同样不含 HST，但性质不同。
- **ITC 限制规则：** 餐饮娱乐支出仅可抵扣 50% 的 HST；个人/商业混合用途支出按商业用途比例抵扣；特定行业有额外限制。
- **各省 HST/GST/PST 税率表：** Ontario 13% HST、BC 5% GST + 7% PST、Alberta 5% GST only，等等。

**维护方式：** 税法变更时由人工更新。不随系统运行自动增长，不是活文档。

**token 预算：** 500 - 1,500 tokens。

**与其他信息源的关系：** Profile.has_hst_registration 决定客户是否适用 HST（false 时所有交易强制 exempt）；tax_reference 提供"如果适用，具体怎么判断某类交易的 HST 处理方式"的事实依据。

**Profile.md**

全量提供。关键字段的作用：

- industry → 影响科目选择（建筑 vs 餐饮 vs 科技）
- business_type → 决定个人消费走 Shareholder Loan（corporation）还是 Owner's Draw（sole proprietorship）
- owner_uses_company_account → true 时零售类 vendor 默认降置信度；但 receipt、supplementary_context 或稳定单一 observation 等强证据可以覆盖这条默认风险提示
- has_employees → false 时 payroll 类交易标记异常
- has_hst_registration → false 时所有 HST = exempt
- loans → 识别还贷交易
- bank_accounts → 识别疑似未配置的内部转账

**COA.csv**

全量提供。AI 选择的科目必须存在于此表中。这是验证约束，不是参考信息。

### 条件加载的材料

**行业规则文件（knowledge_base/industry/{industry}.md）**

按 profile.industry 加载。这些文件不预先创建，而是在运行中发现 AI 对特定行业的交易持续犯错时逐步积累。例如：发现 AI 反复把建筑公司的设备租赁分到 Equipment Purchase 而不是 Equipment Rental → 写一条纠正规则到 construction.md。

**通用 Vendor 参考（knowledge_base/vendors/common_vendors.md）**

仅当 observation 查询未命中时加载。包含加拿大常见 vendor 的典型科目映射（原通用 vendor 库迁移而来）。LLM 对知名 vendor 通常不需要此参考，此文件主要对冷启动阶段（observations 为空）有辅助价值。

### 不需要的材料

- ~~accounting_axioms.md~~：LLM 已知会计基础知识，无需额外教学
- ~~独立的 hst_rules.md~~：HST 事实性规则已纳入 tax_reference.md

---

## 7. 技术实现要点

### Prompt 结构

```
┌─────────────────────────────────────────────────┐
│ System Prompt（稳定层，prompt caching 复用）       │
│                                                   │
│  - SKILL.md 分类指令                              │
│  - tax_reference.md                               │
│  - Profile.md 全量                                │
│  - COA.csv 全量                                   │
│  - HST 税率（代码计算后硬编码）                      │
│  - 行业规则文件（如有）                              │
│                                                   │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ User Message（交易层，每笔交易独立）               │
│                                                   │
│  - 当前交易数据                                    │
│  - supplementary_context（如有）                    │
│  - cheque_info（如有）                              │
│  - receipt 信息（如有）                             │
│  - observation 查询结果（代码预查询）                │
│  - common_vendors 参考（仅 observation 无记录时）    │
│                                                   │
└─────────────────────────────────────────────────┘
```

### 调用流程

```python
# 阶段一：组装稳定层（每个客户一次）
system_prompt = assemble_system_prompt(client_id)

# 阶段二 + 三 + 四：逐笔处理
for transaction in pending_queue:
    # 代码预查询
    observation = query_observation(transaction.description, transaction.direction, client_id)
    common_vendors = load_if_no_observation(observation)
    
    # 组装交易层
    user_message = assemble_transaction_prompt(
        transaction, observation, common_vendors
    )
    
    # 一次 LLM 调用（阶段三 + 四在 prompt 指令中顺序执行）
    result = llm_call(system=system_prompt, user=user_message)
    
    # 阶段五：路由
    if result.confidence == "high":
        je_input = build_je_lines(transaction, result, client_id)  # → 构造 je_lines
        je_result = validate_je(je_input)                          # → 校验格式
        write_observation(result)                                  # → Observations
        write_transaction_log(                                     # → Transaction Log
            transaction, je_result.je_lines,
            classified_by="ai_high_confidence",
            ai_reasoning=result.ai_reasoning
        )
    else:
        mark_pending(transaction, result)  # → Coordinator Agent
```

### 上下文体量估算

| 内容 | 估算 token 量 |
| --- | --- |
| SKILL.md 分类指令 | 1,000 - 2,000 |
| tax_reference.md | 500 - 1,500 |
| Profile.md | 500 - 3,000 |
| COA.csv | 2,000 - 5,000 |
| 行业规则文件（如有） | 500 - 1,500 |
| **稳定层合计** | **4,500 - 13,000** |
| 交易层（含 observation + receipt） | 200 - 800 |
| **总输入** | **5,000 - 14,000** |

此体量在现代 LLM 有效注意力范围内，不会导致判断质量下降。

**需防范的风险：** 行业规则文件的膨胀。单个文件不超过 2,000 tokens，超过时拆分为子主题文件，代码层按更细条件选择加载。

---

## 8. 与其他组件的关系

### 上游（谁把交易传给置信度分类器）

| 组件 | 关系 |
| --- | --- |
| Node 2（Rules 匹配） | Rules 未命中的交易收集到待处理队列后，逐笔传给分类器 |

### 信息源（分类器读取的数据）

| 组件 | 读取方式 |
| --- | --- |
| Profile.md | 代码全量加载到 system prompt |
| COA.csv | 代码全量加载到 system prompt |
| tax_reference.md | 代码加载到 system prompt |
| 行业规则文件 | 代码按 profile.industry 条件加载到 system prompt |
| Observations.md | 代码精确查询同 (pattern, direction) 记录，加载到交易层 prompt |
| common_vendors.md | 代码在 observation 无记录时加载到交易层 prompt |

### 下游（分类器的输出去向）

| 置信度 | 下游组件 | 行为 |
| --- | --- | --- |
| 高置信度 | build_je_lines.py + validate_je | 调用 build_je_lines.py 根据 account + hst + 交易数据构造 je_lines，再调用 validate_je 校验格式 |
| 高置信度 | Node 5（写入 Observations） | 更新 classification_history, count, months_seen，confirmed_by 标记为 ai |
| 高置信度 | Transaction Log | JE 生成后，调用 write_transaction_log.py 写入完整交易记录（classified_by = ai_high_confidence，ai_reasoning 来自本次输出） |
| 高置信度 | Node 6（输出报告） | 归入 Section B（PROBABLE） |
| PENDING | Coordinator Agent | 批量收集所有 PENDING 交易，与 accountant 沟通 |
