# AI Abuse Analytics — Trust & Safety Operating Workbench

A privacy-safe, reproducible portfolio project showing how an analyst can move from **AI-product telemetry → investigation → evidence → rule/policy decision → audit trail**.

> **Scope:** independent synthetic project inspired by analytical problems in a public GitHub Data Analyst role supporting Copilot Trust & Safety. It does **not** use GitHub internal data, prompts, completions, rules, taxonomies, thresholds, experiments, or enforcement systems.

## Start here

For a 2–3 minute review:

1. Open [`docs/START_HERE.md`](docs/START_HERE.md).
2. Open the generated **Decision Center** at `docs/index.html` and read **v1.0 Operating brief — start here**.
3. Inspect one generated `artifacts/evidence_packages/PKG-xxx.md` file to see how a case is connected to rule, experiment, data-quality and governance evidence.
4. Read [`docs/JD_TRACEABILITY.md`](docs/JD_TRACEABILITY.md) for the public-role-to-repository mapping.

## Executive question

> With limited analyst capacity, which behavior should be investigated, what benign explanations could produce the same signals, is the evidence strong enough to change a rule or policy, did a mitigation really reduce harm rather than move it elsewhere, and can another team reconstruct why the decision was made?

The project is deliberately organized around those decisions rather than a model leaderboard.

```text
privacy-safe telemetry + accounts + entitlements + review outcomes
        ↓
data contracts / signal health / source-of-truth boundaries
        ↓
known-abuse detection + unknown-pattern discovery
        ↓
investigation queue + entity / entitlement evidence
        ↓
false-positive / uncertainty / evidence-volume checks
        ↓
historical replay + adversarial adaptation stress
        ↓
shadow → cluster-randomized canary/control experiment
        ↓
ITT / placebo / negative control / spillover / displacement / user-impact
        ↓
hold / continue / pause / rollback recommendation
        ↓
versioned control registry + decision lineage + SLO + incident replay
        ↓
case-to-policy evidence package + audit trail
        ↓
human analyst / policy-owner decision
```

No score, rule, cohort, experiment estimate, or evidence package authorizes automatic enforcement or automatic policy expansion.

# v1.0 — Operating and audit layer

v1.0 does not add another classifier. It turns the v0.3–v0.9 analytical modules into one auditable operating system.

## 1. Versioned control registry

`artifacts/operating_control_registry.csv` puts the major analytical controls in one lifecycle view:

- detection rules;
- candidate abuse taxonomies;
- policy experiments.

Each row records:

```text
control id / type / version
stage
owner
evidence state
primary evidence
promotion gate
rollback trigger
source artifacts
automatic action boundary
```

This prevents a rule, taxonomy proposal, or experiment from becoming an isolated notebook result with no owner or lifecycle.

## 2. Decision lineage

`artifacts/decision_lineage.csv` connects every current operating decision to:

```text
decision id
priority
owner + partners
evidence summary
recommended action
review gate
evidence references
decision state
```

The core question is not only **“what did the model say?”** but also:

> Who owns the decision, which evidence supports it, what remains uncertain, and what must happen before the next stage?

## 3. Data lineage and purpose limitation

`artifacts/data_lineage.csv` makes source-of-truth boundaries explicit.

Examples:

| Source | Purpose | Important boundary |
|---|---|---|
| telemetry | behavioral analytics | not the billing source of truth |
| entitlements | cycle/allowance analysis | separate billing/entitlement contract |
| reviews | matured feedback | delayed outcomes are not silently treated as negatives |
| pre-rollout telemetry | experiment assignment | post-treatment behavior prohibited from assignment |
| investigation artifacts | evidence package | default layer remains privacy-safe/pseudonymous |

The default analyst layer excludes raw prompts, completions, raw IPs, raw device identifiers, card numbers and payment details.

## 4. Operating SLO scorecard

`artifacts/operating_slo_scorecard.csv` turns analytical quality into operational gates.

Current SLO families include:

- source-contract health;
- one-FTE queue/SLA health;
- rule-evidence maturity;
- canary matured-review evidence;
- automatic-action boundary.

