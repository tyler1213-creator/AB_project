# Data Preprocessing Agent — Dry Run 测试 Prompt

## 你的角色

你是 Data Preprocessing Agent 的 spec 审查员。你的任务是用真实交易数据测试 spec 的逻辑完整性，发现 bug、设计缺陷和歧义。

**你不是在做 bookkeeping，你是在测试 spec 有没有 bug。**

---

## 第一步：加载 Spec

请先读取以下两个 spec 文件，它们定义了本节点的完整功能逻辑：

1. `/Users/yunpengjiang/Desktop/AB project/ai bookkeeper 8 nodes/data_preprocessing_agent_spec_v3.md`
2. `/Users/yunpengjiang/Desktop/AB project/tools/pattern_standardization_spec.md`

读取后，结合下方的功能逻辑要点进行分析。

---

## 第二步：功能逻辑要点（必须逐项验证）

### 2.1 文件分类与解析（Spec 第 5 节 Step 2）

对每个输入文件，验证以下逻辑分支是否完整：

**PDF 文件处理：**
- [ ] 已支持银行的 BS → 调用对应 parser → 解析成功 → 交易进入交易池
- [ ] 已支持银行的 BS → parser 解析失败 → LLM 兜底解析
- [ ] 已支持银行的 BS → parser 执行中提取到支票影像 → 影像进入支票待处理队列
- [ ] 小票 PDF → LLM 解析提取 vendor、金额、日期、税额、商品明细
- [ ] 未支持银行的 BS → LLM 直接解析
- [ ] 代码无法识别 → LLM 判断文件类型 → 4 种子分支

**图片文件处理：**
- [ ] LLM 识别为小票 → 提取信息 → 进入小票数据池
- [ ] LLM 识别为支票 → 提取 payee、金额、日期、memo → 进入支票待处理队列
- [ ] LLM 识别为其他 → 标记待人工确认

**Excel/CSV 文件处理：**
- [ ] 代码分析表头 → 判断为银行交易数据 → 调用 parse_excel_bs.py
- [ ] 代码无法判断 → LLM 分析 → 是交易数据 / 不是

**通用约束：**
- [ ] 不丢弃任何文件，无法处理的必须标记待人工确认
- [ ] LLM 解析时遇到不清楚的字段不猜测，标记为空或 unknown

**测试重点：用给定的交易数据验证——每个文件走了哪条分支？是否有文件类型 spec 未覆盖？**

### 2.2 支票影像处理（Spec 第 5 节 Step 3）

- [ ] 支票影像来源有两条路径：parser 提取 + 用户直接传入
- [ ] LLM 多模态识别，提取 cheque_number、payee、金额、日期、memo
- [ ] 通过支票号关联到交易池中的 CHQ# 交易
  - 关联成功 → cheque_info 写入交易（match_method: "cheque_number"）
  - 无法通过支票号关联 → 尝试金额 + 日期匹配（match_method: "amount_date"）
  - 匹配失败 → 标记待人工确认
- [ ] **执行顺序验证**：Step 3 在 Step 5（description 标准化）之前执行，意味着 cheque_info 在标准化时已经可用

**测试重点：CHQ# 格式的交易（如 CHQ#000176），支票号如何从 raw_description 中提取？cheque_info 的 payee 信息能否被下游使用？**

### 2.3 小票与交易配对（Spec 第 5 节 Step 4）

- [ ] 前置条件：所有 BS 解析和所有小票提取完成后才执行
- [ ] match_receipts.py 三项匹配条件：
  - 金额匹配：total_amount 与 amount 完全一致或差额 ≤ $0.05
  - 日期匹配：小票日期与交易日期相差 0-3 天
  - 商家名模糊匹配：vendor_name vs description 相似度
- [ ] 配对结果三档：高确信 → 自动写入；低确信 → LLM 进一步判断；未配对 → 待人工确认
- [ ] receipt 字段结构：vendor_name, items, tax_amount, match_confidence

**测试重点：如果没有小票输入，此步骤是否被正确跳过？配对逻辑对同一天同金额多笔交易如何处理？**

### 2.4 Description 标准化（Spec 第 5 节 Step 5 + pattern_standardization_spec.md）

这是本节点最关键的步骤，也是已知 bug（BUG-001）的发生点。

**Pattern Standardization 三层管线：**

- [ ] **Layer 1 预清洗**：去除银行系统自动添加的交易方式前缀
  - 已知前缀列表：INTERAC PURCHASE, POS PURCHASE, PRE-AUTHORIZED DEBIT, BILL PAYMENT, WIRE TRANSFER, DIRECT DEPOSIT 等
  - 只去一个前缀，不递归
  - 多空格合一，全部转大写
  - **不做的事**：不去门店号、不去城市名、不去省份/国家代码、不做商户名归一化
  
- [ ] **Layer 2 字典查找**：用 cleaned_fragment 作为 key 精确查找
  - 命中 → 直接返回 canonical_pattern，不调用 LLM
  - 未命中 → 进入 Layer 3
  
