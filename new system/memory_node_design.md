# Memory Node Design

> Deprecated for active design work.
>
> This file is retained as historical brainstorming material only. Its accepted
> contract details have been consolidated into `new system/new_system.md`.
> Do not continue updating this file during new-system convergence.

## Document role

This document previously recorded accepted design details for the new system's memory layer.

It is no longer a working design record. `new_system.md` is the only active
new-system design source.

## Brainstorm sections

The new-system core design is being converged in these sections:

1. `Entity Memory / Entity Resolution（实体记忆 / 实体识别）`
2. `Case Memory（案例记忆）`
3. `Entity-based Rules（基于实体的规则）`
4. `Runtime Handoff / Evidence Pack（运行时交接 / 证据包）`
5. `Governance / Review / Lint Pass（治理 / 审核 / 批后体检）`
6. `Transaction Log / Audit Trace（交易日志 / 审计轨迹）`
7. `Onboarding New Baseline（新系统初始化流程）`
8. `Synthetic Dry Run Baseline（合成 dry run 基线）`

## Section 1: Entity Memory / Entity Resolution

Status: completed.

### Confirmed decisions

#### Entity grain

`Entity（实体）` uses `counterparty/vendor/payee + role/context（交易对手/商家/收款人 + 角色/上下文）` as its conceptual grain.

The entity layer answers:

- who the object is
- what role/context it has in this client relationship

The entity layer does not directly answer:

- which COA account should be used
- which HST treatment should apply
- whether this transaction should be booked automatically

Those decisions belong to `case memory（案例记忆）`, `rules（规则）`, Node 3, and accountant governance.

#### Role authority

Runtime role inference is conservative.

- The system may propose `candidate_role（候选角色）`.
- A stable role requires accountant confirmation.
- Onboarding may create `accountant_derived_role（来自会计历史数据推导的角色）` as a controlled exception when the source is accountant-prepared historical books, but this must carry explicit authority/source metadata.

#### Entity resolution status

`entity_resolution_status（实体识别状态）` has five values:

- `resolved_entity（已识别实体）`: safely resolved to one stable entity.
- `resolved_entity_with_unconfirmed_role（已识别实体但角色未确认）`: the object is known, but its role/context for this client is not confirmed.
- `new_entity_candidate（新实体候选）`: likely a new object not yet in stable entity memory.
- `ambiguous_entity_candidates（多实体歧义）`: could match multiple known entities or roles; unsafe to choose automatically.
- `unresolved（无法识别）`: evidence is insufficient to identify the object.

#### New entity candidate behavior

`new_entity_candidate（新实体候选）` does not automatically block current-period classification.

Allowed:

- Node 3 may classify the current transaction as high confidence if current evidence is strong enough.
- The transaction may create a candidate entity and a case-memory record.

Not allowed:

- It cannot match a deterministic rule.
- It cannot become a stable entity without governance.
- It cannot create or promote a rule without accountant review.

#### Entity fields

A stable `Entity（实体）` should use a medium field set:

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

The entity contract should not contain COA classification, HST treatment, embedding/vector implementation details, or tax profiles as core fields.

#### Alias governance

`aliases（别名/表面写法）` use three states:

- `candidate_alias（候选别名）`: may help Node 3 as context; cannot support rule match.
- `approved_alias（已确认别名）`: can support entity resolution and deterministic rule match.
- `rejected_alias（已拒绝别名）`: negative evidence for future matching.

#### Role storage

`roles（角色/上下文）` are not stored as a long-term three-state list.

- Stable entity records store only confirmed roles.
- Runtime `candidate_role（候选角色）` belongs in `entity_resolution_output（实体识别输出）`, not in the long-term entity record.
- Onboarding-derived roles must carry source/authority metadata if accepted as a controlled exception.

#### Entity lifecycle status

`status（生命周期状态）` is separate from automation eligibility.

Values:

- `candidate（候选实体）`: proposed entity, not yet stable.
- `active（有效实体）`: confirmed long-term entity that can be referenced.
- `merged（已合并实体）`: old entity merged into another entity; kept for audit and redirection.
- `archived（归档实体）`: retained for history but not used in normal matching.

`active（有效实体）` is necessary but not sufficient for rule match.

#### Automation policy

`automation_policy（自动化策略）` controls whether an entity may participate in automatic classification.

Values:

- `eligible（允许自动化）`: allows deterministic rule match and Node 3 case-based high confidence.
- `case_allowed_but_no_promotion（允许案例自动化但禁止规则升级）`: allows case-based high confidence, but blocks rule-promotion candidacy.
- `rule_required（需要规则才可自动化）`: only approved rules may automate; no-rule cases go PENDING.
- `review_required（必须人工复核）`: entity can be identified, but every transaction requires accountant confirmation.
- `disabled（禁用自动化）`: no automatic classification path is allowed.

`rule_required（需要规则才可自动化）` is preferred over the earlier phrase `rule_only（只允许明确规则自动化）`.

#### Automation and rule governance

Entity-level automation policy and rule lifecycle governance are separate.

- The system may automatically downgrade `automation_policy（自动化策略）` during `lint pass（批后体检）`, for example from `eligible（允许自动化）` to `case_allowed_but_no_promotion（允许案例自动化但禁止规则升级）` or `rule_required（需要规则才可自动化）`.
- Upgrading or relaxing `automation_policy（自动化策略）` requires accountant approval.
- Every `rules（规则）` creation, upgrade, modification, deletion, or downgrade requires accountant review and approval.
- The system can place candidates into `rule_governance_queue（规则治理队列）`, but cannot modify active rules by itself.

