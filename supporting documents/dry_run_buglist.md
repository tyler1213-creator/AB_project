# Phase 0 Dry Run — Active Bug List

---

只保留**当前仍未解决**、且仍影响系统设计 / 接口契约的真实问题。

已解决并从本清单移除的历史项：

- `BUG-003`：Output Report / Review Agent 的 `report_draft` 时序冲突
- `BUG-004`：HST 控制科目命名与 revenue 校验不一致
- `BUG-005`：`owner_uses_company_account` 对零售类 vendor 的高置信度限制过于绝对
- Pattern Standardization 的 Layer 3 文档补全项

---

## BUG-001: CHQ 交易的 pattern 标准化仍会丢失收款人语义

**归属：** Data Preprocessing Agent / Pattern Standardization  
**严重程度：** 高  
**状态：** 未解决

### 问题本质

当前 `standardize_description` 的接口仍以：

```python
standardize_description(raw_description, client_id)
```

为准，只吃银行流水原始描述，不吃已经在预处理前一步拿到的 `cheque_info`。

而支票交易的 `raw_description` 往往只有：

- `CHQ#000176`
- `CHQ#000245`

这类字符串本身不包含真正有业务意义的收款人信息。  
所以即使 Step 3 已经从 cheque image 提取到了：

- `payee`
- `memo`
- `cheque_number`

Step 5 在做 pattern 标准化时也用不上这些信息，最终只能把 canonical pattern 压成 `CHQ`。

### 为什么这是系统级 bug

这个问题不是“某笔交易分类不准”那么简单，而是**学习主键被破坏**。

本系统后续多个节点都把 `description` / canonical pattern 当成统一锚点：

- Observations 按 `(pattern, direction)` 聚合
- Rules 按 pattern 匹配
- Node 3 按 pattern 查 observation 历史
- Coordinator 按 pattern 归组展示 PENDING

如果所有支票都共享同一个 pattern = `CHQ`，那系统相当于失去了“这张支票到底付给谁”的结构化记忆。

### 当前错误链条

1. cheque image processing 已经拿到 `cheque_info.payee`
2. description standardization 仍只看 `raw_description`
3. canonical pattern 被压成 `CHQ`
4. 所有支票支出被聚合到同一 observation：`(CHQ, debit)`
5. `classification_history` 混入多个完全不同的收款人和科目
6. observation 变成脏聚合，通常只能走 `non_promotable: true`
7. 规则学习路径和高置信度历史参考同时失效

### 影响范围

1. **Observations 被污染**
   同一条 `(CHQ, debit)` observation 会混入 subcontractor、rent、loan payment、owner draw 等完全不同语义。

2. **Rules 无法建立**
   因为根本没有稳定的“支票收款人 pattern”，Node 2 无法为不同 payee 建独立 rule。

3. **Node 3 历史参考失真**
   AI 查询到的 observation 历史不是某个 payee 的历史，而是一坨所有支票的混合历史。

4. **Coordinator 分组无意义**
   PENDING 若按 `CHQ` 归组，会把不同收款人的支票错误地放在一起，降低 accountant 处理效率。

5. **支票学习路径被切断**
   无法形成有意义 observation
   → 无法升级 rule
   → 永远依赖 AI / 人工。

### 触发条件

- Data Preprocessing Step 3 已经提取并写入 `cheque_info`
- Step 5 仍调用 `standardize_description(raw_description, client_id)`
- `standardize_description` contract 没有 `cheque_info` 输入位

### 当前相关 spec 现状

- [tools/pattern_standardization_spec.md](/Users/yunpengjiang/Desktop/AB%20project/tools/pattern_standardization_spec.md) 目前接口仍只接 `raw_description, client_id`
- [ai bookkeeper 8 nodes/data_preprocessing_agent_spec_v3.md](/Users/yunpengjiang/Desktop/AB%20project/ai%20bookkeeper%208%20nodes/data_preprocessing_agent_spec_v3.md) 已明确 Step 3 先得到 `cheque_info`，Step 5 再做标准化

### 需要解决的设计决策

真正还没定死的不是“要不要修”，而是**怎么把 cheque 语义喂给 pattern 标准化，同时不破坏现有 pattern dictionary contract**。

至少需要明确：

1. `standardize_description` 是否要新增可选输入 `cheque_info`
2. 当存在 `cheque_info.payee` 时，canonical pattern 的提取基础是否应改为 `payee`
3. `memo` 是否只作为辅助解释，还是也允许参与 canonical pattern 生成
4. payee 是否需要先做最小归一化，再写入 Pattern Dictionary

### 当前建议方向

优先方向仍是：

- `standardize_description` 增加可选 `cheque_info`
- 当 `cheque_info.payee` 存在时，以 payee 为主语义来源生成 canonical pattern
- `memo` 仅作为辅助 disambiguation，不默认进入 canonical pattern

这样至少能让支票交易重新获得稳定、可学习的 pattern 主键。

---

## BUG-002: Node 1 内部转账匹配读取哪个字段，跨节点 contract 仍未定

