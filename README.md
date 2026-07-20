# AI Abuse Analytics

A privacy-safe, reproducible Trust & Safety analytics workbench for AI developer-tool abuse investigation.

> **Portfolio scope:** this is an independent synthetic project inspired by the analytical problems described in a GitHub Data Analyst role supporting Copilot Trust & Safety. It does not use GitHub internal data, internal rules, or production systems.

## Executive summary

The project answers a practical operating question:

> With limited analyst review capacity, which AI-product accounts should be investigated first, why were they prioritized, how do we avoid harming legitimate users, and did a mitigation actually reduce harmful behavior?

It models the complete analytical loop rather than a single classifier:

```text
privacy-safe synthetic telemetry
        ↓
data contracts + signal coverage
        ↓
emerging-trend monitoring
        ↓
SQL feature mart
        ↓
risk + anomaly + conservative entity linkage
        ↓
review capacity + FPR/FNR + calibration
        ↓
shadow rules + promotion / rollback gates
        ↓
investigation queue + case evidence + competing explanations
        ↓
human review / enforcement / appeal / overturn feedback
        ↓
mitigation measurement + uncertainty
        ↓
threshold / rule / taxonomy revision
```

The default analyst layer does **not** expose raw prompts, completions, IP addresses, payment details, or device identifiers. Scores and candidate rules are used for investigation prioritization, not automatic enforcement.

## What decisions does it support?

The workbench is built around eight recurring questions:

1. Which accounts should investigators review first under a fixed analyst-hour budget?
2. Is unusually high usage abuse, legitimate power use, approved automation, or enterprise infrastructure?
3. Are accounts linked by reliable identity evidence, or merely by shared NAT/VPN/network context?
4. Why was an account prioritized and what competing benign explanations must be checked?
5. Did telemetry coverage or a data producer change before a detection metric moved?
6. Is a candidate rule safe enough to leave shadow mode, and what would trigger rollback?
7. Are review, appeal, and overturn outcomes showing systematic false-positive harm?
8. Did a mitigation reduce abuse after accounting for comparison-group movement and uncertainty?

## Synthetic abuse scenarios

The generator creates realistic-but-synthetic mixtures of:

- scripted automation;
- credential sharing;
- token misuse;
- quota / entitlement evasion;
- coordinated abuse;
- policy / prompt-injection-related safety signals.

It also creates deliberately difficult legitimate confounders:

- high-intensity power users;
- enterprise/shared infrastructure;
- security-research behavior;
- normal variation in device, IP, model-surface, and usage patterns.

This prevents the benchmark from becoming a trivial `high usage = abuse` exercise.

## v0.3: operational analytics controls

### 1. Population drift and calibration

`src/copilot_trust/drift.py` produces:

- `feature_drift_diagnostics.csv`: Population Stability Index (PSI) diagnostics between development and holdout populations;
- `risk_calibration_bins.csv`: predicted risk versus observed known-abuse rate by risk bin.

The operating rule is explicit: a population-shift diagnostic should trigger investigation of instrumentation and segment mix before model changes.

### 2. Queue SLA and analyst capacity

`src/copilot_trust/queue_ops.py` converts flagged accounts into an operational queue with:

- P0–P3 priority tiers;
- queue age and synthetic service-level targets;
- estimated review minutes;
- risk-per-review-minute prioritization;
- analyst-hour scenarios for expected case coverage and known-abuse recall.

The purpose is to connect model output to real review capacity rather than report AUC alone.

### 3. Versioned rule registry and rollback

`src/copilot_trust/rule_registry.py` turns shadow evaluation into an auditable rule register with:

- rule ID and version;
- current stage (`shadow_more_evidence`, `shadow_revise`, or `canary_review_queue`);
- promotion gates;
- rollback triggers;
- an explicit `automatic_enforcement_allowed = false` boundary.

A rule with 100% holdout precision on only two triggered accounts is not treated as production-ready evidence.

### 4. Self-service semantic layer

`sql/06_self_service_semantic_views.sql` defines stable account-review and daily-health views so dashboards do not repeatedly redefine precision, false-positive rate, review workload, or signal coverage.

## Benchmark snapshot

The checked benchmark uses `180` synthetic accounts with seed `17`.

| Metric | Value |
|---|---:|
| Holdout accounts | 54 |
| ROC AUC | 0.914 |
| Average precision | 0.653 |
| Brier score | 0.070 |
| Precision at selected threshold | 0.500 |
| Recall at selected threshold | 0.400 |
| False-positive rate | 0.041 |

These values are **synthetic benchmark results, not production performance claims**. The small holdout is intentionally treated as uncertain: slice metrics include reportability checks, candidate rules require sufficient trigger volume, and mitigation estimates include uncertainty intervals.

## Detection is not enforcement

The risk score combines three signal families:

```text
0.68 × supervised probability
+ 0.17 × anomaly score
+ 0.15 × linked-entity signal
```

