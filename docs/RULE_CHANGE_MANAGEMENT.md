# Rule change management

Every detection-rule change should record:

- rule ID and version;
- owner and reviewers;
- hypothesis and intended decision;
- required input signals and data contracts;
- development/holdout trigger volume;
- precision, recall, false-positive rate, and workload;
- legitimate-user confounders;
- promotion gate;
- rollback trigger;
- effective date and previous version.

The benchmark registry keeps `automatic_enforcement_allowed = false`. Promotion changes only how cases enter a human review queue.
