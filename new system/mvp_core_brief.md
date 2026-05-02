# MVP Core Highlight and Core Loop Brief

## Document Role

This document defines the MVP's product core, validation loop, scope boundary, and design constraints.

It owns:

- MVP core highlight
- MVP validation intent
- MVP core loop
- MVP scope boundaries and non-goals
- high-level criteria for deciding whether later design work belongs in the MVP path

It does not own:

- node schemas
- implementation contracts
- detailed runtime handoff formats
- storage design
- implementation plans
- historical decision records

`new system/new_system.md` remains the active new-system design source. This brief constrains why and what the MVP should validate; detailed system design still belongs in focused design specs after the relevant functional logic is confirmed.

If this brief and an active product spec appear to conflict, stop and ask the user instead of silently merging assumptions.

---

## 1. MVP Positioning

AI Bookkeeper MVP does not primarily validate whether AI can automatically complete every bookkeeping task in one pass.

It validates whether the system can use a client's historical bookkeeping records and accountant feedback to form client-level bookkeeping memory, then use that memory to produce auditable, correctable, and continuously improving bookkeeping suggestions.

The MVP's core measure is not single-transaction classification accuracy. The core measure is whether the learning loop works.

---

## 2. Core Highlight

The MVP core highlight is:

**Client-level business-object understanding + auditable bookkeeping suggestions + accountant feedback learning flywheel.**

In other words:

```text
The system does not merely guess how to classify one transaction.
It gradually understands this client's business objects, historical treatments, and accountant judgment patterns,
then becomes more useful after each review or correction.
```

---

## 3. Three Value Pillars

### 3.1 Automated Bookkeeping Capability

The system learns from historical bookkeeping records:

- common vendors, payees, and customers
- business-object roles and contexts for this client
- historical COA classifications
- GST/HST treatments
- stable recurring patterns
- mixed-use or ambiguous patterns
- accountant judgment patterns

The goal is not a generic AI classifier. The goal is client-level bookkeeping memory.

### 3.2 Auditable Trust

Each suggestion must be traceable to:

- source transaction
- receipt, cheque, invoice, or other evidence
- similar historical cases
- system reasoning
- accountant approval or correction
- final JE
- audit trail

The MVP must prove that AI output is not a black box. It must be reviewable, traceable, and correctable by the accountant.

### 3.3 Accountant Feedback Learning Flywheel

Accountant correction must not only change the final result. It must become a learning signal.

Examples of learning signals:

- one-off exception
- vendor role correction
- business-purpose clarification
- mixed-use risk
- future review requirement
- reusable treatment candidate

The MVP must prove this loop:

```text
accountant correction
→ structured learning signal
→ better handling of the next similar transaction
```

---

## 4. MVP Core Loop

The MVP must run this loop end to end:

```text
historical bookkeeping records
→ extract client-level business objects / historical cases / initial memory
→ ingest new transactions
→ generate account / HST / JE suggestions
→ show evidence + reasoning trace
→ accountant approves or corrects
→ correction is recorded as structured learning
→ the next similar transaction improves
```

If the system only generates suggestions, it is only an AI classifier.

If it learns from correction and improves future handling, it starts becoming AI Bookkeeper.

---

## 5. Core Hypotheses To Validate

### Hypothesis 1: Historical books can become client-level memory

Historical records are not just reference material. They are the source of automation capability.

### Hypothesis 2: Client-level memory improves new-transaction handling

The system should be more reliable than a bare LLM because it knows how this client was treated historically.

### Hypothesis 3: Accountant review can be low-friction

The accountant should quickly see:

```text
what the system suggests
why it suggests that
which historical cases it used
what remains uncertain
how to approve or correct
```

### Hypothesis 4: Correction improves future performance

The system must record the reason and future applicability of a correction, not merely overwrite the final result.

---

## 6. Essential MVP Capabilities

### 6.1 Historical Onboarding

Minimum capability:

- read historical bookkeeping records
- extract common business objects
- connect historical classifications and HST treatments
- form historical cases or customer memory
- mark stable and risky patterns

### 6.2 Runtime Suggestion

Minimum capability:

