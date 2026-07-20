from __future__ import annotations
from pathlib import Path
import pandas as pd


def build_rule_registry(rule_eval: pd.DataFrame, out_dir: str | Path, evidence: pd.DataFrame | None = None) -> pd.DataFrame:
    """Turn shadow-rule evaluation into a versioned promotion/rollback register.

    Point estimates are not enough for promotion. When evidence diagnostics are supplied, the registry
    requires their uncertainty/volume gate to pass before any canary recommendation is possible.
    """
    out = Path(out_dir)
    holdout = rule_eval[rule_eval.evaluation_scope.eq("holdout")].copy() if "evaluation_scope" in rule_eval else rule_eval.copy()
    evidence_map = evidence.set_index("rule_name") if evidence is not None and len(evidence) else None
    rows = []
    for i, r in holdout.reset_index(drop=True).iterrows():
        name = str(r.get("rule_name", f"candidate_{i+1}"))
        triggers = int(r.get("accounts_triggered", 0))
        precision = float(r.get("precision", 0.0))
        fpr = float(r.get("false_positive_rate", 1.0))
        recommendation = str(r.get("recommendation", "review"))
        evidence_pass = False
        evidence_gaps = "evidence_not_evaluated"
        fpr_upper = float("nan")
        precision_lower = float("nan")
        if evidence_map is not None and name in evidence_map.index:
            e = evidence_map.loc[name]
            evidence_pass = bool(int(e.evidence_sufficient_for_policy_review))
            evidence_gaps = str(e.evidence_gaps)
            fpr_upper = float(e.one_sided_95_fpr_upper)
            precision_lower = float(e.one_sided_95_precision_lower)

        if recommendation == "candidate_for_review_queue" and triggers >= 10 and precision >= 0.75 and fpr <= 0.03 and evidence_pass:
            stage = "canary_review_queue"
        elif not evidence_pass or triggers < 5:
            stage = "shadow_more_evidence"
        else:
            stage = "shadow_revise"
        rows.append({
            "rule_id": f"R-{i+1:03d}",
            "rule_name": name,
            "version": "0.5.0",
            "stage": stage,
            "owner": "Trust & Safety Analytics",
            "triggered_accounts_holdout": triggers,
            "holdout_precision": precision,
            "holdout_fpr": fpr,
            "one_sided_95_fpr_upper": fpr_upper,
            "one_sided_95_precision_lower": precision_lower,
            "evidence_gate_passed": evidence_pass,
            "evidence_gaps": evidence_gaps,
            "promotion_gate": "frozen rule + sufficient trigger volume + uncertainty-bounded FPR/precision + legitimate-user review + queue-capacity review",
            "rollback_trigger": "FPR uncertainty/guardrail breach, material appeal/overturn increase, queue SLA failure, or telemetry contract failure",
            "automatic_enforcement_allowed": False,
        })
    registry = pd.DataFrame(rows)
    registry.to_csv(out / "detection_rule_registry.csv", index=False)
    return registry
