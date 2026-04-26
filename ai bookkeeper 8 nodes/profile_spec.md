# Profile.md

---

## 1. 职责定义

存储客户的结构性身份信息，为主 Workflow 各节点和 Agent 提供客户级别的上下文。Profile 只存储**不随交易积累而变化**的信息，只在客户的公司结构发生变化时才更新（如开新银行账户、注册 HST、新增贷款等）。

Profile 承担基于公司结构信息的确定性交易分类（如内部转账），不承担基于业务目的的交易分类判断。后者由 Rules、AI 层和 Accountant 负责。
---

## 2. 数据格式

```yaml
# === 基本信息 ===
company_name: "2830448 ONTARIO LTD."
business_type: "corporation"              # corporation / sole_proprietorship
industry: "Construction"
province: "Ontario"

# === 税务信息 ===
has_hst_registration: true
hst_number: "123456789RT0001"             # 为空时表示未注册或办理中
tax_config:
  type: "HST"                              # HST / GST_PST / GST_only
  rate: 0.13                               # 当前适用的销售税总税率，用于 build_je_lines.py 的 inclusive 拆分计算

# === 人员与运营 ===
has_employees: true
owner_uses_company_account: true          # 老板是否用公司账户做个人交易

# === 银行账户 ===
bank_accounts:
  - id: "TD-5027013"
    type: "Business Chequing"
    coa_account: "Business Chequing"
    coa_number: "1000"
  - id: "TD-6337546"
    type: "Business Savings"
    coa_account: "Business Savings"
    coa_number: "1001"

# === 账户间关系（内部转账匹配用）===
account_relationships:
  - pattern: "TFR-TO 6337546"
    from: "TD-5027013"
    to: "TD-6337546"
    type: "internal_transfer"
  - pattern: "TFR-FR 6337546"
    from: "TD-6337546"
    to: "TD-5027013"
    type: "internal_transfer"

# === 贷款与信用额度 ===
loans:
  - lender: "TD Bank"
    type: "line_of_credit"
    account_pattern: "LOC PAYMENT"
    coa_account: "Line of Credit"
```

### 字段说明

**基本信息**

- **company_name**：公司法律全名
- **business_type**：企业类型。`corporation` 使用 Shareholder Loan 科目处理老板个人消费，`sole_proprietorship` 使用 Owner's Draw
- **industry**：行业类型，AI 层判断业务性质时的上下文参考
- **province**：省份，决定 HST 税率（如 Ontario 13%）

**税务信息**

- **has_hst_registration**：是否已注册 HST。true = 交易需要拆分 HST，false = 全部 exempt。独立于 hst_number 字段，因为注册号可能还在办理中但已确定要注册
- **hst_number**：HST/GST 注册号。为空不一定代表未注册，以 has_hst_registration 为准
- **tax_config**：销售税配置，供 build_je_lines.py 读取做 HST 拆分计算
  - **type**：当前税制类型，由 province 决定。Ontario = HST，BC = GST_PST，Alberta = GST_only。当前只支持 HST，未来扩展时增加 PST 组件字段
  - **rate**：当前销售税总税率。build_je_lines.py 读取此值做 inclusive 拆分计算，不硬编码税率

**人员与运营**

- **has_employees**：是否有员工。影响 AI 层对 payroll 相关交易的判断——如果为 false，任何看起来像 payroll 的交易应标记 PENDING
- **owner_uses_company_account**：老板是否用公司账户做个人消费。如果为 true，AI 层在遇到零售类 vendor（HOME DEPOT、COSTCO、AMAZON 等）时应自动降低置信度

**银行账户**

- **bank_accounts**：客户所有银行账户的列表。每个账户包含 id（银行标识）、type（账户类型）、coa_account（对应的 COA 科目名称）、coa_number（COA 科目编号）

**账户间关系**

- **account_relationships**：客户银行账户之间的转账关系。Node 1 用此字段对交易 `raw_description` 做内部转账的确定性匹配。每条关系包含 pattern（原始银行描述中的匹配字符串）、from / to（源和目标账户 id）、type（关系类型，目前只有 `internal_transfer`）

**贷款与信用额度**

- **loans**：客户的贷款和信用额度列表。AI 层遇到定期固定金额的 debit 时，可参考此字段判断是否为还贷。每条记录包含 lender（贷方）、type（贷款类型）、account_pattern（原始银行描述中的参考字符串）、coa_account（对应的 COA 科目名称）

