# Start here — AI Abuse Analytics v1.0

## 30-second answer

This repository is a **synthetic, privacy-safe Trust & Safety analytics operating workbench for an AI developer product**.

It demonstrates how an analyst can connect:

```text
telemetry / accounts / entitlements / review feedback
→ data contracts
→ known-abuse detection + unknown-pattern discovery
→ investigation
→ evidence power + historical replay + adversarial resilience
→ controlled policy experiment
→ decision lineage + SLO + incident replay + audit
→ human policy decision
```

It does **not** use GitHub internal data or claim production enforcement experience.

## 2–3 minute review path

1. Open [`index.html`](index.html) and read **v1.0 Operating brief — start here** at the top.
2. Review **Decision lineage**: what decision needs attention, who owns it, and what gate remains.
3. Review **Operating SLO scorecard**: what passes, what needs review, and what would block widening/retuning.
4. Inspect one generated `artifacts/evidence_packages/PKG-xxx.md` after running the benchmark: this shows how a pseudonymous investigation candidate connects to competing explanations, rule evidence, experiment state and governance boundaries.
5. Scroll to **Policy experiment / causal evaluation**: targeted metric improvement is not automatically called success when behavior may be displaced.
6. Scroll to **Unknown / emerging abuse discovery** and **Adversarial adaptation**: see how the system handles patterns outside the taxonomy and controls that actors may adapt around.
7. Read [`JD_TRACEABILITY.md`](JD_TRACEABILITY.md) for the public-role-to-repository mapping.

## Four questions to keep in mind

### 1. What should an analyst investigate now?

Use the investigation queue, reason codes, entity/entitlement context and privacy-safe case evidence. A high score is a prioritization signal, not guilt.

### 2. Is the evidence strong enough to change a rule or taxonomy?

Use frozen evaluation, uncertainty/evidence-volume gates, historical replay, legitimate-user impact and adversarial-resilience checks. Small perfect-looking samples are not treated as sufficient evidence.

### 3. Did a mitigation actually reduce harm?

Use the synthetic control/shadow/canary experiment, ITT, placebo/negative controls, pre-trends, spillover/displacement and delayed review evidence. A targeted metric can fall while underlying behavior moves elsewhere.

### 4. Can another team reconstruct the decision?

Use the v1 operating artifacts:

```text
operating_control_registry.csv
decision_lineage.csv
data_lineage.csv
operating_slo_scorecard.csv
incident_replay_register.csv
decision_audit_trail.csv
evidence_package_index.csv
release_readiness.json
```

## Governance boundary

No score, rule, cohort, experiment estimate, registry state or evidence package authorizes automatic enforcement or automatic policy expansion.

The default analyst layer excludes raw prompts, completions, raw IPs, raw device identifiers, card numbers and payment details. Expanded sensitive-data review requires a separate approved access path.

## Reproduce the dynamic operating state

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_all.py --n-accounts 180 --seed 17
```

The pipeline refreshes this file with current synthetic operating-state details, rebuilds `docs/index.html`, and generates the case-to-policy evidence packages.
