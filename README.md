# AI Abuse Analytics

A privacy-safe, reproducible Trust & Safety analytics workbench for AI developer-tool abuse investigation.

> **Portfolio scope:** this is an independent synthetic project inspired by the analytical problems in a public GitHub Data Analyst role supporting Copilot Trust & Safety. It does not use GitHub internal data, rules, policy logic, prompts, completions, or production systems.

## Executive summary

The project starts from an operating problem, not a model:

> With limited analyst capacity, which accounts or account families should be investigated first, why, what benign explanations could produce the same signals, and is there enough evidence to change a detection or mitigation policy?

The workbench models the full decision loop:

```text
privacy-safe telemetry + account + entitlement sources
        ↓
data contracts and signal coverage
        ↓
emerging-trend monitoring
        ↓
SQL feature marts + conservative entity linkage
        ↓
risk / anomaly / candidate rule signals
        ↓
false-positive, calibration, evidence-volume and uncertainty checks
        ↓
historical replay + shadow / canary / rollback gates
        ↓
investigation queue + linked-account and billing-family evidence
        ↓
human review → enforcement decision → appeal / overturn feedback
        ↓
mitigation measurement + analyst-capacity stress testing
        ↓
rule / threshold / taxonomy / data-integration revision
```

The default analyst layer does **not** expose raw prompts, completions, IP addresses, raw device identifiers, card numbers, or payment details. Scores, rules, and billing-family signals prioritize human investigation; they never authorize automatic enforcement.

## What real work questions does it answer?

| Decision question | Main output | Failure mode the project guards against |
|---|---|---|
| What should analysts review first? | investigation queue, P0–P3 SLA, review-capacity scenarios | optimizing AUC without considering analyst workload |
| Is high usage actually abuse? | behavioral evidence + legitimate power-user controls | `high usage = abuse` |
| Are accounts truly linked? | token/payment/device/IP evidence with reliability rules | treating NAT, VPN, enterprise egress, or shared runners as identity proof |
| Is usage-limit evasion occurring? | cycle-level entitlement and billing-family analysis | treating high utilization or shared billing as automatic proof |
| Is a new rule ready? | shadow evaluation, uncertainty bounds, evidence-volume gate | promoting a rule because `precision=100%` on two cases |
| Did a rule still work later? | no-lookahead historical replay | random holdout performance hiding temporal failure |
| Can the team operationalize it? | queue arrival/service simulation | launching a rule that creates unmanageable backlog or SLA breaches |
| Did telemetry break? | schema, referential, uniqueness, and daily signal-coverage contracts | retuning detection because an upstream producer failed |
| Did mitigation work? | DiD-style diagnostic, bootstrap interval, pre-trend checks | claiming causal impact from a simple before/after chart |
| Are users being harmed? | FPR/FNR slices, appeals, overturns, label maturity | ignoring legitimate-user impact and delayed feedback |

## Synthetic benchmark design

The generator creates six abuse scenarios:

- scripted automation;
- credential sharing;
- quota / entitlement evasion;
- token misuse;
- coordinated abuse;
- policy / prompt-injection-related abuse.

For samples large enough to evaluate all scenarios, the benchmark guarantees minimum scenario coverage rather than allowing a random seed to omit an abuse type entirely.

It also creates deliberately difficult legitimate controls:

- high-intensity power users;
- security-research behavior with elevated safety signals;
- shared enterprise/network infrastructure;
- approved organization contexts that legitimately share pseudonymous token, billing, or managed-runner entities.

The approved-organization context is retained for investigation but intentionally excluded from model features. This prevents shared-entity signals from becoming a label shortcut.

## v0.6 — billing and entitlement abuse analytics

A major design rule is:

> Telemetry is not the billing source of truth.

`src/copilot_trust/entitlements.py` creates a separate synthetic entitlement ledger with:

```text
account_id
cycle_index
cycle_start / cycle_end
plan
billing_status
entitlement_limit_per_active_day
entitlement_contract_version
billing_family_ref
billing_context
managed_infrastructure
source_system
```

The analysis aligns usage to entitlement cycles and produces:

- `entitlement_cycle_usage.csv` — account-cycle utilization and near-limit state;
- `billing_family_risk.csv` — multi-account billing-family pressure and explicit shared-billing controls;
- `entitlement_investigation_queue.csv` — privacy-safe investigation leads;
- `entitlement_data_quality.csv` — schema, account-key, and account-cycle uniqueness checks.

A candidate billing family requires multiple linked accounts under simultaneous entitlement pressure. Even then it is only an investigation lead.

The benchmark separately creates legitimate managed/shared organization billing families. They are explicitly marked for enterprise-context review rather than evasion escalation.

See `docs/BILLING_ENTITLEMENT_INVESTIGATION.md` and `sql/09_entitlement_evasion_investigation.sql`.

## v0.5 — historical replay, evidence power, and queue stress

### No-lookahead replay

`historical_rule_replay.csv` evaluates rule versions at historical checkpoints using only events available up to each checkpoint.

Distribution-derived thresholds are learned once from the allowed development period and frozen before holdout/replay use. This removes silent threshold adaptation on evaluation data.

Replay periods include:

```text
pre-mitigation
post-mitigation
emerging-abuse campaign
```

### Mature labels only

Review outcomes are delayed in real operations. Replay therefore records `matured_label_coverage_of_triggers` and does not silently convert unresolved or immature cases into negatives.

### Evidence power

`rule_evidence_power.csv` reports both point estimates and one-sided uncertainty bounds:

```text
observed FPR
95% upper FPR bound
observed precision
95% lower precision bound
trigger volume
evidence sufficiency
```

