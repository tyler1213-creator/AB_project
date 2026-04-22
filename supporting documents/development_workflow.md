# AI Bookkeeper 开发流程框架

## Context

项目有 8 个强耦合节点，节点间共享数据结构和业务逻辑，一动则百动。需要一套开发流程来确保：
- 各节点逻辑一致性
- 级联修改风险尽早暴露
- 跨会话保持全局上下文
- 每个开发会话有规范的执行流程

**核心原则：** 流程服务于质量，不是仪式。组件复杂度低时可以压缩步骤，但 contract 对齐和集成验证不能省。

---

## Phase 0: Dry Run + Contract Layer — 验证 spec 逻辑，定义接口契约

**目标：** 先用可控的 synthetic 输入验证 system design / interface / state flow，再用真实交易验证真实世界输入问题；把确认的数据结构直接写成代码，作为所有节点的共享基础。

### Step 1: Synthetic Dry Run（优先）

1. 准备一套完整的 synthetic pack：
   - 结构化交易数据
   - 完整 profile / COA / rules / observations
   - 预期 routing map
   - accountant simulation script
2. 按 pipeline 顺序模拟：
   - Data Preprocessing：原始数据 → 标准化后的 transaction record 长什么样？
   - Node 1 Profile 匹配：匹配条件是什么、命中/未命中分别输出什么？
   - Node 2 Rules 匹配：同上
   - Node 3 AI 分类：输入什么、输出什么、confidence 怎么定？
   - JE Generator：拿到分类结果后怎么生成借贷分录？
   - Coordinator：PENDING 交易的沟通内容和格式是什么？
   - Output Report：最终 Excel 里每列是什么？
3. 重点检查：
   - 节点接口是否匹配
   - handoff schema 是否足够清楚
   - split / retrigger / review / intervention 等状态流转是否自洽
4. 记录发现的 spec 矛盾或模糊地带，修正 spec

### Step 2: Real-World Dry Run（第二层）

1. 准备多笔有代表性的真实交易（含简单交易 + 带 HST 的复杂交易）
2. 用真实 bank statement / receipt / cheque image 跑同一套 pipeline
3. 重点检查：
   - OCR / parser / ingestion 问题
   - 缺失资料下的行为
   - 真实上下文中的 pending 比例和阻塞点
4. 将“系统设计问题”和“真实输入问题”分开记录，避免混淆

### Step 3: 代码化契约

1. 定义共享数据结构（Python dataclass / Pydantic model）：
   - `TransactionRecord`：标准化后的交易记录 schema
   - `ClassificationResult`：分类结果（account, classified_by, confidence 等）
   - `JELine`：Journal Entry 借贷行
   - 各数据存储的 schema（Profile, Rule, Observation, TransactionLogEntry, InterventionLogEntry）
2. 定义每个处理节点的输入/输出接口：
   - 函数签名（输入类型 → 输出类型）
   - 行为契约：什么条件下返回什么结果（命中/未命中/异常）

**产出：**
- `contracts/` 目录，包含所有共享类型定义和接口签名——整个项目的单一真相来源
- 各 spec 的修正记录
- `Synthetic Dry Run Pack` 设计文档与 findings

**用什么工具：** Synthetic Dry Run 优先使用工作流式编排；Real-World Dry Run 用于补充真实输入验证。契约代码化阶段使用 Superpowers brainstorming（设计 contract 结构）→ writing-plans → executing-plans。

---

## Phase 1: 基础设施 — 共享工具和数据存储层

**目标：** 实现 contract 层之下的基础能力，供所有处理节点调用。

**开发顺序（按依赖关系）：**

### 1a. 共享工具
- Pattern Standardization（description 标准化）
- Pattern Dictionary（SQLite）

### 1b. 数据存储层
- Profile 存储（CRUD + Node 1 匹配逻辑）
- Rules 存储（CRUD + Node 2 匹配逻辑）
- Observations 存储（CRUD + 升级队列逻辑）
- Transaction Log（只写 + 查询）
- Intervention Log（只写 + 查询）

**每个组件的开发流程（Superpowers 内层循环）：**
1. `brainstorming` — 确认实现细节和边界情况
2. `writing-plans` — 具体实现计划
3. `executing-plans` — 写代码（可用 sub agent 并行独立子任务）
4. `requesting-code-review` — 审查
5. `verification-before-completion` — 跑测试 + 验证与 contract 的一致性

组件简单时（如 CRUD 操作）可压缩前两步，但第 5 步（与 contract 对齐 + 测试）不能省。

**每个组件完成后必须做的：**
- 单元测试通过
- 与 contract 层的类型定义对齐（import contract 中的类型，不自己重新定义）
- 更新 CLAUDE.md 的 Current Focus 和任何新的架构决策

