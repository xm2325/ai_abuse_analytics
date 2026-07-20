from __future__ import annotations
from pathlib import Path
import json
import pandas as pd


def build_action_register(metrics:dict,slices:pd.DataFrame,dq:pd.DataFrame,alerts:pd.DataFrame,rules:pd.DataFrame,mitigation:pd.DataFrame,out_dir:str|Path)->pd.DataFrame:
    out_dir=Path(out_dir);out_dir.mkdir(parents=True,exist_ok=True)
    reportable=slices[slices.get("reportable",1).eq(1)] if "reportable" in slices.columns else slices
    worst=(reportable if len(reportable) else slices).sort_values("false_positive_rate",ascending=False).iloc[0]
    failed_dq=dq[dq.status.isin(["fail","warn"])].copy();trend_alerts=alerts[~alerts.metric.str.contains("missing",na=False)].copy() if not alerts.empty else alerts
    if not trend_alerts.empty: trend_alerts["abs_z"]=trend_alerts.robust_z.abs();top_alert=trend_alerts.sort_values(["abs_z","event_date"],ascending=[False,False]).iloc[0]
    else: top_alert=None
    holdout_rules=rules[rules.evaluation_scope.eq("holdout")] if "evaluation_scope" in rules.columns else rules;eligible_rules=holdout_rules[holdout_rules.accounts_triggered>=1];best_rule=(eligible_rules if len(eligible_rules) else holdout_rules).sort_values("precision",ascending=False).iloc[0];mit=mitigation.iloc[0]
    rows=[
        {"priority":"P0" if worst.false_positive_rate>0.05 else "P1","decision":"review threshold impact on legitimate usage","evidence":f"worst holdout FPR={worst.false_positive_rate:.1%} for {worst.slice_type}={worst.slice_value}","recommended_action":"review confounders and plan-specific baselines before any enforcement policy change","owner":"Trust & Safety Analytics","partners":"Product + Anti-Abuse Engineering","review_gate":"human review and policy owner approval"},
        {"priority":"P0" if len(failed_dq) else "P2","decision":"protect detection from telemetry regressions","evidence":failed_dq.iloc[0].observed if len(failed_dq) else "all current contracts within thresholds","recommended_action":failed_dq.iloc[0].recommended_action if len(failed_dq) else "continue monitoring","owner":"Data/Engineering","partners":"Trust & Safety Analytics","review_gate":"data contract restored before retuning detection"},
        {"priority":"P1" if top_alert is not None else "P2","decision":"triage emerging known-signal trend","evidence":f"{top_alert.metric} {top_alert.direction}, robust z={top_alert.robust_z:.1f} on {top_alert.event_date}" if top_alert is not None else "no high-severity observable trend alert in benchmark window","recommended_action":top_alert.next_step if top_alert is not None else "maintain recurring monitor","owner":"Trust & Safety Analytics","partners":"Security + Product","review_gate":"validate signal and benign explanations before new rule"},
        {"priority":"P1","decision":"decide whether a candidate rule can leave shadow mode","evidence":f"{best_rule.rule_name}: precision={best_rule.precision:.1%}, FPR={best_rule.false_positive_rate:.1%}, workload={best_rule.review_workload_share:.1%}","recommended_action":best_rule.recommendation,"owner":"Trust & Safety + Anti-Abuse Engineering","partners":"Data Science + Product","review_gate":"human-investigation queue only; no automatic enforcement"},
        {"priority":"P1","decision":"assess mitigation before wider rollout","evidence":f"DiD-style change={mit.did_account_day_requests:.3f} requests/account-day; 95% bootstrap CI [{mit.bootstrap_95_ci_low:.3f}, {mit.bootstrap_95_ci_high:.3f}]","recommended_action":"check pre-trends, user-impact guardrails, and rollout assignment before causal claim","owner":"Product + Trust & Safety Analytics","partners":"Engineering + Data Science","review_gate":"rollout review"}
    ]
    taxonomy_path=out_dir/"candidate_taxonomy_proposals.csv";cohorts_path=out_dir/"emerging_behavior_cohorts.csv"
    if taxonomy_path.exists() and cohorts_path.exists():
        taxonomy=pd.read_csv(taxonomy_path);cohorts=pd.read_csv(cohorts_path)
        if len(taxonomy) and len(cohorts):
            top=cohorts.sort_values("mean_novelty_score",ascending=False).iloc[0]
            proposal=taxonomy[taxonomy.cohort_id.eq(top.cohort_id)].iloc[0] if taxonomy.cohort_id.eq(top.cohort_id).any() else taxonomy.iloc[0]
            rows.insert(3,{"priority":"P1","decision":"review newly discovered behavior cohort for taxonomy inclusion","evidence":f"{top.cohort_id}: {proposal.candidate_name}, n={int(top.candidate_accounts)}, mean novelty={top.mean_novelty_score:.2f}, known-detector flag rate={top.known_detection_flag_rate:.1%}","recommended_action":"review product/integration changes, telemetry health, entity context, and sampled cases; if still unexplained, freeze a candidate definition for independent shadow replay","owner":"Trust & Safety Analytics","partners":"Product + Security + Anti-Abuse Engineering","review_gate":"taxonomy proposal only; independent replay and matured human labels required before rule promotion"})
    stress_path=out_dir/"adversarial_stress_summary.json"
    if stress_path.exists():
        summary=json.loads(stress_path.read_text());worst_rule=summary.get("worst_single_rule",{});worst_def=summary.get("worst_defense_in_depth",{})
        if worst_rule:
            drop=float(worst_rule.get("recall_drop",0) or 0);target_n=int(worst_rule.get("target_accounts_holdout",0) or 0)
            evidence_limited=target_n<3
            priority="P0" if (drop>=0.50 and not evidence_limited) else "P1"
            evidence=(f"worst target-scenario recall drop={drop:.1%} for {worst_rule.get('rule_name')} under {worst_rule.get('strategy')}; "
                      f"target holdout n={target_n}; worst defense-in-depth drop={float(worst_def.get('recall_drop',0)):.1%}")
            action=("treat the observed drop as a fragility hypothesis because target evidence is small; expand time-based replay/holdout evidence, then add independent signals and define canary/rollback gates"
                    if evidence_limited else
                    "keep exact production boundaries private, add independent signal families, run canary/replay after rule changes, and define rollback on material resilience degradation")
            rows.insert(4,{"priority":priority,"decision":"review detection brittleness under adaptive behavior","evidence":evidence,"recommended_action":action,"owner":"Trust & Safety Analytics + Anti-Abuse Engineering","partners":"Security + Data Science + Product","review_gate":"stress-test evidence volume + rollback review before widening detection policy"})

    experiment_path=out_dir/"policy_experiment_stopping_decision.json";effect_path=out_dir/"policy_experiment_effect_summary.csv"
    if experiment_path.exists() and effect_path.exists():
        exp=json.loads(experiment_path.read_text());effects=pd.read_csv(effect_path)
        primary=effects[(effects.estimand=="ITT_canary_vs_control")&(effects.outcome=="primary_requests")]
        total=effects[(effects.estimand=="ITT_canary_vs_control")&(effects.outcome=="total_requests")]
        p=primary.iloc[0] if len(primary) else None;t=total.iloc[0] if len(total) else None
        reasons=exp.get("guardrail_reasons",[])
        priority="P0" if exp.get("recommended_state")=="rollback_or_pause_to_shadow_for_review" else "P1"
        evidence=(f"cluster-randomized synthetic canary ITT primary={float(p.estimate):.3f} [{float(p.ci95_low):.3f}, {float(p.ci95_high):.3f}]" if p is not None else "primary ITT unavailable")
        if t is not None:evidence+=f"; net total-request ITT={float(t.estimate):.3f}"
        evidence+=f"; displacement ratio={exp.get('displacement_ratio')}; guardrails={','.join(reasons) if reasons else 'none triggered'}"
        rows.insert(5,{"priority":priority,"decision":"decide whether the policy canary should continue, pause, or return to shadow","evidence":evidence,"recommended_action":exp.get("recommended_state","hold_current_canary_collect_more_evidence"),"owner":"Product + Trust & Safety Analytics","partners":"Anti-Abuse Engineering + Data Science + Security","review_gate":"pre-period-only randomized assignment, sequential guardrails, interference review, matured labels, and policy-owner approval; never auto-expand"})
    out=pd.DataFrame(rows);out.to_csv(out_dir/"stakeholder_action_register.csv",index=False);return out


