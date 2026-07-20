# Production data model

## Suggested layers

```text
raw event streams
  → validated event contracts
  → account_usage_daily
  → account_entity_daily
  → signal_coverage_daily
  → review_outcome_daily
  → certified investigation / monitoring / evaluation views
```

Key controls include event-time semantics, late-arrival windows, idempotent backfills, incremental materialization, restricted raw-content access, purpose-limited identity joins, and versioned taxonomy/data contracts.

The local CSV/SQLite/Pandas path is for reproducibility and review, not a production-scale claim.
