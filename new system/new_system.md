# 新系统总纲

## 1. 这份 spec 的定位

这份文档记录的是一套新的系统方案。它不是对旧 node spec 的局部补丁，而是一套独立的、从头到尾重新组织记忆机制和匹配机制的设计。

当前状态有两点必须明确：

- 旧的 node spec 仍然保持原样，作为历史参考和可复用约束来源，不是当前默认设计基线。
- 这份文档是当前唯一的 active new-system design source；旧 spec 不会自动升级到这里，也不应被当作并行的当前设计 authority。

一句话概括新系统：

**旧系统先把交易压成 `pattern（标准描述）`，再学习；新系统先认清“这是谁”和“过去类似情况发生过什么”，再决定能不能自动化。**


## 1.1 当前系统由哪些 Workflow Nodes 与 Logs 组成

本节只是把现有功能逻辑改写成 `workflow node + log/memory store` 的表达方式，方便后续窗口和 Piggy Bai 对齐设计语境；它不新增产品功能，不冻结 schema，也不改变下面各节已经定义的功能逻辑。

### Workflow Nodes

1. `Onboarding Node`：处理历史材料，建立初始 evidence、profile 候选、entity、case 和 rule 候选。
2. `Evidence Intake / Preprocessing Node`：整理新交易证据，统一客观结构字段。
3. `Transaction Identity Node`：分配 `transaction_id`，处理同一交易识别和去重。
4. `Profile / Structural Match Node`：先处理内部转账、贷款还款等客户结构可确定的交易。
5. `Entity Resolution Node`：对非结构性交易识别 counterparty / vendor / payee，输出实体识别状态。
6. `Rule Match Node`：在 entity、alias、role/context 和 automation policy 都允许时，执行确定性 rule match。
7. `Case Judgment Node`：未命中 rule 或 rule 不适用时，读取 case memory 和当前 evidence 形成建议或 pending reason。
8. `Coordinator / Pending Node`：证据不足、实体歧义或判断不稳时，向 accountant 获取确认。
9. `Review Node`：让 accountant 审核、批准或修正系统结果和治理候选。
10. `JE Generation Node`：把已确认或足够可信的分类结果转换成 journal entry。
11. `Transaction Logging Node`：把本笔交易最终处理结果和审计轨迹写入 Transaction Log。
12. `Case Memory Update Node`：把已完成交易沉淀为案例，并提出 entity / alias / role / rule 候选。
13. `Governance Review Node`：处理高权限长期记忆变化，例如 entity merge/split、alias approval、role confirmation、rule promotion、automation policy change。
14. `Knowledge Compilation Node`：把 entity、case、rule、governance 历史编译成人和 agent 可读的客户知识摘要。
15. `Post-Batch Lint Node`：批次结束后检查 entity 拆合、rule 稳定性、case-to-rule 候选和自动化风险。

### Logs / Memory Stores

1. `Evidence Log`：保存原始证据和证据引用，不保存业务结论。
2. `Entity Log`：保存 counterparty / vendor / payee、aliases、roles、status、authority、automation_policy 和证据链接，不保存 COA / HST / JE 结论。
3. `Case Log`：保存真实历史案例、最终分类、证据、例外和 accountant correction；它不是旧 Observations 的简单改名。
4. `Rule Log`：保存 accountant/governance 已批准的 deterministic rules，不保存候选规则或一次性判断。
5. `Transaction Log`：保存每笔交易最终处理结果和审计轨迹；只写和查询，不参与 runtime decision，也不是学习层。
6. `Intervention Log`：保存 accountant 介入、提问、回答、修正和确认过程。
7. `Governance Log`：保存高权限长期记忆变化及其审批状态。
8. `Knowledge Log / Summary Log`：保存从 entity、case、rule、governance 历史编译出的客户知识摘要；不作为 deterministic rule source。
9. `Profile`：保存客户结构档案，例如 bank accounts、internal transfer relationships、tax config、loans、employees；它是 durable store，但不强行改名为 `Profile Log`。

后续设计对象如果看起来是 memory layer，而不是 workflow step，应先明确：哪个 workflow node 读取它、哪个 workflow node 写入它、哪些变化只能作为 candidate 提出、哪些必须经过 accountant / governance approval。

