# Synthetic Dry Run Pack v1 — Accountant Simulation Script

本文件定义 orchestrator 在 Coordinator / Review 阶段应如何扮演 accountant。

目标不是“演戏”，而是以**最小但足够真实的输入**触发系统需要验证的状态变化。

---

## 使用原则

1. 只按本剧本提供信息，不临场扩展业务世界
2. 优先给出能触发明确系统动作的答复
3. 如果本轮目标是验证接口，不要故意制造多余歧义
4. 每条回复都应对应一类系统动作：
   - confirm classification
   - provide business context
   - request split
   - update profile
   - correct review result

---

## Coordinator Stage Responses

### Response A — Resolve T04

**When used:** Coordinator presents `T04` as pending with options.

**Reply:**

> T04 记 Office Supplies，inclusive HST。这笔是现场打印纸、记号笔和收纳盒。

**Expected system effect:**

- `T04` becomes `accountant_confirmed`
- classification:
  - account: `Office Supplies`
  - hst: `inclusive_13`

---

### Response B — Resolve T05

**When used:** Coordinator asks what `T05` was for.

**Reply:**

> T05 是付给 Jason Lee 的分包工程款，记 Subcontractor Expense，inclusive HST。

**Expected system effect:**

- `T05` becomes `accountant_confirmed`
- classification:
  - account: `Subcontractor Expense`
  - hst: `inclusive_13`

---

### Response C — Split T06

**When used:** Coordinator asks about the mixed-use COSTCO transaction `T06`.

**Reply:**

> T06 需要拆分。300.00 是办公室耗材，记 Office Supplies，inclusive HST；217.43 是老板个人购买，记 Shareholder Loan，exempt。

**Expected system effect:**

- `T06` is split into two child transactions
- parent transaction gets `child_transaction_ids`
- child A:
  - amount: `300.00`
  - account: `Office Supplies`
  - hst: `inclusive_13`
- child B:
  - amount: `217.43`
  - account: `Shareholder Loan`
  - hst: `exempt`

---

### Response D — Resolve T07

**When used:** Coordinator presents the cheque transaction `T07` as unresolved.

**Reply:**

> T07 是付给 944217 Ontario Inc 的挖机押金，记 Subcontractor Expense，inclusive HST。

**Expected system effect:**

- `T07` becomes `accountant_confirmed`
- If the system still loses cheque payee signal, record the failure as `BUG-001`

---

### Response E — Resolve T09 + Profile Update

**When used:** Coordinator flags `T09` as payroll-like while profile says `has_employees = false`.

**Reply:**

> 公司从 2024-07-01 开始有 2 名现场员工，profile 需要更新。T09 是工资，记 Wages Expense，exempt。

**Expected system effect:**

- profile update:
  - `has_employees = true`
- `T09` becomes `accountant_confirmed`
- classification:
  - account: `Wages Expense`
  - hst: `exempt`

---

### Response F — Resolve T11

**When used:** Coordinator presents `T11` after `force_review` blocked auto-classification.

**Reply:**

> T11 是和客户开会的餐费，记 Meals & Entertainment，inclusive HST。

**Expected system effect:**

- `T11` becomes `accountant_confirmed`
- classification:
  - account: `Meals & Entertainment`
  - hst: `inclusive_13`

---

## Review Stage Responses

### Review Correction 1 — Correct T12

**When used:** Review Agent presents `T12` as already classified office supplies.

**Reply:**

> T12 这笔改掉，不是 Office Supplies。它是老板个人买的东西，改成 Shareholder Loan，exempt。

**Expected system effect:**

- Transaction Log classification for `T12` is updated
- `classified_by` becomes `accountant_confirmed`
- intervention log records the correction reason

---

## Escalation Rule

If any transaction cannot be matched to a script line:

1. Do not invent a new accountant answer
2. Mark it as out-of-script
3. Record whether the miss was caused by:
   - routing drift
   - node output drift
   - missing schema field
   - orchestrator error
