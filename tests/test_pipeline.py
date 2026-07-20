from pathlib import Path
import sys
import json
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from copilot_trust.pipeline import run


def test_small_pipeline(tmp_path):
    m=run(tmp_path,n_accounts=90,seed=3)
    assert 0<=m["roc_auc"]<=1
    assert 0<=m["false_positive_rate"]<=1
    assert 0<=m["brier_score"]<=1
    required=["docs/index.html","artifacts/investigation_queue.csv","artifacts/emerging_trend_alerts.csv","artifacts/data_quality_findings.csv","artifacts/rule_shadow_evaluation.csv","artifacts/review_feedback_metrics.csv","artifacts/mitigation_evaluation.csv","artifacts/stakeholder_action_register.csv","artifacts/feature_drift_diagnostics.csv","artifacts/risk_calibration_bins.csv","artifacts/queue_sla_snapshot.csv","artifacts/queue_capacity_plan.csv","artifacts/detection_rule_registry.csv","artifacts/policy_threshold_frontier.csv","artifacts/policy_threshold_recommendation.json","artifacts/brief_trust_safety.md","artifacts/brief_engineering.md","artifacts/brief_cela_governance.md"]
    for rel in required: assert (tmp_path/rel).exists(),rel


def test_enforcement_boundary_and_data_contracts(tmp_path):
    run(tmp_path,n_accounts=90,seed=11)
    rules=pd.read_csv(tmp_path/"artifacts/rule_shadow_evaluation.csv"); assert rules.enforcement_boundary.str.contains("never auto-enforce").all()
    queue=pd.read_csv(tmp_path/"artifacts/investigation_queue.csv"); forbidden={"prompt","completion","ip_address","payment_details","device_id"}; assert forbidden.isdisjoint(set(queue.columns))
    dq=pd.read_csv(tmp_path/"artifacts/data_quality_findings.csv"); assert "telemetry_schema" in set(dq.contract); assert "ip_hash_daily_coverage" in set(dq.contract)


def test_v03_operational_controls(tmp_path):
    run(tmp_path,n_accounts=90,seed=19)
    registry=pd.read_csv(tmp_path/"artifacts/detection_rule_registry.csv"); assert (registry.automatic_enforcement_allowed.astype(str).str.lower()=="false").all(); assert registry.rollback_trigger.str.len().gt(20).all()
    queue=pd.read_csv(tmp_path/"artifacts/queue_sla_snapshot.csv"); assert {"priority_tier","sla_hours","sla_breached","estimated_review_minutes"}.issubset(queue.columns)
    drift=pd.read_csv(tmp_path/"artifacts/feature_drift_diagnostics.csv"); assert {"feature","psi","status"}.issubset(drift.columns)


def test_v04_threshold_policy_guardrails(tmp_path):
    run(tmp_path,n_accounts=90,seed=23)
    frontier=pd.read_csv(tmp_path/"artifacts/policy_threshold_frontier.csv"); rec=json.loads((tmp_path/"artifacts/policy_threshold_recommendation.json").read_text())
    assert {"threshold","precision","recall","false_positive_rate","worst_reportable_slice_fpr","feasible_for_human_review_policy"}.issubset(frontier.columns)
    assert rec["enforcement_boundary"].startswith("human investigation")
    assert 0<=rec["review_workload_share"]<=1
    assert "min_triggered_accounts" in rec["guardrails"]