### Trace / Reasoning Boundary

旧系统里的 `ai_reasoning` / `policy_trace` 只作为设计思路参考，不作为新系统命名或字段位置的权威。

已确认边界：

- `ai_reasoning` 在新系统中命名为 `ai_decision_summary`。它是面向人类的 AI 决策摘要，不是 chain-of-thought，不是 authority source，也不能被未来 runtime 当作可复用判断依据。
- `policy_trace` 不是新系统的最终字段名。它原本承载的有用设计意图是：保留足够的系统判断依据，让审计、review、correction 和 governance 能追溯当时系统为什么这样处理；具体拆分方式和字段命名由 Tyler 后续决定。
- `Transaction Log` 保存 transaction lifecycle audit：最终结果、流程路径、最小必要快照和 refs。它不是 root-cause store、learning layer、runtime decision source，也不保存可被未来自动化直接复用的错误推理。
- `Intervention Log` / correction record 保存人工介入、错误表现、修正动作和 root-cause 诊断。
- `Governance Log` / governance event 保存长期权威变化，例如 approval、rejection、downgrade、supersession、rule/entity/profile/case/automation-policy mutation。
- active memory stores 只能暴露 corrected / approved / superseded-aware state；错误的 AI 摘要或旧判断依据只能作为 audit reference 保留，不能作为 active case、rule、entity、profile 或 knowledge authority。
- `decision_control_trace` 不作为新系统独立对象、contract、Log 或 memory store 保留；不要把 risk flags、blockers、exception packs、override evidence、finalization gate result、confidence/uncertainty signals 作为这个独立概念继续设计。


---

## 2. 新系统到底改了什么

旧系统最核心的链条是：

`raw_description（原始交易描述）`  
→ `description（标准描述）`  
→ `Observations（观察记录）`  
→ `Rules（规则）`

它的前提是：只要把交易压成稳定的 `description（标准描述）`，后面就都能跑起来。

新系统放弃这个前提。

新系统的核心链条变成：

`raw evidence（原始证据）`  
→ `entity（实体）`  
→ `case memory（案例记忆）`  
→ `rule（规则）`

这里最关键的变化不是“多了一个数据库”，而是：

- 系统先回答“这笔交易说的是谁”
- 再回答“过去类似情况怎么处理过”
- 最后才回答“这次能不能直接自动处理”

所以 `description（标准描述）` 不再是整个系统的唯一身份核心。它退化成一个运行时展示和兼容字段，而不再是学习链条的根。

---

## 3. 新系统里真正长期存在的几层记忆

### 3.1 `raw evidence（原始证据层）`

这一层保存最原始的材料：

- 银行原始描述
- `receipt（小票）`
- `cheque_info（支票信息）`
- 历史账本原文
- accountant 原话

它的职责很简单：

- 给系统提供原料
- 给审计提供证据
- 永远不因为后续总结而被覆盖

它不是“结论层”，只是证据层。

### 3.2 `transaction identity（交易身份层）`

这一层延续你现在的 `transaction_id（交易永久标识）` 设计。

它只回答：

- 这是不是同一笔交易
- 这是不是重复导入

这一层不做语义，不做分类，不做 vendor 识别。

### 3.3 `entity memory（实体记忆层）`

这是新系统新增的核心层。

它不再问“这串字符串像不像某个 pattern”，而是问：

**这条交易证据最可能指向哪个稳定对象。**

比如同一个对象下面可能挂着很多不同写法：

- `TIM HORTONS #1234`
- `TIMS COFFEE-1234`
- `Tims`
- `Tim Hortons`

新系统不会急着把这些写法压成单一 `pattern（标准描述）` 再说，而是先建立一个 Tim Hortons 实体，把这些写法视为它的不同 `alias（别名）` 或表面形态。

这层的价值是：

- 让不同来源的同一对象可以先会合
- 让旧账本简称、银行新写法、receipt 商家名可以在这里桥接
- 让后面的规则不再直接绑死在脆弱字符串上

#### 3.3.1 实体粒度

`Entity（实体）` 的粒度采用：

