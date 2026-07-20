from __future__ import annotations

from math import sqrt
from pathlib import Path
import pandas as pd


def _wilson_upper(k: int, n: int, z: float = 1.6448536269514722) -> float:
    if n <= 0:
        return 1.0
    p = k / n
    den = 1 + z * z / n
    center = p + z * z / (2 * n)
    radius = z * sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return min(1.0, (center + radius) / den)


def _wilson_lower(k: int, n: int, z: float = 1.6448536269514722) -> float:
    if n <= 0:
        return 0.0
    p = k / n
    den = 1 + z * z / n
    center = p + z * z / (2 * n)
    radius = z * sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return max(0.0, (center - radius) / den)


def evaluate_rule_evidence_power(
    rules: pd.DataFrame,
    out_dir: str | Path,
    *,
    target_fpr: float = 0.05,
    min_precision: float = 0.50,
    min_triggered_accounts: int = 5,
) -> pd.DataFrame:
    """Quantify whether holdout evidence is strong enough to support a rule-policy decision."""
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    holdout = rules[rules.evaluation_scope.eq("holdout")].copy()
    rows = []
    for _, r in holdout.iterrows():
        fp, tn, tp = int(r.fp), int(r.tn), int(r.tp)
        negatives = fp + tn
        triggered = int(r.accounts_triggered)
        fpr_upper = _wilson_upper(fp, negatives)
        precision_lower = _wilson_lower(tp, triggered)
        reasons = []
        if triggered < min_triggered_accounts:
            reasons.append("trigger_volume")
        if fpr_upper > target_fpr:
            reasons.append("fpr_uncertainty")
        if precision_lower < min_precision:
            reasons.append("precision_uncertainty")
        rows.append({
            "rule_name": r.rule_name,
            "holdout_triggered_accounts": triggered,
            "holdout_negative_accounts": negatives,
            "observed_false_positives": fp,
            "observed_precision": float(r.precision),
            "observed_fpr": float(r.false_positive_rate),
            "one_sided_95_fpr_upper": fpr_upper,
            "one_sided_95_precision_lower": precision_lower,
            "target_fpr": target_fpr,
            "min_precision": min_precision,
            "evidence_sufficient_for_policy_review": int(not reasons),
            "evidence_gaps": "|".join(reasons) if reasons else "none",
            "decision_boundary": "evidence sufficiency supports policy review only; never automatic enforcement",
        })
    result = pd.DataFrame(rows).sort_values(["evidence_sufficient_for_policy_review", "one_sided_95_fpr_upper"], ascending=[False, True])
    result.to_csv(out / "rule_evidence_power.csv", index=False)
    return result
