from __future__ import annotations

import argparse
from pathlib import Path

from .data_quality import build_signal_backlog, run_data_contracts
from .drift import evaluate_drift
from .evaluate import data_quality_report, evaluate_slices, review_capacity_analysis
from .features import build_feature_mart
from .feedback import evaluate_review_feedback
from .generate import SyntheticConfig, generate_synthetic_telemetry
from .investigate import build_investigation_queue, build_linked_account_components
from .mitigation import evaluate_mitigation
from .monitoring import build_daily_monitor
from .reporting import build_dashboard, build_executive_brief
from .rules import evaluate_shadow_rules
from .rule_registry import build_rule_registry
from .queue_ops import evaluate_queue_operations
from .scoring import train_and_score
from .stakeholder import build_action_register, build_stakeholder_briefs


def run(root: str | Path, n_accounts: int = 4500, seed: int = 17):
    root = Path(root)
    data = root / "data"
    art = root / "artifacts"
    docs = root / "docs"

    generate_synthetic_telemetry(data, SyntheticConfig(n_accounts=n_accounts, seed=seed))
    build_feature_mart(data, art / "account_feature_mart.csv")
    scores, metrics = train_and_score(art / "account_feature_mart.csv", art, seed=seed)

    slices = evaluate_slices(scores, art)
    review_capacity = review_capacity_analysis(scores, art)
    coverage = data_quality_report(data, art)
    dq = run_data_contracts(data, art)
    signal_backlog = build_signal_backlog(art)
    daily_monitor, alerts = build_daily_monitor(data, art)
    rules = evaluate_shadow_rules(scores, art)
    rule_registry = build_rule_registry(rules, art)
    drift, calibration = evaluate_drift(scores, art)
    queue_sla, queue_capacity = evaluate_queue_operations(scores, data, art)
    review_feedback, enforcement_safety = evaluate_review_feedback(scores, data, art)
    mitigation, mitigation_daily = evaluate_mitigation(data, art, seed=seed)

    build_investigation_queue(scores, data, art)
    build_linked_account_components(scores, data, art)

    action_register = build_action_register(
        metrics, slices, dq, alerts, rules, mitigation, art
    )
    build_stakeholder_briefs(action_register, review_feedback, signal_backlog, art)

    build_dashboard(
        scores,
        metrics,
        slices,
        coverage,
        mitigation,
        mitigation_daily,
        daily_monitor,
        alerts,
        dq,
        rules,
        review_feedback,
        action_register,
        review_capacity,
        drift,
        calibration,
        queue_sla,
        queue_capacity,
        rule_registry,
        docs / "index.html",
    )
    build_executive_brief(
        scores,
        metrics,
        slices,
        coverage,
        mitigation,
        alerts,
        dq,
        review_capacity,
        rules,
        art / "executive_brief.md",
    )
    return metrics


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--n-accounts", type=int, default=180)
    p.add_argument("--seed", type=int, default=17)
    a = p.parse_args()
    print(run(a.root, a.n_accounts, a.seed))


if __name__ == "__main__":
    main()
