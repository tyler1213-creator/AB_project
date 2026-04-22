# Phase 0 Dry Run — Bug List

---

## Data Preprocessing Agent

### BUG-001: CHQ 交易的 pattern 标准化丢失 payee 信息

**严重程度：** 高

**问题描述：**

`standardize_description(raw_description, client_id)` 接口不接受 `cheque_info` 参数。银行流水中所有支票交易的 raw_description 都是 `CHQ#000xxx` 格式（如 `CHQ#000176`），经过 Layer 1 预清洗后 cleaned_fragment 为 `CHQ#000176`，LLM 提取的 canonical pattern 只能是 `CHQ`——因为描述中不包含任何商户/收款人信息。

**影响：**

1. 所有支票交易无论收款人是谁，canonical pattern 都坍缩为 `CHQ`
2. Observations 按 `(pattern, direction)` 聚合——所有支票支出被聚合到同一条 observation `(CHQ, debit)` 下，`classification_history` 混入多个不同科目，导致 `non_promotable: true`，永远无法升级为 rule
3. Node 2 Rules 匹配失效——无法为不同的支票收款人建立独立的 rule
4. Node 3 AI 分类器查找 observation 历史时，拿到的是混合了所有支票收款人的脏数据，置信度判断不可靠
5. 支票交易的学习路径被完全切断：无法积累有意义的 observation → 无法升级 rule → 永远依赖 AI 或人工

**触发条件：**

Data Preprocessing Step 3（cheque image processing）在 Step 5（description standardization）之前执行，所以调用 `standardize_description` 时 `cheque_info`（含 payee_name）已经可用，但接口不接受这个参数。

**涉及 spec：**

- `tools/pattern_standardization_spec.md` — 接口定义缺少 `cheque_info` 参数
- `ai bookkeeper 8 nodes/data_preprocessing_agent_spec_v3.md` — Step 3 产出 cheque_info，Step 5 调用 standardize_description 时未传递

**修复方向（待确认）：**

`standardize_description` 增加可选的 `cheque_info` 参数。当 `cheque_info` 存在且包含 `payee_name` 时，用 payee_name 作为 LLM 提取的基础，使 canonical pattern 变为具体收款人名称（如 `944217 ONTARIO INC`）而非 `CHQ`。

---

### BUG-002: Node 1 / Pattern Standardization 在 transfer 匹配字段上的 contract 未定

**严重程度：** 高

**问题描述：**

Profile 中 `account_relationships.pattern`（如 `TFR-TO 6337546`）是基于银行原始流水字符串定义的。但 Data Preprocessing Agent 会产出标准化后的 `description`，而 Node 1 到底应该读取 `raw_description`、`description`，还是某个专门保留 transfer 信号的字段，当前 contract 还没有定死。

这不是单一节点实现错误，而是 Data Preprocessing / Pattern Standardization / Node 1 之间的跨节点字段契约未明确。

**影响：**

1. Node 1 的内部转账识别逻辑无法正常工作
2. 所有内部转账会穿透到 Node 2/3，被当作普通交易处理
3. 无法正确生成 internal_transfer 类型的 JE（需要两个银行账户互借互贷）

**涉及 spec：**

- `ai bookkeeper 8 nodes/profile_spec.md` — account_relationships.pattern 定义
- `ai bookkeeper 8 nodes/data_preprocessing_agent_spec_v3.md` — Step 5 description standardization 在 pipeline 中的位置
- `tools/pattern_standardization_spec.md` — standardize_description 的输出字段

**待决策：**

需要确定 Node 1 的匹配目标：用 `raw_description` 匹配（保持 pattern 为银行原始格式），还是重新定义 `account_relationships.pattern` 为 canonical pattern 格式。该问题暂时保留在 buglist，待 contract 层统一决策后再回写各 spec。

---

## Node 1 — Profile Match

（暂无独立 bug；BUG-002 为跨节点 contract 问题，暂存于 buglist 待统一决策）

---

## Node 2 — Rules Match

（暂无 bug）

---

## Node 3 — AI Classifier

