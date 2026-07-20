# Detection rule lifecycle

## Stages

`hypothesis → shadow → evidence review → canary review queue → monitored production review queue → revise/retire`

Rules do not move directly from an analyst query to automatic enforcement.

## Promotion gates

A candidate rule should have sufficient trigger volume, acceptable false-positive rate, useful precision/recall under review capacity, explicit legitimate-user confounder analysis, stable input contracts, and an owner.

A small sample with perfect precision is not enough evidence. For example, 100% precision on two holdout hits remains `shadow_more_evidence`.

## Rollback

Rollback/review triggers include false-positive guardrail breaches, material appeal/overturn increases, telemetry contract failures, large population shift, major segment-mix change, or policy/taxonomy changes that invalidate the original interpretation.