**归属：** Profile / Data Preprocessing / Pattern Standardization / Node 1  
**严重程度：** 高  
**状态：** 未解决

### 问题本质

当前 Profile 中的 `account_relationships.pattern` 写法像：

- `TFR-TO 6337546`
- `TFR-FR 6337546`

这明显是**基于银行原始流水字符串**定义的匹配模式。  
但 Data Preprocessing 在进入主 workflow 前，会把交易标准化为：

- `description`：canonical pattern，供下游默认消费
- `raw_description`：仅保留原文，不作为默认确定性匹配字段

于是 contract 就卡住了：

Node 1 识别内部转账时，到底应该匹配哪一个？

- `raw_description`
- `description`
- 还是一个专门给 transfer 保留的中间字段

现在这个问题还没有被系统级写死。

### 为什么这是跨节点 contract 问题

这不是 Node 1 自己能局部补丁修掉的事，因为它同时牵涉四层定义：

1. Profile 里 `account_relationships.pattern` 的语义是什么
2. Pattern Standardization 输出的 `description` 语义是什么
3. Data Preprocessing 应该把什么字段传给 Node 1
4. Node 1 的确定性匹配究竟面向“原始银行信号”还是“canonical pattern”

如果这四个地方口径不统一，Node 1 的内部转账识别一定会飘。

### 当前错误风险

如果 Node 1 误读 `description`：

- 原始银行特有的转账信号可能在标准化过程中被压平
- `account_relationships.pattern` 将无法稳定命中

如果 Node 1 继续硬读 `raw_description`：

- 那就等于 Node 1 成了例外节点，不再遵循“下游默认消费 canonical description”的主 contract
- Profile 里的 `account_relationships.pattern` 也会继续绑定银行原文格式，迁移成本高

所以真正的问题不是“哪个字段更顺手”，而是**内部转账匹配到底属于原始银行信号匹配，还是 canonical pattern 匹配**。

### 影响范围

1. **Node 1 无法稳定识别内部转账**
   该拦住的 internal transfer 可能直接穿透到 Node 2 / Node 3。

2. **下游会把内部转账当普通收支处理**
   这会污染规则学习、AI 分类和 accountant review 路径。

3. **JE 生成逻辑会出错**
   internal transfer 需要基于两个银行账户关系生成对应分录，和普通 expense / revenue 不是同一语义。

4. **Profile contract 不稳定**
   `account_relationships.pattern` 这个字段到底在表达“原始银行字符串”还是“标准化后的 pattern”，现在文档还没有统一。

### 当前相关 spec 现状

- [ai bookkeeper 8 nodes/profile_spec.md](/Users/yunpengjiang/Desktop/AB%20project/ai%20bookkeeper%208%20nodes/profile_spec.md) 目前把 `account_relationships.pattern` 写成类似原始银行字符串
- [ai bookkeeper 8 nodes/data_preprocessing_agent_spec_v3.md](/Users/yunpengjiang/Desktop/AB%20project/ai%20bookkeeper%208%20nodes/data_preprocessing_agent_spec_v3.md) 明确会输出 `description` 和 `raw_description`
- [tools/pattern_standardization_spec.md](/Users/yunpengjiang/Desktop/AB%20project/tools/pattern_standardization_spec.md) 又明确说明 `description` 是下游默认消费字段，而 `raw_description` 不作为默认确定性匹配字段

### 当前待决策的方案空间

现在至少有三条可选路线，需要明确选一条：

#### 方案 A：Node 1 继续匹配 `raw_description`

优点：

- 最贴近现有 `account_relationships.pattern` 写法
- 对 transfer 类银行特有字符串最直接

代价：

- Node 1 成为下游里的“特殊节点”
- `raw_description` 虽然被说成不是默认确定性匹配字段，但这里又变成关键匹配字段，contract 会变得例外化

#### 方案 B：把 `account_relationships.pattern` 改成 canonical pattern，Node 1 匹配 `description`

优点：

- 整体 contract 更统一
- Node 1 和其他节点都围绕 canonical pattern 工作

代价：

- 需要先证明 transfer 信号在标准化后仍足够稳定、可区分
- 现有 Profile 里的写法和未来迁移策略都要重写

#### 方案 C：新增 transfer 专用匹配字段

例如保留一个专门表达“银行原始转账信号”的字段，Node 1 专门读它。

优点：

- 语义最清晰：`description` 管业务聚合，transfer_signal 管内部转账匹配

代价：

- 共享 transaction contract 会再多一个字段
- 需要改上游输出、Node 1 输入、Profile 定义和 dry run pack

### 当前建议方向

这个问题现在仍不适合局部拍脑袋修。  
更合理的下一步是先在 contract 层明确一句话：

“Node 1 的 internal transfer 匹配，究竟是 canonical-pattern 语义，还是 bank-raw-signal 语义？”

这句话一旦定了，后面才知道该改：

- Profile 的 `account_relationships.pattern`
- Data Preprocessing 输出字段
- Pattern Standardization contract
- Node 1 匹配逻辑

在这句话没定之前，继续局部改某一份 spec 只会制造新的不一致。
