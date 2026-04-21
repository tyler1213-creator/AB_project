# transaction_identity_and_dedup — 交易身份与去重工具

---

## 1. 职责定义

为每个原始导入文件和每笔原始交易分配稳定身份，并在进入主 Workflow 之前完成入口层去重。

这个工具解决两个不同问题：

1. **文件级去重**：这是不是一份已经导入过的原始文件
2. **交易身份分配**：这笔原始交易是否之前已经进入过系统；如果进入过，应复用原有 `transaction_id`

它不是主 Workflow 节点，因为它不做会计判断、不做分类，也不参与 Node 1/2/3 的路由。它是 Data Preprocessing 上游的共享基础设施，负责为后续所有节点提供稳定的交易对象身份。

---

## 2. 接口

```python
def register_ingestion_file(file_bytes: bytes, client_id: str, file_name: str) -> dict:
    """
    Returns:
        {
            "file_hash": str,              # SHA-256(file_bytes)
            "is_duplicate_file": bool,     # 是否为完全相同的已导入文件
        }
    """


def assign_transaction_identity(client_id: str, transaction: dict) -> dict:
    """
    transaction 必需字段：
        bank_account, date, direction, amount, raw_description?, balance?

    Returns:
        {
            "transaction_id": str,         # txn_<ULID>
            "dedupe_fingerprint": str,     # 去重指纹
            "is_duplicate_transaction": bool,
        }
    """
```

### 返回字段用途

| 字段 | 用途 |
|------|------|
| `file_hash` | 写入导入登记表，用于文件级去重 |
| `is_duplicate_file` | 命中时整份文件不再继续解析和入池 |
| `transaction_id` | 下游所有节点统一引用的稳定交易标识 |
| `dedupe_fingerprint` | 交易级去重键，仅供入口层与 registry 使用 |
| `is_duplicate_transaction` | 命中时复用原有 `transaction_id`，并跳过重复交易的后续处理 |

### `dedupe_fingerprint` 定义

V1 只定义一个 `dedupe_fingerprint`，避免多层规则造成灰区。

字段来源遵循“入口层稳定、解析前置、最少依赖下游语义”的原则：

- `client_id`
- `bank_account`
- `date`
- `direction`
- `amount_abs`
- `balance`（仅当该来源稳定提供时纳入）

**不纳入 V1 fingerprint 的字段：**

- `description`（canonical pattern）
- `pattern_source`
- `raw_description`（parser / OCR 差异过大，只作为人工排查辅助信息）

哈希算法统一使用 `SHA-256`。字段序列化顺序必须固定，例如：

```text
client_id|bank_account|date|direction|amount_abs|balance_or_empty
```

---

## 3. 内部实现

### 3.1 文件级去重

```
原始文件进入系统
  → 读取 file_bytes
  → 计算 file_hash = SHA-256(file_bytes)
  → 查询 processed_files
    → 命中 → 标记 duplicate_file，整份文件停止进入后续流程
    → 未命中 → 允许继续解析
```

### 3.2 交易身份分配

```
文件解析完成，得到原始交易候选
  → 先完成入口层字段归一化
     - bank_account 映射到 profile.bank_accounts[].id
     - amount 统一为绝对值
     - direction 统一为 debit / credit
     - date 统一为 YYYY-MM-DD
  → 计算 dedupe_fingerprint
  → 查询 ingested_transactions
    → 命中 → 复用已有 transaction_id，并将当前交易标记为 duplicate_transaction
    → 未命中 → 生成新的 transaction_id = "txn_" + ULID
               写入 registry
```

### 3.3 `transaction_id` 生成原则

- `transaction_id` 是**永久对象主键**，不是由业务字段反复重算的确定性字符串
- 它在交易首次 ingest 时生成一次，此后永远复用
- 推荐格式：`txn_<ULID>`
- 推荐示例：`txn_01JVF8Y7T6M3K2N9Q4R5S8W1XZ`

采用 ULID 的原因：

- 唯一性高
- 按时间近似有序，便于日志与排查
- 与业务字段解耦，不受 parser 规则变动影响

---

## 4. 内部存储

每个客户一个轻量 SQLite：

```text
{client_dir}/ingestion_registry.db
```

### 表 1：`processed_files`

```sql
CREATE TABLE processed_files (
    file_hash TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    status TEXT NOT NULL
);
```

用途：记录哪些原始文件已经导入过。

### 表 2：`ingested_transactions`

```sql
CREATE TABLE ingested_transactions (
    transaction_id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    bank_account TEXT NOT NULL,
    date TEXT NOT NULL,
    direction TEXT NOT NULL,
    amount_abs REAL NOT NULL,
    balance REAL,
    dedupe_fingerprint TEXT NOT NULL UNIQUE,
    source_file_hash TEXT NOT NULL,
    first_seen_at TEXT NOT NULL
);

CREATE INDEX idx_ingested_transactions_fingerprint
ON ingested_transactions(dedupe_fingerprint);
```

用途：

- 记录已见过的原始交易
- 维护 `dedupe_fingerprint -> transaction_id` 的持久映射

### 读写边界

- **允许读写**：Data Preprocessing / Ingestion 层
- **禁止读取作为业务判断依据**：Node 1 / Node 2 / Node 3 / Coordinator / Review / Transaction Log

### 生命周期

- 与审计链保持一致，建议与 Transaction Log 同档保留
- 不作为 accountant 日常查看对象
- 仅在导入、重跑、问题排查时被技术层使用

---

## 5. 错误处理

### 文件级重复

- 命中 `processed_files.file_hash`
- 整份文件停止进入后续流程
- 在预处理摘要中记录“重复文件已跳过”

### 交易级重复

- 命中 `ingested_transactions.dedupe_fingerprint`
- 复用已有 `transaction_id`
- 当前批次中的重复交易不再进入 Pattern Standardization 和后续节点
- 在预处理摘要中记录“重复交易已跳过”

### 指纹必需字段缺失

- 若无法得到 `bank_account / date / direction / amount_abs` 中任一关键字段
- 不生成 `transaction_id`
- 该交易标记为预处理异常，进入待人工确认清单

### Registry 不可用

- 视为阻断级错误
- 不允许继续进入主 Workflow
- 原因：没有稳定身份分配，就无法保证 split / review / audit chain 的一致性

---

## 6. 被谁调用

| 调用方 | 调用时机 | 操作 |
|--------|---------|------|
| Data Preprocessing Agent | 原始文件进入系统后、解析前 | 计算 `file_hash`，执行文件级去重 |
| Data Preprocessing Agent | 文件解析完成、字段归一化后、description 标准化前 | 计算 `dedupe_fingerprint`，分配或复用 `transaction_id` |

调用顺序：

```
原始文件
  → file_hash 去重
  → 解析为原始交易
  → 入口层字段归一化
  → 交易身份分配 / 交易级去重
  → description 标准化
  → Node 1 / Node 2 / Node 3 ...
```

---

## 7. 文件位置

```text
tools/
  transaction_identity_and_dedup_spec.md   # 本规格
  transaction_identity.py                  # 主模块（file_hash / dedupe_fingerprint / transaction_id 分配）
  ingestion_registry_db.py                 # SQLite 读写封装
```
