# standardize_description — Pattern 标准化工具

---

## 1. 职责定义

将银行流水的原始 description 转化为稳定、可聚合的 canonical pattern，供下游所有节点使用。

**核心思想：用 LLM 做理解，用字典做确定性。理解一次，缓存永久。**

这是整个系统学习能力的基础：Observations 按 pattern 聚合，Rules 按 pattern 匹配，置信度分类器按 pattern 查找历史，Coordinator 按 pattern 分组 PENDING 交易。Pattern 不稳定，一切下游匹配都会断裂。

---

## 2. 接口

```python
def standardize_description(raw_description: str, client_id: str) -> dict:
    """
    Returns:
        {
            "description": str,        # canonical pattern（写入交易数据的 description 字段）
            "raw_description": str,    # 银行原始描述，原样保留
            "cleaned_fragment": str,   # Layer 1 预清洗输出（字典 key，不传递给下游节点）
            "source": str,             # "dictionary_hit" | "llm_extraction" | "fallback"
        }
    """
```

| 返回字段 | 下游用途 |
|----------|---------|
| `description` | 所有下游节点（Node 1/2/3、Coordinator、Observations、Rules、Transaction Log、输出报告）消费的 canonical pattern |
| `raw_description` | Transaction Log 第一层存档、数据预处理 Agent 摘要 |
| `cleaned_fragment` | 仅用于工具内部字典查找，不传递给下游节点 |
| `source` | 仅用于监控和调试，不传递给下游节点 |

---

## 3. 三层管线

```
raw_description → [Layer 1: 最小确定性预清洗] → cleaned_fragment（字典 key）
                  → [Layer 2: Pattern Dictionary 精确查找]
                     → 命中 → 返回 canonical pattern
                     → 未命中 → [Layer 3: LLM 提取（传全量已知 pattern 列表）]
                                → 返回 pattern + 写入字典缓存
                                → LLM 不可用 → 降级：用 cleaned_fragment 作临时 pattern
                                               标记 source: "fallback"，后续可修正
```

### Layer 1：最小确定性预清洗

**只去除银行系统自动添加的交易方式前缀。** 这些前缀是银行元数据，不是商户身份的一部分，且同一商户可能因支付方式不同带不同前缀。

```python
KNOWN_PREFIXES = [
    "INTERAC PURCHASE", "INTERAC E-TRANSFER", "INTERAC ETRANSFER",
    "POS PURCHASE", "POS",
    "PRE-AUTHORIZED DEBIT", "PRE-AUTHORIZED CREDIT", "PAD",
    "ELECTRONIC FUNDS TRANSFER", "EFT",
    "BILL PAYMENT", "BILL PMT",
    "WIRE TRANSFER", "WIRE",
    "DIRECT DEPOSIT", "DIR DEP", "MOBILE DEPOSIT",
    # 各银行特有前缀（TD、BMO、RBC 等，按需扩充）
]

def pre_clean(raw_description):
    text = raw_description.strip().upper()
    text = " ".join(text.split())          # 多空格合一
    for prefix in KNOWN_PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
            break                           # 只去一个前缀，不递归
    return text
```

**不做的事：** 不去门店号、不去城市名、不去省份/国家代码、不做任何商户名归一化。全部留给 LLM。

### Layer 2：Pattern Dictionary 精确查找

用 cleaned_fragment 作为 key 在字典中做精确查找。命中则直接返回 canonical_pattern，不调用 LLM。

### Layer 3：LLM Pattern 提取

**输入：**
- `raw_description`：原始银行流水描述
- `cleaned_fragment`：Layer 1 预清洗后的字符串
- `existing_patterns: [...]`：全量已知 pattern 列表（从 Pattern Dictionary 提取所有唯一 canonical_pattern 值）

**不做预过滤，直接传全量列表。** 一个客户稳态 200-300 个 pattern，约 1000-1500 tokens，对 LLM 来说很小。预过滤会引入漏召回风险（如 `AMZN MKTP` 无法通过 token 匹配找到 `AMAZON MARKETPLACE`），而 LLM 看到完整列表可以凭语义理解识别缩写/变体。

**LLM 指令要点：**

1. 提取商户/实体名称，去除门店号、地点、流水号
2. 如果明确是已知 pattern 的变体（包括缩写、别名），返回该已知 pattern 的精确字符串
3. **默认保留服务区分**：`ROGERS WIRELESS` 和 `ROGERS CABLE` 是两个不同 pattern（accountant 如需合并通过审核 Agent 操作）
4. 支付处理器保留前缀：`SQ *LOCAL COFFEE` → `SQ *LOCAL COFFEE`
5. 泛型描述原样返回：`DEPOSIT` → `DEPOSIT`
6. 政府机构保留用途区分：`CRA FED TAX` → `CRA FEDERAL TAX`

