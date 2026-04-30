# 新旧节点差异

> 已停止作为 active design source。
>
> 本文件仅保留为早期背景材料，用于理解最初的新旧系统差异。当前新系统设计统一以
> `new system/new_system.md` 为准。后续收敛新系统 contract 时不要继续更新本文件。

## 1. 这份文档的定位

这份文档只回答一个问题：

**如果采用新系统，旧系统里哪些环节被替代，哪些节点规则会失去原来的作用。**

它不是新的运行 spec，而是旧系统和新系统的对照图。

---

## 2. `standardize_description（标准化描述工具）`

原系统里的角色：

- 把 `raw_description（原始交易描述）` 压成 `description（标准描述）`
- 用 `cleaned_fragment（清洗片段）` 做精确查找
- 在进入主 pipeline 之前先把“这是谁”收敛成一个 canonical pattern（标准模式）

新系统里的变化：

- 它不再承担“核心身份识别”职责
- 它的主角色被 `entity resolution（实体识别）` 取代
- 它如果保留，也只适合作为 alias cache（别名缓存）或运行时兼容层

因此失去作用的旧规则：

- `cleaned_fragment（清洗片段）` 作为长期稳定主键
- `Pattern Dictionary（模式字典）` 作为身份识别核心记忆
- `fallback（回退模式）` 作为主要降级学习路径
- “只要把交易压成稳定 pattern（标准描述），下游就都能跑”

---

## 3. `Pattern Dictionary（模式字典）`

原系统里的角色：

- 维护 `cleaned_fragment（清洗片段） -> canonical_pattern（标准模式）`
- 保证同一片段长期返回同一 `pattern（标准描述）`

新系统里的变化：

- 核心记忆位置让给 `entity memory（实体记忆）`
- 它不再是 identity（身份识别） 主存储
- 它最多只保留为 exact alias（精确别名） 命中缓存
- 只有 `approved_alias（已确认别名）` 可以支持确定性 rule match（规则命中）
- `candidate_alias（候选别名）` 只能作为 Node 3 的参考上下文，不能触发规则自动化

因此失去作用的旧规则：

- “同一 vendor（商家） 的变体主要靠字典收敛”
- “Onboarding（初始化导入） 的核心产出之一是把历史批量写进字典”
- “Review（审核） 主要通过 pattern 合并/重命名/拆分来修正长期记忆”

---

## 4. `Data Preprocessing Agent（数据预处理代理）`

原系统里的角色：

- 判断是否存在 identity signal（身份信号）
- 有就生成 `description（标准描述）`
- 没有就 `description = null（标准描述为空）`

新系统里的变化：

- 预处理仍然负责解析、配对、结构标准化和 `transaction_id（交易永久标识）`
- 但“生成 `description（标准描述）`”不再是它最核心的职责
- 更重要的动作变成“整理证据，交给实体识别层”
- `description（标准描述）` 和 `pattern_source（模式来源）` 不再决定长期学习入口
- 运行时应产出 `entity_resolution_output（实体识别输出）`，说明实体识别状态、命中别名、候选角色、使用证据和阻断原因

因此失去作用的旧规则：

- “只有 `raw_description（原始交易描述）` 自己带有身份信号时才有学习入口”
- “`cheque payee（支票收款人）` 直接充当稳定 `description（标准描述）`”
- “`description = null（标准描述为空）` 的交易天然与长期记忆隔离”
- `pattern_source（模式来源） = dictionary_hit / llm_extraction / fallback / null（字典命中 / 模型提取 / 回退 / 空）` 这套来源语义作为核心运行解释

---

## 5. `Onboarding Agent（初始化代理）`

原系统里的角色：

- 历史账本先批量产出 `pattern（标准描述）`
- 再按 `pattern（标准描述） + direction（方向）` 聚合成 `Observations（观察记录）`
- 再把稳定 observation（观察记录） 升成 `Rules（规则）`

新系统里的变化：

- onboarding 先建立 `entity memory（实体记忆）`
- 再建立 `case memory（案例记忆）`
- 最后只从少量稳定对象里筛选 `rule（规则）`

因此失去作用的旧规则：

- “历史材料的首要目标是产出稳定 pattern（标准描述）”
- “Onboarding（初始化导入） 应先构造 observation（观察记录）”
- “Onboarding（初始化导入） 可直接从历史重复里自动产出高 authority `rule（规则）`”
- “旧账本简称如果不能稳定映射到 pattern（标准描述），它的价值就很低”

---

## 6. `Observations（观察记录）`

原系统里的角色：

- `pattern（标准描述）` 历史统计层
- `Rules（规则）` 的候选暂存区
- Node 3 的历史参考源

新系统里的变化：

- 这层的主角色让给 `case memory（案例记忆）`
- 原子案例先存，再编译摘要
- 条件性规律可以被表达，不再只能依赖计数直方图

因此失去作用的旧规则：

- 以 `pattern（标准描述） + direction（方向）` 作为主聚合键
- `count（次数）`、`months_seen（出现月份）`、`classification_history（分类历史计数）` 作为主要表达方式
- 出现第二种分类就自动 `non_promotable（不可升级）`
- `description = null（标准描述为空）` 的交易不进入学习层
- `pattern_source = fallback（模式来源为回退）` 的交易不进入学习层
- “Node 3 主要看统计分布，再自己猜例外原因”

---

## 7. `Rules（规则）`

原系统里的角色：

- `pattern（标准描述）` 的确定性执行层
- Node 2 通过 `transaction.description（交易标准描述） == rule.pattern（规则模式）` 命中

新系统里的变化：

