# Adversarial adaptation and detection-evasion stress testing

## Decision question

A detection rule can look strong on a static holdout and still become weak after users adapt to visible controls, rate limits, review patterns, or enforcement. This module asks:

> If behavior changes specifically in the direction that reduces known rule signals, which controls become brittle, how quickly does recall degrade, and does a multi-signal defense degrade more gracefully?

This is a **coarse synthetic resilience benchmark**. It is not a real-product bypass guide and does not reproduce or disclose any GitHub/Copilot production controls.

## Synthetic adaptation families

The stress suite uses six abstract adaptation families:

- `velocity_smoothing` — reduces burst/regularity/overnight signatures;
- `identity_fragmentation` — weakens device/IP dispersion evidence;
- `token_rotation` — weakens repeated shared-token evidence;
- `quota_spreading` — reduces concentrated quota/payment/device pressure;
- `policy_signal_suppression` — weakens aggregate policy/injection signal rates;
- `multi_signal_blending` — applies smaller changes across several signal families at once.

Each is evaluated at 25%, 50%, 75%, and 100% synthetic adaptation strength. These percentages are scenario parameters, not estimates of attacker capability.

## Frozen-rule requirement

The rules are frozen before the stress test. The adversarial benchmark does **not** re-fit thresholds after adaptation. This preserves the question we actually care about:

> How brittle is the existing detection definition when behavior changes?

The development-derived velocity and quota cutoffs remain fixed.

## Outputs

### `adversarial_rule_stress.csv`

Per rule × strategy × adaptation strength:

- baseline recall;
- adapted recall;
- recall drop;
- baseline/adapted precision;
- baseline/adapted FPR;
- review workload.

### `defense_in_depth_stress.csv`

A diagnostic union of independent frozen rule families. It is not a production ensemble policy. It tests whether diversified signals degrade more gracefully than the most brittle single rule.

### `adversarial_stress_summary.json`

Captures the worst observed single-rule degradation and worst defense-in-depth degradation, plus the operating response.

### `evasion_regression_gates.csv`

Release-style analytical gates:

1. brittleness must be measured and surfaced rather than hidden;
2. defense-in-depth should not degrade worse than the worst single rule;
3. severe adaptation scenarios have a diagnostic recall floor.

A warning means **do not silently widen or promote the affected control**. It should trigger rework, independent-signal development, canary/replay testing, and rollback planning.

## Threshold gaming and near-boundary behavior

Exact production thresholds should not be published or treated as stable safety boundaries. A deterministic threshold can create a target for optimization. Operationally:

- use ranges and uncertainty internally rather than public exact cutoffs;
- watch for growing mass just below a known review boundary;
- compare multiple independent signal families;
- rotate or retire brittle rules through a versioned registry;
- use shadow → canary → replay → policy-owner review;
- define rollback triggers before widening a rule.

## Defense-in-depth interpretation

A lower recall drop in the multi-rule diagnostic does **not** prove the system is safe. It only suggests that one adaptation family cannot remove every signal at once as easily as it can remove one deterministic indicator.

Before operational use, still review:

- false positives and legitimate-user impact;
- analyst capacity and SLA;
- label maturity and uncertainty;
- telemetry health and drift;
- appeals / overturned enforcement;
- product or integration changes that may mimic adaptation.

## Rollback trigger examples

A canary or recently widened control should return to shadow/review when any of these occur materially:

- recall proxy deteriorates after a behavior shift;
- false-positive or appeal/overturn rates increase;
- queue backlog breaches analyst capacity;
- a new legitimate product workflow overlaps the signal;
- telemetry coverage or semantics change;
- adversarial stress regression exceeds the accepted resilience envelope.

## Safety boundary

The stress suite is for defensive analytics and governance. It uses only synthetic aggregated account features and coarse scenario transforms. It does not provide real system thresholds, exploit steps, operational bypass instructions, or automatic enforcement decisions.