- process new transactions
- use client profile context
- identify or candidate-match business objects
- retrieve similar historical cases
- suggest account / HST / JE treatment
- decide whether accountant review is required

### 6.3 Evidence-Backed Explanation

Each suggestion should include:

- suggested account
- suggested HST treatment
- JE input or JE result
- evidence used
- related historical cases
- reasoning summary
- uncertainty or risk

### 6.4 Accountant Review / Correction

The accountant should be able to:

- approve
- change account
- change HST treatment
- provide business purpose
- mark a one-off exception
- require future review
- explain how similar cases should be handled later

### 6.5 Structured Learning Update

Each correction should record:

- original suggestion
- final decision
- correction reason
- whether it is one-off
- whether it is reusable
- whether it affects similar transactions
- related transaction / evidence / case references

### 6.6 Audit Trail

Each completed transaction must be traceable through:

```text
source transaction
→ evidence
→ system suggestion
→ accountant decision
→ final JE
→ learning update if any
```

---

## 7. MVP Contract Principle

This brief does not freeze final node schemas.

Before synthetic dry run or implementation, the project must define the minimal executable contracts required to support the confirmed core-loop functional logic.

Those contracts must be derived from functional design discussions, not guessed in advance.

Principle:

```text
confirm functional logic
→ define necessary contracts
→ run dry run / implementation
```

The MVP does not require full future-state schemas, but it cannot proceed without the minimal contracts needed to execute and validate the core loop.

---

## 8. MVP Non-Priorities

The MVP should not prioritize:

- full autonomous bookkeeping
- payroll
- complex GST/HST edge cases
- intercompany workflows
- inventory-heavy workflows
- loan amortization
- capital asset / depreciation workflows
- complex shareholder loan workflows
- accrual adjustment
- multi-currency
- QBO export hardening
- full governance UI
- real-world ingestion robustness

These may matter later, but they should not distract from validating the MVP core loop.

---

## 9. Synthetic Dry Run Target

The next synthetic dry run should validate the MVP loop rather than the old node sequence.

It should validate whether:

- historical data can generate client-level memory
- new transactions can use that memory
- suggestions are evidence-backed
- the accountant can quickly approve or correct
- correction becomes structured learning
- the next similar transaction improves
- audit trail is complete enough
- risky or uncertain cases go to review
- one-off correction is not blindly promoted into a durable rule

Dry run is a validation tool. It should expose problems, not pre-solve every possible design issue.

---

## 10. MVP Success Criteria

### 10.1 Suggestion Quality

- Stable transactions receive reasonable suggestions.
- Mixed-use or ambiguous transactions surface risk.
- Uncertain cases go to review instead of being forced into automatic handling.

### 10.2 Review Efficiency

- The accountant can quickly understand system suggestions.
- Approve/correct cost is lower than judging from scratch.
- Review information is sufficient but not overloaded.

### 10.3 Learning Loop

- Correction is structured.
- The next similar transaction can use the correction.
- The system distinguishes one-off exceptions from reusable learning.

### 10.4 Auditability

- Final result is traceable to source evidence.
- JE aligns with classification and HST treatment.
- Accountant decision is recorded.
- Reasoning is reviewable.

### 10.5 Scope Discipline

- Complex edge cases do not pull the MVP off course.
- Full governance platform work is not started prematurely.
- The project does not drift back into a pattern-only workflow.

---

## 11. Later Design Principle

Later node or contract design should serve this line:

```text
historical memory
→ suggestion
→ review
→ structured learning
→ better future automation
```

To decide whether a function belongs in the MVP path, ask:

1. Does it directly help the system learn from history?
2. Does it directly improve new-transaction suggestions?
3. Does it reduce accountant review cost?
4. Does it turn correction into reusable future memory?
5. Does it strengthen audit traceability?

If not, it is probably not MVP-core work.

---

## 12. Final Summary

AI Bookkeeper MVP validates whether the system can form client-level bookkeeping capability from historical records and accountant feedback.

That capability should produce auditable, correctable, reusable bookkeeping suggestions and convert human intervention into better future automation.

The MVP is not about becoming fully autonomous immediately. It is about proving:

```text
client-level memory + auditable suggestions + accountant feedback
= a bookkeeping workflow that becomes more useful over time
```