`counterparty/vendor/payee + role/context（交易对手/商家/收款人 + 角色/上下文）`

也就是说，实体层回答两个问题：

- 这是谁
- 它在这个客户关系里扮演什么角色

但实体层不直接回答：

- 应该入哪个 COA 科目
- 应该采用哪种 HST 处理
- 这笔交易是否可以自动落账

这些仍然属于 `case memory（案例记忆）`、`rules（规则）`、Node 3 和 accountant governance 的职责。

#### 3.3.2 实体识别状态

运行时的 `entity_resolution_output（实体识别输出）` 必须明确给出 `entity_resolution_status（实体识别状态）`：

- `resolved_entity（已识别实体）`：已安全识别到一个稳定实体。
- `resolved_entity_with_unconfirmed_role（已识别实体但角色未确认）`：对象已知，但 role/context 尚未被 accountant 确认。
- `new_entity_candidate（新实体候选）`：系统认为这是新对象，但还不是稳定实体。
- `ambiguous_entity_candidates（多实体歧义）`：可能对应多个已知实体或角色，不能安全归属。
- `unresolved（无法识别）`：证据不足，无法判断是谁。

`new_entity_candidate（新实体候选）` 不天然阻断当前交易分类。只要当前证据足够强，Node 3 可以高置信分类本笔交易；但它不能命中 rule，不能未经治理变成稳定实体，也不能自动创建或升级 rule。

`new_entity_candidate（新实体候选）` 可以为当前交易创建候选实体和 case-memory 记录，但这些记录只作为待治理记忆，不能直接获得稳定实体或规则权限。

#### 3.3.3 稳定实体字段

稳定 `Entity（实体）` 采用中等字段集：

- `entity_id（实体唯一标识）`
- `display_name（展示名称）`
- `entity_type（实体类型）`
- `aliases（别名/表面写法）`
- `roles（角色/上下文）`
- `status（生命周期状态）`
- `authority（确认来源与可信级别）`
- `evidence_links（证据链接）`
- `risk_flags（风险标记）`
- `governance_notes（治理备注）`
- `created_from（创建来源）`
- `automation_policy（自动化策略）`

实体 contract 不应把 COA 分类、HST 处理、embedding/vector 实现细节、或 tax profile 放进核心字段。实体层只负责“是谁”和“在客户关系里的角色/上下文”，不直接持有会计分类结论。

#### 3.3.4 别名和角色治理

`aliases（别名/表面写法）` 分三种状态：

- `candidate_alias（候选别名）`：可以作为 Node 3 的参考上下文，但不能支持 rule match。
- `approved_alias（已确认别名）`：可以支持 entity resolution 和 rule match。
- `rejected_alias（已拒绝别名）`：作为未来识别时的负证据。

`roles（角色/上下文）` 不采用长期三态。稳定实体只保存 accountant 确认过的 role。系统运行时推断出的 `candidate_role（候选角色）` 只放在当前交易的 `entity_resolution_output（实体识别输出）` 中。

Onboarding 可以在受控例外下生成 `accountant_derived_role（来自会计历史数据推导的角色）`，但前提是来源为 accountant 已处理过的历史账本，并且必须保留明确的 authority/source metadata。

#### 3.3.5 状态和自动化策略

`status（生命周期状态）` 只表示实体本身在长期记忆中的状态：

- `candidate（候选实体）`
- `active（有效实体）`
- `merged（已合并实体）`
- `archived（归档实体）`

`active（有效实体）` 不等于可以自动分类。实体是否允许自动化由 `automation_policy（自动化策略）` 控制：

- `eligible（允许自动化）`：允许 rule match，也允许 Node 3 基于 case memory 高置信自动分类。
- `case_allowed_but_no_promotion（允许案例自动化但禁止规则升级）`：允许 case-based 高置信分类，但不允许进入 rule promotion 候选。
- `rule_required（需要规则才可自动化）`：只有已批准 rule 可以自动分类；无 rule 时必须 PENDING。
- `review_required（必须人工复核）`：实体可识别，但每次都需要 accountant 确认。
- `disabled（禁用自动化）`：不允许任何自动分类路径。