An SLO can return `pass`, `review`, or `breach`. A breach blocks the relevant widening/retuning path rather than being hidden behind a model metric.

## 5. Incident replay register

`artifacts/incident_replay_register.csv` records a reproducible incident view:

```text
what signal failed or alerted
how it was detected
blast radius
what decision was taken
what evidence is replayed
recovery gate
current state
```

Data-quality incidents and behavioral alerts are deliberately separated. Broken telemetry should be repaired/replayed before inventing a new abuse taxonomy or retuning a rule.

## 6. Case → policy evidence package

The pipeline generates privacy-safe evidence packages under:

```text
artifacts/evidence_packages/
```

A package links one investigation candidate to:

- risk/reason-code context;
- competing benign explanations;
- entity-linkage cautions;
- rule lifecycle/evidence state;
- historical replay and adversarial-resilience evidence;
- policy-experiment state;
- review/appeal evidence;
- privacy and escalation gates.

It is a **decision package**, not an abuse verdict.

## 7. Deterministic audit trail and release readiness

`artifacts/decision_audit_trail.csv` records the ordered analytical stages for the current reproducible run.

`artifacts/release_readiness.json` summarizes:

- operating-layer status;
- SLO breaches/reviews;
- registered controls;
- decision-lineage rows;
- evidence-package count;
- current policy-experiment state;
- automatic enforcement/policy-expansion boundaries.

“Ready” means **portfolio/demo operating artifacts are coherent**, not that the repository is certified for production Trust & Safety use.

# What real work questions does the repository answer?

| Decision question | Main evidence | Failure mode guarded against |
|---|---|---|
| What should analysts review first? | investigation queue, P0–P3 SLA, evidence packages | optimizing AUC without considering analyst capacity |
| Is high usage actually abuse? | behavior + legitimate high-intensity controls | `high usage = abuse` |
| Are accounts truly linked? | token/payment/device evidence + IP caution | NAT/VPN/shared runner = same actor |
| Is usage-limit evasion occurring? | entitlement cycles + billing-family analysis | telemetry or near-limit usage = billing truth |
| Is there a new modus operandi? | novelty cohorts + taxonomy proposals | only detecting known labels |
| Is novelty actually a telemetry incident? | signal-health diagnostics | creating abuse theories from broken instrumentation |
| Is a rule ready? | frozen holdout + uncertainty + evidence volume | `100% precision` on tiny samples = safe |
| Does it still work later? | no-lookahead historical replay | random holdout hides temporal failure |
| Will actors adapt around it? | adversarial stress + signal-diversity diagnostics | static-user assumption |
| Did mitigation really work? | randomized synthetic canary ITT | before/after change = causal proof |
| Did behavior move elsewhere? | alternate-surface + total activity + migration | targeted metric falls while underlying activity moves |
| Should canary continue? | sequential/evidence-aware stopping | auto-widening from one favorable metric |
| Are legitimate users harmed? | FPR slices + acceptance + appeal/overturn | delayed negative feedback ignored |
| Can another team audit the decision? | control registry + lineage + SLO + audit + packages | one-off analyst logic cannot be reconstructed |

# Analytical layers

## Known abuse detection

Synthetic scenarios include scripted automation, credential sharing, quota/entitlement evasion, token misuse, coordinated abuse, and aggregate policy/prompt-injection signals.

Methods include:

- SQL-style feature marts;
- logistic baseline;
- Isolation Forest;
- conservative graph/entity signal;
- frozen shadow rules;
- FPR/FNR and slice diagnostics;
- calibration and drift diagnostics.

## Legitimate-user confounders

The synthetic benchmark deliberately includes:

- power users;
- shared enterprise/network infrastructure;
- security-research behavior;
- approved organization contexts with legitimate shared token/payment/runner entities.

Approved-organization context is not used as a model label shortcut.

## Unknown / emerging abuse discovery

A benchmark-only hidden pattern is injected but cannot be read by discovery.

```text
recent vs baseline behavior
→ robust novelty
→ behavior cohorts
→ telemetry-health screen
→ graph/context triage
→ candidate taxonomy
→ independent shadow replay required
```

Novelty is never treated as an abuse finding by itself.

## Historical replay and evidence power

