from __future__ import annotations

from pathlib import Path
import html
import json
import pandas as pd


def _csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def _js(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def _table(df: pd.DataFrame, n: int = 10) -> str:
    if df is None or len(df) == 0:
        return '<p class="muted">No rows available.</p>'
    return df.head(n).to_html(index=False, classes="data-table", border=0, escape=True)


def enhance_decision_center(index_path: str | Path, artifact_dir: str | Path) -> None:
    """Inject a recruiter/manager-first operating brief above analytical detail."""
    index_path=Path(index_path);art=Path(artifact_dir)
    if not index_path.exists(): return
    page=index_path.read_text()
    readiness=_js(art/"release_readiness.json");slos=_csv(art/"operating_slo_scorecard.csv");controls=_csv(art/"operating_control_registry.csv");decisions=_csv(art/"decision_lineage.csv");packages=_csv(art/"evidence_package_index.csv");incidents=_csv(art/"incident_replay_register.csv")
    blocked=int((decisions.decision_state=="blocked_or_hold").sum()) if len(decisions) and "decision_state" in decisions else 0
    slo_breach=int(slos.status.eq("breach").sum()) if len(slos) else 0;slo_review=int(slos.status.eq("review").sum()) if len(slos) else 0
    exp=readiness.get("policy_experiment_state","n/a")
    cards=[
        ("Release",str(readiness.get("release","1.0.0"))),
        ("Operating status",str(readiness.get("operating_layer_status","n/a"))),
        ("Registered controls",str(readiness.get("registered_controls",len(controls)))),
        ("Decisions on hold",str(blocked)),
        ("SLO breaches / reviews",f"{slo_breach} / {slo_review}"),
        ("Evidence packages",str(readiness.get("evidence_packages",len(packages)))),
        ("Policy experiment",str(exp)),
    ]
    cards_html="".join(f'<div class="card"><span>{html.escape(k)}</span><strong style="font-size:20px">{html.escape(v)}</strong></div>' for k,v in cards)
    top_decisions=decisions[[c for c in ["decision_id","priority","decision","decision_state","owner","recommended_action"] if c in decisions.columns]].head(8) if len(decisions) else decisions
    slo_view=slos[[c for c in ["slo","target","observed","status","breach_action"] if c in slos.columns]] if len(slos) else slos
    control_view=controls[[c for c in ["control_id","control_type","name","stage","evidence_state","owner","automatic_action_allowed"] if c in controls.columns]].head(10) if len(controls) else controls
    pkg_view=packages[[c for c in ["package_id","account_id","risk_score","decision_state","experiment_state","package_path"] if c in packages.columns]].head(5) if len(packages) else packages
    incident_view=incidents[[c for c in ["incident_id","incident_type","signal","severity","decision_taken","status"] if c in incidents.columns]].head(6) if len(incidents) else incidents
    section=f"""
    <section id='operating-brief'>
      <h2>v1.0 Operating brief — start here</h2>
      <p class='note'><strong>Executive answer:</strong> this workbench is an auditable decision-support system, not an auto-enforcement engine. Start with the decisions on hold, SLO/evidence gaps, and case-to-policy packages; drill into detection, discovery, replay, adversarial stress, and experiment sections only when needed.</p>
      <div class='cards'>{cards_html}</div>
      <div class='grid'>
        <div class='panel'><h3>Decision lineage</h3>{_table(top_decisions,8)}</div>
        <div class='panel'><h3>Operating SLO scorecard</h3>{_table(slo_view,8)}</div>
        <div class='panel'><h3>Versioned control registry</h3>{_table(control_view,10)}</div>
        <div class='panel'><h3>Case → policy evidence packages</h3>{_table(pkg_view,5)}</div>
        <div class='panel'><h3>Incident / replay register</h3>{_table(incident_view,6)}</div>
      </div>
      <p class='note danger'><strong>Governance boundary:</strong> control registry state, scores, rules, cohorts, experiments and evidence packages support human decisions only. No artifact authorizes automatic enforcement or automatic policy expansion.</p>
    </section>
    """
    marker="<h2>What needs a decision now?</h2>"
    if marker in page:
        page=page.replace(marker,section+marker,1)
    else:
        page=page.replace("</h1>","</h1>"+section,1)
    index_path.write_text(page)


def build_start_here(out_path: str | Path, artifact_dir: str | Path) -> None:
    """Create a two-to-three-minute repository entry point for recruiters and reviewers."""
    out_path=Path(out_path);art=Path(artifact_dir);out_path.parent.mkdir(parents=True,exist_ok=True)
    readiness=_js(art/"release_readiness.json");slos=_csv(art/"operating_slo_scorecard.csv");decisions=_csv(art/"decision_lineage.csv");packages=_csv(art/"evidence_package_index.csv")
    holds=decisions[decisions.decision_state.eq("blocked_or_hold")] if len(decisions) and "decision_state" in decisions else pd.DataFrame()
    reviews=slos[slos.status.ne("pass")] if len(slos) else pd.DataFrame()
    top_pkg=packages.iloc[0].package_path if len(packages) else "not available"
    text=f"""# Start here — AI Abuse Analytics v1.0

## 30-second answer
This repository is a **synthetic, privacy-safe Trust & Safety analytics operating workbench for an AI developer product**. It connects telemetry, account, entitlement and review signals to known-abuse detection, unknown-pattern discovery, investigation, rule evidence, adversarial-resilience testing, controlled policy experiments, appeal/overturn feedback, and auditable operating decisions.

It does **not** use GitHub internal data or claim production enforcement experience.

## Current operating state
- Release: **{readiness.get('release','1.0.0')}**
- Portfolio/demo readiness: **{readiness.get('operating_layer_status','n/a')}**
- Registered controls: **{readiness.get('registered_controls','n/a')}**
- SLO breaches: **{readiness.get('slo_breaches','n/a')}**; review-needed SLOs: **{readiness.get('slo_reviews','n/a')}**
- Policy experiment state: **{readiness.get('policy_experiment_state','n/a')}**
- Automatic enforcement: **disabled**
- Automatic policy expansion: **disabled**

## The four questions to ask
1. **What should an analyst investigate now?** — `artifacts/investigation_queue.csv` and privacy-safe case files.
2. **Is the evidence strong enough to change a rule/taxonomy?** — rule registry, evidence-power bounds, historical replay and adversarial stress.
3. **Did a mitigation actually reduce harm, or move behavior elsewhere?** — cluster-randomized synthetic canary, ITT/ATT-style diagnostics, placebo/negative controls and displacement monitoring.
4. **Can another team reconstruct why a decision was made?** — `operating_control_registry.csv`, `decision_lineage.csv`, `decision_audit_trail.csv`, `data_lineage.csv`, SLOs and evidence packages.

## Current hold / review signals
{holds[[c for c in ['priority','decision','recommended_action'] if c in holds.columns]].head(6).to_markdown(index=False) if len(holds) else 'No explicit blocked/hold decision rows in the current synthetic run.'}

## Operating SLOs needing review
{reviews[[c for c in ['slo','observed','status','breach_action'] if c in reviews.columns]].to_markdown(index=False) if len(reviews) else 'All current operating SLOs pass.'}

## One evidence package to inspect
`artifacts/{top_pkg}`

This package shows how a single pseudonymous investigation candidate is connected to competing explanations, rule/evidence state, experiment context, privacy boundaries and policy escalation gates.

## 2–3 minute review path
1. Open `docs/index.html` and read **v1.0 Operating brief — start here**.
2. Inspect one row in **Decision lineage** and one **Case → policy evidence package**.
3. Scroll to **Policy experiment / causal evaluation** to see why a targeted metric decrease is not automatically called a success.
4. Scroll to **Unknown / emerging abuse discovery** and **Adversarial adaptation** to see how the system handles novel and adaptive behavior.
5. Read `docs/JD_TRACEABILITY.md` for the public-role-to-repository mapping.

## Architecture in one line
`data contracts → detection/discovery → investigation → evidence/replay/resilience → controlled experiment → decision lineage/SLO/audit → human policy decision`

## Production boundary
The v1.0 operating layer demonstrates analytical reasoning, contracts, lineage, lifecycle controls and decision governance in a reproducible local benchmark. A real deployment would require production event infrastructure, IAM, retention/access controls, formal experiment governance, incident tooling, immutable audit systems, service ownership and approved policy/legal processes.
"""
    out_path.write_text(text)
