# Billing and entitlement abuse investigation

GitHub-style AI product abuse can involve attempts to evade usage limits by distributing activity across multiple accounts, credentials, or billing identities. Billing and entitlement signals are useful, but they are easy to misuse if shared organizational billing is treated as proof of common malicious control.

v0.6 adds a separate synthetic entitlement ledger and a cycle-aware investigation workflow.

## Why the ledger is separate from telemetry

Telemetry is not treated as the billing source of truth. The project builds `data/entitlements.csv` as a separate source with:

- account and cycle identifiers;
- cycle start/end;
- plan;
- billing status;
- per-active-day entitlement limit;
- pseudonymous billing-family reference;
- billing context;
- managed-infrastructure indicator;
- source-system field.

This separation forces explicit data integration and data-contract checks before quota-abuse analysis.

## Investigation questions

The analysis asks:

1. Which accounts repeatedly approach their entitlement within a cycle?
2. Are several accounts in the same billing family under entitlement pressure at the same time?
3. Is the apparent relationship explained by legitimate enterprise/shared billing?
4. Does a candidate family require deeper identity or payment review through an approved access path?
5. Are billing/entitlement contracts complete and referentially valid before using the signals operationally?

## Outputs

`entitlement_cycle_usage.csv`

Account-cycle usage, effective allowance, utilization ratio, and near-limit indicator.

`billing_family_risk.csv`

Cycle-level family summaries including:

- family account count;
- combined requests and allowance;
- number of near-limit accounts;
- family usage ratio;
- managed-infrastructure share;
- legitimate shared-billing context;
- candidate multi-account evasion flag;
- reason codes.

`entitlement_investigation_queue.csv`

A privacy-safe lead queue. It exposes pseudonymous billing-family references rather than raw payment details.

`entitlement_data_quality.csv`

Checks schema, account-key integrity, and one-row-per-account-cycle uniqueness.

## What is not enough for enforcement

The following are investigation signals, not proof:

- multiple accounts with the same billing family;
- high entitlement utilization;
- synchronized near-limit usage;
- plan changes or billing retries;
- shared devices or networks.

Before escalation, an investigator should check legitimate explanations such as:

- enterprise or organization-level shared billing;
- multi-seat usage;
- approved automation;
- billing migrations;
- account consolidation;
- credits or temporary entitlement changes;
- family or organization ownership changes.

## Safe operating path

```text
cycle-level entitlement pressure
        ↓
shared billing-family pattern
        ↓
managed/shared-billing context check
        ↓
corroborate with independent behavioral or identity evidence
        ↓
human investigation
        ↓
policy / privacy review where required
        ↓
possible enforcement decision
```

The billing-family signal never authorizes automatic enforcement.
