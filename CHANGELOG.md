# Changelog

## v0.5.0 — historical replay, evidence power, and queue stress testing

- Added time-based historical replay with explicit no-lookahead windows and replay phases around mitigation and emerging-abuse changes.
- Froze distribution-derived shadow-rule thresholds on the development split before holdout evaluation, removing holdout threshold adaptation.
- Added one-sided uncertainty bounds for rule FPR and precision so small clean samples are not treated as sufficient policy evidence.
- Added mature-label coverage at each replay checkpoint; unresolved or not-yet-mature labels are not silently treated as negatives.
- Added synthetic analyst queue arrival/service simulation across 0.5, 1.0, and 2.0 FTE scenarios, including backlog, SLA, utilization, and p95 time-to-review diagnostics.
- Added Decision Center sections, SQL replay example, operating documentation, tests, and CI artifact contracts for the new controls.

All v0.5 outputs remain investigation and policy-review decision support. They never authorize automatic enforcement.

## v0.4.0 — threshold policy simulation

- Added a threshold frontier for human-review policy planning.
- Added hard guardrails for global FPR, review workload, worst reportable slice FPR, minimum precision, and minimum triggered-account evidence volume.
- Added an explicit `no_threshold_meets_all_guardrails` outcome rather than forcing a policy choice.
- Added SQL threshold-frontier example and policy-review documentation.
- Extended CI/tests to require the new policy artifacts.

On the 180-account seed-17 synthetic benchmark, no threshold had enough evidence to satisfy every guardrail. The diagnostic least-violation threshold is not a production recommendation.