系统可以在 `lint pass（批后体检）` 中自动降级 `automation_policy（自动化策略）`，但升级或放宽必须 accountant 批准。

`rule_required（需要规则才可自动化）` 是当前正式命名；不要再使用早期的 `rule_only（只允许明确规则自动化）`。

实体级 `automation_policy（自动化策略）` 和规则生命周期治理是两条独立权限线：

- 系统可以在 `lint pass（批后体检）` 中自动降低实体自动化权限，例如从 `eligible（允许自动化）` 降到 `case_allowed_but_no_promotion（允许案例自动化但禁止规则升级）` 或 `rule_required（需要规则才可自动化）`。
- 升级或放宽实体自动化权限必须 accountant 批准。
- 任何 `rules（规则）` 的创建、升级、修改、删除、降级都必须经过 accountant review and approval。
- 系统可以把候选项放入 `rule_governance_queue（规则治理队列）`，但不能自行修改 active rule。

#### 3.3.6 实体识别输出 contract

运行时 `entity_resolution_output（实体识别输出）` 采用中等字段集：

- `status（识别状态）`：五种 `entity_resolution_status（实体识别状态）` 之一。
- `entity_id（实体唯一标识）`：安全识别到稳定实体时填写。
- `confidence（识别置信度）`：只表示实体识别置信度，不表示会计分类置信度。
- `reason（识别理由）`：简短说明为什么选择该状态或实体。
- `matched_alias（命中的别名）`：命中的 alias 或当前证据表面文本。
- `alias_status（别名状态）`：`candidate_alias（候选别名）`、`approved_alias（已确认别名）`、或 `rejected_alias（已拒绝别名）`。
- `candidate_role（候选角色）`：当前交易的系统推断角色，不经 accountant 确认不得写入稳定实体角色。
- `evidence_used（使用的证据）`：用于识别的证据来源，例如 raw description、receipt vendor、cheque payee、historical ledger name、或 accountant context。
- `blocking_reason（阻断原因）`：如果该识别结果不能支持确定性自动化，说明阻断原因。
- `candidate_entities（候选实体列表）`：在 ambiguous 或 unresolved 场景下列出可能实体。

这个输出 contract 不暴露 embedding/vector 命中、raw model prompt trace、或全部 rejected candidates 等实现细节。

### 3.4 `case memory（案例记忆层）`

这层替代旧系统的 `Observations（观察记录）` 主角色。

旧系统的 `Observations（观察记录）` 更像统计直方图。  
新系统的 `case memory（案例记忆）` 先保留原子案例。

也就是说，系统不是先说：

- Home Depot 出现了 5 次
- 其中 4 次是材料费
- 1 次是老板借款

而是先记住那 5 个真实案例各自发生了什么：

- 哪笔有 `receipt（小票）`
- 哪笔没有
- 哪笔是 accountant 说过“这次是私人装修”
- 哪笔金额异常大

然后系统再从这些案例中编译出摘要。

这层的价值是：

- 可以表达“通常是 X，但在 Y 条件下是 Z”
- 不会因为出现第二种分类就立刻把学习路径锁死
- 让 Node 3 拿到的是案例和条件，而不是纯计数

### 3.5 `rules（规则层）`

这层继续保留，而且仍然是确定性执行层。

但它不再主要回答：

- 这条 `pattern（标准描述）` 怎么分

而更接近回答：

- 这个 `entity（实体）` 在这个上下文下怎么分

所以它的核心价值不变：

- 命中就直接处理
- 不需要模型再判断
- 仍然由 accountant 掌握高 authority 写入口

变的是它绑定的对象更稳了，不再过度依赖单一字符串。

Rule match 的前置条件也因此改变。新系统中，只有同时满足以下条件时，交易才可以进入 rule match：

- `entity.status（实体生命周期状态） = active（有效实体）`
- `matched_alias（命中的别名） = approved_alias（已确认别名）`
- rule 要求的 role/context 已确认并满足
- `automation_policy（自动化策略）` 允许 rule-based automation
- 存在适用的 active rule
- 当前交易满足 rule 自身的 `direction（方向）`、`amount_range（金额范围）` 和其他已批准条件