---

## 3. 数据来源

### 来源一：Onboarding Agent 问卷收集

新客户接入时，Onboarding Agent 通过问卷或问答方式向 accountant 或客户收集信息，构建初始 profile.md。

### 来源二：Onboarding Agent 历史数据提取

Onboarding Agent 分析客户过去已由 accountant 做好的历史账本，提取公司结构信息构建 profile.md。

### 来源三：Coordinator Agent 捕获变更信号

处理 PENDING 交易过程中，accountant 可能提供新的公司结构信息（如新增银行账户关系、员工状态变化）。Coordinator Agent 不直接更新 profile.md，而是记录结构化的 `profile_change_request`，由审核 Agent 在审核阶段统一确认并写入。

---

## 4. 状态与生命周期

**Profile 没有状态流转机制。它是一份持续维护的文档，创建后只做增量更新。**

```
Onboarding Agent 创建初始 profile.md
  → 系统运行过程中按需更新
  → 无过期、无清理、无删除机制
```

更新只在以下场景发生：

- 客户开了新银行账户或关了旧账户 → 更新 bank_accounts 和 account_relationships
- 客户注册了 HST → 更新 has_hst_registration 和 hst_number
- 客户新增或还清贷款 → 更新 loans
- 客户公司结构变化（如雇了第一个员工）→ 更新 has_employees
- 客户开始或停止用公司账户做个人消费 → 更新 owner_uses_company_account

---

## 5. 被谁读取

| 读取者 | 时机 | 目的 |
| --- | --- | --- |
| Node 1（Profile 匹配） | 每笔交易进入主 Workflow 时 | 读取 account_relationships，对交易 `raw_description` 做内部转账确定性匹配。匹配成功且 JE 生成后，调用 write_transaction_log.py 写入 Transaction Log（classified_by = profile_match，profile_match_detail） |
| Node 3（置信度分类器） | 交易进入 AI 判断时 | 读取 industry、business_type、has_employees、owner_uses_company_account、loans 等作为判断上下文 |
| build_je_lines.py | 构造 JE 时 | 读取 tax_config.rate 做 HST 拆分计算；读取 bank_accounts 确定银行科目 |
| Coordinator Agent | 处理 PENDING 交易时 | 读取 profile 了解客户背景，辅助与 accountant 的沟通 |
| 审核 Agent | 审核阶段 | 读取 profile 了解客户结构，辅助理解 accountant 的修改意图 |

---

## 6. 被谁修改

| 修改者 | 操作 | 触发条件 |
| --- | --- | --- |
| Onboarding Agent | 创建完整 profile | 新客户接入时 |
| 审核 Agent | 更新 bank_accounts / account_relationships / 其他字段 | 处理 Coordinator 阶段记录的 profile_change_requests（经 accountant 确认后写入），或审核对话中 accountant 主动提出变更 |

**Coordinator Agent 不直接修改 profile。** 它在处理 PENDING 交易时捕获 accountant 提供的 profile 变更信号，记录为结构化的 `profile_change_request`，由审核 Agent 在审核阶段统一处理写入。

**所有 Agent 对 profile 的修改必须基于 accountant 提供的信息，不能自行推断或猜测公司结构。**

---

## 7. 与其他组件的关系

### 消费者（谁读取 Profile）

| 组件 | 关系 |
| --- | --- |
| Node 1（Profile 匹配） | 读取 account_relationships 做内部转账匹配 |
| Node 3（置信度分类器） | 读取客户背景信息作为分类判断上下文 |
| build_je_lines.py | 读取 tax_config.rate 和 bank_accounts 用于 JE 构造 |
| Coordinator Agent | 读取客户背景辅助 PENDING 交易沟通 |
| 审核 Agent | 读取客户背景辅助审核 |

### 修改者

| 组件 | 关系 |
| --- | --- |
| Onboarding Agent | 创建初始 profile |
| 审核 Agent | 运行期 profile 更新（处理 Coordinator 阶段记录的变更请求 + 审核对话中 accountant 主动提出的变更） |

**注意：** Coordinator Agent 只记录 profile_change_request，不直接修改 profile。

### 依赖

| 组件 | 关系 |
| --- | --- |
| COA（coa.csv） | profile 中的 coa_account 和 coa_number 必须与 coa.csv 中的科目一致 |