**开发期 schema 迁移策略：** 开发阶段 SQLite schema 变更直接 drop + recreate，不做增量迁移。测试数据用脚本生成，保证可重建。进入 Phase 3 集成测试后如需改 schema，评估数据重建成本再决定。

---

## Phase 2: 处理节点 — 按 pipeline 顺序逐段开发

**开发顺序（按数据流方向）：**

```
2a. Data Preprocessing
2b. Node 1 (Profile 匹配) — 依赖 Phase 1 的 Profile 存储
2c. Node 2 (Rules 匹配) — 依赖 Phase 1 的 Rules 存储
2d. Node 3 (AI 分类器) — 依赖 Phase 1 的 Observations 存储
2e. JE Generator — 依赖分类结果
2f. Coordinator — 依赖 PENDING 判定逻辑
2g. Output Report — 依赖 JE 数据
2h. Review Agent — 依赖所有前置节点
```

**每个节点的开发纪律：**

1. **开始前**：加载 contract 层 + 该节点 spec + 上下游已实现的代码
2. **开发中**：走 Superpowers 内层循环（brainstorming → plan → execute → review → verify），复杂度低的节点可压缩
3. **完成后**：
   - 用真实数据跑通该节点与上游的衔接（不是等全部写完再集成）
   - 如果发现 contract 需要修改 → **先改 contract，再改受影响的已完成节点，最后继续当前节点**
   - 更新 CLAUDE.md

**级联修改处理流程：**
```
发现问题 → 评估影响范围（哪些已完成节点受影响）
         → 判断修改规模：
           - 小改（1-2 个节点、字段增删）→ 走修复流程
           - 大改（3+ 个节点、结构性变更）→ 先暂停，重新评估 contract 设计是否合理
         → 确认走修复流程：
           → 先修改 contract 层
           → 逐个修复受影响的节点（每个一个会话）
           → 跑集成测试确认修复完成
           → 回到当前节点继续开发
```

---

## Phase 3: 集成测试 — 端到端验证

**目标：** 全 pipeline 跑通，用多种类型的真实交易验证系统整体行为。

**测试数据设计：**
- 复用 Phase 0 走查的交易作为 baseline
- 补充覆盖以下场景：
  - 基础：简单收入/支出、带 HST 的交易、HST exempt 交易
  - 分类路径：Profile 命中、Rule 命中、AI 高置信、AI 低置信 → PENDING
  - 边界：退款/冲销、跨省交易（不同税率）、外币交易、同一 vendor 多种分类
  - 异常：缺失字段、格式不规范的银行流水、重复交易

**验收标准：**
- 分类正确性：每笔交易的 classified_by 和 account 与预期一致
- JE 完整性：每笔 JE 借贷平衡，HST/GST 分录正确
- 审计合规：Transaction Log 完整记录每笔交易的分类依据和路径
- 输出格式：Excel 报告可直接供 accountant 审核，无需人工调整格式

**排查流程：**
端到端失败时，按 pipeline 方向逐节点检查输出，定位到第一个输出不符合预期的节点，从该节点开始修复。

---

## Phase 4: Onboarding Agent — 新客户初始化

**单独放在最后：** 因为它是一次性流程，且依赖所有其他节点的完成来验证初始化结果是否正确。

---

## 跨会话一致性维护规则

这些规则贯穿所有 Phase，是防止"脱节"的核心纪律：

### 1. CLAUDE.md 是持久化的 PM
- `Current Focus`：当前在开发哪个节点、进展到哪一步
- `Architecture Decisions`：新增的设计决策和理由
- 每个会话结束时更新

### 2. Contract 层是单一真相来源
- 所有节点的数据结构都 import 自 `contracts/`
- 任何 schema 变更必须先改 contract，再改节点代码
- 禁止在节点内部重新定义 contract 中已有的类型

### 3. 每个节点完成后立即集成验证
- 不攒到最后再集成
- 用真实数据验证与上游的衔接
- 集成测试代码随节点一起写，不单独补

### 4. 级联修改有固定流程
- 不能只改当前节点"绕过去"
- 必须回溯到 contract → 受影响节点 → 当前节点
- 影响范围超过 3 个节点时，先评估是否需要重新设计 contract

### 5. Memory 记录非显而易见的决策
- 为什么选了方案 A 而不是 B
- 哪个 spec 的哪个部分在 dry run 中被修改了，为什么
- 不记录代码能体现的东西

### 6. 会话粒度
- **默认规则**：一个组件（Phase 1）或一个节点（Phase 2）= 一个会话
- **级联修改**：每个受影响节点单独一个会话
- **Phase 0**：可以是一个较长的会话，走查和契约定义是连续思考过程
- 每个会话结束前更新 CLAUDE.md 的 Current Focus
