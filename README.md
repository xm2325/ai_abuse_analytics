# AI Abuse Analytics

A privacy-safe, reproducible Trust & Safety analytics workbench for AI developer-tool abuse investigation.

> **Portfolio scope:** this is an independent synthetic project inspired by analytical problems in a public GitHub Data Analyst role supporting Copilot Trust & Safety. It does not use GitHub internal data, rules, taxonomies, policy logic, prompts, completions, or production systems.

## Executive summary

The project starts from operating decisions rather than a model leaderboard:

> With limited analyst capacity, which accounts or account families should be investigated first, what benign explanations could produce the same signals, can we detect a new abuse pattern that is not yet in the taxonomy, and is there enough evidence to change a detection or mitigation policy?

The workbench models the full decision loop:

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
false-positive, calibration, evidence-volume and uncertainty checks
        ↓
historical replay + shadow / canary / rollback gates
        ↓
investigation queue + linked-account + billing-family evidence
        ↓
human review → enforcement decision → appeal / overturn feedback
        ↓
mitigation measurement + analyst-capacity stress testing
        ↓
rule / threshold / taxonomy / data-integration revision
```

The default analyst layer does **not** expose raw prompts, completions, IP addresses, raw device identifiers, card numbers, or payment details. Scores, novelty cohorts, rules, and billing-family signals prioritize human investigation; they never authorize automatic enforcement.

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
| Can the team operationalize it? | queue arrival/service simulation | accurate rule creates unmanageable backlog |
| Did mitigation work? | DiD-style diagnostic, bootstrap interval, pre-trend checks | before/after movement = causal proof |
| Are legitimate users being harmed? | FPR/FNR slices, appeals, overturns, label maturity | ignoring delayed negative feedback |

# v0.7 — Unknown / emerging abuse discovery

Known-rule monitoring cannot find every new abuse pattern. v0.7 adds a separate discovery path for behaviors that are **not represented in the current taxonomy**.

## Hidden-pattern benchmark without label leakage

The synthetic benchmark injects a late pattern called internally:

```text
surface_hopping_token_rotation
```

The hidden pattern is deliberately designed not to match existing shortcuts:

- modest rather than extreme request growth;
- no policy-signal spike;
- no shared token across accounts;
- stable device/IP identity;
- abrupt model-surface switching;
- rapid per-account token rotation.

A benchmark-only file records which accounts received the hidden pattern:

```text
data/hidden_novelty_manifest.csv
```

**The discovery system never reads this manifest.** It is only used after outputs are fixed to measure synthetic recovery.

## Discovery workflow

```text
account-day behavior
        ↓
baseline 28-day window vs recent 10-day window
        ↓
robust multivariate change scores
        ↓
novelty candidate set
        ↓
behavior cohort clustering
        ↓
telemetry-health screen
        ↓
entity/context graph triage
        ↓
candidate taxonomy proposal
        ↓
analyst competing-explanation review
        ↓
development-only candidate shadow definition
        ↓