Those weights are benchmark design choices, not a claim about any GitHub system.

A high score means:

```text
prioritize for investigation
```

It does **not** mean:

```text
automatically suspend the user
```

Every case bundle includes evidence, recent activity, identity-context cautions, competing explanations, and an evidence standard before escalation.

## Conservative linked-account analysis

Entity linkage uses different reliability levels:

| Entity | Benchmark reliability | Use |
|---|---:|---|
| token fingerprint | 1.00 | strong linkage seed with lifecycle context |
| payment fingerprint | 0.90 | strong supporting linkage |
| device fingerprint | 0.80 | useful with corroboration |
| IP context | 0.35 | supporting context only |

High-degree shared entities are prevented from automatically seeding components. IP sharing alone is never treated as identity proof because NAT, VPNs, enterprise egress, managed fleets, and shared runners can create legitimate overlap.

## Emerging-trend monitoring and data incidents

`src/copilot_trust/monitoring.py` tracks daily:

- requests per active account;
- agent usage share;
- prompt-injection signal rate;
- content-policy signal rate;
- safety-block rate;
- near-quota account rate;
- IP and device signal missingness.

Alerts use rolling robust baselines, MAD-based robust z-scores, materiality checks, and persistence/extreme-event gates.

The synthetic benchmark also injects a short IP-telemetry coverage incident. The required action is to repair/annotate the data incident before detection retuning.

## Shadow rule lifecycle

Candidate rules cover identity dispersion, shared tokens, scripted usage, quota evasion, and policy-signal escalation.

Each rule reports:

- development and holdout trigger volume;
- precision and recall;
- false-positive rate;
- review workload;
- legitimate-confounder hits;
- promotion recommendation.

The rule registry then adds versioning, owner, promotion gate, rollback trigger, and enforcement boundary.

## Review → appeal → overturn feedback

Synthetic case-management data includes:

```text
investigation_id
review_date
review_outcome
enforcement_action
appeal_filed
appeal_outcome
final_outcome
decision_latency_hours
taxonomy_version
policy_version
```

Recent review outcomes are treated as delayed labels using a maturity window. Cleared cases and overturned enforcement decisions are negative feedback for threshold/rule review rather than being discarded.

## Mitigation measurement

The project builds an account-day panel and reports a difference-in-differences-style diagnostic with:

- treated versus comparison groups;
- pre/post means;
- bootstrap 95% interval;
- pre-trend slopes.

The benchmark output explicitly states that the synthetic assignment is not randomized and the result is not causal proof.

## Data quality as part of the detection system

Contracts check:

- required schema;
- request-ID uniqueness;
- account referential integrity;
- model-family domain;
- daily IP/device/token/payment signal coverage.

A telemetry regression is treated as a detection-system incident. The project also generates a signal-integration backlog linking each proposed data source to the analytical problem, decision, privacy class, and partner team.

## Stakeholder outputs

The pipeline creates different decision products for different audiences:

- `brief_trust_safety.md`: investigation, user-impact, rule-readiness, review feedback, mitigation evidence;
- `brief_engineering.md`: telemetry failures and highest-value integration requests;
- `brief_cela_governance.md`: purpose limitation, raw-content boundaries, identity linkage, enforcement boundaries, and auditability;
- `stakeholder_action_register.csv`: priority, decision, evidence, action, owner, partners, and review gate.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_all.py --n-accounts 180 --seed 17
```

Run tests:

```bash
pytest -q
```

The pipeline generates synthetic event data locally, rebuilds all analytical artifacts, and writes `docs/index.html` as the Decision Center.

## Repository map

```text
src/copilot_trust/
  generate.py          synthetic telemetry + review feedback
  features.py          SQL-style account feature mart
  scoring.py           supervised + anomaly + graph risk scoring
  monitoring.py        recurring trend monitoring
  data_quality.py      contracts + signal-integration backlog
  rules.py             shadow rule evaluation
  rule_registry.py     versioning, promotion, rollback
  investigate.py       queue, case bundles, linked-account evidence
  feedback.py          review / appeal / overturn loop
  mitigation.py        DiD-style mitigation diagnostics
  drift.py             PSI + calibration diagnostics
  queue_ops.py         SLA / analyst-capacity planning
  stakeholder.py       cross-functional decision outputs
  reporting.py         Decision Center + executive brief

sql/                    analyst queries and semantic views
config/                 taxonomy + metric contracts
docs/                   architecture, governance, runbooks, operating model
tests/                  integration and enforcement-boundary tests
.github/workflows/       reproducible CI benchmark
```

## Production boundary

CSV + SQLite/Pandas are used for a local, reproducible portfolio benchmark. A production design would use partitioned event-time marts, incremental materialization, late-arrival handling, idempotent backfills, restricted raw-content access, and versioned data/taxonomy contracts.

This repository intentionally does not pretend to reproduce GitHub production scale or internal systems.