`lint warning（批后体检警告）` 或近期 `intervention（人工干预）` 不应作为 rule match 里的临时额外判断。它们应通过治理流程改变 `automation_policy（自动化策略）` 或 rule 状态，从而影响未来匹配。

### 3.6 `transaction log（交易审计日志）`

这一层继续保留原定位：

- 记录这笔交易最后为什么这么分
- 只写和查询
- 不参与主 workflow 的运行时判断

新系统不会把它改成学习层，也不会让它直接反喂 Node 3。

---

## 4. Onboarding 从开始到结束如何运作

### 4.1 第一步：接收历史材料

系统接收：

- 银行流水
- 历史账本
- 小票
- 支票
- accountant 对客户的补充说明

这一步的目标不是立即生成 `rule（规则）`，而是先把所有历史材料变成可处理的证据集合。

### 4.2 第二步：先做结构标准化

系统只统一那些客观字段：

- 日期
- 金额
- `direction（方向）`
- `bank_account（银行账户）`

这一步仍然是硬标准化。  
但系统不会在这一阶段强迫每一笔历史交易都立刻产出稳定 `description（标准描述）`。

### 4.3 第三步：为历史交易分配 `transaction_id（交易永久标识）`

这一层保持和旧系统一致：

- 每笔历史交易都先拿到稳定身份
- 去重问题先解决

### 4.4 第四步：抽取 `profile（客户结构档案）` 候选事实

系统会从历史材料里尝试提取：

- 客户有哪些银行账户
- 哪些是内部转账
- 有没有贷款
- 有没有员工
- 老板是否常用公司账户做个人消费

但这一步先形成候选事实，不直接把所有猜测写死进 `profile（客户结构档案）`。

### 4.5 第五步：建立实体

这是 onboarding 最关键的动作。

系统会把历史材料里提到的对象做会合：

- 银行描述中的商家名
- 历史账本中的简称
- `receipt（小票）` 上的 vendor 名字
- `cheque_info（支票信息）` 里的收款人

比如：

- 历史账本写 `Tims`
- 银行流水写 `TIM HORTONS #1234`
- 小票写 `Tim Hortons`

系统不再先问“这三条能不能压成同一个 pattern”，而是先问：

**它们是不是同一个实体。**

### 4.6 第六步：建立历史案例

如果一笔历史交易已经有 accountant 处理过的分类结果，系统就把它写进 `case memory（案例记忆）`。

这里记住的不是一串压缩统计，而是：

- 这是哪个实体
- 这笔最后怎么分
- 当时有没有小票
- 有没有例外说明

### 4.7 第七步：编译客户专属知识

系统会从实体和案例中生成可读摘要，例如：

- Tim Hortons 这类交易通常是餐饮费
- Home Depot 大多数是材料费，但混有少量老板私人消费
- John Smith 通常是分包商，但名字歧义较高

这些摘要是为了帮助后续判断，不是直接等于规则。

### 4.8 第八步：只把少量稳定对象升级成 `rule（规则）`

只有当某个实体满足下面这类条件时，系统才会考虑生成初始规则：

- 对象足够稳定
- 历史分类长期一致
- 没有明显混用，或者例外边界非常清楚

所以 onboarding 的产出顺序变成：

- 先建 `entity memory（实体记忆）`
- 再建 `case memory（案例记忆）`
- 最后才筛选 `rule（规则）`

而不是旧系统那种：

- 先造 `pattern（标准描述）`
- 再造 observation
- 再尽快升 rule

---

## 5. 主 workflow 处理新交易时如何运作

### 5.1 先做预处理和交易去重

这部分基本延续旧系统：

- 解析文件
- 配对小票与支票
- 统一结构字段
- 生成 `transaction_id（交易永久标识）`

### 5.2 先过 `profile（客户结构档案）`

系统先判断这笔是不是明确的结构性交易：

- 内部转账
- 已知贷款还款
- 其他可以由 `profile（客户结构档案）` 直接确定的情况

如果是，就直接按 Node 1 处理。

### 5.3 再做 `entity resolution（实体识别）`

如果不是结构性交易，系统下一步不是直接去匹配 `pattern（标准描述）`，而是先认对象。