A rule with zero observed false positives can still remain `shadow_more_evidence` when the sample is too small to support the target FPR.

### Queue stress testing

`queue_simulation_summary.csv` evaluates synthetic 0.5, 1.0, and 2.0 analyst-FTE scenarios using only arrival date, priority, risk proxy, and estimated review effort.

It reports:

- backlog;
- SLA breaches;
- utilization;
- maximum/final backlog;
- p95 time to review.

Benchmark labels are not used to prioritize the simulated queue.

See `docs/HISTORICAL_REPLAY_AND_EVIDENCE.md` and `sql/08_historical_rule_replay.sql`.

## Threshold policy is a decision problem, not a tuning problem

`policy_threshold_frontier.csv` evaluates candidate human-review thresholds against:

- global false-positive rate;
- review-capacity share;
- worst reportable slice FPR;
- minimum precision;
- minimum triggered-account evidence volume.

The system can return:

```text
no_threshold_meets_all_guardrails
```

rather than forcing a policy recommendation.

See `docs/THRESHOLD_POLICY_REVIEW.md` and `sql/07_threshold_policy_frontier.sql`.

## Conservative linked-account analysis

Entity signals have different meanings:

| Entity | Benchmark role |
|---|---|
| token fingerprint | strong link only with lifecycle/context review |
| billing/payment-family reference | strong supporting relation, but shared organization billing is a known confounder |
| device fingerprint | useful with corroboration; managed runners can be shared legitimately |
| IP context | supporting context only; never identity proof |

High-degree shared entities are prevented from automatically creating giant account components.

## Shadow rule lifecycle

Candidate rules cover identity dispersion, shared tokens, scripted usage, quota evasion, and policy signals.

The workflow is:

```text
hypothesis
  ↓
shadow rule
  ↓
frozen definition
  ↓
holdout + temporal replay
  ↓
evidence-volume / uncertainty review
  ↓
legitimate-user impact review
  ↓
queue-capacity review
  ↓
canary human-review queue OR remain in shadow
  ↓
rollback if user impact, appeals, queue SLA, or data contracts deteriorate
```

`automatic_enforcement_allowed` is always false in the rule registry.

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

Cleared cases and overturned enforcement decisions are negative feedback for rule/threshold review. Recent outcomes are subject to a label-maturity window.

## Emerging-trend monitoring and data incidents

Daily monitoring covers:

- requests per active account;
- agent usage share;
- prompt-injection and content-policy signal rates;
- safety-block rate;
- entitlement pressure;
- IP/device signal missingness.

The synthetic benchmark injects a telemetry-coverage incident. The required response is to repair or annotate the data problem before detection retuning.

## Mitigation measurement

The project builds an account-day panel and reports a difference-in-differences-style diagnostic with:

- treated and comparison groups;
- pre/post means;
- bootstrap 95% interval;
- pre-trend slopes.

This is an observational synthetic diagnostic, not causal proof.

## Stakeholder outputs

Different teams receive different decision products:

- `brief_trust_safety.md` — investigation priorities, user impact, rule readiness, review feedback, mitigation evidence;
- `brief_engineering.md` — telemetry failures and high-value data integrations;
- `brief_cela_governance.md` — purpose limitation, data-access boundaries, identity linkage, enforcement boundaries, auditability;
- `stakeholder_action_register.csv` — priority, evidence, recommended action, owner, partner teams, and review gate.

## Decision Center

Running the pipeline writes `docs/index.html` with sections for:

```text
executive decisions
emerging trends
historical replay and evidence sufficiency
billing and entitlement abuse
false-positive / legitimate-user impact
investigation
queue operations and stress testing
data quality
drift and calibration
mitigation
governance and appeal feedback
```

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

GitHub Actions independently rebuilds a synthetic benchmark, verifies the required decision artifacts, and uploads the decision package. Benchmark metrics are intentionally not hard-coded in this README because they change when the synthetic stress design changes; use the generated `model_metrics.json` and the CI artifact for the checked run.

## Repository map

```text
src/copilot_trust/
  generate.py             synthetic telemetry + review feedback
  synthetic_controls.py   legitimate entity-sharing confounders
  entitlements.py         separate billing/entitlement source and cycle analysis
  features.py             SQL-style account feature mart
  scoring.py              supervised + anomaly + graph risk scoring
  monitoring.py           recurring trend monitoring
  data_quality.py         contracts + signal-integration backlog
  rules.py                frozen shadow-rule evaluation
  evidence_power.py       uncertainty/evidence sufficiency
  rule_registry.py        versioning, promotion, rollback
  historical_replay.py    no-lookahead temporal replay
  investigate.py          queue, case bundles, linked-account evidence
  queue_ops.py            SLA / analyst-capacity planning
  queue_simulation.py     arrival/service stress testing
  feedback.py             review / appeal / overturn loop
  mitigation.py           DiD-style mitigation diagnostics
  drift.py                PSI + calibration diagnostics
  policy_simulation.py    threshold-policy frontier
  stakeholder.py          cross-functional decision outputs
  reporting.py            Decision Center + executive brief

sql/                       reusable analyst queries and semantic views
config/                    taxonomy + metric contracts
docs/                      architecture, governance, runbooks, operating model
tests/                     integration, safety-boundary, and artifact-contract tests
.github/workflows/          reproducible CI benchmark
```

## Production boundary

CSV + SQLite/Pandas are used for a local, reproducible portfolio benchmark. A production design would use event-time partitioned marts, incremental materialization, late-arrival handling, idempotent backfills, versioned contracts/taxonomies, restricted raw-content access, and controlled identity/billing integrations.

This repository intentionally does not claim to reproduce GitHub production scale, internal systems, internal policies, or real Copilot abuse data.
