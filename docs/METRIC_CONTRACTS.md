# Metric contracts

Every operational metric needs a unit, owner, decision, dimensions, and failure behavior.

Examples:

- **False-positive rate** — unit: account; decision: threshold/rule review; publish slices only when sample-size guards are met.
- **Review-capacity precision** — unit: account; decision: daily/weekly queue size; segment by plan and managed infrastructure.
- **Signal coverage** — unit: event; decision: data incident; do not hide a telemetry regression by retuning detection.
- **Appeal overturn rate** — unit: enforced investigation; decision: enforcement-safety review; use matured labels.
- **Mitigation effect** — unit: requests/account-day; decision: rollout review; require comparison group, interval, and pre-trend checks.
