from pathlib import Path
import json
import sys
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from copilot_trust.pipeline import run


def test_v10_operating_layer_lineage_slo_and_evidence_packages(tmp_path):
    run(tmp_path, n_accounts=120, seed=47)
    art=tmp_path/"artifacts"; docs=tmp_path/"docs"
    required=[
        "operating_control_registry.csv","decision_lineage.csv","data_lineage.csv","operating_slo_scorecard.csv",
        "incident_replay_register.csv","decision_audit_trail.csv","evidence_package_index.csv","release_readiness.json"
    ]
    for name in required:
        assert (art/name).exists() and (art/name).stat().st_size>0, name
    controls=pd.read_csv(art/"operating_control_registry.csv")
    decisions=pd.read_csv(art/"decision_lineage.csv")
    lineage=pd.read_csv(art/"data_lineage.csv")
    slos=pd.read_csv(art/"operating_slo_scorecard.csv")
    incidents=pd.read_csv(art/"incident_replay_register.csv")
    audit=pd.read_csv(art/"decision_audit_trail.csv")
    packages=pd.read_csv(art/"evidence_package_index.csv")
    readiness=json.loads((art/"release_readiness.json").read_text())

    assert {"detection_rule","candidate_taxonomy","policy_experiment"}.issubset(set(controls.control_type))
    assert controls.automatic_action_allowed.astype(str).str.lower().eq("false").all()
    assert controls.promotion_gate.str.len().gt(20).all()
    assert controls.rollback_trigger.str.len().gt(20).all()
    assert {"decision_id","evidence_refs","lineage_boundary","decision_state"}.issubset(decisions.columns)
    assert decisions.lineage_boundary.str.contains("no row authorizes automatic enforcement").all()
    assert decisions.loc[decisions.priority.eq("P0"),"decision_state"].eq("blocked_or_hold").all()
    assert {"source","derived_artifact","purpose","contract_or_boundary","sensitivity","freshness_slo"}.issubset(lineage.columns)
    assert lineage.status.eq("available_current_run").all()
    assert {"source_contract_health","rule_evidence_maturity","canary_matured_review_evidence","automatic_action_boundary"}.issubset(set(slos.slo))
    assert not slos.status.eq("breach").all()
    assert slos.loc[slos.slo.eq("automatic_action_boundary"),"status"].eq("pass").all()
    assert {"incident_id","incident_type","decision_taken","recovery_gate","status"}.issubset(incidents.columns)
    assert audit.stage_order.is_monotonic_increasing and audit.stage.nunique()>=8
    assert len(packages)>=1
    assert packages.automatic_enforcement_allowed.astype(str).str.lower().eq("false").all()
    assert packages.control_context_match.str.len().gt(0).all()
    for rel in packages.package_path:
        p=art/rel
        assert p.exists() and p.stat().st_size>300
        text=p.read_text().lower()
        assert "no automatic enforcement" in text
        assert "raw prompts" in text
        assert "competing explanations" in text
        assert "relevant registered rule context" in text
    assert readiness["release"]=="1.0.0"
    assert readiness["artifact_integrity_status"]=="ready_for_portfolio_demo"
    assert readiness["operating_decision_status"] in {"blocked_by_active_operating_slo_breach","review_gates_open","nominal"}
    assert readiness["automatic_enforcement_allowed"] is False
    assert readiness["automatic_policy_expansion_allowed"] is False
    assert readiness["evidence_packages"]==len(packages)
    assert (docs/"START_HERE.md").exists()
    assert "2–3 minute review path" in (docs/"START_HERE.md").read_text()
    html=(docs/"index.html").read_text()
    assert "v1.0 Operating brief — start here" in html
    assert "Case → policy evidence packages" in html