independent replay + matured labels + uncertainty + capacity review
```

Main outputs:

```text
artifacts/emerging_novelty_accounts.csv
artifacts/emerging_behavior_cohorts.csv
artifacts/emerging_graph_edges.csv
artifacts/emerging_graph_triage.csv
artifacts/candidate_taxonomy_proposals.csv
artifacts/novel_shadow_rule_candidates.csv
artifacts/novelty_incident_diagnostics.csv
artifacts/emerging_discovery_benchmark.json
```

### Novelty is not an abuse finding

A new behavior cohort can be caused by:

- product launches;
- approved integrations;
- SDK retry behavior;
- enterprise automation;
- client migrations;
- telemetry regressions;
- genuinely new abuse.

Therefore the output is:

```text
analyst_taxonomy_review_required
```

not:

```text
confirmed abuse
```

A generated rule stops at:

```text
independent_shadow_replay_required
```

and `automatic_enforcement_allowed = false`.

See `docs/EMERGING_ABUSE_DISCOVERY.md` and `sql/10_emerging_abuse_discovery.sql`.

# v0.6 — Billing and entitlement abuse analytics

Telemetry is not treated as the billing source of truth.

The project creates a separate synthetic entitlement ledger:

```text
data/entitlements.csv
```

and aligns usage to entitlement cycles before analyzing multi-account pressure.

Outputs:

```text
entitlement_cycle_usage.csv
billing_family_risk.csv
entitlement_investigation_queue.csv
entitlement_data_quality.csv
```

A candidate billing family requires multiple linked accounts under simultaneous entitlement pressure. Even then it is only an investigation lead.

Legitimate managed/shared organization billing families are explicitly represented as competing explanations and must not be classified as quota evasion solely because they share billing context.

See `docs/BILLING_ENTITLEMENT_INVESTIGATION.md` and `sql/09_entitlement_evasion_investigation.sql`.

# v0.5 — Time-based validation and evidence sufficiency

## No-lookahead historical replay

`historical_rule_replay.csv` evaluates rules at historical checkpoints using only events available up to each checkpoint.

Distribution-derived thresholds are frozen before holdout/replay use, removing silent evaluation-data adaptation.

## Delayed labels

Review outcomes are not assumed to exist immediately. Replay tracks matured-label coverage so unresolved cases are not silently treated as negatives.

## Rule evidence power

`rule_evidence_power.csv` reports:

```text
observed FPR
one-sided 95% FPR upper bound
observed precision
one-sided 95% precision lower bound
trigger volume
evidence sufficiency
```

A rule can have zero observed false positives and still remain in `shadow_more_evidence` when the sample is too small.

## Queue stress testing

`queue_simulation_summary.csv` tests synthetic 0.5, 1.0, and 2.0 analyst-FTE scenarios using case arrival time, priority, risk proxy, and review effort.

It reports backlog, SLA breaches, utilization, and p95 time-to-review.

See `docs/HISTORICAL_REPLAY_AND_EVIDENCE.md` and `sql/08_historical_rule_replay.sql`.

# Detection, investigation, and governance layers

## Synthetic known abuse scenarios

The benchmark includes:

- scripted automation;
- credential sharing;
- quota/entitlement evasion;
- token misuse;
- coordinated abuse;
- policy/prompt-injection-related signals.

For sufficiently large benchmark samples, CI guarantees minimum coverage of all six scenarios rather than allowing a random seed to omit a JD-relevant case.

## Legitimate confounders

The benchmark deliberately includes:

- high-intensity power users;
- security-research behavior with elevated safety signals;
- shared enterprise/network infrastructure;
- approved organization contexts with legitimate shared token/payment/runner entities.

Approved-organization context is available to investigators but excluded from model features, preventing it from becoming a label shortcut.

## Conservative linked-account analysis

Entity overlap does not have one meaning:

| Entity | Analytical treatment |
|---|---|
| token fingerprint | strong supporting linkage, lifecycle/context still required |
| payment fingerprint | strong supporting linkage, ownership/billing context required |
| device fingerprint | useful with corroboration |
| IP context | supporting context only |

IP-only overlap never proves common control because NAT, VPNs, enterprise egress, managed fleets, and shared runners create benign overlap.

## Threshold policy guardrails

`policy_threshold_frontier.csv` evaluates human-review thresholds against:

- global false-positive rate;
- review-capacity share;
- worst reportable slice FPR;
- minimum precision;
- minimum evidence volume.

The system may return:

```text
no_threshold_meets_all_guardrails
```

instead of forcing a recommendation.

## Review → appeal → overturn feedback

Synthetic case management includes review outcomes, enforcement actions, appeals, overturns, decision latency, taxonomy version, and policy version.

Cleared cases and overturned enforcement decisions feed back into threshold, rule, and taxonomy review.

## Mitigation measurement

The project builds an account-day panel and reports a DiD-style diagnostic with bootstrap uncertainty and pre-trend checks.

It explicitly does **not** claim causal proof from a simple before/after chart.

## Data quality is part of detection

Contracts cover:

- schema;
- request-ID uniqueness;
- account referential integrity;
- signal coverage;
- entitlement schema and account-cycle uniqueness;
- instrumentation regressions.

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
- reusable SQL workflows and semantic views.

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
config/                   taxonomy + metric contracts
docs/                     architecture, governance, runbooks, JD mapping
tests/                    integration and enforcement-boundary tests
.github/workflows/         reproducible CI benchmark
```

# Production boundary

CSV + SQLite/Pandas are used for a local reproducible portfolio benchmark. A production design would use partitioned event-time marts, incremental materialization, late-arrival handling, idempotent backfills, versioned data/taxonomy contracts, restricted sensitive-data access, and auditable policy/review systems.

This repository intentionally does not claim GitHub-scale data, internal Copilot telemetry, internal abuse taxonomy access, or production enforcement experience.