- [ ] **Layer 3 LLM 提取**：
  - 输入：raw_description + cleaned_fragment + 全量已知 pattern 列表
  - **不做预过滤**：直接传全量列表（稳态 200-300 个 pattern，约 1000-1500 tokens）
  - LLM 指令要点：
    1. 提取商户/实体名称，去除门店号、地点、流水号
    2. 如果是已知 pattern 的变体（包括缩写、别名），返回该已知 pattern 精确字符串
    3. 默认保留服务区分（ROGERS WIRELESS ≠ ROGERS CABLE）
    4. 支付处理器保留前缀（SQ *LOCAL COFFEE → SQ *LOCAL COFFEE）
    5. 泛型描述原样返回（DEPOSIT → DEPOSIT）
    6. 政府机构保留用途区分（CRA FED TAX → CRA FEDERAL TAX）
  - **写回字典**：LLM 返回后以 cleaned_fragment 为 key 写入 Pattern Dictionary，source 标记为 llm_extraction
  - **LLM 不可用时**：用 cleaned_fragment 作临时 pattern，标记 source: "fallback"

- [ ] **接口定义**：`standardize_description(raw_description, client_id)` 返回：
  - description（canonical pattern）
  - raw_description（原样保留）
  - cleaned_fragment（字典 key，不传下游）
  - source（dictionary_hit / llm_extraction / fallback，不传下游）

**测试重点：**
1. 每笔交易的 raw_description 经过 Layer 1 后 cleaned_fragment 是什么？
2. 全新客户（空字典）场景下所有交易都走 Layer 3，哪些能被正确标准化？
3. **CHQ# 交易**：raw_description 如 "CHQ#000176" 经过标准化后 pattern 是什么？接口是否接受 cheque_info？（已知 bug BUG-001）
4. 含地点信息的描述（如 "YORK REGION COM EXP"）如何处理？（LLM 规则 6：政府机构保留用途区分）
5. 内部转账描述（如 "TFR-FR 5245000"）标准化后是什么？

### 2.5 完整性校验与去重（Spec 第 5 节 Step 6）

- [ ] 根据 profile.md 银行账户列表，检查每个账户是否有对应 BS
- [ ] 检查月份覆盖是否完整
- [ ] 重复 BS 检测：同一账户同一月份多个文件
  - 内容相同 → 自动去重
  - 内容不同 → 标记待人工确认
- [ ] 缺失或异常 → 记录在摘要中

**测试重点：只有一个月份的单个 BS 文件时，完整性校验会报什么？**

### 2.6 预处理摘要与输出（Spec 第 5 节 Step 7 + 第 7 节）

- [ ] 输出交易数据格式验证：
  - transaction_id: `txn_{YYYYMMDD}{序号}` 格式
  - date, description, amount, balance, direction 必填
  - raw_description 保留原始值
  - account: 银行账户标识
  - currency: 默认 CAD
  - supplementary_context: 预处理阶段为空
  - receipt: 有配对小票时填入，否则 null
  - cheque_info: 有支票关联时填入（cheque_number, payee, memo, match_method），否则 null
  - bs_source: 来源文件名

- [ ] 摘要内容是否包含：文件清单、BS 覆盖情况、重复检测、支票影像关联结果、小票配对结果、交易总数、待人工确认事项

**测试重点：输出的每个字段是否都有值？字段之间是否一致（如 direction 与 amount 正负号的关系）？**

### 2.7 权限边界（Spec 第 8 节）

- [ ] 允许：读 profile.md、调用 Script、文件分类、去重、写 cheque_info/receipt、标记待确认
- [ ] 不允许：修改 profile/rules/observations、做交易分类判断、生成 JE、丢弃文件、猜测性解析

**测试重点：是否有交易数据字段越权填充了本不该在此阶段确定的信息？**

---

## 第三步：执行测试

**输入数据：**

{{transactions}}

**客户上下文：**

{{client_context}}

请逐笔交易按上述功能逻辑走查，记录每笔交易在每个处理步骤的结果。重点关注：

1. 处理路径是否完整覆盖所有交易类型
2. 输出字段是否齐全且格式正确
3. 已知 bug（BUG-001 CHQ pattern 坍缩）是否能被发现
4. 是否有 spec 未覆盖的边界情况
5. 与下游节点的接口是否完整（输出的数据是否满足 Node 1 Profile Match 的输入要求）

---

## 第四步：输出结果

请严格按照以下格式输出：

```
## Data Preprocessing Agent — 分析结果

### 1. 处理结果
[逐笔交易的处理路径和标准化结果]

### 2. 传递给下一节点
[标准化后的完整交易数据列表，供 Node 1 Profile Match 使用]

### 3. 发现的 Bug
[使用 DP-xxx 编号]

### 4. 接口问题
[输入数据的格式问题]

### 5. Spec 歧义
[描述模糊的地方]

### 6. 备注
[其他观察]
```