#### Entity resolution output

`entity_resolution_output（实体识别输出）` should use a medium field set:

- `status（识别状态）`: one of the five `entity_resolution_status（实体识别状态）` values.
- `entity_id（实体唯一标识）`: resolved stable entity ID when one safe entity is identified.
- `confidence（识别置信度）`: confidence in the entity-resolution result, not the accounting classification.
- `reason（识别理由）`: short human-readable explanation of why this status/entity was chosen.
- `matched_alias（命中的别名）`: alias or surface text that matched the transaction evidence.
- `alias_status（别名状态）`: whether the matched alias is `candidate_alias（候选别名）`, `approved_alias（已确认别名）`, or `rejected_alias（已拒绝别名）`.
- `candidate_role（候选角色）`: system-proposed role/context for this transaction, not persisted as a stable role unless accountant confirms it.
- `evidence_used（使用的证据）`: evidence sources used for this resolution, such as raw description, receipt vendor, cheque payee, historical ledger name, or accountant context.
- `blocking_reason（阻断原因）`: why this result cannot support deterministic automation, if applicable.
- `candidate_entities（候选实体列表）`: possible matching entities when the status is ambiguous or unresolved.

The output should not expose implementation details such as embedding/vector hits, raw model prompt traces, or all rejected candidates as part of the stable contract.

#### Rule match prerequisites

A transaction may enter `rule match（规则命中）` only when all of the following are true:

- `entity.status（实体生命周期状态） = active（有效实体）`.
- `matched_alias（命中的别名）` is `approved_alias（已确认别名）`.
- Any role/context required by the rule is confirmed and satisfied.
- `automation_policy（自动化策略）` allows rule-based automation.
- An `active rule（有效规则）` exists for the resolved entity and applicable context.
- The transaction satisfies the rule's own conditions, such as `direction（方向）`, `amount_range（金额范围）`, and any approved conditional fields.

`lint warning（批后体检警告）` or recent `intervention（人工干预）` should affect future rule matching by changing `automation_policy（自动化策略）` or rule status through governance, not by adding ad hoc checks inside rule match.

#### Entity merge and split

`entity merge/split（实体合并/拆分）` is a governance action, not a runtime action.

Runtime may create:

- `merge_candidate（合并候选）`
- `split_candidate（拆分候选）`

Runtime may not directly merge or split stable entities.

Minimum rules:

- `merge entity（合并实体）`: the old `entity_id（实体唯一标识）` is not deleted. Its `status（生命周期状态）` becomes `merged（已合并实体）`, and it stores `merged_into_entity_id（合并目标实体 ID）`.
- `split entity（拆分实体）`: the original entity remains. Any split-out object receives a new `entity_id（实体唯一标识）`.
- Historical cases are not automatically mass-reassigned during split. Only accountant-confirmed cases may be migrated to the new entity.
- Active rules do not automatically follow merge or split. Related rule changes must enter `rule_governance_queue（规则治理队列）` and require accountant approval.
- Aliases may be proposed for migration during merge/split, but moving an `approved_alias（已确认别名）` requires accountant confirmation.
- Transaction Log history is not rewritten. Later merge/split interpretation is explained through governance events.

#### Entity governance events

All long-term changes to `entity memory（实体记忆）` must be recorded as `entity_governance_event（实体治理事件）`.

`event_id（治理事件唯一标识）` is the primary key for one governance action. `entity_id（实体唯一标识）` remains a required query index, but it does not replace `event_id（治理事件唯一标识）` because one entity can have many events, and one event can affect multiple entities.

Minimum fields:

- `event_id（治理事件唯一标识）`
- `event_type（治理事件类型）`: examples include `approve_alias（批准别名）`, `reject_alias（拒绝别名）`, `confirm_role（确认角色）`, `merge_entity（合并实体）`, `split_entity（拆分实体）`, `change_automation_policy（修改自动化策略）`
- `entity_ids（相关实体 ID 列表）`
- `affected_aliases（受影响别名）`
- `affected_roles（受影响角色）`
- `old_value（修改前值）`
- `new_value（修改后值）`
- `source（来源）`: examples include `lint_pass（批后体检）`, `review_agent（审核代理）`, `accountant_instruction（会计指令）`, `onboarding（初始化）`
- `requires_accountant_approval（是否需要会计批准）`
- `approval_status（批准状态）`: `pending（待批准）`, `approved（已批准）`, `rejected（已拒绝）`, `auto_applied_downgrade（自动降级已生效）`
- `accountant_id（会计标识）`
- `reason（原因说明）`
- `evidence_links（证据链接）`
- `created_at（创建时间）`
- `resolved_at（处理完成时间）`

Core rules:

- All long-term entity-memory mutations write an event.
- Events can be queried by `event_id（治理事件唯一标识）`, `entity_id（实体唯一标识）`, `approval_status（批准状态）`, `event_type（治理事件类型）`, and related transaction/case references when present.
- System-applied automation-policy downgrades may take effect immediately, but must be recorded as `auto_applied_downgrade（自动降级已生效）` and surfaced to Review Agent.
- Events requiring accountant approval cannot change long-term entity memory before approval.
- Review Agent should group events by business meaning and event type rather than showing raw event fields directly to accountant.

### Remaining questions for Section 1

No open Section 1 questions remain before consolidating related specs.
