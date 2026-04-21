# JE 构造与校验（Journal Entry Builder & Validator）

---

## 1. 职责定义

JE 的生成分为两个独立步骤，由两个脚本分别承担：

- **build_je_lines.py（构造）**：共用脚本，根据交易数据 + 分类结果 + Profile + COA 构造完整的 je_lines。所有需要生成 JE 的调用方（Node 1/2/3、Coordinator Agent、审核 Agent）统一通过此脚本构造，不各自实现构造逻辑
- **validate_je（校验）**：校验 je_lines 格式合规性。不执行任何计算，不读取任何外部文件。确保所有进入 Transaction Log 的 je_lines 符合统一的格式规范

调用流程：`分类结果 → build_je_lines.py 构造 → validate_je 校验 → 写入 Transaction Log`

---

## 1.5 build_je_lines.py（JE 构造脚本）

### 输入

```yaml
build_input:
  transaction:
    amount: 156.78                         # 交易金额（绝对值）
    direction: "debit"                     # 银行流水方向：debit（钱出去）/ credit（钱进来）
    bank_account: "TD-5027013"             # 银行账号 ID
  classification:
    account: "Supplies & Materials"        # 分类得出的 COA 科目名
    hst: "inclusive_13"                    # exempt / inclusive_13 / unknown / internal_transfer
  client_id: "client_001"                  # 用于加载 Profile 和 COA
```

### 执行逻辑

```
Step 1: 银行账号 → COA 科目名
  → 读取 Profile.bank_accounts
  → 查找 bank_account ID 对应的 coa_account
  → 例："TD-5027013" → "Business Chequing"

Step 2: 查 classification.account 的 Type
  → 读取 COA.csv
  → 查找 classification.account 对应的 Type 列
  → 例："Supplies & Materials" → Type = "Expenses"

Step 3: 确定 JE 行数
  → hst == "inclusive_*" → 3 行
  → 其他（exempt / unknown / internal_transfer）→ 2 行

Step 4: 计算金额（仅 inclusive 时）
  → 读取 Profile.tax_config.rate（例：0.13）
  → pre_tax = round(amount / (1 + rate), 2)
  → hst_amount = round(amount - pre_tax, 2)

Step 5: 确定借贷方向
  → direction == "debit"（钱出去）→ Credit 银行科目, Debit 分类科目
  → direction == "credit"（钱进来）→ Debit 银行科目, Credit 分类科目
  → HST 行与分类科目同侧

Step 6: 选择 HST 科目（仅 inclusive 时）
  → account Type 属于 Expenses / Cost of Goods Sold / Other Expense / Assets 类
    → "HST/GST Receivable"
  → account Type 属于 Income / Other Income 类
    → "HST/GST Payable"

Step 7: 组装 je_lines 数组
```

### 输出

```yaml
je_input:
  transaction_id: "txn_01JVF8Y7T6M3K2N9Q4R5S8W1XZ"
  hst_type: "inclusive_13"
  je_lines:
    - { type: "debit", account: "Supplies & Materials", amount: 138.74 }
    - { type: "debit", account: "HST/GST Receivable", amount: 18.04 }
    - { type: "credit", account: "Business Chequing", amount: 156.78 }
```

输出直接传给 validate_je 校验。

### 数据依赖

| 文件 | 读取内容 |
|------|---------|
| Profile.md | bank_accounts（银行账号 → COA 科目映射）、tax_config.rate（税率） |
| COA.csv | Type 列（判断科目类型，决定借贷方向和 HST 科目选择） |

### 设计原则

- **纯确定性计算**：所有步骤都是查表 + 规则 + 算术，不涉及 LLM 判断
- **税率数据驱动**：从 Profile.tax_config.rate 读取，不硬编码。未来扩展多省税制时改数据不改逻辑
- **单一职责**：只负责从（amount + direction + account + hst）构造 je_lines，不做分类判断

---

## 2. validate_je 输入

