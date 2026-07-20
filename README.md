# AI Abuse Analytics

A privacy-safe, reproducible Trust & Safety analytics workbench for AI developer-tool abuse investigation, detection validation, and policy decision support.

> **Portfolio scope:** this is an independent synthetic project inspired by analytical problems in a public GitHub Data Analyst role supporting Copilot Trust & Safety. It does not use GitHub internal data, rules, taxonomies, production thresholds, prompts, completions, experiments, or enforcement systems.

## Executive summary

The project starts from operating decisions rather than a model leaderboard:

> With limited analyst capacity, which accounts should be investigated first, what benign explanations could produce the same signals, can we detect previously unknown abuse, will controls survive adaptive behavior, and did a mitigation actually reduce abuse rather than move it to another account or product surface?

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
shadow → cluster-randomized canary/control experiment
        ↓
ITT + spillover + displacement + user-impact guardrails
        ↓
sequential human-reviewed stop / pause / rollback decision
        ↓
investigation queue + linked-account + billing-family evidence
        ↓
human review → enforcement decision → appeal / overturn feedback
        ↓
rule / threshold / taxonomy / policy / data-integration revision
```

The default analyst layer does **not** expose raw prompts, completions, IP addresses, raw device identifiers, card numbers, or payment details. Scores, novelty cohorts, rules, experiment estimates, and billing-family signals support human investigation and policy review; they never authorize automatic enforcement.

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
| Did a mitigation actually work? | cluster-randomized canary ITT + placebo/negative controls | before/after movement = causal proof |
| Did behavior move elsewhere? | alternate-surface, total-activity and spillover diagnostics | targeted metric falls while harm is displaced |
| Should the canary continue or rollback? | sequential guardrails + stopping decision | automatic widening from one favorable metric |
| Are effects different across user groups? | reportability-gated HTE diagnostics | overreacting to tiny subgroup estimates |
| Can the team operationalize it? | queue arrival/service simulation | accurate rule creates unmanageable backlog |
| Are legitimate users being harmed? | FPR/FNR slices, acceptance guardrails, appeals, overturns | ignoring delayed negative feedback |

# v0.9 — Investigation experimentation and causal policy evaluation

A mitigation can make the visible metric fall without reducing the underlying problem. v0.9 adds a separate experiment path designed around that failure mode.

## 1. Pre-rollout-only assignment

Experiment eligibility, clustering, and stratification use **only data available before rollout**.

The experiment intentionally does not use a full-period risk score for assignment because post-rollout behavior would leak treatment outcomes into experiment design.

Pre-period inputs include:

```text
active days
requests per active day
aggregate policy-signal rate
plan / region / managed-infrastructure context
pre-period organization / token / payment relationships
```

## 2. Cluster-randomized arms

Accounts connected by stronger pre-period contexts are assigned together:

```text
same organization
low-degree shared token context
low-degree shared payment context
        ↓
randomization cluster
```

Arms:

```text
control
shadow
canary
```

`shadow` has no user-facing treatment and provides an operational placebo/reference arm.

IP overlap is deliberately **not** used as identity proof or as a strong randomization linkage. It remains weak context for spillover sensitivity because NAT, VPNs, enterprise egress, and shared infrastructure create benign overlap.

## 3. Hidden benchmark truth cannot define the experiment

Synthetic responder and migration truth lives in:

```text
data/hidden_policy_experiment_manifest.csv
```

It is benchmark-only and never used by:

```text
eligibility
cluster construction
stratification
arm assignment
effect estimation
HTE
sequential stopping
```

This prevents the evaluator from using the answer key to design the experiment.

## 4. Causal estimands

### ITT — assigned canary vs control

The primary policy estimand is cluster-level intention-to-treat.

```text
assigned canary cluster change
        minus
assigned control cluster change
```

It answers the operational question:

> What is the effect of assigning an eligible cluster to the canary under observed exposure and non-compliance?

### Wald ATT-style diagnostic

The project also reports:

```text
ITT / canary exposure rate
```

This is explicitly labeled a diagnostic because it requires strong exclusion/monotonicity-style assumptions. ITT remains the primary experiment view.

## 5. A falling primary metric is not enough

The experiment separately measures:

```text
primary-surface requests
alternate-surface requests
total requests
acceptance-rate guardrail
prompt-length negative control
shadow placebo
```

Interpretation:

```text
primary falls a lot
+ alternate surface rises
+ total barely changes
        ↓
possible displacement
not equivalent harm reduction
```

## 6. Interference and actor migration

The workflow does not assume one account's treatment cannot affect another account.

Synthetic benchmark scenarios include:

```text
policy affects account A
        ↓
