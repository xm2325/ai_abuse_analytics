# AI Abuse Analytics

A privacy-safe, reproducible Trust & Safety analytics workbench for AI developer-tool abuse investigation.

> **Portfolio scope:** this is an independent synthetic project inspired by analytical problems in a public GitHub Data Analyst role supporting Copilot Trust & Safety. It does not use GitHub internal data, rules, taxonomies, production thresholds, prompts, completions, or enforcement systems.

## Executive summary

The project starts from operating decisions rather than a model leaderboard:

> With limited analyst capacity, which accounts should be investigated first, what benign explanations could produce the same signals, can we detect previously unknown abuse, will our controls survive adaptive behavior, and is there enough evidence to change a rule or policy?

```text
privacy-safe telemetry + account + entitlement sources
        ↓
data contracts and signal coverage
        ↓
known-signal monitoring + unknown-pattern discovery
        ↓
SQL feature marts + conservative entity linkage
        ↓
risk / anomaly / behavior cohorts / candidate rules
        ↓
false-positive, calibration, uncertainty and evidence-volume checks
        ↓
historical replay + adversarial adaptation stress
        ↓
shadow / canary / rollback gates
        ↓
investigation queue + linked-account + billing-family evidence
        ↓
human review → enforcement decision → appeal / overturn feedback
        ↓
mitigation measurement + analyst-capacity stress testing
        ↓
rule / threshold / taxonomy / data-integration revision
```

The default analyst layer does **not** expose raw prompts, completions, IP addresses, raw device identifiers, card numbers, or payment details. Scores, novelty cohorts, rules, billing-family signals, and stress-test results prioritize human analysis; they never authorize automatic enforcement.

## What real work questions does it answer?

| Decision question | Main output | Failure mode guarded against |
|---|---|---|
| What should analysts review first? | investigation queue, P0–P3 SLA, capacity scenarios | optimizing AUC without considering workload |
| Is high usage actually abuse? | behavioral evidence + legitimate power-user controls | `high usage = abuse` |
| Are accounts truly linked? | token/payment/device/IP evidence with reliability rules | shared NAT/VPN/runner = same actor |
| Is usage-limit evasion occurring? | cycle-level entitlement and billing-family analysis | high utilization/shared billing = abuse |
| Is there a new modus operandi outside the taxonomy? | novelty scores, behavior cohorts, taxonomy proposals | only monitoring known rules |
| Is novelty actually a telemetry incident? | recent-vs-baseline signal-health diagnostics | creating an abuse theory because instrumentation changed |
| Is a new rule ready? | shadow evaluation, uncertainty bounds, evidence-volume gate | `precision=100%` on two cases = safe |
| Did a rule still work later? | no-lookahead historical replay | random holdout hides temporal failure |
| Will the rule survive adaptive behavior? | adversarial rule stress + defense-in-depth diagnostic | assuming users remain static after controls appear |
| Can the team operationalize it? | queue arrival/service simulation | accurate rule creates unmanageable backlog |
| Did mitigation work? | DiD-style diagnostic, bootstrap interval, pre-trend checks | before/after movement = causal proof |
| Are legitimate users being harmed? | FPR/FNR slices, appeals, overturns, label maturity | ignoring delayed negative feedback |

# v0.8 — Adversarial adaptation and detection-resilience stress testing

Static holdout performance is not enough for abuse detection. Actors may change behavior after limits, rules, reviews, or mitigations become visible.

v0.8 freezes current rule definitions and applies coarse synthetic adaptation scenarios to known-abuse holdout accounts.

## Stress families

```text
velocity_smoothing
identity_fragmentation
token_rotation
quota_spreading
policy_signal_suppression
multi_signal_blending
```

Each is evaluated at four synthetic strengths:

```text
25% / 50% / 75% / 100%
```

These percentages are scenario parameters, not estimates of attacker capability.

## Core outputs

```text
artifacts/adversarial_rule_stress.csv
artifacts/defense_in_depth_stress.csv
artifacts/adversarial_stress_summary.json
artifacts/evasion_regression_gates.csv
```

The analysis measures:

- baseline vs adapted recall;
- recall degradation by rule family;
- precision / FPR / review-workload changes;
- worst brittle rule;
- diversified multi-rule resilience;
- release-style regression gates.

## Why freeze the rules?

The stress test does **not** re-fit thresholds after behavior changes.

```text
frozen rule definition
        ↓
synthetic adaptation
        ↓
measure degradation
```

This answers the real question:

> How brittle is the control we already deployed or are considering widening?

It does not let the rule silently move after seeing the stress data.

## Defense-in-depth

A diagnostic union of independent frozen rule families is compared with single-rule behavior.

This does **not** claim a production ensemble policy. It tests whether diversified signals degrade more gracefully than one deterministic indicator.

If a single rule collapses under one adaptation family but the broader signal set retains coverage, the operating response is:

```text
identify brittle dependency
        ↓
add independent corroborating signals
        ↓
shadow / replay
        ↓
canary with user-impact + capacity guardrails
        ↓
rollback if resilience degrades materially
```

## Evasion regression gates

`evasion_regression_gates.csv` includes checks such as:

- brittleness must be measured and surfaced;
- defense-in-depth must not degrade worse than the most brittle single rule;
- severe-adaptation scenarios have a diagnostic recall floor.

A warning does not trigger automatic threshold tuning. It routes the control back to analysis, signal development, canary/replay, and rollback review.

See `docs/ADVERSARIAL_ADAPTATION.md` and `sql/11_adversarial_rule_resilience.sql`.

# v0.7 — Unknown / emerging abuse discovery

Known-rule monitoring cannot find every new abuse pattern. v0.7 adds a separate discovery path for behaviors that are **not represented in the current taxonomy**.

A benchmark-only hidden pattern is injected, but discovery cannot read its manifest. The system uses recent-vs-baseline behavior changes, robust novelty scoring, clustering, telemetry-health checks, graph/context triage, and analyst taxonomy proposals.

```text
account behavior
    ↓
recent vs baseline change
    ↓
novelty candidate set
    ↓
behavior cohorts
    ↓
telemetry incident screen
    ↓
graph/context triage
    ↓
candidate taxonomy
    ↓
independent shadow replay required
```

Main outputs:

```text
emerging_novelty_accounts.csv
emerging_behavior_cohorts.csv
emerging_graph_triage.csv
candidate_taxonomy_proposals.csv
novel_shadow_rule_candidates.csv
emerging_discovery_benchmark.json
```

Novelty is not an abuse finding. Product launches, SDK changes, enterprise automation, migrations, integrations, or telemetry regressions can produce similar behavior.

See `docs/EMERGING_ABUSE_DISCOVERY.md` and `sql/10_emerging_abuse_discovery.sql`.

# v0.6 — Billing and entitlement abuse analytics

Telemetry is not treated as the billing source of truth. The project creates a separate synthetic entitlement ledger and aligns usage to entitlement cycles before analyzing multi-account pressure.

```text
data/entitlements.csv
        ↓
entitlement_cycle_usage.csv
        ↓
billing_family_risk.csv
        ↓
entitlement_investigation_queue.csv
```

Legitimate managed/shared organization billing is explicitly represented as a competing explanation.

See `docs/BILLING_ENTITLEMENT_INVESTIGATION.md` and `sql/09_entitlement_evasion_investigation.sql`.

# v0.5 — Time-based validation, evidence power and queue stress

## No-lookahead historical replay

Rules are evaluated at historical checkpoints using only data available up to that checkpoint.

## Delayed labels

Unresolved or immature review outcomes are not silently treated as negatives.

## Evidence power

The system reports point estimates plus one-sided uncertainty bounds and trigger volume. A rule can show zero observed false positives and still remain in `shadow_more_evidence` when the sample is too small.

## Queue stress

Synthetic 0.5, 1.0, and 2.0 analyst-FTE scenarios report backlog, SLA breaches, utilization, and p95 review time.

See `docs/HISTORICAL_REPLAY_AND_EVIDENCE.md` and `sql/08_historical_rule_replay.sql`.