build_je_lines.py 或调用方传入以下数据：

```yaml
je_input:
  transaction_id: "txn_01JVF8Y7T6M3K2N9Q4R5S8W1XZ"       # 上游分配的永久交易标识
  hst_type: "inclusive_13"                # exempt | inclusive_13 | unknown | internal_transfer
  je_lines:
    - { type: "debit", account: "Supplies & Materials", amount: 138.71 }
    - { type: "debit", account: "HST Receivable", amount: 18.07 }
    - { type: "credit", account: "Business Chequing", amount: 156.78 }
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| transaction_id | string | 是 | 关联的交易标识 |
| hst_type | string | 是 | HST 处理方式，取值：`exempt` / `inclusive_13` / `unknown` / `internal_transfer` |
| je_lines | array | 是 | 已构造好的完整借贷分录 |
| je_lines[].type | string | 是 | `debit` 或 `credit` |
| je_lines[].account | string | 是 | COA 中的科目名称 |
| je_lines[].amount | number | 是 | 金额，必须 > 0 |

**注意：** 正常流程下，je_lines 由 build_je_lines.py 统一构造。validate_je 作为最后一道防线，确保格式合规。

---

## 3. 执行逻辑

### 3.1 格式校验规则

JE 生成器按以下顺序校验传入的 je_input：

```
Step 1: 基础字段校验
  → transaction_id 非空
  → hst_type 是四个合法值之一
  → je_lines 非空且长度 ≥ 2

Step 2: 逐行校验
  → 每行 type 是 "debit" 或 "credit"
  → 每行 account 非空字符串
  → 每行 amount > 0

Step 3: 借贷平衡校验
  → sum(debit amounts) == sum(credit amounts)
  → 允许误差：±$0.01（四舍五入差异）

Step 4: hst_type 与行数一致性校验
  → exempt:          恰好 2 行（1 debit + 1 credit）
  → inclusive_13:    恰好 3 行（2 debit + 1 credit）
  → unknown:         恰好 2 行（1 debit + 1 credit）
  → internal_transfer: 恰好 2 行（1 debit + 1 credit）

Step 5: hst_type 特定校验
  → inclusive_13: 必须有一行 account = "HST Receivable"（debit 侧）
  → internal_transfer: 两行的 account 都必须是银行类科目（不含费用/收入科目）
```

### 3.2 四种标准 JE 模版

以下模版供调用方参考，确保构造的 je_lines 能通过校验。

**模版 1: exempt（免 HST）**

适用：profile.has_hst_registration = false，或该费用类别不含 HST。

```yaml
# 支出示例：$100 办公用品
hst_type: "exempt"
je_lines:
  - { type: "debit", account: "Office Supplies", amount: 100.00 }
  - { type: "credit", account: "Business Chequing", amount: 100.00 }

# 收入示例：$500 服务收入
hst_type: "exempt"
je_lines:
  - { type: "debit", account: "Business Chequing", amount: 500.00 }
  - { type: "credit", account: "Service Revenue", amount: 500.00 }
```

**模版 2: inclusive_13（含 13% HST）**

适用：交易金额含 HST，需拆分为 pre_tax + hst_amount。

拆分公式（调用方负责计算，公式由代码实现）：
`pre_tax = total / (1 + 0.13)`, `hst_amount = total - pre_tax`

```yaml
# 支出示例：$156.78（含 HST）
hst_type: "inclusive_13"
je_lines:
  - { type: "debit", account: "Supplies & Materials", amount: 138.74 }
  - { type: "debit", account: "HST Receivable", amount: 18.04 }
  - { type: "credit", account: "Business Chequing", amount: 156.78 }

# 收入示例：$1130.00（含 HST）
hst_type: "inclusive_13"
je_lines:
  - { type: "debit", account: "Business Chequing", amount: 1130.00 }
  - { type: "credit", account: "Service Revenue", amount: 1000.00 }
  - { type: "credit", account: "HST Payable", amount: 130.00 }
