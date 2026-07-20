from __future__ import annotations
from pathlib import Path
import html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _table_html(df: pd.DataFrame, n: int = 12) -> str:
    if df is None or len(df) == 0: return '<p class="muted">No rows available.</p>'
    return df.head(n).to_html(index=False, classes="data-table", border=0, escape=True)


def _pct(x: float) -> str: return f"{100 * float(x):.1f}%"


def _fig_html(fig) -> str:
    fig.update_layout(template="plotly_dark", margin=dict(l=40, r=20, t=55, b=40), height=380)
    return fig.to_html(full_html=False, include_plotlyjs="cdn")


def _optional_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def build_dashboard(scores, metrics, slices, coverage, mitigation, mitigation_daily, daily_monitor, alerts, dq, rules, review_feedback, action_register, review_capacity, drift, calibration, queue_sla, queue_capacity, rule_registry, out_path: str | Path) -> None:
    out_path=Path(out_path); out_path.parent.mkdir(parents=True,exist_ok=True); art=out_path.parent.parent/"artifacts"
    replay=_optional_csv(art/"historical_rule_replay.csv"); replay_summary=_optional_csv(art/"historical_rule_replay_summary.csv"); power=_optional_csv(art/"rule_evidence_power.csv"); queue_sim=_optional_csv(art/"queue_simulation_summary.csv")
    holdout=scores[scores.split.eq("holdout")].copy()
    risk_fig=px.histogram(holdout,x="risk_score",color="label",nbins=24,barmode="overlay",title="Holdout risk distribution")
    map_fig=px.scatter(holdout,x="requests_per_active_day",y="unique_devices",size="unique_ips",color="risk_score",hover_name="account_id",hover_data=["plan","managed_infrastructure","reason_codes"],title="Investigation map: velocity × device dispersion")
    reportable=slices[slices.reportable.eq(1)].copy() if "reportable" in slices.columns else slices.copy()
    fpr_fig=px.bar(reportable.sort_values("false_positive_rate",ascending=False).head(12),x="slice_value",y="false_positive_rate",color="slice_type",title="False-positive rate by reportable operational slice")
    trend_cols=[c for c in ["policy_signal_rate","injection_rate","ip_missing_rate","requests_per_active_account"] if c in daily_monitor.columns]
    trend_long=daily_monitor[["event_date"]+trend_cols].melt("event_date",var_name="metric",value_name="value")
    trend_fig=px.line(trend_long,x="event_date",y="value",color="metric",title="Recurring abuse and telemetry monitor")
    cap_fig=px.line(review_capacity,x="review_capacity_share",y=["precision_at_capacity","known_abuse_recall_at_capacity"],markers=True,title="Review-capacity trade-off")
    drift_fig=px.bar(drift.sort_values("psi",ascending=False),x="feature",y="psi",color="status",title="Population-shift diagnostic (PSI)")
    cal_fig=go.Figure(); cal_fig.add_trace(go.Scatter(x=calibration.mean_predicted_risk,y=calibration.observed_known_abuse_rate,mode="markers+lines",name="Observed")); cal_fig.add_trace(go.Scatter(x=[0,1],y=[0,1],mode="lines",name="Perfect calibration")); cal_fig.update_layout(title="Holdout risk calibration diagnostic",xaxis_title="Mean predicted risk",yaxis_title="Observed known-abuse rate")
    queue_fig=px.bar(queue_capacity,x="analyst_hours",y="cases_reviewable",text="cases_reviewable",title="Estimated analyst capacity")
    replay_fig=px.line(replay,x="checkpoint",y="accounts_triggered",color="rule_id",line_dash="phase",markers=True,title="Time-based rule replay: triggered accounts") if len(replay) else go.Figure()
    queue_sim_fig=px.bar(queue_sim,x="analyst_fte",y=["max_backlog","final_backlog"],barmode="group",title="Queue stress test by analyst FTE") if len(queue_sim) else go.Figure()
    if len(power):
        power_fig=px.scatter(power,x="observed_fpr",y="one_sided_95_fpr_upper",size="holdout_triggered_accounts",color="evidence_sufficient_for_policy_review",hover_name="rule_name",title="Observed FPR vs one-sided 95% upper bound")
        power_fig.add_hline(y=0.05,line_dash="dash",annotation_text="5% FPR guardrail")
    else: power_fig=go.Figure()
    worst_fpr=float(reportable.false_positive_rate.max()) if len(reportable) else float(slices.false_positive_rate.max()) if len(slices) else 0.0
    top10=review_capacity.iloc[(review_capacity.review_capacity_share-0.10).abs().argmin()] if len(review_capacity) else None
    severe_alerts=int(alerts.severity.isin(["high","critical"]).sum()) if len(alerts) and "severity" in alerts else 0
    breached=int(queue_sla.sla_breached.sum()) if len(queue_sla) and "sla_breached" in queue_sla else 0
    evidence_ready=int(power.evidence_sufficient_for_policy_review.sum()) if len(power) else 0
    one_fte=queue_sim.iloc[(queue_sim.analyst_fte-1.0).abs().argmin()] if len(queue_sim) else None
    cards=[("Holdout AP",f"{metrics['average_precision']:.3f}"),("Top-10% review precision",_pct(top10.precision_at_capacity) if top10 is not None else "n/a"),("Top-10% known-abuse recall",_pct(top10.known_abuse_recall_at_capacity) if top10 is not None else "n/a"),("Worst reportable FPR",_pct(worst_fpr)),("High / critical alerts",str(severe_alerts)),("Evidence-ready rules",str(evidence_ready)),("1-FTE final replay backlog",str(int(one_fte.final_backlog)) if one_fte is not None else "n/a"),("Synthetic SLA breaches",str(breached))]
    cards_html="".join(f'<div class="card"><span>{html.escape(k)}</span><strong>{html.escape(v)}</strong></div>' for k,v in cards)
    css="""body{font-family:Inter,system-ui,sans-serif;background:#0d1117;color:#e6edf3;margin:0}.wrap{max-width:1280px;margin:auto;padding:32px}h1,h2{letter-spacing:-.02em}h2{margin-top:46px;border-top:1px solid #30363d;padding-top:26px}.sub,.muted{color:#8b949e}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px}.card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:18px}.card span{display:block;color:#8b949e;font-size:13px}.card strong{display:block;font-size:28px;margin-top:8px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(480px,1fr));gap:18px}.panel{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:16px;overflow:auto}.data-table{border-collapse:collapse;width:100%;font-size:13px}.data-table th,.data-table td{border-bottom:1px solid #30363d;padding:9px;text-align:left}.data-table th{color:#8b949e}.note{border-left:4px solid #58a6ff;padding:12px 16px;background:#161b22}.danger{border-left-color:#f85149}code{color:#79c0ff}"""
    page=f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>AI Abuse Analytics Decision Center</title><style>{css}</style></head><body><main class='wrap'>
    <h1>AI Abuse Analytics Decision Center</h1><p class='sub'>Privacy-safe synthetic benchmark for AI developer-tool Trust & Safety analytics. Scores and rules prioritize investigation; they do not authorize automatic enforcement.</p><div class='cards'>{cards_html}</div>
    <h2>What needs a decision now?</h2><div class='panel'>{_table_html(action_register,10)}</div>
    <h2>Emerging trends</h2><div class='grid'><div class='panel'>{_fig_html(trend_fig)}</div><div class='panel'><h3>Alerts</h3>{_table_html(alerts,10)}</div></div>
    <h2>Historical replay and rule evidence</h2><div class='grid'><div class='panel'>{_fig_html(replay_fig)}</div><div class='panel'>{_fig_html(power_fig)}</div><div class='panel'><h3>Replay summary</h3>{_table_html(replay_summary,12)}</div><div class='panel'><h3>Evidence sufficiency</h3>{_table_html(power,12)}</div></div><p class='note'>Replay checkpoints exclude future events. Distribution-derived rule thresholds are frozen before holdout evaluation. Small observed FPR is not treated as safe until uncertainty bounds and evidence volume also pass.</p>
    <h2>Detection and legitimate-user impact</h2><div class='grid'><div class='panel'>{_fig_html(risk_fig)}</div><div class='panel'>{_fig_html(fpr_fig)}</div><div class='panel'>{_fig_html(cap_fig)}</div><div class='panel'><h3>Shadow-rule evaluation</h3>{_table_html(rules[rules.evaluation_scope.eq('holdout')] if 'evaluation_scope' in rules else rules,10)}</div></div>
    <h2>Investigation</h2><div class='grid'><div class='panel'>{_fig_html(map_fig)}</div><div class='panel'><h3>Rule promotion / rollback register</h3>{_table_html(rule_registry,10)}</div></div>
    <h2>Operations and queue stress</h2><div class='grid'><div class='panel'>{_fig_html(queue_fig)}</div><div class='panel'>{_fig_html(queue_sim_fig)}</div><div class='panel'><h3>Queue SLA snapshot</h3>{_table_html(queue_sla[["account_id","risk_score","priority_tier","queue_age_hours","sla_hours","sla_breached"]].head(15) if len(queue_sla) else queue_sla,15)}</div><div class='panel'><h3>Replay queue scenarios</h3>{_table_html(queue_sim,10)}</div></div>
    <h2>Data quality</h2><div class='grid'><div class='panel'><h3>Signal coverage</h3>{_table_html(coverage,12)}</div><div class='panel'><h3>Contract findings</h3>{_table_html(dq,12)}</div></div>
    <h2>Drift and calibration</h2><div class='grid'><div class='panel'>{_fig_html(drift_fig)}</div><div class='panel'>{_fig_html(cal_fig)}</div></div>
    <h2>Mitigation</h2><div class='panel'>{_table_html(mitigation,5)}</div><p class='note'>Mitigation estimates are synthetic DiD-style diagnostics. Bootstrap intervals and pre-trends are shown to prevent unsupported causal claims.</p>
    <h2>Governance</h2><div class='panel'><h3>Review / appeal feedback</h3>{_table_html(review_feedback,12)}</div><p class='note danger'><strong>Boundary:</strong> no raw prompts, completions, IP addresses, payment details, or device identifiers are exposed in the default analyst layer. Expanded content or identity review requires an approved access path.</p>
    </main></body></html>"""
    out_path.write_text(page,encoding="utf-8")


def build_executive_brief(scores,metrics,slices,coverage,mitigation,alerts,dq,review_capacity,rules,out_path: str | Path) -> None:
    out_path=Path(out_path); art=out_path.parent; reportable=slices[slices.reportable.eq(1)] if "reportable" in slices.columns else slices
    worst=(reportable if len(reportable) else slices).sort_values("false_positive_rate",ascending=False).head(1); worst_text="No reportable slice." if not len(worst) else f"{worst.iloc[0].slice_type}={worst.iloc[0].slice_value}, FPR={worst.iloc[0].false_positive_rate:.1%}"
    cap=review_capacity.iloc[(review_capacity.review_capacity_share-0.10).abs().argmin()] if len(review_capacity) else None; mit=mitigation.iloc[0] if len(mitigation) else None
    power=_optional_csv(art/"rule_evidence_power.csv"); queue_sim=_optional_csv(art/"queue_simulation_summary.csv"); evidence_ready=int(power.evidence_sufficient_for_policy_review.sum()) if len(power) else 0; one_fte=queue_sim.iloc[(queue_sim.analyst_fte-1.0).abs().argmin()] if len(queue_sim) else None
    text=f"""# Executive brief

