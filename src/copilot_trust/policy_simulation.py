from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd


def _binary_metrics(y: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    y = y.astype(int)
    pred = pred.astype(bool)
    tp = int(((y == 1) & pred).sum())
    fp = int(((y == 0) & pred).sum())
    tn = int(((y == 0) & ~pred).sum())
    fn = int(((y == 1) & ~pred).sum())
    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": tp / max(1, tp + fp),
        "recall": tp / max(1, tp + fn),
        "false_positive_rate": fp / max(1, fp + tn),
        "false_negative_rate": fn / max(1, fn + tp),
        "review_workload_share": float(pred.mean()),
    }


def simulate_threshold_policy(
    scores: pd.DataFrame,
    out_dir: str | Path,
    *,
    max_global_fpr: float = 0.05,
    max_review_share: float = 0.15,
    max_reportable_slice_fpr: float = 0.10,
    min_precision: float = 0.50,
    min_triggered_accounts: int = 5,
) -> tuple[pd.DataFrame, dict]:
    """Evaluate human-review thresholds under capacity, user-impact, and evidence guardrails."""
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    h = scores[scores.split.eq("holdout")].copy().reset_index(drop=True)
    if h.empty:
        raise ValueError("Threshold policy simulation requires a non-empty holdout set")

    raw = np.unique(np.concatenate([
        np.linspace(float(h.risk_score.min()), float(h.risk_score.max()), 80),
        h.risk_score.quantile(np.linspace(0.50, 0.99, 40)).to_numpy(),
    ]))
    rows = []
    for threshold in np.sort(raw):
        pred = h.risk_score.to_numpy() >= threshold
        m = _binary_metrics(h.label.to_numpy(), pred)
        slice_fprs = []
        for column in ["plan", "managed_infrastructure", "legitimate_profile"]:
            if column not in h.columns:
                continue
            for _, g in h.groupby(column, dropna=False):
                negatives = int((g.label == 0).sum())
                if len(g) < 10 or negatives < 5:
                    continue
                slice_fprs.append(_binary_metrics(g.label.to_numpy(), g.risk_score.to_numpy() >= threshold)["false_positive_rate"])
        worst_slice_fpr = max(slice_fprs) if slice_fprs else m["false_positive_rate"]
        managed = h[h.managed_infrastructure.eq(1)] if "managed_infrastructure" in h.columns else h.iloc[0:0]
        if len(managed) and int((managed.label == 0).sum()) > 0:
            managed_fpr = _binary_metrics(managed.label.to_numpy(), managed.risk_score.to_numpy() >= threshold)["false_positive_rate"]
        else:
            managed_fpr = np.nan

        violations = []
        if m["false_positive_rate"] > max_global_fpr: violations.append("global_fpr")
        if m["review_workload_share"] > max_review_share: violations.append("review_capacity")
        if worst_slice_fpr > max_reportable_slice_fpr: violations.append("slice_fpr")
        if m["precision"] < min_precision: violations.append("precision")
        if int(pred.sum()) < min_triggered_accounts: violations.append("evidence_volume")
        rows.append({
            "threshold": float(threshold), **m,
            "worst_reportable_slice_fpr": float(worst_slice_fpr),
            "managed_infrastructure_fpr": float(managed_fpr) if not np.isnan(managed_fpr) else np.nan,
            "feasible_for_human_review_policy": int(len(violations) == 0),
            "guardrail_violations": "|".join(violations) if violations else "none",
            "estimated_reviews_per_1000_accounts": int(round(1000 * m["review_workload_share"])),
        })

    frontier = pd.DataFrame(rows).sort_values("threshold").reset_index(drop=True)
    feasible = frontier[frontier.feasible_for_human_review_policy.eq(1)].copy()
    if len(feasible):
        chosen = feasible.sort_values(["recall", "precision", "review_workload_share"], ascending=[False, False, True]).iloc[0]
        status = "candidate_for_human_review_policy"
    else:
        frontier["violation_count"] = frontier.guardrail_violations.apply(lambda x: 0 if x == "none" else len(str(x).split("|")))
        chosen = frontier.sort_values(["violation_count", "false_positive_rate", "review_workload_share", "recall"], ascending=[True, True, True, False]).iloc[0]
        status = "no_threshold_meets_all_guardrails"

    recommendation = {
        "status": status,
        "selected_threshold": float(chosen.threshold),
        "precision": float(chosen.precision),
        "recall": float(chosen.recall),
        "global_false_positive_rate": float(chosen.false_positive_rate),
        "worst_reportable_slice_fpr": float(chosen.worst_reportable_slice_fpr),
        "review_workload_share": float(chosen.review_workload_share),
        "estimated_reviews_per_1000_accounts": int(chosen.estimated_reviews_per_1000_accounts),
        "guardrails": {"max_global_fpr": max_global_fpr, "max_review_share": max_review_share, "max_reportable_slice_fpr": max_reportable_slice_fpr, "min_precision": min_precision, "min_triggered_accounts": min_triggered_accounts},
        "enforcement_boundary": "human investigation prioritization only; never automatic enforcement",
        "evidence_warning": "Synthetic holdout and delayed-label benchmark; re-estimate on matured production review outcomes before policy change.",
    }
    frontier.to_csv(out / "policy_threshold_frontier.csv", index=False)
    (out / "policy_threshold_recommendation.json").write_text(json.dumps(recommendation, indent=2))
    return frontier, recommendation
