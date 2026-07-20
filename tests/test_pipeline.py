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
    required=["docs/index.html","artifacts/investigation_queue.csv","artifacts/emerging_trend_alerts.csv","artifacts/data_quality_findings.csv","artifacts/rule_shadow_evaluation.csv","artifacts/review_feedback_metrics.csv","artifacts/mitigation_evaluation.csv","artifacts/stakeholder_action_register.csv","artifacts/feature_drift_diagnostics.csv","artifacts/risk_calibration_bins.csv","artifacts/queue_sla_snapshot.csv","artifacts/queue_capacity_plan.csv","artifacts/detection_rule_registry.csv","artifacts/policy_threshold_frontier.csv","artifacts/policy_threshold_recommendation.json","artifacts/historical_rule_replay.csv","artifacts/historical_case_arrivals.csv","artifacts/historical_rule_replay_summary.csv","artifacts/rule_evidence_power.csv","artifacts/queue_simulation_daily.csv","artifacts/queue_simulation_summary.csv","artifacts/entitlement_cycle_usage.csv","artifacts/billing_family_risk.csv","artifacts/entitlement_investigation_queue.csv","artifacts/entitlement_data_quality.csv","artifacts/emerging_novelty_accounts.csv","artifacts/emerging_behavior_cohorts.csv","artifacts/emerging_graph_triage.csv","artifacts/candidate_taxonomy_proposals.csv","artifacts/novel_shadow_rule_candidates.csv","artifacts/novelty_incident_diagnostics.csv","artifacts/emerging_discovery_benchmark.json","artifacts/adversarial_rule_stress.csv","artifacts/defense_in_depth_stress.csv","artifacts/adversarial_stress_summary.json","artifacts/evasion_regression_gates.csv","artifacts/brief_trust_safety.md","artifacts/brief_engineering.md","artifacts/brief_cela_governance.md"]
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


def test_v05_historical_replay_and_evidence_power(tmp_path):
    run(tmp_path,n_accounts=90,seed=29)
    replay=pd.read_csv(tmp_path/"artifacts/historical_rule_replay.csv")
    assert {"checkpoint","window_end","rule_id","phase","matured_label_coverage_of_triggers","lookahead_protection"}.issubset(replay.columns)
    assert replay.lookahead_protection.eq("events_after_checkpoint_excluded").all()
    frozen=pd.read_csv(tmp_path/"artifacts/rule_shadow_evaluation.csv")
    assert frozen.threshold_source.eq("development_frozen").all()
    for _,g in frozen.groupby("rule_name"):
        assert g.velocity_cut.nunique(dropna=False)==1
        assert g.quota_cut.nunique(dropna=False)==1
    power=pd.read_csv(tmp_path/"artifacts/rule_evidence_power.csv")
    assert {"one_sided_95_fpr_upper","one_sided_95_precision_lower","evidence_sufficient_for_policy_review","decision_boundary"}.issubset(power.columns)
    assert power.decision_boundary.str.contains("never automatic enforcement").all()
    registry=pd.read_csv(tmp_path/"artifacts/detection_rule_registry.csv")
    assert {"evidence_gate_passed","evidence_gaps","one_sided_95_fpr_upper"}.issubset(registry.columns)
    assert registry.loc[registry.stage.eq("canary_review_queue"),"evidence_gate_passed"].astype(str).str.lower().eq("true").all()
    sim=pd.read_csv(tmp_path/"artifacts/queue_simulation_summary.csv")
    assert {"analyst_fte","cases_arrived","final_backlog","max_backlog","p95_time_to_review_hours"}.issubset(sim.columns)
    assert (sim.final_backlog>=0).all()


def test_v06_entitlement_abuse_and_shared_billing_context(tmp_path):
    run(tmp_path,n_accounts=120,seed=31)
    assert (tmp_path/"data/entitlements.csv").exists()
    accounts=pd.read_csv(tmp_path/"data/accounts.csv")
    usage=pd.read_csv(tmp_path/"artifacts/entitlement_cycle_usage.csv")
    families=pd.read_csv(tmp_path/"artifacts/billing_family_risk.csv")
    queue=pd.read_csv(tmp_path/"artifacts/entitlement_investigation_queue.csv")
    dq=pd.read_csv(tmp_path/"artifacts/entitlement_data_quality.csv")
    expected={"scripted_automation","credential_sharing","quota_evasion","token_misuse","coordinated_abuse","policy_abuse"}
    counts=accounts[accounts.ground_truth_abuse_type.ne("legitimate")].ground_truth_abuse_type.value_counts()
    assert expected.issubset(set(counts.index))
    assert (counts.loc[list(expected)]>=2).all()
    assert "approved_organization_context" in accounts.columns
    approved=accounts[accounts.approved_organization_context.eq(1)]
    assert len(approved)>=6
    assert approved.ground_truth_abuse_type.eq("legitimate").all()
    assert {"cycle_index","usage_ratio","near_limit","billing_family_ref","entitlement_contract_version"}.issubset(usage.columns)
    assert {"family_accounts","near_limit_accounts","shared_billing_context","candidate_multi_account_evasion","reason_codes"}.issubset(families.columns)
    assert {"entitlement_schema","entitlement_account_referential_integrity","entitlement_cycle_uniqueness"}.issubset(set(dq.contract))
    assert dq.status.eq("pass").all()
    forbidden={"payment_details","card_number","raw_payment_method"}
    assert forbidden.isdisjoint(set(queue.columns))
    assert len(queue)>0
    assert families.candidate_multi_account_evasion.eq(1).any()
    assert ((families.shared_billing_context==1) & families.reason_codes.str.contains("shared_billing_requires_enterprise_context_review")).any()
    assert not ((families.shared_billing_context==1) & (families.candidate_multi_account_evasion==1)).any()


