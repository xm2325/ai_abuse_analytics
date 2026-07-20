# Architecture

## Local reproducible path

```text
synthetic accounts + telemetry + review outcomes
        ↓
validated data contracts
        ↓
account feature mart
        ↓
supervised probability + anomaly score + conservative linkage signal
        ↓
risk score and shadow rules
        ↓
review-capacity analysis + investigation queue
        ↓
case evidence + human review + appeal feedback
        ↓
mitigation / drift / calibration / operational monitoring
        ↓
Decision Center + stakeholder briefs
```

The local implementation uses CSV, Pandas, SQLite-style SQL, scikit-learn, and Plotly so the complete benchmark can be rebuilt in CI.

## Production translation

A production design would separate raw event ingestion, restricted identity/content zones, validated event-time marts, certified metrics, investigator-facing case views, and monitoring outputs. Large event tables should be partitioned by event time and materialized incrementally. Late-arriving data and backfills must be idempotent.

The analyst layer should consume derived, purpose-limited signals by default. Raw prompt/completion access should not be required for ordinary prioritization and should use a separate approved path when needed.
