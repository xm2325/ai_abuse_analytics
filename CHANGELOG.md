# Changelog

## v1.0.0 — Trust & Safety operating and audit layer

- Unified detection rules, candidate taxonomies, and policy experiments in `operating_control_registry.csv` with owners, lifecycle stages, evidence state, promotion gates, rollback triggers, source artifacts, and explicit no-auto-action boundaries.
- Added `decision_lineage.csv` so each current operating decision can be traced to evidence, owner/partners, recommended action, review gate, and lineage boundary.
- Added `data_lineage.csv` documenting source-of-truth separation, purpose, sensitivity, ownership, contracts, and freshness expectations across telemetry, accounts, entitlements, reviews, experiments, and evidence packages.
- Added `operating_slo_scorecard.csv` covering source-contract health, one-FTE queue health, rule-evidence maturity, canary matured-review evidence, and the automatic-action boundary.
- Added `incident_replay_register.csv` to reconstruct data-contract incidents and high-severity signal alerts with blast radius, response, replay evidence, and recovery gate.
- Added deterministic `decision_audit_trail.csv` for the ordered evidence flow from ingestion/contracts through detection, discovery, replay/resilience, experiment, investigation, decision routing, and release readiness.
- Added privacy-safe case-to-policy evidence packages under `artifacts/evidence_packages/`, linking investigation candidates to competing explanations, rule/evidence state, replay/resilience, experiment state, review feedback, privacy boundaries, and escalation gates.
- Added `release_readiness.json` summarizing operating-layer status, SLO gaps, registered controls, evidence packages, experiment state, and explicit no-auto-enforcement/no-auto-expansion boundaries.
- Added `docs/START_HERE.md` and a recruiter/manager-first v1.0 Operating Brief at the top of the Decision Center so the repository can be understood in a 2–3 minute review path.
- Rewrote the README around the end-to-end operating decision flow rather than version-by-version feature accumulation.
- Added v1.0 integration tests and CI artifact contracts for lineage, SLOs, audit, evidence packages, release readiness, governance boundaries, and Decision Center entry points.

v1.0 is a portfolio/demo operating layer, not a production certification. It does not claim GitHub internal data, production thresholds, real enforcement systems, formal production incident tooling, or real policy approval.

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

Policy experiment outputs are decision support only. No sequential metric auto-expands a canary, and no experimental result authorizes automatic enforcement.

## v0.8.0 — adversarial adaptation and detection-resilience stress testing

- Added frozen-rule adversarial stress tests across velocity smoothing, identity fragmentation, token rotation, quota spreading, policy-signal suppression, and blended multi-signal adaptation.
- Added four synthetic adaptation strengths per scenario to measure recall degradation rather than assume static behavior.
- Added per-rule brittleness outputs and a defense-in-depth diagnostic that compares diversified rule families against single-rule degradation.
- Added release-style evasion regression gates and evidence-volume-aware stakeholder routing.
- Added defensive SQL for near-boundary bunching, rule-overlap decay, canary rollback monitoring, and signal-diversity audits.

## v0.7.0 — unknown / emerging abuse discovery

- Added a benchmark-only hidden late-emerging pattern absent from the known abuse taxonomy.
- Added recent-vs-baseline multivariate novelty scoring, behavior-cohort clustering, candidate taxonomy proposals, telemetry-health diagnostics, and graph/context triage.
- Hidden benchmark labels are never used by ranking, clustering, graph triage, or taxonomy generation.

## v0.6.0 — billing and entitlement abuse analytics

- Added a separate synthetic entitlement ledger, cycle-level usage analysis, billing-family investigation, legitimate managed/shared-billing controls, and entitlement data contracts.
- Added minimum benchmark coverage for all six known abuse scenarios and approved organization contexts with legitimate shared token/payment/runner entities.

## v0.5.0 — historical replay, evidence power, and queue stress testing

- Added no-lookahead historical replay, frozen development thresholds, one-sided uncertainty/evidence-volume gates, delayed label maturity, and 0.5/1/2-FTE queue simulation.

## v0.4.0 — threshold policy simulation

- Added a threshold frontier with FPR, review-workload, worst-slice, precision, and trigger-volume guardrails plus an explicit `no_threshold_meets_all_guardrails` outcome.