```

注意：支出拆 HST 时 debit 侧是 HST Receivable（进项税可抵扣）；收入拆 HST 时 credit 侧是 HST Payable（销项税应缴）。调用方负责正确选择科目。

**模版 3: unknown（HST 待定）**

适用：零售类 vendor 无小票，HST 状态无法确定。结构同 exempt，但系统在 Transaction Log 中标记 `hst: "unknown"`，待后续确认。

```yaml
# 支出示例：$45.20 Walmart
hst_type: "unknown"
je_lines:
  - { type: "debit", account: "Supplies & Materials", amount: 45.20 }
  - { type: "credit", account: "Business Chequing", amount: 45.20 }
```

**模版 4: internal_transfer（内部转账）**

适用：Node 1 profile_match 识别的内部账户间转账。无费用/收入科目，无 HST。

```yaml
# 示例：从 Chequing 转 $5000 到 Savings
hst_type: "internal_transfer"
je_lines:
  - { type: "debit", account: "Business Savings", amount: 5000.00 }
  - { type: "credit", account: "Business Chequing", amount: 5000.00 }
```

---

## 4. 输出

### 校验通过

原样返回传入的 je_lines，不做任何修改。调用方随后将 je_lines 写入 Transaction Log 第二层。

```yaml
result:
  status: "valid"
  je_lines: [...]  # 原样返回
```

### 校验失败

返回错误信息，列明所有不通过的校验项。调用方不应将校验失败的 JE 写入 Transaction Log。

```yaml
result:
  status: "invalid"
  errors:
    - "debit 总额 (156.78) ≠ credit 总额 (156.77): 差额 $0.01 超出容差"
    - "hst_type = inclusive_13 但 je_lines 只有 2 行，应为 3 行"
```

---

## 5. 异常处理

| 异常场景 | 处理方式 |
|----------|----------|
| debit ≠ credit（超出 ±$0.01） | 返回 invalid + 差额详情 |
| je_lines 缺少必填字段 | 返回 invalid + 缺失字段列表 |
| hst_type 与 je_lines 行数不匹配 | 返回 invalid + 期望行数 vs 实际行数 |
| inclusive_13 但无 HST Receivable/Payable 行 | 返回 invalid + 提示缺少 HST 行 |
| internal_transfer 但包含费用/收入科目 | 返回 invalid + 提示内部转账不应有费用/收入科目 |
| amount ≤ 0 | 返回 invalid + 指出哪一行 |
| hst_type 不在合法值范围 | 返回 invalid + 合法值列表 |

**JE 生成器不处理的异常（调用方职责）：**
- account 名称是否在 COA 中存在 — 调用方在分类阶段已校验
- HST 拆分金额是否计算正确 — 调用方负责计算
- 交易方向是否正确 — 调用方负责判断

---

## 6. 与其他组件的关系

### 调用方（谁调用 build_je_lines.py + validate_je）

| 调用方 | 场景 |
|--------|------|
| Node 1（Profile 匹配） | 内部转账匹配成功后，调用 build_je_lines.py 构造 → validate_je 校验 |
| Node 2（Rules 匹配） | Rule 匹配成功后，调用 build_je_lines.py 构造 → validate_je 校验 |
| 置信度分类器 | 高置信度分类完成后，调用 build_je_lines.py 构造 → validate_je 校验 |
| Coordinator Agent | accountant 确认 PENDING 交易后，调用 build_je_lines.py 构造 → validate_je 校验 |
| 审核 Agent | accountant 修正分类后，调用 build_je_lines.py 构造 → validate_je 校验 |

### 数据文件依赖

- **build_je_lines.py**：读取 Profile.md（bank_accounts, tax_config）和 COA.csv（Type 列）
- **validate_je**：无。纯校验函数，不读取不写入任何文件。

### 输出流向

| 下游 | 关系 |
|------|------|
| Transaction Log | 校验通过的 je_lines 由调用方写入 Transaction Log 第二层 |