### BUG-005: owner_uses_company_account 对零售类 vendor 的高置信度限制过于绝对

**严重程度：** 高

**问题描述：**

Node 3 spec 将 `profile.owner_uses_company_account = true` + 零售类 vendor 视为高置信度的硬性否决条件。这会把有强证据的交易也强行压回 PENDING，例如：

1. `T03`：HOME DEPOT 且 receipt.items 已明确是施工材料
2. `T12`：DOLLARAMA 且 observation 历史长期单一，用于验证 review correction 路径

**影响：**

1. synthetic pack 中设计好的 Section B / review correction 路径无法被真正触发
2. receipt 作为最强信号的设计价值被削弱
3. 系统会对一批本可高置信度处理的交易过度保守

**涉及 spec：**

- `ai bookkeeper 8 nodes/confidence_classifier_spec.md`
- `dry_run_codex/dry-run-pipeline-workflow/references/synthetic_pack_v1/expected_routing_map.md`

**修复方向：**

将 `owner_uses_company_account` 从绝对 veto 调整为默认降置信度规则；当 receipt、supplementary_context 或稳定单一 observation 已提供足够强的业务反证时，允许高置信度。

---

## JE Generator

### BUG-004: HST 控制科目命名与 revenue 校验规则不一致

**严重程度：** 高

**问题描述：**

`build_je_lines.py` 使用 `HST/GST Receivable` / `HST/GST Payable`，但 `validate_je` 示例和校验规则仍写 `HST Receivable` / `HST Payable`，且 inclusive 校验只明确要求 receivable，没有把收入侧 payable 说清。

**影响：**

1. 同一 shared contract 在 JE / Transaction Log / Output Report 之间不一致
2. 合法的收入类 inclusive JE 可能被错误判 invalid
3. dry run 无法稳定判断哪个名字才是 canonical

**涉及 spec：**

- `ai bookkeeper 8 nodes/je_generator_spec.md`
- `ai bookkeeper 8 nodes/transaction_log_spec.md`
- `ai bookkeeper 8 nodes/output_report_spec.md`
- `dry_run_codex/dry-run-pipeline-workflow/references/synthetic_pack_v1/client_foundation_pack.json`

**修复方向：**

统一使用 `HST/GST Receivable` / `HST/GST Payable`，并让 inclusive 校验同时覆盖支出侧 receivable 与收入侧 payable。

---

## Coordinator Agent

（暂无 bug）

---

## Output Report

### BUG-003: Output Report 的生成时机与 Review Agent 输入契约冲突

**严重程度：** 高

**问题描述：**

Dry run workflow 和 handoff schema 都要求 Output Report 节点在 Review Agent 前生成 `report_draft`。但 `output_report_spec.md` 目前写的是“输出报告不是审核载体”，且“审核完毕后才按需生成”。

**影响：**

1. Step 7 → Step 8 的接口在 spec 层不闭环
2. Review Agent 依赖的 Section A / B / C 输入来源不清
3. 最终交付物与审核前快照被混成同一个概念

**涉及 spec：**

- `ai bookkeeper 8 nodes/output_report_spec.md`
- `.claude/commands/dry-run-pipeline-workflow.md`
- `dry_run_codex/dry-run-pipeline-workflow/agents/output_report.md`
- `dry_run_codex/dry-run-pipeline-workflow/references/handoff_schema.md`

**修复方向：**

区分两个产物：审核前 `report_draft` 与审核后最终 `.xlsx` 导出。

---

## Review Agent

（暂无 bug）

---

## Onboarding Agent

（暂无 bug）

---

## Shared Tools

### Pattern Standardization

（BUG-001 同时涉及此工具，详见 Data Preprocessing Agent 节）

### Layer 3 文档补全（已修复）

**问题描述：** Layer 3 LLM 提取后写回 Pattern Dictionary 的步骤在原 spec 的流程图中有简要提及，但 Layer 3 详细说明段落中缺少显式描述。

**修复：** 已在 `tools/pattern_standardization_spec.md` Layer 3 部分补充"写回字典"段落，明确记录写回行为、key/value 来源和 source 标记。
