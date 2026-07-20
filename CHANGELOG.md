# Changelog

## v0.9.0 — investigation experimentation and causal policy evaluation

- Added a pre-rollout-only experiment assignment workflow so eligibility and randomization never use post-treatment behavior or hidden benchmark truth.
- Added cluster-randomized `control` / `shadow` / `canary` arms using stronger organization/token/payment context to reduce obvious treatment contamination.
- Added cluster-level ITT estimates, a clearly labeled Wald ATT-style diagnostic, pre-trend checks, a shadow placebo arm, and a prompt-length negative-control outcome.
- Added explicit behavior-displacement analysis across primary surface, alternate surfaces, total activity, and synthetic cross-account migration.
- Added interference audits that keep IP as context-only and never treat it as identity proof.
- Added sequential canary monitoring with conservative descriptive boundaries, user-impact guardrails, displacement checks, and human-reviewed stop / pause / rollback recommendations.
- Added matured review / appeal guardrails and exploratory heterogeneous-treatment-effect diagnostics with minimum cluster evidence-volume requirements.
- Added a benchmark-only hidden responder/migration manifest that is never used by assignment, estimation, HTE, or stopping-rule calculations.
- Added Decision Center views, stakeholder routing, SQL workflow, documentation, tests, CI artifact contracts, and version 0.9.0.

Policy experiment outputs are decision support only. No sequential metric auto-expands a canary, and no experimental result authorizes automatic enforcement. A production design would require formal power/MDE planning, experiment registry, exposure consistency, approved sequential inference, network-interference assumptions, privacy review, and policy-owner sign-off.

## v0.8.0 — adversarial adaptation and detection-resilience stress testing

- Added frozen-rule adversarial stress tests across velocity smoothing, identity fragmentation, token rotation, quota spreading, policy-signal suppression, and blended multi-signal adaptation.
- Added four synthetic adaptation strengths per scenario to measure recall degradation rather than assume static behavior.
- Added per-rule brittleness outputs and a defense-in-depth diagnostic that compares diversified rule families against single-rule degradation.
- Added release-style evasion regression gates, including a severe-adaptation recall floor and a rule-dependency review gate.
- Added stakeholder action routing for material resilience degradation, with canary/replay/rollback recommendations.
- Added defensive SQL for near-boundary bunching, rule-overlap decay, canary rollback monitoring, and signal-diversity audits.
- Added documentation, tests, CI artifact contracts, and version 0.8.0.

The stress suite uses coarse synthetic feature transforms only. It does not reproduce real product controls, publish operational thresholds, provide bypass steps, or authorize automatic enforcement.

## v0.7.0 — unknown / emerging abuse discovery

- Added a benchmark-only hidden late-emerging pattern that is absent from the known abuse taxonomy.
- Added recent-vs-baseline multivariate novelty scoring without using abuse labels or review outcomes.
- Added behavior-cohort clustering, candidate taxonomy proposals, and development-only shadow-rule definitions.
- Added telemetry-health diagnostics so behavioral novelty is separated from instrumentation incidents before escalation.
- Added graph/context triage with a strict boundary that IP-only overlap never proves common control.
- Added benchmark-only hidden-pattern recall calculated after discovery; the hidden manifest is never used by ranking, clustering, graph triage, or taxonomy generation.
- Added Decision Center views, SQL workflow, documentation, tests, and CI artifact contracts.

Novelty is not an abuse verdict. A discovered cohort must pass analyst competing-explanation review, independent shadow/replay validation, matured-label review, uncertainty guardrails, and queue-capacity checks before any policy change.

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
