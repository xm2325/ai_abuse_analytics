from __future__ import annotations

from pathlib import Path
import html
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _table_html(df: pd.DataFrame, n: int = 12) -> str:
    if df is None or len(df) == 0:
        return '<p class="muted">No rows available.</p>'
    return df.head(n).to_html(index=False, classes="data-table", border=0, escape=True)


def _pct(x: float) -> str:
    return f"{100 * float(x):.1f}%"


def _fig_html(fig) -> str:
    fig.update_layout(template="plotly_dark", margin=dict(l=40, r=20, t=55, b=40), height=380)
    return fig.to_html(full_html=False, include_plotlyjs="cdn")


def _optional_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def _optional_json(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def build_dashboard(scores, metrics, slices, coverage, mitigation, mitigation_daily, daily_monitor, alerts, dq, rules, review_feedback, action_register, review_capacity, drift, calibration, queue_sla, queue_capacity, rule_registry, out_path: str | Path) -> None:
    out_path = Path(out_path); out_path.parent.mkdir(parents=True, exist_ok=True); art = out_path.parent.parent / "artifacts"
    replay = _optional_csv(art / "historical_rule_replay.csv"); replay_summary = _optional_csv(art / "historical_rule_replay_summary.csv")
    power = _optional_csv(art / "rule_evidence_power.csv"); queue_sim = _optional_csv(art / "queue_simulation_summary.csv")
    billing = _optional_csv(art / "billing_family_risk.csv"); entitlement_queue = _optional_csv(art / "entitlement_investigation_queue.csv"); entitlement_dq = _optional_csv(art / "entitlement_data_quality.csv")
    novelty = _optional_csv(art / "emerging_novelty_accounts.csv"); cohorts = _optional_csv(art / "emerging_behavior_cohorts.csv"); graph_triage = _optional_csv(art / "emerging_graph_triage.csv")
    taxonomy = _optional_csv(art / "candidate_taxonomy_proposals.csv"); novelty_incident = _optional_csv(art / "novelty_incident_diagnostics.csv"); discovery_benchmark = _optional_json(art / "emerging_discovery_benchmark.json")
    adversarial = _optional_csv(art / "adversarial_rule_stress.csv"); defense = _optional_csv(art / "defense_in_depth_stress.csv"); evasion_gates = _optional_csv(art / "evasion_regression_gates.csv"); adversarial_summary = _optional_json(art / "adversarial_stress_summary.json")
    exp_effects = _optional_csv(art / "policy_experiment_effect_summary.csv"); exp_seq = _optional_csv(art / "policy_experiment_sequential_monitor.csv"); exp_pretrend = _optional_csv(art / "policy_experiment_pretrend.csv")
    exp_hte = _optional_csv(art / "policy_experiment_heterogeneous_effects.csv"); exp_interference = _optional_csv(art / "policy_experiment_interference_audit.csv"); exp_reviews = _optional_csv(art / "policy_experiment_review_guardrails.csv")
    exp_stop = _optional_json(art / "policy_experiment_stopping_decision.json"); exp_benchmark = _optional_json(art / "policy_experiment_benchmark.json")

    holdout = scores[scores.split.eq("holdout")].copy()
    risk_fig = px.histogram(holdout, x="risk_score", color="label", nbins=24, barmode="overlay", title="Holdout risk distribution")
    map_fig = px.scatter(holdout, x="requests_per_active_day", y="unique_devices", size="unique_ips", color="risk_score", hover_name="account_id", hover_data=["plan", "managed_infrastructure", "reason_codes"], title="Investigation map: velocity × device dispersion")
    reportable = slices[slices.reportable.eq(1)].copy() if "reportable" in slices.columns else slices.copy()
    fpr_fig = px.bar(reportable.sort_values("false_positive_rate", ascending=False).head(12), x="slice_value", y="false_positive_rate", color="slice_type", title="False-positive rate by reportable operational slice")
    trend_cols = [c for c in ["policy_signal_rate", "injection_rate", "ip_missing_rate", "requests_per_active_account"] if c in daily_monitor.columns]
    trend_long = daily_monitor[["event_date"] + trend_cols].melt("event_date", var_name="metric", value_name="value")
    trend_fig = px.line(trend_long, x="event_date", y="value", color="metric", title="Recurring abuse and telemetry monitor")
    cap_fig = px.line(review_capacity, x="review_capacity_share", y=["precision_at_capacity", "known_abuse_recall_at_capacity"], markers=True, title="Review-capacity trade-off")
    drift_fig = px.bar(drift.sort_values("psi", ascending=False), x="feature", y="psi", color="status", title="Population-shift diagnostic (PSI)")
    cal_fig = go.Figure(); cal_fig.add_trace(go.Scatter(x=calibration.mean_predicted_risk, y=calibration.observed_known_abuse_rate, mode="markers+lines", name="Observed")); cal_fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Perfect calibration")); cal_fig.update_layout(title="Holdout risk calibration diagnostic", xaxis_title="Mean predicted risk", yaxis_title="Observed known-abuse rate")
    queue_fig = px.bar(queue_capacity, x="analyst_hours", y="cases_reviewable", text="cases_reviewable", title="Estimated analyst capacity")
    replay_fig = px.line(replay, x="checkpoint", y="accounts_triggered", color="rule_id", line_dash="phase", markers=True, title="Time-based rule replay: triggered accounts") if len(replay) else go.Figure()
    queue_sim_fig = px.bar(queue_sim, x="analyst_fte", y=["max_backlog", "final_backlog"], barmode="group", title="Queue stress test by analyst FTE") if len(queue_sim) else go.Figure()
    if len(power):
        power_fig = px.scatter(power, x="observed_fpr", y="one_sided_95_fpr_upper", size="holdout_triggered_accounts", color="evidence_sufficient_for_policy_review", hover_name="rule_name", title="Observed FPR vs one-sided 95% upper bound"); power_fig.add_hline(y=0.05, line_dash="dash", annotation_text="5% FPR guardrail")
    else: power_fig = go.Figure()
    entitlement_fig = px.scatter(billing, x="family_accounts", y="family_usage_ratio", size="near_limit_accounts", color="shared_billing_context", hover_name="billing_family_ref", hover_data=["cycle_index", "candidate_multi_account_evasion", "reason_codes"], title="Billing-family entitlement pressure") if len(billing) else go.Figure()
    novelty_fig = px.scatter(novelty, x="token_rotation_delta", y="surface_switch_delta", size="novelty_score", color="cohort_id", hover_name="account_id", hover_data=[c for c in ["known_detection_flagged", "known_risk_score", "triage_status"] if c in novelty.columns], title="Unknown-pattern discovery: token rotation × surface switching") if len(novelty) else go.Figure()
    adversarial_fig = px.line(adversarial, x="adaptation_strength", y="adapted_recall", color="rule_name", line_dash="strategy", markers=True, title="Frozen-rule recall under synthetic adaptive behavior") if len(adversarial) else go.Figure()
    defense_fig = px.line(defense, x="adaptation_strength", y="adapted_recall", color="strategy", markers=True, title="Defense-in-depth diagnostic under adaptation") if len(defense) else go.Figure()
    exp_effect_fig = px.bar(exp_effects[exp_effects.estimand.isin(["ITT_canary_vs_control", "negative_control_ITT", "shadow_placebo_vs_control"])], x="outcome", y="estimate", color="estimand", barmode="group", title="Policy experiment effect estimates") if len(exp_effects) else go.Figure()
    exp_seq_fig = px.line(exp_seq, x="checkpoint", y=["primary_itt", "total_requests_itt", "alternate_surface_itt"], markers=True, title="Sequential canary monitoring") if len(exp_seq) else go.Figure()

    worst_fpr = float(reportable.false_positive_rate.max()) if len(reportable) else float(slices.false_positive_rate.max()) if len(slices) else 0.0
    top10 = review_capacity.iloc[(review_capacity.review_capacity_share - 0.10).abs().argmin()] if len(review_capacity) else None
    breached = int(queue_sla.sla_breached.sum()) if len(queue_sla) and "sla_breached" in queue_sla else 0
    evidence_ready = int(power.evidence_sufficient_for_policy_review.sum()) if len(power) else 0
    one_fte = queue_sim.iloc[(queue_sim.analyst_fte - 1.0).abs().argmin()] if len(queue_sim) else None
    candidate_families = int(billing.candidate_multi_account_evasion.sum()) if len(billing) and "candidate_multi_account_evasion" in billing else 0
    hidden_recall = discovery_benchmark.get("hidden_recall_at_candidate_set")
    worst_single_drop = adversarial_summary.get("worst_single_rule", {}).get("recall_drop"); worst_defense_drop = adversarial_summary.get("worst_defense_in_depth", {}).get("recall_drop")
    primary_exp = exp_effects[(exp_effects.estimand=="ITT_canary_vs_control")&(exp_effects.outcome=="primary_requests")] if len(exp_effects) else pd.DataFrame()
    primary_itt = float(primary_exp.iloc[0].estimate) if len(primary_exp) else None
    cards = [
        ("Holdout AP", f"{metrics['average_precision']:.3f}"),
        ("Top-10% review precision", _pct(top10.precision_at_capacity) if top10 is not None else "n/a"),
        ("Worst reportable FPR", _pct(worst_fpr)),
        ("Policy canary state", str(exp_stop.get("recommended_state", "n/a"))),
        ("Primary canary ITT*", f"{primary_itt:.3f}" if primary_itt is not None else "n/a"),
        ("Novel behavior cohorts", str(len(cohorts))),
        ("Hidden novelty recall*", _pct(hidden_recall) if hidden_recall is not None else "n/a"),
        ("Worst single-rule recall drop*", _pct(worst_single_drop) if worst_single_drop is not None else "n/a"),
        ("Worst defense recall drop*", _pct(worst_defense_drop) if worst_defense_drop is not None else "n/a"),
        ("Evidence-ready rules", str(evidence_ready)),
        ("Candidate billing families", str(candidate_families)),
        ("1-FTE final replay backlog", str(int(one_fte.final_backlog)) if one_fte is not None else "n/a"),
        ("Synthetic SLA breaches", str(breached)),
    ]
    cards_html = "".join(f'<div class="card"><span>{html.escape(k)}</span><strong>{html.escape(v)}</strong></div>' for k, v in cards)
    css = """body{font-family:Inter,system-ui,sans-serif;background:#0d1117;color:#e6edf3;margin:0}.wrap{max-width:1280px;margin:auto;padding:32px}h1,h2{letter-spacing:-.02em}h2{margin-top:46px;border-top:1px solid #30363d;padding-top:26px}.sub,.muted{color:#8b949e}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px}.card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:18px}.card span{display:block;color:#8b949e;font-size:13px}.card strong{display:block;font-size:24px;margin-top:8px;overflow-wrap:anywhere}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(480px,1fr));gap:18px}.panel{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:16px;overflow:auto}.data-table{border-collapse:collapse;width:100%;font-size:13px}.data-table th,.data-table td{border-bottom:1px solid #30363d;padding:9px;text-align:left}.data-table th{color:#8b949e}.note{border-left:4px solid #58a6ff;padding:12px 16px;background:#161b22}.danger{border-left-color:#f85149}code{color:#79c0ff}"""
    page = f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>AI Abuse Analytics Decision Center</title><style>{css}</style></head><body><main class='wrap'>
    <h1>AI Abuse Analytics Decision Center</h1><p class='sub'>Privacy-safe synthetic benchmark for AI developer-tool Trust & Safety analytics. Scores, experiments, novelty cohorts, billing-family signals, and rules support human investigation and policy review; they do not authorize automatic enforcement.</p><div class='cards'>{cards_html}</div>
    <p class='muted'>* Policy-experiment estimates, hidden novelty recall, and adversarial recall degradation are synthetic benchmark diagnostics only. Hidden benchmark manifests are never used by assignment, estimation, discovery, or policy decisions.</p>
    <h2>What needs a decision now?</h2><div class='panel'>{_table_html(action_register,14)}</div>
    <h2>Policy experimentation / causal evaluation</h2><div class='grid'><div class='panel'>{_fig_html(exp_effect_fig)}</div><div class='panel'>{_fig_html(exp_seq_fig)}</div><div class='panel'><h3>Pre-trend diagnostics</h3>{_table_html(exp_pretrend,10)}</div><div class='panel'><h3>Interference / spillover audit</h3>{_table_html(exp_interference,10)}</div><div class='panel'><h3>Heterogeneous effects</h3>{_table_html(exp_hte[exp_hte.reportable.eq(1)] if len(exp_hte) and 'reportable' in exp_hte else exp_hte,12)}</div><div class='panel'><h3>Matured review guardrails</h3>{_table_html(exp_reviews,10)}</div></div><p class='note danger'><strong>Experiment boundary:</strong> eligibility, clustering, and assignment use pre-rollout data only. Strong org/token/payment links define randomization clusters; IP remains context-only. Sequential monitoring never auto-expands a canary. Spillover, user-impact, delayed-label, and policy-owner review can pause or return a treatment to shadow.</p>
    <h2>Adversarial adaptation / detection resilience</h2><div class='grid'><div class='panel'>{_fig_html(adversarial_fig)}</div><div class='panel'>{_fig_html(defense_fig)}</div><div class='panel'><h3>Evasion regression gates</h3>{_table_html(evasion_gates,10)}</div><div class='panel'><h3>Largest rule degradations</h3>{_table_html(adversarial.sort_values('recall_drop',ascending=False).head(12) if len(adversarial) else adversarial,12)}</div></div><p class='note danger'><strong>Defensive boundary:</strong> this is a coarse synthetic resilience stress test. It does not reproduce real production thresholds or provide a bypass procedure. Material degradation routes a rule to rework, independent-signal development, canary/replay, and rollback review.</p>
    <h2>Unknown / emerging abuse discovery</h2><div class='grid'><div class='panel'>{_fig_html(novelty_fig)}</div><div class='panel'><h3>Behavior cohorts</h3>{_table_html(cohorts,12)}</div><div class='panel'><h3>Candidate taxonomy proposals</h3>{_table_html(taxonomy,12)}</div><div class='panel'><h3>Graph/context triage</h3>{_table_html(graph_triage,12)}</div><div class='panel'><h3>Novelty vs telemetry incident</h3>{_table_html(novelty_incident,10)}</div></div><p class='note'>Discovery uses recent-vs-baseline behavior changes and does not read hidden benchmark labels. A novel cohort becomes a taxonomy proposal and candidate shadow definition only after telemetry-health and legitimate-integration review.</p>
    <h2>Emerging known-signal trends</h2><div class='grid'><div class='panel'>{_fig_html(trend_fig)}</div><div class='panel'><h3>Alerts</h3>{_table_html(alerts,10)}</div></div>
    <h2>Historical replay and rule evidence</h2><div class='grid'><div class='panel'>{_fig_html(replay_fig)}</div><div class='panel'>{_fig_html(power_fig)}</div><div class='panel'><h3>Replay summary</h3>{_table_html(replay_summary,12)}</div><div class='panel'><h3>Evidence sufficiency</h3>{_table_html(power,12)}</div></div><p class='note'>Replay checkpoints exclude future events. Small observed FPR is not treated as safe until uncertainty bounds and evidence volume also pass.</p>
    <h2>Billing and entitlement abuse</h2><div class='grid'><div class='panel'>{_fig_html(entitlement_fig)}</div><div class='panel'><h3>Entitlement investigation queue</h3>{_table_html(entitlement_queue,15)}</div><div class='panel'><h3>Billing/entitlement data contracts</h3>{_table_html(entitlement_dq,10)}</div></div><p class='note'>Multi-account entitlement pressure is an investigation signal, not proof of evasion. Managed enterprise/shared billing context must be checked before escalation.</p>
    <h2>Detection and legitimate-user impact</h2><div class='grid'><div class='panel'>{_fig_html(risk_fig)}</div><div class='panel'>{_fig_html(fpr_fig)}</div><div class='panel'>{_fig_html(cap_fig)}</div><div class='panel'><h3>Shadow-rule evaluation</h3>{_table_html(rules[rules.evaluation_scope.eq('holdout')] if 'evaluation_scope' in rules else rules,10)}</div></div>
    <h2>Investigation</h2><div class='grid'><div class='panel'>{_fig_html(map_fig)}</div><div class='panel'><h3>Rule promotion / rollback register</h3>{_table_html(rule_registry,10)}</div></div>
    <h2>Operations and queue stress</h2><div class='grid'><div class='panel'>{_fig_html(queue_fig)}</div><div class='panel'>{_fig_html(queue_sim_fig)}</div><div class='panel'><h3>Queue SLA snapshot</h3>{_table_html(queue_sla[["account_id","risk_score","priority_tier","queue_age_hours","sla_hours","sla_breached"]].head(15) if len(queue_sla) else queue_sla,15)}</div><div class='panel'><h3>Replay queue scenarios</h3>{_table_html(queue_sim,10)}</div></div>
    <h2>Data quality</h2><div class='grid'><div class='panel'><h3>Signal coverage</h3>{_table_html(coverage,12)}</div><div class='panel'><h3>Contract findings</h3>{_table_html(dq,12)}</div></div>
    <h2>Drift and calibration</h2><div class='grid'><div class='panel'>{_fig_html(drift_fig)}</div><div class='panel'>{_fig_html(cal_fig)}</div></div>
    <h2>Mitigation</h2><div class='panel'>{_table_html(mitigation,5)}</div><p class='note'>The legacy mitigation view is a synthetic DiD-style diagnostic. v0.9 adds a separate randomized-canary experiment path for stronger causal reasoning and explicit spillover/guardrail checks.</p>
    <h2>Governance</h2><div class='panel'><h3>Review / appeal feedback</h3>{_table_html(review_feedback,12)}</div><p class='note danger'><strong>Boundary:</strong> no raw prompts, completions, IP addresses, payment details, or device identifiers are exposed in the default analyst layer. Expanded content or identity review requires an approved access path.</p>
    </main></body></html>"""
    out_path.write_text(page, encoding="utf-8")


def build_executive_brief(scores, metrics, slices, coverage, mitigation, alerts, dq, review_capacity, rules, out_path: str | Path) -> None:
    out_path = Path(out_path); art = out_path.parent; reportable = slices[slices.reportable.eq(1)] if "reportable" in slices.columns else slices
    worst = (reportable if len(reportable) else slices).sort_values("false_positive_rate", ascending=False).head(1)
    worst_text = "No reportable slice." if not len(worst) else f"{worst.iloc[0].slice_type}={worst.iloc[0].slice_value}, FPR={worst.iloc[0].false_positive_rate:.1%}"
    cap = review_capacity.iloc[(review_capacity.review_capacity_share - 0.10).abs().argmin()] if len(review_capacity) else None; mit = mitigation.iloc[0] if len(mitigation) else None
    power = _optional_csv(art / "rule_evidence_power.csv"); queue_sim = _optional_csv(art / "queue_simulation_summary.csv"); billing = _optional_csv(art / "billing_family_risk.csv")
    cohorts = _optional_csv(art / "emerging_behavior_cohorts.csv"); discovery_benchmark = _optional_json(art / "emerging_discovery_benchmark.json"); incident = _optional_csv(art / "novelty_incident_diagnostics.csv")
    adversarial_summary = _optional_json(art / "adversarial_stress_summary.json"); evasion_gates = _optional_csv(art / "evasion_regression_gates.csv")
    exp_effects = _optional_csv(art / "policy_experiment_effect_summary.csv"); exp_stop = _optional_json(art / "policy_experiment_stopping_decision.json"); exp_bench = _optional_json(art / "policy_experiment_benchmark.json")
    evidence_ready = int(power.evidence_sufficient_for_policy_review.sum()) if len(power) else 0; one_fte = queue_sim.iloc[(queue_sim.analyst_fte - 1.0).abs().argmin()] if len(queue_sim) else None; candidate_families = int(billing.candidate_multi_account_evasion.sum()) if len(billing) and "candidate_multi_account_evasion" in billing else 0
    hidden_recall = discovery_benchmark.get("hidden_recall_at_candidate_set"); incident_status = "clear" if len(incident) and not incident.status.eq("possible_data_incident").any() else "review telemetry health first"
    worst_rule = adversarial_summary.get("worst_single_rule", {}); worst_defense = adversarial_summary.get("worst_defense_in_depth", {})
    gate_warnings = int(evasion_gates.status.eq("warn").sum()) if len(evasion_gates) else 0; gate_failures = int(evasion_gates.status.eq("fail").sum()) if len(evasion_gates) else 0
    primary = exp_effects[(exp_effects.estimand=="ITT_canary_vs_control")&(exp_effects.outcome=="primary_requests")].head(1) if len(exp_effects) else pd.DataFrame()
    total = exp_effects[(exp_effects.estimand=="ITT_canary_vs_control")&(exp_effects.outcome=="total_requests")].head(1) if len(exp_effects) else pd.DataFrame()
    text = f"""# Executive brief

## Decision summary
The benchmark is designed for investigation prioritization and policy review, not automatic enforcement. Holdout average precision is **{metrics['average_precision']:.3f}** with false-positive rate **{metrics['false_positive_rate']:.1%}** at the selected threshold.

At approximately 10% review capacity, benchmark precision is **{cap.precision_at_capacity:.1%}** and known-abuse recall is **{cap.known_abuse_recall_at_capacity:.1%}**.

The highest reportable legitimate-user impact slice is **{worst_text}**. This should trigger confounder review before threshold or policy changes.

## Policy experiment / canary decision
{f"Cluster-randomized synthetic canary ITT on primary requests is **{float(primary.iloc[0].estimate):.3f}** with 95% interval **[{float(primary.iloc[0].ci95_low):.3f}, {float(primary.iloc[0].ci95_high):.3f}]**. Net total-request ITT is **{float(total.iloc[0].estimate):.3f}**." if len(primary) and len(total) else "No policy-experiment estimate is available."}

Recommended experiment state: **{exp_stop.get('recommended_state','n/a')}**. Displacement ratio: **{exp_stop.get('displacement_ratio','n/a')}**. Canary exposure rate: **{exp_stop.get('exposure_rate_canary','n/a')}**.

Eligibility, clustering, and assignment use pre-rollout data only. Strong org/token/payment links define randomization clusters. IP remains context-only for spillover sensitivity and never proves common control. Hidden responder/migration truth is benchmark-only and is not used by assignment or estimation: **{exp_bench.get('manifest_used_by_effect_estimation') is False}**.

## Adversarial adaptation / rule resilience
{f"The largest synthetic single-rule recall degradation is **{float(worst_rule.get('recall_drop',0)):.1%}** for **{worst_rule.get('rule_name')}** under **{worst_rule.get('strategy')}**. The worst defense-in-depth diagnostic drop is **{float(worst_defense.get('recall_drop',0)):.1%}**." if worst_rule else "No adversarial stress result is available."}

Evasion regression gates: **{gate_failures} failures**, **{gate_warnings} warnings**. Material degradation should trigger rule rework, independent-signal development, canary/replay, and rollback review rather than silent threshold tuning.

## Unknown / emerging abuse discovery
The unsupervised recent-vs-baseline workflow produced **{len(cohorts)}** behavior cohorts. Telemetry-health screen: **{incident_status}**. {f"Benchmark-only hidden-pattern recall in the candidate set is **{hidden_recall:.1%}**; hidden labels are never used for ranking or clustering." if hidden_recall is not None else "No hidden-pattern benchmark result is available."}

Novel cohorts are not abuse findings. They become analyst taxonomy proposals first, then require competing-explanation review and an independent shadow/replay window before any rule promotion.

## Billing / entitlement investigation
Synthetic cycle-level analysis identifies **{candidate_families}** billing-family cycles for multi-account entitlement-pressure review. Managed enterprise billing, shared organizational payment context, plan changes, credits, and legitimate multi-seat usage must be checked before escalation.

## Time-based validation and evidence sufficiency
Historical replay excludes events after each checkpoint. **{evidence_ready}** candidate rules currently satisfy the synthetic evidence-sufficiency diagnostic. A low observed FPR is not considered enough when uncertainty or trigger volume is weak.

{f"Under the 1.0-FTE replay scenario, final backlog is **{int(one_fte.final_backlog)}** cases and maximum backlog is **{int(one_fte.max_backlog)}**." if one_fte is not None else "No queue replay scenario available."}

## Monitoring and data trust
High/critical alerts: **{int(alerts.severity.isin(['high','critical']).sum()) if len(alerts) and 'severity' in alerts else 0}**. Data-contract failures/warnings: **{int(dq.status.isin(['fail','warn']).sum()) if len(dq) else 0}**.

## Legacy mitigation evidence
{f"DiD-style request change: **{mit.did_account_day_requests:.3f} requests/account-day**, bootstrap 95% interval **[{mit.bootstrap_95_ci_low:.3f}, {mit.bootstrap_95_ci_high:.3f}]**." if mit is not None else "No mitigation estimate available."}

The legacy DiD view remains observational and is not causal proof. The randomized synthetic canary is a separate evaluation path and still requires interference, user-impact, sequential, and policy-owner review.

## Operating boundaries
- Never use post-rollout data or hidden benchmark truth to define experiment eligibility, clusters, or assignment.
- Never auto-expand a canary from a sequential metric; policy-owner review is mandatory.
- Treat spillover and behavior displacement as part of the treatment effect, not as success hidden in another surface/account.
- Use negative controls, shadow placebo, pre-trends, matured review outcomes, and HTE evidence-volume checks before causal claims.
- Treat adversarial stress as a resilience diagnostic, not a bypass guide or production threshold disclosure.
- Separate behavioral novelty from telemetry/data incidents before creating a taxonomy proposal.
- Treat IP or shared billing context as supporting evidence, not identity or abuse proof.
- Feed cleared cases, appeals, overturns, experiment outcomes, and rollback decisions back into threshold, taxonomy, and policy review.
- Use a separate approved path for raw-content or expanded identity review.
"""
    out_path.write_text(text, encoding="utf-8")
