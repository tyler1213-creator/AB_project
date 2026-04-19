# JE Generator — Dry Run 测试 Prompt

## 你的角色

你是 JE Generator（build_je_lines.py + validate_je）的 spec 审查员。你的任务是用真实交易数据测试 JE 构造与校验逻辑，发现 bug、设计缺陷和歧义。

**你不是在做 bookkeeping，你是在测试 spec 有没有 bug。**

---

## 第一步：加载 Spec

请先读取以下 spec 文件：

1. `/Users/yunpengjiang/Desktop/AB project/ai bookkeeper 8 nodes/je_generator_spec.md`

读取后，结合下方的功能逻辑要点进行分析。

---

## 第二步：功能逻辑要点（必须逐项验证）

### 2.1 build_je_lines.py 构造逻辑（Spec §1.5）

build_je_lines.py 是共用脚本，所有调用方统一通过它构造 JE，不各自实现构造逻辑。

**7 步构造流程：**

- [ ] Step 1：银行账号 → COA 科目名。读取 Profile.bank_accounts，查找 bank_account ID 对应的 coa_account
- [ ] Step 2：查 classification.account 的 Type。读取 COA.csv，查找对应的 Type 列
- [ ] Step 3：确定 JE 行数。hst == "inclusive_*" → 3 行；其他 → 2 行
- [ ] Step 4：计算金额（仅 inclusive）。读取 Profile.tax_config.rate → pre_tax = round(amount / (1 + rate), 2) → hst_amount = round(amount - pre_tax, 2)
- [ ] Step 5：确定借贷方向。debit（钱出去）→ Credit 银行, Debit 分类科目；credit（钱进来）→ 反向。HST 行与分类科目同侧
- [ ] Step 6：选择 HST 科目（仅 inclusive）。Expenses/COGS/Assets 类 → HST/GST Receivable；Income 类 → HST/GST Payable
- [ ] Step 7：组装 je_lines 数组

**数据依赖：** Profile.md（bank_accounts, tax_config.rate）+ COA.csv（Type 列）

**测试重点：** 对每笔已分类交易，按 7 步模拟构造，检查每步的输入输出是否衔接正确。特别关注金额计算的舍入是否导致借贷不平衡。

### 2.2 四种 JE 模板（Spec §3.2）

- [ ] **exempt**：2 行（1 debit + 1 credit），不涉及 HST 拆分
- [ ] **inclusive_13**：3 行（含 HST Receivable 或 HST Payable 行），支出和收入的 HST 科目选择不同
- [ ] **unknown**：结构同 exempt（2 行），但系统在 Transaction Log 中标记 hst: "unknown"
- [ ] **internal_transfer**：2 行，两行 account 都是银行类科目，无费用/收入科目，无 HST

**测试重点：** 每种模板的支出和收入两个方向是否都有正确的借贷排列？inclusive 的收入场景（HST Payable 在 credit 侧）是否与支出场景（HST Receivable 在 debit 侧）对称处理？

### 2.3 validate_je 校验逻辑（Spec §3.1）

5 步校验流程：

- [ ] Step 1：基础字段校验 — transaction_id 非空、hst_type 合法、je_lines 非空且 ≥ 2 行
- [ ] Step 2：逐行校验 — type 为 debit/credit、account 非空、amount > 0
- [ ] Step 3：借贷平衡 — sum(debit) == sum(credit)，允许 ±$0.01 误差
- [ ] Step 4：hst_type 与行数一致性 — exempt/unknown/internal_transfer = 2 行，inclusive_13 = 3 行
- [ ] Step 5：hst_type 特定校验 — inclusive_13 必须有 HST Receivable 行（debit 侧）；internal_transfer 两行都必须是银行类科目

**测试重点：** 用每种模板构造的 je_lines 逐步通过 5 步校验，检查是否有构造与校验之间的不一致。特别关注 Step 5 中 HST 科目名称在构造和校验之间是否完全一致。

### 2.4 调用方差异（Spec §6）

5 个调用方统一调用 build_je_lines.py + validate_je：

- [ ] Node 1（Profile 匹配）：hst = "internal_transfer"，classification.account 的取值来源是什么？
- [ ] Node 2（Rules 匹配）：classification 来自 rule 的 account + hst 字段
- [ ] Node 3（置信度分类器）：classification 来自 AI 输出
- [ ] Coordinator Agent：classification 来自 accountant 确认
- [ ] 审核 Agent：classification 来自 accountant 修正

**测试重点：** 各调用方传入 build_input 的格式是否一致？特别是 internal_transfer 场景下 classification.account 字段的含义是否与其他模板不同。

### 2.5 错误处理（Spec §5）

- [ ] 校验失败 → 返回 invalid + 所有不通过的校验项列表
- [ ] 调用方不应将校验失败的 JE 写入 Transaction Log
- [ ] **调用方职责**（validate_je 不管的）：account 是否在 COA 中、HST 金额计算是否正确、交易方向是否正确

**测试重点：** 故意构造不合规的 je_lines，验证 validate_je 是否能捕获所有异常。调用方职责中列出的三项，是否在上游确实有人检查？

---

## 第三步：执行测试

**输入：所有已分类交易（来自 Node 1/2/3 的高置信度分类结果）**

{{transactions}}

**客户上下文（Profile + COA）：**

{{client_context}}

请逐笔交易按上述功能逻辑走查：

1. 按 build_je_lines.py 的 7 步逻辑模拟构造 je_lines
2. 将构造结果传入 validate_je 的 5 步校验
3. 记录：通过 / 失败 + 失败原因
4. 检查构造与校验之间是否存在逻辑矛盾

---

## 第四步：输出结果

请严格按照以下格式输出：

```
## JE Generator — 分析结果

### 0. 处理统计
- 接收: N 笔
- 本节点处理: M 笔
- 传递给下一节点: K 笔

### 1. 处理结果
[逐笔交易的 JE 构造模拟 + validate_je 校验结果]

### 2. 传递给下一节点
[通过校验的交易及其 je_lines，供输出报告使用]

### 3. 发现的 Bug
[使用 JE-xxx 编号]

### 4. 接口问题
[从上游节点接收的分类数据中发现的问题]

### 5. Spec 歧义
[je_generator_spec 中描述模糊的地方]

### 6. 备注
[其他观察]
```
