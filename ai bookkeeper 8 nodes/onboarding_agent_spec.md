# Onboarding Agent

---

## 1. 职责定义

收集新客户的基础信息和历史交易数据，构建该客户的初始文件集（profile.md / observations.md / rules.md / coa.csv），为主 Workflow 的首次运行提供必要的输入。

Onboarding 是一次性运行的流程。完成初始文件构建后不再参与该客户的后续处理。

**执行方式：** 方式一（问卷收集）涉及自然语言交互，可能需要 LLM 解析回复。方式二（历史数据提取）的核心处理逻辑是代码驱动（确定性），不涉及 LLM 判断——输入是结构化历史账本，处理流程是确定性的解析、聚合、写入。

---

## 2. 触发条件

新客户接入系统时，由产品负责人或 accountant 手动触发。每个客户只运行一次。

---

## 3. 输入

根据信息收集方式的不同，Onboarding Agent 接收两类输入：

### 方式一：问卷收集（无历史数据时）

- Accountant 或客户对问卷问题的回复

### 方式二：历史数据提取（有历史数据时）

- 客户过去由 accountant 做好的历史账本（QBO 导出 / Excel / PDF）
- Accountant 对补充问题的回复（历史数据无法覆盖的信息）

两种方式可以组合使用：先从历史数据中提取能提取的信息，再通过问卷补充缺失项。

---

## 4. 执行流程

### 方式一：问卷收集

```
Step 1: 向 accountant 或客户发送 Onboarding 问卷
Step 2: 接收并解析回复
Step 3: 构建 profile.md
Step 4: 创建空的 observations.md 和 rules.md
Step 5: 从 QBO 导出 COA 存为 coa.csv
```

#### Onboarding 问卷

**必填项（影响系统核心逻辑）：**

1. 公司法律全名
2. 省份（决定 HST 税率）
3. 是否已注册 HST/GST（有 = 拆 HST，无 = 全 exempt）
4. HST/GST 注册号（如已注册）
5. 企业类型（corporation / sole proprietorship）
6. 银行账户列表（银行 + 账号 + 用途）
7. 账户间是否有互相转账（用于构建 account_relationships）

**重要项（影响 AI 判断质量）：**

8. 行业类型
9. 是否有员工（及发薪频率）
10. 老板/股东是否用公司账户做个人交易
11. 是否有贷款或信用额度（贷方 + 类型 + 还款 pattern）

**可选项（提升系统效率但非必需）：**

12. 主要收入付款方式
13. 是否有信用卡需处理

### 方式二：历史数据提取

```
Step 1: 接收并解析历史账本文件
        - 支持格式：QBO 导出（CSV/IIF）、Excel
        - 提取每笔交易的字段：date, description, amount, direction, balance(如有),
          bank_account, account(COA 科目), hst
        - 输出：标准化交易列表（与数据预处理 Agent 输出格式对齐）

Step 2: 从交易数据中提取 Profile 信息
        - 银行账户列表：从交易数据的 bank_account 字段去重提取
        - 账户间关系（account_relationships）：识别内部转账
          - 写入 profile.account_relationships
          - 这些交易从后续 observations 聚合中排除（与 Node 1 权限矩阵一致：
            Profile 匹配的交易不写入 observations）
        - 贷款 pattern：从历史交易中识别还贷交易 → 写入 profile.loans
        - 以上提取结果暂存，等 Step 6 合并写入 profile.md

Step 3: 标准化 description → pattern（调用共享模块）
        - 调用共享模块 standardize_description 将原始 description 标准化为 canonical pattern
        - 批量优化：先提取所有唯一 raw_description → Layer 1 预清洗 → 去重 cleaned_fragment
          → 批量发送 LLM（每批 10-20 条）→ 写入 pattern_dictionary.db
        - 详细设计见 tools/pattern_standardization_spec.md

Step 4: 按 observations 聚合逻辑处理剩余交易
        - 排除 Step 2 中已识别为内部转账的交易
        - 按 (pattern, direction) 聚合（pattern 来自 Step 3 的输出，direction 来自交易数据），聚合逻辑与 observations_spec 第 3 节完全一致：
          - count: 出现总次数
          - months_seen: 出现过的月份列表
          - amount_range: [min, max]
          - confirmed_by: "onboarding_historical"（区别于运行时的 ai / accountant）
          - classification_history: 聚合所有分类结果（account + hst）及各自出现次数
          - non_promotable: classification_history 中存在 2+ 种分类时自动设为 true
          - force_review: false
          - accountant_notes: ""
        - 写入 observations.md

Step 5: rules 升级评估
        - 扫描 observations，检查升级条件（与 rules_spec 第 3 节一致，但无需
          accountant 确认——历史数据本身已是 accountant 审核过的分类结果）：
          - non_promotable: false
          - count ≥ 3
          - months_seen 中至少 2 个不同月份
          - classification_history 中只有一种分类结果
        - 满足条件 → 直接写入 rules.md
        - rule 字段填充：
          - rule_id: 自动生成
          - pattern: 来自 observation 的 pattern
          - amount_range: null（不限金额）
          - direction: 来自 observation 的 direction
          - account: 来自 classification_history 的唯一分类
          - hst: 来自 classification_history 的唯一分类
          - source: "promoted_from_observation_onboarding, {date}"
          - created_date: onboarding 执行日期
          - match_count: 0
        - 不满足条件 → 保留在 observations.md 中，等待运行时自然积累

Step 6: 构建 profile.md
        - 合并 Step 2 提取的结构性信息 + Step 7 问卷补充信息

Step 7: 生成补充问卷，向 accountant 收集历史数据无法覆盖的信息
        - 问卷内容根据 Step 1-5 的提取结果动态生成：已从历史数据中提取到的字段不再询问
        - 可能需要补充的项：
          - company_legal_name
          - province
          - has_hst_registration + hst_number
          - entity_type
          - industry
          - owner_uses_company_account
          - has_employees + payroll_frequency
        - 接收回复后更新 profile.md

Step 8: 从 QBO 导出 COA 存为 coa.csv
```

