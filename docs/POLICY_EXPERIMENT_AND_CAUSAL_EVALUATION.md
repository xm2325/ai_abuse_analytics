# Policy experimentation and causal evaluation

## Decision question

A mitigation can appear successful because the visible metric falls while behavior moves to another surface, account, or workflow. v0.9 asks:

> Should a Trust & Safety policy remain in shadow, continue as a limited canary, pause, or return to shadow after accounting for assignment quality, user impact, spillover, delayed labels, and operational guardrails?

This is a synthetic portfolio benchmark. It does not represent a real GitHub/Copilot experiment, policy, threshold, or enforcement system.

## 1. Pre-rollout-only eligibility and assignment

Experiment eligibility, clustering, and stratification are built only from data before the rollout date.

The workflow deliberately does **not** use the full-period model score for assignment because that score contains post-rollout behavior and would create post-treatment leakage.

Pre-period inputs include:

- active days;
- requests per active day;
- aggregate policy-signal rate;
- plan / region / managed-infrastructure metadata;
- pre-period organization, token, and payment relationships used only to define randomization clusters.

## 2. Cluster-randomized design

Accounts connected by stronger pre-period contexts are assigned together:

- same organization;
- low-degree shared token context;
- low-degree shared payment context.

This reduces obvious treatment contamination across strongly connected accounts.

IP overlap is **not** used as identity proof. It remains a weak context-only neighborhood for spillover sensitivity because NAT, VPNs, corporate egress, and shared infrastructure can produce benign overlap.

Arms:

```text
control
shadow
canary
```

`shadow` has no user-facing treatment and acts as an operational placebo/reference arm.

## 3. Hidden synthetic benchmark truth

`data/hidden_policy_experiment_manifest.csv` records synthetic responder and migration truth **only for benchmark scoring after assignment and estimates are fixed**.

It is never used by:

- eligibility;
- randomization clusters;
- stratification;
- arm assignment;
- ITT / ATT-style estimation;
- pre-trend checks;
- HTE analysis;
- sequential stopping rules.

This separation prevents the experiment evaluator from using the answer key to define the experiment.

## 4. Primary estimands

### ITT: canary vs control

The primary effect is a cluster-level change comparison between assigned canary and control clusters.

It answers:

> What is the effect of assigning an eligible cluster to the canary policy under the observed exposure and non-compliance pattern?

### Wald ATT-style diagnostic

A synthetic complier-style diagnostic divides ITT by observed canary exposure rate.

This requires strong assumptions similar to exclusion / monotonicity reasoning and is therefore explicitly labeled **diagnostic only**.

It should not replace ITT as the primary policy estimand.

## 5. Outcomes

The experiment reports multiple outcomes because a single falling metric can be misleading.

### Primary surface requests

Measures direct movement on the targeted surface.

### Total requests

Measures net activity after same-account surface displacement and synthetic migration inflow.

A large primary reduction with little total reduction suggests displacement rather than true reduction.

### Alternate-surface requests

A positive effect can indicate behavior moving to another product surface.

### Acceptance-rate guardrail

A user-experience proxy. Material deterioration blocks widening even when the primary abuse proxy improves.

### Prompt-length negative control

The synthetic intervention does not target mean prompt length. A material estimated effect is therefore a warning for imbalance, misspecification, or unstable inference.

### Shadow placebo

The shadow arm has no user-facing treatment. A material shadow-vs-control effect is an assignment / pre-trend warning rather than evidence of policy impact.

## 6. Interference and spillover

The project explicitly rejects a naive assumption that one account's treatment cannot affect another account.

Potential mechanisms include:

```text
rate limit on account A
        ↓
activity moves to account B
```

or:

```text
policy affects one product surface
        ↓
activity moves to another surface
```

Outputs therefore separate:

- direct primary-surface movement;
- alternate-surface displacement;
- total activity;
- cross-arm weak-context neighborhood exposure;
- strong-link randomization integrity.

The IP-context network is a **spillover sensitivity graph only** and never an identity graph.

## 7. Pre-trend / parallel-trend diagnostics

Although assignment is randomized in the synthetic benchmark, the workflow still reports pre-period slopes by arm.

Why?

Because in real operational experiments:

- implementation may not be perfectly randomized;
- eligibility may change;
- delayed activation can break comparability;
- cluster sizes can be imbalanced;
- logging changes can create apparent treatment effects.

A material pre-trend gap is therefore a reason to review the experiment before making a causal claim.

## 8. Sequential monitoring

The canary is reviewed at repeated post-rollout checkpoints.

Each checkpoint reports:

- primary ITT;
- total-request ITT;
- alternate-surface movement;
- acceptance-rate guardrail;
- negative-control movement;
- displacement ratio;
- recommended operational action.

The displayed 99% interval is a **conservative descriptive monitoring boundary**, not a claim of a formal group-sequential alpha-spending design.

No metric automatically expands a canary.

Possible recommendations:

```text
hold_canary_collect_more_evidence
continue_canary_collect_evidence
pause_and_review_displacement
rollback_to_shadow_user_impact_guardrail
```

Final policy-owner review remains mandatory.

## 9. Stopping / rollback guardrails

A canary can be paused or returned to shadow when evidence indicates:

- user-experience harm;
- high behavior displacement;
- material pre-trend risk;
- high matured clearance rate among reviewed cases;
- sequential user-impact stop;
- assignment/interference integrity problems.

A favorable primary metric is not sufficient by itself.

## 10. Delayed review / appeal feedback

`policy_experiment_review_guardrails.csv` reports arm-level matured evidence where available:

- matured reviews;
- cleared rate;
- enforcement rate;
- appeal rate among enforced cases;
- overturn rate among appeals;
- evidence-volume status.

Small samples are reported as `limited_matured_review_evidence` rather than converted into confident policy claims.

## 11. Heterogeneous treatment effects

The project reports diagnostic effects by operational slices such as:

- plan;
- managed-infrastructure status;
- region.

A slice is only marked reportable after minimum treated/control cluster counts.

These are exploratory HTE diagnostics. They do not justify slice-specific policy without:

- multiplicity control;
- adequate power;
- stability across time;
- product/legal review;
- legitimate-user impact review.

## 12. Outputs

```text
policy_experiment_assignment.csv
policy_experiment_daily_outcomes.csv
policy_experiment_effect_summary.csv
policy_experiment_pretrend.csv
policy_experiment_heterogeneous_effects.csv
policy_experiment_sequential_monitor.csv
policy_experiment_interference_audit.csv
policy_experiment_review_guardrails.csv
policy_experiment_stopping_decision.json
policy_experiment_benchmark.json
```

## 13. Interpretation hierarchy

Use the following order:

```text
Was assignment defined without post-treatment leakage?
        ↓
Are randomization clusters / interference assumptions credible?
        ↓
Do pre-trends / placebo / negative controls look acceptable?
        ↓
What is ITT on the primary outcome?
        ↓
Did activity move to another surface/account?
        ↓
What is the net total effect?
        ↓
Are user-impact / review / appeal guardrails acceptable?
        ↓
Are HTE findings sufficiently powered?
        ↓
Continue limited canary, collect more evidence, pause, or rollback
```

## 14. Production boundary

A production experiment would additionally require a formal experiment registry, power/MDE calculations, treatment logging, exposure consistency checks, cluster-level robust inference or randomization inference, explicit network-interference assumptions, approved sequential testing design, late-arriving outcome handling, experiment collision management, privacy review, and auditable policy-owner sign-off.

This repository demonstrates the analytical reasoning and controls; it does not claim production causal inference or real policy experimentation experience.