## Decision summary
The benchmark is designed for investigation prioritization, not automatic enforcement. Holdout average precision is **{metrics['average_precision']:.3f}** with false-positive rate **{metrics['false_positive_rate']:.1%}** at the selected threshold.

At approximately 10% review capacity, benchmark precision is **{cap.precision_at_capacity:.1%}** and known-abuse recall is **{cap.known_abuse_recall_at_capacity:.1%}**.

The highest reportable legitimate-user impact slice is **{worst_text}**. This should trigger confounder review before threshold or policy changes.

## Time-based validation and evidence sufficiency
Historical replay excludes events after each checkpoint and freezes distribution-derived rule thresholds before holdout use. **{evidence_ready}** candidate rules currently satisfy the synthetic evidence-sufficiency diagnostic. A low observed FPR is not considered enough when the one-sided uncertainty bound or trigger volume is still weak.

{f"Under the 1.0-FTE replay scenario, final backlog is **{int(one_fte.final_backlog)}** cases and maximum backlog is **{int(one_fte.max_backlog)}**." if one_fte is not None else "No queue replay scenario available."}

## Monitoring and data trust
High/critical alerts: **{int(alerts.severity.isin(['high','critical']).sum()) if len(alerts) and 'severity' in alerts else 0}**. Data-contract failures/warnings: **{int(dq.status.isin(['fail','warn']).sum()) if len(dq) else 0}**.

## Mitigation evidence
{f"DiD-style request change: **{mit.did_account_day_requests:.3f} requests/account-day**, bootstrap 95% interval **[{mit.bootstrap_95_ci_low:.3f}, {mit.bootstrap_95_ci_high:.3f}]**." if mit is not None else "No mitigation estimate available."}

This is synthetic observational analysis and is not causal proof.

## Operating boundaries
- Use scores and candidate rules to prioritize human investigation.
- Validate telemetry before retuning detection.
- Freeze rule definitions before holdout and historical replay evaluation.
- Treat IP sharing as supporting context, not identity proof.
- Require sufficient evidence volume and uncertainty bounds before rule promotion.
- Stress-test investigator capacity before widening a rule or threshold.
- Feed cleared cases, appeals, and overturns back into threshold and rule review.
- Use a separate approved path for raw-content or expanded identity review.
"""
    out_path.write_text(text,encoding="utf-8")
