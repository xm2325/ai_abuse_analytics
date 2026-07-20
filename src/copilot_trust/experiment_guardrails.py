from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd


def refine_policy_experiment_guardrails(out_dir: str | Path) -> dict:
    """Refine synthetic canary stopping decisions using effect uncertainty.

    A large displacement ratio can be unstable when the primary effect is close to zero.
    Treat point-estimate-only displacement as a review signal, not a confirmed stop condition.
    """
    out = Path(out_dir)
    effects = pd.read_csv(out / "policy_experiment_effect_summary.csv")
    seq = pd.read_csv(out / "policy_experiment_sequential_monitor.csv")
    decision = json.loads((out / "policy_experiment_stopping_decision.json").read_text())

    def row(estimand: str, outcome: str):
        g = effects[(effects.estimand == estimand) & (effects.outcome == outcome)]
        return g.iloc[0] if len(g) else None

    primary = row("ITT_canary_vs_control", "primary_requests")
    alternate = row("ITT_canary_vs_control", "alternate_surface_requests")
    acceptance = row("ITT_canary_vs_control", "acceptance_rate_guardrail")
    ratio = decision.get("displacement_ratio")

    possible_displacement = bool(
        primary is not None
        and alternate is not None
        and np.isfinite(float(primary.estimate))
        and np.isfinite(float(alternate.estimate))
        and float(primary.estimate) < 0
        and float(alternate.estimate) > 0
        and ratio is not None
        and np.isfinite(float(ratio))
        and float(ratio) > 0.60
    )
    strong_displacement = bool(
        possible_displacement
        and float(primary.ci95_high) < 0
        and float(alternate.ci95_low) > 0
    )
    strong_user_harm = bool(
        acceptance is not None
        and np.isfinite(float(acceptance.estimate))
        and float(acceptance.estimate) < -0.03
        and float(acceptance.ci95_high) < 0
    )

    old_reasons = [x for x in decision.get("guardrail_reasons", []) if x not in {"high_behavior_displacement", "possible_behavior_displacement_low_precision", "acceptance_rate_harm"}]
    reasons = list(old_reasons)
    if strong_user_harm:
        reasons.append("acceptance_rate_harm")
    if strong_displacement:
        reasons.append("high_behavior_displacement")
    elif possible_displacement:
        reasons.append("possible_behavior_displacement_low_precision")

    hard_stop = strong_user_harm or strong_displacement or any(x in reasons for x in ["pretrend_risk", "high_matured_clearance_rate"])
    if hard_stop:
        state = "rollback_or_pause_to_shadow_for_review"
    elif possible_displacement:
        state = "hold_canary_review_displacement_collect_more_evidence"
    elif primary is not None and np.isfinite(float(primary.ci95_high)) and float(primary.ci95_high) < 0:
        state = "continue_limited_canary_collect_matured_evidence"
    else:
        state = "hold_current_canary_collect_more_evidence"

    decision["recommended_state"] = state
    decision["guardrail_reasons"] = reasons
    decision["displacement_evidence_status"] = (
        "strong_interval_supported" if strong_displacement
        else "point_estimate_signal_low_precision" if possible_displacement
        else "not_observed"
    )
    decision["automatic_policy_expansion_allowed"] = False
    decision["decision_boundary"] = "human policy-owner review required; sequential diagnostics never auto-expand or auto-enforce"
    (out / "policy_experiment_stopping_decision.json").write_text(json.dumps(decision, indent=2))

    if possible_displacement and not strong_displacement and len(seq):
        seq.loc[seq.recommended_action.eq("pause_and_review_displacement"), "recommended_action"] = "hold_canary_review_displacement_collect_more_evidence"
        seq.to_csv(out / "policy_experiment_sequential_monitor.csv", index=False)

    return decision