- 规则仍然保留确定性地位
- 但它绑定的核心对象从 `pattern（标准描述字符串）` 转向 `entity（实体）`
- 未来允许少量、显式、受控的 conditional rule（条件规则）
- rule match（规则命中）必须同时满足：实体为 `active（有效实体）`、命中 `approved_alias（已确认别名）`、所需 role/context 已确认、`automation_policy（自动化策略）` 允许、存在 active rule、交易满足 rule 条件

因此失去作用的旧规则：

- `pattern（标准描述字符串）` 作为 rule（规则） 的主体
- `transaction.description == rule.pattern（交易标准描述等于规则模式）` 作为唯一核心命中逻辑
- “单一分类 + 跨月 + 次数够了” 就足以描述全部升级逻辑
- “有例外就不适合升规则”
- “规则主要是 pattern（标准描述） 的制度化结果”

---

## 8. `Node 3 / confidence classifier（智能判断层）`

原系统里的角色：

- 主要读取同一个 `pattern（标准描述） + direction（方向）` 的 observation（观察记录）
- 再参考 `classification_history（分类历史）`、`force_review（强制人工审核）`、`accountant_notes（会计备注）`

新系统里的变化：

- Node 3 的主要历史输入变成 `evidence pack（证据包）`
- 证据包包含实体、历史案例、已知风险、当前证据强弱
- 它不再以 observation row（单条观察记录） 为唯一入口
- 当 `entity_resolution_status（实体识别状态） = new_entity_candidate（新实体候选）` 且当前证据足够强时，Node 3 仍可高置信分类本笔交易
- 但新实体候选不能命中 rule，也不能未经治理变成稳定实体或创建 rule

因此失去作用的旧规则：

- `query_observation(pattern, direction)（按标准描述和方向查观察）` 是主历史读取动作
- `stable_single_observation（稳定单一观察）` 是主要 override evidence（覆盖证据）
- `fallback_pattern_caution（回退模式谨慎包）` 围绕 `pattern_source（模式来源）` 组织风险
- “没有 `description（标准描述）` 就没有历史参考”

---

## 9. `Coordinator Agent（协调代理）`

原系统里的角色：

- 对 `description（标准描述）` 非空交易按 pattern（标准描述） 归组
- `description = null（标准描述为空）` 的交易逐笔展示

新系统里的变化：

- 有已识别实体的交易按 `entity（实体）` 归组
- 无法安全识别实体的交易，按问题类型或逐笔展示
- 提问时不再只说“这个 pattern（标准描述） 历史上怎么分”，而会带实体与先例上下文

因此失去作用的旧规则：

- “有 `description（标准描述）` 就说明可归为同组”
- “`description = null（标准描述为空）` 就只能形成无意义 null bucket（空桶）”
- `observation_context（观察上下文）` 主要靠 pattern（标准描述） 历史生成

---

## 10. `Review Agent（审核代理）`

原系统里的角色：

- 维护 pattern（标准描述）
- 做 merge pattern（合并标准描述）、rename pattern（重命名标准描述）、split pattern（拆分标准描述）
- 再基于新 pattern rebuild `Observations（观察记录）`

新系统里的变化：

- 它的治理对象从 pattern（标准描述） 转向 entity（实体）
- 更重要的动作会变成 merge entity（合并实体）、split entity（拆分实体）、approve alias（批准别名）、治理 rule health（规则健康）
- entity merge/split（实体合并/拆分） 只能由 Review / Governance 流程执行，runtime 只能生成候选
- 所有长期 entity memory 变更都应写入 `entity_governance_event（实体治理事件）`

因此失去作用的旧规则：

- pattern（标准描述） 是长期治理的核心对象
- `cleaned_fragment（清洗片段）` 是拆分和归属判断的重要治理单位
- rebuild observations by `description（标准描述） + direction（方向）`
- `force_review（强制人工审核）` 和 `accountant_notes（会计备注）` 主要绑在 pattern（标准描述） 上

---

## 11. `Intervention Log（人工干预日志）`

原系统里的角色：

- 记录 accountant 为什么修改
- 主要用于审计和事后排查

新系统里的变化：

- 它会变成 `lint pass（批后体检流程）` 的主要输入之一
- 不再只是归档，而是治理回路的燃料

因此失去作用的旧规则：

- “Intervention Log（人工干预日志） 只是写入，不主动参与系统改进”
- “规则修正信号只在人工回看时才有价值”

---

## 12. `Profile（客户结构档案）`、Node 1、`JE generator（分录生成器）`、`Transaction Log（交易审计日志）`

这些节点不是这次重构的主替代目标。

保留不变的核心逻辑：

- `Profile（客户结构档案）` 仍然是结构事实层
- Node 1 仍然先处理结构性、确定性匹配
- `JE generator（分录生成器）` 仍然纯计算
- `Transaction Log（交易审计日志）` 仍然只写和查询，不直接参与运行时判断

但仍有一个变化要注意：

- `Transaction Log（交易审计日志）` 里的 `description（标准描述）` 和 `pattern_source（模式来源）` 会下降为次级字段
- 更重要的运行时身份会转向 `entity（实体）`
- Transaction Log 不应在 entity merge/split 后重写历史 entity 引用；后续解释应通过 `entity_governance_event（实体治理事件）` 追溯

---

## 13. 一句话总结

真正被替代的不是某一个独立节点，而是整条旧学习链：

`raw_description（原始交易描述）`  
→ `pattern（标准描述）`  
→ `observation（观察记录）`  
→ `rule（规则）`

它会被新链条取代：

`raw evidence（原始证据）`  
→ `entity（实体）`  
→ `case memory（案例记忆）`  
→ `selective rule（选择性规则化）`