它会综合看：

- `raw_description（原始交易描述）`
- `receipt（小票）`
- `cheque_info（支票信息）`
- 旧别名
- 必要时看 accountant 补充上下文

系统要回答的是：

- 这是一个已知实体吗
- 还是一个全新的实体
- 还是一个模糊对象，暂时无法安全归属

### 5.4 命中 `rule（规则）` 的条件改变了

旧系统里，规则命中主要靠：

- `transaction.description（交易标准描述） == rule.pattern（规则模式）`

新系统里，规则命中更接近：

- 这笔交易已经被识别为某个稳定 `entity（实体）`
- 这个实体在当前上下文下有确定性规则

也就是说，规则层依然是 exact 和 deterministic 的，只是它匹配的是更稳的对象，不再直接绑死在原始字符串上。

### 5.5 没命中规则时，再看历史先例

如果某个实体没有规则，系统不会立刻裸奔去猜。

它会先查：

- 过去这个实体通常怎么分
- 哪些条件下会出现例外
- 这次有没有 `receipt（小票）`
- 这次金额是否异常
- 这次是否触发 mixed-use 风险

所以 Node 3 拿到的不是旧系统里单薄的 observation 计数，而是：

- 实体是谁
- 历史先例是什么
- 当前证据是否足以覆盖风险

### 5.6 不够稳时进入 `pending（待人工确认）`

如果这次证据不足，系统就不自动落账，而是让 `Coordinator（协调代理）` 去问 accountant。

但它问的问题会比旧系统更强，因为它已经知道：

- 这笔交易最像哪个历史实体
- 过去类似案例通常如何处理
- 这次卡住的原因是什么

---

## 6. 三个最典型例子

### 6.1 稳定商家：Tim Hortons

历史材料中出现过：

- `TIM HORTONS #1234`
- `TIMS COFFEE-1234`
- `Tims`

系统在 onboarding 时已经把它们会合为同一个 Tim Hortons 实体。

后来来了新交易：

- `TIMS COFFEE-1234`

流程是：

- 先识别出它属于 Tim Hortons 实体
- 再发现这个实体已有稳定 `rule（规则）`
- 于是直接自动分类

这里规则命中的前提不是“原始字符串一模一样”，而是“对象已经被识别为同一个实体”。

### 6.2 混合用途商家：Home Depot

历史上：

- 大多数 Home Depot 是材料费
- 少数是老板个人消费

新交易来了：

- `HOME DEPOT #4521`
- 同时附带 `receipt（小票）`
- 小票上写水泥和钢筋

系统会这样处理：

- 认出这是 Home Depot 实体
- 看到历史上默认是材料费
- 也知道这个实体有 mixed-use 风险
- 但本次小票明确支持业务用途

于是 Node 3 可以高置信分类为材料费。

### 6.3 全新 vendor：第一次出现的科技服务商

新交易来了：

- `Tims Button`

历史里从未出现过这个商家。

系统不会因为它和 `Tims` 长得像，就直接按 Tim Hortons 处理。  
它会先把它视为一个新的或未确认的实体。

接下来分两种情况：

- 如果当前证据足够强，例如有小票、合同、清晰上下文，系统可以高置信分类
- 如果证据不够强，就进 `pending（待人工确认）`

之后，这次处理结果才会成为新的案例和新的实体记忆的一部分。

---

## 7. 批次结束后的治理回路

这是新系统相对旧系统的另一条大变化。

旧系统基本是 forward-only。  
新系统会在批次结束后做一轮健康检查。

它会检查：

- 有没有两个其实是同一个对象，却被拆成两个实体
- 有没有某条 `rule（规则）` 最近频繁被 accountant 改掉
- 有没有某类案例已经足够稳定，值得升级为规则
- 有没有某个实体已经不适合继续自动化

这一步的产物会交给 `Review Agent（审核代理）`，让 accountant 做治理决定。

所以 `Intervention Log（人工干预日志）` 不再只是归档，它会变成系统治理的输入之一。

实体治理必须写入 `entity_governance_event（实体治理事件）`。

