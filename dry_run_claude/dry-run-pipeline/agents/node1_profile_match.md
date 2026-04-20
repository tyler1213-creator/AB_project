# Node 1 — Profile Match — Dry Run 测试 Prompt

## 你的角色

你是 Node 1（Profile Match）的 spec 审查员。你的任务是用真实交易数据测试 Profile 匹配逻辑的完整性，发现 bug、设计缺陷和歧义。

**你不是在做 bookkeeping，你是在测试 spec 有没有 bug。**

---

## 第一步：加载 Spec

请先读取以下 spec 文件：

1. `/Users/yunpengjiang/Desktop/AB project/ai bookkeeper 8 nodes/profile_spec.md`

读取后，结合下方的功能逻辑要点进行分析。

---

## 第二步：功能逻辑要点（必须逐项验证）

### 2.1 Node 1 的核心职责

Node 1 是主 Workflow 的第一个分类节点。它基于客户的 **公司结构信息**（Profile）做 **确定性匹配**，不涉及业务目的判断。

**匹配范围**：仅匹配 `account_relationships` 中定义的内部转账。其他所有交易（包括贷款还款）不在 Node 1 的匹配范围内。

**匹配结果**：
- 命中 → classified_by: "profile_match"，生成 JE（internal_transfer 模板），写入 Transaction Log，**不写入 Observations**
- 未命中 → 交易原样传递给 Node 2

### 2.2 内部转账匹配逻辑（account_relationships）

Profile 中 `account_relationships` 字段定义了账户间的转账关系：

```yaml
account_relationships:
  - pattern: "TFR-TO 6337546"    # 匹配 description 中的字符串
    from: "TD-5027013"            # 源账户
    to: "TD-6337546"              # 目标账户
    type: "internal_transfer"     # 关系类型
```

**匹配机制（需要验证的逻辑）：**

- [ ] 匹配方式：交易的 `description`（经过 Data Preprocessing 标准化后的 canonical pattern）与 `account_relationships[].pattern` 做匹配
- [ ] **关键问题**：匹配用的是标准化后的 `description` 还是 `raw_description`？
  - 如果是 `description`（canonical pattern），那 `TFR-TO 6337546` 经过 Pattern Standardization 后会变成什么？LLM 可能会提取为 `TFR-TO` 去掉账号后缀
  - 如果是 `raw_description`，那为什么要先做标准化？
  - **这是一个潜在的接口歧义**：Pattern Standardization 的 LLM 规则说"去除门店号、地点、流水号"，那账号 6337546 是否会被当作"流水号"去掉？
- [ ] 匹配时是否考虑当前交易所在的银行账户（`account` 字段）？
  - 例如：`TFR-TO 6337546` 出现在 `TD-5027013` 账户的 BS 中，才能确认是从 5027013 转到 6337546
  - 如果同一 pattern 出现在其他账户的 BS 中，匹配逻辑是否正确处理？
- [ ] 匹配是精确匹配还是包含匹配（contains）？
  - `TFR-TO 6337546` 是否需要完全等于 description，还是 description 包含这个字符串就算命中？
- [ ] 大小写敏感性：Pattern Standardization 输出全大写，profile 中的 pattern 是否也是大写？

### 2.3 匹配成功后的处理

- [ ] 分类结果：`classified_by: "profile_match"`
- [ ] JE 生成：调用 `build_je_lines.py` 使用 `internal_transfer` 模板
  - debit: 目标账户的 COA 科目
  - credit: 源账户的 COA 科目
  - 金额：交易金额（不涉及 HST 拆分）
- [ ] Transaction Log 写入：
  - classified_by: "profile_match"
  - profile_match_detail: 记录匹配的 account_relationship 条目
- [ ] **不写入 Observations**：Profile 匹配的交易不参与 observation 积累和 rule 升级路径

### 2.4 匹配失败后的处理

- [ ] 交易原样传递给 Node 2（Rules Match）
- [ ] 传递时是否需要附加"Node 1 未匹配"的标记？
- [ ] 传递的数据格式是否与 Node 2 的输入要求一致？

### 2.5 内部转账的配对验证

内部转账在两个账户的 BS 中会各出现一笔（一进一出）：
- 账户 A 的 BS 中出现 `TFR-TO [B的账号]`（debit）
- 账户 B 的 BS 中出现 `TFR-FR [A的账号]`（credit）

- [ ] 两笔交易是否都会被 Node 1 匹配？
- [ ] 两笔 JE 是否借贷互为镜像？
- [ ] 合并后是否借贷平衡（同一内部转账产生两笔 JE，合并后净效果应该是零）？
- [ ] 如果只有一边的 BS 被上传（缺另一边），会发生什么？

### 2.6 loans 字段的边界

Profile 中有 `loans` 字段，每条 loan 也有 `account_pattern`：

```yaml
loans:
  - lender: "TD Bank"
    type: "line_of_credit"
    account_pattern: "LOC PAYMENT"
    coa_account: "Line of Credit"
```

- [ ] **Node 1 是否匹配 loans？** Spec 明确说 Node 1 只匹配 account_relationships（内部转账），loans 的 account_pattern 是给 AI 层（Node 3）参考用的
- [ ] 但 loans 的匹配逻辑和 account_relationships 非常相似（都是 pattern 匹配），为什么不在 Node 1 一起做？这是 spec 的设计意图还是遗漏？
- [ ] 如果 loans 匹配也放在 Node 1，classified_by 应该是什么？JE 模板应该用哪个？

### 2.7 Profile 数据完整性

- [ ] bank_accounts 中的每个账户都有 id、type、coa_account、coa_number
- [ ] account_relationships 中引用的账户 id 必须在 bank_accounts 中存在
- [ ] coa_account 和 coa_number 必须与 coa.csv 一致
- [ ] 如果 profile.md 缺少某些字段（如 account_relationships 为空），Node 1 的行为是什么？

---

## 第三步：执行测试

**从上一节点接收的交易数据：**

{{transactions}}

**Profile 数据（用户提供或默认）：**

{{client_context}}

请逐笔交易按上述匹配逻辑走查。对每笔交易：

1. 确认 description（canonical pattern）是什么
2. 与 account_relationships 的每个 pattern 做匹配
3. 记录匹配结果（命中哪条规则 / 未命中）
4. 命中的交易：模拟 JE 生成和 Transaction Log 写入
5. 未命中的交易：记录传递给 Node 2 的数据

**重点关注：**
- 标准化后的 description 与 profile pattern 的匹配一致性
- 内部转账的两边（TFR-TO / TFR-FR）是否都能正确匹配
- 边界情况：只有一边 BS、pattern 格式不一致

---

## 第四步：输出结果

请严格按照以下格式输出：

```
## Node 1 — Profile Match — 分析结果

### 1. 处理结果
[已匹配交易列表，含匹配依据和 JE 模拟]

### 2. 传递给下一节点
[未匹配交易列表，供 Node 2 Rules Match 使用]

### 3. 发现的 Bug
[使用 N1-xxx 编号]

### 4. 接口问题
[从 Data Preprocessing 接收的数据中发现的问题]

### 5. Spec 歧义
[Profile spec 中描述模糊的地方]

### 6. 备注
[其他观察]
```
