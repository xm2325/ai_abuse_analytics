# Start here — AI Abuse Analytics v1.0

## 30-second answer
This repository is a **synthetic, privacy-safe Trust & Safety analytics operating workbench for an AI developer product**. It connects telemetry, account, entitlement and review signals to known-abuse detection, unknown-pattern discovery, investigation, rule evidence, adversarial-resilience testing, controlled policy experiments, appeal/overturn feedback, and auditable operating decisions.

It does **not** use GitHub internal data or claim production enforcement experience.

## Current operating state
- Release: **1.0.0**
- Artifact integrity: **ready_for_portfolio_demo**
- Operating status: **ready_with_active_operating_hold**
- Current decision state: **blocked_by_active_operating_slo_breach**
- Registered controls: **9**
- SLO breaches: **1**; review-needed SLOs: **2**
- Active incident/replay rows: **4**
- Policy experiment state: **hold_canary_review_displacement_collect_more_evidence**
- Automatic enforcement: **disabled**
- Automatic policy expansion: **disabled**

The apparent tension is intentional: the **v1 artifacts are coherent and demo-ready**, while the current synthetic operating run correctly blocks widening/retuning because an injected IP-coverage incident is active and evidence/review maturity gates remain open.

## The four questions to ask
1. **What should an analyst investigate now?** — `artifacts/investigation_queue.csv` and privacy-safe case files.
2. **Is the evidence strong enough to change a rule/taxonomy?** — rule registry, evidence-power bounds, historical replay and adversarial stress.
3. **Did a mitigation actually reduce harm, or move behavior elsewhere?** — cluster-randomized synthetic canary, ITT/ATT-style diagnostics, placebo/negative controls and displacement monitoring.
4. **Can another team reconstruct why a decision was made?** — `operating_control_registry.csv`, `decision_lineage.csv`, `decision_audit_trail.csv`, `data_lineage.csv`, SLOs and evidence packages.

## Current hold / review signals
| priority | decision | current state |
|---|---|---|
| P0 | review threshold impact on legitimate usage | `blocked_or_hold` |
| P0 | protect detection from telemetry regressions | `blocked_or_hold` |
| P1 | policy canary continue / pause / return to shadow | `blocked_or_hold` |

## Operating SLOs needing attention
| SLO | observed | status | action |
|---|---:|---|---|
| source contract health | 1 failing/warning contract | breach | repair/annotate source before detection or taxonomy changes |
| rule evidence maturity | 0 evidence-ready rules | review | keep rules in shadow; collect independent replay/matured labels |
| canary matured-review evidence | 4 matured reviews | review | hold/limit canary; collect matured review and appeal outcomes |

The synthetic IP-coverage incident is deliberate. It demonstrates that a healthy operating layer can still produce a **hold** when its source/evidence SLOs say not to widen policy.

## One evidence package to inspect
`artifacts/evidence_packages/PKG-001.md`

The final CI benchmark generated three privacy-safe packages. They connect each pseudonymous investigation candidate to:

- reason codes and risk priority;
- the **relevant** registered rule family rather than a globally convenient rule;
- active data-contract caveats;
- historical replay / evidence-power / adversarial-resilience context;
- current policy-experiment state;
- competing benign explanations;
- privacy and escalation gates.

## 2–3 minute review path
1. Open `docs/index.html` and read **v1.0 Operating brief — start here**.
2. Inspect **Decision lineage** and **Operating SLO scorecard** before reading model metrics.
3. Inspect one **Case → policy evidence package**.
4. Scroll to **Policy experiment / causal evaluation** to see why a targeted metric decrease is not automatically called a success.
5. Scroll to **Unknown / emerging abuse discovery** and **Adversarial adaptation** to see how the system handles novel and adaptive behavior.
6. Read `docs/JD_TRACEABILITY.md` for the public-role-to-repository mapping.

## Architecture in one line
`data contracts → detection/discovery → investigation → evidence/replay/resilience → controlled experiment → decision lineage/SLO/audit → human policy decision`

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

The pipeline refreshes this file, rebuilds `docs/index.html`, and regenerates case-to-policy evidence packages from the current synthetic run.
