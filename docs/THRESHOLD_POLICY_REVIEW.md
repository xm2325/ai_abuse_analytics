# Threshold policy review

A model threshold is an operating policy choice, not only a statistical parameter.

The v0.4 simulator evaluates each candidate threshold against explicit guardrails:

- global false-positive rate;
- analyst review-capacity share;
- worst reportable operational-slice false-positive rate;
- minimum precision for the human-review queue;
- minimum triggered-account evidence volume.

A threshold is feasible only when all guardrails pass. Among feasible choices, the benchmark selects the highest-recall option, then uses precision and lower workload as tie-breakers. If no threshold passes, the system reports `no_threshold_meets_all_guardrails`; it does not invent a safe threshold.

For the checked 180-account synthetic benchmark, no threshold satisfies every guardrail once minimum evidence volume is included. This is the correct conservative result for the small holdout.

The output is a human-review policy aid. It never authorizes automatic enforcement. Production use would require matured review outcomes, current segment mix, current telemetry contracts, appeal/overturn feedback, and policy-owner approval.