`event_id（治理事件唯一标识）` 是单次治理动作的主键；`entity_id（实体唯一标识）` 是重要查询索引，但不能替代 event_id。原因是同一实体会有多次治理动作，而一次治理动作也可能影响多个实体。

典型事件包括：

- `approve_alias（批准别名）`
- `reject_alias（拒绝别名）`
- `confirm_role（确认角色）`
- `merge_entity（合并实体）`
- `split_entity（拆分实体）`
- `change_automation_policy（修改自动化策略）`

治理事件的最小字段集包括：

- `event_id（治理事件唯一标识）`
- `event_type（治理事件类型）`
- `entity_ids（相关实体 ID 列表）`
- `affected_aliases（受影响别名）`
- `affected_roles（受影响角色）`
- `old_value（修改前值）`
- `new_value（修改后值）`
- `source（来源）`，例如 `lint_pass（批后体检）`、`review_agent（审核代理）`、`accountant_instruction（会计指令）`、`onboarding（初始化）`
- `requires_accountant_approval（是否需要会计批准）`
- `approval_status（批准状态）`：`pending（待批准）`、`approved（已批准）`、`rejected（已拒绝）`、`auto_applied_downgrade（自动降级已生效）`
- `accountant_id（会计标识）`
- `reason（原因说明）`
- `evidence_links（证据链接）`
- `created_at（创建时间）`
- `resolved_at（处理完成时间）`

`entity merge/split（实体合并/拆分）` 只能由治理流程执行。运行时最多生成 `merge_candidate（合并候选）` 或 `split_candidate（拆分候选）`。合并时旧 `entity_id` 不删除，而是改为 `merged（已合并实体）` 并指向 `merged_into_entity_id（合并目标实体 ID）`。拆分时新对象获得新的 `entity_id`，历史 cases 不自动全量迁移，只迁移 accountant 明确确认的案例。

Active rules 和 approved aliases 不会自动跟随 merge/split 生效，必须进入治理队列由 accountant 确认。Transaction Log 不重写历史实体引用，后续解释通过 governance event 完成。

治理事件规则：

- 所有长期 entity-memory mutation 都必须写入事件。
- 事件必须能按 `event_id（治理事件唯一标识）`、`entity_id（实体唯一标识）`、`approval_status（批准状态）`、`event_type（治理事件类型）` 查询；如果事件关联具体 transaction/case，也应能按对应引用查询。
- 系统自动降级 `automation_policy（自动化策略）` 可以立即生效，但必须记录为 `auto_applied_downgrade（自动降级已生效）` 并展示给 Review Agent。
- 需要 accountant approval 的事件，在批准前不得改变长期 entity memory。
- Review Agent 应按业务含义和事件类型聚合展示治理事件，不应直接把原始事件字段倾倒给 accountant。

---

## 8. 这套系统中哪些东西仍然保持不变

以下部分不应因为新系统而被推翻：

- `profile（客户结构档案）` 仍然是结构事实层
- Node 1 仍然负责结构性、确定性匹配
- `rule（规则）` 仍然是确定性执行层
- `transaction log（交易审计日志）` 仍然只写和查询，不直接参与运行时判断
- `JE generator（分录生成器）` 仍然是纯计算层
- accountant 仍然拥有最终治理权

所以这套方案不是“把系统全改成语义搜索”，而是：

**把语义能力放在该放的地方，也就是实体识别和历史先例利用层；把确定性仍然保留在该确定的地方。**

---

## 9. 这份 spec 对旧系统的约束

这份新系统总纲当前只做两件事：

- 作为未来是否采纳新系统的设计基线
- 为后续迁移讨论提供统一语言

它当前不自动修改以下旧 spec 的 contract：

- `Pattern Dictionary（模式字典）`
- `Observations（观察记录）`
- `Rules（规则）`
- `Onboarding Agent（初始化代理）`
- `Node 3（智能判断层）`

也就是说，在你明确决定迁移之前：

- 旧 node spec 继续保持原状
- 新系统内容统一以这份 `new_system.md` 为准
- `different_node.md` 和 `memory_node_design.md` 停止作为 active design source，只保留为历史背景/草稿材料，不再要求后续更新