---

## 4. Pattern Dictionary（内部存储）

存储 cleaned_fragment → canonical_pattern 的映射，保证同一 cleaned_fragment 永远返回同一 pattern。

**存储位置：** `{client_dir}/pattern_dictionary.db`（每客户独立，SQLite）

```sql
CREATE TABLE pattern_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cleaned_fragment TEXT NOT NULL UNIQUE,    -- Layer 1 预清洗后的完整字符串，字典 key
    canonical_pattern TEXT NOT NULL,          -- 标准化后的商户/实体名称
    source TEXT NOT NULL,                     -- 条目来源（见下方取值表）
    created_date TEXT NOT NULL,               -- 条目创建日期，YYYY-MM-DD
    raw_description_sample TEXT               -- 原始 description 样本，便于人工审查
);

CREATE INDEX idx_cleaned_fragment ON pattern_entries(cleaned_fragment);
CREATE INDEX idx_canonical_pattern ON pattern_entries(canonical_pattern);
CREATE INDEX idx_source ON pattern_entries(source);
```

#### source 字段取值

| 值 | 含义 |
|---|---|
| `llm_extraction` | 运行时 LLM 提取并缓存 |
| `onboarding_historical` | Onboarding 阶段从历史数据提取 |
| `accountant_override` | Accountant 通过审核 Agent 手动指定 |
| `fallback` | LLM 不可用时用 cleaned_fragment 临时充当 pattern |

#### 字典 key 说明

key = cleaned_fragment（完整字符串）。同一商户不同门店会产生不同 key，这是预期行为：

```
"HOME DEPOT 4521 TORONTO ON"     → "HOME DEPOT"
"HOME DEPOT 8823 MISSISSAUGA ON" → "HOME DEPOT"
"HOME DEPOT 2201 OTTAWA ON"      → "HOME DEPOT"
```

企业交易模式高度重复——总在同样几家门店消费。银行对同一门店的 raw_description 是确定的。Onboarding 处理 6-12 个月历史后，绝大多数高频 description 已被缓存。字典命中率按交易量衡量，不是按唯一商户数。

#### 生命周期预期

| 阶段 | 字典条目数 | LLM 调用 |
|------|-----------|---------|
| Onboarding（历史数据） | 100-300 条 | 5-15 次批量调用 |
| 月度运行（前期） | +5-20 条 | 5-20 次 |
| 月度运行（稳态） | +0-5 条 | 趋近于零 |

条目只增不删（除非 accountant 通过审核 Agent 发起 pattern 变更操作）。

---

## 5. 错误处理

**LLM 不可用时（timeout / rate limit / 格式错误）：** 用 cleaned_fragment 作临时 pattern，标记 `source: "fallback"`，不阻塞流程。

后续批量修正：遍历 pattern_entries 筛选 `source = 'fallback'`，LLM 恢复后重新提取并更新条目。

---

## 6. 被谁调用

| 调用方 | 调用时机 | 操作 |
|--------|---------|------|
| 数据预处理 Agent | 每笔交易标准化时 | 查找 + 缓存新条目（Layer 2 未命中时） |
| Onboarding Agent | 初始化阶段批量处理历史数据 | 批量写入初始条目（每批 10-20 条发送 LLM） |
| 审核 Agent | Accountant 请求合并/重命名/拆分 pattern 时 | 读取受影响的 cleaned_fragment，修改 canonical_pattern |

#### Pattern 变更的下游 Migration

当 accountant 通过审核 Agent 发起 pattern 变更时：

```
1. 更新 Pattern Dictionary（修改相关条目的 canonical_pattern）
2. 更新 Transaction Log（description 字段替换为新 pattern，分类信息不变）
3. 删除受影响的 observation 记录
4. 从 Transaction Log rebuild observations（按 description + direction 重新聚合）
5. 更新 Rules 中引用旧 pattern 的 rule
6. 记录 intervention log
```

支持的变更操作：合并（ROGERS WIRELESS + ROGERS CABLE → ROGERS）、重命名（AMZN MKTP → AMAZON）、拆分（ROGERS → ROGERS WIRELESS + ROGERS CABLE）。

---

## 7. 文件位置

```
tools/
  standardize_description.py        # 主模块，三层管线
  pre_clean.py                      # Layer 1 逻辑
  pattern_dictionary_db.py          # SQLite 读写封装
  references/
    transaction_prefixes.yaml       # 银行前缀列表（供 pre_clean.py 读取）
```
