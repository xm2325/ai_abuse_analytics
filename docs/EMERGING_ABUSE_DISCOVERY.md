# Emerging abuse discovery

This layer addresses a different question from known-rule monitoring:

> What if a harmful behavior is not yet represented in the current abuse taxonomy or detection rules?

## Separation from known labels

The synthetic benchmark injects a late hidden pattern into a small set of accounts. The hidden manifest is **benchmark-only** and is never read by discovery, clustering, graph triage, taxonomy generation, or candidate-rule definition.

Discovery uses only recent-vs-baseline behavior changes:

- request-volume shift;
- per-account token rotation;
- model-surface expansion;
- surface-switch rate;
- agent-share shift;
- acceptance-pattern shift.

The injected benchmark pattern is intentionally not a known rule shortcut: it does not depend on policy-signal spikes, shared tokens across accounts, large device dispersion, or obvious quota pressure.

## Workflow

```text
recent-vs-baseline account behavior
        ↓
robust multivariate novelty score
        ↓
top novelty candidate set
        ↓
behavior cohort clustering
        ↓
telemetry/data-incident screen
        ↓
shared-entity graph/context triage
        ↓
candidate taxonomy proposal
        ↓
analyst competing-explanation review
        ↓
candidate shadow definition only
        ↓
independent replay + matured labels + FPR uncertainty + capacity review
```

## Novelty is not abuse

A novel cohort can be caused by:

- a product launch or UX change;
- an approved organization integration;
- an SDK retry change;
- client migration;
- enterprise automation;
- a telemetry regression;
- genuinely new abuse.

Therefore `candidate_taxonomy_proposals.csv` uses `analyst_taxonomy_review_required`, not an abuse verdict.

## Graph boundary

Graph triage treats token/payment/device overlap as stronger linkage evidence than IP overlap, but even strong linkage is not proof of harmful coordination. IP-only overlap never establishes common control because NAT, VPN, enterprise egress, managed runners, and shared networks create benign overlap.

## From discovery to rule lifecycle

`novel_shadow_rule_candidates.csv` deliberately stops at `independent_shadow_replay_required`.

No discovered cohort may become an enforcement rule from the discovery window itself. Promotion requires:

1. an independently frozen rule definition;
2. a later time window or holdout;
3. matured human-review outcomes;
4. false-positive uncertainty bounds;
5. legitimate integration/context review;
6. analyst queue-capacity validation;
7. policy-owner approval.

## Benchmark-only evaluation

`emerging_discovery_benchmark.json` reports whether the hidden synthetic pattern was recovered by the candidate set. This metric is calculated **after** discovery outputs are fixed and is never fed back into ranking or clustering.
