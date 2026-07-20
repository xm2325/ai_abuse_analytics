# Job-description traceability

This file maps public role themes to concrete repository evidence without claiming access to internal GitHub systems, data, policy logic, production experiments, or enforcement tools.

| Public role theme | Repository evidence | Decision demonstrated |
|---|---|---|
| Analyze product telemetry and usage logs | `telemetry.csv` contract, SQL feature mart, daily monitors, event-time historical replay | distinguish behavior change from instrumentation failure |
| Analyze billing / entitlement data | separate `entitlements.csv` source, cycle alignment, `entitlement_cycle_usage.csv`, billing-family analysis | identify multi-account entitlement pressure without treating telemetry as billing truth |
| Investigate scripted usage | velocity/cadence/overnight signals, shadow rules, historical replay, adversarial velocity-smoothing stress | distinguish automation from high-intensity legitimate use and test whether the rule survives adaptation |
| Investigate account / credential sharing | device/IP dispersion, conservative entity graph, identity-fragmentation stress, competing explanations | avoid treating shared network context as identity proof and quantify brittleness if actors fragment identity signals |
| Investigate token misuse | token-degree evidence, linked-account components, legitimate approved-integration token confounders, token-rotation stress | require corroboration and test whether a token-centric rule fails after behavior changes |
| Investigate usage-limit evasion | separate entitlement ledger, linked billing families, simultaneous near-limit pressure, quota-spreading stress, SQL investigation query | create investigation leads while testing whether concentrated quota signals disappear under account spreading |
| Investigate coordinated activity | coordinated device/IP/payment families, graph evidence, emerging cohort graph triage | distinguish behavioral campaigns from strong identity linkage |
| Prompt-injection / policy-signal analysis | aggregate injection/policy/safety-block signals, security-research confounder, policy-signal suppression stress | investigate safety-signal changes without exposing raw prompts/completions and test resilience when aggregate signals weaken |
| Discover emerging / previously unknown abuse | hidden-taxonomy benchmark, recent-vs-baseline novelty scoring, behavior cohorts, candidate taxonomy proposals | surface new modus operandi without requiring a pre-existing abuse label |
| Separate novelty from data incidents | `novelty_incident_diagnostics.csv`, telemetry coverage contracts, `incident_replay_register.csv` | avoid creating a new abuse taxonomy because instrumentation changed and retain a replay/recovery path |
| Evaluate adaptive adversaries / evasion | `adversarial_rule_stress.csv`, `defense_in_depth_stress.csv`, `evasion_regression_gates.csv`, defensive SQL | quantify rule brittleness and route material degradation into rework/rollback rather than silent threshold tuning |
| Evaluate mitigation / policy impact | pre-rollout-only eligibility, cluster-randomized control/shadow/canary assignment, cluster-level ITT, Wald ATT-style diagnostic | separate assignment-based causal evidence from observational before/after movement |
| Detect policy displacement / actor migration | primary-surface, alternate-surface, total-activity outcomes, synthetic migration benchmark, interference audit | detect when a targeted metric falls because behavior moves rather than truly declines |
| Review experiment validity | pre-trend diagnostics, shadow placebo, prompt-length negative control, hidden-manifest separation | reject causal stories when assignment, trends, controls, or hidden-label boundaries are inconsistent |
| Sequentially monitor a canary | `policy_experiment_sequential_monitor.csv`, evidence-aware stopping guardrails | hold, continue, pause, or return a canary to shadow without automatic widening |
| Evaluate heterogeneous impact | reportability-gated HTE by plan, managed infrastructure, and region | identify possible differential impact while blocking tiny-slice over-interpretation |
| Build reports, dashboards, and self-service analytics | Decision Center, `docs/START_HERE.md`, executive/stakeholder briefs, semantic SQL views | make recurring decisions legible and reproducible rather than one-off analyst queries |
| Build auditable control lifecycle | `operating_control_registry.csv` | see rule/taxonomy/experiment owner, stage, evidence state, promotion gate, rollback trigger, and no-auto-action boundary in one place |
| Maintain decision lineage | `decision_lineage.csv`, `decision_audit_trail.csv` | reconstruct who owned a decision, what evidence supported it, what gate applied, and what stage produced it |
| Maintain data lineage / source-of-truth boundaries | `data_lineage.csv` | distinguish telemetry, entitlement, review and experiment sources by purpose, sensitivity, contract, owner and freshness expectation |
| Operate quality/SLO guardrails | `operating_slo_scorecard.csv`, `release_readiness.json` | block or hold rollout/retuning when data contracts, evidence maturity, queue health, review maturity or governance boundaries are not ready |
| Turn a case into cross-functional evidence | `evidence_packages/*.md`, `evidence_package_index.csv` | give T&S/Product/Engineering/policy owners a privacy-safe case-to-policy package with competing explanations and escalation gates |
| Prototype detection / anomaly methods | logistic baseline, Isolation Forest, linked-entity signal, candidate shadow rules, novelty cohort discovery | compare multiple signal families without equating score with guilt |
| Evaluate false positives / false negatives | FPR/FNR, operational slices, managed-infrastructure and approved-organization controls | quantify legitimate-user impact before policy change |
| Critically evaluate statistical assumptions | frozen thresholds, calibration, PSI, one-sided uncertainty, evidence-volume gates, hidden-label separation, cluster randomization, placebo/negative controls | reject attractive results when evidence, evaluation design, interference, resilience or denominator size is weak |
| Recurring monitoring for emerging abuse | robust daily known-signal alerts plus unsupervised recent-vs-baseline cohort discovery | detect both known metric shifts and patterns outside the current taxonomy |
| Improve abuse-relevant data quality | telemetry/entitlement contracts, signal-integration backlog, incident replay | block detection changes when source data is unreliable and define recovery/replay gates |
| Recommend new pipelines / integrations | backlog entries with analytical problem, proposed source, privacy class and partner team | connect a missing signal to a concrete decision rather than asking for “more features” |
| Operationalize one-off investigation methods | control registry, taxonomy → shadow, replay, resilience, canary, SLO/audit/evidence packages, CI benchmark | turn an analysis into an auditable recurring process with explicit owners and gates |
| Review-capacity and operational tradeoffs | review-capacity frontier, P0–P3 SLA, historical arrivals, 0.5/1/2-FTE simulation, SLO scorecard | test whether a rule/policy is operationally supportable before widening it |
| Review / appeal / overturn feedback | delayed label maturity, review metrics, experiment review guardrails, enforcement safety outputs | feed cleared/overturned cases back into rule, threshold, taxonomy and experiment review |
| SQL / Python / BI-style reporting | reusable SQL, Python pipeline, interactive Decision Center, generated operating artifacts | support investigation, monitoring, resilience, experimentation and operating governance |
| Sensitive-data governance | hashed/pseudonymous metadata, no raw prompt/completion default layer, raw identity/payment boundary, privacy/legal brief | apply purpose limitation and access boundaries to sensitive analysis |
| Cross-functional decision support | T&S, Engineering, privacy/legal briefs, action register, case-to-policy packages | translate the same evidence into owner-specific Product/Security/Engineering/DS/governance actions |
| Mentor / raise analytical quality | metric contracts, evidence gates, runbooks, tests, lineage/SLO/audit standards | encode review standards another analyst can apply consistently |

## Explicit limits

The project does not claim:

- GitHub-scale data volume;
- real Copilot telemetry, prompts, completions, billing, account records, or experiment assignments;
- access to GitHub internal abuse taxonomies, production thresholds, or enforcement policy;
- real CELA decisions, production enforcement, on-call incident response, or immutable production audit infrastructure;
- production causal-inference or experimentation experience;
- that synthetic adversarial transformations reproduce real attacker behavior;
- that the synthetic randomized benchmark replaces formal power/MDE planning, randomization inference, approved sequential testing, or network-interference analysis.

The repository is intended to show analytical reasoning, controls, tooling, experimentation discipline, resilience testing, lineage, evidence packaging, and decision workflows that can transfer to a real Trust & Safety environment.