activity moves to another surface
or
activity migrates toward account B
```

Outputs audit:

- strong-link cluster integrity;
- cross-arm weak-context neighborhoods;
- direct primary movement;
- alternate-surface displacement;
- net total activity.

IP-context overlap remains a **spillover sensitivity graph only** and never proves common control.

## 7. Pre-trend, placebo and negative controls

Before interpreting the canary effect, the project checks:

```text
pre-period slope gaps by arm
shadow vs control placebo
prompt-length negative-control effect
```

Material movement here is a reason to review randomization, implementation, logging, or model assumptions before making a causal claim.

## 8. Sequential monitoring and stopping

Post-rollout checkpoints report:

```text
primary ITT
total-request ITT
alternate-surface ITT
acceptance-rate guardrail
negative-control movement
displacement ratio
recommended action
```

Possible actions:

```text
hold_canary_collect_more_evidence
continue_canary_collect_evidence
pause_and_review_displacement
rollback_to_shadow_user_impact_guardrail
```

The displayed monitoring interval is conservative and descriptive. It is **not** presented as a formal group-sequential alpha-spending design.

No metric automatically widens a canary.

## 9. Delayed review / appeal guardrails

Arm-level matured outcomes include:

```text
matured reviews
cleared rate
enforcement rate
appeal rate
overturn rate
evidence-volume status
```

Tiny samples remain `limited_matured_review_evidence` rather than being converted into confident policy conclusions.

## 10. Heterogeneous treatment effects

Diagnostic HTE is reported by operational slices such as:

```text
plan
managed infrastructure
region
```

A slice is only marked reportable after minimum treated/control cluster evidence. These outputs are exploratory and do not justify slice-specific policy without multiplicity, power, stability, user-impact, and policy/legal review.

## Main v0.9 outputs

```text
artifacts/policy_experiment_assignment.csv
artifacts/policy_experiment_daily_outcomes.csv
artifacts/policy_experiment_effect_summary.csv
artifacts/policy_experiment_pretrend.csv
artifacts/policy_experiment_heterogeneous_effects.csv
artifacts/policy_experiment_sequential_monitor.csv
artifacts/policy_experiment_interference_audit.csv
artifacts/policy_experiment_review_guardrails.csv
artifacts/policy_experiment_stopping_decision.json
artifacts/policy_experiment_benchmark.json
```

See `docs/POLICY_EXPERIMENT_AND_CAUSAL_EVALUATION.md` and `sql/12_policy_experiment_evaluation.sql`.

# v0.8 — Adversarial adaptation and detection resilience

Static holdout performance is not enough for abuse detection. v0.8 freezes rule definitions and tests coarse synthetic adaptation families:

```text
velocity_smoothing
identity_fragmentation
token_rotation
quota_spreading
policy_signal_suppression
multi_signal_blending
```

It measures target-scenario and overall recall degradation, defense-in-depth resilience, review-workload changes, and release-style regression gates. Small target samples are explicitly treated as fragility hypotheses rather than stable resilience estimates.

See `docs/ADVERSARIAL_ADAPTATION.md` and `sql/11_adversarial_rule_resilience.sql`.

# v0.7 — Unknown / emerging abuse discovery

A benchmark-only hidden pattern is injected, but discovery cannot read its manifest.

```text
recent vs baseline behavior
        ↓
robust novelty score
        ↓
behavior cohort
        ↓
telemetry-health screen
        ↓
graph/context triage
        ↓
candidate taxonomy
        ↓
independent shadow replay required
```

Novelty is not an abuse verdict. Product launches, SDK changes, enterprise automation, migrations, integrations, or telemetry regressions can produce similar patterns.

See `docs/EMERGING_ABUSE_DISCOVERY.md` and `sql/10_emerging_abuse_discovery.sql`.

# v0.6 — Billing and entitlement abuse analytics

Telemetry is not treated as billing truth. A separate entitlement ledger is aligned to account cycles before multi-account pressure is analyzed.

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

- no-lookahead historical replay;
- delayed-label coverage;
- one-sided rule uncertainty bounds;
- evidence-volume gates;
- 0.5 / 1.0 / 2.0 analyst-FTE queue simulations.

A clean point estimate on a tiny sample is not treated as policy evidence.

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

IP-only overlap never proves common control.

## Review → appeal → overturn feedback

Synthetic case management includes review outcomes, enforcement actions, appeals, overturns, decision latency, taxonomy version, and policy version. Cleared and overturned cases feed back into threshold, rule, taxonomy, and experiment review.

## Data quality is part of detection

Contracts cover schema, request-ID uniqueness, account referential integrity, signal coverage, entitlement schema, account-cycle uniqueness, and instrumentation regressions.

A telemetry failure should trigger data repair and annotation before detection or experiment retuning.

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
- rule resilience / rollback artifacts;
- cluster-randomized canary experiment and causal-policy diagnostics.

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
  policy_experiment.py    cluster-randomized canary + causal diagnostics
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
  mitigation.py           legacy DiD-style diagnostics
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

CSV + SQLite/Pandas are used for a local reproducible portfolio benchmark. A production design would require partitioned event-time marts, incremental materialization, late-arrival handling, idempotent backfills, versioned data/taxonomy contracts, experiment registry, power/MDE planning, treatment/exposure consistency, cluster-level or randomization inference, approved sequential testing, network-interference assumptions, experiment collision management, restricted sensitive-data access, auditable policy/review systems, and controlled access to operational thresholds.

This repository intentionally does not claim GitHub-scale data, internal Copilot telemetry, internal abuse taxonomy access, production experiments, production thresholds, or production enforcement experience.
