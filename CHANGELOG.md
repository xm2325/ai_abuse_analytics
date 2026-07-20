# Changelog

## v0.6.0 — billing and entitlement abuse analytics

- Added a separate synthetic entitlement ledger rather than treating telemetry as the billing source of truth.
- Added cycle-level usage and effective-allowance analysis.
- Added billing-family aggregation for multi-account entitlement-pressure investigation.
- Added legitimate managed/shared-billing context as an explicit competing explanation before escalation.
- Added privacy-safe entitlement investigation queues using pseudonymous billing-family references rather than raw payment details.
- Added entitlement schema, referential-integrity, and account-cycle uniqueness contracts.
- Added minimum benchmark coverage for all six abuse scenarios when sample size is sufficient, so CI cannot silently omit a JD-relevant scenario because of random sampling.
- Added approved organization contexts with legitimate shared token/payment/runner entities. These contexts are excluded from model features and exist to prevent entity linkage from becoming a label shortcut.
- Added Decision Center reporting, SQL investigation workflow, documentation, tests, and CI artifact contracts.

Billing-family, shared-entity, and near-limit signals remain investigation leads only. Shared billing, shared infrastructure, or high utilization never authorizes automatic enforcement.

## v0.5.0 — historical replay, evidence power, and queue stress testing

- Added time-based historical replay with explicit no-lookahead windows and replay phases around mitigation and emerging-abuse changes.
- Froze distribution-derived shadow-rule thresholds on the development split before holdout evaluation, removing holdout threshold adaptation.
- Added one-sided uncertainty bounds for rule FPR and precision so small clean samples are not treated as sufficient policy evidence.
- Added mature-label coverage at each replay checkpoint; unresolved or not-yet-mature labels are not silently treated as negatives.
- Added synthetic analyst queue arrival/service simulation across 0.5, 1.0, and 2.0 FTE scenarios, including backlog, SLA, utilization, and p95 time-to-review diagnostics.
- Added Decision Center sections, SQL replay example, operating documentation, tests, and CI artifact contracts for the new controls.

All v0.5 outputs remain investigation and policy-review decision support. They never authorize automatic enforcement.

## v0.4.0 — threshold policy simulation

- Added a threshold frontier for human-review policy planning.
- Added hard guardrails for global FPR, review workload, worst reportable slice FPR, minimum precision, and minimum triggered-account evidence volume.
- Added an explicit `no_threshold_meets_all_guardrails` outcome rather than forcing a policy choice.
- Added SQL threshold-frontier example and policy-review documentation.
- Extended CI/tests to require the new policy artifacts.

On the 180-account seed-17 synthetic benchmark, no threshold had enough evidence to satisfy every guardrail. The diagnostic least-violation threshold is not a production recommendation.
