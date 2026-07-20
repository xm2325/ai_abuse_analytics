# Historical replay and evidence review

Trust & Safety rules should not be judged only on a random holdout. Abuse changes over time, mitigations alter behavior, instrumentation can fail, and review labels arrive late.

v0.5 adds a time-based operating review with four controls.

## 1. No-lookahead historical replay

Each checkpoint uses only telemetry at or before that checkpoint. The replay uses a trailing seven-day window and records the exact window boundaries in `historical_rule_replay.csv`.

Distribution-derived thresholds are estimated from an initial baseline period and then frozen. Future checkpoints never redefine earlier rule logic.

The synthetic benchmark separates three periods:

- pre-mitigation;
- post-mitigation;
- emerging-abuse campaign.

This allows an analyst to ask whether a rule still behaves the same after a product or policy intervention and whether a new abuse pattern creates workload or user-impact changes.

## 2. Mature labels only

Operational replay metrics distinguish synthetic benchmark ground truth from labels that would actually have been available at the checkpoint.

A review outcome is considered available only after the configured maturity delay. Unreviewed or not-yet-mature cases are not silently treated as legitimate users.

`matured_label_coverage_of_triggers` makes label incompleteness visible instead of hiding it inside a single precision number.

## 3. Evidence power, not point estimates alone

`rule_evidence_power.csv` reports:

- observed holdout FPR;
- a one-sided 95% upper confidence bound for FPR;
- observed precision;
- a one-sided 95% lower confidence bound for precision;
- triggered-account evidence volume;
- an explicit evidence-sufficiency status.

A rule can have 0% observed FPR and still fail the evidence review when the sample is too small. This prevents a small clean sample from being treated as proof that a rule is safe.

The output supports policy review only. It never authorizes automatic enforcement.

## 4. Queue arrival and service stress test

Historical rule triggers become synthetic investigation-case arrivals. The queue simulator evaluates 0.5, 1.0, and 2.0 analyst-FTE scenarios using only:

- arrival date;
- priority;
- risk proxy;
- estimated review effort.

Benchmark abuse labels are not used to prioritize the queue.

Outputs include:

- daily arrivals and completions;
- backlog;
- unresolved SLA breaches;
- oldest case age;
- utilization;
- maximum and final backlog;
- p95 time to review.

The operating question is not only whether a rule detects abuse. It is whether the team can review the cases safely and quickly enough after the rule is widened.

## Recommended rule-change gate

Before a candidate moves from shadow to a wider human-review queue, check:

1. telemetry contracts are healthy;
2. rule definitions were frozen before evaluation;
3. time-based replay does not show unacceptable drift in FPR or workload;
4. evidence-volume and uncertainty checks are adequate;
5. review-label coverage is understood;
6. queue simulation does not create unacceptable backlog or SLA risk;
7. appeal/overturn feedback does not show concentrated user harm;
8. policy and privacy owners approve any change in data use or enforcement behavior.

These checks are decision support, not an automated promotion system.
