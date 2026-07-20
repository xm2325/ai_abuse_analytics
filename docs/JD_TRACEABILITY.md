# Job-description traceability

This file maps public role themes to concrete repository evidence without claiming access to internal GitHub systems, data, policy logic, or production enforcement tools.

| Public role theme | Repository evidence | Decision demonstrated |
|---|---|---|
| Analyze product telemetry and usage logs | `telemetry.csv` contract, SQL feature mart, daily monitors, event-time historical replay | distinguish behavior change from instrumentation failure |
| Analyze billing / entitlement data | separate `entitlements.csv` source, cycle alignment, `entitlement_cycle_usage.csv`, billing-family analysis | identify multi-account entitlement pressure without treating telemetry as billing truth |
| Investigate scripted usage | velocity/cadence/overnight signals, shadow rules, historical replay | distinguish automation from high-intensity legitimate use |
| Investigate account / credential sharing | device/IP dispersion, conservative entity graph, competing explanations | avoid treating shared network context as identity proof |
| Investigate token misuse | token-degree evidence, linked-account components, legitimate approved-integration token confounders | require corroboration before escalation |
| Investigate usage-limit evasion | separate entitlement ledger, linked billing families, simultaneous near-limit pressure, SQL investigation query | create investigation leads while excluding explicit managed shared-billing controls |
| Investigate coordinated activity | coordinated device/IP/payment families, graph evidence, emerging cohort graph triage | distinguish behavioral campaigns from strong identity linkage |
| Prompt-injection / policy-signal analysis | aggregate injection/policy/safety-block signals, security-research confounder | investigate safety-signal changes without exposing raw prompts/completions |
| Discover emerging / previously unknown abuse | hidden-taxonomy benchmark, recent-vs-baseline novelty scoring, behavior cohorts, candidate taxonomy proposals | surface new modus operandi without requiring a pre-existing abuse label |
| Separate novelty from data incidents | `novelty_incident_diagnostics.csv`, telemetry coverage contracts | avoid creating a new abuse taxonomy because instrumentation changed |
| Build reports, dashboards, and self-service analytics | Decision Center, executive brief, stakeholder briefs, semantic SQL views | make recurring decisions reproducible rather than one-off analyst queries |
| Prototype detection / anomaly methods | logistic baseline, Isolation Forest, linked-entity signal, candidate shadow rules, novelty cohort discovery | compare multiple signal families without equating score with guilt |
| Evaluate false positives / false negatives | FPR/FNR, reportable operational slices, managed-infrastructure and approved-organization controls | quantify legitimate-user impact before policy change |
| Critically evaluate statistical assumptions | frozen holdout thresholds, calibration, PSI, one-sided rule uncertainty bounds, evidence-volume gates, hidden-label separation | reject attractive results when evidence or evaluation design is weak |
| Recurring monitoring for emerging abuse | robust daily known-signal alerts plus unsupervised recent-vs-baseline cohort discovery | detect both known metric shifts and patterns outside the current taxonomy |
| Improve abuse-relevant data quality | telemetry contracts, entitlement contracts, signal-integration backlog | block detection changes when source data is unreliable |
| Recommend new pipelines / integrations | backlog entries with analytical problem, proposed source, decision, privacy class, partner team | connect a missing signal to a concrete decision rather than asking for “more features” |
| Operationalize one-off investigation methods | versioned rule registry, candidate taxonomy → shadow definition, shadow → canary gates, rollback triggers, CI benchmark | turn an analysis into an auditable recurring process |
| Review-capacity and operational tradeoffs | review-capacity frontier, P0–P3 SLA, historical case arrivals, 0.5/1/2-FTE queue simulation | test whether a rule is operationally supportable before widening it |
| Measure mitigation impact | account-day DiD-style diagnostic, bootstrap interval, pre-trend checks | avoid unsupported causal claims from before/after movement |
| Review / appeal / overturn feedback | delayed label maturity, review feedback metrics, enforcement safety outputs | feed cleared and overturned cases back into rule/threshold/taxonomy review |
| SQL / Python / BI-style reporting | reusable SQL queries including emerging-discovery SQL, Python pipeline, semantic views, interactive HTML Decision Center | support both deep investigation and repeatable stakeholder reporting |
| Sensitive-data governance | hashed/pseudonymous metadata, no raw prompt/completion default layer, raw identity/payment boundary, CELA-style brief | apply purpose limitation and access boundaries to sensitive analysis |
| Cross-functional decision support | separate Trust & Safety, Engineering, and privacy/legal briefs plus stakeholder action register | translate the same evidence into different owner-specific actions |
| Mentor / raise analytical quality | analyst playbook, metric contracts, evidence gates, runbooks, tests | encode review standards that another analyst can apply consistently |

## Explicit limits

The project does not claim:

- GitHub-scale data volume;
- real Copilot telemetry, prompts, completions, billing, or account records;
- access to GitHub internal abuse taxonomies or enforcement policy;
- real CELA decisions or production enforcement experience;
- causal proof from the synthetic mitigation experiment.

The repository is intended to show the analytical reasoning, controls, tooling, and decision workflow that can transfer to a real Trust & Safety environment.