Rules are replayed at historical checkpoints with events after each checkpoint excluded.

Evidence outputs include:

- mature-label coverage;
- observed FPR/precision;
- one-sided uncertainty bounds;
- trigger volume;
- evidence sufficiency.

Zero observed false positives on a tiny sample is not considered sufficient evidence.

## Adversarial adaptation / resilience

Frozen rules are stress-tested against coarse synthetic adaptation families:

```text
velocity smoothing
identity fragmentation
token rotation
quota spreading
policy-signal suppression
multi-signal blending
```

The output measures rule brittleness and whether independent signal families degrade more gracefully. Exact production thresholds are never represented.

## Policy experimentation / causal evaluation

The synthetic experiment uses **pre-rollout-only** eligibility/clustering/stratification and cluster-randomizes strong observed org/token/payment contexts into control, shadow and canary arms.

Outputs include:

- ITT and clearly labeled Wald ATT-style diagnostic;
- shadow placebo;
- negative-control outcome;
- pre-trend diagnostics;
- alternate-surface and total-activity displacement;
- interference/migration sensitivity;
- HTE with reportability gates;
- sequential monitoring;
- evidence-aware hold/pause/rollback decision.

A targeted metric decrease is not automatically called a mitigation success.

# Main decision products

```text
docs/START_HERE.md
docs/index.html
artifacts/executive_brief.md
artifacts/stakeholder_action_register.csv
artifacts/operating_control_registry.csv
artifacts/decision_lineage.csv
artifacts/data_lineage.csv
artifacts/operating_slo_scorecard.csv
artifacts/incident_replay_register.csv
artifacts/decision_audit_trail.csv
artifacts/evidence_package_index.csv
artifacts/evidence_packages/*.md
artifacts/release_readiness.json
```

Detailed analytical outputs remain available for detection, discovery, billing/entitlement, replay, evidence power, queue simulation, adversarial stress and policy experiments.

# Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_all.py --n-accounts 180 --seed 17
```

Tests:

```bash
pytest -q
```

GitHub Actions independently rebuilds a 120-account benchmark, verifies required decision/operating artifacts, checks the automatic-action boundary, and uploads the complete review package.

# Repository map

```text
src/copilot_trust/
  generate.py               synthetic known-abuse + review-feedback scenarios
  synthetic_controls.py     legitimate confounders
  synthetic_novelty.py      hidden unknown-pattern benchmark
  features.py               SQL-style account feature mart
  scoring.py                supervised + anomaly + graph prioritization
  monitoring.py             recurring signal monitoring
  emerging_discovery.py     unknown-pattern cohort/taxonomy discovery
  entitlements.py           billing/entitlement source-of-truth analysis
  rules.py                  frozen shadow rules
  evidence_power.py         uncertainty/evidence-volume gates
  historical_replay.py      no-lookahead temporal validation
  adversarial_stress.py     adaptive-behavior resilience tests
  policy_experiment.py      cluster-randomized synthetic canary analysis
  experiment_guardrails.py  evidence-aware stopping decisions
  investigate.py            queue, case timelines and linkage evidence
  feedback.py               review/appeal/overturn loop
  operating_layer.py        v1 control registry, lineage, SLO, replay, audit, packages
  operating_report.py       recruiter/manager-first operating brief
  reporting.py              Decision Center + executive brief

sql/                        reusable analyst workflows
docs/                       architecture, runbooks, JD traceability
artifacts/                  generated decision/evidence products
tests/                      integration and governance-boundary tests
.github/workflows/          reproducible CI benchmark
```

# Production boundary

This repository uses CSV/SQLite/Pandas-style local workflows for a reproducible portfolio benchmark. A production system would additionally require partitioned/incremental event infrastructure, late-arrival/idempotent backfill handling, IAM and retention controls, restricted sensitive-data workflows, formal experiment governance and power analysis, service ownership/on-call processes, immutable audit infrastructure, incident tooling, approved policy/legal procedures, and production-scale observability.

The repository intentionally does **not** claim GitHub-scale data, internal Copilot telemetry, internal abuse taxonomies, real production thresholds, real enforcement systems, or causal effects on a real product.
