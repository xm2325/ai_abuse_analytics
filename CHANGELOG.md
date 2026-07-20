# Changelog

## v0.4.0 — threshold policy simulation

- Added a threshold frontier for human-review policy planning.
- Added hard guardrails for global FPR, review workload, worst reportable slice FPR, minimum precision, and minimum triggered-account evidence volume.
- Added an explicit `no_threshold_meets_all_guardrails` outcome rather than forcing a policy choice.
- Added SQL threshold-frontier example and policy-review documentation.
- Extended CI/tests to require the new policy artifacts.

Checked locally with 4/4 tests passing. On the 180-account seed-17 benchmark, no threshold has enough evidence to satisfy every guardrail. The diagnostic least-violation threshold is not a production recommendation.
