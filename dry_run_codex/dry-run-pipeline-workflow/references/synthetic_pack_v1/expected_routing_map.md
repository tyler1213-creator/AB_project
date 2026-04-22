# Synthetic Dry Run Pack v1 — Expected Routing Map

本文件定义 `T01-T12` 这 12 笔 synthetic 交易理论上应该走的设计路径。

它的用途不是把答案直接喂给节点，而是让 orchestrator 在运行结束后比对：

- 实际路径是否与设计预期一致
- 不一致时，问题更像是 `design bug`、`interface mismatch`，还是 `prompt / orchestration issue`

---

## 总表

| Case | 核心场景 | 预期主路径 | 预期最终状态 | 重点检查 |
|---|---|---|---|---|
| T01 | 内部转账 | DP -> Node 1 -> JE | classified | transfer 字段契约、internal_transfer JE |
| T02 | 稳定 telecom recurring | DP -> Node 1 miss -> Node 2 -> JE | classified | rule schema 是否闭环 |
| T03 | HOME DEPOT + receipt | DP -> N1 miss -> N2 miss -> N3 high -> JE | classified | observation + receipt + HST |
| T04 | AMAZON 无 receipt | DP -> N1 miss -> N2 miss -> N3 pending -> Coordinator | accountant_confirmed | pending with options |
| T05 | EMT 分包款 | DP -> N1 miss -> N2 miss -> N3 pending -> Coordinator | accountant_confirmed | pending without enough context |
| T06 | mixed-use COSTCO | DP -> N1 miss -> N2 miss -> N3 pending -> Coordinator split -> retrigger | split + child transactions completed | split / parent-child / supplementary_context |
| T07 | CHQ + cheque_info | DP -> N1 miss -> N2 miss -> N3 or pending | classified or surfaced bug | cheque_info 穿透、BUG-001 |
| T08 | fallback pattern | DP -> N1 miss -> N2 miss -> N3 pending | unresolved or accountant_confirmed | fallback 不写 observations |
| T09 | payroll-like, no employees | DP -> N1 miss -> N2 miss -> N3 pending anomaly -> Coordinator | accountant_confirmed + profile update | profile constraint / retrigger decision |
| T10 | monthly bank fee | DP -> N1 miss -> Node 2 -> JE | classified | simple deterministic path |
| T11 | force_review observation | DP -> N1 miss -> N2 miss -> N3 pending | accountant_confirmed | force_review contract |
| T12 | review correction case | DP -> N1 miss -> N2 miss -> N3 high -> JE -> Review | corrected in review | transaction log + intervention chain |

---

## Case-by-Case Notes

### T01

- Expected pattern / matching signal: `ONLINE BANKING TRANSFER TO SAVINGS 6337546`
- Expected node outcome: Node 1 should classify it as internal transfer using `profile.account_relationships`
- If it fails:
  - likely `BUG-002`
  - or Node 1 input contract still mismatches transfer fields

### T02

- Expected canonical pattern: `ROGERS WIRELESS`
- Expected rule hit: `R-001`
- Expected classification:
  - account: `Telephone & Internet`
  - hst: `inclusive_13`

### T03

- Expected canonical pattern: `HOME DEPOT`
- Expected Node 3 high-confidence because:
  - receipt exists
  - observation history is clean
  - COA has a clear target account
- Expected classification:
  - account: `Supplies & Materials`
  - hst: `inclusive_13`

### T04

- Expected canonical pattern: `AMAZON` or equivalent marketplace pattern
- Expected Node 3 result: pending with options
- Expected option set should include at least:
  - `Office Supplies`
  - `Supplies & Materials`
  - `Shareholder Loan`
- Coordinator should be able to present these options cleanly

### T05

- Expected Node 3 result: pending without enough business context
- Coordinator should ask for business purpose
- Accountant script should resolve it as:
  - account: `Subcontractor Expense`
  - hst: `inclusive_13`

### T06

- Expected Node 3 result: pending
- Coordinator should accept split instruction
- Expected split:
  - child A: `300.00` -> `Office Supplies`, `inclusive_13`
  - child B: `217.43` -> `Shareholder Loan`, `exempt`
- After split, child transactions should either:
  - be directly completed from accountant input
  - or re-enter workflow with `supplementary_context`

### T07

- Expected watchpoint case
- `cheque_info.payee = 944217 Ontario Inc` and `memo = Excavation deposit` should be available downstream
- Desired behavior:
  - Node 3 can use cheque_info as strong evidence
- Known risk:
  - pattern may collapse to `CHQ`, surfacing `BUG-001`
- This case is successful even if it reveals the bug, as long as the failure is crisply explainable

### T08

- Expected standardization result: fallback pattern
- Expected `pattern_source = fallback`
- Expected downstream contract:
  - may go pending
  - must **not** contribute to observations promotion path

### T09

- Initial profile says `has_employees = false`
- Node 3 should treat payroll-like classification as structurally suspicious and route to pending
- Coordinator script should update profile and classify transaction as:
  - account: `Wages Expense`
  - hst: `exempt`
- This case tests whether profile updates can coexist with current batch resolution

### T10

- Expected rule hit: `R-002`
- Expected classification:
  - account: `Bank Charges`
  - hst: `exempt`

### T11

- Expected observation hit:
  - `force_review = true`
- Node 3 should not auto-classify
- Coordinator should gather accountant answer
- Expected accountant answer:
  - account: `Meals & Entertainment`
  - hst: `inclusive_13`

### T12

- Expected Node 3 high-confidence classification:
  - account: `Office Supplies`
  - hst: `inclusive_13`
- Review stage should later correct it to:
  - account: `Shareholder Loan`
  - hst: `exempt`
- This case tests:
  - post-classification correction path
  - transaction log update path
  - intervention log linkage

---

## Orchestrator Evaluation Rules

If actual routing differs from expected routing, classify the deviation as one of:

1. `design_bug`
2. `interface_mismatch`
3. `schema_gap`
4. `prompt_scope_issue`
5. `acceptable alternate path`

Do not mark every deviation as a bug. The goal is to learn whether the system design remains coherent, not to force every subagent to match a script word-for-word.
