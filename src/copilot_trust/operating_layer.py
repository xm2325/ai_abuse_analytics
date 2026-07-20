from __future__ import annotations

from pathlib import Path
import json
import pandas as pd


def _csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def _js(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def _safe_bool(v) -> bool:
    return str(v).strip().lower() in {"1", "true", "yes"}


def _relevant_rule(rules: pd.DataFrame, reason_codes: str):
    if not len(rules): return None, "no_rule_registry"
    reason=str(reason_codes).lower()
    mapping=[
        (["policy","prompt_injection","injection"],"policy_signal_escalation"),
        (["quota","entitlement"],"quota_evasion_multisignal"),
        (["token"],"shared_token_multisignal"),
        (["velocity","cadence","overnight","scripted"],"scripted_usage_multisignal"),
        (["device","identity","dispersion"],"identity_dispersion_multisignal"),
    ]
    for keys,name in mapping:
        if any(k in reason for k in keys):
            g=rules[rules.rule_name.eq(name)] if "rule_name" in rules else pd.DataFrame()
            if len(g): return g.iloc[0], "reason_code_family_match"
    if "holdout_precision" in rules:
        return rules.sort_values("holdout_precision",ascending=False).iloc[0], "fallback_highest_precision_not_case_specific"
    return rules.iloc[0], "fallback_first_registry_row"


def build_operating_layer(data_dir: str | Path, out_dir: str | Path, action_register: pd.DataFrame) -> dict[str, pd.DataFrame | dict]:
    data=Path(data_dir);out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    rules=_csv(out/"detection_rule_registry.csv");taxonomy=_csv(out/"candidate_taxonomy_proposals.csv");dq=_csv(out/"data_quality_findings.csv");entitlement_dq=_csv(out/"entitlement_data_quality.csv")
    queue=_csv(out/"investigation_queue.csv");queue_sim=_csv(out/"queue_simulation_summary.csv");power=_csv(out/"rule_evidence_power.csv");experiment_reviews=_csv(out/"policy_experiment_review_guardrails.csv")
    experiment_stop=_js(out/"policy_experiment_stopping_decision.json");alerts=_csv(out/"emerging_trend_alerts.csv")

    # Unified versioned control registry.
    control_rows=[]
    for _,r in rules.iterrows():
        control_rows.append({"control_id":str(r.get("rule_id","")),"control_type":"detection_rule","name":str(r.get("rule_name","")),"version":str(r.get("version","legacy")),"stage":str(r.get("stage","unknown")),"owner":str(r.get("owner","Trust & Safety Analytics")),"evidence_state":"gate_passed" if _safe_bool(r.get("evidence_gate_passed",False)) else "more_evidence_required","primary_evidence":f"holdout precision={float(r.get('holdout_precision',0)):.1%}; FPR={float(r.get('holdout_fpr',0)):.1%}","promotion_gate":str(r.get("promotion_gate","human review required")),"rollback_trigger":str(r.get("rollback_trigger","review on material regression")),"automatic_action_allowed":False,"source_artifacts":"detection_rule_registry.csv|rule_evidence_power.csv|historical_rule_replay.csv|evasion_regression_gates.csv"})
    for i,r in taxonomy.iterrows():
        control_rows.append({"control_id":f"T-{i+1:03d}","control_type":"candidate_taxonomy","name":str(r.get("candidate_name",r.get("candidate_taxonomy_name","candidate_taxonomy"))),"version":"1.0.0","stage":"analyst_taxonomy_review","owner":"Trust & Safety Analytics","evidence_state":"hypothesis_only","primary_evidence":str(r.get("evidence_summary","novel behavior cohort")),"promotion_gate":"competing-explanation review + independent shadow replay + matured human labels","rollback_trigger":"telemetry incident, legitimate product/integration explanation, or poor independent replay evidence","automatic_action_allowed":False,"source_artifacts":"emerging_behavior_cohorts.csv|candidate_taxonomy_proposals.csv|novelty_incident_diagnostics.csv"})
    control_rows.append({"control_id":"EXP-001","control_type":"policy_experiment","name":"synthetic_cluster_randomized_canary","version":"1.0.0","stage":str(experiment_stop.get("recommended_state","not_run")),"owner":"Product + Trust & Safety Analytics","evidence_state":str(experiment_stop.get("displacement_evidence_status","not_evaluated")),"primary_evidence":f"primary ITT={experiment_stop.get('primary_itt','n/a')}; displacement={experiment_stop.get('displacement_ratio','n/a')}","promotion_gate":"pre-period-only assignment + placebo/negative control + interference review + matured review evidence + policy owner approval","rollback_trigger":"interval-supported user harm/displacement, pretrend risk, matured clearance/appeal deterioration, or integrity failure","automatic_action_allowed":False,"source_artifacts":"policy_experiment_assignment.csv|policy_experiment_effect_summary.csv|policy_experiment_sequential_monitor.csv|policy_experiment_stopping_decision.json"})
    controls=pd.DataFrame(control_rows);controls.to_csv(out/"operating_control_registry.csv",index=False)

    # Decision lineage. P0 and explicit freeze/hold gates are blocked-or-hold states, not ordinary review rows.
    lineage_rows=[]
    for i,r in action_register.reset_index(drop=True).iterrows():
        priority=str(r.get("priority","P2"));action=str(r.get("recommended_action","review"));gate=str(r.get("review_gate","human review"));decision=str(r.get("decision","review"))
        blocked=(priority=="P0" or action.lower().startswith(("hold","pause","rollback","freeze")) or "restored before" in gate.lower() or "protect detection from telemetry" in decision.lower())
        lineage_rows.append({"decision_id":f"D-{i+1:04d}","priority":priority,"decision":decision,"owner":r.get("owner","Trust & Safety Analytics"),"partners":r.get("partners",""),"evidence_summary":r.get("evidence",""),"recommended_action":action,"review_gate":gate,"decision_state":"blocked_or_hold" if blocked else "review_required","evidence_refs":"stakeholder_action_register.csv|executive_brief.md|relevant_control_registry_row","lineage_boundary":"decision support only; no row authorizes automatic enforcement or automatic policy expansion"})
    lineage=pd.DataFrame(lineage_rows);lineage.to_csv(out/"decision_lineage.csv",index=False)

    # Data lineage and purpose limitation.
    lineage_specs=[
        ("telemetry.csv","account_feature_mart.csv","behavioral feature mart","telemetry_schema + request_id uniqueness + account referential integrity","pseudonymous behavioral metadata","Trust & Safety Analytics","daily"),
        ("accounts.csv","account_feature_mart.csv","account context and operational slices","account referential integrity","pseudonymous account metadata","Data/Engineering","daily"),
        ("entitlements.csv","entitlement_cycle_usage.csv","billing/entitlement source of truth","entitlement schema + account-cycle uniqueness","pseudonymous entitlement metadata","Billing/Data","per billing cycle + daily sync"),
        ("reviews.csv","review_feedback_metrics.csv","matured review/appeal feedback","label maturity and outcome contract","restricted case outcome metadata","Trust & Safety Operations","daily"),
        ("telemetry.csv|accounts.csv","policy_experiment_assignment.csv","pre-period-only experiment eligibility/randomization","post-treatment leakage prohibited","pseudonymous experiment metadata","Product + T&S Analytics","per experiment version"),
        ("investigation_queue.csv|operating_control_registry.csv","evidence_packages/*.md","case-to-policy evidence package","privacy-safe analyst layer only","pseudonymous investigation evidence","Trust & Safety Analytics","on case refresh"),
    ]
    dl_rows=[]
    for src,derived,purpose,contract,sensitivity,owner,freshness in lineage_specs:
        source_names=src.split("|");present=all((data/s).exists() or (out/s).exists() for s in source_names)
        dl_rows.append({"source":src,"derived_artifact":derived,"purpose":purpose,"contract_or_boundary":contract,"sensitivity":sensitivity,"owner":owner,"freshness_slo":freshness,"status":"available_current_run" if present else "review_source_availability"})
    data_lineage=pd.DataFrame(dl_rows);data_lineage.to_csv(out/"data_lineage.csv",index=False)

    # Operating SLOs.
    slo_rows=[];dq_bad=int(dq.status.isin(["warn","fail"]).sum()) if len(dq) and "status" in dq else 0;ent_bad=int(entitlement_dq.status.isin(["warn","fail"]).sum()) if len(entitlement_dq) and "status" in entitlement_dq else 0
    slo_rows.append({"slo":"source_contract_health","target":"0 fail/warn before retuning detection","observed":dq_bad+ent_bad,"status":"pass" if dq_bad+ent_bad==0 else "breach","owner":"Data/Engineering","breach_action":"repair/annotate source before detection or taxonomy changes"})
    if len(queue_sim):
        one=queue_sim.iloc[(queue_sim.analyst_fte.astype(float)-1.0).abs().argmin()];breach=float(one.get("sla_breach_rate_completed",one.get("sla_breach_share",0.0)));backlog=int(one.get("final_backlog",0))
        slo_rows.append({"slo":"one_fte_case_operations","target":"final backlog=0 and completed-case SLA breach <=5%","observed":f"backlog={backlog}; SLA breach={breach:.1%}","status":"pass" if backlog==0 and breach<=0.05 else "review","owner":"Trust & Safety Operations","breach_action":"adjust queue/rule rollout/capacity before widening detection"})
    ev_ready=int(power.evidence_sufficient_for_policy_review.sum()) if len(power) and "evidence_sufficient_for_policy_review" in power else 0
    slo_rows.append({"slo":"rule_evidence_maturity","target":">=1 evidence-ready rule before claiming promotable control","observed":ev_ready,"status":"pass" if ev_ready>=1 else "review","owner":"Trust & Safety Analytics","breach_action":"collect independent replay/matured labels; keep rules in shadow"})
    can_reviews=experiment_reviews[experiment_reviews.arm.eq("canary")] if len(experiment_reviews) and "arm" in experiment_reviews else pd.DataFrame();matured=int(can_reviews.iloc[0].matured_reviews) if len(can_reviews) else 0
    slo_rows.append({"slo":"canary_matured_review_evidence","target":">=5 matured canary reviews for strong review-rate guardrail","observed":matured,"status":"pass" if matured>=5 else "review","owner":"Trust & Safety Operations","breach_action":"hold/limit canary; collect matured review and appeal outcomes"})
    automatic_violation=bool(experiment_stop.get("automatic_policy_expansion_allowed",False)) or bool(controls.automatic_action_allowed.any())
    slo_rows.append({"slo":"automatic_action_boundary","target":"automatic enforcement/policy expansion disabled","observed":automatic_violation,"status":"breach" if automatic_violation else "pass","owner":"Policy/Governance","breach_action":"block release and require policy/legal review"})
    slos=pd.DataFrame(slo_rows);slos.to_csv(out/"operating_slo_scorecard.csv",index=False)

    # Incident replay register.
    incident_rows=[];n=0
    if len(dq):
        for _,r in dq[dq.status.isin(["warn","fail"])].iterrows():
            n+=1;incident_rows.append({"incident_id":f"INC-{n:03d}","incident_type":"data_contract","signal":r.get("contract","unknown"),"severity":r.get("status","warn"),"detected_by":"data_quality_findings.csv","blast_radius":"downstream detection/monitoring depending on affected signal","decision_taken":"freeze retuning and annotate/repair source","replay_evidence":str(r.get("observed","")),"recovery_gate":str(r.get("recommended_action","restore contract then replay")),"status":"open_for_replay_review"})
    if len(alerts):
        severe=alerts[alerts.severity.isin(["high","critical"])] if "severity" in alerts else pd.DataFrame()
        for _,r in severe.head(5).iterrows():
            n+=1;incident_rows.append({"incident_id":f"INC-{n:03d}","incident_type":"behavior_or_signal_alert","signal":r.get("metric","unknown"),"severity":r.get("severity","high"),"detected_by":"emerging_trend_alerts.csv","blast_radius":"affected metric/window; requires benign/product/data explanation review","decision_taken":"triage before taxonomy/rule change","replay_evidence":f"date={r.get('event_date','')}; robust_z={r.get('robust_z','')}","recovery_gate":str(r.get("next_step","validate signal and replay")),"status":"triage_or_replay_required"})
    if not incident_rows:incident_rows.append({"incident_id":"INC-000","incident_type":"nominal_control","signal":"no_active_high_severity_incident","severity":"none","detected_by":"data contracts + recurring monitors","blast_radius":"none identified","decision_taken":"continue monitoring","replay_evidence":"current-run controls within nominal thresholds","recovery_gate":"not applicable","status":"closed_nominal"})
    incidents=pd.DataFrame(incident_rows);incidents.to_csv(out/"incident_replay_register.csv",index=False)

    # Deterministic audit trail.
    audit_specs=[(10,"ingest_and_contract","data_quality_findings.csv","source contracts evaluated"),(20,"feature_and_detection","account_feature_mart.csv|model_metrics.json","features and risk prioritization rebuilt"),(30,"unknown_discovery","candidate_taxonomy_proposals.csv","unknown behavior discovery evaluated"),(40,"rule_evidence","detection_rule_registry.csv|rule_evidence_power.csv","rule evidence and lifecycle gates evaluated"),(50,"adversarial_resilience","evasion_regression_gates.csv","adaptive-behavior resilience evaluated"),(60,"policy_experiment","policy_experiment_stopping_decision.json","canary causal/guardrail decision evaluated"),(70,"investigation","investigation_queue.csv|cases/","human-investigation evidence generated"),(80,"operating_decision","stakeholder_action_register.csv|decision_lineage.csv","owner-specific decisions routed"),(90,"release_readiness","operating_slo_scorecard.csv","operating SLOs and automatic-action boundary checked")]
    audit=pd.DataFrame([{"stage_order":order,"stage":stage,"event":event,"artifact_refs":refs,"status":"completed_current_run","actor":"automated analytical pipeline + human-review gates","audit_boundary":"artifact generation records evidence flow; it does not imply policy approval or enforcement"} for order,stage,refs,event in audit_specs]);audit.to_csv(out/"decision_audit_trail.csv",index=False)

    # One-click case-to-policy evidence packages.
    pkg_dir=out/"evidence_packages";pkg_dir.mkdir(exist_ok=True);package_rows=[]
    bad_contract_rows=dq[dq.status.isin(["warn","fail"])] if len(dq) else pd.DataFrame();bad_contract_names="|".join(bad_contract_rows.contract.astype(str).tolist()) if len(bad_contract_rows) and "contract" in bad_contract_rows else "none"
    dq_summary="all current contracts pass" if dq_bad+ent_bad==0 else f"{dq_bad+ent_bad} contract warning/failure(s) require review ({bad_contract_names})"
    for rank,(_,case) in enumerate(queue.head(3).iterrows(),1):
        package_id=f"PKG-{rank:03d}";account=str(case.account_id);reason=str(case.get("reason_codes",""));risk=float(case.get("risk_score",0.0));rule,rule_match=_relevant_rule(rules,reason)
        rule_text=(f"{rule.rule_name} / stage={rule.stage} / evidence_gate={rule.evidence_gate_passed}" if rule is not None else "no rule registry row available")
        exp_state=str(experiment_stop.get("recommended_state","not available"));displacement=str(experiment_stop.get("displacement_evidence_status","not evaluated"))
        md=f"""# Case-to-policy evidence package: {package_id}\n\n## Executive decision\n**Human investigation / policy review only. No automatic enforcement.**\n\nAccount: `{account}`  \nInvestigation rank: **{rank}**  \nRisk priority score: **{risk:.3f}**  \nReason codes: **{reason}**\n\n## What the evidence currently supports\n- Prioritize this pseudonymous account for analyst review.\n- Treat score/rule/entity evidence as hypotheses requiring corroboration.\n- Data trust status: **{dq_summary}**.\n- Relevant registered rule context: **{rule_text}** (`{rule_match}`).\n- Current policy-experiment state: **{exp_state}**; displacement evidence: **{displacement}**.\n\n## Evidence chain\n1. `investigation_queue.csv` — prioritization and reason codes.\n2. `cases/{account}.md` — privacy-safe timeline and competing explanations where generated.\n3. `shared_entity_evidence.csv` / `linked_account_components.csv` — corroborating entity context; IP alone never proves common control.\n4. `detection_rule_registry.csv` + `rule_evidence_power.csv` — frozen rule lifecycle and uncertainty/evidence volume.\n5. `historical_rule_replay.csv` + `evasion_regression_gates.csv` — time-based and adversarial-resilience evidence.\n6. `policy_experiment_effect_summary.csv` + `policy_experiment_stopping_decision.json` — mitigation/canary evidence and displacement/user-impact guardrails.\n7. `review_feedback_metrics.csv` — matured review/appeal/overturn feedback.\n\n## Competing explanations that must be checked\n- approved automation, agent/CI workflow, or integration;\n- enterprise NAT/VPN/managed fleet/shared runner context;\n- token lifecycle or integration migration;\n- security research or legitimate high-intensity usage;\n- product, entitlement, billing, or telemetry changes.\n\n## Escalation gate\nRequire corroboration across independent signal families, source-contract health, adequate evidence volume, legitimate-user review, and the relevant policy owner. Raw content or expanded identity review requires an approved privacy/legal access path.\n\n## Audit / privacy boundary\nThis package contains synthetic/pseudonymous analyst-layer evidence. It excludes raw prompts, completions, raw IPs, payment details, and raw device identifiers. It is a reproducible evidence package, not an abuse verdict.\n"""
        (pkg_dir/f"{package_id}.md").write_text(md)
        package_rows.append({"package_id":package_id,"account_id":account,"investigation_rank":rank,"risk_score":risk,"decision_state":"human_investigation_required","data_trust":dq_summary,"data_contracts_requiring_review":bad_contract_names,"control_context":rule_text,"control_context_match":rule_match,"experiment_state":exp_state,"package_path":f"evidence_packages/{package_id}.md","automatic_enforcement_allowed":False})
    packages=pd.DataFrame(package_rows);packages.to_csv(out/"evidence_package_index.csv",index=False)

    # Release readiness separates artifact integrity from the current operating decision state.
    slo_breaches=int(slos.status.eq("breach").sum());slo_reviews=int(slos.status.eq("review").sum());governance_breach=bool(slos[(slos.slo=="automatic_action_boundary")].status.eq("breach").any())
    artifact_integrity=(len(controls)>0 and len(lineage)>0 and len(packages)>0 and len(audit)>=8 and not governance_breach)
    operating_decision_status="blocked_by_active_operating_slo_breach" if slo_breaches else "review_gates_open" if slo_reviews else "nominal"
    operating_layer_status="ready_with_active_operating_hold" if artifact_integrity and slo_breaches else "ready_with_review_gates" if artifact_integrity and slo_reviews else "ready_for_portfolio_demo" if artifact_integrity else "artifact_integrity_review_required"
    readiness={"release":"1.0.0","artifact_integrity_status":"ready_for_portfolio_demo" if artifact_integrity else "review_required","operating_decision_status":operating_decision_status,"operating_layer_status":operating_layer_status,"slo_breaches":slo_breaches,"slo_reviews":slo_reviews,"registered_controls":int(len(controls)),"decision_lineage_rows":int(len(lineage)),"evidence_packages":int(len(packages)),"active_incidents":int(incidents.status.ne("closed_nominal").sum()),"policy_experiment_state":experiment_stop.get("recommended_state","not_available"),"automatic_enforcement_allowed":False,"automatic_policy_expansion_allowed":False,"release_boundary":"portfolio/demo artifact integrity is separate from current operating holds; neither certifies a production Trust & Safety system, GitHub-scale infrastructure, or real policy approval"}
    (out/"release_readiness.json").write_text(json.dumps(readiness,indent=2))
    return {"controls":controls,"decisions":lineage,"data_lineage":data_lineage,"slos":slos,"incidents":incidents,"audit":audit,"packages":packages,"readiness":readiness}