def build_stakeholder_briefs(action_register:pd.DataFrame,review_feedback:pd.DataFrame,signal_backlog:pd.DataFrame,out_dir:str|Path)->None:
    out_dir=Path(out_dir);out_dir.mkdir(parents=True,exist_ok=True);p0p1=action_register[action_register.priority.isin(["P0","P1"])];actions_text="\n".join(f"- **{r.decision}** — {r.evidence}. Next: {r.recommended_action}." for _,r in p0p1.iterrows());overall=review_feedback[(review_feedback.scope=="overall")&(review_feedback.value=="all")]
    feedback_line=(f"Matured review confirmation rate is {overall.iloc[0].final_confirmation_rate:.1%}; appeal rate among enforced cases is {overall.iloc[0].appeal_rate_among_enforced:.1%}; overturn rate among appeals is {overall.iloc[0].overturn_rate_among_appeals:.1%}.") if len(overall) else "No matured review feedback is available yet."
    (out_dir/"brief_trust_safety.md").write_text("# Trust & Safety decision brief\n\n## Decisions requiring attention\n"+actions_text+"\n\n## Review feedback\n"+feedback_line+"\n\n## Enforcement boundary\nScores, novelty cohorts, billing-family signals, candidate rules, and experiment outputs prioritize investigation and policy review. Adversarial stress tests measure brittleness but do not authorize automatic enforcement or reveal real production controls. Policy-experiment stopping decisions are advisory only: no canary is widened automatically, and spillover, delayed labels, user-impact guardrails, and interference must be reviewed before policy changes.\n")
    backlog_text="\n".join(f"- **{r.priority}: {r.signal_or_integration}** — {r.analytical_problem}. Partner: {r.partner}." for _,r in signal_backlog.iterrows());(out_dir/"brief_engineering.md").write_text("# Engineering / Data signal brief\n\n## Highest-value integration asks\n"+backlog_text+"\n\n## Operating rule\nA data-quality regression is treated as a detection-system incident. Detection retuning or new-taxonomy creation should not be used to mask broken telemetry. Evasion stress results should drive independent-signal and rollback design, not publication of exact production boundaries. Experiment assignments must be reproducible, pre-period-only, auditable, and insulated from post-treatment leakage.\n")
    (out_dir/"brief_cela_governance.md").write_text("# CELA / privacy review brief\n\n## Default analytical boundary\nThe default workbench uses synthetic metadata and hashed identifiers and does not expose raw prompts, completions, IP addresses, payment details, or device identifiers.\n\n## Review triggers\n- Any request for raw content review.\n- Any new cross-context identity linkage that changes the purpose or sensitivity of data use.\n- Any proposal to move from investigation prioritization to automatic enforcement.\n- Any new retention, sharing, or access pattern for investigation data.\n- Any policy experiment that changes user-facing treatment, eligibility, or exposure beyond the approved canary scope.\n\n## Audit expectation\nTaxonomy version, policy version, randomized assignment, exposure state, review outcome, enforcement action, appeal result, final outcome, and stopping decision should be reconstructable for audit and post-incident review.\n")