---

## 5. 输出

| 输出文件 | 说明 |
| --- | --- |
| profile.md | 客户结构性身份信息，包含基本信息、税务信息、银行账户、账户关系、贷款 |
| observations.md | 初始观察记录。问卷方式下为空文件；历史数据方式下包含从历史账本中提取的 pattern |
| rules.md | 问卷方式下为空文件；历史数据方式下包含满足升级条件的 observations 自动升级的 rules（source 标记为 `promoted_from_observation_onboarding`） |
| coa.csv | 从 QBO 导出的 Chart of Accounts |
| pattern_dictionary.db | Pattern Dictionary 初始版本，包含历史数据中所有 description 到 canonical pattern 的映射（详见 `tools/pattern_standardization_spec.md`） |

---

## 6. 权限边界

### 允许

- ✅ 创建 profile.md
- ✅ 创建 observations.md（含历史 pattern）
- ✅ 创建 rules.md（问卷方式下为空文件，历史数据方式下含自动升级的 rules）
- ✅ 导出并存储 coa.csv
- ✅ 向 accountant 或客户发送问卷并解析回复
- ✅ 分析历史账本提取 pattern
- ✅ 将满足条件的 observations 加入待升级队列
- ✅ 将满足升级条件的 observations 直接写入 rules.md（source 标记为 `promoted_from_observation_onboarding`，无需 accountant 二次确认——历史数据本身已是 accountant 审核过的分类结果）

### 不允许

- ❌ 科目分类判断（只提取历史数据中已有的分类，不自行判断新分类）
- ❌ JE 生成
- ❌ 修改 workflow 逻辑
- ❌ 在 Onboarding 完成后继续参与该客户的后续处理

---

## 7. 与人的交互

| 交互对象 | 交互内容 | 交互形式 |
| --- | --- | --- |
| Accountant | 发送 Onboarding 问卷，接收回复 | 问卷 + 自然语言问答 |
| Accountant | 历史数据提取后的补充问题 | 自然语言问答 |
| Accountant | 提交待升级 observations 清单供审核 | 批量审核列表 |
| 客户（可选） | 部分基本信息可直接向客户收集 | 问卷 |

---

## 8. 与其他组件的关系

### 输出到（Onboarding Agent 创建的文件）

| 组件 | 关系 |
| --- | --- |
| profile.md | 创建初始版本 |
| observations.md | 创建初始版本（可能包含历史 pattern） |
| rules.md | 创建空文件 |
| coa.csv | 从 QBO 导出并存储 |
| pattern_dictionary.db | 创建初始版本 |

### 下游触发

| 组件 | 关系 |
| --- | --- |
| 维护流程 | Onboarding 完成后，历史数据提取的 observations 中满足升级条件的进入待升级队列 |
| 主 Workflow | Onboarding 完成且 accountant 完成初始审核后，主 Workflow 可以开始首次运行 |

### 不直接交互

| 组件 | 关系 |
| --- | --- |
| Coordinator Agent | Onboarding Agent 完成后不再参与，后续 PENDING 处理由 Coordinator Agent 负责 |
| 审核 Agent | Onboarding Agent 不参与审核流程 |
| Node 1-7 | Onboarding Agent 不参与主 Workflow 运行 |