def test_v07_unknown_pattern_discovery_without_label_leakage(tmp_path):
    run(tmp_path,n_accounts=120,seed=37)
    manifest=pd.read_csv(tmp_path/"data/hidden_novelty_manifest.csv")
    novelty=pd.read_csv(tmp_path/"artifacts/emerging_novelty_accounts.csv")
    cohorts=pd.read_csv(tmp_path/"artifacts/emerging_behavior_cohorts.csv")
    graph=pd.read_csv(tmp_path/"artifacts/emerging_graph_triage.csv")
    taxonomy=pd.read_csv(tmp_path/"artifacts/candidate_taxonomy_proposals.csv")
    shadow=pd.read_csv(tmp_path/"artifacts/novel_shadow_rule_candidates.csv")
    incident=pd.read_csv(tmp_path/"artifacts/novelty_incident_diagnostics.csv")
    bench=json.loads((tmp_path/"artifacts/emerging_discovery_benchmark.json").read_text())
    assert len(manifest)>=3 and manifest.taxonomy_visible_to_detector.eq(0).all()
    assert "hidden_pattern" not in novelty.columns
    assert "ground_truth_abuse_type" not in novelty.columns
    assert len(novelty) < 0.20 * 120
    assert bench["hidden_manifest_present"] is True
    assert bench["hidden_recall_at_candidate_set"] >= 0.50
    assert "never used by discovery" in bench["benchmark_only_label_boundary"]
    assert {"candidate_taxonomy_name","data_incident_screen"}.issubset(cohorts.columns)
    assert taxonomy.policy_boundary.str.contains("not an abuse finding").all()
    assert shadow.automatic_enforcement_allowed.astype(str).str.lower().eq("false").all()
    assert shadow.next_stage.eq("independent_shadow_replay_required").all()
    assert graph.identity_boundary.str.contains("never proves common control").all()
    assert not incident.status.eq("possible_data_incident").all()


def test_v08_adversarial_adaptation_and_resilience_gates(tmp_path):
    run(tmp_path,n_accounts=120,seed=41)
    stress=pd.read_csv(tmp_path/"artifacts/adversarial_rule_stress.csv")
    defense=pd.read_csv(tmp_path/"artifacts/defense_in_depth_stress.csv")
    gates=pd.read_csv(tmp_path/"artifacts/evasion_regression_gates.csv")
    summary=json.loads((tmp_path/"artifacts/adversarial_stress_summary.json").read_text())
    assert {"strategy","adaptation_strength","rule_name","baseline_recall","adapted_recall","recall_drop","simulation_boundary"}.issubset(stress.columns)
    assert set(stress.strategy.unique())=={"velocity_smoothing","identity_fragmentation","token_rotation","quota_spreading","policy_signal_suppression","multi_signal_blending"}
    assert set(stress.adaptation_strength.unique())=={0.25,0.5,0.75,1.0}
    assert stress.simulation_boundary.str.contains("not a real-product bypass procedure").all()
    assert (stress.recall_drop>=-1e-12).all()
    assert {"defense","recall_drop","policy_boundary"}.issubset(defense.columns)
    assert defense.policy_boundary.str.contains("diagnostic only").all()
    assert summary["automatic_enforcement_allowed"] is False
    assert summary["worst_single_rule"]["recall_drop"] >= 0
    assert {"single_rule_brittleness_visible","defense_in_depth_not_worse_than_worst_single","severe_adaptation_recall_floor"}.issubset(set(gates.gate))
    assert not gates.status.eq("fail").any()
    action=pd.read_csv(tmp_path/"artifacts/stakeholder_action_register.csv")
    assert action.decision.str.contains("detection brittleness under adaptive behavior").any()
