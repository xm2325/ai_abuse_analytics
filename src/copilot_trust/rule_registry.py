from __future__ import annotations

from pathlib import Path
import pandas as pd


def build_rule_registry(rule_eval: pd.DataFrame, out_dir: str | Path) -> pd.DataFrame:
    """Turn shadow-rule evaluation into a versioned promotion/rollback register."""
    out = Path(out_dir)
    holdout = rule_eval[rule_eval.evaluation_scope.eq("holdout")].copy() if "evaluation_scope" in rule_eval else rule_eval.copy()
    rows = []
    for i, r in holdout.reset_index(drop=True).iterrows():
        triggers = int(r.get("accounts_triggered", 0))
        precision = float(r.get("precision", 0.0))
        fpr = float(r.get("false_positive_rate", 1.0))
        recommendation = str(r.get("recommendation", "review"))
        if recommendation == "candidate_for_review_queue" and triggers >= 10 and precision >= 0.75 and fpr <= 0.03:
            stage = "canary_review_queue"
        elif triggers < 5:
            stage = "shadow_more_evidence"
        else:
            stage = "shadow_revise"
        rows.append({
            "rule_id": f"R-{i+1:03d}",
            "rule_name": r.get("rule_name", f"candidate_{i+1}"),
            "version": "0.3.0",
            "stage": stage,
            "owner": "Trust & Safety Analytics",
            "triggered_accounts_holdout": triggers,
            "holdout_precision": precision,
            "holdout_fpr": fpr,
            "promotion_gate": "sufficient volume + precision/FPR guardrail + legitimate-user review",
            "rollback_trigger": "FPR guardrail breach, material appeal/overturn increase, or telemetry contract failure",
            "automatic_enforcement_allowed": False,
        })
    registry = pd.DataFrame(rows)
    registry.to_csv(out / "detection_rule_registry.csv", index=False)
    return registry
