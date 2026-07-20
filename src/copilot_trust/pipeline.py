from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd
from .adversarial_stress import build_evasion_regression_gates, evaluate_adversarial_adaptation
from .data_quality import build_signal_backlog, run_data_contracts
from .drift import evaluate_drift
from .emerging_discovery import discover_emerging_abuse
from .entitlements import build_synthetic_entitlement_ledger, evaluate_entitlement_abuse
from .evaluate import data_quality_report, evaluate_slices, review_capacity_analysis
from .evidence_power import evaluate_rule_evidence_power
from .features import build_feature_mart
from .feedback import evaluate_review_feedback
from .generate import SyntheticConfig, generate_synthetic_telemetry
from .historical_replay import build_historical_replay
from .investigate import build_investigation_queue, build_linked_account_components
from .mitigation import evaluate_mitigation
from .monitoring import build_daily_monitor
from .reporting import build_dashboard, build_executive_brief
from .rules import evaluate_shadow_rules
from .rule_registry import build_rule_registry
from .queue_ops import evaluate_queue_operations
from .queue_simulation import simulate_queue_capacity
from .policy_simulation import simulate_threshold_policy
from .scoring import train_and_score
from .stakeholder import build_action_register, build_stakeholder_briefs
from .synthetic_controls import inject_legitimate_entity_confounders
from .synthetic_novelty import inject_hidden_emerging_pattern


def run(root: str | Path, n_accounts: int = 4500, seed: int = 17):
    root=Path(root); data=root/"data"; art=root/"artifacts"; docs=root/"docs"
    generate_synthetic_telemetry(data,SyntheticConfig(n_accounts=n_accounts,seed=seed))
    inject_legitimate_entity_confounders(data)
    inject_hidden_emerging_pattern(data,seed=seed)
    build_synthetic_entitlement_ledger(data)
    build_feature_mart(data,art/"account_feature_mart.csv")
    scores,metrics=train_and_score(art/"account_feature_mart.csv",art,seed=seed)
    slices=evaluate_slices(scores,art); review_capacity=review_capacity_analysis(scores,art); coverage=data_quality_report(data,art)
    dq=run_data_contracts(data,art); signal_backlog=build_signal_backlog(art); daily_monitor,alerts=build_daily_monitor(data,art)
    discovery=discover_emerging_abuse(data,art,scores,seed=seed)
    entitlement_usage,billing_families,entitlement_queue,entitlement_dq=evaluate_entitlement_abuse(data,art)
    rules=evaluate_shadow_rules(scores,art); rule_evidence=evaluate_rule_evidence_power(rules,art); rule_registry=build_rule_registry(rules,art,rule_evidence)
    adversarial_stress,defense_stress,adversarial_summary=evaluate_adversarial_adaptation(scores,art)
    # Make target-scenario recall the primary single-rule resilience view when the synthetic
    # holdout contains that rule's target scenario; retain overall recall as explicit context.
    adversarial_stress["baseline_overall_recall"]=adversarial_stress["baseline_recall"]
    adversarial_stress["adapted_overall_recall"]=adversarial_stress["adapted_recall"]
    adversarial_stress["overall_recall_drop"]=adversarial_stress["recall_drop"]
    has_target=adversarial_stress.target_accounts_holdout.gt(0)
    adversarial_stress.loc[has_target,"baseline_recall"]=adversarial_stress.loc[has_target,"baseline_target_recall"]
    adversarial_stress.loc[has_target,"adapted_recall"]=adversarial_stress.loc[has_target,"adapted_target_recall"]
    adversarial_stress.loc[has_target,"recall_drop"]=adversarial_stress.loc[has_target,"target_recall_drop"]
    adversarial_stress["recall_metric_scope"]=has_target.map({True:"target_scenario",False:"overall_fallback_no_target_holdout"})
    adversarial_stress.to_csv(art/"adversarial_rule_stress.csv",index=False)
    # Keep backward-compatible summary keys for downstream briefs while making target-scenario
    # recall the primary single-rule brittleness metric.
    worst_rule=adversarial_summary.get("worst_single_rule",{})
    if worst_rule:
        worst_rule["baseline_recall"]=worst_rule.get("baseline_target_recall",worst_rule.get("baseline_overall_recall"))
        worst_rule["adapted_recall"]=worst_rule.get("adapted_target_recall",worst_rule.get("adapted_overall_recall"))
        worst_rule["recall_drop"]=worst_rule.get("target_recall_drop",worst_rule.get("overall_recall_drop",0.0))
        target_n=int(worst_rule.get("target_accounts_holdout",0) or 0)
        worst_rule["evidence_volume_status"]="sufficient_for_stress_claim" if target_n>=3 else "limited_evidence_fragility_hypothesis"
        worst_rule["evidence_volume_note"]=(
            "Target-scenario stress has at least 3 holdout accounts; still treat as synthetic diagnostic, not production evidence."
            if target_n>=3 else
            f"Only {target_n} target-scenario holdout account(s); treat the observed recall drop as a fragility hypothesis and expand time-based replay before policy conclusions."
        )
        (art/"adversarial_stress_summary.json").write_text(json.dumps(adversarial_summary,indent=2))
    evasion_gates=build_evasion_regression_gates(adversarial_stress,defense_stress,art)
    # Evidence-volume gate prevents a dramatic percentage drop on n=1 or n=2 from being
    # presented as a stable resilience estimate.
    if worst_rule:
        target_n=int(worst_rule.get("target_accounts_holdout",0) or 0)
        evidence_gate=pd.DataFrame([{
            "gate":"target_stress_evidence_volume",
            "observed":target_n,
            "guardrail":">= 3 target-scenario holdout accounts",
            "status":"pass" if target_n>=3 else "warn",
            "action":"if warning, treat brittleness as a hypothesis; expand time-based replay/holdout evidence before policy claims or P0 escalation",
        }])
        evasion_gates=pd.concat([evasion_gates,evidence_gate],ignore_index=True)
        evasion_gates.to_csv(art/"evasion_regression_gates.csv",index=False)
    drift,calibration=evaluate_drift(scores,art)
    queue_sla,queue_capacity=evaluate_queue_operations(scores,data,art); simulate_threshold_policy(scores,art)
    replay,replay_arrivals,replay_summary=build_historical_replay(data,art); queue_sim_daily,queue_sim_summary=simulate_queue_capacity(replay_arrivals,art)
    review_feedback,enforcement_safety=evaluate_review_feedback(scores,data,art); mitigation,mitigation_daily=evaluate_mitigation(data,art,seed=seed)
    build_investigation_queue(scores,data,art); build_linked_account_components(scores,data,art)
    action_register=build_action_register(metrics,slices,dq,alerts,rules,mitigation,art); build_stakeholder_briefs(action_register,review_feedback,signal_backlog,art)
    build_dashboard(scores,metrics,slices,coverage,mitigation,mitigation_daily,daily_monitor,alerts,dq,rules,review_feedback,action_register,review_capacity,drift,calibration,queue_sla,queue_capacity,rule_registry,docs/"index.html")
    build_executive_brief(scores,metrics,slices,coverage,mitigation,alerts,dq,review_capacity,rules,art/"executive_brief.md")
    return metrics


def main():
    p=argparse.ArgumentParser(); p.add_argument("--root",default="."); p.add_argument("--n-accounts",type=int,default=180); p.add_argument("--seed",type=int,default=17); a=p.parse_args(); print(run(a.root,a.n_accounts,a.seed))


if __name__=="__main__": main()
