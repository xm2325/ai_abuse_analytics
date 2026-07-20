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
| Separate novelty from data incidents | `novelty_incident_diagnostics.csv`, telemetry coverage contracts | avoid creating a new abuse taxonomy because instrumentation changed |
| Evaluate adaptive adversaries / evasion | `adversarial_rule_stress.csv`, `defense_in_depth_stress.csv`, `evasion_regression_gates.csv`, defensive SQL | quantify rule brittleness, compare single-rule vs diversified defenses, and route material degradation into rework/rollback rather than silent threshold tuning |
| Evaluate mitigation / policy impact | pre-rollout-only eligibility, cluster-randomized control/shadow/canary assignment, cluster-level ITT, Wald ATT-style diagnostic | separate assignment-based causal evidence from observational before/after movement |
| Detect policy displacement / actor migration | primary-surface, alternate-surface, total-activity outcomes, synthetic migration benchmark, interference audit | detect when a targeted metric falls because behavior moves to another surface/account rather than truly declining |
| Review experiment validity | pre-trend diagnostics, shadow placebo, prompt-length negative control, hidden-manifest separation | reject causal stories when assignment, trends, or controls are inconsistent |
| Sequentially monitor a canary | `policy_experiment_sequential_monitor.csv`, user-impact and displacement guardrails, stopping decision | decide whether to hold, continue, pause, or return a canary to shadow without automatic widening |
| Evaluate heterogeneous impact | reportability-gated HTE by plan, managed infrastructure, and region | identify possible differential impact while blocking tiny-slice over-interpretation |
| Build reports, dashboards, and self-service analytics | Decision Center, executive brief, stakeholder briefs, semantic SQL views | make recurring decisions reproducible rather than one-off analyst queries |
| Prototype detection / anomaly methods | logistic baseline, Isolation Forest, linked-entity signal, candidate shadow rules, novelty cohort discovery | compare multiple signal families without equating score with guilt |
| Evaluate false positives / false negatives | FPR/FNR, reportable operational slices, managed-infrastructure and approved-organization controls | quantify legitimate-user impact before policy change |
| Critically evaluate statistical assumptions | frozen holdout thresholds, calibration, PSI, one-sided rule uncertainty bounds, evidence-volume gates, hidden-label separation, pre-period-only randomization, placebo/negative controls, cluster-level inference | reject attractive results when evidence, evaluation design, interference, or resilience is weak |
| Recurring monitoring for emerging abuse | robust daily known-signal alerts plus unsupervised recent-vs-baseline cohort discovery | detect both known metric shifts and patterns outside the current taxonomy |
| Improve abuse-relevant data quality | telemetry contracts, entitlement contracts, signal-integration backlog | block detection changes when source data is unreliable |
| Recommend new pipelines / integrations | backlog entries with analytical problem, proposed source, decision, privacy class, partner team | connect a missing signal to a concrete decision rather than asking for “more features” |
| Operationalize one-off investigation methods | versioned rule registry, candidate taxonomy → shadow definition, shadow → canary gates, rollback triggers, experiment registry-style artifacts, CI benchmark | turn an analysis into an auditable recurring process with explicit resilience and experiment checks |
| Review-capacity and operational tradeoffs | review-capacity frontier, P0–P3 SLA, historical case arrivals, 0.5/1/2-FTE queue simulation | test whether a rule is operationally supportable before widening it |
| Measure mitigation impact | legacy DiD-style diagnostic plus cluster-randomized synthetic canary experiment | distinguish observational evidence from stronger assignment-based policy evaluation |
| Review / appeal / overturn feedback | delayed label maturity, review feedback metrics, experiment arm review guardrails, enforcement safety outputs | feed cleared and overturned cases back into rule/threshold/taxonomy/experiment review |
| SQL / Python / BI-style reporting | reusable SQL including emerging-discovery, adversarial-resilience, and policy-experiment workflows; Python pipeline; interactive Decision Center | support deep investigation, recurring monitoring, resilience analysis, and policy experimentation |
| Sensitive-data governance | hashed/pseudonymous metadata, no raw prompt/completion default layer, raw identity/payment boundary, CELA-style brief | apply purpose limitation and access boundaries to sensitive analysis |
| Cross-functional decision support | separate Trust & Safety, Engineering, and privacy/legal briefs plus stakeholder action register | translate the same evidence into Product, Security, Anti-Abuse Engineering, DS, and governance actions |
| Mentor / raise analytical quality | metric contracts, evidence gates, runbooks, tests, experiment-validity checks | encode review standards that another analyst can apply consistently |

## Explicit limits

The project does not claim:

- GitHub-scale data volume;
- real Copilot telemetry, prompts, completions, billing, account records, or experiment assignments;
- access to GitHub internal abuse taxonomies, production thresholds, or enforcement policy;
- real CELA decisions or production enforcement experience;
- production causal-inference or experimentation experience;
- that the synthetic adversarial transformations reproduce real attacker behavior;
- that the synthetic randomized benchmark replaces formal power/MDE planning, randomization inference, approved sequential testing, or network-interference analysis.

The repository is intended to show analytical reasoning, controls, tooling, experimentation discipline, resilience testing, and decision workflows that can transfer to a real Trust & Safety environment.