# Detection, investigation and governance layers

## Synthetic known-abuse scenarios

- scripted automation;
- credential sharing;
- quota/entitlement evasion;
- token misuse;
- coordinated abuse;
- policy/prompt-injection-related signals.

## Deliberately difficult legitimate controls

- high-intensity power users;
- security-research behavior;
- shared enterprise/network infrastructure;
- approved organization contexts with legitimate shared token/payment/runner entities.

Approved-organization context is available to investigators but excluded from model features, preventing it from becoming a label shortcut.

## Conservative entity linkage

| Entity | Analytical treatment |
|---|---|
| token fingerprint | strong supporting linkage; lifecycle/context still required |
| payment fingerprint | strong supporting linkage; ownership/billing context required |
| device fingerprint | useful with corroboration |
| IP context | supporting context only |

IP-only overlap never proves common control because NAT, VPNs, enterprise egress, managed fleets, and shared runners create benign overlap.

## Threshold policy guardrails

The project can explicitly return:

```text
no_threshold_meets_all_guardrails
```

instead of forcing a recommendation when FPR, review capacity, worst-slice impact, precision, or evidence volume are inadequate.

## Review → appeal → overturn feedback

Synthetic case management includes review outcomes, enforcement actions, appeals, overturns, decision latency, taxonomy version, and policy version. Cleared and overturned cases feed back into threshold, rule, and taxonomy review.

## Mitigation measurement

The project builds an account-day panel and reports a DiD-style diagnostic with bootstrap uncertainty and pre-trend checks. It does not claim causal proof from a simple before/after chart.

## Data quality is part of detection

Contracts cover schema, request-ID uniqueness, account referential integrity, signal coverage, entitlement schema, account-cycle uniqueness, and instrumentation regressions.

A telemetry failure should trigger data repair and annotation before detection retuning.

# Decision products

The pipeline produces:

- interactive `docs/index.html` Decision Center;
- executive brief;
- Trust & Safety brief;
- Engineering/data-integration brief;
- privacy/legal governance brief;
- stakeholder action register;
- investigation case bundles;
- reusable SQL workflows and semantic views;
- adversarial resilience artifacts and rollback-oriented regression gates.

# Quick start

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

GitHub Actions independently rebuilds a 120-account benchmark, verifies required decision artifacts, and uploads the decision package.

# Repository map

```text
src/copilot_trust/
  generate.py             known synthetic abuse + review feedback
  synthetic_controls.py   legitimate shared-entity confounders
  synthetic_novelty.py    hidden emerging-pattern benchmark injection
  emerging_discovery.py   novelty/cohort/taxonomy/graph discovery
  adversarial_stress.py   adaptive-behavior resilience stress tests
  entitlements.py         entitlement ledger + billing-family analysis
  features.py             SQL-style feature mart
  scoring.py              supervised + anomaly + graph prioritization
  monitoring.py           recurring known-signal monitoring
  historical_replay.py    no-lookahead time replay
  evidence_power.py       rule uncertainty/evidence gates
  rules.py                shadow rule evaluation
  rule_registry.py        promotion/rollback lifecycle
  investigate.py          queues, case evidence, linked accounts
  feedback.py             review/appeal/overturn loop
  mitigation.py           DiD-style diagnostics
  queue_ops.py            SLA/capacity planning
  queue_simulation.py     arrival/service stress testing
  data_quality.py         contracts + integration backlog
  reporting.py            Decision Center + executive brief

sql/                      reusable analyst queries
docs/                     architecture, governance, runbooks, JD mapping
tests/                    integration and enforcement-boundary tests
.github/workflows/         reproducible CI benchmark
```

# Production boundary

CSV + SQLite/Pandas are used for a local reproducible portfolio benchmark. A production design would use partitioned event-time marts, incremental materialization, late-arrival handling, idempotent backfills, versioned data/taxonomy contracts, restricted sensitive-data access, auditable policy/review systems, and controlled access to operational thresholds.

This repository intentionally does not claim GitHub-scale data, internal Copilot telemetry, internal abuse taxonomy access, production thresholds, or production enforcement experience.
